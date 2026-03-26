# DATA_MODEL.md

## BizPulse AI — Canonical Data Model

**Document Type:** Logical Data Model + Storage Routing Reference  
**Status:** Working baseline for Phase 1 implementation  
**Primary Use:** Source document for schema design, migration authoring, API contract drafting, and service boundary validation

---

## 1. Purpose

This document defines the canonical BizPulse logical data model across operational storage, time-series storage, vector search, cache/state, and lake storage. It is intended to be used with `ARCHITECTURE.md`, `API_CONTRACT.md`, `COMPLIANCE_MATRIX.md`, and `OFFLINE_SYNC_SPEC.md`.

This is **not** a full SQL DDL. It is the authoritative model for:
- business entities
- ownership boundaries
- primary keys and foreign keys
- tenant isolation model
- storage routing
- append-only and audit constraints
- sync and conflict-sensitive data classes
- AI/ML output persistence boundaries

The model reflects the binding architecture decisions that BizPulse uses PostgreSQL as the operational source of truth, TimescaleDB for business metrics, InfluxDB for infrastructure telemetry, pgvector as the default vector store, Redis only for ephemeral state, and Kafka/Flink as the ingestion/event backbone. fileciteturn9file7 fileciteturn8file0

---

## 2. Foundational Modeling Principles

### 2.1 Source-of-truth rules

1. **PostgreSQL is the operational system of record.** All transactional records, user accounts, compliance filings, and financial statements are persisted there. fileciteturn9file9turn9file7
2. **TimescaleDB stores business time-series linked to operational facts**, such as revenue trends, cash flow metrics, and user activity metrics tied back to transaction or business identifiers. fileciteturn9file9turn9file7
3. **InfluxDB stores infrastructure telemetry only**, never business facts. fileciteturn9file9turn7file8
4. **pgvector is the default vector store** for embeddings and RAG until a DPIA explicitly permits otherwise. fileciteturn8file0turn8file1
5. **Redis is ephemeral only** for sessions, counters, cache, and queue support. It is never a system of record. fileciteturn9file9turn7file8
6. **S3 stores lake data and regulated document objects** such as Parquet partitions and PDF/A documents. fileciteturn9file6turn8file0

### 2.2 Financial data rules

1. Monetary amounts are stored in **minor units (pesewas)** as integers, never floats. fileciteturn8file0
2. Financial transaction records are **append-only / event-sourced**. No destructive update/delete path is allowed for accounting facts. fileciteturn8file0turn9file3
3. Tax rates are never hardcoded and must come from a configuration table. fileciteturn8file0turn7file8
4. Every compliance-relevant mutation must leave a tamper-evident audit trail. fileciteturn9file4

### 2.3 Tenant and access model

BizPulse is modeled as a **multi-tenant SaaS platform** where the core tenant boundary is the **business**. Users belong to one or more businesses through membership and role assignment records. Row-level isolation must be enforceable by `business_id`. fileciteturn8file0turn9file2

### 2.4 Offline and sync model

Offline sync is first-class. The model explicitly distinguishes:
- append-only financial records
- mergeable settings and tax inputs
- manually resolved inventory conflicts
- versioned documents
- device-local NLP history that must **not** sync cross-device fileciteturn8file0turn9file4

---

## 3. Storage Topology

| Store | Role | Canonical data families |
|---|---|---|
| PostgreSQL 16 | Operational source of truth | users, businesses, memberships, transactions, ledger events, compliance filings, consent records, subscriptions, inventory, documents metadata, financial statements, model outputs metadata |
| TimescaleDB | Business time-series | daily_revenue, daily_cashflow, user_activity_metrics, forecast snapshots, trend aggregates |
| pgvector | Embeddings in PostgreSQL | document embeddings, regulation embeddings, query embeddings |
| Redis | Ephemeral state | JWT/session state, rate-limit counters, idempotency windows, short-TTL NLP cache, queue support |
| InfluxDB | Infra telemetry | latency, throughput, pod metrics, queue DLQ metrics, failover metrics |
| S3 | Durable object / analytic storage | document binaries (PDF/A), OCR intermediates, Parquet lake data, export artefacts |
| Kafka | Event backbone | raw and enriched transaction event streams |

