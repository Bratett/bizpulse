-- BizPulse AI — Employee & Payroll Tables
-- Supports employee management and PAYE payroll computation records.
-- All monetary values in pesewas (BIGINT).

CREATE TABLE employees (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id      UUID NOT NULL REFERENCES businesses(id),
    employee_number  TEXT,
    first_name       TEXT NOT NULL,
    last_name        TEXT NOT NULL,
    tin              TEXT,
    ssnit_number     TEXT,
    status           TEXT NOT NULL DEFAULT 'active'
                     CHECK (status IN ('active', 'terminated', 'on_leave')),
    hire_date        DATE NOT NULL,
    termination_date DATE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (business_id, employee_number)
);

CREATE INDEX idx_emp_business ON employees(business_id);
CREATE INDEX idx_emp_status ON employees(business_id, status);

CREATE TABLE payroll_records (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id             UUID NOT NULL REFERENCES businesses(id),
    employee_id             UUID NOT NULL REFERENCES employees(id),
    period_year             INTEGER NOT NULL,
    period_month            INTEGER NOT NULL CHECK (period_month BETWEEN 1 AND 12),
    gross_salary_pesewas    BIGINT NOT NULL CHECK (gross_salary_pesewas >= 0),
    ssnit_employee_pesewas  BIGINT NOT NULL DEFAULT 0,
    paye_pesewas            BIGINT NOT NULL DEFAULT 0,
    net_salary_pesewas      BIGINT NOT NULL DEFAULT 0,
    computation_details     JSONB,
    status                  TEXT NOT NULL DEFAULT 'DRAFT'
                            CHECK (status IN ('DRAFT', 'COMPUTED', 'APPROVED', 'PAID')),
    computed_at             TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, period_year, period_month)
);

CREATE INDEX idx_pr_business ON payroll_records(business_id);
CREATE INDEX idx_pr_employee ON payroll_records(employee_id);
CREATE INDEX idx_pr_period ON payroll_records(business_id, period_year, period_month);

GRANT SELECT ON employees TO bizpulse_readonly;
GRANT SELECT ON payroll_records TO bizpulse_readonly;
