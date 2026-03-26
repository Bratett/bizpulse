"""BizPulse AI — Compliance Service (FastAPI)

GRA tax compliance: tax periods, computation, filing, and reporting.
All monetary values are in pesewas (BIGINT). Rates in basis points.
"""

import json
import os
import uuid
from datetime import date, datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor

from auth import get_current_user
from config import settings
from database import (
    execute_in_transaction,
    get_connection,
    query,
    query_single,
    release_connection,
)
from fastapi.responses import Response
from models import (
    CITReportResponse,
    ComputePayrollRequest,
    CreateEmployeeRequest,
    CreateInvoiceRequest,
    CreateTaxPeriodRequest,
    EmployeeResponse,
    InvoiceResponse,
    MarkFiledRequest,
    PayrollRecordResponse,
    PeriodStatus,
    TaxCategory,
    TaxPeriodResponse,
    TaxSummaryResponse,
    UpdateEmployeeRequest,
    UpdateInvoiceRequest,
    VATReportResponse,
)
from tax_engine import (
    compute_all_taxes,
    compute_cit,
    compute_nhil_getfund,
    compute_paye,
    compute_vat,
)

app = FastAPI(title="BizPulse Compliance Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc() -> datetime:
    return datetime.utcnow()


def _new_id() -> str:
    return str(uuid.uuid4())


def _fetch_rates() -> list[dict]:
    """Load all rows from compliance_rates."""
    return query("SELECT * FROM compliance_rates")


def _fetch_period(period_id: str, business_id: str) -> dict | None:
    return query_single(
        "SELECT * FROM tax_periods WHERE id = %s AND business_id = %s",
        (period_id, business_id),
    )


def _fetch_transactions(business_id: str, start_date: date, end_date: date) -> list[dict]:
    """Fetch transactions with tax-category metadata for a date range."""
    return query(
        """
        SELECT t.*, COALESCE(ttm.tax_category, 'STANDARD_RATED') AS tax_category
        FROM transactions t
        LEFT JOIN transaction_tax_metadata ttm ON t.id = ttm.transaction_id
        WHERE t.business_id = %s AND t.transaction_date BETWEEN %s AND %s
        """,
        (business_id, start_date, end_date),
    )


def _fetch_business_info(business_id: str) -> dict:
    """Return business name and TIN for reports."""
    row = query_single(
        "SELECT name, tin FROM businesses WHERE id = %s",
        (business_id,),
    )
    if not row:
        return {"name": "Unknown", "tin": None}
    return {"name": row["name"], "tin": row.get("tin")}


# ---------------------------------------------------------------------------
# 1. Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "compliance-svc"}


# ---------------------------------------------------------------------------
# 2. GET /tax/summary
# ---------------------------------------------------------------------------

@app.get("/tax/summary", response_model=TaxSummaryResponse)
async def tax_summary(user: dict = Depends(get_current_user)):
    """Current tax obligations overview for the authenticated business."""
    business_id = user["business_id"]

    periods = query(
        """
        SELECT tp.*,
               COALESCE(
                   (SELECT SUM(tc.computed_amount_pesewas)
                    FROM tax_computations tc
                    WHERE tc.period_id = tp.id),
                   0
               ) AS total_liability_pesewas
        FROM tax_periods tp
        WHERE tp.business_id = %s
        ORDER BY tp.end_date DESC
        """,
        (business_id,),
    )

    total_outstanding = sum(
        p["total_liability_pesewas"]
        for p in periods
        if p["status"] != PeriodStatus.FILED.value
    )

    # Next deadline: the earliest end_date among non-filed periods
    non_filed = [p for p in periods if p["status"] != PeriodStatus.FILED.value]
    next_deadline = min((p["end_date"] for p in non_filed), default=None)

    return TaxSummaryResponse(
        business_id=business_id,
        total_outstanding_pesewas=total_outstanding,
        next_deadline=next_deadline,
        periods=[TaxPeriodResponse(**p) for p in periods],
        rates_as_of=date.today(),
    )


# ---------------------------------------------------------------------------
# 3. GET /tax/periods
# ---------------------------------------------------------------------------

@app.get("/tax/periods", response_model=list[TaxPeriodResponse])
async def list_tax_periods(
    period_type: str | None = Query(default=None, description="Filter by period type"),
    status: str | None = Query(default=None, description="Filter by status"),
    user: dict = Depends(get_current_user),
):
    """List tax periods with optional filters."""
    business_id = user["business_id"]

    sql = """
        SELECT tp.*,
               COALESCE(
                   (SELECT SUM(tc.computed_amount_pesewas)
                    FROM tax_computations tc
                    WHERE tc.period_id = tp.id),
                   0
               ) AS total_liability_pesewas
        FROM tax_periods tp
        WHERE tp.business_id = %s
    """
    params: list = [business_id]

    if period_type:
        sql += " AND tp.period_type = %s"
        params.append(period_type)

    if status:
        sql += " AND tp.status = %s"
        params.append(status)

    sql += " ORDER BY tp.end_date DESC"

    rows = query(sql, tuple(params))
    return [TaxPeriodResponse(**r) for r in rows]


# ---------------------------------------------------------------------------
# 4. POST /tax/periods — create a new tax period
# ---------------------------------------------------------------------------

@app.post("/tax/periods", response_model=TaxPeriodResponse, status_code=201)
async def create_tax_period(
    body: CreateTaxPeriodRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new tax period. Validates no overlaps per (business_id, period_type)."""
    business_id = user["business_id"]

    # Validation: end_date >= start_date
    if body.end_date < body.start_date:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_DATE_RANGE", "message": "end_date must be >= start_date"}},
        )

    # Validation: no overlapping periods for same business + period_type
    overlap = query_single(
        """
        SELECT id FROM tax_periods
        WHERE business_id = %s
          AND period_type = %s
          AND start_date <= %s
          AND end_date >= %s
        """,
        (business_id, body.period_type.value, body.end_date, body.start_date),
    )
    if overlap:
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "PERIOD_OVERLAP", "message": "An overlapping period already exists"}},
        )

    period_id = _new_id()
    now = _now_utc()

    execute_in_transaction([
        (
            """
            INSERT INTO tax_periods (id, business_id, period_type, start_date, end_date, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (period_id, business_id, body.period_type.value, body.start_date, body.end_date, PeriodStatus.DRAFT.value, now),
        ),
    ])

    row = _fetch_period(period_id, business_id)
    row["total_liability_pesewas"] = 0
    return TaxPeriodResponse(**row)