The routing rules above are binding and come directly from the requirements and technical specification. fileciteturn9file9turn9file7turn7file8

---

## 4. Bounded Contexts and Ownership

### 4.1 User Service owns
- users
- user_credentials references / identity links
- businesses
- business_memberships
- roles and permissions mappings
- consent records
- subscription tiers and subscriptions
- device registrations

### 4.2 Transaction Service owns
- transaction events
- transaction projections
- accounts / chart of accounts mapping references
- transaction sources and external provider links
- reconciliation records
- sync batches
- idempotency records
- inventory movement events

### 4.3 Analytics Service owns
- financial statement runs
- generated statement snapshots
- forecast runs and forecast points
- credit scoring feature sets and score results
- KPI aggregates and analytics materializations

### 4.4 Compliance Service owns
- compliance rates
- compliance filings
- filing submissions and receipts
- payroll compliance records
- tax calculations and tax periods
- regulatory alerts
- audit chain records

### 4.5 NLP Service owns
- prompt templates and model routing configs
- intent classifications
- structured query results metadata
- vector index references
- response cache metadata

### 4.6 Notification Service owns
- notification templates
- outbound notification jobs
- delivery attempts
- provider callback normalization records
- escalation flags

---

## 5. Core Entity Model

Below, “PK” means primary key and “FK” means foreign key.

### 5.1 Tenant and identity domain

#### 5.1.1 `users`
Represents a natural person using the system.

**Key fields**
- `id` (PK, UUID)
- `keycloak_subject_id` (unique)
- `email_encrypted`
- `phone_encrypted`
- `first_name_encrypted`
- `last_name_encrypted`
- `preferred_language`
- `status` (`active`, `invited`, `suspended`, `deleted`)
- `mfa_enabled`
- `created_at`, `updated_at`

**Notes**
- PII fields require field-level encryption. fileciteturn8file0turn9file1
- One user can belong to multiple businesses.

#### 5.1.2 `businesses`
Represents the tenant boundary.

**Key fields**
- `id` (PK, UUID)
- `legal_name`
- `trading_name`
- `registration_number`
- `tax_identification_number`
- `industry_sector`
- `base_currency` (default `GHS`)
- `country_code`
- `subscription_tier_id` (FK)
- `status`
- `created_at`, `updated_at`

**Relationships**
- One business has many memberships, transactions, filings, documents, statements, devices, branches, and metric series.

#### 5.1.3 `business_memberships`
Associates users to businesses with role context.

**Key fields**
- `id` (PK)
- `business_id` (FK → businesses)
- `user_id` (FK → users)
- `role_code`
- `status`
- `joined_at`
- `invited_by_user_id` (FK → users)

#### 5.1.4 `roles`
System role catalog.

**Key fields**
- `id` (PK)
- `code` (`owner`, `admin`, `accountant`, `cashier`, `staff`, `auditor`, etc.)
- `description`

#### 5.1.5 `role_permissions`
Maps role to permission scopes.

**Key fields**
- `role_id` (FK)
- `permission_code`

#### 5.1.6 `consent_records`
Granular data processing consent as required by Act 843.

**Key fields**
- `id` (PK)
- `user_id` (FK)
- `business_id` (nullable FK if tenant-scoped)
- `consent_category`
- `granted` (bool)
- `captured_at`
- `withdrawn_at`
- `source_channel` (`mobile`, `web`, `ussd`, `assisted`)
- `policy_version`

This is explicitly required to support granular onboarding consent with timestamps and per-category withdrawal. fileciteturn9file4

#### 5.1.7 `subscription_tiers`
Tier catalog.

