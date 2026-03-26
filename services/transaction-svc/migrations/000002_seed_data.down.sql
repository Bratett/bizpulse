-- Reverse seed data
DELETE FROM compliance_rates WHERE created_by_user_id IS NULL;
DELETE FROM chart_of_accounts WHERE is_system_default = TRUE;
