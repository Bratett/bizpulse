# SECURITY_BASELINE.md

## 1. Purpose

This document defines the minimum security baseline for BizPulse AI across infrastructure, identity, application services, data handling, AI/ML workflows, delivery channels, integrations, and operational processes. It is the build-facing reference for engineers, DevOps/SRE, QA, compliance, and security reviewers.

It is intended to be used with:
- `ARCHITECTURE.md` for system boundaries and deployment topology
- `DATA_MODEL.md` for sensitive-data placement and storage routing
- `API_CONTRACT.md` for auth, tenancy, idempotency, and webhook rules
- `COMPLIANCE_MATRIX.md` for obligation-to-control mapping
- `DECISIONS.md` for ADR-backed exceptions or security trade-offs

This baseline is mandatory for all phases. Where a control is marked “Gate 1”, it is required before Phase 1 can pass into Phase 2.

---

## 2. Security Objectives

BizPulse AI must protect:
1. SME financial data and derived analytics
2. PII and consent-linked customer/business records
3. append-only financial transaction history and ledger integrity
4. compliance filings and tax-related submissions
5. multilingual NLP interactions and AI-generated outputs
6. mobile-first and offline-first workflows in unreliable network conditions
7. third-party integration credentials and callback endpoints

Primary goals:
- preserve confidentiality of PII and regulated records
- preserve integrity of financial and compliance data
- enforce tenant isolation across all services and channels
- ensure traceability through tamper-evident audit records
- minimize blast radius through least privilege and segmentation
- maintain resilience under telco/API instability and hostile traffic
- meet Gate 1 security expectations: zero critical findings and all high findings remediated or formally risk-accepted

---

## 3. Binding Security Decisions

The following architectural/security decisions are locked unless superseded by an ADR:

1. **Identity Provider:** Keycloak is the system identity provider for OAuth 2.0 / OIDC.
2. **Gateway Validation:** Kong validates JWTs at the gateway boundary; downstream services trust verified claims propagated by Kong.
3. **Gateway Topology:** Kong is HA from the start; single-instance Kong is prohibited.
4. **Token Lifetime:** JWT access tokens expire in 15 minutes.
5. **Storage Baseline:** PostgreSQL is the operational source of truth; pgvector is the default vector store pending any later compliant change.
6. **Transaction Integrity:** Financial transactions are append-only and idempotent; mutable CRUD-style transaction handling is prohibited.
7. **Provider Traffic Pattern:** All outbound calls to rate-limited upstream providers must flow through Asynq-backed queues; direct in-path synchronous calls are prohibited for production paths.
8. **Encryption Baseline:** AES-256 at rest and TLS 1.3 in transit are baseline requirements.
9. **PII Handling:** Sensitive PII requires field-level encryption in addition to storage-level protections.
10. **Admin Access:** MFA is mandatory for all administrative access.

---

## 4. Security Architecture by Layer

### 4.1 Network Security

Minimum controls:
- VPC isolation for all cloud environments
- private subnets for stateful data services
- public exposure limited to approved ingress components only
- CloudFlare WAF and DDoS protection at the internet edge
- Kubernetes network policies between namespaces and services
- deny-by-default ingress/egress where feasible
- environment separation for local, staging, and production
- controlled egress for outbound third-party integrations

Required topology expectations:
- data tier is not directly internet-addressable
- admin planes are separated from public API traffic
- telco/payment/compliance integrations use narrowly scoped egress rules
- internal service traffic should be encrypted where supported; mTLS is preferred for service-to-service traffic in staging/production

### 4.2 Application Security

Minimum controls:
- OAuth 2.0 / OIDC via Keycloak
- JWT validation at Kong
- RBAC and least-privilege enforcement at gateway and service layers
- input validation on all user and provider-controlled payloads
- explicit request/response schemas per API contract
- rate limiting by client type and subscription tier
- idempotency enforcement on write and callback paths
- centralized error handling that avoids secret/PII leakage
- safe file upload handling for document workflows

### 4.3 Data Security

Minimum controls:
- AES-256 encryption at rest for primary storage classes
- TLS 1.3 for all in-transit traffic crossing process or network boundaries
- field-level encryption for sensitive PII and equivalent regulated fields
- tenant scoping on all business-owned records
- row-level security where defined for PostgreSQL
- append-only controls for transaction and ledger records
- immutable or tamper-evident audit/event trails for high-risk actions

### 4.4 Access Security