**Key fields**
- `id` (PK)
- `code` (`free`, `starter`, `growth`, `professional`, `enterprise`)
- `display_name`
- `monthly_price_pesewas`
- `offline_duration_days`
- `device_storage_budget_mb`
- `api_rate_limit_per_day`
- `feature_flags_json`

Offline duration and device storage budgets derive from the offline architecture requirements. fileciteturn7file1

#### 5.1.8 `subscriptions`
A business’ active or historical plan enrollment.

**Key fields**
- `id` (PK)
- `business_id` (FK)
- `subscription_tier_id` (FK)
- `billing_status`
- `starts_at`
- `ends_at`
- `renewal_channel`
- `momo_reference`

---

## 6. Business structure and operational setup

### 6.1 `branches`
Optional physical or reporting branch/unit.

**Key fields**
- `id` (PK)
- `business_id` (FK)
- `name`
- `code`
- `location_text`
- `is_head_office`

### 6.2 `business_settings`
Tenant-level settings subject to LWW sync conflict strategy.

**Key fields**
- `business_id` (PK/FK)
- `default_tax_profile_id`
- `timezone`
- `fiscal_year_start_month`
- `invoice_preferences_json`
- `notification_preferences_json`
- `updated_at`

Settings are a sync class that uses last-write-wins. fileciteturn8file0

### 6.3 `devices`
Registered client devices for offline sync and push delivery.

**Key fields**
- `id` (PK)
- `business_id` (FK)
- `user_id` (FK)
- `platform` (`android`, `ios`, `web`)
- `device_fingerprint`
- `push_token`
- `last_seen_at`
- `offline_capable`
- `revoked_at`

### 6.4 `sync_batches`
Tracks offline delta sync submissions.

**Key fields**
- `id` (PK)
- `business_id` (FK)
- `device_id` (FK)
- `submitted_by_user_id` (FK)
- `idempotency_key`
- `submitted_at`
- `status`
- `item_count`
- `checksum_before`
- `checksum_after`
- `failure_reason`

### 6.5 `sync_batch_items`
Each change in a batch.

**Key fields**
- `id` (PK)
- `sync_batch_id` (FK)
- `entity_type`
- `entity_id`
- `operation_type`
- `client_version`
- `server_version`
- `conflict_strategy`
- `resolution_status`

---

## 7. Financial transaction domain

This is the highest-integrity area of the model.

### 7.1 `chart_of_accounts`
IFRS-aligned chart of accounts reference. fileciteturn8file0turn9file4

**Key fields**
- `id` (PK)
- `business_id` (FK, nullable for system defaults)
- `account_code`
- `account_name`
- `account_type` (`asset`, `liability`, `equity`, `income`, `expense`)
- `parent_account_id` (self-FK)
- `is_system_default`
- `active`

### 7.2 `transaction_sources`
Enumerates where a transaction originated.

**Key fields**
- `id` (PK)
- `business_id` (FK)
- `source_type` (`mtn_momo`, `vodafone_cash`, `airteltigo`, `bank_feed`, `manual`, `pos`, `ecommerce`, `ocr_document`)
- `provider_account_ref`
- `display_name`
- `status`

### 7.3 `transaction_events`
Immutable append-only event stream for financial facts.

**Key fields**
- `id` (PK, UUID)
- `business_id` (FK)
- `transaction_group_id` (logical aggregate id)
- `event_type` (`captured`, `classified`, `adjusted`, `reversed`, `settled`, `reconciled`)
- `source_id` (FK → transaction_sources)
- `source_provider`
- `external_reference`
- `idempotency_key`
- `occurred_at`
- `recorded_at`
- `currency_code`
- `amount_minor`
- `amount_ghs_pesewas`
- `exchange_rate`
- `exchange_rate_source`
- `direction` (`inflow`, `outflow`)
- `merchant_name`
- `merchant_category`
- `description`
- `raw_payload_ref`
- `created_by_user_id` (nullable FK)

**Constraints**
- immutable after insert
- unique constraint on (`business_id`, `idempotency_key`) for defined windows or via companion idempotency table
- no hard delete

