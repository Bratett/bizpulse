# CLAUDE.md — BizPulse AI Agent Operating Context

## Purpose
This file is the persistent operating context for Claude Code when working inside the BizPulse AI monorepo. It is not product documentation. It is a high-signal execution guide that keeps implementation aligned with the authoritative specifications.

## Source of Truth Hierarchy
When requirements conflict, resolve in this order:
1. `BizPulse_AI_Unified_Implementation_Specification_v1.2.md`
2. `BizPulse_AI_Technical_Specification_v1_2.md`
3. `BizPulse_AI_Requirements_Breakdown.md`
4. ADRs in `docs/DECISIONS.md`
5. Current sprint context

Do not invent alternate architecture unless explicitly approved through an ADR.

## System Identity
BizPulse AI is a compliance-heavy, offline-first, multilingual AI platform for Ghanaian SMEs. It is not a simple CRUD SaaS app. It spans:
- backend microservices
- mobile app
- web PWA
- USSD gateway
- WhatsApp channel
- financial data processing
- analytics and forecasting
- compliance automation
- multilingual NLP

## Locked Architecture Decisions
These are non-negotiable unless superseded by a formal ADR.

1. **Architecture style:** microservices.
2. **Backend language split:**
   - Go: `user-svc`, `transaction-svc`, `notification-svc`
   - Python: `analytics-svc`, `compliance-svc`, `nlp-svc`
3. **Gateway:** Kong. Production topology is HA from the beginning; do not design a single-instance production gateway.
4. **Identity:** Keycloak is the IdP. Kong validates JWTs at the gateway. Downstream services trust gateway-verified claims.
5. **Transactions:** append-only / event-sourced financial records. Never implement mutable ledger updates or delete flows for financial transactions.
6. **Vector store:** `pgvector` is the default and current implementation target. Do not scaffold Pinecone production integration unless a later ADR explicitly authorizes it after DPIA clearance.
7. **Tax rates:** all VAT, NHIL/GETFund, CIT, PAYE, WHT, and related compliance rates must be data-driven from configuration tables. Never hardcode rates.
8. **Kafka schema format:** Avro. Schemas live in `/shared/avro` and must exist before producer/consumer generation.
9. **Offline-first:** mandatory. Mobile uses SQLite with encrypted WAL and queue-based delta sync with idempotency.
10. **USSD/SMS fallback:** Africa's Talking is the designated fallback provider. Health-check-triggered failover from direct telco routes is required.
11. **Outbound provider calls:** rate-limited upstream calls must use Asynq with backoff, retry, concurrency control, deduplication, and DLQ behavior.
12. **Primary infrastructure region:** AWS `af-south-1`; DR posture includes `eu-west-1`.
13. **Client channels:** React Native (Expo), Next.js PWA, USSD gateway, WhatsApp Business API.
14. **Model versions:** keep pinned model identifiers as specified unless formally upgraded.
15. **Build order principle:** build deep before wide.

## Delivery Channels and Tech Stack
### Clients
- `mobile/` → React Native with Expo
- `web/` → Next.js with TypeScript and PWA support
- `ussd/` or equivalent gateway component → telco APIs + Africa's Talking fallback
- WhatsApp via Notification Service integration

### Core Services
- `services/user-svc` → registration, tenancy, RBAC, consent, subscriptions
- `services/transaction-svc` → ingestion, append-only ledger, sync, idempotency, event emission
- `services/analytics-svc` → financial statements, forecasting, analytics
- `services/compliance-svc` → tax, GRA, SSNIT, compliance workflows
- `services/nlp-svc` → LLM routing, multilingual NLP, RAG, advisory safeguards
- `services/notification-svc` → push, SMS, WhatsApp, delivery workflows

### Data Layer
- PostgreSQL 16 as operational system of record
- TimescaleDB for business time-series / metric tables
- `pgvector` for embeddings / RAG
- Redis 7 for cache, idempotency support, queues
- InfluxDB 2.x for infrastructure / operational telemetry where specified
- S3 / Parquet for data lake and long-term exports

### Streaming / Processing
- Kafka-compatible event backbone
- Avro contracts
- Flink stream processing for enrichment, validation, deduplication, and metrics pipelines

## Repository Expectations
Expected monorepo shape:
- `services/`
- `mobile/`
- `web/`
- `ml/`
- `infra/`
- `integrations/`
- `shared/avro/`
- `shared/sdk/`
- `docs/`
- `CLAUDE.md`
- `docs/SESSION_LOG.md`
- `docs/DECISIONS.md`

Prefer changing existing files over creating duplicate alternatives. Keep naming consistent and predictable.

## Required Working Style
### 1) Spec-first, tests-first
For non-trivial work, follow this sequence:
1. design note
2. tests
3. implementation
4. integration verification
5. documentation update

Do not jump straight into broad implementation if interfaces or invariants are still ambiguous.

### 2) Narrow task slices
Implement one endpoint, one workflow slice, one consumer, one migration set, or one screen at a time. Avoid broad unreviewable code generation.

### 3) Layered service implementation
Preferred order inside a service:
1. schema / contracts
2. repository layer
3. pure business logic
4. orchestration layer
5. handler / API layer
6. integration tests

