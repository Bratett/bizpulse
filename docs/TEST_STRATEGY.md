# TEST_STRATEGY.md

## 1. Purpose

This document defines the canonical testing strategy for BizPulse AI across all phases of delivery. It exists to ensure the platform is validated **before implementation and before release** across functional correctness, financial integrity, compliance accuracy, security posture, performance, resilience, offline behavior, AI quality, and phase-gate readiness.

This is an implementation-facing strategy document. It does **not** replace executable test suites, OpenAPI contract tests, Avro schema compatibility checks, penetration tests, or provider certification packs. It defines what must be tested, when, by whom, with what environments, and what evidence is required for release and phase-gate decisions.

---

## 2. Source-of-Truth Position

`TEST_STRATEGY.md` sits between the implementation specifications and the executable quality assets:

- `ARCHITECTURE.md` defines system boundaries and runtime topology.
- `DATA_MODEL.md` defines entity integrity rules and storage boundaries.
- `API_CONTRACT.md` defines interface contracts that must be testable.
- `OFFLINE_SYNC_SPEC.md` defines disconnected behavior and conflict handling.
- `SECURITY_BASELINE.md` defines minimum security controls that require verification.
- `OBSERVABILITY_SLO.md` defines measurable operational targets and alerting expectations.
- `COMPLIANCE_MATRIX.md` defines control obligations that must be evidenced.

This file answers: **what evidence proves the system is fit to move from dev → staging → production → next phase gate?**

---

## 3. Testing Principles

### 3.1 Tests-first is mandatory

BizPulse follows a spec-first, tests-first workflow. Human-reviewed tests must be defined before functional implementation for services, workflows, and regulated calculations. The implementation spec explicitly warns against delegating vague build requests to the AI agent and directs teams to generate and review tests before writing functional code. fileciteturn27file5

### 3.2 Financial and compliance logic are not “best effort”

Financial records are append-only and idempotent by design; tax and compliance behavior must be validated against authoritative fixtures and approved rate tables rather than inferred during coding. The strategy therefore prioritizes deterministic test fixtures, reconciliation checks, and audit-trace verification over purely UI-centric testing. fileciteturn27file7turn27file8

### 3.3 Observability is part of testability

Every service must emit telemetry from its first commit. Test completion is not limited to “green tests”; it also requires logs, traces, metrics, and error reporting to be verifiable in staging and production-like conditions. Treating observability as post-MVP is explicitly prohibited. fileciteturn27file5

### 3.4 Offline and upstream-failure scenarios are first-class

BizPulse must function under intermittent connectivity, upstream throttling, provider outages, and telco failures. Testing must therefore cover offline storage, sync replay, conflict resolution, queue backoff, DLQ handling, and Africa’s Talking fallback rather than focusing only on happy-path online requests. fileciteturn27file3turn27file7

### 3.5 Phase gates require evidence, not verbal confidence

Release and phase transitions are governed by documented thresholds such as MVP completeness, security findings, p95 latency, uptime, and NLP resolution rates. Every gate must be backed by test evidence mapped to an owner. fileciteturn27file2turn27file4

---

## 4. Quality Objectives

The testing programme must prove the following before general availability of each scoped capability:

1. **Correctness:** Features satisfy the functional requirements and acceptance criteria.
2. **Integrity:** Financial, tax, sync, and reconciliation flows preserve exactness and prevent duplicate or destructive writes.
3. **Security:** No critical vulnerabilities; highs remediated or formally risk-accepted before gate progression.
4. **Performance:** Baseline concurrency and latency objectives are met under realistic load.
5. **Reliability:** Services degrade gracefully during outages, retries, failovers, and offline conditions.
6. **Compliance:** Regulated calculations, filings, audit trails, retention controls, and evidence outputs are correct.
7. **Usability under local constraints:** USSD, PWA on 2G, and offline workflows remain usable for target Ghana-market conditions.
8. **AI safety and quality:** NLP/advisory outputs stay within bounded behavior, use pinned model versions, and surface escalation paths where certainty is insufficient.

---

## 5. Scope of Testing

### 5.1 In scope

- Backend services: User, Transaction, Notification, Analytics, Compliance, NLP
- API gateway and auth boundaries (Kong + Keycloak)
- Shared contracts (OpenAPI, Avro)
- Datastores and persistence rules (PostgreSQL, TimescaleDB, Redis, pgvector, InfluxDB where applicable)
- Mobile app, PWA, and USSD channel behavior
- Offline sync flows and conflict handling
- External integrations: GRA, MTN MoMo, Vodafone Cash, bank feeds, SSNIT, Africa’s Talking, Anthropic
- CI/CD quality gates and rollback criteria
- Observability, alerting, and DR verification

