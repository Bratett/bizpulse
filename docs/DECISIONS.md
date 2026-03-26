# DECISIONS.md

## Purpose

This file is the Architecture Decision Record (ADR) log for BizPulse AI. It records binding technical, platform, compliance, and operating decisions that shape implementation. It exists so that every AI-agent session, human engineer, and reviewer can answer four questions quickly:

1. What was decided?
2. Why was it decided?
3. What alternatives were rejected?
4. What follow-up work or review trigger exists?

This document should be updated whenever a meaningful architectural, security, data, integration, delivery-channel, or ML governance decision is made. The unified implementation specification explicitly requires `docs/DECISIONS.md` as a maintained artefact and states that foundational architecture choices must be captured as ADRs before code generation begins.

---

## How to Use This File

- Treat every entry here as a binding engineering constraint unless it is explicitly marked **Superseded** or **Proposed**.
- Read this file before generating or modifying architecture, service scaffolding, integration code, or infra code.
- When a decision changes, do **not** silently rewrite history. Add a new ADR entry that supersedes the prior one.
- Link implementation artefacts, specs, or follow-up tickets in the “Consequences / Follow-up” section.
- Decisions that remain externally dependent (for example, DPIA outcomes, partner credentials, regulator interpretation, fairness governance) must remain visibly open until formally closed.

---

## Status Legend

- **Accepted** — Binding and approved for implementation
- **Proposed** — Preferred direction, not yet binding
- **Deferred** — Deliberately postponed
- **Superseded** — Replaced by a later ADR
- **Rejected** — Considered and explicitly not chosen
- **Open** — Requires external validation, approval, or time-bound resolution

---

## ADR Template

Use this template for all new entries.

```md
## ADR-XXXX: Short Decision Title
- Date:
- Status:
- Owners:
- Scope:

### Context
Describe the problem, constraint, or decision pressure.

### Decision
State the decision in one or two clear sentences.

### Rationale
Why this option was chosen.

### Alternatives Considered
- Option A — why not chosen
- Option B — why not chosen

### Consequences / Follow-up
- Immediate implementation implications
- Risks
- Review trigger or expiry condition
- Linked artefacts / tickets
```

---

# Accepted ADRs

## ADR-0001: Default Vector Store Is pgvector Until DPIA Confirms Otherwise
- Date: 2026-03-19
- Status: **Accepted**
- Owners: CTO, DPO, Lead Architect
- Scope: RAG, embeddings, retrieval, AI infrastructure

### Context
BizPulse requires vector retrieval for AI workflows, but cross-border data transfer implications remain subject to DPIA review under Ghana’s data protection obligations. The implementation spec explicitly blocks Pinecone as the default production choice until adequacy is confirmed.

### Decision
Use **pgvector** as the default and implementation-target vector store for all RAG and embedding features. Do not scaffold Pinecone production integration unless a later ADR explicitly changes this after DPIA approval.

### Rationale
pgvector keeps vector data within the existing PostgreSQL stack, reduces operational sprawl, and avoids building a production dependency on a transfer path that may fail compliance review.

### Alternatives Considered
- **Pinecone now** — rejected because adequacy is not yet confirmed and would introduce compliance and migration risk.
- **Dual-write pgvector + Pinecone** — rejected because it adds complexity before a decision is justified.

### Consequences / Follow-up
- All retrieval code should target PostgreSQL + pgvector abstractions.
- Any Pinecone experiment must be isolated from production pathways.
- Review trigger: formal DPIA outcome and executive approval.
- Related artefacts: `ARCHITECTURE.md`, `DATA_MODEL.md`, `ML_MODEL_REGISTRY.md`.

---

## ADR-0002: Financial Transaction Records Are Append-Only / Event-Sourced
- Date: 2026-03-19
- Status: **Accepted**
- Owners: Lead Architect, Compliance Lead, Transaction Service Owner
- Scope: transaction engine, ledgering, reconciliation, sync

### Context
The platform handles business-critical financial records and compliance-relevant transaction histories. The specification requires immutability and idempotency rather than mutable CRUD-style financial updates.

### Decision
Model financial transactions as **append-only events**. Never overwrite or delete financial facts in-place. Corrections must be represented by compensating or superseding events, not destructive edits.

### Rationale
Append-only architecture preserves auditability, supports reconciliation, aligns with compliance needs, and avoids trying to retrofit immutability later.

### Alternatives Considered
- **Standard CRUD transaction table** — rejected because it weakens audit integrity and complicates compliance evidence.
- **Mutable summary tables as source of truth** — rejected because summaries should be derived, not authoritative.

