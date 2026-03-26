# INTEGRATION_MANIFEST.md

## Document Control
- **Document:** Integration Manifest
- **System:** BizPulse AI
- **Version:** 1.0
- **Status:** Canonical implementation reference
- **Purpose:** Single source of truth for all third-party, partner, regulator, telecom, payments, AI, messaging, and platform integrations required to build and operate BizPulse AI.

---

## 1. Purpose and Scope

This document defines the complete integration estate for BizPulse AI. It exists to prevent a common failure mode in complex systems: engineering teams begin coding against an incomplete mental model of external dependencies, then later discover partner onboarding lead times, missing credentials, undocumented rate limits, callback edge cases, and regulatory prerequisites.

`INTEGRATION_MANIFEST.md` is therefore both:

1. a **build-time implementation reference** for engineers and AI coding agents, and
2. an **operational dependency register** for product, compliance, partnerships, DevOps, and security teams.

It must be kept current from pre-development through production scaling.

---

## 2. Architectural Role of Integrations

BizPulse AI is a multi-channel, compliance-heavy, offline-first platform serving Ghanaian SMEs. The platform consists of six backend microservices, four client delivery channels, a multi-database data layer, Kafka/Flink streaming, and a regulated external dependency surface spanning GRA, SSNIT, DPC, BoG-adjacent considerations, telcos, mobile money, and messaging providers. External integrations are therefore not peripheral; they are part of the core system boundary. fileciteturn17file0

The required pre-development artefacts explicitly include an integration manifest covering all third-party APIs such as MTN MoMo, Vodafone Cash, GhIPSS, GRA, SSNIT, and Africa’s Talking, including sandbox credentials, rate limits, and error codes. This file is that artefact. fileciteturn17file1

---

## 3. Integration Design Principles

### 3.1 Non-Negotiable Principles

1. **All primary data remains in AWS af-south-1.** No integration design may violate the primary data residency rule.
2. **All financial mutations are append-only and idempotent.** No upstream response may cause destructive overwrite of prior financial records.
3. **All outbound calls to rate-limited upstream providers must go through Asynq.** Direct synchronous provider calls from business-critical request paths are prohibited for rate-limited integrations. fileciteturn17file0turn17file2
4. **JWT validation occurs at Kong; service trust is internal.** Public integrations that enter through BizPulse APIs must respect the gateway trust boundary.
5. **Provider abstraction is required where a fallback exists.** The notification and USSD paths must be provider-agnostic behind internal interfaces.
6. **Callbacks/webhooks are normalized internally.** Upstream provider payloads are never propagated unmodified across the internal domain model.
7. **Sandbox-first, production-later.** Every external integration must define a sandbox readiness state before production onboarding.
8. **Secrets never live in code or markdown.** This document records secret locations and ownership, not actual secret values.

### 3.2 Integration Classification

All integrations must be classified into one of the following categories:

- **Regulatory / Government**
- **Payments / Financial Rails**
- **Telecom / USSD / SMS**
- **Messaging / Customer Communication**
- **AI / ML / Speech**
- **Commerce / Data Sources**
- **Identity / Security / Platform**
- **Observability / Operations**

---

## 4. Standard Integration Record Template

Every integration in this manifest should be maintained using the structure below:

- Integration name
- Category
- Business purpose
- Internal owner
- Primary consuming service(s)
- Environment(s): local / sandbox / staging / production
- Protocol(s): REST, webhook, SMPP, ISO 20022, SFTP, etc.
- Authentication method
- Required credentials / certificates
- Data classification handled
- Idempotency requirement
- Rate-limit profile
- Retry and backoff policy
- Circuit breaker / failover behavior
- Callback / webhook behavior
- Observability requirements
- Compliance / legal prerequisites
- Testing approach
- Production readiness checklist
- Known risks / assumptions

---

## 5. Cross-Cutting Integration Policies

### 5.1 Authentication and Secret Handling

- All API keys, OAuth secrets, certificates, webhook signing keys, and partner credentials must be stored in managed secret storage.
- Secrets must be environment-scoped.
- Rotation schedule, owner, and expiry dates must be tracked outside code.
- Mutual TLS, IP allowlisting, or signed callback verification must be enabled wherever the partner supports it.

### 5.2 Outbound Queue Policy

