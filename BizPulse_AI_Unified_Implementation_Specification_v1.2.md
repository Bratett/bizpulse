# BizPulse AI — Unified Implementation Specification
## Enterprise-Grade AI Agent Execution Guide

**Document Type:** Consolidated Implementation Specification & AI Agent Execution Playbook
**Source Documents:** BizPulse AI Claude Code Strategic Roadmap + BizPulse AI Strategic Implementation Roadmap
**Based On:** BizPulse AI Technical Specification v1.2 & Requirements Breakdown (March 2026)
**Classification:** Internal — Engineering Leadership
**Status:** Living Reference — Update at Each Phase Gate
**Prepared For:** AI Agent (Claude Code) + Senior Systems Architect / Lead Developer

---

> **Version 1.2 Alignment Note:** This document has been updated to align with Technical Specification v1.2 (March 2026). Four architectural additions are incorporated from the independent board-level review: (1) USSD/SMS aggregator fallback via Africa's Talking with automated health-check failover (§1.4, §2.2, Sprint 6, §7.1.6); (2) DPIA hard-commit schedule with binding Phase 1 drop-dead date for the Pinecone/pgvector decision (§1.3, §2.1.2, §7.1.8); (3) OTA app update policy via Expo EAS Update for Phase 2 beta distribution (§4.1, Sprint 6); (4) Outbound API rate limit management via Asynq worker queue (§1.3, §5.2.3, §7.1.7). Gate checklists, CLAUDE.md, and Appendix B prompt templates updated accordingly. All v1.2 additions are marked with a `[v1.2]` tag.

---

## Table of Contents

