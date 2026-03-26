-- BizPulse AI — Seed Data
-- IFRS-aligned chart of accounts (system defaults) + GRA tax rates
--
-- HUMAN-GATED: Founder must verify GRA rates against https://gra.gov.gh
-- before running this migration in production.

-- ============================================================
-- CHART OF ACCOUNTS — System Defaults (IFRS-aligned for Ghanaian SMEs)
-- business_id = NULL means these are system-wide defaults
-- Tenants can override by creating accounts with their own business_id
-- ============================================================

-- INCOME accounts
INSERT INTO chart_of_accounts (account_code, account_name, account_type, is_system_default) VALUES
('4000', 'Revenue',              'income',  TRUE),
('4100', 'Sales Revenue',        'income',  TRUE),
('4200', 'Service Revenue',      'income',  TRUE),
('4300', 'Interest Income',      'income',  TRUE),
('4400', 'Other Income',         'income',  TRUE);

-- EXPENSE accounts
INSERT INTO chart_of_accounts (account_code, account_name, account_type, is_system_default) VALUES
('5000', 'Cost of Goods Sold',   'expense', TRUE),
('5100', 'Direct Materials',     'expense', TRUE),
('5200', 'Direct Labour',        'expense', TRUE),
('6000', 'Operating Expenses',   'expense', TRUE),
('6100', 'Rent & Utilities',     'expense', TRUE),
('6200', 'Salaries & Wages',     'expense', TRUE),
('6300', 'Marketing & Advertising', 'expense', TRUE),
('6400', 'Office Supplies',      'expense', TRUE),
('6500', 'Transportation',       'expense', TRUE),
('6600', 'Insurance',            'expense', TRUE),
('6700', 'Professional Fees',    'expense', TRUE),
('6800', 'Depreciation',         'expense', TRUE),
('6900', 'Bank Charges',         'expense', TRUE),
('7000', 'Taxes & Levies',       'expense', TRUE),
('7100', 'Miscellaneous Expenses', 'expense', TRUE);

-- ASSET accounts (needed for future balance sheet, included for completeness)
INSERT INTO chart_of_accounts (account_code, account_name, account_type, is_system_default) VALUES
('1000', 'Cash & Bank',          'asset',   TRUE),
('1100', 'Accounts Receivable',  'asset',   TRUE),
('1200', 'Inventory',            'asset',   TRUE),
('1300', 'Prepaid Expenses',     'asset',   TRUE),
('1500', 'Fixed Assets',         'asset',   TRUE);

-- LIABILITY accounts
INSERT INTO chart_of_accounts (account_code, account_name, account_type, is_system_default) VALUES
('2000', 'Accounts Payable',     'liability', TRUE),
('2100', 'Accrued Expenses',     'liability', TRUE),
('2200', 'VAT Payable',          'liability', TRUE),
('2300', 'PAYE Payable',         'liability', TRUE),
('2400', 'Loans Payable',        'liability', TRUE);

-- EQUITY accounts
INSERT INTO chart_of_accounts (account_code, account_name, account_type, is_system_default) VALUES
('3000', 'Owner Equity',         'equity',  TRUE),
('3100', 'Retained Earnings',    'equity',  TRUE);

-- ============================================================
-- GRA TAX RATES — National Defaults (COMPLIANCE_MATRIX.md CM-019 to CM-024)
-- All rates in basis points: 1500 = 15.00%
--
-- ⚠️  HUMAN VERIFICATION REQUIRED before production use:
--     Check current rates at https://gra.gov.gh
--     Last verified: [FOUNDER MUST FILL DATE]
-- ============================================================

-- VAT (CM-021) — Standard rate 15% (12.5% VAT + 2.5% combined levy)
INSERT INTO compliance_rates (rate_type, rate_code, jurisdiction, percentage_basis_points, effective_from, source_reference) VALUES
('VAT', 'VAT_STANDARD', 'GH', 1500, '2023-01-01', 'GRA VAT Act 2013 (Act 870) as amended');

-- NHIL + GETFund Levy (CM-019) — Combined 2.5%
INSERT INTO compliance_rates (rate_type, rate_code, jurisdiction, percentage_basis_points, effective_from, source_reference) VALUES
('NHIL_GETFUND', 'NHIL', 'GH', 250, '2023-01-01', 'NHIL Act 2003 (Act 650)'),
('NHIL_GETFUND', 'GETFUND', 'GH', 250, '2023-01-01', 'GETFund Act 2000 (Act 581)');

-- CIT (CM-024) — Standard rate 25%
INSERT INTO compliance_rates (rate_type, rate_code, jurisdiction, percentage_basis_points, effective_from, source_reference) VALUES
('CIT', 'CIT_STANDARD', 'GH', 2500, '2023-01-01', 'Income Tax Act 2015 (Act 896)');

-- PAYE Brackets (CM-022) — Progressive rates
INSERT INTO compliance_rates (rate_type, rate_code, jurisdiction, percentage_basis_points, effective_from, applies_to_transaction_type, source_reference) VALUES
('PAYE', 'PAYE_BAND_1', 'GH', 0,    '2023-01-01', 'First GHS 402/month',        'Income Tax Act 2015 (Act 896)'),
('PAYE', 'PAYE_BAND_2', 'GH', 500,  '2023-01-01', 'Next GHS 110/month',         'Income Tax Act 2015 (Act 896)'),
('PAYE', 'PAYE_BAND_3', 'GH', 1000, '2023-01-01', 'Next GHS 130/month',         'Income Tax Act 2015 (Act 896)'),
('PAYE', 'PAYE_BAND_4', 'GH', 1750, '2023-01-01', 'Next GHS 3,000/month',       'Income Tax Act 2015 (Act 896)'),
('PAYE', 'PAYE_BAND_5', 'GH', 2500, '2023-01-01', 'Next GHS 16,395/month',      'Income Tax Act 2015 (Act 896)'),
('PAYE', 'PAYE_BAND_6', 'GH', 3000, '2023-01-01', 'Exceeding GHS 20,037/month', 'Income Tax Act 2015 (Act 896)');

-- WHT (CM-023) — Common withholding rates
INSERT INTO compliance_rates (rate_type, rate_code, jurisdiction, percentage_basis_points, effective_from, applies_to_transaction_type, source_reference) VALUES
('WHT', 'WHT_GENERAL',      'GH', 300,  '2023-01-01', 'General supply of goods/services',   'Income Tax Act 2015 (Act 896)'),
('WHT', 'WHT_PROFESSIONAL', 'GH', 1500, '2023-01-01', 'Professional/technical services',     'Income Tax Act 2015 (Act 896)'),
('WHT', 'WHT_RENT',         'GH', 800,  '2023-01-01', 'Rent payments',                       'Income Tax Act 2015 (Act 896)');
