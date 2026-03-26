"""BizPulse AI — Tax Computation Engine

Pure computation functions for GRA tax obligations.
All rates come from the compliance_rates table (never hardcoded).
All amounts in pesewas (integer). Rates in basis points (1500 = 15.00%).

Sprint 1 VAT simplification:
  - Output VAT = VAT rate applied to STANDARD_RATED INCOME transactions
  - Input VAT = VAT rate applied to STANDARD_RATED EXPENSE transactions
  - Amounts assumed VAT-exclusive (documented in ADR)
"""

from datetime import date


def apply_rate_bps(amount_pesewas: int, rate_bps: int) -> int:
    """Apply a basis-points rate to an amount. Returns pesewas (rounded down)."""
    if amount_pesewas < 0 or rate_bps < 0:
        raise ValueError("Amount and rate must be non-negative")
    return (amount_pesewas * rate_bps) // 10000


def find_effective_rate(
    rates: list[dict],
    rate_type: str,
    rate_code: str,
    as_of: date,
) -> dict | None:
    """Find the effective rate for a given type, code, and date.

    Rates must have: rate_type, rate_code, percentage_basis_points,
    effective_from, effective_to (None = currently active).
    """
    for r in rates:
        if r["rate_type"] != rate_type or r["rate_code"] != rate_code:
            continue
        if r["effective_from"] > as_of:
            continue
        if r.get("effective_to") and r["effective_to"] < as_of:
            continue
        return r
    return None


def find_rates_by_type(
    rates: list[dict],
    rate_type: str,
    as_of: date,
) -> list[dict]:
    """Find all effective rates for a given type and date."""
    result = []
    for r in rates:
        if r["rate_type"] != rate_type:
            continue
        if r["effective_from"] > as_of:
            continue
        if r.get("effective_to") and r["effective_to"] < as_of:
            continue
        result.append(r)
    return result


def sum_transactions(transactions: list[dict], txn_type: str, tax_category: str) -> int:
    """Sum pesewas for transactions matching type and tax category.

    Each transaction dict must have:
      - type: 'INCOME' or 'EXPENSE'
      - amount_pesewas: int
      - tax_category: str (from transaction_tax_metadata join, default STANDARD_RATED)
    """
    return sum(
        t["amount_pesewas"]
        for t in transactions
        if t.get("type") == txn_type and t.get("tax_category", "STANDARD_RATED") == tax_category
    )


def compute_vat(
    transactions: list[dict],
    rates: list[dict],
    as_of: date,
) -> dict:
    """Compute VAT (output - input) for a period.

    Returns:
        dict with taxable_sales, output_vat, taxable_purchases, input_vat, net_vat,
        rate_bps, and computation_details.
    """
    vat_rate = find_effective_rate(rates, "VAT", "VAT_STANDARD", as_of)
    if not vat_rate:
        return {
            "taxable_sales_pesewas": 0,
            "output_vat_pesewas": 0,
            "taxable_purchases_pesewas": 0,
            "input_vat_pesewas": 0,
            "net_vat_pesewas": 0,
            "rate_bps": 0,
            "error": "No effective VAT rate found",
        }

    rate_bps = vat_rate["percentage_basis_points"]

    taxable_sales = sum_transactions(transactions, "INCOME", "STANDARD_RATED")
    taxable_purchases = sum_transactions(transactions, "EXPENSE", "STANDARD_RATED")

    output_vat = apply_rate_bps(taxable_sales, rate_bps)
    input_vat = apply_rate_bps(taxable_purchases, rate_bps)
    net_vat = output_vat - input_vat

    return {
        "taxable_sales_pesewas": taxable_sales,
        "output_vat_pesewas": output_vat,
        "taxable_purchases_pesewas": taxable_purchases,
        "input_vat_pesewas": input_vat,
        "net_vat_pesewas": net_vat,
        "rate_bps": rate_bps,
    }


def compute_nhil_getfund(
    transactions: list[dict],
    rates: list[dict],
    as_of: date,
) -> dict:
    """Compute NHIL + GETFund levies.

    Queries BOTH NHIL and GETFund rate rows and sums them.
    Applied to the same taxable sales base as VAT.
    """
    nhil_getfund_rates = find_rates_by_type(rates, "NHIL_GETFUND", as_of)

    taxable_sales = sum_transactions(transactions, "INCOME", "STANDARD_RATED")

    levy_details = []
    total_levy = 0

    for rate in nhil_getfund_rates:
        levy_amount = apply_rate_bps(taxable_sales, rate["percentage_basis_points"])
        levy_details.append({
            "rate_code": rate["rate_code"],
            "rate_bps": rate["percentage_basis_points"],
            "amount_pesewas": levy_amount,
        })
        total_levy += levy_amount

    return {
        "taxable_base_pesewas": taxable_sales,
        "total_levy_pesewas": total_levy,
        "levy_details": levy_details,
    }