Minimum controls:
- MFA for admin roles
- least privilege for human and machine identities
- short-lived access tokens
- session management and revocation controls
- break-glass process for emergency privileged access
- no shared admin accounts
- service accounts per service/workload/environment

### 4.5 Detection and Monitoring

Minimum controls:
- centralized audit logging
- SIEM integration
- anomaly detection and real-time alerting
- certificate expiry monitoring
- queue/DLQ alerting for critical outbound workflows
- security-relevant metrics and dashboards in Datadog/observability stack

### 4.6 Assurance

Minimum controls:
- quarterly penetration testing
- annual security audits
- dependency and static analysis in CI
- formal review before phase gates
- bug bounty program at the maturity stage defined by business readiness

---

## 5. Identity, Authentication, and Authorization Baseline

### 5.1 Identity Model

Authoritative components:
- **Keycloak**: user authentication, realms, clients, user federation, role mapping
- **Kong**: JWT validation, routing, coarse access control, rate limiting
- **Services**: authorization checks using verified claims, tenant context, role context, and resource ownership

### 5.2 Authentication Rules

1. All interactive user authentication flows must use Keycloak-backed OAuth 2.0 / OIDC.
2. Access tokens must expire after **15 minutes**.
3. Refresh token handling must be scoped per client type and revocable.
4. MFA is mandatory for:
   - platform administrators
   - security/compliance operators
   - production support with privileged access
   - any console that can manage integrations, tax configs, or filing actions
5. Machine-to-machine authentication must use dedicated clients/service accounts, never user tokens.
6. Local development shortcuts must never be enabled in staging or production.

### 5.3 Authorization Rules

1. RBAC is enforced for every protected API.
2. Tenant context (`business_id` or equivalent) is mandatory for business-scoped operations.
3. Services must reject requests where tenant claims and resource ownership do not align.
4. Privileged functions require explicit roles and positive authorization checks; absence of role is deny.
5. Sensitive actions require additional audit events, including:
   - tax rate changes
   - compliance filing submission or resubmission
   - admin role assignment or revocation
   - integration credential rotation
   - data export containing business/PII records

### 5.4 Baseline Role Categories

At minimum, document and enforce:
- Platform Admin
- Business Owner/Admin
- Finance/Operations User
- Compliance User
- Read-Only Analyst
- Support/Operations
- Security/Compliance Admin
- Service Accounts

Every role must map to:
- allowed APIs
- prohibited APIs
- data scope
- export permissions
- approval requirements for high-risk actions

---

## 6. Secrets and Key Management

### 6.1 General Rules

1. Secrets must never be hardcoded in source code, images, or config committed to VCS.
2. Secrets must be stored in an approved secret-management system for each environment.
3. Each service/environment pair must have distinct credentials.
4. Rotation procedures must exist for:
   - database credentials
   - API provider secrets
   - Africa’s Talking credentials
   - telco/payment provider tokens
   - Anthropic API keys
   - webhook signing secrets
   - encryption keys
5. Access to production secrets must be tightly limited and audited.

### 6.2 Encryption Keys

1. Storage-level encryption keys and field-level encryption keys must be separately governed where feasible.
2. Field-level encryption keys for PII must have documented rotation impact and recovery procedures.
3. Key access must be granted only to workloads that require decryption.
4. Key usage must be logged for privileged paths where the platform supports it.

---

## 7. Data Protection Baseline

### 7.1 Data Classification

At minimum classify data into:
- **Public**: marketing/help content
- **Internal**: operational documents and non-sensitive telemetry
- **Confidential**: business data, transactions, statements, filings
- **Restricted**: PII, credentials, tokens, encrypted document contents, regulated filing artefacts

### 7.2 Storage Routing Rules

- **PostgreSQL**: operational records, users, businesses, consent, subscriptions, transactions, ledger, compliance records
- **TimescaleDB**: business time-series metrics linked to operational facts
- **InfluxDB**: infrastructure telemetry and custom operational metrics, not system-of-record business data
- **Redis**: ephemeral cache/session/idempotency/queue support only; no durable source-of-truth records
- **pgvector**: vector embeddings within PostgreSQL boundary by default
- **S3/object storage**: documents, exports, filing artefacts, model/data-lake assets as defined by architecture

### 7.3 Encryption Requirements

1. All supported storage systems must have encryption at rest enabled using an AES-256 baseline.
2. All networked data transfer must use TLS 1.3.
3. Sensitive PII must additionally use field-level encryption.
4. Backups and snapshots must be encrypted.
5. Export files containing restricted/confidential data must be encrypted or access-controlled with expiry-bound delivery mechanisms.