All outbound calls to rate-limited providers must be dispatched through **Asynq**, which the architecture locks as the outbound API queue for GRA, MTN MoMo, Vodafone Cash, bank feeds, and Anthropic Claude API. The rationale is explicit in the spec: external providers have inconsistent and sometimes undocumented rate limits, and unmanaged direct calling would create cascading failure at scale. fileciteturn17file0turn17file2

Required queue features for each outbound integration:

- provider-specific concurrency caps
- exponential backoff with jitter
- retry classification by status/error class
- dead-letter queue routing
- poison message detection
- idempotency key propagation where provider supports it
- correlation IDs across enqueue, request, callback, and final domain event

### 5.3 Webhook and Callback Policy

- All provider callbacks terminate at a dedicated ingestion edge.
- Signature verification is required when supported.
- Raw payload must be stored in immutable callback logs.
- Internal systems consume a normalized callback event schema.
- Callback processing must be idempotent.
- Duplicate and out-of-order callback delivery must be assumed.

### 5.4 Data Residency and Privacy Policy

- Provider payloads containing personal or financial data must be classified before integration approval.
- Cross-border processing implications must be reviewed by compliance for any provider with data egress outside approved residency boundaries.
- Vector-store-related data flows remain bound to the pgvector-first constraint unless a DPIA formally changes that decision. fileciteturn17file1

### 5.5 Environment Promotion Policy

No integration may be marked production-ready without:

- named owner
- sandbox credential validation
- error-code mapping completed
- retry policy approved
- observability dashboards defined
- runbook link created
- security review completed
- legal/compliance dependency status recorded

---

## 6. Integration Inventory Summary

| Integration | Category | Primary Service(s) | Phase | Criticality | State |
|---|---|---|---|---|---|
| Keycloak | Identity / Security | user-svc, gateway | Phase 0 | Critical | Required from Day 1 |
| Kong Gateway | Platform Edge | gateway, all services | Phase 0 | Critical | Required from Day 1 |
| Anthropic Claude API | AI / NLP | nlp-svc | Phase 1 | Critical | Required for NLP |
| Whisper / speech stack | AI / Speech | nlp-svc | Phase 1 | High | Required for voice workflows |
| MTN MoMo API | Payments | transaction-svc, notification-svc | Phase 1 | Critical | Long-lead dependency |
| Vodafone Cash API | Payments | transaction-svc, notification-svc | Phase 1 | Critical | Long-lead dependency |
| AirtelTigo telco integration | Telecom / USSD / SMS | custom USSD gateway, notification-svc | Phase 1/2 | High | Needed for direct telco path |
| GRA API / tax software registration | Regulatory | compliance-svc | Phase 1 | Critical | Long-lead dependency |
| SSNIT integration | Regulatory | compliance-svc | Phase 2 | High | Long-lead dependency |
| GhIPSS / ISO 20022 rails | Banking / Financial Rails | transaction-svc | Phase 2/3 | High | Partner dependent |
| Africa’s Talking | Telecom / SMS fallback | custom USSD gateway, notification-svc | Sprint 6 / Phase 1 | Critical | Mandatory fallback |
| WhatsApp Business API | Messaging | notification-svc, nlp-svc | Phase 2 | High | Channel expansion |
| Expo EAS Update | Mobile Ops | mobile | Phase 2 | High | OTA updates |
| MLflow | AI / Ops | ml, analytics-svc, nlp-svc | Phase 1 | Medium | Internal platform dependency |
| Datadog | Observability | all services | Phase 1 | High | Required for metrics/logs |
| CloudFlare | Edge Security | gateway/web | Phase 0 | High | WAF / DDoS |
| Bank feed partners (Ecobank, Fidelity, etc.) | Banking | transaction-svc, analytics-svc | Phase 3 | Medium/High | Expand by partnership |
| RGD / registrar integrations | Government | compliance-svc, user-svc | Phase 3+ | Medium | Future |
| Jumia / Tonaton / social commerce data sources | Commerce | analytics-svc | Phase 4 | Medium | Optional / strategic |
| Ghana Post GPS / logistics data | Logistics | analytics-svc, user-svc | Phase 4 | Medium | Optional / strategic |

This inventory is consistent with the architecture’s external integration surface and the pre-development requirement to document all third-party APIs before service implementation accelerates. fileciteturn17file1turn17file2

---

## 7. Detailed Integration Records

## 7.1 Keycloak