This design follows the append-only/event-sourced transaction mandate and the ingestion enrichment requirements for merchant categorization and currency conversion. fileciteturn8file0turn9file9

### 7.4 `transaction_projections`
Read-optimized current state of a transaction aggregate.

**Key fields**
- `id` (PK)
- `business_id` (FK)
- `transaction_group_id` (unique within tenant)
- `latest_event_id` (FK → transaction_events)
- `posting_date`
- `settlement_date`
- `status`
- `counterparty_name`
- `account_id` (FK → chart_of_accounts)
- `tax_treatment_code`
- `is_reconciled`

**Purpose**
- query efficiency for dashboards, reporting, and NLP fact checking
- derived from immutable events, not authoritative by itself

### 7.5 `ledger_entries`
Double-entry or structured accounting postings derived from transaction facts.

**Key fields**
- `id` (PK)
- `business_id` (FK)
- `transaction_event_id` (FK)
- `account_id` (FK)
- `entry_side` (`debit`, `credit`)
- `amount_minor`
- `currency_code`
- `posting_date`

### 7.6 `reconciliations`
Tracks matching of internal and external financial records.

**Key fields**
- `id` (PK)
- `business_id` (FK)
- `transaction_group_id`
- `external_statement_line_ref`
- `reconciliation_status`
- `matched_at`
- `matched_by_user_id`

### 7.7 `provider_balances`
Latest known provider balances for wallets or bank accounts.

**Key fields**
- `id` (PK)
- `business_id` (FK)
- `source_id` (FK)
- `balance_minor`
- `currency_code`
- `as_of_timestamp`

### 7.8 `idempotency_records`
Operational idempotency guard.

**Key fields**
- `idempotency_key` (PK)
- `business_id` (FK)
- `first_seen_at`
- `request_hash`
- `result_reference_type`
- `result_reference_id`
- `expires_at`

The specification explicitly requires idempotency enforcement and duplicate rejection. fileciteturn8file0turn9file9

---

## 8. Inventory, commerce, and document-linked operational data

The specs mention inventory and ecommerce ingestion, so the canonical model includes inventory entities even if Phase 1 only uses a subset. fileciteturn9file0turn9file6

### 8.1 `products`
- `id` (PK)
- `business_id` (FK)
- `sku`
- `name`
- `category`
- `unit_of_measure`
- `default_sale_price_minor`
- `default_purchase_price_minor`
- `active`

### 8.2 `inventory_locations`
- `id` (PK)
- `business_id` (FK)
- `branch_id` (FK)
- `name`

### 8.3 `inventory_counts`
Latest count snapshot per item/location.

- `id` (PK)
- `business_id` (FK)
- `product_id` (FK)
- `location_id` (FK)
- `quantity_on_hand`
- `unit_cost_minor`
- `last_counted_at`
- `last_counted_by_user_id`

Inventory count conflicts require manual diff-based resolution during sync. fileciteturn9file4

### 8.4 `inventory_movements`
Append-only stock movements.

- `id` (PK)
- `business_id` (FK)
- `product_id` (FK)
- `location_id` (FK)
- `movement_type` (`sale`, `purchase`, `adjustment`, `transfer`, `return`)
- `quantity_delta`
- `related_transaction_event_id` (FK)
- `occurred_at`

### 8.5 `orders`
For POS/e-commerce order ingestion.

- `id` (PK)
- `business_id` (FK)
- `source_id` (FK)
- `external_order_ref`
- `customer_name`
- `status`
- `order_total_minor`
- `currency_code`
- `ordered_at`

### 8.6 `order_items`
- `id` (PK)
- `order_id` (FK)
- `product_id` (FK)
- `quantity`
- `unit_price_minor`
- `line_total_minor`
- `tax_minor`

---

## 9. Compliance and regulatory domain

### 9.1 `compliance_rates`
Central configuration table for VAT, NHIL/GETFund, CIT, PAYE, WHT, and other rates.