### 7.4 PII and Sensitive Field Handling

Field-level encryption is mandatory for high-risk personal/business identifiers and equivalent sensitive fields, including examples such as:
- legal name where policy requires protected storage
- national ID or registration identifiers
- phone numbers where classified as sensitive in context
- bank/mobile money account identifiers
- tax IDs / payroll-linked identifiers
- provider tokens and credentials
- consent evidence linked to identifiable persons

Exact protected columns should be maintained in the schema/data model documentation and reflected in migration policy.

### 7.5 Tenant Isolation

1. Every business-scoped record must carry tenant ownership metadata.
2. Database row-level security must be used where defined for multi-tenant operational tables.
3. Cross-tenant reads are prohibited except for explicitly approved platform-admin workflows with audit capture.
4. Cached material must avoid cross-tenant contamination.
5. Vector retrieval/RAG queries must remain tenant-scoped for tenant-owned knowledge where applicable.

---

## 8. Financial Integrity and Idempotency Controls

### 8.1 Append-Only Financial Records

1. Transactions and ledger-affecting records are append-only.
2. Corrections must occur through reversal/adjustment entries, not destructive update/delete semantics.
3. Audit trails must preserve the full chain of financial state changes.
4. Any exception process must be ADR-backed and auditable.

### 8.2 Idempotency

Idempotency is mandatory for:
- inbound provider callbacks
- payment/mobile money ingestion
- manual transaction import paths
- compliance submission retries
- asynchronous job execution where duplicate side effects are possible

Rules:
1. Each protected write path must define an idempotency key scheme.
2. Idempotency windows and retention must be documented per flow.
3. Duplicate detection outcomes must be observable and logged.
4. Retry-safe behavior must be verifiable by tests.

---

## 9. API and Gateway Security Baseline

### 9.1 Kong Baseline

Kong must provide:
- JWT validation
- route-level auth policies
- subscription-tier or client-class rate limiting
- request size and abuse protection where applicable
- upstream timeout/circuit-breaker strategy
- audit-friendly correlation IDs

Staging/production baseline:
- HA topology with a **3-instance minimum**
- PostgreSQL-backed configuration in staging/production
- no single-point gateway deployment

### 9.2 API Design Security Requirements

1. OpenAPI contracts must be the source of truth for protected routes.
2. Request schemas must reject malformed/unexpected payloads.
3. Error payloads must avoid leaking internal topology, secrets, raw stack traces, or sensitive record contents.
4. Write endpoints must declare idempotency expectations where relevant.
5. Pagination and filtering must be safe against data overexposure.
6. Export/report endpoints must enforce role and tenant boundaries.

### 9.3 Webhook and Callback Security

All inbound provider callbacks must implement:
- signature verification or equivalent authenticity checks where available
- replay protection
- IP/source validation where feasible
- idempotency protection
- raw payload retention policy for debugging and audit
- normalized internal event mapping

---

## 10. Service-to-Service and Queue Security

### 10.1 Internal Service Communication

1. Internal APIs must use authenticated service identities.
2. mTLS is preferred for service-to-service traffic in staging and production.
3. Services must only call explicitly permitted upstreams.
4. Service accounts must be unique per workload/environment.

### 10.2 Kafka / Streaming Security

1. All Kafka topics must have schema-defined payloads (Avro).
2. Producers and consumers must authenticate using environment-specific credentials.
3. Topic ACLs must follow least privilege.
4. Sensitive payload content should be minimized; do not over-broadcast restricted data.
5. Dead-letter and replay processes must be controlled and auditable.

### 10.3 Asynq Outbound Queue Controls

The outbound API worker queue is a security-relevant control, not just an availability feature.

Rules:
1. All outbound calls to GRA, MTN MoMo, Vodafone Cash, bank feeds, and Anthropic API must be enqueued through Asynq.
2. No production direct synchronous calls from application handlers to those providers.
3. Backoff policy:
   - immediate
   - 5 seconds
   - 30 seconds
   - 5 minutes
   - 30 minutes
   - DLQ
   - ±20% jitter on all delays
4. Per-provider concurrency limits must be enforced.
5. DLQ events for critical providers must raise alerts.
6. GRA-related DLQ events must additionally alert the DPO/security/compliance path as specified by operations.
7. Queue metrics must be exported for monitoring.

---

## 11. Mobile, Web, USSD, and Offline Security

### 11.1 Mobile App Security