### Consequences / Follow-up
- Idempotency keys are mandatory on transaction writes and ingestion paths.
- Reconciliation and reporting pipelines must read immutable source events.
- Derived balance/snapshot tables may exist, but they are not the source of truth.
- Related artefacts: `DATA_MODEL.md`, `API_CONTRACT.md`, `OFFLINE_SYNC_SPEC.md`, `SECURITY_BASELINE.md`.

---

## ADR-0003: Tax and Compliance Rates Live in Configuration Tables, Not Code
- Date: 2026-03-19
- Status: **Accepted**
- Owners: Compliance Lead, Data Lead, Backend Leads
- Scope: compliance engine, payroll, tax calculations, reporting

### Context
The requirements specify that tax-rate changes must be possible without code deployment and must be verified against current official publications before release.

### Decision
Store VAT, CST/NHIL/GETFund, CIT, PAYE, WHT, and related compliance rates in **configuration tables only**. Hardcoded rate literals in application logic are prohibited.

### Rationale
Tax and regulatory rates change over time. Configuration-driven storage enables safe updates, auditability, and release discipline.

### Alternatives Considered
- **Hardcoded constants in services** — rejected because rate changes would require code changes and raise audit risk.
- **Per-service rate duplication** — rejected because it creates inconsistency and drift.

### Consequences / Follow-up
- Validation, effective-date modeling, and approval workflow are required.
- CI or review rules should reject hardcoded rate literals where feasible.
- Review trigger: new Finance Act or regulator publication.
- Related artefacts: `DATA_MODEL.md`, `COMPLIANCE_MATRIX.md`, `SECURITY_BASELINE.md`.

---

## ADR-0004: Claude Model Versions Are Pinned and Release-Controlled
- Date: 2026-03-19
- Status: **Accepted**
- Owners: AI Lead, Product Lead, CTO
- Scope: NLP service, advisory workflows, prompt orchestration

### Context
The technical specification pins model versions and requires review before any upgrade because model behavior changes can affect reliability, cost, and user experience.

### Decision
Treat `claude-sonnet-4-6` for complex NLP and `claude-haiku-4-5-20251001` for simpler workloads as pinned production constants until changed by a formal release decision.

### Rationale
Pinning preserves reproducibility, regression control, and cost/performance predictability.

### Alternatives Considered
- **Always use latest available model** — rejected because it introduces silent behavior change.
- **Unpinned environment-based selection** — rejected because it weakens release governance.

### Consequences / Follow-up
- Model changes require testing, documentation, and a new ADR.
- Fallback logic may route between pinned models, but not to unapproved versions.
- Related artefacts: `ML_MODEL_REGISTRY.md`, `OBSERVABILITY_SLO.md`, `CLAUDE.md`.

---

## ADR-0005: Kong Runs in HA Topology From Phase 1
- Date: 2026-03-19
- Status: **Accepted**
- Owners: Platform Lead, Security Lead
- Scope: gateway, ingress, runtime topology

### Context
The requirements and implementation guide explicitly prohibit a single-instance Kong deployment in staging or production. Gateway downtime would affect every channel and service.

### Decision
Deploy **Kong as a minimum three-instance HA topology** from Sprint 1 onward for non-local environments.

### Rationale
The API gateway is a platform choke point. Retrofitting HA later is a production-risk event and violates the specs.

### Alternatives Considered
- **Single-instance Kong then scale later** — rejected because the spec explicitly disallows it.
- **Different gateway platform now** — rejected because the architecture already commits to Kong.

### Consequences / Follow-up
- Terraform, Kubernetes, and runbooks must assume HA from the start.
- Local development may use single-instance Kong only as a dev convenience.
- Related artefacts: `ARCHITECTURE.md`, `SECURITY_BASELINE.md`, `OBSERVABILITY_SLO.md`.

---

## ADR-0006: Kong Validates JWTs at the Gateway Boundary, Keycloak Is the IdP
- Date: 2026-03-19
- Status: **Accepted**
- Owners: Security Lead, Platform Lead
- Scope: auth, identity, gateway, services

### Context
The platform requires centralized identity management and gateway-enforced access. The specifications assign identity to Keycloak and token validation to Kong.

### Decision
Use **Keycloak** as the identity provider and **Kong** as the enforcement point that validates JWTs at the gateway. Downstream services trust verified claims forwarded by Kong and avoid duplicative token validation unless a specific exception is documented.

### Rationale
This centralizes policy enforcement, simplifies services, and reduces repeated security logic.

