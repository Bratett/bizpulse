-- Rollback: Remove band_ceiling_pesewas column from compliance_rates

ALTER TABLE compliance_rates DROP COLUMN IF EXISTS band_ceiling_pesewas;
