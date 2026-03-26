"""Tests for BizPulse AI Tax Computation Engine.

Covers: VAT, NHIL/GETFund, CIT, WHT computation logic.
All amounts in pesewas. Rates in basis points.
"""

import pytest
from datetime import date

from tax_engine import (
    apply_rate_bps,
    compute_all_taxes,
    compute_cit,
    compute_nhil_getfund,
    compute_paye,
    compute_vat,
    compute_wht,
    find_effective_rate,
    find_rates_by_type,
    sum_transactions,
)

# ============================================================
# Test fixtures — GRA tax rates matching seed data
# ============================================================

SAMPLE_RATES = [
    {"rate_type": "VAT", "rate_code": "VAT_STANDARD", "percentage_basis_points": 1500,
     "effective_from": date(2023, 1, 1), "effective_to": None},
    {"rate_type": "NHIL_GETFUND", "rate_code": "NHIL", "percentage_basis_points": 250,
     "effective_from": date(2023, 1, 1), "effective_to": None},
    {"rate_type": "NHIL_GETFUND", "rate_code": "GETFUND", "percentage_basis_points": 250,
     "effective_from": date(2023, 1, 1), "effective_to": None},
    {"rate_type": "CIT", "rate_code": "CIT_STANDARD", "percentage_basis_points": 2500,
     "effective_from": date(2023, 1, 1), "effective_to": None},
    {"rate_type": "WHT", "rate_code": "WHT_GENERAL", "percentage_basis_points": 300,
     "effective_from": date(2023, 1, 1), "effective_to": None},
]

EXPIRED_RATE = {
    "rate_type": "VAT", "rate_code": "VAT_STANDARD", "percentage_basis_points": 1250,
    "effective_from": date(2020, 1, 1), "effective_to": date(2022, 12, 31),
}

SAMPLE_TRANSACTIONS = [
    {"type": "INCOME", "amount_pesewas": 100000, "tax_category": "STANDARD_RATED"},  # GHS 1,000
    {"type": "INCOME", "amount_pesewas": 50000, "tax_category": "STANDARD_RATED"},   # GHS 500
    {"type": "INCOME", "amount_pesewas": 20000, "tax_category": "ZERO_RATED"},       # GHS 200 (zero-rated)
    {"type": "EXPENSE", "amount_pesewas": 30000, "tax_category": "STANDARD_RATED"},  # GHS 300
    {"type": "EXPENSE", "amount_pesewas": 10000, "tax_category": "EXEMPT"},          # GHS 100 (exempt)
    {"type": "EXPENSE", "amount_pesewas": 5000, "tax_category": "NON_DEDUCTIBLE"},   # GHS 50 (non-deductible)
]

AS_OF = date(2026, 3, 1)


# ============================================================
# apply_rate_bps
# ============================================================

class TestApplyRateBps:
    def test_standard_vat(self):
        # 15% of GHS 1,000 (100,000 pesewas) = GHS 150 (15,000 pesewas)
        assert apply_rate_bps(100000, 1500) == 15000

    def test_nhil_levy(self):
        # 2.5% of GHS 1,000 = GHS 25
        assert apply_rate_bps(100000, 250) == 2500

    def test_cit_rate(self):
        # 25% of GHS 10,000 = GHS 2,500
        assert apply_rate_bps(1000000, 2500) == 250000

    def test_zero_amount(self):
        assert apply_rate_bps(0, 1500) == 0

    def test_zero_rate(self):
        assert apply_rate_bps(100000, 0) == 0

    def test_small_amount_rounding(self):
        # 15% of 1 pesewa = 0 (rounds down)
        assert apply_rate_bps(1, 1500) == 0

    def test_rounding_truncates(self):
        # 15% of 99 pesewas = 14.85 → 14 (truncated)
        assert apply_rate_bps(99, 1500) == 14

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError):
            apply_rate_bps(-100, 1500)

    def test_negative_rate_raises(self):
        with pytest.raises(ValueError):
            apply_rate_bps(100, -1500)


# ============================================================
# find_effective_rate
# ============================================================

