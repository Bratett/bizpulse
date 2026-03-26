# ML_MODEL_REGISTRY.md

## 1. Purpose

This document is the canonical registry and governance reference for all machine learning, AI inference, and model-adjacent decision systems used by BizPulse AI.

It exists to ensure that every model or model-like decision component is:
- explicitly named and versioned
- tied to a business capability and owning service
- trained, evaluated, promoted, and rolled back through a controlled process
- monitored for quality, drift, latency, and fairness in production
- aligned with BizPulse's regulatory, security, and data residency constraints

This document complements, but does not replace:
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/API_CONTRACT.md`
- `docs/COMPLIANCE_MATRIX.md`
- `docs/OBSERVABILITY_SLO.md`
- MLflow experiment and model registry records
- code-level model cards and evaluation artefacts in the repository

---

## 2. Scope

The registry covers five categories of modelled or AI-driven behaviour:

1. **Predictive models**
   - cash flow forecasting
   - demand prediction
   - credit risk scoring
   - supplier risk assessment

2. **Language and voice systems**
   - query routing
   - intent classification
   - multilingual NLP assistance
   - speech-to-text
   - code-switching detection

3. **Retrieval and document intelligence**
   - embeddings and vector retrieval
   - OCR/document parsing
   - invoice, receipt, and contract extraction

4. **Rules-plus-model hybrid systems**
   - tax advisory support
   - compliance recommendation support
   - structured fallback classification

5. **External model dependencies**
   - Anthropic Claude models
   - Whisper-based transcription stack
   - any future third-party hosted or self-hosted models

---

## 3. Governing Principles

### 3.1 Spec-Locked Principles

The following principles are binding unless replaced by a formal ADR:

- **MLflow is the system of record** for experiment tracking, evaluation artefacts, and model lineage.
- **BentoML is the preferred serving layer** for packaged Python-based model inference workloads.
- **Claude model versions are pinned** and may only change through formal release review.
- **pgvector is the default production vector store** unless a DPIA later approves an alternative cross-border option.
- **Phase 1 must avoid premature ML optimization.** Simpler, explainable, faster-to-ship approaches are preferred where they satisfy MVP requirements.
- **Fairness evaluation for credit-related models is mandatory and not delegatable to the AI coding agent.**
- **Local language quality validation requires native-speaker human review** before production claims are made for Twi, Ga, Ewe, Hausa, or Dagbani.

### 3.2 Architecture Principles

- Prefer deterministic and auditable approaches for compliance- and finance-adjacent flows.
- Separate training concerns from online inference concerns.
- Treat feature definitions as versioned contracts, not informal code assumptions.
- Prefer models that are robust in low-data environments for early phases.
- Maintain rollback-safe serving paths for every production model.
- Preserve reproducibility: dataset version, feature schema version, code commit SHA, model artefact hash, and environment manifest must be recorded together.

### 3.3 Data Protection Principles

- Do not move embedding, document, or query-derived data outside approved residency boundaries without DPIA approval.
- Minimize personal data in training corpora where the task does not require it.
- Use anonymization or pseudonymization for analytics and model-training workloads where possible.
- Restrict production data access for model training to approved roles and audited pipelines.

---

## 4. Registry Record Format

Every model or model-like component must have a record with the following minimum fields.

| Field | Description |
|---|---|
| Registry ID | Stable internal identifier, e.g. `ML-CF-001` |
| Model Name | Human-readable name |
| Capability Domain | Forecasting, scoring, NLP, ASR, retrieval, parsing, etc. |
| Business Function | What user or service outcome this enables |
| Owner | Team or accountable lead |
| Serving Service | Analytics Service, NLP Service, Compliance Service, etc. |
| Model Type | Rule-based, statistical, classical ML, deep learning, LLM, embedding model |
| Current Stage | Draft, Experimental, Staging, Production, Deprecated, Retired |
| Phase Availability | Planned phase or currently active phase |
| Inputs / Feature Schema Version | Versioned contract for inputs |
| Training Data Source | Approved source datasets |
| Evaluation Suite | Metrics and scenario tests required |
| Fairness / Safety Requirements | Bias checks, human review, exclusion rules |
| Runtime Target | Latency and throughput expectations |
| Fallback Path | Degraded-mode or substitute behaviour |
| Rollback Strategy | Previous stable version, switch method |
| Monitoring | Drift, latency, error, and quality signals |
| Compliance Notes | DPIA, audit, consent, explainability, legal notes |

---

## 5. Model Lifecycle and Stages

### 5.1 Stages

| Stage | Meaning | Allowed Use |
|---|---|---|
| Draft | Conceptual entry only | No code generation against it without review |
| Experimental | In research or offline evaluation | Offline testing only |
| Staging | Candidate validated in pre-production | Limited shadow or internal use |
| Production | Approved for user-facing or service-critical use | Live traffic allowed |
| Deprecated | Still callable but being phased out | Migration only |
| Retired | No further use allowed | Historical record only |

### 5.2 Promotion Rules

A model may advance only when all of the following exist:

- versioned feature schema
- reproducible training pipeline or documented vendor dependency
- evaluation report against approved metrics
- observability instrumentation
- rollback plan
- security and data-handling review
- fairness review where applicable
- sign-off by the accountable owner and technical lead

Additional requirements by category:

- **Credit scoring:** fairness review, adverse-impact testing, explanation plan, human override path
- **Multilingual NLP:** native-speaker validation for each language level claimed
- **RAG / embeddings:** residency and DPIA alignment; prompt-injection and retrieval safety tests
- **Speech models:** word error rate testing plus noisy-environment testing

### 5.3 Retirement Rules

A model must be retired when any of the following occurs:

- a pinned external version is no longer supported
- a successor model becomes the approved default
- fairness or security concerns cannot be remediated within risk tolerance
- the feature or channel it serves is removed from scope
- a data residency or legal ruling makes continued use non-compliant

---

## 6. Production Registry

### 6.1 Forecasting Models

| Registry ID | Model Name | Domain | Default Approach | Owner | Service | Phase | Stage |
|---|---|---|---|---|---|---|---|
| `ML-CF-001` | Cash Flow Forecasting | Forecasting | **Prophet in Phase 1**; LSTM only after later approval | Analytics Lead | Analytics Service | Phase 1+ | Planned Production |
| `ML-DP-001` | Demand Prediction | Forecasting | Statistical / time-series baseline first; richer ML later | Analytics Lead | Analytics Service | Phase 2+ | Experimental |
| `ML-SR-001` | Supplier Risk Assessment | Risk scoring | Hybrid feature-based scoring baseline first | Analytics Lead | Analytics Service | Phase 2+ | Draft |

#### `ML-CF-001` — Cash Flow Forecasting

**Business purpose**
- Predict inflows and outflows over 30/60/90-day horizons.
- Support working capital recommendations and proactive alerts.

**Why this approach**
- Phase 1 explicitly prefers Prophet over LSTM because it is simpler, faster to deploy, and sufficient for MVP forecasting needs.

**Inputs / features (initial schema)**
- business ID
- dated income and expense aggregates
- payment rail mix (cash, bank, mobile money)
- seasonality indicators
- market-day / festival calendar features
- sector tag
- region tag
- optional subscription / recurring expense markers

**Training data sources**
- normalized transaction ledger aggregates
- reconciled mobile money and bank sync data
- business profile metadata
- curated Ghana-specific seasonality calendar

**Evaluation**
- MAPE / sMAPE by forecast horizon
- MAE and WAPE by business segment
- backtesting over rolling windows
- error breakdown by sector and region

**Fallback path**
- seasonal naive forecast
- rule-based trend extrapolation for businesses with insufficient history

**Upgrade note**
- Any move from Prophet to LSTM or another neural architecture requires a formal ADR, benchmark evidence, serving-cost review, and rollback validation.

---

### 6.2 Credit and Risk Models

| Registry ID | Model Name | Domain | Default Approach | Owner | Service | Phase | Stage |
|---|---|---|---|---|---|---|---|
| `ML-CR-001` | Alternative Credit Risk Score | Credit scoring | Feature-based supervised model with explainability requirements | ML Lead + Risk Lead | Analytics Service | Phase 2+ | Draft |
| `ML-FR-001` | Fairness Monitoring Layer | Model assurance | Post-score fairness and disparity monitoring | ML Lead + Compliance | Analytics Service | Phase 2+ | Draft |

#### `ML-CR-001` — Alternative Credit Risk Score

**Business purpose**
- Estimate creditworthiness for SMEs lacking formal financial histories.
- Use alternative signals relevant to Ghanaian SMEs.

**Approved signal families**
- mobile money transaction history
- utility payment regularity
- business cash flow stability indicators
- sector behavior features
- regional features where legally and ethically acceptable
- social commerce or transaction continuity indicators where lawfully sourced

**Prohibited shortcuts**
- direct use of protected demographic attributes in scoring logic
- unreviewed proxy variables with strong discrimination risk
- opaque production deployment without explanation outputs

**Fairness requirements**
- demographic parity analysis
- disparate impact testing using the 80% rule
- intersectional fairness evaluation
- ongoing bias drift monitoring
- human review of fairness outputs before production approval

**Human-governed controls**
- appeals path with target 5-day resolution SLA
- human-in-the-loop escalation for flagged decisions
- Algorithmic Impact Assessment before deployment affecting credit, pricing, or access decisions

**Evaluation**
- AUC / PR-AUC
- calibration error
- false positive / false negative balance
- stability by sector, region, and business formality tier
- fairness metrics on approved audit cohorts

**Explainability requirement**
- Produce reason codes or interpretable factor summaries suitable for user-visible explanation and internal review.

**Promotion constraint**
- This model cannot be promoted to Production without fairness sign-off from authorized human reviewers.

---

### 6.3 NLP and LLM-Driven Systems

| Registry ID | Model Name | Domain | Default Approach | Owner | Service | Phase | Stage |
|---|---|---|---|---|---|---|---|
| `ML-NLP-001` | Intent Classification MVP | Query routing | **Rule-based** in Phase 1 | NLP Lead | NLP Service | Phase 1 | Planned Production |
| `ML-NLP-002` | Intent Classification ML Upgrade | Query routing | ML-based classifier after corpus threshold is met | NLP Lead | NLP Service | Phase 2+ | Draft |
| `ML-NLP-003` | Claude Complex Query Path | LLM inference | `claude-sonnet-4-6` pinned | NLP Lead | NLP Service | Phase 1+ | Planned Production |
| `ML-NLP-004` | Claude Simple Query Path | LLM inference | `claude-haiku-4-5-20251001` pinned | NLP Lead | NLP Service | Phase 1+ | Planned Production |
| `ML-NLP-005` | Code-Switching Detector | Language routing | Lightweight classifier / rules hybrid | NLP Lead | NLP Service | Phase 2+ | Experimental |
| `ML-NLP-006` | Multilingual Advisory Assistant | Generative advisory | LLM + tool use + retrieval | NLP Lead | NLP Service | Phase 2+ | Experimental |

#### `ML-NLP-001` — Intent Classification MVP

**Why this approach**
- Phase 1 explicitly avoids premature ML optimization and requires rule-based intent classification for the NLP MVP.

**Purpose**
- Route user requests into simple lookup, advice, tax, document analysis, or human escalation paths.

**Promotion rule**
- Keep this as default until the training corpus threshold for the ML upgrade is met and validated.

#### `ML-NLP-002` — Intent Classification ML Upgrade

**Activation prerequisite**
- The ML upgrade is not the default path until the approved training corpus threshold is reached and reviewed.

**Evaluation**
- intent precision/recall/F1
- confusion matrix by language and code-switched traffic
- fallback rate
- escalation rate
- resolution rate without human assistance

#### `ML-NLP-003` and `ML-NLP-004` — Pinned Claude Paths

**Pinned versions**
- Complex path: `claude-sonnet-4-6`
- Simple path: `claude-haiku-4-5-20251001`

**Use routing**
- simple structured queries route to Haiku path
- complex financial, tax, advisory, and document tasks route to Sonnet path

**Change control**
- vendor model version changes require formal release review
- prompt, tool-routing, and output guard changes require regression testing

**Fallback chain**
1. pinned Claude primary path
2. cached response for high-confidence repeated intent
3. local fine-tuned or lightweight structured-query classifier where available
4. USSD/SMS structured fallback for critical queries with human escalation flag

**Safety requirements**
- no direct execution of unsupported financial or legal advice beyond defined product policy
- require traceable tool usage for factual business data responses
- log model path, prompt template version, tool usage, and response outcome metadata

---

### 6.4 Speech and Voice Models

| Registry ID | Model Name | Domain | Default Approach | Owner | Service | Phase | Stage |
|---|---|---|---|---|---|---|---|
| `ML-ASR-001` | English Speech-to-Text MVP | ASR | **Off-the-shelf Whisper** | NLP Lead | NLP Service | Phase 1 | Planned Production |
| `ML-ASR-002` | Twi Voice Upgrade | ASR | Fine-tuned language support after real data collection | NLP Lead | NLP Service | Phase 2+ | Draft |
| `ML-ASR-003` | Ga/Ewe Voice Beta | ASR | Beta quality with staged validation | NLP Lead | NLP Service | Phase 2+ | Draft |

#### `ML-ASR-001` — English Speech-to-Text MVP

**Why this approach**
- Phase 1 explicitly prefers off-the-shelf Whisper for English STT.

**Evaluation**
- word error rate
- entity capture accuracy for dates, currency, and business terms
- noisy-environment performance
- latency under mobile/network constraints

#### `ML-ASR-002` — Twi Voice Upgrade

**Constraint**
- Twi fine-tuning is deferred to a later phase when real user data exists and native-speaker validation can be organized.

**Promotion prerequisites**
- approved corpus sourcing
- linguistic QA
- privacy review of audio retention and transcription storage

---

### 6.5 Retrieval, Embeddings, and Document Intelligence

| Registry ID | Model Name | Domain | Default Approach | Owner | Service | Phase | Stage |
|---|---|---|---|---|---|---|---|
| `ML-RAG-001` | Compliance / Knowledge Retrieval | Retrieval | Embeddings + pgvector + LangChain | NLP Lead + Compliance Lead | NLP Service / Compliance Service | Phase 1+ | Planned Production |
| `ML-DOC-001` | Document Parsing and Summarization | Document AI | OCR + parser + LLM summarization | NLP Lead | NLP Service | Phase 1+ | Planned Production |
| `ML-EMB-001` | Embedding Model Baseline | Embeddings | Residency-safe embedding stack recorded in MLflow | NLP Lead | NLP Service | Phase 1+ | Draft |

#### `ML-RAG-001` — Compliance / Knowledge Retrieval

**Purpose**
- retrieve tax, compliance, and business-knowledge context for grounded answers

**Vector-store rule**
- production default is pgvector
- any non-resident managed vector database remains blocked unless DPIA clearance is obtained within the binding decision schedule

**Evaluation**
- retrieval precision@k / recall@k on curated evaluation sets
- answer groundedness checks
- citation coverage for regulated-answer paths
- prompt-injection resistance tests
- latency and freshness checks

**Safety**
- retrieval corpora must be source-governed and versioned
- regulated-answer flows should separate quoted regulation sources from inferred guidance

#### `ML-DOC-001` — Document Parsing and Summarization

**Use cases**
- invoice summarization
- receipt extraction
- contract parsing with local business terminology
- business document understanding

**Evaluation**
- field extraction precision/recall
- document type classification accuracy
- summary faithfulness and omission checks
- multilingual terminology robustness where applicable

---

## 7. Feature Schemas and Dataset Governance

### 7.1 Feature Schema Versioning

Every production model must reference a feature schema version in the format:

`FS-<domain>-<major>.<minor>`

Examples:
- `FS-CASHFLOW-1.0`
- `FS-CREDIT-1.0`
- `FS-INTENT-1.0`

A feature schema change is:
- **major** when it adds/removes fields or changes semantics
- **minor** when it adds non-breaking metadata or transformations

### 7.2 Dataset Requirements

Each model version must record:
- dataset name
- dataset version
- extraction window
- consent / lawful basis classification where relevant
- anonymization or pseudonymization status
- label generation methodology
- class balance notes where applicable
- excluded populations or segments

### 7.3 Training Data Restrictions

- Do not train on raw production exports without approval and audit trail.
- Do not mix sandbox, synthetic, and production-labelled data without recording proportions and rationale.
- Do not reuse document or voice corpora across unrelated tasks without confirming lawful basis and retention compatibility.

---

## 8. Evaluation Standards

### 8.1 Minimum Evaluation Pack

Every candidate promotion must attach:
- offline evaluation report
- scenario / edge-case suite
- latency benchmark
- failure-mode summary
- rollback plan
- model card or equivalent summary

### 8.2 Category-Specific Metrics

| Category | Required Metrics |
|---|---|
| Forecasting | MAPE/sMAPE, MAE, WAPE, segment stability |
| Binary scoring | AUC, PR-AUC, calibration, threshold analysis |
| Multi-class NLP | Precision, Recall, F1, confusion matrix |
| Speech | WER, term capture accuracy, latency |
| Retrieval | Precision@k, Recall@k, groundedness, citation coverage |
| Document extraction | Field precision/recall, doc-type accuracy, faithfulness |

### 8.3 Production Readiness Tests

- cold-start latency
- concurrency under expected load
- failure on missing or malformed features
- stale-cache or stale-index behaviour
- graceful degradation when upstream LLM or provider is unavailable
- observability signal emission to Datadog / MLflow / metrics pipelines

---

## 9. Fairness, Ethics, and Human Oversight

### 9.1 Mandatory Fairness Controls

For credit, risk, pricing, or access-affecting models:
- demographic parity analysis
- disparate impact testing (80% rule)
- intersectional fairness evaluation
- monitored bias drift
- documented remediation plan

### 9.2 Governance Controls

- AI Ethics Board review for high-impact model categories
- Algorithmic Impact Assessment before deployment affecting credit, pricing, or access decisions
- anonymous whistleblower path for bias concerns
- quarterly fairness audit cadence for production high-impact models

### 9.3 User Transparency

Where applicable, models must support:
- user-accessible rationale summaries
- explainable recommendation outputs
- escalation to human review when a decision is challenged

---

## 10. Serving, Routing, and Runtime Controls

### 10.1 Serving Standards

- Python-served ML inference packages should be packaged through BentoML where appropriate.
- All experiments, artefacts, and lineage must be registered in MLflow.
- Every production endpoint must expose version metadata and health status.
- Every model-serving deployment must have a previous stable version available for rollback.

### 10.2 Runtime Metadata to Log

At minimum, log:
- registry ID
- model version
- feature schema version
- inference timestamp
- tenant-safe business segment metadata
- latency
- confidence or score band where applicable
- fallback path used
- error class if failed

### 10.3 Fallback Rules

Every production model must define one of the following:
- simpler previous model version
- deterministic rules engine
- cached response
- manual-review route
- channel fallback (for critical queries, including USSD/SMS where defined)

---

## 11. Monitoring, Drift, and Alerting

### 11.1 Monitoring Dimensions

Every Production model must emit signals for:
- request rate
- latency
- timeout/error rate
- output distribution drift
- input feature drift
- fallback rate
- business quality proxy metric

### 11.2 Drift Policy

| Drift Type | Example | Required Action |
|---|---|---|
| Feature drift | mobile money mix shifts materially | investigate within agreed SLO window |
| Label drift | repayment outcomes change after policy change | retraining review |
| Outcome disparity drift | one segment degrades disproportionately | fairness escalation |
| Retrieval drift | relevant documents no longer retrieved | re-index / evaluation refresh |

### 11.3 Alert Triggers

At minimum, page or escalate when:
- latency breaches model SLO for sustained period
- error or fallback rate exceeds approved threshold
- bias drift exceeds approved threshold on high-impact model
- retrieval groundedness or citation coverage falls below safe threshold for regulated-answer paths

---

## 12. Release, Rollback, and Change Control

### 12.1 Release Package

Every production release must include:
- model version ID
- model artefact reference
- feature schema version
- evaluation summary
- fairness summary where applicable
- serving image version
- migration or index update notes if relevant
- rollback command or procedure

### 12.2 Rollback Rules

Rollback must be possible without retraining. For each model, store:
- prior stable artefact
- prior feature schema compatibility note
- index compatibility note for embedding changes
- kill switch or traffic-routing method

### 12.3 Vendor Model Version Changes

For pinned external models:
- do not silently update vendor model IDs
- run regression pack before changing pinned identifiers
- record prompt-template version and tool-routing version alongside vendor model change

---

## 13. Ownership Matrix

| Domain | Primary Owner | Secondary Owner |
|---|---|---|
| Forecasting | Analytics Lead | Product Manager |
| Credit scoring | ML Lead / Risk Lead | Compliance Officer |
| NLP assistant | NLP Lead | Product Manager |
| Speech models | NLP Lead | QA Lead |
| Retrieval / RAG | NLP Lead | Compliance Lead |
| Model registry governance | Technical Lead | ML Lead |
| Fairness governance | Compliance Officer | ML Lead |

---

## 14. Phase-Aligned Delivery Plan

### Phase 1 Minimum Registry Scope

The following must be concretely defined before or during Phase 1 implementation:
- `ML-CF-001` Cash Flow Forecasting (Prophet baseline)
- `ML-NLP-001` Intent Classification MVP (rule-based)
- `ML-NLP-003` Claude complex-query path
- `ML-NLP-004` Claude simple-query path
- `ML-ASR-001` English STT MVP (Whisper)
- `ML-RAG-001` compliance/knowledge retrieval on pgvector
- `ML-DOC-001` document parsing and summarization baseline

### Phase 2 Expansion Candidates

- `ML-NLP-002` ML-based intent classifier
- `ML-ASR-002` Twi voice fine-tuning
- `ML-CR-001` alternative credit scoring
- `ML-DP-001` demand prediction
- `ML-FR-001` fairness monitoring layer

### Phase 3+ Expansion Candidates

- advanced supplier risk modelling
- multilingual voice maturity beyond beta
- wider sector-specific calibration packs
- more advanced ensemble forecasting where justified by data and ROI

---

## 15. Open ADR Items

The following items require explicit ADRs before implementation or promotion:

1. Exact production embedding model selection and hosting pattern.
2. Whether any LSTM or transformer-based forecaster is justified after Phase 1 Prophet baseline.
3. Credit-score model class selection and explanation method.
4. Threshold for moving intent classification from rule-based to ML-based path.
5. Audio retention and redaction policy for voice training datasets.
6. Fairness dashboard ownership and review cadence implementation details.
7. Whether document extraction uses one unified parser stack or task-specific pipelines.
8. Any Pinecone adoption after DPIA outcome, including migration/dual-write strategy if ever approved.

---

## 16. Definition of Done for This Registry

`docs/ML_MODEL_REGISTRY.md` is considered usable when:
- every active AI/ML capability has a registry entry
- each entry names an owner, service, stage, and fallback path
- Phase 1 defaults are locked and do not conflict with implementation constraints
- fairness controls are explicit for credit-related use cases
- serving, evaluation, monitoring, and rollback requirements are unambiguous
- all later model changes are expected to update this file and the relevant ADRs

