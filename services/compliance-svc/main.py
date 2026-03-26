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
from models import (
    CITReportResponse,
    CreateTaxPeriodRequest,
    MarkFiledRequest,
    PeriodStatus,
    TaxCategory,
    TaxPeriodResponse,
    TaxSummaryResponse,
    VATReportResponse,
)
from tax_engine import (
    compute_all_taxes,
    compute_cit,
    compute_nhil_getfund,
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
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("COMPLIANCE_SVC_PORT", "8082"))
    uvicorn.run(app, host="0.0.0.0", port=port)