class TestFindEffectiveRate:
    def test_finds_current_rate(self):
        rate = find_effective_rate(SAMPLE_RATES, "VAT", "VAT_STANDARD", AS_OF)
        assert rate is not None
        assert rate["percentage_basis_points"] == 1500

    def test_returns_none_for_unknown_type(self):
        rate = find_effective_rate(SAMPLE_RATES, "UNKNOWN", "UNKNOWN", AS_OF)
        assert rate is None

    def test_excludes_expired_rate(self):
        rates = SAMPLE_RATES + [EXPIRED_RATE]
        rate = find_effective_rate(rates, "VAT", "VAT_STANDARD", AS_OF)
        assert rate["percentage_basis_points"] == 1500  # current, not expired

    def test_finds_rate_within_expired_period(self):
        rate = find_effective_rate([EXPIRED_RATE], "VAT", "VAT_STANDARD", date(2021, 6, 15))
        assert rate is not None
        assert rate["percentage_basis_points"] == 1250

    def test_excludes_future_rate(self):
        future_rate = {"rate_type": "VAT", "rate_code": "VAT_STANDARD",
                       "percentage_basis_points": 2000,
                       "effective_from": date(2030, 1, 1), "effective_to": None}
        rate = find_effective_rate([future_rate], "VAT", "VAT_STANDARD", AS_OF)
        assert rate is None

    def test_rate_on_effective_from_date(self):
        rate = find_effective_rate(SAMPLE_RATES, "VAT", "VAT_STANDARD", date(2023, 1, 1))
        assert rate is not None

    def test_rate_on_effective_to_date(self):
        rate = find_effective_rate([EXPIRED_RATE], "VAT", "VAT_STANDARD", date(2022, 12, 31))
        assert rate is not None


# ============================================================
# find_rates_by_type
# ============================================================

class TestFindRatesByType:
    def test_finds_both_nhil_getfund(self):
        rates = find_rates_by_type(SAMPLE_RATES, "NHIL_GETFUND", AS_OF)
        assert len(rates) == 2
        codes = {r["rate_code"] for r in rates}
        assert codes == {"NHIL", "GETFUND"}

    def test_single_vat_rate(self):
        rates = find_rates_by_type(SAMPLE_RATES, "VAT", AS_OF)
        assert len(rates) == 1

    def test_empty_for_unknown_type(self):
        rates = find_rates_by_type(SAMPLE_RATES, "UNKNOWN", AS_OF)
        assert len(rates) == 0


# ============================================================
# sum_transactions
# ============================================================

class TestSumTransactions:
    def test_standard_rated_income(self):
        total = sum_transactions(SAMPLE_TRANSACTIONS, "INCOME", "STANDARD_RATED")
        assert total == 150000  # 100000 + 50000

    def test_zero_rated_income(self):
        total = sum_transactions(SAMPLE_TRANSACTIONS, "INCOME", "ZERO_RATED")
        assert total == 20000

    def test_standard_rated_expense(self):
        total = sum_transactions(SAMPLE_TRANSACTIONS, "EXPENSE", "STANDARD_RATED")
        assert total == 30000

    def test_non_deductible_expense(self):
        total = sum_transactions(SAMPLE_TRANSACTIONS, "EXPENSE", "NON_DEDUCTIBLE")
        assert total == 5000

    def test_empty_transactions(self):
        total = sum_transactions([], "INCOME", "STANDARD_RATED")
        assert total == 0

    def test_default_category(self):
        # Transaction without tax_category defaults to STANDARD_RATED
        txns = [{"type": "INCOME", "amount_pesewas": 10000}]
        total = sum_transactions(txns, "INCOME", "STANDARD_RATED")
        assert total == 10000


# ============================================================
# compute_vat
# ============================================================

