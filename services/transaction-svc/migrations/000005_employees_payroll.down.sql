-- Rollback: Drop employee & payroll tables

DROP INDEX IF EXISTS idx_pr_period;
DROP INDEX IF EXISTS idx_pr_employee;
DROP INDEX IF EXISTS idx_pr_business;
DROP TABLE IF EXISTS payroll_records;

DROP INDEX IF EXISTS idx_emp_status;
DROP INDEX IF EXISTS idx_emp_business;
DROP TABLE IF EXISTS employees;
