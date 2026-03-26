"""Unit tests for P&L report generation and trend analysis.

Tests use deterministic financial fixtures to verify pesewa-accurate calculations.
All monetary values are in pesewas (1 GHS = 100 pesewas).
"""

from datetime import date, datetime
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures — mock data simulating query results from the transactions table
# ---------------------------------------------------------------------------

MOCK_TRANSACTIONS = [
    {
        "type": "INCOME",
        "account_code": "4100",
        "account_name": "Sales Revenue",
        "total_pesewas": 500000,  # GHS 5,000.00
        "transaction_count": 10,
    },
    {
        "type": "INCOME",
        "account_code": "4200",
        "account_name": "Service Revenue",
        "total_pesewas": 150000,  # GHS 1,500.00
        "transaction_count": 3,
    },
    {
        "type": "EXPENSE",
        "account_code": "6100",
        "account_name": "Rent & Utilities",
        "total_pesewas": 120000,  # GHS 1,200.00
        "transaction_count": 2,
    },
    {
        "type": "EXPENSE",
        "account_code": "6200",
        "account_name": "Salaries & Wages",
        "total_pesewas": 200000,  # GHS 2,000.00
        "transaction_count": 1,
    },
    {
        "type": "EXPENSE",
        "account_code": "6500",
        "account_name": "Transportation",
        "total_pesewas": 30000,  # GHS 300.00
        "transaction_count": 5,
    },
]


# ===================================================================
# Profit & Loss — basic tests
# ===================================================================


@patch("reports.query")
def test_profit_and_loss_basic(mock_query):
    """Given known transactions, P&L should match expected values exactly."""
    from reports import profit_and_loss

    mock_query.return_value = MOCK_TRANSACTIONS

    result = profit_and_loss(
        business_id="test-biz-id",
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 31),
    )

    # Revenue = 500000 + 150000 = 650000 pesewas (GHS 6,500.00)
    assert result["revenue"]["total_pesewas"] == 650000
    assert len(result["revenue"]["items"]) == 2

    # Expenses = 120000 + 200000 + 30000 = 350000 pesewas (GHS 3,500.00)
    assert result["expenses"]["total_pesewas"] == 350000
    assert len(result["expenses"]["items"]) == 3

    # Net Income = 650000 - 350000 = 300000 pesewas (GHS 3,000.00)
    assert result["net_income_pesewas"] == 300000

    assert result["currency"] == "GHS"
    assert result["report_type"] == "profit_and_loss"


@patch("reports.query")
def test_profit_and_loss_no_transactions(mock_query):
    """P&L with no transactions should show zero revenue, expenses, and net income."""
    from reports import profit_and_loss

    mock_query.return_value = []

    result = profit_and_loss(
        business_id="empty-biz",
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
    )

    assert result["revenue"]["total_pesewas"] == 0
    assert result["expenses"]["total_pesewas"] == 0
    assert result["net_income_pesewas"] == 0
    assert result["revenue"]["items"] == []
    assert result["expenses"]["items"] == []


@patch("reports.query")
def test_profit_and_loss_expenses_exceed_revenue(mock_query):
    """When expenses exceed revenue, net income should be negative."""
    from reports import profit_and_loss

    mock_query.return_value = [
        {
            "type": "INCOME",
            "account_code": "4100",
            "account_name": "Sales Revenue",
            "total_pesewas": 100000,  # GHS 1,000.00
            "transaction_count": 2,
        },
        {
            "type": "EXPENSE",
            "account_code": "6200",
            "account_name": "Salaries & Wages",
            "total_pesewas": 250000,  # GHS 2,500.00
            "transaction_count": 1,
        },
    ]

    result = profit_and_loss(
        business_id="loss-biz",
        date_from=date(2026, 2, 1),
        date_to=date(2026, 2, 28),
    )

    assert result["net_income_pesewas"] == -150000  # GHS -1,500.00 loss