class TestComputeVat:
    def test_basic_vat_computation(self):
        result = compute_vat(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF)
        assert result["taxable_sales_pesewas"] == 150000
        assert result["output_vat_pesewas"] == 22500  # 15% of 150,000
        assert result["taxable_purchases_pesewas"] == 30000
        assert result["input_vat_pesewas"] == 4500  # 15% of 30,000
        assert result["net_vat_pesewas"] == 18000  # 22,500 - 4,500
        assert result["rate_bps"] == 1500

    def test_vat_no_transactions(self):
        result = compute_vat([], SAMPLE_RATES, AS_OF)
        assert result["net_vat_pesewas"] == 0

    def test_vat_no_rate(self):
        result = compute_vat(SAMPLE_TRANSACTIONS, [], AS_OF)
        assert "error" in result

    def test_vat_only_exempt_transactions(self):
        txns = [{"type": "INCOME", "amount_pesewas": 100000, "tax_category": "EXEMPT"}]
        result = compute_vat(txns, SAMPLE_RATES, AS_OF)
        assert result["output_vat_pesewas"] == 0

    def test_vat_negative_net_when_more_purchases(self):
        txns = [
            {"type": "INCOME", "amount_pesewas": 10000, "tax_category": "STANDARD_RATED"},
            {"type": "EXPENSE", "amount_pesewas": 50000, "tax_category": "STANDARD_RATED"},
        ]
        result = compute_vat(txns, SAMPLE_RATES, AS_OF)
        assert result["net_vat_pesewas"] < 0  # Refund position


# ============================================================
# compute_nhil_getfund
# ============================================================

class TestComputeNhilGetfund:
    def test_both_levies_summed(self):
        result = compute_nhil_getfund(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF)
        # NHIL 2.5% of 150,000 = 3,750 + GETFund 2.5% of 150,000 = 3,750 = 7,500
        assert result["total_levy_pesewas"] == 7500
        assert len(result["levy_details"]) == 2

    def test_individual_levy_amounts(self):
        result = compute_nhil_getfund(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF)
        for detail in result["levy_details"]:
            assert detail["amount_pesewas"] == 3750  # Each is 2.5% of 150,000

    def test_no_rates(self):
        result = compute_nhil_getfund(SAMPLE_TRANSACTIONS, [], AS_OF)
        assert result["total_levy_pesewas"] == 0

    def test_no_transactions(self):
        result = compute_nhil_getfund([], SAMPLE_RATES, AS_OF)
        assert result["total_levy_pesewas"] == 0


# ============================================================
# compute_cit
# ============================================================

class TestComputeCit:
    def test_basic_cit_computation(self):
        result = compute_cit(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF)
        # Revenue: 100,000 + 50,000 + 20,000 = 170,000
        # Deductible: 30,000 (standard) + 10,000 (exempt) = 40,000
        # Non-deductible: 5,000
        # Net profit: 170,000 - 40,000 = 130,000
        # CIT: 25% of 130,000 = 32,500
        assert result["total_revenue_pesewas"] == 170000
        assert result["total_deductible_expenses_pesewas"] == 40000
        assert result["non_deductible_expenses_pesewas"] == 5000
        assert result["net_profit_pesewas"] == 130000
        assert result["cit_liability_pesewas"] == 32500

    def test_cit_net_loss(self):
        txns = [
            {"type": "INCOME", "amount_pesewas": 10000, "tax_category": "STANDARD_RATED"},
            {"type": "EXPENSE", "amount_pesewas": 50000, "tax_category": "STANDARD_RATED"},
        ]
        result = compute_cit(txns, SAMPLE_RATES, AS_OF)
        assert result["net_profit_pesewas"] == 0  # Clamped to zero
        assert result["cit_liability_pesewas"] == 0

    def test_cit_no_rate(self):
        result = compute_cit(SAMPLE_TRANSACTIONS, [], AS_OF)
        assert "error" in result

    def test_cit_no_transactions(self):
        result = compute_cit([], SAMPLE_RATES, AS_OF)
        assert result["cit_liability_pesewas"] == 0


# ============================================================
# compute_wht
# ============================================================

class TestComputeWht:
    def test_basic_wht_computation(self):
        result = compute_wht(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF)
        # 3% of 30,000 (standard-rated expenses) = 900
        assert result["wht_amount_pesewas"] == 900
        assert result["rate_bps"] == 300

    def test_wht_no_rate(self):
        result = compute_wht(SAMPLE_TRANSACTIONS, [], AS_OF)
        assert "error" in result

    def test_wht_no_expenses(self):
        txns = [{"type": "INCOME", "amount_pesewas": 100000, "tax_category": "STANDARD_RATED"}]
        result = compute_wht(txns, SAMPLE_RATES, AS_OF)
        assert result["wht_amount_pesewas"] == 0


# ============================================================
# compute_all_taxes
# ============================================================

