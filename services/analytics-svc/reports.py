from datetime import date

from database import query


def profit_and_loss(business_id: str, date_from: date, date_to: date) -> dict:
    """Generate a Profit & Loss statement for the given business and date range.

    Revenue = sum of INCOME transactions grouped by account
    Expenses = sum of EXPENSE transactions grouped by account
    Net Income = Revenue - Expenses

    All amounts are in pesewas (BIGINT). Frontend converts to cedis for display.

    JOIN logic: prefers business-specific account name over system default.
    Uses DISTINCT ON to avoid double-counting when a business overrides a
    system default account code.
    """
    rows = query(
        """
        SELECT
            t.type,
            t.account_code,
            COALESCE(biz_coa.account_name, sys_coa.account_name, t.account_code) AS account_name,
            SUM(t.amount_pesewas) AS total_pesewas,
            COUNT(*) AS transaction_count
        FROM transactions t
        LEFT JOIN chart_of_accounts biz_coa
            ON biz_coa.business_id = t.business_id
            AND biz_coa.account_code = t.account_code
            AND biz_coa.active = TRUE
        LEFT JOIN chart_of_accounts sys_coa
            ON sys_coa.business_id IS NULL
            AND sys_coa.account_code = t.account_code
            AND sys_coa.active = TRUE
            AND biz_coa.id IS NULL
        WHERE t.business_id = %s
            AND t.transaction_date >= %s
            AND t.transaction_date <= %s
        GROUP BY t.type, t.account_code, COALESCE(biz_coa.account_name, sys_coa.account_name, t.account_code)
        ORDER BY t.type, t.account_code
        """,
        (business_id, date_from, date_to),
    )

    income_items = []
    expense_items = []
    total_income = 0
    total_expenses = 0

    for row in rows:
        item = {
            "account_code": row["account_code"],
            "account_name": row["account_name"] or row["account_code"],
            "total_pesewas": int(row["total_pesewas"]),
            "transaction_count": int(row["transaction_count"]),
        }

        if row["type"] == "INCOME":
            income_items.append(item)
            total_income += item["total_pesewas"]
        elif row["type"] == "EXPENSE":
            expense_items.append(item)
            total_expenses += item["total_pesewas"]

    net_income = total_income - total_expenses

    return {
        "report_type": "profit_and_loss",
        "business_id": business_id,
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
        "revenue": {
            "items": income_items,
            "total_pesewas": total_income,
        },
        "expenses": {
            "items": expense_items,
            "total_pesewas": total_expenses,
        },
        "net_income_pesewas": net_income,
        "currency": "GHS",
    }


def profit_and_loss_trend(business_id: str, months: int = 6) -> list[dict]:
    """Generate month-over-month P&L summary for trend display."""
    rows = query(
        """
        SELECT
            DATE_TRUNC('month', t.transaction_date) AS month,
            t.type,
            SUM(t.amount_pesewas) AS total_pesewas
        FROM transactions t
        WHERE t.business_id = %s
            AND t.transaction_date >= (CURRENT_DATE - (%s * INTERVAL '1 month'))
        GROUP BY DATE_TRUNC('month', t.transaction_date), t.type
        ORDER BY month
        """,
        (business_id, months),
    )

    months_data = {}
    for row in rows:
        month_key = row["month"].strftime("%Y-%m")
        if month_key not in months_data:
            months_data[month_key] = {"month": month_key, "income_pesewas": 0, "expense_pesewas": 0}

        if row["type"] == "INCOME":
            months_data[month_key]["income_pesewas"] = int(row["total_pesewas"])
        elif row["type"] == "EXPENSE":
            months_data[month_key]["expense_pesewas"] = int(row["total_pesewas"])

    result = []
    for month_data in sorted(months_data.values(), key=lambda x: x["month"]):
        month_data["net_income_pesewas"] = month_data["income_pesewas"] - month_data["expense_pesewas"]
        result.append(month_data)

    return result
