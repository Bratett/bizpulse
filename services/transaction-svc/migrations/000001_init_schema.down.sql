-- Reverse initial schema migration
DROP TRIGGER IF EXISTS trg_no_delete_transactions ON transactions;
DROP TRIGGER IF EXISTS trg_no_update_transactions ON transactions;
DROP FUNCTION IF EXISTS prevent_transaction_mutation();

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS compliance_rates;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS chart_of_accounts;
DROP TABLE IF EXISTS consent_records;
DROP TABLE IF EXISTS user_business_memberships;
DROP TABLE IF EXISTS businesses;
DROP TABLE IF EXISTS users;
