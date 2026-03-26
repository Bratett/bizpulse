-- BizPulse AI — Initial Schema Migration
-- Aligns with DATA_MODEL.md and COMPLIANCE_MATRIX.md
-- MVP simplifications noted inline; canonical names used where possible

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- USERS (Section 5.1.1 — simplified for MVP, no field-level encryption yet)
-- ============================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    preferred_language TEXT NOT NULL DEFAULT 'en',
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'invited', 'suspended', 'deleted')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- BUSINESSES (Section 5.1.2)
-- ============================================================
CREATE TABLE businesses (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legal_name               TEXT NOT NULL,
    trading_name             TEXT,
    registration_number      TEXT,
    tax_identification_number TEXT,
    industry_sector          TEXT,
    base_currency            TEXT NOT NULL DEFAULT 'GHS',
    country_code             TEXT NOT NULL DEFAULT 'GH',
    status                   TEXT NOT NULL DEFAULT 'active',
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- USER-BUSINESS MEMBERSHIP (multi-tenant boundary)
-- ============================================================
CREATE TABLE user_business_memberships (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id),
    business_id UUID NOT NULL REFERENCES businesses(id),
    role        TEXT NOT NULL DEFAULT 'owner'
                CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, business_id)
);

CREATE INDEX idx_ubm_user ON user_business_memberships(user_id);
CREATE INDEX idx_ubm_business ON user_business_memberships(business_id);

-- ============================================================
-- CONSENT RECORDS (Section 5.1.6 — Ghana DPA 843)
-- ============================================================
CREATE TABLE consent_records (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id          UUID NOT NULL REFERENCES users(id),
    business_id      UUID REFERENCES businesses(id),
    consent_category TEXT NOT NULL,
    granted          BOOLEAN NOT NULL,
    captured_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    withdrawn_at     TIMESTAMPTZ,
    source_channel   TEXT NOT NULL DEFAULT 'web'
                     CHECK (source_channel IN ('mobile', 'web', 'ussd', 'assisted')),
    policy_version   TEXT NOT NULL DEFAULT '1.0'
);

CREATE INDEX idx_consent_user ON consent_records(user_id);

-- ============================================================
-- CHART OF ACCOUNTS (Section 7.1 — IFRS-aligned)
-- ============================================================
CREATE TABLE chart_of_accounts (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id       UUID REFERENCES businesses(id),  -- NULL = system default
    account_code      TEXT NOT NULL,
    account_name      TEXT NOT NULL,
    account_type      TEXT NOT NULL
                      CHECK (account_type IN ('asset', 'liability', 'equity', 'income', 'expense')),
    parent_account_id UUID REFERENCES chart_of_accounts(id),
    is_system_default BOOLEAN NOT NULL DEFAULT FALSE,
    active            BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (business_id, account_code)
);

CREATE INDEX idx_coa_business ON chart_of_accounts(business_id);
CREATE INDEX idx_coa_type ON chart_of_accounts(account_type);

-- ============================================================
-- TRANSACTIONS (MVP simplified shape — see plan note on canonical migration)
-- Canonical DATA_MODEL.md section 7.3 uses direction/amount_minor/event_type;
-- MVP uses type/amount_pesewas for simplicity. Migration planned for Sprint 1.
-- APPEND-ONLY: no UPDATE or DELETE allowed on this table.
-- ============================================================
CREATE TABLE transactions (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id      UUID NOT NULL REFERENCES businesses(id),
    idempotency_key  TEXT NOT NULL,
    type             TEXT NOT NULL CHECK (type IN ('INCOME', 'EXPENSE')),
    amount_pesewas   BIGINT NOT NULL CHECK (amount_pesewas > 0),
    account_code     TEXT NOT NULL,
    description      TEXT,
    transaction_date DATE NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by       UUID NOT NULL REFERENCES users(id),
    UNIQUE (business_id, idempotency_key)
);

CREATE INDEX idx_txn_business ON transactions(business_id);
CREATE INDEX idx_txn_date ON transactions(business_id, transaction_date);
CREATE INDEX idx_txn_type ON transactions(business_id, type);

-- Prevent UPDATE and DELETE on transactions (append-only enforcement)
CREATE OR REPLACE FUNCTION prevent_transaction_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Transactions are append-only. UPDATE and DELETE are not permitted.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_no_update_transactions
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION prevent_transaction_mutation();

CREATE TRIGGER trg_no_delete_transactions
    BEFORE DELETE ON transactions
    FOR EACH ROW EXECUTE FUNCTION prevent_transaction_mutation();

-- ============================================================
-- COMPLIANCE RATES (Section 9.1 — tax rates from config only)
-- All rates in basis points: 1500 = 15.00%
-- ============================================================
CREATE TABLE compliance_rates (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id                 UUID REFERENCES businesses(id),  -- NULL = national default
    rate_type                   TEXT NOT NULL
                                CHECK (rate_type IN ('VAT', 'NHIL_GETFUND', 'CIT', 'PAYE', 'WHT')),
    rate_code                   TEXT NOT NULL,
    jurisdiction                TEXT NOT NULL DEFAULT 'GH',
    applies_to_transaction_type TEXT,
    percentage_basis_points     BIGINT NOT NULL,
    effective_from              DATE NOT NULL,
    effective_to                DATE,  -- NULL = currently active
    source_reference            TEXT,
    created_by_user_id          UUID REFERENCES users(id),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rates_type ON compliance_rates(rate_type);
CREATE INDEX idx_rates_effective ON compliance_rates(effective_from, effective_to);

-- ============================================================
-- AUDIT LOG (Section 14.1 — simplified, hash chaining deferred)
-- ============================================================
CREATE TABLE audit_log (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id        UUID REFERENCES businesses(id),
    actor_user_id      UUID REFERENCES users(id),
    entity_type        TEXT NOT NULL,
    entity_id          UUID NOT NULL,
    action_code        TEXT NOT NULL,
    before_snapshot    JSONB,
    after_snapshot     JSONB,
    occurred_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address_masked  TEXT
    -- hash_prev and hash_current deferred to Sprint 1 (tamper-evidence chaining)
);

CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_business ON audit_log(business_id);
CREATE INDEX idx_audit_time ON audit_log(occurred_at);

-- Grant SELECT to read-only role (Analytics Service)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bizpulse_readonly;