# ---------------------------------------------------------------------------
# 5. POST /tax/periods/{period_id}/compute
# ---------------------------------------------------------------------------

@app.post("/tax/periods/{period_id}/compute")
async def compute_taxes(period_id: str, user: dict = Depends(get_current_user)):
    """Compute taxes for a period.

    Uses SELECT FOR UPDATE on the period row to prevent concurrent computation.
    All writes happen in a single transaction.
    """
    business_id = user["business_id"]
    user_id = user["user_id"]

    # Use a manual connection for SELECT FOR UPDATE within the same transaction
    conn = get_connection()
    try:
        conn.autocommit = False
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Lock the period row (MF-2: SELECT FOR UPDATE)
            cur.execute(
                "SELECT * FROM tax_periods WHERE id = %s AND business_id = %s FOR UPDATE",
                (period_id, business_id),
            )
            period = cur.fetchone()

            if not period:
                conn.rollback()
                raise HTTPException(
                    status_code=404,
                    detail={"error": {"code": "NOT_FOUND", "message": "Tax period not found"}},
                )

            if period["status"] == PeriodStatus.FILED.value:
                conn.rollback()
                raise HTTPException(
                    status_code=409,
                    detail={"error": {"code": "ALREADY_FILED", "message": "Cannot compute taxes for a filed period"}},
                )

            # Fetch transactions and rates (these reads can happen outside the
            # locked scope, but keeping them inside is fine for correctness)
            cur.execute(
                """
                SELECT t.*, COALESCE(ttm.tax_category, 'STANDARD_RATED') AS tax_category
                FROM transactions t
                LEFT JOIN transaction_tax_metadata ttm ON t.id = ttm.transaction_id
                WHERE t.business_id = %s AND t.transaction_date BETWEEN %s AND %s
                """,
                (business_id, period["start_date"], period["end_date"]),
            )
            transactions = [dict(row) for row in cur.fetchall()]

            cur.execute("SELECT * FROM compliance_rates")
            rates = [dict(row) for row in cur.fetchall()]

            # Compute
            as_of = period["end_date"]
            result = compute_all_taxes(transactions, rates, as_of, period["period_type"])
            now = _now_utc()

            # Delete previous computations for this period (recomputation)
            cur.execute(
                "DELETE FROM tax_computations WHERE period_id = %s",
                (period_id,),
            )

            # Insert each computation line
            for comp in result.get("computations", []):
                comp_id = _new_id()
                cur.execute(
                    """
                    INSERT INTO tax_computations
                        (id, period_id, rate_type, rate_code, base_amount_pesewas,
                         rate_bps, computed_amount_pesewas, computation_details, computed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        comp_id,
                        period_id,
                        comp.get("type", ""),
                        comp.get("rate_code", comp.get("type", "")),
                        comp.get("taxable_sales_pesewas", comp.get("taxable_base_pesewas", 0)),
                        comp.get("rate_bps", 0),
                        _total_for_computation(comp),
                        json.dumps(comp),
                        now,
                    ),
                )

            # Update period status
            cur.execute(
                """
                UPDATE tax_periods
                SET status = %s, computed_at = %s
                WHERE id = %s
                """,
                (PeriodStatus.COMPUTED.value, now, period_id),
            )

            # Audit log
            cur.execute(
                """
                INSERT INTO audit_log (id, business_id, user_id, action, entity_type, entity_id, details, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    _new_id(),
                    business_id,
                    user_id,
                    "TAX_COMPUTED",
                    "tax_period",
                    period_id,
                    json.dumps({
                        "period_type": period["period_type"],
                        "total_liability_pesewas": result["total_liability_pesewas"],
                    }),
                    now,
                ),
            )

            conn.commit()

    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Failed to compute taxes"}},
        )
    finally:
        conn.autocommit = True
        release_connection(conn)

    return result


