-- BizPulse AI — Sprint 1: Transaction Tax Metadata
-- Separate table because transactions has append-only triggers (no UPDATE/DELETE).
-- This table is mutable — tax categorization can be corrected.
-- Joined with transactions at query time for tax computation.

CREATE TABLE transaction_tax_metadata (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id  UUID NOT NULL REFERENCES transactions(id),
    business_id     UUID NOT NULL REFERENCES businesses(id),
    tax_category    TEXT NOT NULL DEFAULT 'STANDARD_RATED'
                    CHECK (tax_category IN (
                        'STANDARD_RATED',
                        'ZERO_RATED',
                        'EXEMPT',
                        'NON_DEDUCTIBLE'
                    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (transaction_id)
);

CREATE INDEX idx_ttm_business ON transaction_tax_metadata(business_id);
CREATE INDEX idx_ttm_category ON transaction_tax_metadata(business_id, tax_category);

-- Grant SELECT to read-only role (Analytics Service)
GRANT SELECT ON transaction_tax_metadata TO bizpulse_readonly;
