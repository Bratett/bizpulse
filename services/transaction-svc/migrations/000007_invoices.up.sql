CREATE TABLE invoices (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id         UUID NOT NULL REFERENCES businesses(id),
    invoice_number      TEXT,
    customer_name       TEXT NOT NULL,
    customer_tin        TEXT,
    line_items          JSONB NOT NULL,
    subtotal_pesewas    BIGINT NOT NULL,
    vat_pesewas         BIGINT NOT NULL,
    total_pesewas       BIGINT NOT NULL,
    notes               TEXT,
    status              TEXT NOT NULL DEFAULT 'DRAFT'
                        CHECK (status IN ('DRAFT', 'SENT', 'PAID', 'CANCELLED')),
    created_by          UUID NOT NULL REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_inv_business ON invoices(business_id);
CREATE INDEX idx_inv_status ON invoices(business_id, status);
CREATE INDEX idx_inv_created ON invoices(business_id, created_at);

GRANT SELECT ON invoices TO bizpulse_readonly;