def _total_for_computation(comp: dict) -> int:
    """Extract the primary computed amount from a computation dict."""
    for key in (
        "net_vat_pesewas",
        "total_levy_pesewas",
        "wht_amount_pesewas",
        "cit_liability_pesewas",
    ):
        if key in comp:
            return comp[key]
    return 0


# ---------------------------------------------------------------------------
# 6. GET /tax/reports/vat/{period_id}
# ---------------------------------------------------------------------------

@app.get("/tax/reports/vat/{period_id}", response_model=VATReportResponse)
async def vat_report(period_id: str, user: dict = Depends(get_current_user)):
    """VAT return report data for a computed period."""
    business_id = user["business_id"]

    period = _fetch_period(period_id, business_id)
    if not period:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Tax period not found"}},
        )

    if period["status"] == PeriodStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "NOT_COMPUTED", "message": "Taxes have not been computed for this period"}},
        )

    transactions = _fetch_transactions(business_id, period["start_date"], period["end_date"])
    rates = _fetch_rates()
    as_of = period["end_date"]

    vat = compute_vat(transactions, rates, as_of)
    nhil = compute_nhil_getfund(transactions, rates, as_of)
    biz = _fetch_business_info(business_id)

    # Split NHIL and GETFund from levy_details
    nhil_amount = 0
    getfund_amount = 0
    for detail in nhil.get("levy_details", []):
        if "NHIL" in detail.get("rate_code", ""):
            nhil_amount += detail["amount_pesewas"]
        elif "GETFUND" in detail.get("rate_code", ""):
            getfund_amount += detail["amount_pesewas"]

    total_payable = vat["net_vat_pesewas"] + nhil["total_levy_pesewas"]

    return VATReportResponse(
        period_id=period_id,
        business_name=biz["name"],
        business_tin=biz["tin"],
        period_start=period["start_date"],
        period_end=period["end_date"],
        taxable_sales_pesewas=vat["taxable_sales_pesewas"],
        output_vat_pesewas=vat["output_vat_pesewas"],
        taxable_purchases_pesewas=vat["taxable_purchases_pesewas"],
        input_vat_pesewas=vat["input_vat_pesewas"],
        net_vat_payable_pesewas=vat["net_vat_pesewas"],
        nhil_pesewas=nhil_amount,
        getfund_pesewas=getfund_amount,
        total_payable_pesewas=total_payable,
        computation_date=period.get("computed_at"),
    )


# ---------------------------------------------------------------------------
# 7. GET /tax/reports/cit/{period_id}
# ---------------------------------------------------------------------------

@app.get("/tax/reports/cit/{period_id}", response_model=CITReportResponse)
async def cit_report(period_id: str, user: dict = Depends(get_current_user)):
    """CIT return report data for a computed period."""
    business_id = user["business_id"]

    period = _fetch_period(period_id, business_id)
    if not period:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Tax period not found"}},
        )

    if period["status"] == PeriodStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "NOT_COMPUTED", "message": "Taxes have not been computed for this period"}},
        )

    transactions = _fetch_transactions(business_id, period["start_date"], period["end_date"])
    rates = _fetch_rates()
    as_of = period["end_date"]

    cit = compute_cit(transactions, rates, as_of)
    biz = _fetch_business_info(business_id)

    return CITReportResponse(
        period_id=period_id,
        business_name=biz["name"],
        business_tin=biz["tin"],
        period_start=period["start_date"],
        period_end=period["end_date"],
        total_revenue_pesewas=cit["total_revenue_pesewas"],
        total_deductible_expenses_pesewas=cit["total_deductible_expenses_pesewas"],
        non_deductible_expenses_pesewas=cit["non_deductible_expenses_pesewas"],
        net_profit_pesewas=cit["net_profit_pesewas"],
        cit_rate_bps=cit["cit_rate_bps"],
        cit_liability_pesewas=cit["cit_liability_pesewas"],
        computation_date=period.get("computed_at"),
    )