### 5.2 Out of scope for automated AI-agent-only validation

The implementation spec explicitly states that certain areas cannot be fully delegated to the AI agent and require human or specialist review. The testing strategy therefore treats the following as **human-governed validation domains**:

- Ghanaian legal interpretation of GRA/API compliance rules
- Act 843 DPIA sign-off and cross-border transfer judgment
- Credit-scoring fairness review across protected demographic segments
- Twi/Ga/Ewe/Hausa/Dagbani linguistic accuracy validation
- Penetration test sign-off by a qualified external security practitioner
- Financial statement accuracy sign-off by a qualified accountant
- Regulatory phase-gate go/no-go decisions by the responsible leadership group fileciteturn27file5turn27file7

---

## 6. Test Pyramid and Layer Model

BizPulse uses a broadened test pyramid adapted for regulated, distributed systems.

### 6.1 Layer 0 — Static and design-time validation

Purpose: catch errors before runtime.

Includes:
- markdown/spec linting for docs-as-code artefacts
- OpenAPI validation
- Avro schema linting and compatibility checks
- SQL migration linting
- infrastructure-as-code validation
- secret scanning
- dependency policy scanning
- SAST on pull requests

### 6.2 Layer 1 — Unit tests

Purpose: validate isolated business rules quickly and deterministically.

Includes:
- tax/VAT/CST/PAYE/WHT calculators using fixture tables
- ledger append-only write policies
- idempotency key behavior
- retry/backoff calculation functions
- conflict resolution selectors
- NLP intent-routing rules for MVP rule-based classifier
- permissions/RBAC checks
- serialization/deserialization logic for contracts

Target: **minimum 80% coverage before PR merge** as defined in the requirements breakdown CI/CD workflow. Coverage alone is not sufficient; critical financial and compliance branches must be explicitly tested even if overall coverage exceeds threshold. fileciteturn27file4

### 6.3 Layer 2 — Contract tests

Purpose: verify service interfaces do not drift.

Includes:
- OpenAPI request/response contract tests for all service boundaries
- schema-based validation for public/internal REST APIs
- Kong header propagation and auth-claim forwarding checks
- Avro producer/consumer compatibility tests
- webhook signature and callback payload tests
- provider adapter conformance tests against recorded sandbox fixtures

### 6.4 Layer 3 — Integration tests

Purpose: validate service-to-service and service-to-datastore behavior in realistic environments.

Includes:
- transaction ingestion to ledger persistence
- compliance calculation to filing package generation
- analytics read models against TimescaleDB
- Asynq queue workers against Redis-backed retry behavior
- Keycloak-issued tokens accepted by Kong and trusted by downstream services
- pgvector embedding insert/search behavior
- document upload, OCR pipeline handoff, and metadata persistence
- notification fan-out and callback normalization

Integration tests run against staging-like backing services, not mocks only. The CI workflow explicitly calls for integration tests against a staging database before artifact promotion. fileciteturn27file4

### 6.5 Layer 4 — End-to-end and user-journey tests

Purpose: validate business-critical flows across multiple services and channels.

Includes:
- sign-up → connect MoMo → ingest transactions → generate P&L
- VAT computation → filing preparation → submission workflow
- inventory update offline → sync replay → conflict prompt on reconnect
- ask NLP assistant → structured answer → audit log → escalation path
- USSD session flow for low-connectivity users
- PWA on constrained network performing core dashboard tasks
- OTA update smoke tests for mobile beta releases

### 6.6 Layer 5 — Non-functional and operational tests

Purpose: validate production readiness.

Includes:
- performance/load/stress tests
- resilience/chaos/failover tests
- backup/restore and DR drills
- security verification and penetration testing
- observability verification
- rate-limit/backpressure behavior
- certificate lifecycle checks
- release rollback rehearsals

---

## 7. Test Types and Required Coverage

### 7.1 Functional testing

Must cover every accepted FR scope item in the currently active phase plan. At a minimum, each feature must have:
- acceptance criteria
- normal-path tests
- edge-case tests
- authorization tests
- audit/logging assertions where required
- failure-path behavior

For Gate 1, QA must be able to evidence **≥80% MVP feature completeness passing acceptance testing**. fileciteturn27file4turn27file2