### Alternatives Considered
- **Every service validates tokens independently** — rejected because it duplicates auth logic and increases inconsistency risk.
- **No dedicated IdP** — rejected because it conflicts with the architecture and compliance posture.

### Consequences / Follow-up
- Claims contract and header propagation rules must be defined.
- Admin access must layer MFA and RBAC on top of this model.
- Related artefacts: `API_CONTRACT.md`, `SECURITY_BASELINE.md`, `ARCHITECTURE.md`.

---

## ADR-0007: Offline Sync Uses a Per-Data-Type Conflict Strategy
- Date: 2026-03-19
- Status: **Accepted**
- Owners: Mobile Lead, Platform Lead, Product Lead
- Scope: mobile, PWA, offline sync, reconciliation

### Context
BizPulse is explicitly offline-first and targets users with intermittent connectivity. A one-size-fits-all conflict strategy would be unsafe across financial, inventory, settings, and compliance data.

### Decision
Apply conflict resolution by data type:
- Financial transactions: append-only, no overwrite
- Business settings/profile: last-write-wins
- Inventory counts: manual resolution prompt
- Tax computation inputs: server-side merge with audit trail
- Documents: version-history approach
- NLP conversation history: device-local only, not synced cross-device

### Rationale
Different domains carry different risk and traceability requirements. The policy is already fixed in the specification and must be implemented directly.

### Alternatives Considered
- **Single global last-write-wins** — rejected because it is unsafe for financial and inventory data.
- **Manual conflict resolution for everything** — rejected because it would degrade usability and throughput.

### Consequences / Follow-up
- API responses must support per-item conflict outcomes.
- QA must test each conflict class separately.
- Related artefacts: `OFFLINE_SYNC_SPEC.md`, `API_CONTRACT.md`, `DATA_MODEL.md`.

---

## ADR-0008: Backend Language Split Is Go for Core Operational Services and Python for Analytics / Compliance / NLP
- Date: 2026-03-19
- Status: **Accepted**
- Owners: CTO, Lead Architect
- Scope: service scaffolding, hiring, tooling, CI/CD

### Context
The implementation guide assigns languages before scaffolding to prevent random per-service choices and toolchain fragmentation.

### Decision
Use **Go** for User Service, Transaction Service, and Notification Service. Use **Python** for Analytics Service, Compliance Service, and NLP Service.

### Rationale
This matches the strengths of each service domain while preserving a coherent runtime model and staffing plan.

### Alternatives Considered
- **All services in one language** — rejected because it would compromise either operational efficiency or AI/ML velocity.
- **Ad hoc per-team language choice** — rejected because it weakens maintainability and onboarding.

### Consequences / Follow-up
- Shared tooling, testing, and observability must respect the split.
- New services should inherit one of these language tracks unless a new ADR says otherwise.
- Related artefacts: `ARCHITECTURE.md`, `CLAUDE.md`, `ML_MODEL_REGISTRY.md`.

---

## ADR-0009: Kafka Event Schemas Use Avro and Must Be Registered Before Producer/Consumer Code
- Date: 2026-03-19
- Status: **Accepted**
- Owners: Data Platform Lead, Service Owners
- Scope: eventing, Kafka, Flink, schema evolution

### Context
The implementation spec fixes Avro as the Kafka schema format and requires registered schemas before code generation for producers or consumers.

### Decision
Use **Avro** as the message schema format for Kafka topics. Store schemas in `/shared/avro/` and require schema registration and review before production event code is generated.

### Rationale
Schema governance is required for event evolution, compatibility, and multi-service coordination.

### Alternatives Considered
- **JSON without schema governance** — rejected because it weakens compatibility guarantees.
- **Proto for Kafka events** — rejected because Avro is already the project-standard choice.

### Consequences / Follow-up
- Idempotency fields and ISO 8601 timestamps are mandatory in relevant topics.
- Event contract review becomes a precondition for queue and stream work.
- Related artefacts: `API_CONTRACT.md`, `OBSERVABILITY_SLO.md`, `DATA_MODEL.md`.

---

## ADR-0010: Africa’s Talking Is the USSD/SMS Fallback Provider
- Date: 2026-03-19
- Status: **Accepted**
- Owners: CTO, Partnerships Lead, Platform Lead
- Scope: USSD, SMS, resilience, channel continuity

### Context
USSD is a primary continuity channel for low-connectivity users. The v1.2 review adds a mandatory fallback provider choice and explicitly prefers Africa’s Talking over Hubtel due to commercial conflict concerns.

### Decision
Use **Africa’s Talking** as the designated automated fallback provider for USSD session rerouting and SMS delivery when direct telco integrations fail health checks or cross the configured failure threshold.