**Key fields**
- `id` (PK)
- `business_id` (nullable FK for national defaults)
- `rate_type` (`VAT`, `NHIL_GETFUND`, `CIT`, `PAYE`, `WHT`)
- `rate_code`
- `jurisdiction`
- `applies_to_transaction_type`
- `percentage_basis_points`
- `effective_from`
- `effective_to`
- `source_reference`
- `created_by_user_id`

This table is mandatory because rates must be data-driven and updateable without deployment. fileciteturn8file0turn7file8

### 9.2 `tax_periods`
- `id` (PK)
- `business_id` (FK)
- `tax_type`
- `period_start`
- `period_end`
- `status`

### 9.3 `tax_calculations`
Stores computed tax outcomes for traceability.

- `id` (PK)
- `business_id` (FK)
- `tax_period_id` (FK)
- `calculation_type`
- `input_snapshot_json`
- `output_snapshot_json`
- `computed_at`
- `computed_by`
- `rate_snapshot_json`

Tax input conflicts require merge plus audit trail, so preserving both inputs and outputs is required. fileciteturn9file4

### 9.4 `compliance_filings`
Represents a filing obligation or generated filing package.

- `id` (PK)
- `business_id` (FK)
- `tax_period_id` (FK)
- `filing_type` (`VAT`, `CIT`, `PAYE`, `WHT`, `SSNIT`)
- `status`
- `generated_xml_ref`
- `generated_pdf_ref`
- `submission_due_at`
- `submitted_at`
- `receipt_reference`

### 9.5 `filing_submissions`
Tracks outbound submission attempts and results.

- `id` (PK)
- `compliance_filing_id` (FK)
- `provider_name` (`GRA`, `SSNIT`)
- `submission_reference`
- `attempt_number`
- `status`
- `error_code`
- `error_message_masked`
- `submitted_at`
- `response_received_at`

### 9.6 `payroll_records`
- `id` (PK)
- `business_id` (FK)
- `employee_identifier`
- `gross_pay_minor`
- `tax_withheld_minor`
- `ssnit_amount_minor`
- `pay_period_start`
- `pay_period_end`

### 9.7 `regulatory_alerts`
- `id` (PK)
- `business_id` (FK)
- `alert_type`
- `severity`
- `message`
- `due_at`
- `resolved_at`

---

## 10. Financial statements and analytics domain

### 10.1 `statement_runs`
A generation run for formal statements.

- `id` (PK)
- `business_id` (FK)
- `statement_type` (`pnl`, `balance_sheet`, `cash_flow`, `equity_changes`)
- `period_start`
- `period_end`
- `basis` (`accrual`, `cash`, `direct`, `indirect`)
- `generated_at`
- `generated_by`
- `source_snapshot_hash`

### 10.2 `statement_artifacts`
Generated outputs.

- `id` (PK)
- `statement_run_id` (FK)
- `format` (`json`, `pdfa`, `xbrl`)
- `storage_ref`
- `checksum`

### 10.3 `kpi_snapshots`
Operational KPI points persisted in PostgreSQL for app querying.

- `id` (PK)
- `business_id` (FK)
- `metric_code`
- `metric_value_numeric`
- `metric_as_of_date`
- `window_code`

### 10.4 `daily_revenue` (Timescale hypertable)
- `time`
- `business_id`
- `branch_id`
- `transaction_count`
- `gross_revenue_minor`
- `net_revenue_minor`

### 10.5 `daily_cashflow` (Timescale hypertable)
- `time`
- `business_id`
- `inflow_minor`
- `outflow_minor`
- `net_cashflow_minor`
- `linked_transaction_count`

### 10.6 `user_activity_metrics` (Timescale hypertable)
- `time`
- `business_id`
- `active_user_count`
- `query_count`
- `sync_success_count`
- `sync_failure_count`

Timescale hypertables for these metric families are explicitly called out in the implementation guide. fileciteturn8file0turn9file2

---