**Category:** Identity / Security  
**Purpose:** Identity provider for user authentication, tenant claims, role issuance, and session management.  
**Primary Consumers:** Kong, user-svc, all client applications  
**Phase:** Phase 0  
**Criticality:** Critical

### Design Notes
- Kong validates JWTs at the gateway boundary using Keycloak-issued tokens; downstream services trust verified claims from Kong headers. fileciteturn17file0
- MFA is required for admin-grade roles per the security baseline already established in the project.

### Protocol / Auth
- OIDC / OAuth 2.0
- JWT access tokens
- Refresh tokens for supported clients

### Required Artefacts
- realm configuration export
- client definitions per channel/app
- RBAC mapping to internal roles
- JWKS endpoint configuration in Kong

### Operational Requirements
- token expiry aligned with security baseline
- admin realm audit logging enabled
- environment-specific clients for local, staging, prod

---

## 7.2 Kong API Gateway

**Category:** Platform Edge  
**Purpose:** Central ingress, routing, JWT validation, rate limiting, traffic policy enforcement, and protection of internal microservices.  
**Primary Consumers:** all external and client traffic  
**Phase:** Phase 0  
**Criticality:** Critical

### Design Notes
- Kong HA topology is mandatory from Sprint 1; single-instance Kong is prohibited in staging/production. fileciteturn17file0
- Kong sits in front of mobile, PWA, USSD gateway integrations, and service APIs.

### Required Plugins / Controls
- JWT / OIDC auth
- inbound rate limiting
- request ID injection
- IP restrictions for admin surfaces
- CORS policies
- upstream timeout and circuit-breaker tuning

### Evidence Required
- declarative config repo path
- HA topology diagram
- plugin matrix by route

---

## 7.3 Anthropic Claude API

**Category:** AI / NLP  
**Purpose:** Language understanding and assistant responses for complex and simple query paths.  
**Primary Consumers:** nlp-svc  
**Phase:** Phase 1  
**Criticality:** Critical

### Locked Constraints
- model versions are pinned constants: `claude-sonnet-4-6` for complex NLP and `claude-haiku-4-5-20251001` for simple queries. Upgrades are formal release decisions. fileciteturn17file0
- outbound calls must route through Asynq like other rate-limited providers. fileciteturn17file0turn17file2

### Protocol / Auth
- HTTPS REST API
- API key / service credential

### Data Handling Notes
- redact or minimize sensitive payloads before upstream transmission
- retain request/response metadata separately from user content where possible
- log prompt and completion hashes, not raw content, unless explicitly approved for debugging

### Required Controls
- per-model timeout settings
- prompt template versioning
- fallback behavior when provider unavailable
- token usage metering
- region/privacy review

---

## 7.4 Speech / Voice Stack (Whisper or Equivalent)

**Category:** AI / Speech  
**Purpose:** Speech-to-text for English and local-language voice workflows.  
**Primary Consumers:** nlp-svc, mobile  
**Phase:** Phase 1  
**Criticality:** High

### Notes
- Voice is a core feature for low-literacy workflows and multilingual support.
- Cultural and linguistic validation remains a human responsibility even if the AI agent scaffolds the technical integration. fileciteturn17file0

### Requirements
- streaming or batch transcription path defined
- audio retention and deletion policy defined
- language identification confidence thresholds recorded
- failure fallback to text-only workflows

---

## 7.5 MTN MoMo API

**Category:** Payments / Mobile Money  
**Purpose:** Transaction ingestion, payment events, balance and settlement visibility, and SME financial workflow integration.  
**Primary Consumers:** transaction-svc, analytics-svc, notification-svc  
**Phase:** Phase 1  
**Criticality:** Critical

### Dependency Status
- Commercial agreement is a long-lead external dependency that must be initiated in Week 1. Delay puts the product’s core capability at risk. fileciteturn16file4turn16file6

### Protocol / Auth
- Partner API (exact auth to be confirmed from partner docs)
- Typically OAuth/client credentials and callback registration

### Required Credential Set
- base URL(s): sandbox and production
- client ID / secret
- API subscription key or equivalent
- callback secret / signing config
- whitelisted IPs / certificates if required

### Required Internal Capabilities
- transaction polling and/or subscription model
- webhook verification and normalization
- append-only ledger mapping
- reconciliation state model
- provider reference ↔ internal transaction correlation
- retry via Asynq for all outbound provider actions