### Rationale
This preserves channel continuity, avoids competitor dependency, and matches the updated architecture guidance.

### Alternatives Considered
- **Hubtel fallback** — rejected due to commercial conflict concerns.
- **No fallback provider** — rejected because telco outages would disproportionately affect users who rely most on USSD.

### Consequences / Follow-up
- Notification normalization must be provider-agnostic.
- Sidecar health-check and routing-switch logic are required.
- Credentials and callback specs must be captured in `INTEGRATION_MANIFEST.md`.
- Related artefacts: `ARCHITECTURE.md`, `INTEGRATION_MANIFEST.md`, `OBSERVABILITY_SLO.md`.

---

## ADR-0011: Asynq Is the Standard Outbound API Queue for Rate-Limited Upstream Calls
- Date: 2026-03-19
- Status: **Accepted**
- Owners: Platform Lead, Service Owners
- Scope: outbound integrations, retries, DLQ, resilience

### Context
Third-party providers such as GRA, MTN MoMo, Vodafone Cash, bank feeds, and the Anthropic API impose rate limits and intermittent failures. The v1.2 review adds a dedicated outbound worker queue requirement.

### Decision
Use **Asynq** as the standard queueing mechanism for outbound calls to rate-limited upstream providers. Route these calls through retry-aware queues rather than issuing them directly in-path from request handlers.

### Rationale
Asynq fits the Go-heavy services landscape, reuses Redis already in the stack, and formalizes backoff, concurrency control, and DLQ handling.

### Alternatives Considered
- **Direct synchronous provider calls** — rejected because it risks cascading failures and poor latency under throttling.
- **Celery / Sidekiq** — rejected because they add runtime/tooling divergence without enough benefit in this architecture.

### Consequences / Follow-up
- Per-provider retry and concurrency policies must be documented.
- DLQ metrics and PagerDuty paths are required.
- Related artefacts: `INTEGRATION_MANIFEST.md`, `OBSERVABILITY_SLO.md`, `SECURITY_BASELINE.md`.

---

## ADR-0012: Primary Cloud Region Is AWS af-south-1 With eu-west-1 for DR Only
- Date: 2026-03-19
- Status: **Accepted**
- Owners: CTO, Platform Lead, Compliance Lead
- Scope: cloud infrastructure, residency, DR

### Context
The requirements breakdown fixes primary data residency in AWS Africa (Cape Town) and allows cross-region replication to eu-west-1 for disaster recovery only.

### Decision
Use **AWS af-south-1** as the primary cloud and data residency region. Limit **eu-west-1** usage to disaster recovery and explicitly approved replication paths.

### Rationale
This aligns with residency expectations, latency goals, and the documented regional operating model.

### Alternatives Considered
- **Primary hosting outside Africa** — rejected because it conflicts with stated residency direction.
- **Multi-primary across regions at launch** — rejected because it adds complexity without a launch need.

### Consequences / Follow-up
- Terraform, backup, and DR documentation must reflect this split.
- Any new data transfer outside primary residency requires formal review.
- Related artefacts: `ARCHITECTURE.md`, `COMPLIANCE_MATRIX.md`, `SECURITY_BASELINE.md`.

---

# Open / Time-Bound ADRs

## ADR-0013: DPIA Final Outcome for Pinecone vs. pgvector
- Date: 2026-03-19
- Status: **Open**
- Owners: DPO, CTO
- Scope: vector platform strategy

### Context
The implementation guide sets a binding DPIA schedule and a drop-dead date to prevent indefinite ambiguity.

### Current Position
pgvector is the implementation default. Pinecone remains blocked for production until adequacy is confirmed.

### Required Resolution
By the end of Phase 1, either:
- confirm Pinecone adequacy and record a superseding ADR, or
- formally commit to pgvector as the permanent production vector store.

### Consequences / Follow-up
- No production Pinecone scaffolding before closure.
- This ADR must be closed no later than the end of Phase 1.

---

## ADR-0014: Credit Scoring Fairness Governance and Approval Workflow
- Date: 2026-03-19
- Status: **Open**
- Owners: AI Lead, Compliance Lead, Executive Sponsor
- Scope: credit scoring, ethics, fairness, access decisions

### Context
The technical specification requires demographic fairness evaluation, human-in-the-loop review, appeals handling, and external governance for models that affect credit or access. This is not something an AI coding agent should “auto-decide.”

### Current Position
Fairness testing and approval are mandatory, but the precise approval workflow, review board cadence, external validator role, and deployment gate criteria still require human governance definition.