# ---------------------------------------------------------------------------
# 8. POST /tax/periods/{period_id}/mark-filed
# ---------------------------------------------------------------------------

@app.post("/tax/periods/{period_id}/mark-filed")
async def mark_filed(
    period_id: str,
    body: MarkFiledRequest,
    user: dict = Depends(get_current_user),
):
    """Mark a tax period as filed with GRA."""
    business_id = user["business_id"]
    user_id = user["user_id"]

    period = _fetch_period(period_id, business_id)
    if not period:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Tax period not found"}},
        )

    if period["status"] == PeriodStatus.FILED.value:
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "ALREADY_FILED", "message": "Period is already filed"}},
        )

    if period["status"] == PeriodStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "NOT_COMPUTED", "message": "Compute taxes before filing"}},
        )

    now = _now_utc()
    filing_id = _new_id()

    execute_in_transaction([
        # Insert filing record
        (
            """
            INSERT INTO filing_records
                (id, period_id, business_id, filing_reference, filing_method, notes, filed_at, filed_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (filing_id, period_id, business_id, body.filing_reference, body.filing_method, body.notes, now, user_id),
        ),
        # Update period status
        (
            """
            UPDATE tax_periods
            SET status = %s, filed_at = %s
            WHERE id = %s AND business_id = %s
            """,
            (PeriodStatus.FILED.value, now, period_id, business_id),
        ),
        # Audit log
        (
            """
            INSERT INTO audit_log (id, business_id, user_id, action, entity_type, entity_id, details, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                _new_id(),
                business_id,
                user_id,
                "TAX_FILED",
                "tax_period",
                period_id,
                json.dumps({
                    "filing_reference": body.filing_reference,
                    "filing_method": body.filing_method,
                }),
                now,
            ),
        ),
    ])

    return {
        "status": "filed",
        "period_id": period_id,
        "filing_id": filing_id,
        "filed_at": now.isoformat(),
    }


# ---------------------------------------------------------------------------
# 9. GET /tax/rates
# ---------------------------------------------------------------------------

@app.get("/tax/rates")
async def get_tax_rates(user: dict = Depends(get_current_user)):
    """Current effective rates from the compliance_rates table."""
    today = date.today()
    rows = query(
        """
        SELECT rate_type, rate_code, percentage_basis_points, effective_from, effective_to
        FROM compliance_rates
        WHERE effective_from <= %s
          AND (effective_to IS NULL OR effective_to >= %s)
        ORDER BY rate_type, rate_code
        """,
        (today, today),
    )

    # Serialize dates for JSON
    for row in rows:
        for key in ("effective_from", "effective_to"):
            if row.get(key) and isinstance(row[key], date):
                row[key] = row[key].isoformat()

    return {"rates": rows, "as_of": today.isoformat()}


# ---------------------------------------------------------------------------
# 10. PATCH /tax/metadata/{transaction_id}
# ---------------------------------------------------------------------------

@app.patch("/tax/metadata/{transaction_id}")
async def update_tax_metadata(
    transaction_id: str,
    body: dict,
    user: dict = Depends(get_current_user),
):
    """Update the tax category for a transaction (upsert)."""
    business_id = user["business_id"]

    # Validate tax_category value
    tax_category = body.get("tax_category")
    if not tax_category:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "MISSING_FIELD", "message": "tax_category is required"}},
        )

    try:
        TaxCategory(tax_category)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_VALUE",
                    "message": f"tax_category must be one of: {[e.value for e in TaxCategory]}",
                }
            },
        )

    # Verify the transaction belongs to this business
    txn = query_single(
        "SELECT id FROM transactions WHERE id = %s AND business_id = %s",
        (transaction_id, business_id),
    )
    if not txn:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Transaction not found"}},
        )

    # Upsert into transaction_tax_metadata
    execute_in_transaction([
        (
            """
            INSERT INTO transaction_tax_metadata (transaction_id, tax_category, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (transaction_id) DO UPDATE
            SET tax_category = EXCLUDED.tax_category, updated_at = EXCLUDED.updated_at
            """,
            (transaction_id, tax_category, _now_utc()),
        ),
    ])

    return {"transaction_id": transaction_id, "tax_category": tax_category}


# ---------------------------------------------------------------------------
# 11. POST /employees — create employee
# ---------------------------------------------------------------------------