## 11. ML / AI domain

### 11.1 `forecast_runs`
Metadata for a forecast model execution.

- `id` (PK)
- `business_id` (FK)
- `model_name`
- `model_version`
- `run_type` (`cash_flow`, `demand_prediction`)
- `training_cutoff_date`
- `generated_at`
- `validation_mape`
- `directional_accuracy`
- `feature_summary_json`

### 11.2 `forecast_points`
Point predictions.

- `id` (PK)
- `forecast_run_id` (FK)
- `forecast_date`
- `predicted_inflow_minor`
- `predicted_outflow_minor`
- `predicted_net_position_minor`
- `ci_lower_minor`
- `ci_upper_minor`

The initial forecasting scaffold is specified with these output fields and Prophet-based runs. fileciteturn8file1

### 11.3 `credit_score_runs`
- `id` (PK)
- `business_id` (FK)
- `model_version`
- `generated_at`
- `score_value`
- `risk_band`
- `explanation_summary_json`
- `bias_check_reference`

### 11.4 `model_registry_refs`
Application-facing references to MLflow/BentoML artefacts.

- `id` (PK)
- `model_name`
- `model_version`
- `registry_uri`
- `serving_uri`
- `status`

### 11.5 `nlp_queries`
Metadata for user NLP interactions that may be centrally logged.

- `id` (PK)
- `business_id` (FK)
- `user_id` (FK)
- `intent_code`
- `detected_language`
- `model_used`
- `response_time_ms`
- `resolution_status`
- `escalation_flag`
- `created_at`

The observability spec explicitly requires logging these fields. fileciteturn7file8

### 11.6 `nlp_response_artifacts`
- `id` (PK)
- `nlp_query_id` (FK)
- `response_type`
- `structured_data_json`
- `narrative_text_masked`
- `fact_check_status`
- `cache_hit`

### 11.7 `vector_embeddings`
Embeddings stored in PostgreSQL/pgvector.

- `id` (PK)
- `business_id` (nullable FK)
- `document_id` (nullable FK)
- `embedding_scope` (`regulation_doc`, `business_doc`, `query_cache`)
- `source_text_checksum`
- `embedding_model`
- `embedding` (vector)
- `chunk_index`
- `created_at`

### 11.8 Device-local NLP history
Conversation history for NLP sessions must remain device-local and not be synced. It is therefore **excluded from the shared server-side canonical model** except for minimal masked metadata needed for observability and incident analysis. fileciteturn9file4

---

## 12. Document and OCR domain

### 12.1 `documents`
Document metadata record.

- `id` (PK)
- `business_id` (FK)
- `uploaded_by_user_id` (FK)
- `document_type` (`invoice`, `receipt`, `statement`, `tax_return`, `report`, `other`)
- `storage_ref`
- `storage_format` (`pdfa`, `image`, `xml`, `json`)
- `checksum`
- `retention_until`
- `version_number`
- `supersedes_document_id` (self-FK)
- `created_at`

Documents must be stored in PDF/A where applicable and retained for 7 years. fileciteturn9file6

### 12.2 `ocr_extractions`
- `id` (PK)
- `document_id` (FK)
- `extraction_status`
- `vendor_name`
- `invoice_number`
- `total_amount_minor`
- `tax_amount_minor`
- `due_date`
- `raw_extraction_json`
- `confidence_score`
- `processed_at`

### 12.3 `document_line_items`
- `id` (PK)
- `ocr_extraction_id` (FK)
- `description`
- `quantity`
- `unit_price_minor`
- `line_total_minor`
- `tax_minor`

### 12.4 `document_links`
Associates documents to transactions, filings, or statements.

- `id` (PK)
- `document_id` (FK)
- `linked_entity_type`
- `linked_entity_id`

---

## 13. Notification and external delivery domain

### 13.1 `notification_templates`
- `id` (PK)
- `channel` (`push`, `sms`, `whatsapp`, `email`)
- `template_code`
- `language_code`
- `content_template`
- `status`