@patch("reports.query")
def test_profit_and_loss_pesewa_accuracy(mock_query):
    """Verify exact pesewa values — no floating point drift."""
    from reports import profit_and_loss

    mock_query.return_value = [
        {
            "type": "INCOME",
            "account_code": "4100",
            "account_name": "Sales Revenue",
            "total_pesewas": 1,  # 1 pesewa = GHS 0.01
            "transaction_count": 1,
        },
        {
            "type": "EXPENSE",
            "account_code": "6900",
            "account_name": "Bank Charges",
            "total_pesewas": 1,  # 1 pesewa
            "transaction_count": 1,
        },
    ]

    result = profit_and_loss(
        business_id="penny-biz",
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )

    assert result["revenue"]["total_pesewas"] == 1
    assert result["expenses"]["total_pesewas"] == 1
    assert result["net_income_pesewas"] == 0  # exact zero, no float drift


# ===================================================================
# Profit & Loss — JOIN deduplication (business-specific vs system default)
# ===================================================================


@patch("reports.query")
def test_profit_and_loss_business_override_system_account(mock_query):
    """When a business has overridden a system-default account code, the query's
    COALESCE + conditional JOIN should prefer the business-specific name and
    NOT double-count the amount.

    Scenario: account_code 4100 has a system default name "General Sales" and
    a business-specific name "Ama's Provisions Revenue". The SQL uses a LEFT JOIN
    with `biz_coa.id IS NULL` guard on the system JOIN so only one row appears.
    We simulate the already-deduplicated query output to verify the Python layer
    handles it correctly.
    """
    from reports import profit_and_loss

    mock_query.return_value = [
        {
            "type": "INCOME",
            "account_code": "4100",
            "account_name": "Ama's Provisions Revenue",  # business override
            "total_pesewas": 800000,  # GHS 8,000.00
            "transaction_count": 15,
        },
        {
            "type": "INCOME",
            "account_code": "4200",
            "account_name": "Delivery Fees",  # system default (no override)
            "total_pesewas": 45000,  # GHS 450.00
            "transaction_count": 9,
        },
        {
            "type": "EXPENSE",
            "account_code": "6100",
            "account_name": "Kumasi Market Stall Rent",  # business override
            "total_pesewas": 200000,  # GHS 2,000.00
            "transaction_count": 1,
        },
    ]

    result = profit_and_loss(
        business_id="ama-provisions-001",
        date_from=date(2026, 1, 1),
        date_to=date(2026, 3, 31),
    )

    # Should see exactly 2 income items, not duplicated by the JOIN
    assert len(result["revenue"]["items"]) == 2
    assert result["revenue"]["total_pesewas"] == 845000  # 800000 + 45000

    # Verify business-specific name is used
    names = [item["account_name"] for item in result["revenue"]["items"]]
    assert "Ama's Provisions Revenue" in names
    assert "Delivery Fees" in names

    # Expense side
    assert len(result["expenses"]["items"]) == 1
    assert result["expenses"]["items"][0]["account_name"] == "Kumasi Market Stall Rent"
    assert result["expenses"]["total_pesewas"] == 200000

    # Net income
    assert result["net_income_pesewas"] == 645000  # 845000 - 200000


# ===================================================================
# Profit & Loss — large BIGINT amounts
# ===================================================================


@patch("reports.query")
def test_profit_and_loss_large_bigint_amounts(mock_query):
    """Verify P&L handles amounts near the BIGINT boundary without overflow.

    PostgreSQL BIGINT max is 9,223,372,036,854,775,807.
    A large Ghanaian enterprise might process billions of cedis. This test uses
    amounts in the trillions-of-pesewas range to stress the Python int arithmetic.
    """
    from reports import profit_and_loss

    # ~92 billion GHS in pesewas — well within BIGINT but large enough to
    # catch any accidental float conversion or 32-bit int truncation.
    large_income = 9_200_000_000_000  # 9.2 trillion pesewas = GHS 92 billion
    large_expense = 8_100_000_000_000  # 8.1 trillion pesewas = GHS 81 billion

    mock_query.return_value = [
        {
            "type": "INCOME",
            "account_code": "4100",
            "account_name": "Bulk Commodity Sales",
            "total_pesewas": large_income,
            "transaction_count": 500000,
        },
        {
            "type": "EXPENSE",
            "account_code": "6100",
            "account_name": "Import Duties & Logistics",
            "total_pesewas": large_expense,
            "transaction_count": 250000,
        },
    ]

    result = profit_and_loss(
        business_id="large-enterprise-gh",
        date_from=date(2025, 1, 1),
        date_to=date(2025, 12, 31),
    )

    assert result["revenue"]["total_pesewas"] == large_income
    assert result["expenses"]["total_pesewas"] == large_expense
    assert result["net_income_pesewas"] == large_income - large_expense
    assert result["net_income_pesewas"] == 1_100_000_000_000

    # Verify the values are Python ints, not floats
    assert isinstance(result["revenue"]["total_pesewas"], int)
    assert isinstance(result["expenses"]["total_pesewas"], int)
    assert isinstance(result["net_income_pesewas"], int)