@app.post("/employees", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    body: CreateEmployeeRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new employee for the authenticated business."""
    business_id = user["business_id"]
    user_id = user["user_id"]
    employee_id = _new_id()
    now = _now_utc()

    execute_in_transaction([
        (
            """
            INSERT INTO employees
                (id, business_id, employee_number, first_name, last_name,
                 tin, ssnit_number, hire_date, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                employee_id, business_id, body.employee_number,
                body.first_name, body.last_name, body.tin,
                body.ssnit_number, body.hire_date, now, now,
            ),
        ),
        (
            """
            INSERT INTO audit_log (id, business_id, user_id, action, entity_type, entity_id, details, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                _new_id(), business_id, user_id, "EMPLOYEE_CREATED",
                "employee", employee_id,
                json.dumps({"first_name": body.first_name, "last_name": body.last_name}),
                now,
            ),
        ),
    ])

    row = query_single(
        "SELECT * FROM employees WHERE id = %s AND business_id = %s",
        (employee_id, business_id),
    )
    return EmployeeResponse(**row)


# ---------------------------------------------------------------------------
# 12. GET /employees — list employees
# ---------------------------------------------------------------------------

@app.get("/employees", response_model=list[EmployeeResponse])
async def list_employees(
    status: str | None = Query(default=None, description="Filter by status (active, terminated, on_leave)"),
    user: dict = Depends(get_current_user),
):
    """List employees for the authenticated business."""
    business_id = user["business_id"]

    sql = "SELECT * FROM employees WHERE business_id = %s"
    params: list = [business_id]

    if status:
        sql += " AND status = %s"
        params.append(status)

    sql += " ORDER BY last_name, first_name"

    rows = query(sql, tuple(params))
    return [EmployeeResponse(**r) for r in rows]


# ---------------------------------------------------------------------------
# 13. GET /employees/{employee_id} — get employee detail
# ---------------------------------------------------------------------------

@app.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str, user: dict = Depends(get_current_user)):
    """Get a single employee by ID."""
    business_id = user["business_id"]

    row = query_single(
        "SELECT * FROM employees WHERE id = %s AND business_id = %s",
        (employee_id, business_id),
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Employee not found"}},
        )

    return EmployeeResponse(**row)


# ---------------------------------------------------------------------------
# 14. PATCH /employees/{employee_id} — update employee
# ---------------------------------------------------------------------------

@app.patch("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    body: UpdateEmployeeRequest,
    user: dict = Depends(get_current_user),
):
    """Update an employee's details."""
    business_id = user["business_id"]
    user_id = user["user_id"]

    existing = query_single(
        "SELECT * FROM employees WHERE id = %s AND business_id = %s",
        (employee_id, business_id),
    )
    if not existing:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Employee not found"}},
        )

    # Build dynamic SET clause from provided fields
    updates = {}
    if body.first_name is not None:
        updates["first_name"] = body.first_name
    if body.last_name is not None:
        updates["last_name"] = body.last_name
    if body.tin is not None:
        updates["tin"] = body.tin
    if body.ssnit_number is not None:
        updates["ssnit_number"] = body.ssnit_number
    if body.status is not None:
        updates["status"] = body.status.value

    if not updates:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "NO_UPDATES", "message": "No fields to update"}},
        )

    now = _now_utc()
    updates["updated_at"] = now

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values())
    values.extend([employee_id, business_id])

    execute_in_transaction([
        (
            f"UPDATE employees SET {set_clause} WHERE id = %s AND business_id = %s",
            tuple(values),
        ),
        (
            """
            INSERT INTO audit_log (id, business_id, user_id, action, entity_type, entity_id, details, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                _new_id(), business_id, user_id, "EMPLOYEE_UPDATED",
                "employee", employee_id,
                json.dumps({"updated_fields": list(updates.keys())}),
                now,
            ),
        ),
    ])

    row = query_single(
        "SELECT * FROM employees WHERE id = %s AND business_id = %s",
        (employee_id, business_id),
    )
    return EmployeeResponse(**row)


# ---------------------------------------------------------------------------
# 15. POST /payroll/compute — compute PAYE for all active employees
# ---------------------------------------------------------------------------

@app.post("/payroll/compute")
async def compute_payroll(
    body: ComputePayrollRequest,
    user: dict = Depends(get_current_user),
):
    """Compute PAYE for all active employees for a given month.

    For each active employee: look up their latest payroll record gross salary
    (or existing DRAFT record for the requested period), compute PAYE using
    progressive bands, and upsert the payroll_records row.
    All writes in a single transaction.
    """
    business_id = user["business_id"]
    user_id = user["user_id"]

    conn = get_connection()
    try:
        conn.autocommit = False
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Fetch active employees
            cur.execute(
                "SELECT * FROM employees WHERE business_id = %s AND status = 'active'",
                (business_id,),
            )
            employees = [dict(row) for row in cur.fetchall()]

            if not employees:
                conn.rollback()
                raise HTTPException(
                    status_code=400,
                    detail={"error": {"code": "NO_EMPLOYEES", "message": "No active employees found"}},
                )

            # Fetch compliance rates
            cur.execute("SELECT * FROM compliance_rates")
            rates = [dict(row) for row in cur.fetchall()]

            as_of = date(body.period_year, body.period_month, 1)
            now = _now_utc()
            results = []

            for emp in employees:
                emp_id = str(emp["id"])

                # Look for existing payroll record (DRAFT) for this period
                cur.execute(
                    """
                    SELECT * FROM payroll_records
                    WHERE employee_id = %s AND period_year = %s AND period_month = %s
                    """,
                    (emp_id, body.period_year, body.period_month),
                )
                existing_record = cur.fetchone()

                if existing_record:
                    existing_record = dict(existing_record)
                    gross_salary = existing_record["gross_salary_pesewas"]
                else:
                    # Look for previous month's payroll to carry forward salary
                    cur.execute(
                        """
                        SELECT gross_salary_pesewas FROM payroll_records
                        WHERE employee_id = %s AND status IN ('COMPUTED', 'APPROVED', 'PAID')
                        ORDER BY period_year DESC, period_month DESC
                        LIMIT 1
                        """,
                        (emp_id,),
                    )
                    prev = cur.fetchone()
                    gross_salary = dict(prev)["gross_salary_pesewas"] if prev else 0

                if gross_salary <= 0:
                    # Skip employees with no salary data
                    continue

                # Compute PAYE
                paye_result = compute_paye(gross_salary, rates, as_of)

                # SSNIT employee contribution: 5.5% (550 bps) of gross salary
                ssnit_employee = (gross_salary * 550) // 10000

                # Net salary = gross - SSNIT employee - PAYE
                net_salary = gross_salary - ssnit_employee - paye_result["total_paye_pesewas"]

                computation_details = json.dumps({
                    "paye": paye_result,
                    "ssnit_rate_bps": 550,
                })

                if existing_record:
                    # Update existing record
                    record_id = str(existing_record["id"])
                    cur.execute(
                        """
                        UPDATE payroll_records
                        SET ssnit_employee_pesewas = %s,
                            paye_pesewas = %s,
                            net_salary_pesewas = %s,
                            computation_details = %s,
                            status = 'COMPUTED',
                            computed_at = %s,
                            updated_at = %s
                        WHERE id = %s
                        """,
                        (
                            ssnit_employee, paye_result["total_paye_pesewas"],
                            net_salary, computation_details, now, now, record_id,
                        ),
                    )
                else:
                    # Insert new record
                    record_id = _new_id()
                    cur.execute(
                        """
                        INSERT INTO payroll_records
                            (id, business_id, employee_id, period_year, period_month,
                             gross_salary_pesewas, ssnit_employee_pesewas, paye_pesewas,
                             net_salary_pesewas, computation_details, status, computed_at,
                             created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'COMPUTED', %s, %s, %s)
                        """,
                        (
                            record_id, business_id, emp_id,
                            body.period_year, body.period_month,
                            gross_salary, ssnit_employee,
                            paye_result["total_paye_pesewas"], net_salary,
                            computation_details, now, now, now,
                        ),
                    )

                results.append({
                    "employee_id": emp_id,
                    "employee_name": f"{emp['first_name']} {emp['last_name']}",
                    "gross_salary_pesewas": gross_salary,
                    "ssnit_employee_pesewas": ssnit_employee,
                    "paye_pesewas": paye_result["total_paye_pesewas"],
                    "net_salary_pesewas": net_salary,
                })

            # Audit log
            cur.execute(
                """
                INSERT INTO audit_log (id, business_id, user_id, action, entity_type, entity_id, details, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    _new_id(), business_id, user_id, "PAYROLL_COMPUTED",
                    "payroll", business_id,
                    json.dumps({
                        "period_year": body.period_year,
                        "period_month": body.period_month,
                        "employee_count": len(results),
                    }),
                    now,
                ),
            )

            conn.commit()

    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Failed to compute payroll"}},
        )
    finally:
        conn.autocommit = True
        release_connection(conn)

    return {
        "period_year": body.period_year,
        "period_month": body.period_month,
        "employees_computed": len(results),
        "records": results,
    }


# ---------------------------------------------------------------------------
# 16. GET /payroll/records — list payroll records
# ---------------------------------------------------------------------------

@app.get("/payroll/records", response_model=list[PayrollRecordResponse])
async def list_payroll_records(
    period_year: int | None = Query(default=None, description="Filter by year"),
    period_month: int | None = Query(default=None, description="Filter by month (1-12)"),
    user: dict = Depends(get_current_user),
):
    """List payroll records for the authenticated business."""
    business_id = user["business_id"]

    sql = """
        SELECT pr.*, e.first_name, e.last_name
        FROM payroll_records pr
        JOIN employees e ON pr.employee_id = e.id
        WHERE pr.business_id = %s
    """
    params: list = [business_id]

    if period_year is not None:
        sql += " AND pr.period_year = %s"
        params.append(period_year)

    if period_month is not None:
        sql += " AND pr.period_month = %s"
        params.append(period_month)

    sql += " ORDER BY pr.period_year DESC, pr.period_month DESC, e.last_name, e.first_name"

    rows = query(sql, tuple(params))
    return [
        PayrollRecordResponse(
            id=str(r["id"]),
            employee_id=str(r["employee_id"]),
            employee_name=f"{r['first_name']} {r['last_name']}",
            period_year=r["period_year"],
            period_month=r["period_month"],
            gross_salary_pesewas=r["gross_salary_pesewas"],
            ssnit_employee_pesewas=r["ssnit_employee_pesewas"],
            paye_pesewas=r["paye_pesewas"],
            net_salary_pesewas=r["net_salary_pesewas"],
            status=r["status"],
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 17. POST /invoices — create invoice
# ---------------------------------------------------------------------------

@app.post("/invoices", response_model=InvoiceResponse, status_code=201)
async def create_invoice(
    body: CreateInvoiceRequest,
    user: dict = Depends(get_current_user),
):
    """Create and persist an invoice.

    Line items are stored as JSONB. Subtotal, VAT, and total are computed
    server-side from line_items and the current VAT rate.
    """
    business_id = user["business_id"]
    user_id = user["user_id"]
    invoice_id = _new_id()
    now = _now_utc()

    # Fetch current VAT rate for computation
    rates = _fetch_rates()
    vat_rate_bps = 1500  # default 15%
    today = date.today()
    for r in rates:
        if r.get("rate_code") == "VAT_STANDARD":
            eff_from = r.get("effective_from")
            eff_to = r.get("effective_to")
            if eff_from and eff_from <= today and (eff_to is None or eff_to >= today):
                vat_rate_bps = r["percentage_basis_points"]
                break

    # Compute totals from line items
    subtotal_pesewas = 0
    total_vat_pesewas = 0
    serialized_items = []
    for item in body.line_items:
        line_sub = int(item.quantity * item.unit_price_pesewas)
        line_vat = int(round(line_sub * vat_rate_bps / 10_000)) if item.vat_applicable else 0
        subtotal_pesewas += line_sub
        total_vat_pesewas += line_vat
        serialized_items.append({
            "description": item.description,
            "quantity": item.quantity,
            "unit_price_pesewas": item.unit_price_pesewas,
            "vat_applicable": item.vat_applicable,
        })

    total_pesewas = subtotal_pesewas + total_vat_pesewas

    execute_in_transaction([
        (
            """
            INSERT INTO invoices
                (id, business_id, customer_name, customer_tin, line_items,
                 subtotal_pesewas, vat_pesewas, total_pesewas, notes,
                 status, created_by, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'DRAFT', %s, %s, %s)
            """,
            (
                invoice_id, business_id, body.customer_name,
                body.customer_tin, json.dumps(serialized_items),
                subtotal_pesewas, total_vat_pesewas, total_pesewas,
                body.notes, user_id, now, now,
            ),
        ),
        (
            """
            INSERT INTO audit_log (id, business_id, user_id, action, entity_type, entity_id, details, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                _new_id(), business_id, user_id, "INVOICE_CREATED",
                "invoice", invoice_id,
                json.dumps({"customer_name": body.customer_name, "total_pesewas": total_pesewas}),
                now,
            ),
        ),
    ])

    row = query_single(
        "SELECT * FROM invoices WHERE id = %s AND business_id = %s",
        (invoice_id, business_id),
    )
    row["line_items"] = json.loads(row["line_items"]) if isinstance(row["line_items"], str) else row["line_items"]
    return InvoiceResponse(**row)


# ---------------------------------------------------------------------------
# 18. GET /invoices — list invoices
# ---------------------------------------------------------------------------

@app.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    status: str | None = Query(default=None, description="Filter by status (DRAFT, SENT, PAID, CANCELLED)"),
    user: dict = Depends(get_current_user),
):
    """List invoices for the authenticated business."""
    business_id = user["business_id"]

    sql = "SELECT * FROM invoices WHERE business_id = %s"
    params: list = [business_id]

    if status:
        sql += " AND status = %s"
        params.append(status)

    sql += " ORDER BY created_at DESC"

    rows = query(sql, tuple(params))
    results = []
    for r in rows:
        r["line_items"] = json.loads(r["line_items"]) if isinstance(r["line_items"], str) else r["line_items"]
        results.append(InvoiceResponse(**r))
    return results


# ---------------------------------------------------------------------------
# 19. GET /invoices/{invoice_id} — get invoice detail
# ---------------------------------------------------------------------------

@app.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user)):
    """Get a single invoice by ID."""
    business_id = user["business_id"]

    row = query_single(
        "SELECT * FROM invoices WHERE id = %s AND business_id = %s",
        (invoice_id, business_id),
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Invoice not found"}},
        )

    row["line_items"] = json.loads(row["line_items"]) if isinstance(row["line_items"], str) else row["line_items"]
    return InvoiceResponse(**row)


# ---------------------------------------------------------------------------
# 20. PATCH /invoices/{invoice_id} — update invoice
# ---------------------------------------------------------------------------

@app.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    body: UpdateInvoiceRequest,
    user: dict = Depends(get_current_user),
):
    """Update an invoice (status changes, customer info, notes)."""
    business_id = user["business_id"]
    user_id = user["user_id"]

    existing = query_single(
        "SELECT * FROM invoices WHERE id = %s AND business_id = %s",
        (invoice_id, business_id),
    )
    if not existing:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Invoice not found"}},
        )

    updates = {}
    if body.status is not None:
        updates["status"] = body.status.value
    if body.notes is not None:
        updates["notes"] = body.notes
    if body.customer_name is not None:
        updates["customer_name"] = body.customer_name
    if body.customer_tin is not None:
        updates["customer_tin"] = body.customer_tin

    if not updates:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "NO_UPDATES", "message": "No fields to update"}},
        )

    now = _now_utc()
    updates["updated_at"] = now

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values())
    values.extend([invoice_id, business_id])

    execute_in_transaction([
        (
            f"UPDATE invoices SET {set_clause} WHERE id = %s AND business_id = %s",
            tuple(values),
        ),
        (
            """
            INSERT INTO audit_log (id, business_id, user_id, action, entity_type, entity_id, details, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                _new_id(), business_id, user_id, "INVOICE_UPDATED",
                "invoice", invoice_id,
                json.dumps({"updated_fields": list(updates.keys())}),
                now,
            ),
        ),
    ])

    row = query_single(
        "SELECT * FROM invoices WHERE id = %s AND business_id = %s",
        (invoice_id, business_id),
    )
    row["line_items"] = json.loads(row["line_items"]) if isinstance(row["line_items"], str) else row["line_items"]
    return InvoiceResponse(**row)


# ---------------------------------------------------------------------------
# 21. GET /invoices/{invoice_id}/pdf — generate PDF for saved invoice
# ---------------------------------------------------------------------------

@app.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: str, user: dict = Depends(get_current_user)):
    """Generate a PDF for a persisted invoice using render_invoice_pdf."""
    from reports import render_invoice_pdf

    business_id = user["business_id"]

    row = query_single(
        "SELECT * FROM invoices WHERE id = %s AND business_id = %s",
        (invoice_id, business_id),
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Invoice not found"}},
        )

    line_items = json.loads(row["line_items"]) if isinstance(row["line_items"], str) else row["line_items"]

    # Fetch business details for the PDF header
    biz = _fetch_business_info(business_id)

    # Fetch current VAT rate
    rates = _fetch_rates()
    vat_rate_bps = 1500
    today = date.today()
    for r in rates:
        if r.get("rate_code") == "VAT_STANDARD":
            eff_from = r.get("effective_from")
            eff_to = r.get("effective_to")
            if eff_from and eff_from <= today and (eff_to is None or eff_to >= today):
                vat_rate_bps = r["percentage_basis_points"]
                break

    business_data = {
        "legal_name": biz.get("name", ""),
        "trading_name": biz.get("name", ""),
        "tax_identification_number": biz.get("tin", "N/A"),
        "country_code": "GH",
    }

    request_data = {
        "customer_name": row["customer_name"],
        "customer_tin": row.get("customer_tin"),
        "line_items": line_items,
        "notes": row.get("notes"),
    }

    pdf_bytes = render_invoice_pdf(business_data, request_data, vat_rate_bps)

    filename = f"invoice-{row.get('invoice_number') or invoice_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("COMPLIANCE_SVC_PORT", "8082"))
    uvicorn.run(app, host="0.0.0.0", port=port)