def compute_cit(
    transactions: list[dict],
    rates: list[dict],
    as_of: date,
) -> dict:
    """Compute Corporate Income Tax on net profit.

    Net profit = total income - deductible expenses.
    Non-deductible expenses are excluded from the deduction.
    CIT is only applied if net profit > 0.
    """
    cit_rate = find_effective_rate(rates, "CIT", "CIT_STANDARD", as_of)
    if not cit_rate:
        return {
            "total_revenue_pesewas": 0,
            "total_deductible_expenses_pesewas": 0,
            "non_deductible_expenses_pesewas": 0,
            "net_profit_pesewas": 0,
            "cit_rate_bps": 0,
            "cit_liability_pesewas": 0,
            "error": "No effective CIT rate found",
        }

    rate_bps = cit_rate["percentage_basis_points"]

    # All income counts toward revenue
    total_revenue = sum(
        t["amount_pesewas"]
        for t in transactions
        if t.get("type") == "INCOME"
    )

    # Deductible = all expenses EXCEPT NON_DEDUCTIBLE category
    deductible_expenses = sum(
        t["amount_pesewas"]
        for t in transactions
        if t.get("type") == "EXPENSE"
        and t.get("tax_category", "STANDARD_RATED") != "NON_DEDUCTIBLE"
    )

    non_deductible_expenses = sum(
        t["amount_pesewas"]
        for t in transactions
        if t.get("type") == "EXPENSE"
        and t.get("tax_category", "STANDARD_RATED") == "NON_DEDUCTIBLE"
    )

    net_profit = max(0, total_revenue - deductible_expenses)
    cit_liability = apply_rate_bps(net_profit, rate_bps)

    return {
        "total_revenue_pesewas": total_revenue,
        "total_deductible_expenses_pesewas": deductible_expenses,
        "non_deductible_expenses_pesewas": non_deductible_expenses,
        "net_profit_pesewas": net_profit,
        "cit_rate_bps": rate_bps,
        "cit_liability_pesewas": cit_liability,
    }


def compute_wht(
    transactions: list[dict],
    rates: list[dict],
    as_of: date,
) -> dict:
    """Compute Withholding Tax obligations.

    WHT applies to specific expense types. Sprint 1 uses general WHT rate
    on all STANDARD_RATED expenses as a conservative estimate.
    """
    wht_rate = find_effective_rate(rates, "WHT", "WHT_GENERAL", as_of)
    if not wht_rate:
        return {
            "taxable_base_pesewas": 0,
            "wht_amount_pesewas": 0,
            "rate_bps": 0,
            "error": "No effective WHT rate found",
        }

    rate_bps = wht_rate["percentage_basis_points"]
    taxable_base = sum_transactions(transactions, "EXPENSE", "STANDARD_RATED")
    wht_amount = apply_rate_bps(taxable_base, rate_bps)

    return {
        "taxable_base_pesewas": taxable_base,
        "wht_amount_pesewas": wht_amount,
        "rate_bps": rate_bps,
    }


def compute_paye(gross_salary_pesewas: int, rates: list[dict], as_of: date) -> dict:
    """Compute PAYE using Ghana progressive tax bands.

    Walks through PAYE bands in order (PAYE_BAND_1 through PAYE_BAND_6).
    Each band has a ceiling (band_ceiling_pesewas) and a rate (percentage_basis_points).
    Band 6 has no ceiling (remainder taxed at top rate).
    """
    paye_rates = sorted(
        find_rates_by_type(rates, "PAYE", as_of),
        key=lambda r: r["rate_code"],
    )

    if not paye_rates:
        return {
            "gross_salary_pesewas": gross_salary_pesewas,
            "total_paye_pesewas": 0,
            "band_details": [],
            "error": "No effective PAYE rates found",
        }

    remaining = gross_salary_pesewas
    total_paye = 0
    band_details = []

    for rate in paye_rates:
        if remaining <= 0:
            break
        ceiling = rate.get("band_ceiling_pesewas")
        taxable_in_band = min(remaining, ceiling) if ceiling else remaining
        paye_for_band = apply_rate_bps(taxable_in_band, rate["percentage_basis_points"])

        band_details.append({
            "rate_code": rate["rate_code"],
            "ceiling_pesewas": ceiling,
            "taxable_amount_pesewas": taxable_in_band,
            "rate_bps": rate["percentage_basis_points"],
            "paye_pesewas": paye_for_band,
        })

        total_paye += paye_for_band
        remaining -= taxable_in_band

    return {
        "gross_salary_pesewas": gross_salary_pesewas,
        "total_paye_pesewas": total_paye,
        "effective_rate_bps": (total_paye * 10000) // gross_salary_pesewas if gross_salary_pesewas > 0 else 0,
        "band_details": band_details,
    }


def compute_all_taxes(
    transactions: list[dict],
    rates: list[dict],
    as_of: date,
    period_type: str,
) -> dict:
    """Compute all applicable taxes for a period.

    VAT_MONTHLY: VAT + NHIL/GETFund + WHT
    CIT_ANNUAL: CIT only
    WHT_MONTHLY: WHT only
    """
    result = {"period_type": period_type, "as_of": str(as_of), "computations": []}

    if period_type == "VAT_MONTHLY":
        vat = compute_vat(transactions, rates, as_of)
        nhil = compute_nhil_getfund(transactions, rates, as_of)
        wht = compute_wht(transactions, rates, as_of)
        result["computations"] = [
            {"type": "VAT", **vat},
            {"type": "NHIL_GETFUND", **nhil},
            {"type": "WHT", **wht},
        ]
        result["total_liability_pesewas"] = (
            vat["net_vat_pesewas"]
            + nhil["total_levy_pesewas"]
            + wht["wht_amount_pesewas"]
        )

    elif period_type == "CIT_ANNUAL":
        cit = compute_cit(transactions, rates, as_of)
        result["computations"] = [{"type": "CIT", **cit}]
        result["total_liability_pesewas"] = cit["cit_liability_pesewas"]

    elif period_type == "WHT_MONTHLY":
        wht = compute_wht(transactions, rates, as_of)
        result["computations"] = [{"type": "WHT", **wht}]
        result["total_liability_pesewas"] = wht["wht_amount_pesewas"]

    else:
        result["error"] = f"Unknown period type: {period_type}"
        result["total_liability_pesewas"] = 0

    return result