### Rate-Limit / Retry Policy
- classify endpoints by read vs write vs status-check
- exponential backoff with jitter
- idempotent retry only on safe classes
- DLQ on repeated 429/5xx or semantic partner failures

### Observability
- success rate
- callback latency
- duplicate callback count
- reconciliation lag
- provider outage incidents

---

## 7.6 Vodafone Cash API

**Category:** Payments / Mobile Money  
**Purpose:** Same class of functionality as MTN MoMo for Vodafone Cash users and merchants.  
**Primary Consumers:** transaction-svc, analytics-svc, notification-svc  
**Phase:** Phase 1  
**Criticality:** Critical

### Dependency Status
- Commercial agreement is a long-lead external dependency that must be initiated in Week 1. fileciteturn16file4turn16file6

### Technical Policy
- same queueing, callback normalization, reconciliation, and idempotency requirements as MTN MoMo
- do not assume parity of field names, status vocabularies, or callback timing with MTN MoMo

---

## 7.7 Direct Telco APIs (MTN, Vodafone, AirtelTigo) for USSD/SMS

**Category:** Telecom / USSD / SMS  
**Purpose:** Primary routing path for USSD sessions and SMS notifications.  
**Primary Consumers:** custom USSD gateway, notification-svc  
**Phase:** Phase 1 onward  
**Criticality:** Critical for low-connectivity users

### Locked Architecture
- Primary route is a custom gateway to direct telco APIs.
- Africa’s Talking is mandatory fallback, activated automatically after 3 consecutive primary failures within 60 seconds or telco health-check failure. fileciteturn17file0turn17file2

### Requirements
- menu/session state compatibility across providers
- health-check sidecar implementation
- SMS status callback normalization
- provider-agnostic internal interface
- outage-aware routing metrics

### Legal / Regulatory Dependency
- NCA USSD licensing is a long-lead action and must be initiated early. fileciteturn16file4turn16file6

---

## 7.8 Africa’s Talking

**Category:** Telecom / SMS / USSD Fallback  
**Purpose:** Automated fallback aggregator for USSD and SMS when direct telco integrations fail.  
**Primary Consumers:** custom USSD gateway, notification-svc  
**Phase:** Sprint 6 / Phase 1  
**Criticality:** Critical

### Locked Architecture
- Africa’s Talking is the required fallback provider.
- Hubtel must not be used for this fallback role due to commercial conflict concerns.
- Fallback activates automatically based on health-check sidecar logic. fileciteturn17file0turn17file2

### Dependency Status
- Africa’s Talking account and API credentials are a long-lead dependency and should be initiated in parallel with Week 1 work; delay leaves the platform without automated recovery for direct telco outage. fileciteturn17file1

### Required Fields to Track
- application/account identifier
- sandbox credentials
- production credentials
- SMS sender IDs
- callback endpoints
- USSD short code mapping
- status code mapping
- throughput assumptions

### Internal Requirements
- fallback trigger state machine
- callback normalization to shared internal schema
- audit log of fallback activations
- Datadog custom metric `ussd.fallback.activated` per spec requirement. fileciteturn16file0

---

## 7.9 GRA API / Certified Tax Software Registration

**Category:** Regulatory / Government  
**Purpose:** VAT return workflows, tax filing exports/submissions, compliance automation, and release-time tax accuracy alignment.  
**Primary Consumers:** compliance-svc  
**Phase:** Phase 1  
**Criticality:** Critical

### Dependency Status
- GRA API access and Certified Tax Software registration are 3–6 month dependencies and must begin in Week 1. They are on the Gate 1 critical path. fileciteturn16file4turn16file6

### Required Artefacts
- API access approval status
- certified software registration status
- VAT XML schema
- endpoint catalogue
- environment guide
- sample payloads and error codes
- release verification procedure for current Finance Act rates

### Design Constraints
- all VAT/CST/CIT/PAYE/WHT rates must come from configuration tables, not code
- GRA VAT rates must be re-verified before every release
- compliance calculations must use decimal-safe arithmetic rules and money stored in integer pesewas in DB. fileciteturn16file0

### Retry / Queue Policy
- all submissions and status checks via Asynq
- explicit handling for duplicate filing attempts
- human review queue for ambiguous validation failures

---

## 7.10 SSNIT Integration