1. [Executive Assessment](#1-executive-assessment)
2. [Pre-Development Preparation](#2-pre-development-preparation)
3. [Project Initialization](#3-project-initialization)
4. [Sprint-by-Sprint Implementation Plan](#4-sprint-by-sprint-implementation-plan)
5. [Testing Architecture & Protocols](#5-testing-architecture--protocols)
6. [Cross-Cutting Concerns](#6-cross-cutting-concerns)
7. [Professional Recommendations & Risk Mitigation](#7-professional-recommendations--risk-mitigation)
8. [Phase Gate Readiness Checklists](#8-phase-gate-readiness-checklists)
9. [Appendix A: CLAUDE.md — AI Agent System Context](#appendix-a-claudemd--ai-agent-system-context)
10. [Appendix B: Prompt Templates for Recurring Tasks](#appendix-b-prompt-templates-for-recurring-tasks)
11. [Appendix C: Session Management Templates](#appendix-c-session-management-templates)
12. [Appendix D: Key Requirement-to-Sprint Mapping](#appendix-d-key-requirement-to-sprint-mapping)

---

## 1. Executive Assessment

### 1.1 System Complexity Profile

BizPulse AI is not a typical SaaS product. It is a multi-domain, compliance-heavy, offline-first, multilingual AI platform targeting infrastructure-constrained Ghanaian SMEs. The system comprises:

- **Six backend microservices:** User Service, Transaction Engine, Analytics Service, Compliance Service, NLP Service, Notification Service
- **Four client delivery channels:** React Native mobile (Expo), Next.js PWA, USSD gateway, WhatsApp Business API
- **Multi-database data layer:** PostgreSQL 16 + TimescaleDB + pgvector, InfluxDB 2.x, Redis 7
- **Streaming data pipeline:** Apache Kafka + Apache Flink
- **ML/AI inference stack:** LangChain, Whisper, MLflow, BentoML, Anthropic Claude API (claude-sonnet-4-6 and claude-haiku-4-5-20251001 — pinned)
- **Infrastructure:** AWS af-south-1 (primary), eu-west-1 (DR), Terraform, ArgoCD, Kong HA, CloudFlare
- **Regulatory surface:** GRA, DPC, BoG, NCA, SSNIT (six agencies simultaneously)
- **Multilingual NLP:** English, Twi, Ga, Ewe, Hausa, Dagbani, including code-switching detection

This is a 48-month, ~$12.5M USD programme spanning five phases with formal phase gates. No AI agent will build this end-to-end in a single session. This specification is designed for disciplined, incremental AI-assisted engineering — sprint by sprint, slice by slice.

### 1.2 AI Agent Capability Boundaries

**The AI agent (Claude Code) excels at:**
- Scaffolding microservice boilerplate from well-defined specifications
- Generating database schemas, migration scripts, and seed data from requirements tables
- Writing API endpoint implementations when given OpenAPI specifications or clear interface contracts
- Producing Terraform modules, Kubernetes manifests, Helm charts, and ArgoCD configurations
- Generating comprehensive test suites (unit, integration, contract) when given acceptance criteria
- Implementing data pipeline logic (Kafka consumers, Flink jobs) from documented processing rules
- Building React Native screens, Next.js pages, and component libraries from design specifications
- Refactoring, debugging, and optimising code when provided with failing tests or performance profiles
- Drafting compliance-checking logic from regulatory rule tables
- Producing technical design documents before code generation
- Acting as a code reviewer for security, compliance, and performance issues

**The AI agent requires significant human guidance for:**
- Architectural trade-off decisions (e.g., the Pinecone vs. pgvector DPIA outcome)
- Third-party API integration where live sandbox credentials and partner documentation are needed
- ML model training, evaluation, and hyperparameter tuning on proprietary datasets
- Ghanaian regulatory interpretation (GRA XML schemas, SSNIT file formats, NCA licensing)
- Security architecture validation — penetration testing, SIEM configuration, WAF rule tuning
- Performance tuning under real production load profiles
- Cultural and linguistic validation of Twi/Ga/Ewe/Hausa/Dagbani NLP outputs
- Go/No-Go decisions at each Phase Gate
- ML model fairness evaluation for credit scoring across demographic segments

### 1.3 Foundational Architectural Decisions (Lock Before Day 1)

The following decisions must be made and recorded in Architecture Decision Records (ADRs) before any code generation begins. These are not decisions for the AI agent to make — they must be provided to it as constraints.

| Decision | Resolution | Rationale |
|----------|-----------|-----------|
| Vector database | **pgvector** (default) | Pinecone is blocked until DPIA confirms adequacy for cross-border transfer under Act 843. Build all RAG pipelines against pgvector. Treat any future Pinecone migration as a separate release. |
| Transaction architecture | **Event sourcing / append-only** | The spec mandates append-only financial records with idempotency enforcement. Do not build CRUD-style and retrofit immutability. |
| Tax rate storage | **Config table only** | NFR-MAI-001 requires tax rate changes without code deployment. All VAT, CST, CIT, PAYE, and WHT rates must reside in a `compliance_rates` table. Any hardcoded rate literal is a PR rejection. |
| Claude model versions | **Pinned** | `claude-sonnet-4-6` (complex NLP) and `claude-haiku-4-5-20251001` (simple queries) are pinned constants. Every upgrade is a formal release decision. |
| Kong HA topology | **3-instance minimum from Sprint 1** | Single-instance Kong is explicitly prohibited. Retrofitting HA topology on a live API gateway is a production risk event. |
| Auth token validation | **Kong validates JWTs at gateway** | Keycloak is the IdP. Kong handles token validation at the gateway boundary. Individual services trust verified claims from Kong headers. |
| Offline sync conflict strategy | **Per-data-type matrix** | Financial transactions: append-only. Settings: Last-Write-Wins. Inventory counts: manual resolution prompt. Tax inputs: merge with audit log. Documents: version history. See §2.1 OFFLINE_SYNC_SPEC.md. |
| Backend language assignment | **Go:** User, Transaction, Notification services. **Python:** Analytics, Compliance, NLP services. | Confirm or amend before any service scaffolding. |
| Kafka schema format | **Avro** | Avro IDL in `/shared/avro/`. All topics must have registered schemas before any producer/consumer code is generated. |

> **[v1.2] Two additional decisions locked at this stage:**

| Decision | Resolution | Rationale |
|----------|-----------|-----------|
| USSD/SMS fallback provider | **Africa's Talking** | Hubtel is a direct BizPulse competitor (§7.1); using Hubtel infrastructure creates a commercial conflict of interest. Africa's Talking is the designated aggregator fallback, activated automatically by a health-check sidecar on 3 consecutive primary gateway failures within 60 seconds. See §1.4. |
| Outbound API queue | **Asynq (Go-native, Redis-backed)** | All outbound calls to rate-limited upstream providers (GRA, MTN MoMo, Vodafone Cash, bank feeds, Anthropic Claude API) must be routed through Asynq. Chosen over Celery/Sidekiq because it matches the Go services stack and uses Redis already provisioned in the data layer — no new runtime dependency. See §5.2.3. |

---

## 1.4 USSD/SMS Redundancy Architecture [v1.2]

> **v1.2 Addition — Technical Specification §1.2.2 (Architecture Recommendation #6):** USSD is BizPulse's primary channel for low-connectivity and low-literacy users — precisely those who cannot fall back to the mobile app or PWA. A telco API outage has a disproportionate user impact. Automated failover to Africa's Talking is required from Sprint 6 onwards.

| Routing Tier | Provider | Role | Trigger |
|---|---|---|---|
| Primary | Custom Gateway → Direct Telco APIs (MTN, Vodafone, AirtelTigo) | All USSD sessions and SMS notifications | Default |
| Fallback | **Africa's Talking** (pan-African aggregator) | USSD session re-routing and SMS delivery | Activated automatically when primary gateway returns 3 consecutive errors within 60 seconds, or when a telco API health check fails |

**Implementation notes:**
- Africa's Talking is preferred over Hubtel for this fallback role as Hubtel is a direct BizPulse competitor (§7.1); using Hubtel's infrastructure creates a commercial conflict of interest.
- The fallback trigger is managed by a health-check sidecar process on the Custom Gateway, which monitors telco API response codes and switches routing automatically — no manual intervention required.
- NCA licensing covers USSD number range assignment; the aggregator fallback does not require a separate NCA license as the USSD short code remains BizPulse's.
- SMS delivery status callbacks are normalised across both providers to a common internal schema, ensuring notification service logic is provider-agnostic.
- Africa's Talking API credentials must be added to `docs/INTEGRATION_MANIFEST.md` alongside MTN MoMo and Vodafone Cash during pre-development preparation.
- Sprint 6 AI agent task: generate the health-check sidecar and Africa's Talking client alongside the primary USSD gateway prototype — not as a post-launch enhancement.

---

## 2. Pre-Development Preparation

> **Principle:** Every hour invested in pre-development artefacts multiplies into days of saved iteration. Skipping this phase is the most common failure mode in AI-assisted development — the agent produces technically correct code that doesn't align with the actual system.

### 2.1 Required Documentation Artefacts

The following artefacts must exist in version control before the first AI agent session. The agent reads these as context; it cannot reason correctly about BizPulse without them.

| Artefact | File Path | Purpose | Source |
|----------|-----------|---------|--------|
| Architecture overview | `docs/ARCHITECTURE.md` | Canonical system component diagram: API Gateway → Microservices → Data Layer → External Integrations | Spec §1.2.2 |
| Data model | `docs/DATA_MODEL.md` | Full ER definitions: transactions, users, businesses, compliance records, ML model outputs | Must be authored |
| API contracts | `docs/API_CONTRACT.md` | OpenAPI 3.0 YAML for every internal service boundary | Must be authored |
| Compliance matrix | `docs/COMPLIANCE_MATRIX.md` | Maps every regulatory requirement (Act 843, GRA, SSNIT, BoG) to the specific service and function responsible | Spec §2 |
| Integration manifest | `docs/INTEGRATION_MANIFEST.md` | All third-party APIs: MTN MoMo, Vodafone Cash, GhIPSS, GRA, SSNIT, **Africa's Talking** (USSD/SMS fallback [v1.2]) — sandbox credentials, rate limits, error codes | Must be gathered from vendors |
| Offline sync spec | `docs/OFFLINE_SYNC_SPEC.md` | Conflict resolution rules per data type translated into concrete state machine diagrams | Spec §1.3 |
| ML model registry | `docs/ML_MODEL_REGISTRY.md` | Architecture decisions per model: LSTM/Prophet for cash flow, credit scoring feature schema, bias testing criteria | Must be authored |
| Security baseline | `docs/SECURITY_BASELINE.md` | AES-256 at-rest and in-transit requirements, RBAC matrices, idempotency key schemes, TLS lifecycle rules | Spec §2.1.1 |
| ADR log | `docs/DECISIONS.md` | Every significant architectural decision: what was decided, why, alternatives rejected | Maintained every session |
| Session log | `docs/SESSION_LOG.md` | End-of-session summaries from the AI agent | Maintained every session |

#### 2.1.1 Interface Contracts (Required Before Each Service Sprint)

**API Contracts (OpenAPI 3.0 YAML):** Write or generate an OpenAPI specification for every service-to-service and service-to-client API. Include request/response schemas, error codes, and authentication requirements. The AI agent generates server stubs and client SDKs directly from these specs.

**Event Contracts (Avro IDL):** Define every Kafka topic's message schema. Include the idempotency key field (FR-SYN-002), ISO 8601 timestamps, and all enrichment fields from the Flink pipeline: merchant category, currency conversion fields (FR-ING-003, FR-ING-004).

**Database Schema (SQL DDL):** Draft the initial schema covering at minimum: users, businesses, transactions, compliance_filings, consent_records, tax_rate_config, subscription_tiers. Include TimescaleDB hypertable definitions for business metrics tables. The AI agent refines and extends from this foundation.

#### 2.1.2 Regulatory Reference Files

Assemble the following as documents that can be provided to the AI agent as context when working on compliance-related services:

- GRA VAT return XML schema (obtain during Week 1 registration)
- SSNIT payroll file format specification
- GhIPSS ISO 20022 message format documentation
- Ghana Data Protection Act 843 full text
- IFRS for SMEs standard (relevant sections on financial statement presentation)
- ICAG report format templates
- Current GRA tax rate tables: VAT 12.5%, NHIL/GETFund 2.5%, CIT 25%, PAYE progressive brackets, WHT matrix 3–15%

#### 2.1.2 DPIA Hard-Commit Schedule [v1.2]

> **v1.2 Addition — Technical Specification §2.1.2 (Architecture Recommendation #7):** The DPIA process must be time-bounded to prevent indefinite use of Pinecone as a de facto standard while compliance status remains unresolved. Without a hard deadline, the engineering team risks building deeper Pinecone dependencies that make a later migration to pgvector progressively more costly and disruptive.

The default vector store is **pgvector** (consolidated within the existing PostgreSQL ecosystem). Pinecone may only be adopted in production if the DPIA confirms adequacy for cross-border transfer under Act 843. The following schedule is **binding — not advisory.**

| Milestone | Date | Owner | Consequence of Miss |
|---|---|---|---|
| DPIA initiated | Week 1 (Phase 1 start) | DPO + Compliance Officer | Escalate to CTO; block Phase 1 Gate if not started by Week 4 |
| DPIA findings delivered | End of Month 3 | DPO | Trigger automatic pgvector commitment if findings are inconclusive |
| **Drop-dead decision date** | **End of Phase 1 (Month 6)** | **CTO + DPO** | **If Pinecone adequacy is not confirmed by this date, pgvector becomes the committed production vector store. All Pinecone integration work is frozen. No exceptions without board-level sign-off.** |
| pgvector production-ready (if triggered) | End of Phase 2 (Month 12) | Technical Lead | Phase 2 Gate criterion: vector store must be production-stable |

> **AI agent constraint:** The AI agent must never scaffold Pinecone production integration. All RAG pipeline code is written against pgvector. If the DPIA outcome changes this, it is a formal release decision with a separate ADR entry in `docs/DECISIONS.md`.

#### 2.1.3 Design System & UI/UX Artefacts

For frontend code generation, the AI agent requires:
- Figma or equivalent design system with component specifications for mobile and PWA
- Screen flow document covering the 12 operational workflows (§12.1–§12.8)
- USSD menu tree specification (FR-USSD-003: resolution within 5 screens)
- Voice interaction flow diagrams for the NLP assistant (confirmation-based for low-literacy users per FR-NLP-010)
- Colour palette, typography, and accessibility standards for target devices: Tecno, Itel, Infinix mid-range Android (FR-MOB-002)

### 2.2 Long-Lead Regulatory Dependencies — Initiate on Day 1

These are not development tasks. They are administrative and legal procurement actions that run in parallel with development from Week 1. The AI agent cannot unblock them. Assign a dedicated non-engineering resource to own every track.

| Action | Lead Time | Risk if Delayed |
|--------|-----------|-----------------|
| GRA API access + Certified Tax Software registration | 3–6 months | VAT filing blocked at Gate 1 — on critical path |
| MTN MoMo + Vodafone Cash API commercial agreements | 2–4 months | Core transaction sync blocked; product non-viable |
| Data Protection Commission (DPC) registration | 4–8 weeks | Operating without registration is a regulatory violation |
| Bank of Ghana licensing consultation | 3–6 months | Financial services feature scope undefined |
| SSNIT API access | 2–4 months | Payroll compliance unavailable at Gate 2 |
| NCA USSD licensing | 2–3 months | USSD channel absent at launch |
| **Africa's Talking aggregator account + API credentials [v1.2]** | **2–4 weeks** | **USSD/SMS fallback unavailable; direct telco outage has no automated recovery path** |

**Escalation rule:** If the MTN MoMo commercial agreement has not reached final negotiation by Month 3, this is a CEO-level escalation, not a partnerships team issue.

### 2.3 Development Environment Configuration

#### 2.3.1 Local Development Toolchain

| Component | Tool & Version | Configuration Notes |
|-----------|---------------|---------------------|
| Monorepo | Turborepo or Nx | See §2.3.2 for directory structure |
| Go services | Go 1.22+ | Uber Go style guide; shared internal packages for auth middleware, error handling, logging |
| Python services | Python 3.12+ with Poetry | Virtual environments per service; shared utilities on internal PyPI |
| Mobile | React Native (Expo SDK 52+) | Managed workflow; verify Expo compatibility with SQLite WAL encryption |
| Web | Next.js 15+ with TypeScript | PWA config with Workbox; service worker for offline caching |
| Databases (local) | Docker Compose | PostgreSQL 16 + TimescaleDB + pgvector, Redis 7, InfluxDB 2.x, Redpanda (lighter Kafka-compatible for local dev) |
| API Gateway (local) | Kong (Docker) | Single-instance for local dev; HA cluster required in staging/production |
| ML tracking | MLflow (local server) | Experiment tracking before cloud deployment |

#### 2.3.2 Monorepo Directory Structure

Establish this structure before the first AI agent session. The agent generates better-organised code when the structure is pre-established.

```
bizpulse-ai/
├── services/
│   ├── user-svc/                     # Go — Registration, auth, consent, subscriptions
│   │   ├── cmd/main.go
│   │   ├── internal/
│   │   └── api/
│   ├── transaction-svc/              # Go — Core financial transaction processing
│   │   ├── cmd/main.go
│   │   ├── internal/
│   │   └── api/
│   ├── analytics-svc/                # Python — Cash flow, demand prediction, credit scoring
│   │   ├── pyproject.toml (Poetry)
│   │   └── src/
│   ├── compliance-svc/               # Python — GRA, SSNIT, Act 843 compliance engine
│   │   ├── pyproject.toml (Poetry)
│   │   └── src/
│   ├── nlp-svc/                      # Python — Claude API integration, multilingual routing
│   │   ├── pyproject.toml (Poetry)
│   │   └── src/
│   ├── notification-svc/             # Go — Push, SMS, WhatsApp
│   │   ├── cmd/main.go
│   │   ├── internal/
│   │   └── api/
│   └── api-gateway-config/           # Kong declarative configuration
├── mobile/                           # React Native (Expo) app
├── web/                              # Next.js PWA
├── ml/                               # Model training, MLflow experiments
│   ├── cash-flow-model/
│   ├── credit-scoring-model/
│   └── demand-prediction-model/
├── infra/
│   ├── terraform/
│   │   └── modules/                  # VPC, EKS, RDS, ElastiCache, MSK, S3, ECR, Route53, ACM
│   ├── kubernetes/
│   │   ├── base/
│   │   ├── overlays/staging/
│   │   └── overlays/production/
│   └── monitoring/
├── integrations/
│   ├── mtn-momo/
│   ├── vodafone-cash/
│   ├── gra-api/
│   └── ssnit/
├── compliance/                       # Regulatory documentation, audit configs
├── shared/
│   ├── avro/                         # Kafka Avro event schemas
│   ├── sdk/                          # Shared client SDKs
│   └── proto/                        # Protobuf definitions (if used)
├── docs/                             # All architecture artefacts from §2.1
├── CLAUDE.md                         # AI agent system context — see Appendix A
└── SESSION_LOG.md                    # End-of-session summaries
```

#### 2.3.3 CI/CD Pipeline

| Component | Tool | Configuration |
|-----------|------|---------------|
| Source control | GitHub | Branch protection: require ≥1 senior review; SAST scan on every PR |
| CI | GitHub Actions | Unit tests, integration tests, container builds, SAST (Semgrep or Snyk), dependency scanning |
| Container registry | AWS ECR (af-south-1) | Images tagged with git SHA and semantic version |
| CD | ArgoCD | GitOps to EKS; staging auto-deploy on merge to main; production requires manual approval |
| IaC | Terraform | Remote state in S3 with DynamoDB locking; modules per service |

#### 2.3.4 AWS Infrastructure Baseline

Provision the following via Terraform before development begins (the AI agent generates the modules; a human with AWS access applies them):

- VPC with public, private, and isolated subnets across 3 AZs (FR-SEC-010, FR-DR-006)
- EKS cluster with managed node groups
- RDS PostgreSQL 16 Multi-AZ with TimescaleDB and pgvector extensions
- ElastiCache Redis cluster
- MSK (Managed Streaming for Kafka) or self-managed Kafka on EKS
- S3 buckets: data lake (Parquet, 7-year retention per FR-DOC-003), document storage (PDF/A), Terraform state
- ECR repositories per service
- Route 53 hosted zone with health checks for DR failover (FR-DR-008)
- ACM certificates with auto-renewal (FR-CERT-001)
- CloudFlare WAF and DDoS protection (FR-SEC-011)

---

## 3. Project Initialization

### 3.1 The CLAUDE.md Context File

The `CLAUDE.md` file at the monorepo root is the AI agent's persistent context. It is the single most critical preparation step. The agent reads it on every invocation. Its full contents are defined in **Appendix A** and must be kept current. Update it at the start of every sprint.

**Token budget discipline:** `CLAUDE.md` competes directly with the code being reasoned about for space in the model's context window. Every token it consumes is a token unavailable for the actual implementation task. As BizPulse grows across five phases — new services, new integrations, new regulatory requirements — there will be pressure to keep adding to this file. Resist it.

Apply these rules as the project matures:
- **Remove, don't accumulate.** When a constraint is fully enforced by CI (e.g., a linter rule prevents hardcoded rates), remove it from `CLAUDE.md` — the toolchain now owns it.
- **Sprint context replaces, not appends.** The "Current Sprint Context" block should reflect *only* the current sprint. Prior sprint summaries belong in `docs/SESSION_LOG.md`, not here.
- **Maximum length guideline: 150 lines.** If `CLAUDE.md` exceeds this, audit it. Every line should be a constraint the agent would otherwise violate, not documentation it already knows.
- **Separate by audience.** If junior developers need onboarding context, put it in `docs/ONBOARDING.md`. `CLAUDE.md` is written for the AI, not for humans.

### 3.2 Three-Layer Context Model

The AI agent operates with a finite context window. Manage it deliberately across three layers.

**Layer 1 — Persistent Context (CLAUDE.md):** Always present. Technology stack, code standards, compliance constraints, file structure, and current sprint focus. Updated at the start of each sprint.

**Layer 2 — Sprint Context (provided at session start):** The specific requirements tables for the current sprint's feature area. For example, when working on the Transaction Engine, provide:
- FR-INT-001 through FR-INT-005 requirements table
- FR-ING-001 through FR-ING-006 requirements table
- Transaction Capture & Sync Workflow (§12.2)
- Kafka topic schema definitions
- Relevant ADRs (schema ownership, event format)

**Layer 3 — Task Context (provided per prompt):** The specific file, function, or test being worked on. One endpoint at a time for backend services. One screen at a time for frontend work.

**Context drift prevention:** Every 5–7 turns, re-anchor critical constraints: *"Confirm: we are still using pgvector, not Pinecone. VAT rates are still config-table-sourced only. Model strings remain pinned."*

### 3.3 Spec-First, Tests-First Workflow (Apply to Every Feature)

The recommended sequence for every feature is three phases — design, then tests, then code. Skipping either of the first two phases is the most common failure mode in AI-assisted development.

**Phase 0 — Technical Design Document**

Before generating any code or tests, instruct the AI agent to produce a design document:

```
Before writing any code, produce a technical design document for
[feature/module name] covering:
1. Input schema (what data it consumes and from where)
2. Output schema (exact fields and types)
3. Algorithm approach and justification
4. Edge cases and how each is handled
5. Error scenarios and fallback behaviour
6. Integration points with other services

Based on: [attach relevant spec sections and requirements IDs]
```

Review and correct the design document before proceeding. This is the highest-value step in the entire workflow — an uncorrected design error is cheapest here and most expensive in production.

**Phase 0.5 — Tests First (AI TDD)**

After the design document is approved, generate unit tests *before* generating functional code. The human reviews the test cases to verify they cover the domain edge cases — the AI will not catch what it does not know to look for.

```
Based on the approved design document for [feature/module name],
generate the unit test suite ONLY — do not write any functional code yet.

For each function, include test cases covering:
- Happy path (standard valid input)
- Boundary values (zero, negative, maximum)
- Domain-specific edge cases: [list from design doc — e.g., multi-currency
  transactions, zero-rated VAT items, credit note refunds, idempotency
  key collisions, 30-day offline sync recovery]
- Error paths (invalid input, external API failure, timeout)
- Compliance invariants: [e.g., rate sourced from config table, monetary
  values in pesewas, audit log entry generated]

Use [pytest with parametrize / table-driven Go tests].
All monetary values in pesewas (BIGINT). No mocks of business logic — only
mock I/O boundaries (database, external APIs).
```

**Human review gate:** Before accepting the test suite, verify that every domain edge case from the design document has at least one corresponding test. For financial calculation functions, this review is mandatory regardless of seniority. Add any missing cases before proceeding.

Once the test suite is approved, instruct the AI to generate the functional code to pass it:

```
The test suite for [feature/module name] has been reviewed and approved.
Now generate the functional implementation that passes all tests.
Do not modify the tests. If a test appears incorrect, flag it — do not work around it.
```

This sequence ensures the implementation is constrained by human-verified acceptance criteria rather than the AI's own assumptions about what the code should do.

### 3.4 Service Initialization Pattern

For every service, apply this two-phase pattern:

**Phase A — Interface Definition:** Generate API handler stubs and interface definitions from the OpenAPI specification or requirements table. Review and approve all interfaces before any implementation begins. This is especially critical for: Transaction Engine ↔ Analytics Service, NLP Service ↔ Transaction Engine, Compliance Service ↔ GRA API.

**Phase B — Layered Implementation:** Apply the tests-first pattern from §3.3 at each layer, validating before proceeding to the next:
```
Layer 0 → Unit tests (generated and human-reviewed BEFORE functional code)
Layer 1 → Data access functions only (repository pattern) — must pass Layer 0 tests
Layer 2 → Business logic (pure functions; no I/O dependencies)
Layer 3 → Service orchestration (coordinates repo + business logic)
Layer 4 → API endpoints (validates input, delegates to service layer)
Layer 5 → Integration tests (generated after all layers pass unit tests)
```

Never ask the AI agent to generate all layers in one prompt for complex features.

### 3.5 Initial Scaffolding Prompts (Sprint 0)

Execute these sequentially, reviewing output before proceeding.

**Prompt 1 — Monorepo Scaffold:**

```
Review the CLAUDE.md context. Scaffold the complete monorepo directory
structure for BizPulse AI. Create:

1. Go module initialization for: user-svc, transaction-svc, notification-svc.
   Each with /cmd/main.go, /internal/, /api/ directories and a Dockerfile.

2. Python project initialization for: analytics-svc, compliance-svc, nlp-svc.
   Each with pyproject.toml (Poetry), /src/ directory, Dockerfile.

3. React Native (Expo) initialization in /mobile.

4. Next.js initialization with TypeScript in /web.

5. Shared directories: /shared/avro/, /shared/sdk/, /shared/proto/.

6. Infrastructure directories: /infra/terraform/modules/,
   /infra/kubernetes/base/, /infra/kubernetes/overlays/staging/,
   /infra/kubernetes/overlays/production/.

7. Docker Compose for local development with: PostgreSQL 16
   (TimescaleDB + pgvector), Redis 7, InfluxDB 2.x,
   Redpanda (Kafka-compatible), Keycloak.

8. GitHub Actions CI workflow: lint, test, build, security scan
   for all services.

Do not generate business logic. Focus on project structure,
dependency management, and build tooling only.
```

**Prompt 2 — Database Foundation:**

```
Generate the PostgreSQL schema for BizPulse AI Phase 1.
Use the following requirements as source of truth:

[Paste FR-DAT-001 through FR-DAT-005]
[Paste FR-SEC-007 through FR-SEC-009 for RBAC and field-level encryption]
[Paste FR-BIZ-001 through FR-BIZ-006 for subscription tier schema]
[Paste FR-DPC-003 for consent tracking schema]

Requirements:
- All monetary values in minor units (pesewas) as BIGINT
- All timestamps as TIMESTAMPTZ UTC
- Field-level encryption for PII (use pgcrypto)
- TimescaleDB hypertables for: daily_revenue, daily_cashflow,
  user_activity_metrics — linked to transactions via foreign keys
- pgvector extension with a vector_embeddings table
- Row-level security policies per tenant (business_id)
- Migration files in golang-migrate format (up/down SQL files)

Generate: 001_initial_schema.up.sql and 001_initial_schema.down.sql
```

**Prompt 3 — Kafka Event Schemas:**

```
Generate Avro schema definitions for the following Kafka topics:

- raw.momo.transactions
- raw.vodafone.transactions
- raw.bank.statements
- raw.manual.entries
- processed.transactions.enriched

Each schema must include:
- idempotency_key (string, required) — FR-SYN-002
- event_timestamp (ISO 8601 string, required)
- source_provider (enum: MTN_MOMO, VODAFONE_CASH, BANK, MANUAL)
- Raw topics: provider-specific raw fields
- Processed topic: enriched fields including merchant_category,
  original_currency, converted_amount_ghs_pesewas,
  fraud_score, deduplication_status

Place all files in /shared/avro/
```

### 3.6 AI Tooling Orientation (Junior Developer Onboarding)

This specification is primarily addressed to senior engineers and the lead architect. When junior developers are onboarded to the methodology — typically from Phase 2 onward as the team scales — they need a brief orientation to the mechanics of working with the AI agent before they can apply this playbook effectively. This section covers only what differs from a standard development workflow.

**Which tool to use**

BizPulse AI engineering uses **Claude Code** (Anthropic's CLI agent) as the primary AI development tool. It has direct read/write access to the repository workspace, can run shell commands, and maintains state across a session. It is not a chat interface that requires pasting code back and forth.

| Tool | When to use |
|------|-------------|
| Claude Code (CLI) | All code generation, scaffolding, refactoring, and review tasks defined in this specification |
| Claude.ai (browser) | Architecture discussion, design document drafting, specification review — tasks where no workspace access is needed |
| GitHub Copilot (inline) | Autocomplete within the editor for boilerplate; not a substitute for Claude Code sessions |

**Essential Claude Code CLI patterns**

```bash
# Start a session with workspace context loaded
claude                        # Opens interactive session; CLAUDE.md auto-loaded

# Common in-session commands
/edit path/to/file.go         # Open a specific file for targeted editing
/add docs/COMPLIANCE_MATRIX.md  # Add a document to the current context
/clear                        # Reset context (use before switching to a new service)

# Ensure the agent has full workspace read access before starting
# Run from the monorepo root — not a subdirectory
```

**Before starting any session**
1. Navigate to the monorepo root — not a service subdirectory. The agent needs to see `CLAUDE.md` and the full directory structure.
2. Confirm `CLAUDE.md` reflects the current sprint (check the "Current Sprint Context" block).
3. Load the sprint-specific context documents using `/add` before issuing the first task prompt.
4. Use the Session Opening Template from Appendix C.1.

**The one rule that matters most for junior engineers:** Never issue a task that spans more than one endpoint, one function, or one screen in a single prompt. Wide prompts produce wide, unreviewed code. Narrow prompts produce reviewable code. If you are unsure how narrow to go, go narrower.

**Where to find more context**
- `docs/ONBOARDING.md` — project-specific setup, environment configuration, and team conventions
- `docs/SESSION_LOG.md` — history of what has been built and what decisions were made
- `docs/DECISIONS.md` — ADR log; read before making any architectural choice
- Appendix B of this document — prompt templates for every common task type

### Build Sequence Overview

Build deep before building wide. The ordering below is driven by the dependency graph and the Gate 1 criteria.

```
Phase 1 Sprint Sequence (Months 1–6 → Gate 1 Target)
│
├── Sprint 0 (Weeks 1–2):   Infrastructure & Scaffolding
├── Sprint 1 (Weeks 3–4):   Data Foundation (Database + User Service)
├── Sprint 2 (Weeks 5–8):   Transaction Engine + Event Pipeline
├── Sprint 3 (Weeks 9–12):  Analytics & Financial Reporting
├── Sprint 4 (Weeks 13–16): NLP Foundation (Claude Integration)
├── Sprint 5 (Weeks 17–20): Compliance Engine (GRA + Tax + SSNIT)
└── Sprint 6 (Weeks 21–24): Client Applications + Integration + Security Audit
```

### Service Dependency Map (Reference Before All Sessions)

```
Kong API Gateway
  ├── User Service (Go)
  │     ├── PostgreSQL (users, businesses, consent, subscriptions)
  │     ├── Keycloak (identity)
  │     └── Redis (sessions)
  ├── Transaction Engine (Go)
  │     ├── PostgreSQL (transactions, ledger)
  │     ├── TimescaleDB (business metrics hypertables)
  │     ├── Kafka (producer: processed.transactions.enriched)
  │     └── Redis (idempotency cache)
  ├── Analytics Service (Python)
  │     ├── PostgreSQL / TimescaleDB (read)
  │     ├── MLflow (model registry)
  │     ├── BentoML (model serving)
  │     └── S3 (data lake reads)
  ├── Compliance Service (Python)
  │     ├── PostgreSQL (compliance filings, tax config)
  │     ├── GRA API (external)
  │     ├── SSNIT API (external)
  │     └── S3 (document storage, PDF/A)
  ├── NLP Service (Python)
  │     ├── Anthropic Claude API (claude-sonnet-4-6 and claude-haiku-4-5-20251001)
  │     ├── Whisper (STT)
  │     ├── LangChain + pgvector (RAG)
  │     ├── Redis (response cache, TTL 5 min)
  │     └── PostgreSQL (read — fact-checking against transactional data)
  └── Notification Service (Go)
        ├── Kafka (consumer: processed.transactions.enriched, compliance.alerts)
        ├── WhatsApp Business API (external)
        ├── SMS gateway (external)
        └── Firebase Cloud Messaging (push)

Apache Flink (Stream Processing)
  ├── Kafka (consumer: raw.*.transactions)
  ├── Kafka (producer: processed.transactions.enriched)
  ├── PostgreSQL (write: operational records)
  ├── TimescaleDB (write: business metric time-series)
  └── S3 (write: data lake, Parquet)
```

---

### Sprint 0: Infrastructure & Scaffolding (Weeks 1–2)

**AI agent tasks:**
- Generate Terraform modules: VPC, EKS, RDS, ElastiCache, MSK, S3, ECR, Route 53, ACM
- Generate Kubernetes base manifests (namespaces, resource quotas, network policies)
- Generate ArgoCD application definitions per service
- Generate Docker Compose for local development
- Generate GitHub Actions CI workflow (lint, test, build, SAST, dependency scan)
- Generate the CLAUDE.md project context file (see Appendix A)
- Generate Kong declarative configuration:
  - DB-less mode for local dev
  - PostgreSQL-backed HA cluster for staging/production
  - Rate limiting plugins per subscription tier (FR-SEC-012)

**Human tasks:**
- Provision the AWS account and configure IAM roles
- Apply Terraform to create the infrastructure
- Verify EKS cluster connectivity
- Set up Keycloak instance; configure realms, client applications, and user federation
- Initiate all regulatory dependencies: GRA, MTN MoMo, DPC, BoG (Week 1 mandatory)

---

### Sprint 1: Data Foundation (Weeks 3–4)

**AI agent tasks:**
- Generate the initial PostgreSQL schema migration (Prompt 2 above)
- Generate Avro event schemas for all Kafka topics (Prompt 3 above)
- Implement User Service (Go):
  - Registration and authentication via Keycloak integration
  - Consent management (FR-DPC-003)
  - Business profile creation and management
- Generate RBAC middleware for Go services (FR-SEC-007)
- Generate field-level encryption utilities using pgcrypto (FR-SEC-009)
- Generate subscription tier enforcement logic (FR-BIZ-001–006)

**Human tasks:**
- Review and approve database schema — particularly: monetary column types, TimescaleDB hypertable design, RLS policy correctness
- Configure Keycloak realms, client applications, and user federation
- Verify field-level encryption meets Act 843 requirements with compliance officer

**Key requirements:** FR-DAT-001–005, FR-SEC-001–009, FR-DPC-001–003, FR-BIZ-001–006

---

### Sprint 2: Transaction Engine & Event Pipeline (Weeks 5–8)

**AI agent tasks:**
- Implement the Transaction Engine (Go):
  - CRUD operations (append-only; no update/delete for financial records)
  - Idempotency enforcement: Redis check → PostgreSQL write → 409 on duplicate (FR-SYN-002)
  - Kafka event publishing to processed.transactions.enriched
  - Atomic batch sync endpoint with full rollback on any failure (FR-SYN-004)
- Generate Kafka consumer for raw.momo.transactions topic
- Implement Apache Flink stream processing jobs:
  - Deduplication
  - Schema validation (dead-letter queue on failure)
  - Merchant categorisation
  - Currency conversion with GHS pesewas as canonical unit
  - Fraud scoring placeholder
  - TimescaleDB write for business metrics
  - S3 Parquet write for data lake
- Generate MTN MoMo API integration client:
  - OAuth 2.0 flow
  - Webhook handler
  - Hourly batch fallback
- **[v1.2]** Generate Asynq worker queue implementation (Go, Redis-backed):
  - Wrap all outbound calls to GRA, MTN MoMo, Vodafone Cash, and bank feeds in Asynq tasks
  - Per-provider concurrency limits; priority queues (GRA = critical, bank feeds = low)
  - Exponential backoff with ±20% jitter (delays: 5s → 30s → 5m → 30m)
  - Dead Letter Queue (DLQ) after 5 failures; PagerDuty alert on DLQ event; additional DPO alert for GRA DLQ events
  - DLQ metrics emitted to InfluxDB as custom Datadog metrics
- Generate test suites at all three levels (see §5)

**Human tasks:**
- Coordinate with MTN MoMo for sandbox credentials (commercial agreement in progress from Week 1)
- Validate Flink job behaviour with sample MoMo transaction data
- Review idempotency and conflict resolution logic against the spec

**Key requirements:** FR-INT-001–005, FR-ING-001–006, FR-SYN-001–005, FR-CON-001–005

---

### Sprint 3: Analytics & Financial Reporting (Weeks 9–12)

**AI agent tasks:**
- Implement the Analytics Service (Python):
  - Financial statement generation engine
  - IFRS-aligned chart of accounts (FR-FIN-001)
  - P&L Statement generator
  - Balance Sheet generator
  - Cash Flow Statement generator (direct and indirect methods)
  - Statement of Changes in Equity generator (FR-COM-003)
  - Multi-currency handling with live exchange rate integration (FR-FIN-002)
- Generate XBRL export (FR-FIN-008) and PDF/A report generation (FR-DOC-002)
- Implement the TimescaleDB query layer for business metric aggregation
- Scaffold the cash flow forecasting model using **Prophet** (Phase 1; not LSTM — see §7.2.5):
  - 30/60/90-day forecast horizons
  - Features: MoMo settlement lag (T+1 to T+3), seasonal dummies (Homowo, Easter, Christmas, agricultural cycles), transaction volume
  - Output: date, predicted_inflow, predicted_outflow, net_position, confidence_interval_lower, confidence_interval_upper
  - MLflow tracking: model version, training date, validation MAPE, directional accuracy, feature importances
  - Backtesting gate: ≥70% directional accuracy on held-out set
  - Bias check: cross-sector forecast accuracy comparison

**Human tasks:**
- Source and validate training data for the cash flow forecasting model
- Validate financial statement output against ICAG format templates with a qualified accountant
- Review XBRL output against IFRS Taxonomy

**Key requirements:** FR-FIN-001–010, FR-ANA-001–006, FR-DOC-001–003

---

### Sprint 4: NLP Foundation — Claude Integration (Weeks 13–16)

**AI agent tasks:**
- Implement the NLP Service (Python):
  - LangChain orchestrator and prompt template management
  - LLM Router: `claude-haiku-4-5-20251001` for simple queries (<500ms target), `claude-sonnet-4-6` for complex queries (3–5s acceptable)
  - Multilingual intent detection: English, Twi, Ga, Ewe (Phase 1 scope)
  - Code-switching detection for English-Twi/Ga mixing
  - Intent classification for 30+ core financial query types (FR-NLP-014)
- Implement RAG pipeline with pgvector:
  - Regulation documents corpus
  - Business documents
  - No Pinecone until DPIA clears
- Implement Redis response cache (5-minute TTL — Fallback 1)
- Implement Whisper STT integration for English
- Implement hallucination mitigation layer (FR-ADV-006):
  - Every numerical value in an LLM response must be cross-referenced against the transaction database
  - If LLM output disagrees with database value: database wins — always
  - Architecture: LLM generates narrative structure; data layer populates all numbers
- Implement compliance filter and financial disclaimer appending (FR-ADV-005)
- Generate PII detection and masking pipeline (§5.3.1)

**Human tasks:**
- Source and curate the Twi speech dataset for Whisper fine-tuning (Phase 2 prep)
- Engage native speakers for Twi business terminology glossary (FR-NLP-009: ≥200 terms)
- Curate the regulation document corpus for RAG indexing
- Validate intent classification accuracy on a Ghanaian English test set (target: ≥95% per FR-NLP-001)
- Design and test the low-literacy voice interaction flow (FR-NLP-010)
- **[v1.2]** Confirm DPIA progress with DPO — findings are due by end of Month 3 (one month prior to this sprint's close). If findings are inconclusive, pgvector commitment is automatic per §2.1.2; no further decision is required.

**Key requirements:** FR-NLP-001–014, FR-ADV-001–006

---

### Sprint 5: Compliance Engine (Weeks 17–20)

**AI agent tasks:**
- Implement the Compliance Service (Python):
  - Configuration-driven tax rate table system (FR-TAX-001, FR-COM-002) — zero hardcoded rates
  - VAT calculation engine: composite 12.5% VAT + 2.5% NHIL/GETFund from config table
  - GRA VAT return XML generation conforming to GRA schema
  - CIT engine at 25% with sector-specific rates (FR-TAX-004)
  - PAYE progressive rate calculation (FR-TAX-005)
  - WHT matrix 3–15% by transaction type (FR-TAX-008)
  - GRA submission pipeline: submit → retry with exponential backoff (max 3) → dead-letter Kafka queue on failure
  - Filing workflow per §12.4 (VAT Filing Workflow)
  - Regulatory alert system (FR-COM-009)
  - Audit trail logging with tamper-evident storage (FR-DPC-009)

**Human tasks:**
- Obtain and integrate the GRA API sandbox (dependency initiated Week 1; expect availability ~Week 17)
- Validate all tax calculations against current GRA Finance Act with compliance officer
- Execute mandatory pre-launch rate verification step (FR-TAX-002)
- Test GRA XML submission in sandbox
- Initiate SSNIT API integration (dependency should be active from ~Week 7)

**Key requirements:** FR-COM-001–009, FR-TAX-001–008, FR-DPC-007–009

---

### Sprint 6: Client Applications, Integration & Security Audit (Weeks 21–24)

**AI agent tasks:**

*Mobile (React Native / Expo):*
- Onboarding flow (§12.1), dashboard, transaction views, forecast charts, voice query interface, settings
- SQLite offline storage with encrypted WAL (FR-OFF-001, FR-OFF-002)
- Delta sync engine with checksum validation (FR-SYN-001, FR-SYN-003)
- Conflict resolution UI for inventory counts (FR-CON-003)
- TLS certificate pinning (FR-MOB-004, FR-CERT-004)

*Web PWA (Next.js):*
- Compliance dashboard and financial statements
- Multi-user management interface
- Service worker for 2G optimisation: ≤8s load on 2G (FR-WEB-002)

*USSD Gateway:*
- Scaffold USSD gateway prototype (FR-USSD-001–005)
- Menu tree resolving within 5 screens (FR-USSD-003)
- LLM fallback channel integration (FR-USSD-004)
- **[v1.2]** Implement health-check sidecar process on the Custom Gateway (monitors telco API response codes; triggers failover on 3 consecutive failures within 60 seconds)
- **[v1.2]** Implement Africa's Talking client for USSD session re-routing and SMS delivery fallback
- **[v1.2]** Normalise SMS delivery status callbacks across primary and Africa's Talking providers to a common internal schema

*Notification Service (Go):*
- Push notifications (Firebase Cloud Messaging)
- SMS gateway integration
- WhatsApp Business API template messages

*Integration & Security:*
- Generate k6 load test scripts for Gate 1 baseline (200 concurrent users, p95 < 500ms)
- Generate PWA Lighthouse test configuration (target: <8s on 2G simulation)
- Generate mock servers for all external APIs (GRA, SSNIT, MoMo, Vodafone Cash, Africa's Talking)
- Dependency vulnerability scanning configuration for CI
- **[v1.2]** Generate Expo EAS Update configuration (`eas.json`) with separate channels for development, staging, and production; configure staged rollout (10% of beta users, 2-hour observation window); set `FORCE_IMMEDIATE` policy for critical fixes and background update for standard fixes
- **[v1.2]** Ensure Asynq worker queue is operational for GRA and MoMo outbound calls (implemented in Sprint 2; verified end-to-end here)

**Human tasks:**
- UX testing on target devices: Tecno, Itel, Infinix (FR-MOB-002)
- Low-literacy user testing for voice interface (FR-NLP-010)
- Performance testing on simulated 2G (FR-WEB-002)
- USSD testing with NCA-allocated shortcode
- End-to-end workflow testing of all 8 operational workflows (§12.1–§12.8)
- **External penetration test — Gate 1 hard criterion: zero critical findings**

**Key requirements:** FR-MOB-001–008, FR-WEB-001–004, FR-OFF-001–004, FR-SYN-001–005, FR-USSD-001–005

---

## 5. Testing Architecture & Protocols

### 5.1 Test Generation Strategy

For every feature, the AI agent generates tests at three levels. The sequence matters: **unit tests are generated and human-reviewed before any functional code is written** (see §3.3). Integration and contract tests follow once unit tests pass. All three levels must be explicitly prompted — they will not be generated automatically unless requested.

#### 5.1.1 Unit Tests (Generated Before Implementation — Tests-First)

Unit tests are the first deliverable for every function, not the last. Generate them immediately after the design document is approved and before any functional code is written. The human reviewer's job at this stage is to verify domain edge cases — the AI cannot know what it does not know about the business domain.

**Critical edge cases that must appear in every financial or compliance test suite:**
- Zero-amount transactions and zero-rated items (e.g., exempt VAT)
- Negative amounts (credit notes, refunds, reversals)
- Multi-currency inputs with GHS pesewas as the canonical output unit
- Rate changes mid-period (verify config table reload, not cached stale rate)
- Idempotency key collision (same key submitted twice within 24-hour window)
- Boundary values at tier thresholds (subscription limits, WHT rate brackets)
- Offline edge cases: 30-day gap recovery, batch rollback on partial failure

**Go services:** Table-driven test patterns; ≥5 cases per function; testify for assertions.
**Python services:** pytest with parametrize; mock all external dependencies; ≥80% coverage for compliance-svc, ≥70% for all others.

**Example prompt — compliance service (tests-first):**

```
Generate the unit test suite for the VAT calculation function.
Do NOT write the function implementation — tests only.

Requirements: FR-COM-001 (composite rate 12.5% VAT + 2.5% NHIL/GETFund
from config table), FR-TAX-001 (rates from config, not hardcoded),
FR-COM-002 (rate change requires only data update)

Test cases must include:
1. Standard VAT on a taxable sale
2. Zero-rated item (VAT = 0)
3. Exempt item (no VAT applied)
4. Input tax credit deduction
5. Net VAT payable (output tax - input tax)
6. Rate change mid-period (verify config reload, not stale cache)
7. Multi-currency transaction (GHS conversion before VAT)
8. Boundary: amount = 0
9. Boundary: negative amount (credit note / refund)
10. Verify rates loaded from config table, not constants

Use pytest with parametrize. All monetary values in pesewas.
```

After human review confirms all domain edge cases are covered, generate the implementation:

```
The VAT calculation test suite has been reviewed and approved.
Now implement the VAT calculation function to pass all tests.
Do not modify any test. Flag any test that appears incorrect rather than
working around it.
```

#### 5.1.2 Integration Tests (Generated After Unit Tests Pass)

Critical integration test scenarios:

```
For the Transaction Engine, generate integration tests that:
1. Start Dockerized PostgreSQL + TimescaleDB + Redis + Redpanda
2. Submit a valid transaction via HTTP POST
3. Verify record exists in PostgreSQL
4. Verify business metric written to TimescaleDB hypertable
5. Verify event published to Kafka topic
6. Submit same transaction (same idempotency key)
7. Verify 409 with original transaction ID
8. Submit batch of 10 offline-queued transactions atomically
9. Inject failure at transaction 7 of 10
10. Verify full batch rollback — zero of 10 committed

Use testcontainers-go for container lifecycle.
```

Additional required integration tests:
- Offline sync → reconnect → conflict resolution for all five data types (Spec §1.3.2)
- GRA submission → retry → dead-letter queue flow
- MoMo transaction ingestion → Kafka → database persistence
- NLP query → Claude API → structured response → hallucination check → UI rendering

#### 5.1.3 Contract Tests (Generated Per Service Boundary)

```
Generate Pact contract tests between NLP Service (consumer)
and Transaction Engine (provider).

The NLP Service calls Transaction Engine to fact-check financial
query responses (FR-ADV-006 — hallucination mitigation).

Contract: NLP Service requests user's transaction summary for a
date range and expects:
- total_inflows_pesewas (integer)
- total_outflows_pesewas (integer)
- net_position_pesewas (integer)
- transaction_count (integer)

Generate both the consumer test (Python/NLP Service) and
the provider verification (Go/Transaction Engine).
```

#### 5.1.4 Performance & Load Tests

- k6 or Locust load test scripts — gate on: API p95 < 500ms @ 200 concurrent users (Gate 1)
- PWA Lighthouse audit — gate on: <8s on 2G simulation
- MLflow backtesting pipeline — gate on: ≥70% directional accuracy
- **Run load tests weekly in CI** from Sprint 2 onward against staging. Do not wait until Gate 1.

### 5.2 Debugging Protocol

When generated code fails, provide the AI agent with maximum diagnostic signal:

```
Bug report: [describe the symptom, not the assumed cause]

Service: [service name]
Environment: [local / staging / production]

Evidence:
- Error message (exact): [paste]
- Relevant log lines: [paste structured JSON logs]
- Request payload: [paste — remove PII]
- Datadog trace ID (if available): [paste]
- When it started: [timestamp]
- Frequency: [every request / intermittent / specific condition]

What I've already ruled out: [list]

Ask: What are the most likely root causes ranked by probability?
Then walk me through a diagnostic sequence.
```

Do not ask the AI agent to "fix the tests" without providing the exact error output. Provide the trifecta: the test, the error, the source code.

### 5.2.3 Outbound API Rate Limit Management [v1.2]

> **v1.2 Addition — Technical Specification §5.2.3 (Architecture Recommendation #9):** BizPulse's own API gateway implements robust inbound rate limiting. However, the external providers BizPulse calls — GRA, MTN MoMo, Vodafone Cash, bank feeds, Anthropic Claude API — all enforce their own outbound rate limits. At Phase 3 scale (5 million API calls/day), unmanaged upstream throttling will cause cascading failures in the transaction engine, compliance filing pipeline, and credit scoring service.

**Recommended Solution: Asynq (Go-native, Redis-backed)**

Asynq is chosen over alternatives (Celery, Sidekiq) because it is written in Go — matching BizPulse's core services stack — and is backed by Redis, which is already provisioned in the data layer. This avoids introducing a new runtime dependency solely for task queuing.

**External API Rate Limit Profiles:**

| Provider | Known Limit | Impact if Exceeded | Retry Strategy |
|---|---|---|---|
| GRA API | Low-volume (estimated <100 req/min) | Filing failures, compliance risk | Exponential backoff; DLQ after 5 failures; alert DPO |
| MTN MoMo API | ~300 req/min (commercial tier) | Transaction sync gaps | Exponential backoff with jitter; auto-resume |
| Vodafone Cash API | ~150 req/min (estimated) | Transaction sync gaps | Same as MoMo |
| Bank Feeds (Open Banking) | Varies by bank (50–200 req/min) | Statement gaps | Linear backoff; daily batch fallback |
| Anthropic Claude API | Tier-based (tokens/min + req/min) | NLP service degradation | Haiku fallback (§5.3.3); queue non-urgent requests |

**Backoff Policy:**

| Attempt | Delay | Notes |
|---|---|---|
| 1 (initial) | Immediate | First attempt; no delay |
| 2 | 5 seconds | Base delay |
| 3 | 30 seconds | Exponential |
| 4 | 5 minutes | Exponential |
| 5 | 30 minutes | Final retry |
| DLQ | — | Alert fired via PagerDuty; manual review required for GRA/compliance tasks; additional DPO alert for GRA DLQ events |

Jitter of ±20% is applied to all retry delays to prevent thundering herd on provider recovery.

**Worker Queue Design:**
- Priority queues per provider (GRA = critical, bank feeds = low)
- Per-provider concurrency limits (respects upstream rate caps)
- Task deduplication via idempotency keys
- 429 / 503 response → re-queue with backoff
- Success → write result to PostgreSQL / emit Kafka event
- DLQ → PagerDuty alert + InfluxDB metric

> **AI agent constraint:** No application service (Transaction, Compliance, Analytics) may make a direct synchronous HTTP call to GRA, MTN MoMo, Vodafone Cash, bank feeds, or the Anthropic Claude API. All such calls must be enqueued as Asynq tasks. See Appendix B prompt template B.5 for the Asynq task implementation template.

### 5.3 Compliance Verification Pass

After every feature touching financial data, compliance reporting, or user PII:

```
Review [function/module name] against these criteria:
1. Is the VAT/tax rate sourced exclusively from the compliance_rates table?
2. Is there any possibility of a hardcoded rate anywhere in the call chain?
3. Does the audit log capture all fields required for Act 843 traceability?
4. Are all GRA API calls covered by retry logic with dead-letter fallback?
5. Is user PII encrypted at rest and masked in log outputs?
6. Are all monetary values in pesewas (BIGINT), not floats?

List any violations found and propose the fix for each.
```

---

## 6. Cross-Cutting Concerns

These are implemented incrementally across all sprints, not as a single sprint. Include them in every service's implementation from the start.

### 6.1 Observability (Implemented from Sprint 0)

Observability is a Gate 1 prerequisite, not a post-MVP concern. Instrument every service at the moment of deployment.

**Go services — generate Datadog APM instrumentation:**
```
For each Go service, generate Datadog APM instrumentation:
- HTTP middleware that traces every request
- Database query tracing for PostgreSQL
- Kafka producer/consumer span tracing
- Custom metrics: transaction count, error rate, latency percentiles
```

**Python services:**
```
For each Python service, generate:
- ddtrace instrumentation for FastAPI
- MLflow integration for model metric reporting
- Custom Datadog metrics for NLP resolution rate (NFR-OBS-004)
  and bias drift monitoring (NFR-OBS-005)
```

**Required logging per query/operation:**
- Every NLP query: intent, language detected, model used, response time, resolution status, escalation flag
- Every compliance filing: filing type, submission status, GRA receipt ID, error codes
- Every transaction: service, idempotency key, source provider, processing time

**InfluxDB write clients for infrastructure metrics:** API latency, Kafka throughput, pod metrics (FR-DAT-003)

> **[v1.2] Additional observability requirements:**
> - **Asynq DLQ events:** emit custom metrics to InfluxDB and trigger PagerDuty alerts on every DLQ entry. GRA DLQ events additionally alert the DPO.
> - **Africa's Talking fallback activations:** log each failover event as a Datadog custom metric (`ussd.fallback.activated`) to enable USSD channel availability reporting.
> - **OTA update deployments:** log EAS Update deployment events (channel, rollout percentage, error rate) to Datadog for staged rollout monitoring and rollback triggering.

### 6.2 Security Hardening (Applied Per Service)

- Input validation schemas on all API endpoints (FR-SEC-016)
- JWT validation via Kong gateway middleware (FR-SEC-002)
- Rate limiting per subscription tier (FR-SEC-012):
  - Starter, Growth, Professional, Enterprise tiers
- CORS and CSP headers for the PWA
- Dependency vulnerability scanning in CI (Semgrep / Snyk)
- TLS certificate automation (ACM auto-renewal + certificate pinning in mobile)
- Field-level PII encryption (pgcrypto) reviewed against Act 843

### 6.3 Financial Calculation Integrity Rules

Every function that performs monetary arithmetic requires mandatory human review regardless of who generated it:

- **Python:** Use `decimal.Decimal` — never `float`
- **Go:** Use `shopspring/decimal` — never `float64`
- **Database:** Store all monetary values as `BIGINT` (pesewas)
- **Timestamps:** `TIMESTAMPTZ` UTC everywhere
- All affected functions: VAT, NHIL/GETFund, CIT, PAYE, WHT, credit scoring, cash flow forecasting

### 6.4 Naming Standards (Enforced in All Generated Output)

- Ghana Enterprises Agency: always **"GEA"** — never "NBSSI"
- Kenya is **"East Africa Track"** — never "ECOWAS"
- Tax rates: always sourced from `compliance_rates` config table — never hardcoded literals
- Model strings: always reference the pinned constants in config — never inline strings
- **[v1.2]** USSD/SMS fallback provider: always **"Africa's Talking"** — never "Hubtel" (commercial conflict of interest; see §1.4)

### 6.5 Scalability Design Principles (Designed for Phase 3 from Day 1)

| Dimension | Phase 1 Baseline (Gate 1) | Must Scale To (Gate 3) |
|-----------|--------------------------|------------------------|
| Concurrent users | 200 | 25,000 |
| Daily transactions | 50,000 | 2,000,000 |
| API calls/day | 100,000 | 5,000,000 |
| Data storage | 500 GB | 10 TB |

- **Partition transactions table by month from Sprint 1.** Changing partitioning strategy post-launch is expensive.
- **Kafka partition count:** Set conservatively high (12–24 partitions for main transaction topics). Increasing partitions on live topics requires consumer group rebalancing.
- **Connection pooling:** Use PgBouncer from Day 1. Never connect application services directly to PostgreSQL.
- **Read replicas:** Analytics Service must read from replicas from Sprint 3 onward. Analytics queries must never contend with transaction writes.
- **Session state:** Always in Redis, never in service memory.
- **HPA:** Kubernetes HPA must be configured from Sprint 1. The spec requires scale-out within 3 minutes of threshold breach (NFR-SCA-001). Test this in staging before Gate 1.

---

## 7. Professional Recommendations & Risk Mitigation

### 7.1 Critical Risk Areas

#### 7.1.1 Financial Calculation Integrity
The highest-stakes technical risk. A rounding error in VAT calculation or a floating-point artefact in a credit score has regulatory consequences.

**Mitigation:** Establish a "financial calculation review" gate. Flag every function performing monetary arithmetic for mandatory manual review by a developer who understands the regulatory implications. Use `decimal.Decimal` in Python, `shopspring/decimal` in Go, BIGINT in PostgreSQL — without exception.

#### 7.1.2 Offline Sync Correctness
The offline-first architecture is BizPulse's core differentiator and its most complex engineering problem.

**Mitigation:** Build the sync engine as an isolated, heavily-tested module before building any user-visible features. Minimum 50 integration tests covering: normal sync, duplicate detection, batch rollback on partial failure, checksum mismatch, 30-day offline recovery, and every conflict resolution path (financial append-only, settings LWW, inventory manual resolution, tax audit merge). Test against a physical device running real SQLite, not only emulators.

#### 7.1.3 LLM Hallucination in Financial Contexts
FR-ADV-006 is not optional. An LLM fabricating a financial figure causes direct regulatory harm to a user.

**Mitigation:** The database always wins. Every numerical claim in an LLM response is cross-referenced against the transaction database before delivery. Design the architecture so the LLM generates narrative structure only; the data layer populates all numbers. Never let the LLM interpolate financial figures.

#### 7.1.4 Regulatory Dependency Lead Times
GRA API access (3–6 months) is on the critical path for Gate 1. If delayed, the entire Phase 1 timeline is at risk.

**Mitigation:** Start every regulatory dependency on Day 1. Build mock/stub integrations for all external APIs immediately so development can proceed in parallel. The AI agent can generate mock servers from documented API schemas. The compliance officer must report on regulatory dependency status weekly.

#### 7.1.5 MoMo API Commercial Access
The entire product is built on mobile money transaction data. Without live MTN MoMo and Vodafone Cash API access, the core data ingestion pipeline cannot be tested in production conditions.

**Mitigation:** If MoMo agreements have not reached final negotiation by Month 3, escalate to CEO level. This is not a partnerships team issue at that point.

#### 7.1.6 USSD Channel Outage [v1.2]
USSD is the primary channel for users without smartphones — the segment least able to fall back to the mobile app or PWA. A telco API outage without automated recovery creates a service gap precisely where the user impact is highest.

**Mitigation:** Africa's Talking aggregator fallback (§1.4) with automated health-check sidecar. Failover requires zero manual intervention. Test the failover mechanism in staging before the Phase 2 pilot launch. Ensure USSD channel availability is tracked as a Datadog custom metric (`ussd.fallback.activated`) visible in the observability dashboard.

#### 7.1.7 Outbound API Rate Limit Cascades [v1.2]
At Phase 3 scale (5M API calls/day), unmanaged upstream throttling from GRA, MoMo, bank feeds, and Anthropic will cause cascading failures across the transaction engine, compliance filing pipeline, and credit scoring service simultaneously.

**Mitigation:** Asynq worker queue (§5.2.3) implemented from Sprint 2. Per-provider concurrency limits prevent thundering herd. Exponential backoff with ±20% jitter prevents recovery spikes. Dead Letter Queue with PagerDuty alerting ensures no silent failure. GRA DLQ events additionally alert the DPO given compliance filing implications. Monitor DLQ rate as a Gate 2 criterion (target: <1% of total outbound API calls).

#### 7.1.8 DPIA Delay Risk [v1.2]
If the DPIA process drifts without a hard deadline, the engineering team risks building Pinecone dependencies that become expensive to unwind at Phase 2. An unresolved compliance status also blocks the Phase 2 Gate review.

**Mitigation:** Binding DPIA schedule (§2.1.2) with a drop-dead date at end of Phase 1 (Month 6). If Pinecone adequacy is not confirmed by that date, pgvector is automatically committed — no further decision required. Gate 1 checklist includes DPIA initiation status verification. Gate 2 checklist requires the final decision to be recorded in `docs/DECISIONS.md`.

#### 7.2.1 Context Window Overflow
**Pitfall:** Loading the entire specification into context and asking "build the transaction engine."
**Avoidance:** One feature. One endpoint. One prompt. Always. Use the three-layer context model from §3.2.

#### 7.2.2 Undirected Code Generation
**Pitfall:** Asking "create the mobile app" without screen designs and component specifications.
**Avoidance:** Provide Figma exports or detailed wireframes per screen. Break mobile development into individual screen prompts. Provide the exact data shapes each screen expects.

#### 7.2.3 Skipping Phase A (Interface-First)
**Pitfall:** Asking for a complete service implementation in one go. Results in tightly coupled code with implicit interfaces.
**Avoidance:** Always run Phase A (interface definition) before Phase B (implementation). This is non-negotiable for service boundaries.

#### 7.2.4 Ignoring USSD
**Pitfall:** Treating USSD as an afterthought. USSD is the LLM fallback channel and the primary channel for users without smartphones.
**Avoidance:** Design the USSD menu tree during Sprint 0. Implement the USSD gateway as a first-class service during Sprint 6. NCA licensing (2–3 months) must start by Week 4.

#### 7.2.5 Premature ML Optimisation
**Pitfall:** Spending Phase 1 time on LSTM architecture, hyperparameter tuning, or custom Twi speech model training.
**Avoidance:** Use Prophet for cash flow forecasting in Phase 1 (simpler, faster to deploy, meets MVP requirement). Use off-the-shelf Whisper for English STT. Defer Twi fine-tuning to Phase 2 when real user data exists. Use rule-based intent classification for NLP MVP; upgrade to ML-based classification when the 500+ example training corpus (FR-NLP-008) is available.

#### 7.2.6 Treating Observability as Post-MVP
**Pitfall:** Bolting on monitoring after features are built.
**Avoidance:** Sprint 0 includes Datadog instrumentation baseline. Every service generated by the AI agent includes observability from its first commit. The NLP resolution rate (Gate 2 criterion) must be measurable from the day the NLP service is deployed.

### 7.3 Boundaries — What Must Never Be Delegated to the AI Agent

| Do Not Delegate | Required Resource |
|-----------------|------------------|
| GRA API compliance legal interpretation | Qualified tax counsel familiar with Ghana Revenue Authority |
| Act 843 Data Protection Impact Assessment | Qualified data protection practitioner with legal sign-off |
| ML model fairness evaluation for credit scoring | Human review of bias outputs across protected demographic segments |
| Twi/Ga/Ewe/Hausa NLP accuracy validation | Native speaker QA testers per language |
| Regulatory go/no-go decisions at Phase Gates | Compliance Officer + Technical Lead + Product Manager |
| Penetration test findings sign-off | External qualified security practitioner |
| Financial statement accuracy sign-off | Qualified accountant (ICAG standard) |
| **[v1.2] DPIA findings and Pinecone/pgvector final decision** | **CTO + DPO — binding decision required by end of Phase 1 (Month 6); no exceptions without board-level sign-off** |
| **[v1.2] Africa's Talking failover test sign-off** | **Engineering Lead + Operations — must be tested in staging before Phase 2 pilot launch; not delegatable to AI agent** |

### 7.4 How to Maximise AI Agent Effectiveness

- **Spec before code.** The most valuable output is a technical design document. Use the agent to reason about architecture first.
- **Tests before implementation.** Generate and human-review unit tests before writing a single line of functional code (§3.3). For financial and compliance functions, this is where domain edge cases are caught — not in code review.
- **Narrow every prompt.** "Build the analytics service" is a bad prompt. "Build the Kafka consumer for incoming transaction events in the analytics-svc, consuming from transactions.processed, implementing at-least-once delivery with manual offset commits after database write confirms" is a good prompt.
- **Always run a self-critique pass.** After any compliance or ML logic is generated, immediately prompt: *"What are the edge cases this implementation doesn't handle? What assumptions did you make that could be wrong for the BizPulse context specifically?"*
- **Use the agent as a code reviewer.** Paste your own code with: *"Review this for correctness, security vulnerabilities, performance anti-patterns, and Act 843 compliance issues. Be critical."*
- **Never accept the first version of complex logic.** Iterate.
- **Maintain DECISIONS.md.** Every significant architectural decision made during a session: what was decided, why, alternatives rejected. This protects future sessions when context is lost.
- **Keep CLAUDE.md lean.** As the project grows, audit CLAUDE.md regularly against the 150-line budget (§3.1). A bloated context file crowds out the code being reasoned about. Constraints enforced by CI tooling should be removed from CLAUDE.md — the linter owns them now.

---

## 8. Phase Gate Readiness Checklists

### Gate 1 Engineering Checklist (Month 6)

**Infrastructure:**
- [ ] All 9 infra components deployed via Terraform; zero manual cloud console changes
- [ ] Kong HA cluster: 3 instances confirmed operational with health monitoring
- [ ] Kubernetes HPA configured; scale-out confirmed within 3 minutes of threshold breach
- [ ] Certificate lifecycle automation operational; zero expired certificates

**Core Services:**
- [ ] Transaction engine: append-only enforced; idempotency keys validated in load test
- [ ] Offline sync: 30-day offline → reconnect → reconciliation tested for all 5 data types
- [ ] pgvector operational; Pinecone DPIA status documented in `docs/DECISIONS.md` (initiated Week 1; in-progress)
- [ ] VAT computation: zero hardcoded rates confirmed by automated test
- [ ] Claude model versions pinned in config; confirmed not to drift
- [ ] **[v1.2]** Asynq worker queue operational; all outbound calls to GRA and MoMo routed through queue — no direct synchronous calls from application services
- [ ] **[v1.2]** Africa's Talking fallback client deployed; failover tested in staging (3-failure trigger verified)
- [ ] **[v1.2]** OTA update pipeline configured (EAS Update); test rollout and rollback verified

**Security:**
- [ ] External penetration test complete; zero critical findings
- [ ] Field-level encryption for PII confirmed (schema audit)
- [ ] Audit logging with tamper-evident storage (log integrity verification)

**Performance:**
- [ ] API p95 < 500ms @ 200 concurrent users (k6 load test report on file)
- [ ] PWA Lighthouse score: < 8s on 2G simulation

**Observability:**
- [ ] Datadog dashboards live for all services
- [ ] NLP resolution rate tracking dashboard live
- [ ] Bias drift monitoring dashboards live; no unresolved threshold breach alerts

**Compliance & Regulatory:**
- [ ] DPC registration certificate on file
- [ ] GRA Certified Tax Software application submitted (acknowledgement on file)
- [ ] MTN MoMo API agreement signed or in final negotiation
- [ ] GEA naming audit: zero "NBSSI" references in codebase or UI
- [ ] **[v1.2]** DPIA initiated (Week 1 mandatory); in-progress status confirmed with DPO
- [ ] **[v1.2]** Africa's Talking API credentials obtained, configured, and referenced in `docs/INTEGRATION_MANIFEST.md`

**Quality:**
- [ ] All P1 requirements passing acceptance tests
- [ ] ≥2 signed partner LOIs (≥1 telco or bank)
- [ ] USSD prototype functional on NCA-allocated shortcode
- [ ] **[v1.2]** USSD prototype includes Africa's Talking fallback — failover activation logged in Datadog

---

### Gate 2 Engineering Checklist (Month 12)

- [ ] NLP resolution rate ≥70% confirmed from production logs (not synthetic test)
- [ ] GRA submission success rate ≥95% from pilot compliance logs
- [ ] Monthly churn tracking operational; ≤10% pilot cohort churn
- [ ] MTN MoMo + Vodafone Cash live API integrations confirmed
- [ ] SSNIT payroll compliance module operational (if API access secured)
- [ ] Demand prediction model deployed with MLflow tracking
- [ ] Credit scoring MVP operational (requires ≥30 days transaction history per user)
- [ ] Kong auto-scaling tested; scale-out confirmed within 3 minutes
- [ ] Bias monitoring dashboards live; no unresolved threshold breach alerts
- [ ] ISO 27001 gap assessment initiated (target certification Gate 3)
- [ ] **[v1.2]** Pinecone/pgvector decision confirmed and recorded in `docs/DECISIONS.md` (DPIA drop-dead date was end of Phase 1)
- [ ] **[v1.2]** Asynq DLQ rate <1% of total outbound API calls across all providers
- [ ] **[v1.2]** Africa's Talking fallback activation events visible in Datadog dashboard; zero missed failover triggers during pilot
- [ ] **[v1.2]** OTA update pipeline used for ≥1 production deployment; rollback capability verified in production

---

## Appendix A: CLAUDE.md — AI Agent System Context

This is the canonical content of the `CLAUDE.md` file at the repository root. Copy this verbatim, then update the **Current Sprint Context** section at the start of each sprint.

```markdown
# BizPulse AI — AI Agent System Context
# TOKEN BUDGET: Keep this file under 150 lines. Every line should be a constraint
# the agent would otherwise violate. Documentation belongs in docs/ONBOARDING.md.
# Remove constraints once enforced by CI tooling — don't accumulate.

## What This Project Is
BizPulse AI is an enterprise-grade AI platform for Ghanaian SMEs.
It is mobile-first, offline-capable, multilingual (English, Twi, Ga, Ewe, Hausa, Dagbani),
and built for infrastructure-constrained environments (intermittent connectivity, 2G networks).
Primary cloud: AWS af-south-1 (Cape Town). DR: eu-west-1.

## Primary Technical Stack
- Backend Services (Go 1.22): user-svc, transaction-svc, notification-svc
  — Follow Uber Go style guide. All services use structured logging (slog).
  — Error handling: wrap with context; never swallow errors.
- Backend Services (Python 3.12 + Poetry): analytics-svc, compliance-svc, nlp-svc
  — Black formatting, Ruff linting, type hints mandatory. All ML models tracked in MLflow.
- Mobile: React Native (Expo SDK 52+), offline-first with SQLite WAL encryption
- Web: Next.js 15+, TypeScript strict mode, PWA with Workbox service worker
- API Gateway: Kong (HA, 3-instance minimum, PostgreSQL-backed) — NEVER single-instance
- Databases: PostgreSQL 16 + TimescaleDB + pgvector, InfluxDB 2.x, Redis 7
- Event Streaming: Apache Kafka (Avro schemas in /shared/avro/)
- ML/AI Stack: LangChain, Whisper, MLflow, BentoML, Anthropic Claude API
- Auth: Keycloak (OAuth 2.0 / OIDC); Kong validates JWTs at gateway. JWT expiry: 15 minutes.
- IaC: Terraform + ArgoCD + Kubernetes (EKS)

## Pinned AI Model Versions — DO NOT CHANGE WITHOUT EXPLICIT RELEASE REVIEW
- Complex NLP (Sonnet path): claude-sonnet-4-6
- Simple queries (Haiku path): claude-haiku-4-5-20251001

## [v1.2] Outbound API Queue — Asynq
- Asynq (Go-native, Redis-backed) manages ALL outbound calls to upstream providers.
- Providers in scope: GRA, MTN MoMo, Vodafone Cash, bank feeds, Anthropic Claude API.
- NEVER make direct synchronous HTTP calls from application services to these providers.
- Always enqueue as an Asynq task; the worker pool handles retry, backoff, and DLQ.
- Backoff: immediate → 5s → 30s → 5m → 30m → DLQ (±20% jitter on all delays).
- GRA DLQ events: alert DPO in addition to PagerDuty.
- DLQ metrics: emit to InfluxDB as custom Datadog metrics.

## [v1.2] USSD/SMS Fallback — Africa's Talking
- Primary: Custom Gateway → direct telco APIs (MTN, Vodafone, AirtelTigo).
- Fallback: Africa's Talking aggregator — activated automatically on 3 consecutive primary
  failures within 60 seconds via health-check sidecar (no manual intervention required).
- NEVER use Hubtel for USSD/SMS fallback — commercial conflict of interest (§7.1).
- SMS delivery status callbacks normalised to common internal schema across both providers.
- Log failover events as Datadog custom metric: ussd.fallback.activated.

## [v1.2] OTA App Updates — Expo EAS Update
- EAS Update is the delivery mechanism for critical and standard bug fixes.
- OTA updates are JavaScript/asset changes ONLY — native module changes require store submission.
- Staged rollout: 10% of beta users first; 2-hour observation window before full rollout.
- Critical fixes: updateType FORCE_IMMEDIATE. Standard fixes: background update on next launch.
- TLS pin updates: OTA staged rollout, 45 days before expiry, 30-day overlap window.
- Rollback: EAS Update instant rollback to prior published update is primary recovery mechanism.

## Critical Compliance Constraints
- Ghana Data Protection Act (Act 843, 2012) governs ALL data handling
- All primary data must reside in AWS af-south-1 (Cape Town) — DR only in eu-west-1
- Pinecone is NOT production-approved until DPIA is complete; use pgvector only
- **[v1.2] DPIA DROP-DEAD DATE: end of Phase 1 (Month 6).** If Pinecone adequacy is not confirmed
  by this date, pgvector is the committed production vector store — no exceptions without board sign-off.
- VAT/CST/CIT/PAYE/WHT rates must NEVER be hardcoded — always read from compliance_rates config table
- GRA VAT rates must be verified against current Finance Act before every release
- All financial calculations must use decimal types — NEVER float/float64
- All monetary values stored as BIGINT (pesewas) — NEVER decimal/float in DB

## Offline-First Architecture Rules
- All mobile features must degrade gracefully without connectivity
- SQLite with encrypted WAL is the local store on device
- Sync uses queue-based delta protocol with server-side idempotency keys
- Financial transactions are append-only — no overwrites, no deletes
- Conflict resolution is defined per data type — see docs/OFFLINE_SYNC_SPEC.md

## Code Quality Non-Negotiables
- TypeScript: strict mode, no `any`, ESLint + Prettier
- Unit test coverage: ≥80% (compliance-svc), ≥70% (all other services)
- All services emit structured logs (JSON) to stdout — Datadog-compatible
- All mutation APIs must enforce idempotency keys
- Zero expired TLS certificates — automated certificate lifecycle management
- All infrastructure changes via Terraform + ArgoCD only; no manual console changes
- All timestamps: ISO 8601 UTC (TIMESTAMPTZ in DB)
- Integration tests run against Dockerized dependencies via testcontainers

## Performance Targets (Gate 1 minimum)
- API p95 response time: <500ms under 200 concurrent users
- NLP simple query (Haiku path): <500ms
- NLP complex query (Sonnet path): <3–5s
- PWA core dashboard on 2G: <8s load time

## Naming Standards
- Ghana Enterprises Agency is always "GEA" — NEVER "NBSSI"
- Kenya is "East Africa Track" — NEVER "ECOWAS"
- Tax rates always sourced from config table — NEVER hardcoded literals
- [v1.2] USSD/SMS fallback provider is always "Africa's Talking" — NEVER "Hubtel"

## File Structure Reference
/services/{service-name}/cmd/         — Entrypoints (Go)
/services/{service-name}/internal/    — Business logic (Go)
/services/{service-name}/api/         — HTTP/gRPC handlers (Go)
/services/{service-name}/src/         — Source (Python)
/mobile/src/                          — React Native app
/web/src/                             — Next.js PWA
/infra/terraform/modules/             — Terraform modules
/infra/kubernetes/                    — Kubernetes manifests
/shared/avro/                         — Kafka Avro event schemas
/shared/sdk/                          — Shared client SDKs
/docs/                                — Architecture artefacts
/compliance/                          — Regulatory documentation

## Current Sprint Context
[UPDATE THIS SECTION AT THE START OF EVERY SPRINT]
Sprint: [number]
Weeks: [range]
Service in focus: [service name]
Requirements in scope: [FR-* IDs]
Interfaces defined this sprint: [list]
Previously completed: [brief summary]
ADR decisions in force: [relevant ADR IDs]
```

---

## Appendix B: Prompt Templates for Recurring Tasks

### B.1 New API Endpoint Implementation

```
Service: [service name]
Language: [Go / Python]
Endpoint: [HTTP method] [path]
Requirement IDs: [FR-XXX-NNN]

Purpose: [one sentence]

Request schema:
[JSON schema or example]

Response schema:
[JSON schema or example]

Error cases:
- [error condition] → [HTTP status] + [error body]

Auth: [public / authenticated / admin-only]
Rate limit tier: [starter / growth / professional / enterprise]

Generate:
1. Handler function
2. Service/use-case function
3. Repository function (if DB interaction needed)
4. Unit tests (table-driven, ≥5 cases including edge cases)
5. Integration test against Dockerized dependencies
6. Datadog APM instrumentation
```

### B.2 Database Migration

```
Migration number: [NNN]
Purpose: [what this migration does]

Changes:
- [ADD TABLE / ADD COLUMN / ALTER / CREATE INDEX / etc.]

Requirements: [relevant FR-* IDs]

Constraints:
- Must be backwards compatible (zero-downtime deployment)
- Must include both up and down migration
- Must use explicit types (no ORM magic)
- Monetary columns: BIGINT (pesewas)
- Timestamps: TIMESTAMPTZ UTC
- PII columns: pgcrypto encrypted
```

### B.3 Kafka Stream Processing Job (Flink)

```
Job name: [name]
Input topic: [Kafka topic]
Output topic: [Kafka topic]
Output stores: [PostgreSQL / TimescaleDB / S3]

Processing steps:
1. [step description with field-level detail]
2. [step description]

Requirements: [relevant FR-ING-* or FR-ANA-* IDs]

Error handling:
- Schema validation failures → dead-letter queue
- Processing failures → retry 3x with exponential backoff, then dead-letter

Generate the Flink job in [Java / Python] with unit tests.
```

### B.4 React Native Screen

```
Screen name: [name]
Navigation: [position in app navigation hierarchy]
Requirements: [FR-MOB-*, FR-OFF-*, etc.]

Data sources:
- [API endpoint or local SQLite query]

Offline behaviour:
- [what happens when offline]

UI elements:
[list of components with interaction descriptions]

Generate:
1. Screen component with TypeScript
2. Custom hooks for data fetching and state management
3. Offline-aware data layer (SQLite read/write)
4. Component tests
```

### B.5 Compliance Feature (Regulatory Context)

```
Context: BizPulse AI compliance-svc. Act 843 and GRA requirements apply.
See docs/COMPLIANCE_MATRIX.md (attached).

Task: Implement [feature name].

Requirements:
- Tax/VAT rate must be fetched from compliance_rates table — NEVER hardcoded
- Output must conform to [GRA / SSNIT] schema — schema file attached
- All inputs validated before computation begins
- Audit log entry required for every [action] (fields: user_id, business_id,
  period, generated_at, submitted_at, reference_id)
- [v1.2] GRA API calls must be routed through Asynq worker queue — no direct
  synchronous calls. Use the Asynq task enqueuer helper (see B.7).
- Dead-letter Kafka topic on exhausted retries; DPO alert on GRA DLQ events
- Unit tests must mock external API for both success and failure paths

Reference: [API spec attached]. [Compliance matrix section X.X attached].
```

### B.6 ML Model Implementation

```
Context: BizPulse AI analytics-svc — [model name] module.
ML stack: Python 3.12, MLflow, pandas, [Prophet / scikit-learn / TensorFlow].
Model spec: docs/ML_MODEL_REGISTRY.md (attached).

Task: Implement the [model name] pipeline.

Requirements:
- [Forecast horizons / prediction targets]
- Features: [list with domain significance]
- Output schema: [exact fields and types]
- Register every run in MLflow with: model version, training date,
  validation metrics, feature importances
- Backtesting must validate [metric] ≥ [threshold] on held-out set
- Bias check: run performance comparison across [demographic / sector segments]

Do not use synthetic data. Use schema from docs/DATA_MODEL.md.
```

### B.7 Outbound API Call via Asynq [v1.2]

Use this template for ANY outbound call to GRA, MTN MoMo, Vodafone Cash, bank feeds,
or the Anthropic Claude API. Direct synchronous calls to these providers are prohibited.

```
Context: BizPulse AI [service-name] — outbound call to [provider].
Queue: Asynq (Go), Redis-backed. See docs/ARCHITECTURE.md §5.2.3.

Task: Implement [task description] as an Asynq worker task.

Task payload schema:
- [field]: [type] — [description]

Queue configuration:
- Priority: [critical | default | low]  (GRA = critical; bank feeds = low)
- Per-provider concurrency limit: [N] concurrent workers maximum
- Retry policy: exponential backoff (immediate → 5s → 30s → 5m → 30m); ±20% jitter
- After 5 failures: Dead Letter Queue; alert PagerDuty
- GRA tasks additionally: alert DPO on DLQ event
- Success: write result to PostgreSQL / emit Kafka event to [topic]
- DLQ: log metric to InfluxDB as [metric-name]

Generate:
1. Asynq task type definition and payload struct (Go)
2. Worker handler function with provider client call
3. Task enqueuer helper function
4. Unit tests: mock Asynq client covering success, retry (429/503), and DLQ paths
5. Datadog metrics for queue depth, retry count, DLQ rate
6. Integration test using testcontainers-go (Redis + mock provider server)
```

### B.8 USSD Gateway with Africa's Talking Fallback [v1.2]

Use this template when implementing or extending the USSD gateway.
The health-check sidecar and Africa's Talking client must always be included.

```
Context: BizPulse AI USSD gateway — primary channel for low-connectivity users.
Fallback provider: Africa's Talking. See docs/INTEGRATION_MANIFEST.md.

Task: Implement [USSD feature / menu screen].

Routing requirements:
- Primary: Custom Gateway → direct telco API (MTN / Vodafone / AirtelTigo)
- Fallback: Africa's Talking aggregator, activated automatically:
    Trigger: 3 consecutive primary failures within a 60-second window
    Mechanism: health-check sidecar (Go goroutine) — no manual intervention
- SMS delivery status callbacks normalised to common internal schema
- USSD short code assignment remains BizPulse's — no separate NCA license needed
- Log each fallback activation: Datadog custom metric ussd.fallback.activated

USSD feature requirements:
- Menu tree resolves within 5 screens (FR-USSD-003)
- [additional feature-specific requirements]

Generate:
1. USSD session handler for [feature]
2. Health-check sidecar (Go goroutine + atomic failure counter + 60s window reset)
3. Africa's Talking client: USSD re-routing + SMS delivery methods
4. Callback normalisation layer (maps both provider schemas to internal schema)
5. Unit tests for failover trigger logic (exactly 3 failures in 60s window)
6. Unit tests for callback normalisation (both provider response shapes)
7. Integration test: simulate primary failure → verify Africa's Talking receives session
```

```
Context: BizPulse AI analytics-svc — [model name] module.
ML stack: Python 3.12, MLflow, pandas, [Prophet / scikit-learn / TensorFlow].
Model spec: docs/ML_MODEL_REGISTRY.md (attached).

Task: Implement the [model name] pipeline.

Requirements:
- [Forecast horizons / prediction targets]
- Features: [list with domain significance]
- Output schema: [exact fields and types]
- Register every run in MLflow with: model version, training date,
  validation metrics, feature importances
- Backtesting must validate [metric] ≥ [threshold] on held-out set
- Bias check: run performance comparison across [demographic / sector segments]

Do not use synthetic data. Use schema from docs/DATA_MODEL.md.
```

---

## Appendix C: Session Management Templates

### C.1 Session Opening Template

Use this at the start of every AI agent session.

```
## Session Context
Project: BizPulse AI
Service: [service name]
Session Goal: [one sentence — what will be complete by end of session]
Sprint: [sprint number], Weeks [range]
Constraints in force: See CLAUDE.md (loaded)
Attached artefacts: [list all documents attached]

## What Was Completed Last Session
[paste from SESSION_LOG.md]

## This Session's Task
[precise, narrow, scoped task — use prompt templates from Appendix B]

## Completion Criteria
This session is complete when:
1. [specific deliverable 1]
2. [specific deliverable 2]
3. Unit tests pass for all new code
4. No compliance constraint violations identified
5. Datadog instrumentation included
```

### C.2 Session Closing Prompt

Run this before closing every session. Save the output to SESSION_LOG.md.

```
Summarise this session:
1. What was built (specific files, functions, endpoints)
2. What is incomplete (partially started, pending decisions)
3. Architectural decisions made during this session
4. Assumptions I should verify before the next session
5. What must be resolved or clarified before continuing this work
```

### C.3 Constraint Drift Re-Anchor

Run every 5–7 turns during any session:

```
Confirm the following constraints are still in force in the current
implementation:
1. We are using pgvector, not Pinecone
2. All VAT/tax rates are sourced from the compliance_rates config table —
   no hardcoded values
3. All monetary values are BIGINT (pesewas), not float
4. Claude model strings are referencing the pinned constants only
5. All timestamps are TIMESTAMPTZ UTC
6. [v1.2] All outbound calls to GRA, MoMo, Vodafone, and bank feeds are
   routed via Asynq — no direct synchronous HTTP calls from application services
7. [v1.2] USSD/SMS fallback provider is Africa's Talking — never Hubtel
8. [v1.2] OTA updates are JavaScript/asset changes only — native module
   changes require full store submission, not EAS Update

Flag any drift you detect in the code generated this session.
```

---

## Appendix D: Key Requirement-to-Sprint Mapping

| Requirement ID | Description | Sprint | Gate |
|----------------|-------------|--------|------|
| NFR-MAI-003 | Infrastructure as Code (Terraform + ArgoCD) | 0 | 1 |
| NFR-REL-006 | Kong HA cluster (3 instances) | 0 | 1 |
| NFR-OBS-001 | Datadog instrumentation baseline | 0 | 1 |
| FR-DAT-001–005 | Database schema and data layer | 1 | 1 |
| FR-SEC-001–009 | Auth, RBAC, field-level encryption | 1 | 1 |
| FR-DPC-001–003 | Consent management, DPC registration | 1 | 1 |
| FR-BIZ-001–006 | Subscription tier enforcement | 1 | 1 |
| FR-INT-001–005 | Transaction engine core | 2 | 1 |
| FR-ING-001–006 | Kafka ingestion + Flink pipeline | 2 | 1 |
| FR-SYN-001–005 | Offline sync and idempotency | 2 | 1 |
| FR-CON-001–005 | Conflict resolution matrix | 2 | 1 |
| **FR-OUTQ-001 [v1.2]** | **Asynq outbound API worker queue** | **2** | **1** |
| FR-FIN-001–010 | Financial statement generation | 3 | 1 |
| FR-ANA-001–006 | Cash flow forecasting | 3 | 2 |
| FR-DOC-001–003 | Document storage (PDF/A, XBRL) | 3 | 1 |
| FR-NLP-001–014 | Multilingual NLP + intent classification | 4 | 2 |
| FR-ADV-001–006 | Advisory engine + hallucination mitigation | 4 | 2 |
| FR-COM-001–009 | Compliance engine (VAT, SSNIT) | 5 | 1 |
| FR-TAX-001–008 | Tax calculation engine | 5 | 1 |
| FR-DPC-007–009 | Audit trail and tamper-evident logging | 5 | 1 |
| FR-MOB-001–008 | Mobile app (React Native) | 6 | 1 |
| FR-WEB-001–004 | PWA (Next.js) | 6 | 1 |
| FR-OFF-001–004 | Offline storage (SQLite WAL) | 6 | 1 |
| FR-USSD-001–005 | USSD gateway | 6 | 1 |
| **FR-USSD-006 [v1.2]** | **Africa's Talking fallback + health-check sidecar** | **6** | **1** |
| **FR-OTA-001 [v1.2]** | **Expo EAS Update OTA pipeline configuration** | **6** | **1** |
| NFR-PERF-001 | API p95 < 500ms @ 200 concurrent users | 6 (load test) | 1 |
| NFR-PERF-006 | PWA 2G performance < 8s | 6 (Lighthouse) | 1 |
| NFR-REL-003/004 | Transaction RTO ≤15min / RPO 0 | 2 (design) / 6 (DR test) | 1 |
| NFR-SCA-001 | HPA scale-out within 3 minutes | 0 (config) / 6 (test) | 1 |
| NFR-OBS-004–005 | NLP resolution rate + bias drift monitoring | 4 | 2 |

---

*This document is the authoritative, consolidated reference for BizPulse AI. It supersedes all prior standalone roadmap documents.*

*It is a living specification. Update CLAUDE.md and the Current Sprint Context at the start of every sprint. Update the SESSION_LOG.md after every AI agent session. Update the Gate checklists as requirements evolve. Update DECISIONS.md after every significant architectural decision.*

*Based on: BizPulse AI Technical Specification v1.2 & Requirements Breakdown — March 2026*
*Consolidated from: BizPulse AI Claude Code Strategic Roadmap + BizPulse AI Strategic Implementation Roadmap*
*Updated from v1.1: four board-level architecture additions — USSD/SMS fallback (Africa's Talking), DPIA hard-commit schedule, OTA update policy (Expo EAS Update), outbound API rate limit management (Asynq)*
*Further refined: AI TDD (tests-first) workflow (§3.3, §3.4, §5.1.1); CLAUDE.md token budget discipline (§3.1, Appendix A); AI tooling orientation for junior developers (§3.6)*