Baseline controls:
- secure auth token storage
- encrypted local SQLite/WAL storage for offline mode
- session expiry/reauth handling
- jailbreak/root detection strategy as product maturity warrants
- safe update/rollback practices for OTA distribution when enabled
- minimal local retention of restricted data

### 11.2 PWA/Web Security

Baseline controls:
- secure session/token handling
- CSP and browser-hardening headers
- protection against XSS/CSRF where applicable to architecture
- service-worker cache scoping to avoid sensitive data leakage
- secure export/download flows

### 11.3 USSD/SMS Security

Baseline controls:
- minimize sensitive data exposure in USSD/SMS content
- session state validation
- provider callback normalization and verification
- failover logic audited between direct telco APIs and Africa’s Talking fallback
- no secrets or sensitive identifiers exposed in logs or screen text

### 11.4 Offline Sync Security

1. Offline data stores must be encrypted.
2. Sync reconciliation must preserve auditability.
3. Conflicts involving financial or tax data must follow the approved conflict strategy; silent destructive overwrite is prohibited.
4. Sync APIs must return per-item outcomes so clients can reason about conflict, duplication, or rejection safely.
5. Device compromise assumptions must be reflected in local retention limits and forced revalidation after long offline periods.

---

## 12. AI/ML and NLP Security Baseline

### 12.1 Model and Inference Security

1. Pinned model identifiers must be treated as release-controlled constants.
2. Prompt/inference paths must not bypass tenant and authorization checks.
3. LLM outputs that can influence finance/compliance actions must be grounded against authoritative business data or regulation sources.
4. High-risk AI outputs must include confidence, provenance, or escalation logic where applicable.
5. Response caching must not leak data across tenants.

### 12.2 RAG / Vector Security

1. pgvector is the default vector store.
2. Pinecone production integration must not be scaffolded unless a formal later decision changes it.
3. Embedded content must be classified and tenant-scoped.
4. Retrieval boundaries must respect data ownership and sensitivity.

### 12.3 Prompt and Tool Security

1. Tool-enabled AI flows must use allowlisted tools/actions.
2. Generated actions that can trigger filings, notifications, or exports must require policy checks and human confirmation where defined.
3. Prompt injection resistance must be considered for document ingestion and external content workflows.
4. OCR/document parsing pipelines must sanitize and classify content before downstream use.

---

## 13. Logging, Audit, and Tamper Evidence

### 13.1 Logging Principles

1. Use structured logging across services.
2. Do not log secrets, raw access tokens, private keys, or unnecessary PII.
3. Logs must include correlation IDs/request IDs for traceability.
4. Security-relevant failures must be distinguishable from routine application errors.

### 13.2 Audit Events

At minimum, audit the following:
- authentication success/failure for privileged access
- role changes and permission grants
- consent capture/update/withdrawal
- tax/compliance rate changes
- filing submission/resubmission/cancellation
- export generation and download of sensitive reports
- provider credential changes and secret rotation events
- manual overrides in reconciliation or sync conflict handling
- administrative data-access events across tenant boundaries

### 13.3 Tamper-Evident Requirements

High-risk audit trails and financial/compliance event histories must be tamper-evident. The implementation may vary, but the baseline requires:
- append-only event retention where appropriate
- immutable storage or integrity verification for critical audit streams
- restricted write access to audit sinks
- alerting on audit pipeline disruption

---

## 14. Certificate and Cryptographic Lifecycle Management

Certificate management is a defined baseline requirement.

Controls:
1. TLS 1.3 is the required transport baseline.
2. Certificate inventory must be maintained for public ingress, internal gateways, and relevant service endpoints.
3. Renewal processes must be automated where possible.
4. Expiry monitoring and alerting are mandatory.
5. Changes that can affect pinning/client trust must be validated before release.
6. Post-deployment monitoring must confirm certificate changes did not break client access.

---

## 15. SDLC, CI/CD, and Environment Security

### 15.1 Repository and Build Security

1. CI must run at minimum:
   - lint
   - test
   - build
   - security scan
2. Include SAST and dependency scanning in GitHub Actions or equivalent pipeline.
3. Secrets scanning should be enabled pre-merge and in CI.
4. Build artefacts must be traceable to commits and releases.

### 15.2 Environment Separation

1. Local, staging, and production must use separate credentials and secrets.
2. Production data must not be copied to lower environments without formal approval and sanitization.
3. Access to production clusters and databases must be restricted and audited.

### 15.3 Release Security Checks

Before release of significant changes:
- unit/integration/contract tests green
- schema/migration review completed
- security scan reviewed
- performance/load test run for significant changes
- observability/alerting coverage confirmed
- rollback path verified