**Category:** Regulatory / Government  
**Purpose:** Payroll compliance workflows and statutory filing support.  
**Primary Consumers:** compliance-svc  
**Phase:** Phase 2  
**Criticality:** High

### Dependency Status
- SSNIT API access is a 2–4 month dependency and must be initiated early. fileciteturn16file4turn16file6

### Required Inputs
- file format specification
- transmission mechanism
- validation rules
- credential / certificate requirements
- error response taxonomy

### Internal Requirements
- payroll export generator
- filing status tracking
- reconciliation between payroll run and accepted submission

---

## 7.11 GhIPSS / ISO 20022 Financial Rails

**Category:** Banking / Financial Rails  
**Purpose:** Bank and interbank financial connectivity, future settlement rails, and standardized message interchange.  
**Primary Consumers:** transaction-svc, analytics-svc  
**Phase:** Phase 2/3  
**Criticality:** High

### Required Artefacts
- ISO 20022 documentation
- message schemas
- bank partner onboarding constraints
- certificate requirements
- status and settlement lifecycle rules

### Technical Requirements
- message validation pipeline
- canonical internal payment object
- signature and non-repudiation handling where applicable

---

## 7.12 Bank Feed Integrations (Ecobank, Fidelity, Others)

**Category:** Banking  
**Purpose:** Transaction import, cash visibility, and future reconciliation across business accounts.  
**Primary Consumers:** transaction-svc, analytics-svc  
**Phase:** Phase 3  
**Criticality:** Medium to High

### Design Policy
- bank-specific adapters behind common feed interface
- polling and webhook support abstracted internally
- per-bank onboarding tracked separately under this parent integration family

### Required Fields
- partner bank name
- onboarding status
- auth type
- statement/feed formats
- settlement lag expectations
- legal agreement status

---

## 7.13 WhatsApp Business API

**Category:** Messaging / Customer Communication  
**Purpose:** Business messaging channel, assistant interaction surface, and notifications for users preferring WhatsApp over app/web.  
**Primary Consumers:** notification-svc, nlp-svc  
**Phase:** Phase 2  
**Criticality:** High

### Required Controls
- template approval workflow
- inbound/outbound session rules
- user consent and opt-out tracking
- media handling policy
- callback normalization and delivery-state mapping

---

## 7.14 Expo EAS Update

**Category:** Mobile Operations  
**Purpose:** OTA delivery of JavaScript/asset bug fixes for the React Native mobile app.  
**Primary Consumers:** mobile, release engineering  
**Phase:** Phase 2  
**Criticality:** High

### Locked Policy
- EAS Update is the OTA mechanism.
- OTA applies only to JavaScript/asset changes; native changes require store submission.
- staged rollout begins with 10% beta users and a 2-hour observation window before full rollout.
- critical fixes use `FORCE_IMMEDIATE`; rollback to prior published update is the primary recovery mechanism. fileciteturn16file0

### Manifest Requirements
- release channel naming
- rollout approval owner
- rollback operator
- signing / trust requirements
- compatibility notes with SQLite encrypted WAL and pinned TLS updates

---

## 7.15 Datadog

**Category:** Observability / Operations  
**Purpose:** Metrics, logs, tracing, SLA evidence, fallback activation metrics, and operational alerting.  
**Primary Consumers:** all services, SRE, security, compliance operations  
**Phase:** Phase 1  
**Criticality:** High

### Requirements
- structured JSON logs from all services
- integration dashboards by provider
- alerts for callback failure, queue buildup, 429 bursts, cert expiry, and fallback activation
- custom metrics for critical integration state transitions

---

## 7.16 CloudFlare

**Category:** Edge Security / Operations  
**Purpose:** WAF, DDoS protection, and DNS/edge security in front of public endpoints.  
**Primary Consumers:** gateway/web surfaces  
**Phase:** Phase 0  
**Criticality:** High

### Requirements
- WAF rules per channel
- webhook path allowlisting strategy
- rate-limit exceptions for trusted partner callbacks where needed
- DNS and failover coordination with Route 53

---

## 7.17 Commerce / Marketplace Data Sources

**Category:** Commerce / Strategic Data  
**Purpose:** Optional future enrichment for market intelligence, pricing signals, and demand forecasting.  
**Primary Consumers:** analytics-svc  
**Phase:** Phase 4  
**Criticality:** Medium