### 4) Human-owned blockers must be called out
Explicitly mark legal, regulatory, credential, sandbox-access, vendor-contract, and live-infrastructure dependencies as human-owned blockers.

## Mandatory Engineering Invariants
1. Monetary values are stored in **minor units (pesewas)** as integers / BIGINT.
2. Use UTC timestamps and explicit timezone-safe handling.
3. Preserve idempotency for any replayable ingestion or sync path.
4. Every financial or compliance-sensitive action must be auditable.
5. PII must be encrypted or masked according to the security baseline.
6. Do not log raw secrets, tokens, or unmasked sensitive fields.
7. No hardcoded tax or regulatory rates.
8. No direct synchronous outbound provider calls where Asynq is mandated.
9. Database truth overrides LLM-generated numeric claims.
10. For offline sync, apply the per-data-type conflict policy rather than generic last-write-wins.

## Offline Sync Conflict Rules
Use these baseline policies unless a more specific spec section overrides them:
- financial transactions → append-only, no destructive merge
- settings/profile preferences → last-write-wins where explicitly allowed
- inventory counts → manual resolution flow
- tax/compliance input data → merge with audit trail
- documents → version history

## NLP and Advisory Guardrails
1. RAG must target `pgvector`.
2. Use pinned model variants per spec.
3. Separate narrative generation from numeric truth. Numbers should come from verified application data.
4. Add compliance disclaimers where the product spec requires them.
5. Treat multilingual and code-switching support as a feature with testable accuracy expectations, not just prompt text.

## Outbound Queue Policy
All outbound calls to rate-limited third-party providers must be designed around Asynq.
Minimum behavior:
- provider-specific queues / priorities
- retry with backoff and jitter
- idempotency / deduplication
- DLQ after retry exhaustion
- alerting / observability hooks
- no silent drop of failed compliance-critical work

## Security and Compliance Posture
Always preserve requirements tied to:
- Ghana Data Protection Act 843
- GRA workflows and submission integrity
- SSNIT obligations
- NCA / USSD operational constraints
- auditability and traceability
- tenant isolation / RBAC
- certificate lifecycle controls

If a task touches security, compliance, tax, filing, or personal data, include a short self-check covering:
- rate source correctness
- audit log coverage
- encryption/masking
- retry / DLQ behavior where applicable
- tenant boundary integrity

## Documentation Discipline
Keep these files current when affected:
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/API_CONTRACT.md`
- `docs/OFFLINE_SYNC_SPEC.md`
- `docs/SECURITY_BASELINE.md`
- `docs/COMPLIANCE_MATRIX.md`
- `docs/DECISIONS.md`
- `docs/SESSION_LOG.md`

When you make an architectural choice, add or update an ADR entry in `docs/DECISIONS.md`.
When a session ends, summarize completed work, open risks, and next steps in `docs/SESSION_LOG.md`.

## Output Contract for Claude Code Sessions
Unless instructed otherwise, structure substantive responses with:
1. objective
2. assumptions
3. plan
4. files to create/update
5. implementation
6. tests
7. risks / blockers
8. next recommended step

## Design System
Always read DESIGN.md before making any visual or UI decisions.
All font choices, colors, spacing, and aesthetic direction are defined there.
Do not deviate without explicit user approval.
In QA mode, flag any code that doesn't match DESIGN.md.

## Current Sprint Context
Replace this section at the start of each sprint. Do not append indefinitely.

- Current phase: `TBD`
- Current sprint: `TBD`
- Primary goal: `TBD`
- In-scope requirements IDs: `TBD`
- Active blockers: `TBD`
- Files currently in focus: `TBD`

## gstack
Use the `/browse` skill from gstack for all web browsing. Never use `mcp__Claude_in_Chrome__*` tools directly.

Available gstack skills:
- `/office-hours` — YC-style brainstorming and idea validation
- `/plan-ceo-review` — CEO/founder-mode plan review
- `/plan-eng-review` — Engineering manager plan review
- `/plan-design-review` — Designer's eye plan review
- `/design-consultation` — Design system creation
- `/review` — Pre-landing PR review
- `/ship` — Ship workflow (test, review, PR)
- `/land-and-deploy` — Merge, deploy, verify
- `/canary` — Post-deploy canary monitoring
- `/benchmark` — Performance regression detection
- `/browse` — Headless browser for QA and testing
- `/qa` — QA test and fix bugs
- `/qa-only` — QA report only (no fixes)
- `/design-review` — Visual QA and polish
- `/setup-browser-cookies` — Import cookies for authenticated testing
- `/setup-deploy` — Configure deployment settings
- `/retro` — Weekly engineering retrospective
- `/investigate` — Systematic debugging
- `/document-release` — Post-ship documentation update
- `/codex` — OpenAI Codex second opinion
- `/cso` — Chief Security Officer audit
- `/autoplan` — Auto-review pipeline
- `/careful` — Safety guardrails for destructive commands
- `/freeze` — Restrict edits to a directory
- `/guard` — Full safety mode (careful + freeze)
- `/unfreeze` — Clear freeze boundary
- `/gstack-upgrade` — Upgrade gstack to latest

## Context Budget Rule
Keep this file lean. Remove instructions once they are fully enforced by tooling or CI. This file should stay focused on constraints the agent is likely to violate without persistent reminders.