### Required Resolution
Define:
- who approves a credit model for deployment
- which fairness thresholds are binding
- what evidence is required per release
- how appeals and override workflows are recorded

### Consequences / Follow-up
- Production credit decisions should not bypass human-reviewed governance.
- `ML_MODEL_REGISTRY.md` should be updated once this is finalized.

---

## ADR-0015: Final Tooling Choice for Monorepo Orchestration (Nx vs. Turborepo)
- Date: 2026-03-19
- Status: **Open**
- Owners: Platform Lead, Frontend Lead
- Scope: build tooling, CI/CD, workspace management

### Context
The implementation guide allows either Nx or Turborepo for the monorepo baseline but does not make a binding final selection.

### Current Position
Both are acceptable in principle. The repo should not drift into mixed orchestration tooling.

### Required Resolution
Choose one after evaluating:
- multi-language ergonomics
- CI caching behavior
- developer experience with mobile/web/backend mix
- code generation and task-graph needs

### Consequences / Follow-up
- Once selected, add a new accepted ADR and close this one.
- Scaffold scripts, CI jobs, and contributor docs against only one orchestrator.

---

## ADR-0016: Managed MSK vs. Self-Managed Kafka on EKS for Initial Deployment
- Date: 2026-03-19
- Status: **Open**
- Owners: Platform Lead, Finance Lead
- Scope: streaming infrastructure, cost, ops

### Context
The infrastructure baseline permits either AWS MSK or self-managed Kafka on EKS. A final production choice is not explicitly locked in the uploaded specs.

### Current Position
Local development may use Redpanda or equivalent, but production/staging requires a single authoritative Kafka path.

### Required Resolution
Choose based on:
- operational burden
- reliability/SLA needs
- cost profile at Phase 1 and Phase 2 scale
- observability and security integration

### Consequences / Follow-up
- Infra modules, runbooks, and scaling plans depend on this choice.
- Close before production-grade event pipeline work begins.

---

# Rejected Decisions Register

## REJ-0001: Single-Instance Kong in Staging or Production
- Date: 2026-03-19
- Status: **Rejected**
- Reason
The requirements and implementation guide explicitly prohibit this topology outside local development.

---

## REJ-0002: Pinecone as Default Production Vector Store Before DPIA Outcome
- Date: 2026-03-19
- Status: **Rejected**
- Reason
This conflicts with the locked default to pgvector and the time-bound DPIA decision rule.

---

## REJ-0003: Hardcoded Tax or Compliance Rates in Application Logic
- Date: 2026-03-19
- Status: **Rejected**
- Reason
Rates must live in configuration tables and be updateable without deployment.

---

## REJ-0004: CRUD-Style Mutable Financial Ledger as Source of Truth
- Date: 2026-03-19
- Status: **Rejected**
- Reason
This conflicts with append-only financial integrity and auditability requirements.

---

## REJ-0005: Direct In-Request Calls to Rate-Limited Upstream Providers as the Standard Pattern
- Date: 2026-03-19
- Status: **Rejected**
- Reason
The v1.2 architecture requires outbound queueing via Asynq for rate-limited providers.

---

# Review Triggers

Update this file immediately when any of the following occurs:

- DPIA outcome changes vector-store eligibility
- a new regulator or partner imposes a structural architecture constraint
- a model version changes in production
- a new service is added or an existing service changes language/runtime
- an integration changes auth model, callback model, or retry pattern materially
- a security control shifts responsibility between gateway and services
- offline conflict policy changes for any data class
- a phase-gate review introduces a binding architectural condition
- a fairness or ethics governance rule is formally approved

---

# Session Update Rule

At the end of any engineering or architecture session that changes a binding decision:

1. Add or update the ADR entry.
2. Cross-check impacted files (`ARCHITECTURE.md`, `DATA_MODEL.md`, `API_CONTRACT.md`, `SECURITY_BASELINE.md`, `INTEGRATION_MANIFEST.md`, `ML_MODEL_REGISTRY.md`, `OBSERVABILITY_SLO.md`).
3. Record the session summary in `SESSION_LOG.md`.
4. Update `CLAUDE.md` only if the decision must remain in active agent context for the current sprint.

---

# Source Alignment Note

This document reflects the uploaded BizPulse requirements, technical specification, and unified implementation guide as of March 2026, including the locked decisions for pgvector-by-default, append-only financial records, config-table tax rates, pinned Claude versions, Kong HA, gateway JWT validation, per-data-type offline conflict handling, Avro event schemas, Africa’s Talking fallback, Asynq outbound queueing, and AWS `af-south-1` primary residency.