### 7.2 Financial integrity testing

This is one of the highest-priority tracks.

Must verify:
- append-only behavior for financial records
- no destructive overwrite/delete paths in transaction history
- idempotent replay on duplicate upstream callbacks and offline resubmits
- deterministic statement calculations from fixed fixtures
- reconciliation across ingestion, ledger, and reporting read models
- audit traces for manual corrections and adjustments
- rollback behavior on partial failure in multi-step transaction workflows

### 7.3 Compliance and tax testing

Must verify:
- all tax rates come from configuration tables only
- no hard-coded rate literals in code paths
- output matches GRA test cases and approved fixtures
- XML/file packages conform to regulator-specified structures where available
- compliance rule changes require controlled approval and regression revalidation

The CI/CD workflow explicitly requires tax computation validation against GRA test cases during staging. fileciteturn27file4turn27file8

### 7.4 Security testing

Must include:
- SAST on pull requests
- dependency vulnerability scanning
- authn/authz negative-path testing
- MFA enforcement checks for privileged roles
- JWT validation at Kong boundary
- secret exposure checks
- encryption-at-rest and transport configuration verification
- audit logging presence for regulated actions
- external penetration testing before gate transition

Gate 1 requires **zero critical security findings** and remediation or formal risk acceptance of highs. fileciteturn27file4turn27file2

### 7.5 Performance and scalability testing

Baseline requirements include:
- load testing at **200 concurrent users** for significant changes in Gate 1 baseline
- **p95 API response time < 500 ms** under baseline test load
- PWA constrained-network target validation
- queue throughput and backlog drain testing
- database contention testing for high-write transaction paths
- horizontal scale checks where required

The requirements breakdown explicitly defines the 200-user load test and p95 API requirement as part of the deployment workflow. fileciteturn27file4turn27file6

### 7.6 Offline sync testing

Must cover all rules in `OFFLINE_SYNC_SPEC.md`, including:
- local queue persistence across app restarts
- encrypted SQLite WAL operation
- delta sync sequencing
- duplicate replay protection
- checksum reconciliation before merge commit
- partial batch rollback
- 30-day vs 7-day offline-window enforcement by tier where scoped
- conflict handling by data type:
  - financial transactions: append-only
  - settings: last-write-wins
  - inventory: manual resolution
  - tax inputs: server merge with audit trail
  - documents: version history
- user-facing conflict notification on next login

The requirements breakdown explicitly requires post-sync audit logging and manual inventory conflict confirmation before dashboard load. fileciteturn27file4turn27file7

### 7.7 Integration and provider testing

Must cover sandbox or controlled-fixture verification for:
- MTN MoMo
- Vodafone Cash
- bank feeds
- GRA
- SSNIT
- Anthropic models
- Africa’s Talking fallback path

Because upstream providers enforce rate limits, tests must include backoff, jitter, retry exhaustion, and DLQ behavior through Asynq. GRA DLQ behavior requires special escalation paths and must be included in staging verification. fileciteturn27file3

### 7.8 AI/NLP/advisory testing

Must verify:
- model version pinning is enforced
- rule-based intent classifier behavior for MVP
- prompt template determinism where applicable
- hallucination mitigation guards
- escalation for unsupported or low-confidence advice
- language fallback and unsupported-language behavior
- regression suite over approved prompt/query set
- NLP resolution rate measurement from first deployment

Gate 2 requires **NLP resolution ≥70%**; therefore the measurement pipeline and evaluation harness must exist before Phase 2 → 3 progression. fileciteturn27file2turn27file5

### 7.9 Usability and accessibility testing

Must cover:
- mobile usability for low-end Android devices
- USSD menu clarity and transaction safety prompts
- PWA performance on 2G-like profiles
- multilingual display and fallback behavior where scoped
- critical form flows under connectivity transitions

### 7.10 Observability verification

Must verify in staging and production-like environments:
- Datadog traces appear for HTTP/DB/Kafka paths
- custom metrics emit for sync, filings, NLP, queue, fallback events
- structured logs include required correlation IDs
- alerts fire at threshold and route correctly
- dashboards reflect current service inventory
- DLQ and failover metrics surface in the right team views

---

## 8. Phase-Based Testing Strategy

### 8.1 Sprint 0 / Phase 0 — Foundations

Required before substantial implementation:
- CI pipelines created
- SAST/dependency scanning enabled
- test harnesses scaffolded for Go, Python, web, mobile
- contract-test tooling selected and wired
- Datadog/metrics/logging baseline enabled
- sample fixtures for tax, transaction, and sync logic created
- OpenAPI and Avro validation wired into CI
- PR quality gates enforced