### 13.2 `notification_jobs`
- `id` (PK)
- `business_id` (FK)
- `user_id` (nullable FK)
- `channel`
- `template_id` (FK)
- `payload_json`
- `priority`
- `status`
- `scheduled_at`
- `created_at`

### 13.3 `notification_deliveries`
- `id` (PK)
- `notification_job_id` (FK)
- `provider_name`
- `provider_message_id`
- `attempt_number`
- `delivery_status`
- `sent_at`
- `delivered_at`
- `error_code`

### 13.4 `provider_callbacks`
Normalized provider callback ledger.

- `id` (PK)
- `provider_name`
- `callback_type`
- `normalized_status`
- `raw_payload_json`
- `received_at`

A normalized callback model is required because SMS status events must be provider-agnostic across primary and Africa’s Talking fallback providers. fileciteturn8file0turn8file1

---

## 14. Audit, security, and compliance traceability

### 14.1 `audit_log`
Tamper-evident access and change log.

- `id` (PK)
- `business_id` (nullable FK)
- `actor_user_id` (nullable FK)
- `entity_type`
- `entity_id`
- `action_code`
- `before_snapshot_json`
- `after_snapshot_json`
- `occurred_at`
- `ip_address_masked`
- `hash_prev`
- `hash_current`

Tamper-evident audit logging is explicitly required by Act 843 compliance requirements. fileciteturn9file4

### 14.2 `security_events`
- `id` (PK)
- `business_id` (nullable FK)
- `user_id` (nullable FK)
- `event_type`
- `severity`
- `details_json`
- `occurred_at`

### 14.3 `breach_incidents`
- `id` (PK)
- `incident_code`
- `detected_at`
- `severity`
- `status`
- `dpc_notified_at`
- `user_notification_started_at`

The model supports the required 72-hour breach notification workflow. fileciteturn9file4

---

## 15. Event model and Kafka-aligned data contracts

The canonical streaming topics specified for Phase 1 are: 
- `raw.momo.transactions`
- `raw.vodafone.transactions`
- `raw.bank.statements`
- `raw.manual.entries`
- `processed.transactions.enriched` fileciteturn9file9turn8file0

### 15.1 Common event envelope fields
Every event schema should include:
- `event_id`
- `idempotency_key`
- `event_timestamp`
- `business_id`
- `source_provider`
- `schema_version`
- `trace_id`

### 15.2 Raw transaction events
Raw topics preserve provider-native fields plus normalized minimum fields needed for replay and enrichment.

### 15.3 Enriched transaction events
Must include:
- merchant category
- original currency
- converted amount in GHS pesewas
- fraud score placeholder
- deduplication status fileciteturn9file2turn9file9

---

## 16. Conflict resolution mapping by entity class

| Entity / data class | Conflict strategy | Modeling implication |
|---|---|---|
| Financial transactions | Append-only | never overwrite facts; create new event or reject duplicate |
| Business settings | Last-write-wins | maintain version timestamp and source metadata |
| Inventory counts | Manual resolution | preserve both versions and resolution record |
| Tax computation inputs | Server merge + audit trail | preserve original and merged snapshots |
| Documents | Version history | supersession chain rather than overwrite |
| NLP conversation history | Device-local only | exclude from shared sync model |

This matrix follows the explicitly locked offline sync decision and detailed conflict requirements. fileciteturn8file0turn9file4

### 16.1 `conflict_resolutions`
- `id` (PK)
- `business_id` (FK)
- `entity_type`
- `entity_id`
- `client_snapshot_json`
- `server_snapshot_json`
- `resolved_snapshot_json`
- `resolved_by_user_id`
- `resolved_at`
- `resolution_type`

---

## 17. Indexing and partitioning guidance

### 17.1 PostgreSQL
Recommended index categories:
- all FK columns
- `business_id` on every tenant-scoped table
- `idempotency_key` unique/lookup indexes
- `occurred_at`, `posting_date`, `submitted_at`, `generated_at`
- filtered indexes on active subscriptions, pending filings, unresolved alerts

