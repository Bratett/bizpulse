-- BizPulse AI — Sprint 1: Tax Period Tracking Tables
-- Supports GRA compliance workflow: create period → compute taxes → review → file
-- All monetary values in pesewas (BIGINT). Rates in basis points.

-- ============================================================
-- TAX PERIODS — Track filing cycles (monthly VAT, annual CIT)
-- ============================================================
CREATE TABLE tax_periods (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id),
    period_type TEXT NOT NULL
                CHECK (period_type IN ('VAT_MONTHLY', 'CIT_ANNUAL', 'WHT_MONTHLY')),
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    status      TEXT NOT NULL DEFAULT 'DRAFT'
                CHECK (status IN ('DRAFT', 'COMPUTED', 'REVIEWED', 'FILED')),
    computed_at TIMESTAMPTZ,
    filed_at    TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_date_range CHECK (end_date >= start_date),
    UNIQUE (business_id, period_type, start_date)
);

CREATE INDEX idx_tp_business ON tax_periods(business_id);
CREATE INDEX idx_tp_status ON tax_periods(business_id, status);
CREATE INDEX idx_tp_dates ON tax_periods(business_id, start_date, end_date);

-- ============================================================
-- TAX COMPUTATIONS — Individual rate computations per period
-- Immutable once written (recompute creates new rows after clearing old)
-- ============================================================
CREATE TABLE tax_computations (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tax_period_id            UUID NOT NULL REFERENCES tax_periods(id) ON DELETE CASCADE,
    rate_type                TEXT NOT NULL,
    rate_code                TEXT NOT NULL,
    base_amount_pesewas      BIGINT NOT NULL,
    rate_bps                 INTEGER NOT NULL,
    computed_amount_pesewas  BIGINT NOT NULL,
    computation_details      JSONB,
    computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tc_period ON tax_computations(tax_period_id);

-- ============================================================
-- FILING RECORDS — Track when/how periods were filed with GRA
-- ============================================================
CREATE TABLE filing_records (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tax_period_id    UUID NOT NULL REFERENCES tax_periods(id),
    filed_by         UUID NOT NULL REFERENCES users(id),
    filing_reference TEXT,
    filing_method    TEXT NOT NULL DEFAULT 'MANUAL'
                     CHECK (filing_method IN ('MANUAL', 'PORTAL', 'API')),
    filed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes            TEXT
);

CREATE INDEX idx_fr_period ON filing_records(tax_period_id);

-- Grant SELECT to read-only role (Analytics Service)
GRANT SELECT ON tax_periods TO bizpulse_readonly;
GRANT SELECT ON tax_computations TO bizpulse_readonly;
GRANT SELECT ON filing_records TO bizpulse_readonly;