### 8.2 Phase 1 — Gate 1 foundation

Focus:
- service scaffolding correctness
- append-only transaction engine
- compliance and tax baseline
- auth/gateway correctness
- analytics and reporting basics
- early offline mechanics
- baseline performance/security evidence

Gate 1 exit evidence must include:
- MVP completeness ≥80%
- zero critical security findings
- baseline load-test evidence
- integration-test evidence across core services
- DPC/compliance-related evidence as defined in the gate checklist fileciteturn27file4turn27file2

### 8.3 Phase 2 — intelligence and beta expansion

Focus:
- NLP resolution and regression measurement
- OTA/mobile-beta verification
- broader offline and mobile test coverage
- reliability under partner sandbox conditions
- advisory-engine safety checks

### 8.4 Phase 3 — scale and national coverage

Focus:
- sustained uptime and regional rollout quality
- provider-throttle resilience
- queue scaling and backlog management
- stronger chaos/failover coverage
- API uptime evidence over 90 days for Gate 3 fileciteturn27file2

### 8.5 Phases 4–5 — ecosystem, APIs, commercialization, and regional expansion

Focus:
- partner/API certification suites
- B2B integration regression packs
- localization/regional compliance tracks
- DR/failover maturity
- long-horizon performance, capacity, and error-budget management

---

## 9. Environment Strategy

### 9.1 Local development

Purpose: fast feedback.

Should support:
- unit tests
- lightweight integration tests via containers/testcontainers
- contract validation
- fixture-driven calculators and queue logic
- offline client simulation where feasible

### 9.2 CI environment

Runs on every PR / merge as appropriate:
- static checks
- unit tests
- contract tests
- integration tests with ephemeral services where possible
- vulnerability scanning
- build validation

### 9.3 Staging

Purpose: production-like verification before release.

Must support:
- staging database/infrastructure
- smoke tests
- integration and end-to-end tests
- GRA test-case validation
- load tests for significant changes
- alert validation and trace inspection
- fallback and DLQ scenario drills

### 9.4 Production

Production is not for exploratory testing. It is for:
- smoke verification after controlled deploy
- canary/rolling update observation
- telemetry validation
- incident reproduction in a controlled manner
- game days with approved runbooks

The deployment workflow requires a 30-minute elevated monitoring window post deployment. fileciteturn27file4

---

## 10. Test Data Strategy

### 10.1 Principles

- Use deterministic, version-controlled fixtures.
- Separate synthetic, masked, and regulator-provided sample data.
- Never use raw production PII in lower environments.
- Ensure financial and compliance fixtures cover edge cases, reversals, adjustments, duplicates, missing timestamps, and malformed provider payloads.

### 10.2 Required fixture packs

1. **Financial fixtures**
   - cash-in/cash-out/mobile-money transactions
   - duplicate callbacks
   - partial failures
   - reconciliation mismatches

2. **Compliance fixtures**
   - valid and invalid tax periods
   - GRA XML cases
   - approved rate-table snapshots
   - payroll/SSNIT edge cases

3. **Offline fixtures**
   - stale versions
   - checksum mismatch scenarios
   - inventory collisions
   - tier-limit breaches

4. **AI/NLP fixtures**
   - approved intent/query corpus
   - low-confidence queries
   - unsupported language samples
   - prompt-injection and hallucination-challenge samples

5. **Provider fixtures**
   - rate-limit responses
   - timeout responses
   - malformed callback payloads
   - authentication failures

---

## 11. Automation Strategy

### 11.1 What must be automated

- static analysis
- unit tests
- contract tests
- the majority of integration tests
- smoke tests
- regression packs for core business flows
- load-test baseline scripts
- schema compatibility checks
- deployment quality gates
- observability presence checks where practical

### 11.2 What remains manual or human-supervised

- exploratory testing
- linguistic validation in Ghanaian languages
- accountant review of financial statement correctness
- legal/regulatory interpretation checks
- external penetration test execution and sign-off
- fairness review for credit-scoring models
- selected USSD usability sessions with target users

### 11.3 AI-agent role in testing

The AI agent may generate:
- test plans
- fixture scaffolds
- unit/integration test suites
- mock providers
- property-based test templates
- load-test scripts
- regression matrices

But the AI agent must not be treated as the final arbiter for:
- regulatory validity
- fairness sign-off
- security sign-off
- language-quality sign-off
- gate go/no-go decisions fileciteturn27file5turn27file7