@patch("reports.query")
def test_profit_and_loss_near_max_bigint(mock_query):
    """Edge case: amounts approaching PostgreSQL BIGINT max.

    Python handles arbitrary precision, but we want to confirm no accidental
    truncation or type coercion.
    """
    from reports import profit_and_loss

    near_max = 9_223_372_036_854_775_000  # just under BIGINT max
    smaller = 1_000_000_000_000

    mock_query.return_value = [
        {
            "type": "INCOME",
            "account_code": "4100",
            "account_name": "Mega Revenue",
            "total_pesewas": near_max,
            "transaction_count": 1,
        },
        {
            "type": "EXPENSE",
            "account_code": "6100",
            "account_name": "Mega Cost",
            "total_pesewas": smaller,
            "transaction_count": 1,
        },
    ]

    result = profit_and_loss(
        business_id="stress-test-biz",
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
    )

    assert result["revenue"]["total_pesewas"] == near_max
    assert result["expenses"]["total_pesewas"] == smaller
    assert result["net_income_pesewas"] == near_max - smaller
    assert isinstance(result["net_income_pesewas"], int)


# ===================================================================
# Profit & Loss — period metadata
# ===================================================================


@patch("reports.query")
def test_profit_and_loss_period_metadata(mock_query):
    """P&L report should include correct business_id and period dates."""
    from reports import profit_and_loss

    mock_query.return_value = MOCK_TRANSACTIONS

    result = profit_and_loss(
        business_id="kwame-electronics-002",
        date_from=date(2026, 2, 1),
        date_to=date(2026, 2, 28),
    )

    assert result["business_id"] == "kwame-electronics-002"
    assert result["period"]["from"] == "2026-02-01"
    assert result["period"]["to"] == "2026-02-28"


# ===================================================================
# profit_and_loss_trend tests
# ===================================================================


@patch("reports.query")
def test_trend_three_months_data(mock_query):
    """Trend with 3 months of data returns 3 monthly entries with correct
    income, expense, and net income calculations."""
    from reports import profit_and_loss_trend

    mock_query.return_value = [
        # January 2026 — income
        {
            "month": datetime(2026, 1, 1),
            "type": "INCOME",
            "total_pesewas": 300000,  # GHS 3,000
        },
        # January 2026 — expense
        {
            "month": datetime(2026, 1, 1),
            "type": "EXPENSE",
            "total_pesewas": 180000,  # GHS 1,800
        },
        # February 2026 — income
        {
            "month": datetime(2026, 2, 1),
            "type": "INCOME",
            "total_pesewas": 450000,  # GHS 4,500
        },
        # February 2026 — expense
        {
            "month": datetime(2026, 2, 1),
            "type": "EXPENSE",
            "total_pesewas": 200000,  # GHS 2,000
        },
        # March 2026 — income
        {
            "month": datetime(2026, 3, 1),
            "type": "INCOME",
            "total_pesewas": 620000,  # GHS 6,200
        },
        # March 2026 — expense
        {
            "month": datetime(2026, 3, 1),
            "type": "EXPENSE",
            "total_pesewas": 310000,  # GHS 3,100
        },
    ]

    result = profit_and_loss_trend(business_id="trend-biz-001", months=3)

    assert len(result) == 3

    # January
    assert result[0]["month"] == "2026-01"
    assert result[0]["income_pesewas"] == 300000
    assert result[0]["expense_pesewas"] == 180000
    assert result[0]["net_income_pesewas"] == 120000

    # February
    assert result[1]["month"] == "2026-02"
    assert result[1]["income_pesewas"] == 450000
    assert result[1]["expense_pesewas"] == 200000
    assert result[1]["net_income_pesewas"] == 250000

    # March
    assert result[2]["month"] == "2026-03"
    assert result[2]["income_pesewas"] == 620000
    assert result[2]["expense_pesewas"] == 310000
    assert result[2]["net_income_pesewas"] == 310000

    # Verify correct SQL params were passed
    mock_query.assert_called_once()
    call_args = mock_query.call_args
    assert call_args[0][1] == ("trend-biz-001", 3)