class TestComputeAllTaxes:
    def test_vat_monthly_includes_all_levies(self):
        result = compute_all_taxes(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF, "VAT_MONTHLY")
        assert len(result["computations"]) == 3
        types = {c["type"] for c in result["computations"]}
        assert types == {"VAT", "NHIL_GETFUND", "WHT"}
        assert result["total_liability_pesewas"] > 0

    def test_cit_annual_only_cit(self):
        result = compute_all_taxes(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF, "CIT_ANNUAL")
        assert len(result["computations"]) == 1
        assert result["computations"][0]["type"] == "CIT"

    def test_wht_monthly_only_wht(self):
        result = compute_all_taxes(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF, "WHT_MONTHLY")
        assert len(result["computations"]) == 1
        assert result["computations"][0]["type"] == "WHT"

    def test_unknown_period_type(self):
        result = compute_all_taxes(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF, "UNKNOWN")
        assert "error" in result
        assert result["total_liability_pesewas"] == 0

    def test_vat_monthly_total_correct(self):
        result = compute_all_taxes(SAMPLE_TRANSACTIONS, SAMPLE_RATES, AS_OF, "VAT_MONTHLY")
        # VAT net: 18,000 + NHIL/GETFund: 7,500 + WHT: 900 = 26,400
        assert result["total_liability_pesewas"] == 26400


# ============================================================
# compute_paye — Ghana progressive PAYE tax bands
# ============================================================

# PAYE rates matching seed data (000002_seed_data.up.sql + 000006_paye_band_ceilings.up.sql)
PAYE_RATES = [
    {"rate_type": "PAYE", "rate_code": "PAYE_BAND_1", "percentage_basis_points": 0,
     "band_ceiling_pesewas": 40200,
     "effective_from": date(2023, 1, 1), "effective_to": None},
    {"rate_type": "PAYE", "rate_code": "PAYE_BAND_2", "percentage_basis_points": 500,
     "band_ceiling_pesewas": 11000,
     "effective_from": date(2023, 1, 1), "effective_to": None},
    {"rate_type": "PAYE", "rate_code": "PAYE_BAND_3", "percentage_basis_points": 1000,
     "band_ceiling_pesewas": 13000,
     "effective_from": date(2023, 1, 1), "effective_to": None},
    {"rate_type": "PAYE", "rate_code": "PAYE_BAND_4", "percentage_basis_points": 1750,
     "band_ceiling_pesewas": 300000,
     "effective_from": date(2023, 1, 1), "effective_to": None},
    {"rate_type": "PAYE", "rate_code": "PAYE_BAND_5", "percentage_basis_points": 2500,
     "band_ceiling_pesewas": 1639500,
     "effective_from": date(2023, 1, 1), "effective_to": None},
    {"rate_type": "PAYE", "rate_code": "PAYE_BAND_6", "percentage_basis_points": 3000,
     "band_ceiling_pesewas": None,
     "effective_from": date(2023, 1, 1), "effective_to": None},
]