---

## 12. Quality Gates in CI/CD

The requirements breakdown defines the canonical deployment workflow. The following gates are mandatory:

### 12.1 Pull request gate

Must pass before merge:
- unit coverage ≥80%
- SAST with no critical findings
- dependency scan within policy
- contract validation
- changed-code tests passing
- required peer review/sign-off

### 12.2 Main branch / build gate

Must pass before artifact publication:
- integration tests against staging-like database
- container build
- schema validation
- migration checks
- compliance sign-off for rate table changes

### 12.3 Staging gate

Must pass before production deploy:
- smoke tests
- end-to-end critical path tests
- tax/GRA validation
- observability presence verification
- performance baseline for significant changes
- rollback plan available

### 12.4 Post-deploy gate

Must be monitored after release:
- error rate under threshold
- p95 latency within expected band
- no alert storms or severe regression signals
- certificate checks clean
- fallback metrics stable

The requirements breakdown explicitly states that **error rate >1% triggers PagerDuty** during post-deployment monitoring. fileciteturn27file4

---

## 13. Resilience, DR, and Failure Testing

### 13.1 Queue and rate-limit testing

Because outbound provider calls must pass through Asynq, test suites must validate:
- retry schedule (immediate, 5s, 30s, 5m, 30m)
- ±20% jitter application
- retry exhaustion to DLQ
- safe replay after provider recovery
- no duplicate downstream business effect on retries
- alerting on DLQ
- DPO alert path for GRA DLQ events fileciteturn27file3

### 13.2 Telco and USSD fallback testing

Must validate:
- primary telco gateway failure detection
- activation after 3 consecutive primary failures within 60 seconds
- automatic traffic switch to Africa’s Talking
- session continuity expectations
- recovery/switchback conditions
- metrics and alert generation for failover events fileciteturn27file7turn27file9

### 13.3 DR / failover testing

Must validate:
- backup integrity
- restore drills
- regional failover runbooks
- RTO/RPO objectives where scoped
- Route 53 / standby promotion procedures where applicable
- annual full failover drill and bi-annual tabletop evidence fileciteturn27file1turn27file6

---

## 14. Security Verification Approach

### 14.1 Minimum automated security controls

- SAST on every PR
- dependency vulnerability scan on every build
- container image scanning
- IaC validation and policy checks
- secret scanning
- auth negative-path testing

### 14.2 Manual and specialist controls

- external penetration test before major gate transitions
- WAF/rule review where deployed
- SIEM alert validation
- certificate pinning/lifecycle verification
- abuse-case testing for payment and filing paths

### 14.3 Security release rule

No phase gate may be passed with unresolved critical findings. High findings require remediation or formal documented risk acceptance by the authorized governance group. fileciteturn27file4turn27file2

---

## 15. Observability and Test Evidence Requirements

For every critical test run, evidence should be retained as applicable:
- CI job URL / build number
- git commit SHA
- environment identifier
- structured test report
- logs/traces/metrics references
- screenshots or videos for channel/UI behavior where useful
- load-test summary
- security scan report
- sign-off owner and date

For incident-like failures in generated code, use the diagnostic reporting format described in the implementation spec: exact error, logs, request payload sans PII, trace ID, timestamp, frequency, and what has been ruled out. fileciteturn27file3

---

## 16. Roles and Responsibilities

### 16.1 Engineering

Owns:
- unit tests
- contract tests
- service integration tests
- migration tests
- queue/provider adapter tests
- observability instrumentation checks

### 16.2 QA / Quality Engineering

Owns:
- acceptance test design
- end-to-end suites
- regression packs
- release evidence collation
- feature completeness measurement
- exploratory testing coordination

### 16.3 SRE / Platform

Owns:
- performance/load testing
- resilience/failover drills
- alert validation
- environment parity and deployment verification

### 16.4 Security

Owns:
- scan policy definition
- vulnerability triage
- penetration test coordination
- security release recommendation

### 16.5 Compliance / Finance / Domain SMEs

Own:
- tax-rate verification sign-off
- GRA/SSNIT output review
- legal interpretation escalation
- financial-statement accuracy sign-off

### 16.6 Product / Gate committee

Own:
- phase-gate go/no-go decision based on evidence pack, not informal status updates fileciteturn27file5turn27file4

---

## 17. Phase-Gate Evidence Matrix

### 17.1 Gate 1 — Phase 1 → Phase 2