@patch("reports.query")
def test_trend_no_data(mock_query):
    """Trend with no transaction data returns an empty list."""
    from reports import profit_and_loss_trend

    mock_query.return_value = []

    result = profit_and_loss_trend(business_id="dormant-biz-gh", months=6)

    assert result == []
    assert isinstance(result, list)


@patch("reports.query")
def test_trend_single_month(mock_query):
    """Trend with data in only one month returns a single entry."""
    from reports import profit_and_loss_trend

    mock_query.return_value = [
        {
            "month": datetime(2026, 3, 1),
            "type": "INCOME",
            "total_pesewas": 750000,  # GHS 7,500
        },
        {
            "month": datetime(2026, 3, 1),
            "type": "EXPENSE",
            "total_pesewas": 420000,  # GHS 4,200
        },
    ]

    result = profit_and_loss_trend(business_id="single-month-biz", months=1)

    assert len(result) == 1
    assert result[0]["month"] == "2026-03"
    assert result[0]["income_pesewas"] == 750000
    assert result[0]["expense_pesewas"] == 420000
    assert result[0]["net_income_pesewas"] == 330000


@patch("reports.query")
def test_trend_month_boundary(mock_query):
    """Transactions on the last day of one month vs. the first day of the next
    should land in their respective monthly buckets (DATE_TRUNC behavior)."""
    from reports import profit_and_loss_trend

    mock_query.return_value = [
        # Last day of February — truncated to 2026-02-01
        {
            "month": datetime(2026, 2, 1),
            "type": "INCOME",
            "total_pesewas": 100000,  # GHS 1,000
        },
        # First day of March — truncated to 2026-03-01
        {
            "month": datetime(2026, 3, 1),
            "type": "INCOME",
            "total_pesewas": 200000,  # GHS 2,000
        },
        # Expense in February
        {
            "month": datetime(2026, 2, 1),
            "type": "EXPENSE",
            "total_pesewas": 50000,  # GHS 500
        },
        # Expense in March
        {
            "month": datetime(2026, 3, 1),
            "type": "EXPENSE",
            "total_pesewas": 75000,  # GHS 750
        },
    ]

    result = profit_and_loss_trend(business_id="boundary-biz", months=2)

    assert len(result) == 2

    # February entry (transactions from Feb 28 go here via DATE_TRUNC)
    feb = result[0]
    assert feb["month"] == "2026-02"
    assert feb["income_pesewas"] == 100000
    assert feb["expense_pesewas"] == 50000
    assert feb["net_income_pesewas"] == 50000

    # March entry (transactions from Mar 1 go here)
    mar = result[1]
    assert mar["month"] == "2026-03"
    assert mar["income_pesewas"] == 200000
    assert mar["expense_pesewas"] == 75000
    assert mar["net_income_pesewas"] == 125000


@patch("reports.query")
def test_trend_income_only_month(mock_query):
    """A month with only income and no expenses should show zero expenses."""
    from reports import profit_and_loss_trend

    mock_query.return_value = [
        {
            "month": datetime(2026, 1, 1),
            "type": "INCOME",
            "total_pesewas": 500000,
        },
    ]

    result = profit_and_loss_trend(business_id="income-only-biz", months=1)

    assert len(result) == 1
    assert result[0]["income_pesewas"] == 500000
    assert result[0]["expense_pesewas"] == 0
    assert result[0]["net_income_pesewas"] == 500000


@patch("reports.query")
def test_trend_results_sorted_chronologically(mock_query):
    """Trend results should be sorted by month ascending even if query returns
    them in a different order."""
    from reports import profit_and_loss_trend

    # Return March before January to verify sorting
    mock_query.return_value = [
        {
            "month": datetime(2026, 3, 1),
            "type": "INCOME",
            "total_pesewas": 300000,
        },
        {
            "month": datetime(2026, 1, 1),
            "type": "INCOME",
            "total_pesewas": 100000,
        },
        {
            "month": datetime(2026, 2, 1),
            "type": "INCOME",
            "total_pesewas": 200000,
        },
    ]

    result = profit_and_loss_trend(business_id="sort-test-biz", months=3)

    months = [entry["month"] for entry in result]
    assert months == ["2026-01", "2026-02", "2026-03"]