class TestComputePaye:
    """Tests for PAYE progressive tax band computation.

    Band structure (monthly):
      Band 1: First GHS 402  (40,200 pesewas)  — 0%
      Band 2: Next  GHS 110  (11,000 pesewas)  — 5%
      Band 3: Next  GHS 130  (13,000 pesewas)  — 10%
      Band 4: Next  GHS 3,000 (300,000 pesewas) — 17.5%
      Band 5: Next  GHS 16,395 (1,639,500 pesewas) — 25%
      Band 6: Remainder                         — 30%
    """

    def test_band_1_zero_rate(self):
        """Salary within first GHS 402 = 0% PAYE."""
        # GHS 300 = 30,000 pesewas, entirely in band 1 (0%)
        result = compute_paye(30000, PAYE_RATES, AS_OF)
        assert result["total_paye_pesewas"] == 0
        assert result["gross_salary_pesewas"] == 30000
        assert len(result["band_details"]) == 1
        assert result["band_details"][0]["rate_code"] == "PAYE_BAND_1"
        assert result["band_details"][0]["paye_pesewas"] == 0

    def test_band_2_five_percent(self):
        """Salary entering band 2 at 5%."""
        # GHS 450 = 45,000 pesewas
        # Band 1: 40,200 at 0% = 0
        # Band 2: 4,800 at 5% = 240
        result = compute_paye(45000, PAYE_RATES, AS_OF)
        assert result["total_paye_pesewas"] == 240
        assert len(result["band_details"]) == 2
        assert result["band_details"][1]["rate_code"] == "PAYE_BAND_2"
        assert result["band_details"][1]["taxable_amount_pesewas"] == 4800
        assert result["band_details"][1]["paye_pesewas"] == 240

    def test_band_3_ten_percent(self):
        """Salary entering band 3 at 10%."""
        # GHS 552 = 55,200 pesewas (40,200 + 11,000 + 4,000)
        # Band 1: 40,200 at 0% = 0
        # Band 2: 11,000 at 5% = 550
        # Band 3: 4,000 at 10% = 400
        result = compute_paye(55200, PAYE_RATES, AS_OF)
        assert result["total_paye_pesewas"] == 950
        assert len(result["band_details"]) == 3
        assert result["band_details"][2]["rate_code"] == "PAYE_BAND_3"
        assert result["band_details"][2]["taxable_amount_pesewas"] == 4000
        assert result["band_details"][2]["paye_pesewas"] == 400

    def test_band_4_seventeen_half_percent(self):
        """Salary entering band 4 at 17.5%."""
        # Total through band 3: 40,200 + 11,000 + 13,000 = 64,200
        # Salary = 164,200 pesewas → 100,000 in band 4
        # Band 1: 40,200 at 0% = 0
        # Band 2: 11,000 at 5% = 550
        # Band 3: 13,000 at 10% = 1,300
        # Band 4: 100,000 at 17.5% = 17,500
        result = compute_paye(164200, PAYE_RATES, AS_OF)
        assert result["total_paye_pesewas"] == 0 + 550 + 1300 + 17500
        assert result["total_paye_pesewas"] == 19350
        assert len(result["band_details"]) == 4
        assert result["band_details"][3]["rate_code"] == "PAYE_BAND_4"
        assert result["band_details"][3]["paye_pesewas"] == 17500

    def test_band_5_twentyfive_percent(self):
        """Salary entering band 5 at 25%."""
        # Total through band 4: 64,200 + 300,000 = 364,200
        # Salary = 464,200 pesewas → 100,000 in band 5
        # Band 1: 0
        # Band 2: 550
        # Band 3: 1,300
        # Band 4: 300,000 * 17.5% = 52,500
        # Band 5: 100,000 * 25% = 25,000
        result = compute_paye(464200, PAYE_RATES, AS_OF)
        expected = 0 + 550 + 1300 + 52500 + 25000
        assert result["total_paye_pesewas"] == expected
        assert len(result["band_details"]) == 5

    def test_band_6_thirty_percent(self):
        """Salary exceeding all bands, hitting band 6 at 30%."""
        # Total through band 5: 64,200 + 300,000 + 1,639,500 = 2,003,700
        # Salary = 2,503,700 pesewas → 500,000 in band 6
        # Band 1: 0
        # Band 2: 550
        # Band 3: 1,300
        # Band 4: 52,500
        # Band 5: 1,639,500 * 25% = 409,875
        # Band 6: 500,000 * 30% = 150,000
        result = compute_paye(2503700, PAYE_RATES, AS_OF)
        expected = 0 + 550 + 1300 + 52500 + 409875 + 150000
        assert result["total_paye_pesewas"] == expected
        assert len(result["band_details"]) == 6
        assert result["band_details"][5]["rate_code"] == "PAYE_BAND_6"
        assert result["band_details"][5]["ceiling_pesewas"] is None

    def test_zero_salary(self):
        """Zero salary produces zero PAYE."""
        result = compute_paye(0, PAYE_RATES, AS_OF)
        assert result["total_paye_pesewas"] == 0
        assert result["effective_rate_bps"] == 0
        assert len(result["band_details"]) == 0

    def test_exact_band_boundary(self):
        """Salary exactly at band 1 ceiling."""
        # GHS 402 = 40,200 pesewas — exactly at band 1 ceiling
        result = compute_paye(40200, PAYE_RATES, AS_OF)
        assert result["total_paye_pesewas"] == 0
        assert len(result["band_details"]) == 1
        assert result["band_details"][0]["taxable_amount_pesewas"] == 40200

    def test_exact_band_1_plus_band_2_boundary(self):
        """Salary exactly at band 1 + band 2 ceiling."""
        # 40,200 + 11,000 = 51,200 pesewas
        result = compute_paye(51200, PAYE_RATES, AS_OF)
        assert result["total_paye_pesewas"] == 550  # 11,000 * 5%
        assert len(result["band_details"]) == 2
        assert result["band_details"][1]["taxable_amount_pesewas"] == 11000

    def test_all_bands_used(self):
        """High salary going through all 6 bands."""
        # GHS 50,000/month = 5,000,000 pesewas — well beyond all bands
        salary = 5000000
        result = compute_paye(salary, PAYE_RATES, AS_OF)
        assert len(result["band_details"]) == 6

        # Verify each band's taxable amount
        assert result["band_details"][0]["taxable_amount_pesewas"] == 40200   # Band 1
        assert result["band_details"][1]["taxable_amount_pesewas"] == 11000   # Band 2
        assert result["band_details"][2]["taxable_amount_pesewas"] == 13000   # Band 3
        assert result["band_details"][3]["taxable_amount_pesewas"] == 300000  # Band 4
        assert result["band_details"][4]["taxable_amount_pesewas"] == 1639500 # Band 5

        # Band 6 remainder: 5,000,000 - 2,003,700 = 2,996,300
        assert result["band_details"][5]["taxable_amount_pesewas"] == 2996300

        # Total PAYE
        expected = (
            0                              # Band 1: 0%
            + (11000 * 500) // 10000       # Band 2: 5% = 550
            + (13000 * 1000) // 10000      # Band 3: 10% = 1,300
            + (300000 * 1750) // 10000     # Band 4: 17.5% = 52,500
            + (1639500 * 2500) // 10000    # Band 5: 25% = 409,875
            + (2996300 * 3000) // 10000    # Band 6: 30% = 898,890
        )
        assert result["total_paye_pesewas"] == expected

    def test_no_rates_available(self):
        """No PAYE rates produces zero tax with error message."""
        result = compute_paye(100000, [], AS_OF)
        assert result["total_paye_pesewas"] == 0
        assert "error" in result
        assert result["band_details"] == []

    def test_effective_rate_calculation(self):
        """Effective rate is correctly computed as total_paye / gross * 10000."""
        # GHS 450 = 45,000 pesewas
        # PAYE = 240 pesewas (from test_band_2_five_percent)
        # Effective rate = (240 * 10000) / 45,000 = 53 bps (0.53%)
        result = compute_paye(45000, PAYE_RATES, AS_OF)
        expected_effective = (240 * 10000) // 45000  # = 53
        assert result["effective_rate_bps"] == expected_effective

    def test_band_details_structure(self):
        """Each band detail has the required fields."""
        result = compute_paye(100000, PAYE_RATES, AS_OF)
        for detail in result["band_details"]:
            assert "rate_code" in detail
            assert "ceiling_pesewas" in detail
            assert "taxable_amount_pesewas" in detail
            assert "rate_bps" in detail
            assert "paye_pesewas" in detail

    def test_one_pesewa_above_band_1(self):
        """One pesewa above band 1 ceiling should enter band 2."""
        result = compute_paye(40201, PAYE_RATES, AS_OF)
        assert len(result["band_details"]) == 2
        assert result["band_details"][1]["taxable_amount_pesewas"] == 1
        # 1 pesewa at 5% (500 bps) = 0 (rounds down)
        assert result["band_details"][1]["paye_pesewas"] == 0
        assert result["total_paye_pesewas"] == 0

    def test_expired_paye_rates_excluded(self):
        """Expired PAYE rates should not be used."""
        expired_rates = [
            {"rate_type": "PAYE", "rate_code": "PAYE_BAND_1", "percentage_basis_points": 0,
             "band_ceiling_pesewas": 40200,
             "effective_from": date(2020, 1, 1), "effective_to": date(2022, 12, 31)},
        ]
        result = compute_paye(100000, expired_rates, AS_OF)
        assert result["total_paye_pesewas"] == 0
        assert "error" in result

    def test_effective_rate_high_salary(self):
        """Effective rate increases with higher salaries (progressive)."""
        low_result = compute_paye(45000, PAYE_RATES, AS_OF)
        high_result = compute_paye(5000000, PAYE_RATES, AS_OF)
        # Higher salary should have higher effective rate
        assert high_result["effective_rate_bps"] > low_result["effective_rate_bps"]