### 17.2 TimescaleDB
Partition/hypertable on time, with `business_id` as a secondary partitioning or indexing dimension.

### 17.3 S3 lake
Partition enriched data by:
- `event_date=YYYY-MM-DD`
- `source_provider=`
- `business_id=` when appropriate for downstream controls

### 17.4 pgvector
Index embeddings by scope and business/regulation boundary; store source checksum to support re-embedding invalidation.

---

## 18. Security and privacy notes

1. PII fields in PostgreSQL require encryption at rest plus field-level protection where appropriate. fileciteturn9file1turn8file0
2. Logs and error payloads must store masked values, not raw PII. fileciteturn7file8
3. Audit tables are append-only.
4. Redis contents must be fully reconstructable from durable stores. fileciteturn9file9
5. Primary operational residency remains within Ghana or AWS Cape Town region. fileciteturn9file4

---

## 19. Recommended Phase 1 implementation subset

Not every entity above must land in Sprint 1. The recommended Phase 1 minimum is:
- users
- businesses
- business_memberships
- consent_records
- subscription_tiers
- subscriptions
- devices
- sync_batches / sync_batch_items
- chart_of_accounts
- transaction_sources
- transaction_events
- transaction_projections
- ledger_entries
- idempotency_records
- compliance_rates
- tax_periods
- tax_calculations
- compliance_filings
- filing_submissions
- documents
- ocr_extractions
- statement_runs
- statement_artifacts
- daily_revenue / daily_cashflow / user_activity_metrics
- vector_embeddings
- audit_log
- notification_jobs / notification_deliveries

This aligns with the implementation guide’s requirement that the initial schema cover at minimum users, businesses, transactions, compliance filings, consent records, tax rate configuration, and subscription tiers, with TimescaleDB hypertables and pgvector included from the start. fileciteturn8file0turn8file1

---

## 20. Open design items to capture in ADRs

The following should be confirmed in `DECISIONS.md` before final SQL generation:
1. whether branches are Phase 1 or Phase 2
2. whether chart of accounts allows tenant overrides of system defaults
3. whether transaction projections are materialized synchronously or asynchronously
4. exact RLS strategy for service accounts vs. user-context queries
5. whether audit hash chaining lives in PostgreSQL or external immutable storage
6. whether credit scoring outputs are persisted per run or only latest-per-business
7. exact retention/deletion handling for erased user requests under Act 843 where financial record retention obligations also apply

---

## 21. Minimal ER relationship summary

- `users` ⇄ `businesses` through `business_memberships`
- `businesses` → `subscriptions` → `subscription_tiers`
- `businesses` → `devices` → `sync_batches` → `sync_batch_items`
- `businesses` → `transaction_sources` → `transaction_events` → `ledger_entries`
- `transaction_events` → `transaction_projections`
- `businesses` → `compliance_rates`, `tax_periods`, `tax_calculations`, `compliance_filings`, `filing_submissions`
- `businesses` → `documents` → `ocr_extractions` → `document_line_items`
- `documents` → `vector_embeddings`
- `businesses` → `statement_runs` → `statement_artifacts`
- `businesses` → `forecast_runs` → `forecast_points`
- `businesses` → `notification_jobs` → `notification_deliveries`
- `businesses` → `audit_log`, `regulatory_alerts`, `security_events`

---

## 22. Implementation handoff guidance for AI agent

When using this file as context for schema generation, the AI agent must preserve these non-negotiables:
- PostgreSQL is the operational source of truth
- all money is integer minor units
- transaction facts are append-only
- tax rates come only from `compliance_rates`
- TimescaleDB is for business metrics, not infra telemetry
- InfluxDB is for infra telemetry only
- pgvector is the default vector store
- Redis is ephemeral only
- `business_id` is the primary tenant isolation key
- conflict handling differs by data class and must not be flattened into one generic overwrite rule