### Candidate Sources
- Jumia
- Tonaton
- social commerce aggregators

### Policy
- treat as optional strategic integrations, not Gate 1 dependencies
- legal terms and scraping/API rights must be reviewed before implementation

---

## 7.18 Logistics / Addressing Data (Ghana Post GPS, Port/Logistics Signals)

**Category:** Logistics / Strategic Data  
**Purpose:** Address enrichment, supply-chain signals, and logistics-aware analytics.  
**Primary Consumers:** analytics-svc, user-svc  
**Phase:** Phase 4  
**Criticality:** Medium

---

## 8. Internal Integration Boundaries

Not all integrations are external vendors. The following internal boundaries must also be treated as formal contracts:

### 8.1 Service-to-Service APIs
- OpenAPI-defined boundaries between user-svc, transaction-svc, analytics-svc, compliance-svc, nlp-svc, and notification-svc
- auth, tenancy, idempotency, and error standards enforced consistently

### 8.2 Event Streaming Contracts
- Kafka topics use Avro schemas in `/shared/avro/`
- schemas registered before producer/consumer code generation
- event envelopes include timestamps, idempotency fields, and enrichment metadata. fileciteturn17file0

### 8.3 Callback Normalization Layer
- provider-specific callbacks transformed into canonical internal events
- raw and normalized forms both retained for audit/debugging

---

## 9. Integration Readiness Matrix

| Integration | Sandbox Ready | Error Map Complete | Retry Policy Defined | Callback Verified | Security Reviewed | Legal/Partner Status | Production Ready |
|---|---|---|---|---|---|---|---|
| Keycloak | Yes | n/a | n/a | n/a | Required | Internal | Pending environment setup |
| Kong | Yes | n/a | n/a | n/a | Required | Internal | Pending HA validation |
| Anthropic Claude API | Pending | Pending | Required | n/a | Required | Commercial review | No |
| MTN MoMo | Pending | Pending | Required | Pending | Required | Agreement required | No |
| Vodafone Cash | Pending | Pending | Required | Pending | Required | Agreement required | No |
| Direct Telco APIs | Pending | Pending | Required | Pending | Required | NCA + partner setup | No |
| Africa’s Talking | Pending | Pending | Required | Pending | Required | Account setup required | No |
| GRA API | Pending | Pending | Required | Pending | Required | Registration required | No |
| SSNIT | Pending | Pending | Required | Pending | Required | Access required | No |
| GhIPSS | Pending | Pending | Required | Pending | Required | Partner/legal required | No |
| WhatsApp Business API | Pending | Pending | Required | Pending | Required | Meta onboarding | No |
| Expo EAS Update | Yes | n/a | n/a | n/a | Required | Internal | Pending release workflow |
| Datadog | Yes | n/a | n/a | n/a | Required | Internal | Pending dashboard setup |

This table should be updated continuously during onboarding.

---

## 10. Credential and Secret Registry Requirements

This manifest must reference, but never contain, the following metadata for each integration:

- secret storage path / vault reference
- owning team / person
- creation date
- expiry / rotation date
- environment scope
- linked runbook
- linked onboarding document
- linked test evidence

Example metadata fields:

| Integration | Secret Ref | Owner | Rotation | Notes |
|---|---|---|---|---|
| MTN MoMo | `vault://bizpulse/prod/mtn-momo` | Platform Eng | 90 days | partner-controlled refresh may vary |
| Vodafone Cash | `vault://bizpulse/prod/vodafone-cash` | Platform Eng | 90 days | webhook key separate |
| Africa’s Talking | `vault://bizpulse/prod/africastalking` | Platform Eng | 90 days | SMS sender IDs tracked separately |
| Anthropic | `vault://bizpulse/prod/anthropic` | NLP Lead | 60 days | usage alerts required |

---

## 11. Standard Error Normalization Model

Each external integration should map raw provider errors into a shared internal taxonomy:

- `AUTHENTICATION_FAILED`
- `AUTHORIZATION_FAILED`
- `RATE_LIMITED`
- `TEMPORARY_UPSTREAM_FAILURE`
- `PERMANENT_UPSTREAM_FAILURE`
- `INVALID_REQUEST`
- `DUPLICATE_REQUEST`
- `INVALID_CALLBACK_SIGNATURE`
- `PARTNER_CONFIGURATION_ERROR`
- `REGULATORY_VALIDATION_FAILURE`
- `MANUAL_REVIEW_REQUIRED`