---

## 16. Vulnerability Management and Security Testing

### 16.1 Testing Baseline

1. External penetration testing is required as part of phase readiness.
2. Quarterly penetration testing is the baseline assurance cadence.
3. Annual security audits are required.
4. Critical/high findings must be tracked to remediation or formal risk acceptance.

### 16.2 Gate 1 Standard

Gate 1 cannot be passed unless:
- zero critical security findings remain open
- all high findings are remediated or formally risk-accepted
- evidence is available from the latest external security assessment

---

## 17. Incident Response and Operational Security

### 17.1 Minimum Preparedness

The platform must maintain:
- incident severity framework
- named on-call/security/compliance escalation paths
- runbooks for auth outage, provider outage, data leak suspicion, callback replay, queue/DLQ failure, certificate expiry, and suspected tenant-boundary breach
- evidence preservation procedures
- customer/regulator notification decision process aligned with compliance obligations

### 17.2 Detection Priorities

Alerts should exist for:
- repeated auth failures / MFA anomalies
- unexpected privilege changes
- abnormal export volume
- webhook signature failures / replay anomalies
- DLQ spikes for critical providers
- certificate expiry risk
- cross-tenant access violation indicators
- sudden increase in API error rate or latency correlated with security events

---

## 18. Control Matrix by Domain

| Domain | Minimum Baseline | Phase Priority |
|---|---|---|
| Identity & auth | Keycloak OIDC, Kong JWT validation, 15-minute JWTs, MFA for admins | Gate 1 |
| API gateway | Kong HA, rate limiting, schema validation, correlation IDs | Gate 1 |
| Data protection | AES-256 at rest, TLS 1.3, field-level PII encryption, tenant isolation | Gate 1 |
| Financial integrity | Append-only transactions, idempotency, auditable corrections | Gate 1 |
| Outbound integrations | Asynq queue, backoff/jitter, DLQ alerting, provider-specific concurrency limits | Gate 1 |
| Logging & audit | Structured logs, sensitive-data redaction, tamper-evident audit for high-risk actions | Gate 1 |
| Mobile/offline | encrypted local store, secure token storage, conflict-safe sync | Gate 1 |
| Queue/stream security | Authenticated producers/consumers, topic ACLs, controlled replay | Gate 1 |
| AI/NLP security | pinned models, grounded outputs, tenant-safe caching/RAG | Gate 2 |
| Bug bounty / advanced assurance | formal bug bounty program | Gate 3+ |

---

## 19. Evidence Required

Engineering and operations must be able to produce the following evidence:
- Keycloak realm/client/role configuration records
- Kong route/plugin/auth/rate-limit configuration
- secret storage and rotation procedures
- encryption-at-rest and TLS configuration evidence
- field-level encryption implementation references
- row-level security and tenant-isolation tests
- idempotency and duplicate-handling tests
- Asynq queue, retry, concurrency, and DLQ configuration
- logging and SIEM forwarding configuration
- certificate inventory and renewal monitoring
- penetration test reports and remediation tracker
- gate review checklist showing zero critical findings and high-finding disposition

---

## 20. Minimum Security Backlog for Sprint 0 / Phase 1

1. Stand up Keycloak and define clients/roles.
2. Stand up Kong in local dev and HA design for staging/production.
3. Define JWT claim contract between Keycloak, Kong, and services.
4. Implement secrets management pattern by environment.
5. Enable encryption at rest and TLS defaults across all stateful services.
6. Design and implement field-level encryption for protected PII fields.
7. Add row-level security/tenant scoping for multi-tenant operational tables.
8. Implement idempotency library/pattern for write and callback paths.
9. Implement audit event schema and structured logging baseline.
10. Implement Asynq queue pattern for all provider-bound outbound calls.
11. Add CI security scanning and dependency scanning.
12. Create incident runbooks and certificate monitoring basics.
13. Schedule external penetration testing ahead of Gate 1.

---

## 21. Open Items Requiring ADR or External Confirmation

The following may require later ADRs or supporting artefacts but do not weaken the baseline defined here:
- exact mTLS implementation approach inside Kubernetes/service mesh
- final secret-management product choice per environment
- exact field list for encrypted PII columns once schema stabilizes
- exact audit retention periods and immutable-storage implementation
- final SIEM product integration details
- production-grade device hardening posture for mobile endpoints
- regulator-specific breach notification workflow details

Until explicitly changed, teams must implement the strictest interpretation compatible with the approved architecture and compliance documents.
