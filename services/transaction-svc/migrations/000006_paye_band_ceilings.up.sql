-- BizPulse AI — Add band_ceiling_pesewas to compliance_rates for PAYE computation
-- Ceilings define the taxable range for each progressive PAYE band.

ALTER TABLE compliance_rates ADD COLUMN IF NOT EXISTS band_ceiling_pesewas BIGINT;

UPDATE compliance_rates SET band_ceiling_pesewas = 40200 WHERE rate_code = 'PAYE_BAND_1';
UPDATE compliance_rates SET band_ceiling_pesewas = 11000 WHERE rate_code = 'PAYE_BAND_2';
UPDATE compliance_rates SET band_ceiling_pesewas = 13000 WHERE rate_code = 'PAYE_BAND_3';
UPDATE compliance_rates SET band_ceiling_pesewas = 300000 WHERE rate_code = 'PAYE_BAND_4';
UPDATE compliance_rates SET band_ceiling_pesewas = 1639500 WHERE rate_code = 'PAYE_BAND_5';
-- Band 6 has no ceiling (remainder) — NULL