Provider-specific error codes must be preserved in metadata, but internal business logic should branch only on normalized classes unless a provider-specific exception is justified.

---

## 12. Retry, Idempotency, and Reconciliation Standards

### 12.1 Retry Classes

**Retry automatically:**
- network timeouts
- connection resets
- HTTP 429
- HTTP 5xx where provider documentation permits retry
- temporary certificate/network edge issues after validation

**Do not retry automatically:**
- authentication failures
- schema validation failures
- malformed requests
- business-rule rejections
- permanent compliance validation rejections

### 12.2 Idempotency Standards

- all mutation APIs inside BizPulse must enforce idempotency keys
- where providers support idempotency, forward the internal key or a deterministic derivative
- where providers do not support idempotency, internal request journals must prevent duplicate effect
- callback processors must be idempotent by provider event ID + payload fingerprint

### 12.3 Reconciliation Standards

Required for payment and filing integrations:

- raw provider transaction/submission record retained
- internal canonical record retained
- comparison/reconciliation job scheduled
- unresolved mismatch escalates to operations queue
- manual override requires audit note

These rules align with the append-only financial architecture and the idempotency requirements already locked in the implementation spec. fileciteturn17file0turn16file0

---

## 13. Testing Strategy by Integration Type

### 13.1 Required Test Layers

- unit tests for adapter logic
- contract tests for request/response schemas
- callback/webhook signature verification tests
- sandbox integration tests
- failure-injection tests for timeouts, 429s, malformed callbacks
- replay/idempotency tests
- reconciliation tests
- observability assertion tests for required metrics/logs

### 13.2 Special Cases

- USSD fallback tests must simulate 3 consecutive direct-telco failures within 60 seconds and verify automatic routing to Africa’s Talking. fileciteturn17file0turn17file2
- GRA release tests must include current-rate verification evidence.
- mobile OTA tests must verify staged rollout and instant rollback behavior.

---

## 14. Ownership Model

| Integration Family | Primary Owner | Secondary Owner |
|---|---|---|
| Identity / Gateway | Platform Engineering | Security Lead |
| Regulatory APIs | Compliance Officer + compliance-svc lead | Legal Counsel |
| Mobile Money / Banking | Technical Lead + transaction-svc lead | Partnerships |
| USSD / SMS / Telco | Notification lead + platform engineering | Partnerships / Ops |
| AI / NLP | NLP lead | Security / Compliance |
| Messaging Channels | notification-svc lead | Product / CX |
| Observability / Edge | SRE Lead | Security Lead |

---

## 15. Open Items and ADR Triggers

The following changes require ADR updates rather than silent edits to this manifest:

1. replacing Africa’s Talking fallback provider
2. changing the outbound queue away from Asynq
3. moving token validation away from Kong
4. adopting Pinecone for production prior to formal DPIA outcome
5. adding a new core regulatory or payment provider
6. changing data residency assumptions for any integration payloads

---

## 16. Immediate Next Actions

### Phase 0 / Week 1 Actions
1. Create onboarding trackers for GRA, MTN MoMo, Vodafone Cash, DPC, SSNIT, NCA, and Africa’s Talking. fileciteturn17file1turn16file6
2. Create per-provider credential placeholders in secret management.
3. Define normalized callback/event schemas.
4. Scaffold Asynq job classes for provider categories.
5. Create Datadog dashboards and alert skeletons for provider health.
6. Record known rate limits and error codes as they are received from vendors.
7. Attach sandbox status to each manifest entry.

### Before Each Service Sprint
- confirm all required upstream documents are attached
- confirm sandbox credentials exist
- confirm OpenAPI/Avro contract dependencies are ready
- confirm retry and idempotency approach is documented
- confirm security review status is known

---

## 17. Maintenance Rule

This document is a living operational artefact. Update it whenever any of the following change:

- a new provider is added
- credentials rotate
- rate limits change
- callback schemas change
- compliance posture changes
- an integration moves from sandbox to production
- a fallback path changes
- an ADR affects integration behavior

If `ARCHITECTURE.md` defines the system shape, `DATA_MODEL.md` defines the persistence model, and `API_CONTRACT.md` defines the interface layer, then `INTEGRATION_MANIFEST.md` defines the external dependency perimeter and how BizPulse survives contact with the real world.