Required evidence:
- QA completion report showing MVP completeness ≥80%
- security report showing zero criticals
- baseline load-test report at 200 concurrent users with p95 API <500 ms
- core integration/e2e evidence for transactions, compliance, auth, and baseline offline behavior
- DPC/compliance readiness evidence as required by gate checklist
- sign-off pack stored in release records fileciteturn27file4turn27file2

### 17.2 Gate 2 — Phase 2 → Phase 3

Required evidence:
- NLP resolution-rate measurement ≥70%
- mobile/PWA/offline beta quality evidence
- expanded regression coverage for advisory and channel flows
- production-observability evidence showing stable trend lines over evaluation period fileciteturn27file2turn27file5

### 17.3 Gate 3 — Phase 3 → Phase 4

Required evidence:
- API uptime ≥99.5% over 90 days
- resilience and failover evidence
- scale/performance evidence aligned to rollout scope
- national coverage operations quality evidence where applicable fileciteturn27file2

### 17.4 Gate 4 — Phase 4 → Phase 5

Required evidence:
- partner/B2B integration certification packs
- API reliability evidence
- commercialization-readiness quality evidence
- regional expansion/regulatory test-readiness evidence fileciteturn27file2

---

## 18. Recommended Tooling Baseline

Final tool choices may evolve, but the minimum recommended approach is:

- **Go services:** `go test`, table-driven tests, fuzz/property tests where appropriate
- **Python services:** `pytest`, fixture-heavy business-rule testing, async worker tests
- **Web/PWA:** component tests + browser E2E suite
- **Mobile:** React Native component/integration/E2E test harnesses + offline simulation tools
- **API contracts:** OpenAPI validators and generated contract checks
- **Kafka:** Avro schema compatibility checks in CI
- **Load/perf:** repeatable scripts for baseline and stress scenarios
- **Security:** SAST, dependency, container, secret, and IaC scanners
- **Observability verification:** Datadog dashboards/trace queries + metric-presence checks

Tool selection must favor deterministic CI execution, low-maintenance operation, and compatibility with Go, Python, Next.js/PWA, and React Native stacks already locked in the architecture. fileciteturn27file7

---

## 19. Anti-Patterns to Avoid

1. Writing service code before acceptance tests and contract tests exist.
2. Measuring only code coverage and ignoring financial/compliance edge cases.
3. Treating mocks as sufficient proof for provider integrations.
4. Ignoring offline and retry behavior until late QA.
5. Deferring observability until after MVP.
6. Asking the AI agent to “fix the tests” without exact errors, logs, and traces.
7. Letting rate-table or model-version changes bypass regression checks.
8. Treating penetration-test sign-off, fairness review, or regulatory interpretation as automatable AI tasks. fileciteturn27file3turn27file5

---

## 20. Minimum Deliverables to Create Next

The following executable assets should be created immediately after this document is adopted:

1. `/tests/README.md` — repo-wide test execution guide
2. `/tests/fixtures/` — versioned domain fixture packs
3. `/tests/contracts/` — OpenAPI and Avro compatibility suites
4. `/tests/e2e/` — critical user-journey suites
5. `/tests/load/` — baseline and stress scripts
6. `/tests/security/` — auth and abuse-case regression suite
7. `/tests/offline/` — sync/conflict scenario pack
8. `/docs/GATE_CHECKLISTS/` — evidence checklists per gate
9. `/docs/TEST_REPORT_TEMPLATE.md` — standardized evidence template

---

## 21. Open ADR / Decision Dependencies

The following areas may require refinement of this strategy after binding decisions or external access are secured:

- final provider sandbox availability and certification rules
- Pinecone/pgvector DPIA final outcome (current default remains pgvector)
- exact mobile OTA rollout tooling configuration per environment
- detailed fairness evaluation protocol for future credit-scoring models
- final language QA staffing plan for Twi/Ga/Ewe/Hausa/Dagbani validation

Until those are resolved, this strategy remains valid as the baseline testing policy.

---

## 22. Maintenance Rule

Update `TEST_STRATEGY.md` whenever any of the following changes:
- phase gate criteria
- core architecture or service boundaries
- compliance obligations affecting verification
- offline conflict policy
- provider integration topology
- observability targets/SLOs
- release workflow or CI/CD controls
- AI model governance that affects evaluation

All material updates should be reflected in `DECISIONS.md` where they represent a binding architectural or governance decision, and summarized in `SESSION_LOG.md` at the end of the working session.
