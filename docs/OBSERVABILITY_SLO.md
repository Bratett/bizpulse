# OBSERVABILITY_SLO.md

## 1. Purpose

This document defines the observability baseline, Service Level Indicators (SLIs), Service Level Objectives (SLOs), alerting rules, dashboard requirements, escalation paths, and evidence expectations for BizPulse AI.

Its purpose is to make BizPulse measurable, supportable, and gate-ready from Sprint 0 onward. Observability is not a post-MVP enhancement. It is a deployment prerequisite and a Gate 1 requirement.

This document should be used by:
- SRE / Platform Engineering
- Backend and ML Engineering
- Product and QA
- Security and Compliance
- On-call operations
- Engineering leadership during phase-gate reviews

---

## 2. Scope

This specification covers observability for:
- API Gateway (Kong HA)
- User Service
- Transaction Engine
- Compliance Service
- Analytics Service
- NLP Service
- Notification Service
- Mobile App / React Native client
- PWA / Next.js client
- USSD gateway and Africa’s Talking fallback path
- WhatsApp delivery channel
- PostgreSQL / TimescaleDB / pgvector
- Redis
- Kafka / Flink
- InfluxDB
- MLflow-tracked model services
- Asynq outbound worker queues
- Kubernetes platform and CI/CD deployment telemetry

---

## 3. Principles

1. **Instrument at first deployment**  
   No service may be deployed without baseline logging, metrics, and traces.

2. **Measure user-critical journeys, not only infrastructure**  
   Balance lookup, transaction sync, filing submission, forecast generation, and NLP query resolution are first-class observability subjects.

3. **Separate business telemetry from infrastructure telemetry**  
   Infrastructure/system telemetry goes to InfluxDB. Business and application tracing/metrics go to Datadog. Model lifecycle and experiment metrics go to MLflow.

4. **Design for low-connectivity reality**  
   Offline sync health, USSD continuity, fallback activation, and delayed provider recovery are required observability domains.

5. **Tie alerts to ownership**  
   Every high-severity alert must name a responsible team and escalation path.

6. **Use error budgets to drive release discipline**  
   SLO breaches must influence rollout, change approval, and operational prioritization.

7. **Retain evidence for gate reviews and audits**  
   Dashboards, alert histories, error-budget reports, and incident logs are formal evidence artefacts.

---

## 4. Tooling Baseline

### 4.1 Required Platforms

| Domain | Primary Tool | Purpose |
|---|---|---|
| Distributed tracing / APM | Datadog APM | HTTP, DB, Kafka, queue, external dependency tracing |
| Application metrics | Datadog | Service KPIs, latency, error rate, custom metrics |
| Infrastructure telemetry | InfluxDB | API latency, Kafka throughput, pod metrics, DB performance, system error rates |
| Model registry & model metrics | MLflow | Model versioning, evaluation metrics, drift and bias tracking inputs |
| Alert routing | PagerDuty | On-call paging and incident escalation |
| Logs | Centralized structured logging pipeline | JSON logs from all services and gateways |
| Deployment telemetry | Datadog + ArgoCD events | Rollout monitoring, regression detection, rollback signals |

### 4.2 Store Routing Rules

- **InfluxDB** is reserved for infrastructure telemetry such as API latency, Kafka throughput, Kubernetes pod metrics, database query performance, and error-rate time series.
- **Datadog** is the primary operational surface for APM, service dashboards, application KPIs, and alerting.
- **MLflow** stores model-run metadata, evaluation results, and experiment history.
- **PostgreSQL** is not to be used as a substitute observability sink for high-cardinality telemetry.
- **Redis** is never the source of truth for observability history.

---

## 5. Telemetry Standards

## 5.1 Logs

All services must emit structured JSON logs with:
- timestamp (ISO 8601 UTC)
- service_name
- environment
- version / git_sha
- trace_id
- span_id (where applicable)
- request_id / correlation_id
- tenant_id / business_id where applicable
- user_id where legally and operationally justified
- severity
- event_type
- message
- outcome / status
- latency_ms when relevant

### 5.1.1 Sensitive Data Rules

Logs must never expose unmasked PII, secrets, full payment instrument details, raw authentication tokens, or plaintext regulated documents.

### 5.1.2 Mandatory Domain Logs

**Every NLP query must log:**
- intent
- language_detected
- model_used
- response_time_ms
- resolution_status
- escalation_flag

**Every compliance filing must log:**
- filing_type
- submission_status
- receipt_id (if available)
- provider
- error_code(s)
- retry_count

**Every transaction flow must log:**
- service
- idempotency_key
- source_provider
- processing_time_ms
- final_status

**Every fallback or degraded-path event must log:**
- fallback_type
- original_dependency
- trigger_condition
- duration
- final_outcome

## 5.2 Metrics

Metrics must be tagged at minimum by:
- environment
- service
- region
- channel (mobile, web, ussd, whatsapp, api)
- provider (where applicable)
- outcome

Cardinality must be controlled. User-level tags are prohibited unless explicitly approved for a narrowly-scoped operational use case.

## 5.3 Traces

Required trace coverage:
- incoming HTTP requests
- service-to-service calls
- PostgreSQL queries
- Kafka producer/consumer spans
- Asynq task enqueue and execution spans
- external provider calls
- long-running model inference chains
- offline sync batch processing spans

---

## 6. Service Level Indicators (SLIs)

BizPulse adopts the following SLI categories:

1. **Availability SLIs** — whether a service is reachable and returns valid responses
2. **Latency SLIs** — whether responses arrive within target time windows
3. **Correctness / success SLIs** — whether key operations complete successfully
4. **Durability / recovery SLIs** — whether data-critical services preserve integrity and meet RTO/RPO expectations
5. **Queue and backlog SLIs** — whether async work is draining within acceptable windows
6. **Model quality operation SLIs** — whether AI services resolve requests and remain within drift/bias thresholds
7. **Channel continuity SLIs** — whether low-connectivity paths remain available

---

## 7. Platform-Wide SLOs

| SLI | SLO | Measurement Window | Notes |
|---|---|---|---|
| Overall platform uptime | 99.9% | Monthly / trailing 30 days | Business-level availability target |
| API uptime | >=99.5% | Trailing 90 days | Gate 3 criterion |
| Production expired TLS certs | 0 | Continuous | Mandatory KPI |
| Deployment downtime | 0 planned downtime | Per deployment | Rolling update requirement |
| Scale-out reaction after threshold breach | <=3 minutes | Per scaling event | HPA target |

### 7.1 Error Budget Policy

For the 99.9% platform uptime SLO, the monthly error budget is approximately 43.8 minutes.

For the 99.5% API uptime SLO, the trailing-90-day error budget is approximately 10.8 hours.

### 7.2 Error Budget Actions

| Condition | Required Action |
|---|---|
| >=50% of monthly error budget consumed | Freeze non-essential production changes for affected service until reviewed |
| >=75% consumed | Require SRE + engineering lead approval for all deployments touching affected service |
| 100% consumed | Reliability recovery sprint required; feature releases paused for affected service except emergency fixes |

---

## 8. Service-Specific SLOs

## 8.1 API Gateway (Kong HA)

| SLI | SLO | Notes |
|---|---|---|
| Gateway availability | 99.95% monthly | 3-instance HA minimum |
| Auth validation success (excluding invalid user tokens) | >=99.9% | Failures investigated for gateway/IdP issues |
| p95 gateway added latency | <100 ms | Excludes backend service processing time |
| 5xx rate | <0.5% | Measured per 5-minute window and daily rollup |

**Critical alerts:**
- any gateway instance unhealthy in cluster
- cluster quorum risk
- spike in 401/403 caused by upstream auth misconfiguration
- p95 added latency breach for 15 minutes

## 8.2 User Service

| SLI | SLO |
|---|---|
| Availability | 99.9% monthly |
| p95 authenticated request latency | <500 ms |
| Auth/profile mutation success | >=99.5% |
| OTP delivery orchestration success | >=99% |

## 8.3 Transaction Engine

| SLI | SLO |
|---|---|
| Availability | 99.95% monthly |
| p95 API latency under Gate 1 baseline load | <500 ms |
| Mobile money transaction sync latency | <2 minutes |
| Duplicate transaction write rate | 0 accepted duplicates |
| RTO | <=15 minutes |
| RPO | 0 minutes |

**Notes:**
- This is a tier-1 service.
- Any threat to append-only integrity is sev-1.

## 8.4 Compliance Service

| SLI | SLO |
|---|---|
| Availability | 99.9% monthly |
| GRA submission success rate | >=95% |
| Filing generation success | >=99% for internally generated filings |
| p95 filing job enqueue latency | <250 ms |
| p95 filing status lookup latency | <500 ms |

## 8.5 Analytics Service

| SLI | SLO |
|---|---|
| Availability | 99.5% monthly |
| Scheduled forecast job success | >=98% |
| Forecast API p95 latency (cached/simple reads) | <1 second |
| Batch feature pipeline completion within schedule window | >=99% |

## 8.6 NLP Service

| SLI | SLO | Source/Reason |
|---|---|---|
| Simple query response time | <500 ms | Haiku path target |
| Complex advisory query response time | <3-5 seconds | Sonnet path target |
| Voice query end-to-end response start | <3 seconds simple / <7 seconds complex | Voice SLA |
| Resolution rate without human escalation | >=70% | Gate 2 criterion |
| Hallucination validation pass rate on numeric outputs | >=99% | Internal operational safeguard |

### 8.6.1 NLP Degraded-Mode SLOs

| SLI | SLO |
|---|---|
| Structured-query fallback success during LLM degradation | >=95% |
| Cache fallback availability | >=99% |
| Escalation queue creation success | >=99.5% |

## 8.7 Notification Service

| SLI | SLO |
|---|---|
| Availability | 99.9% monthly |
| Transactional message enqueue success | >=99.9% |
| Provider callback normalization success | >=99.5% |
| Delivery status update freshness | <=5 minutes lag |

## 8.8 USSD / Low-Connectivity Continuity

| SLI | SLO |
|---|---|
| USSD structured critical query success | >=99% |
| USSD session completion for supported core flows | >=95% |
| Fallback activation correctness when primary telco path fails | 100% |
| Africa’s Talking fallback path availability | >=99.5% |

## 8.9 Offline Sync

| SLI | SLO |
|---|---|
| Sync success rate after reconnect | >=99% |
| Conflict classification correctness | >=99.5% |
| Partial-batch rollback correctness | 100% |
| Checksum reconciliation completion before merge | 100% |

---

## 9. Queue, Streaming, and Async Work SLOs

## 9.1 Asynq Worker Queues

| SLI | SLO |
|---|---|
| Task enqueue success | >=99.9% |
| Retry handling correctness | 100% policy compliance |
| DLQ rate | <0.1% of total tasks daily, excluding provider incidents |
| Critical-queue backlog age (GRA) | <5 minutes sustained |
| Default-queue backlog age | <15 minutes sustained |
| Low-priority backlog age | <60 minutes sustained |

### 9.1.1 Mandatory Asynq Alerts

- any GRA task entering DLQ
- repeated provider 429/503 spikes beyond retry tolerance
- queue saturation / worker starvation
- Redis queue health degradation
- backlog age breach by queue tier

## 9.2 Kafka / Flink

| SLI | SLO |
|---|---|
| Producer success rate | >=99.9% |
| Consumer lag within normal operation | <60 seconds for critical topics |
| Stream job restart recovery | <=10 minutes |
| Schema validation success | 100% |

---

## 10. Database and Storage SLOs

## 10.1 PostgreSQL / TimescaleDB / pgvector

| SLI | SLO |
|---|---|
| Primary DB availability | 99.95% monthly |
| p95 query latency for tier-1 transactional paths | <100 ms |
| Replication health | no sustained lag threatening RPO |
| Backup restore validation | 100% successful on scheduled test restores |

## 10.2 Redis

| SLI | SLO |
|---|---|
| Cache availability | 99.9% monthly |
| Eviction anomaly rate | 0 unmanaged critical anomalies |
| Rate-limit counter correctness | >=99.99% |

## 10.3 InfluxDB

| SLI | SLO |
|---|---|
| Telemetry write success | >=99.5% |
| Query availability for dashboards | >=99% |
| Metric freshness | <=2 minutes ingestion lag |

---

## 11. ML and AI Monitoring

## 11.1 MLflow and Model Ops Metrics

Every deployed model must report to MLflow:
- model version
- training date
- validation metrics
- deployment environment
- feature importances or explainability artefacts where applicable
- fairness evaluation results where applicable

## 11.2 Model Operational SLIs

| SLI | SLO |
|---|---|
| Model inference success rate | >=99% |
| Model version traceability | 100% |
| Bias drift monitoring coverage on flagged models | 100% |
| Experiment registration compliance | 100% |

## 11.3 Drift and Bias Alerts

Applicable especially to credit scoring, pricing, and recommendation models.

Alerts required for:
- statistically significant drift in key features
- degradation in validation/performance against recent labeled outcomes
- disparity threshold breach across monitored cohorts
- missing model metadata or unregistered production model version

---

## 12. Client and Channel Observability

## 12.1 Mobile App

Track:
- crash-free sessions
- sync retry counts
- offline storage budget usage
- biometric auth failures
- certificate pinning errors
- OTA rollout adoption and rollback triggers

### Mobile SLOs

| SLI | SLO |
|---|---|
| Crash-free sessions | >=99.5% |
| Successful startup on supported devices | >=99% |
| Certificate pinning misconfiguration incidents | 0 |
| OTA staged rollout error rate | <1% before broad rollout expansion |

## 12.2 PWA

| SLI | SLO |
|---|---|
| Core dashboard load on 2G | <8 seconds |
| Offline shell availability | >=99% |
| Frontend JS error rate | <1% sessions |

## 12.3 WhatsApp Channel

| SLI | SLO |
|---|---|
| Webhook intake success | >=99.5% |
| Outbound notification template send success | >=98% |
| Message-state normalization success | >=99% |

---

## 13. Dashboards

The following dashboards are mandatory.

### 13.1 Executive Reliability Dashboard

Shows:
- platform uptime
- API uptime
- major incident count
- gate-critical KPI status
- top error budget consumers

### 13.2 Gateway & API Dashboard

Shows:
- request volume
- p50/p95/p99 latency
- 4xx/5xx rate
- auth failure trends
- tenant and channel breakdown

### 13.3 Transaction Integrity Dashboard

Shows:
- transaction ingest rate
- sync latency
- duplicate rejection count
- provider error spikes
- reconciliation status

### 13.4 Compliance Operations Dashboard

Shows:
- filings generated
- filings submitted
- GRA success rate
- retries, backlog, DLQ
- DPO-alerting events

### 13.5 NLP / AI Operations Dashboard

Shows:
- query volume by language and channel
- resolution rate
- latency by model path
- escalation rate
- fallback path usage
- hallucination validation failures
- bias drift indicators

### 13.6 Queue & Provider Dashboard

Shows:
- Asynq backlog by queue
- retry counts
- DLQ events
- provider latency and error distribution
- 429/503 patterns by provider

### 13.7 Low-Connectivity & Continuity Dashboard

Shows:
- offline sync success
- conflict counts by type
- USSD success rate
- Africa’s Talking fallback activations (`ussd.fallback.activated`)
- reconnect recovery latency

### 13.8 Infrastructure Dashboard

Shows:
- pod health
- HPA activity
- DB CPU / memory / IOPS
- Kafka throughput
- consumer lag
- InfluxDB write success

### 13.9 Deployment & Release Dashboard

Shows:
- deployment frequency
- success/failure
- rollout percentage
- OTA metrics
- rollback triggers
- post-deploy error-rate and latency deltas

---

## 14. Alerting and Escalation

## 14.1 Severity Model

| Severity | Description | Response Expectation |
|---|---|---|
| Sev-1 | Revenue, transaction integrity, security, or compliance-critical outage | Immediate page; incident commander assigned |
| Sev-2 | Major degraded capability with active user impact | Immediate page during business-critical hours / rapid escalation |
| Sev-3 | Moderate issue requiring same-day action | Ticket + Slack/ops notification |
| Sev-4 | Informational / trend warning | Dashboard review or backlog item |

## 14.2 Page-Worthy Conditions

A PagerDuty alert is mandatory for:
- platform availability breach conditions
- gateway cluster failure risk
- transaction engine integrity threat
- RPO/RTO threat
- GRA task DLQ entry
- repeated payment provider outage patterns
- sustained NLP degradation affecting critical flows
- failure of USSD fallback activation
- certificate expiry / pinning emergency
- post-deploy error rate >1%

## 14.3 Special Routing Rules

- **Every Asynq DLQ event** must emit an InfluxDB metric and trigger PagerDuty.
- **Every GRA DLQ event** must additionally alert the DPO.
- **Every Africa’s Talking fallback activation** must emit the custom metric `ussd.fallback.activated`.
- **Every OTA deployment** must log channel, rollout percentage, and error rate for staged rollout monitoring.

## 14.4 Baseline Thresholds

| Alert | Threshold |
|---|---|
| API error rate spike | >1% |
| p95 API latency under baseline test | >500 ms sustained |
| NLP resolution rate drop | <70% over rolling evaluation window |
| GRA submission success | <95% |
| USSD success drop | <99% critical query success |
| Queue backlog age breach | per tier SLO breach |
| Dashboard metric freshness lag | >2 minutes for critical telemetry |

---

## 15. Runbooks and Operational Response

Every sev-1 / sev-2 alert class must have a linked runbook covering:
- detection signal(s)
- immediate containment steps
- dependency checks
- rollback / failover steps
- escalation contacts
- evidence capture steps
- user/compliance communication triggers
- closure checklist

Mandatory runbooks include:
- gateway degradation
- Keycloak / auth outage
- transaction reconciliation incident
- GRA submission outage
- provider 429/503 storm
- Kafka consumer lag spike
- offline sync corruption suspicion
- USSD primary-path outage with fallback verification
- certificate pinning incident
- OTA rollback

---

## 16. Gate Evidence Requirements

## 16.1 Gate 1 Evidence

Required evidence:
- instrumentation present for every deployed service
- dashboard links for core services
- load-test report showing API p95 <500 ms at 200 concurrent users
- alert rules configured and test-fired
- post-deploy monitoring workflow active
- zero critical security findings / observability available to support verification

## 16.2 Gate 2 Evidence

Required evidence:
- NLP resolution rate >=70% without escalation
- GRA submission success >=95%
- multilingual observability broken down by language/channel
- queue and fallback metrics operational in production or pilot scale

## 16.3 Gate 3 Evidence

Required evidence:
- API uptime >=99.5% trailing 90 days
- scaling telemetry proving safe growth to target load bands
- HA gateway evidence
- incident and error-budget reporting history

---

## 17. Ownership Model

| Domain | Primary Owner | Supporting Owners |
|---|---|---|
| Gateway / ingress | Platform / SRE | Security, Backend |
| Core service telemetry | Service team | SRE |
| Transaction and reconciliation signals | Transaction team | Finance ops, SRE |
| Compliance and GRA submissions | Compliance team | DPO, SRE |
| NLP and model monitoring | ML / NLP team | Product, SRE |
| Mobile / PWA telemetry | Frontend / Mobile team | Product |
| USSD / fallback telemetry | Channel integrations team | Platform |
| Queue / provider health | Platform + owning service team | SRE |
| Gate evidence compilation | Product + Engineering leadership | All owners |

---

## 18. Implementation Checklist

### Sprint 0 minimum
- Datadog APM enabled for all initial services
- HTTP tracing enabled
- DB tracing enabled
- Kafka tracing scaffolded where applicable
- InfluxDB write clients operational
- structured JSON logging enforced
- PagerDuty integration configured
- first dashboards created

### Before each service reaches staging
- service dashboard exists
- alerts exist
- trace coverage verified
- correlation IDs verified end-to-end
- error-budget policy applied
- runbook linked

### Before production rollout
- SLOs approved by engineering lead
- page-worthy alerts test-fired
- dashboard reviewed with owner
- post-deploy monitoring checklist attached to release

---

## 19. ADR Triggers

An ADR must be created or updated if any of the following changes:
- primary observability platform changes
- telemetry routing between Datadog / InfluxDB / MLflow changes
- alert severity model changes
- gateway SLO targets change materially
- queue or provider criticality model changes
- model-drift governance thresholds change
- mobile or OTA monitoring design changes materially

---

## 20. Open Items

The following items should be finalized during implementation planning:
- exact PagerDuty schedule and escalation roster
- exact retention windows for logs, traces, and metrics by environment
- exact numeric drift thresholds per model family
- exact dashboard URLs once infrastructure is provisioned
- exact SLO windows for some Phase 3/4 services not yet launched

---

## 21. Summary

`OBSERVABILITY_SLO.md` is the operational contract that defines how BizPulse proves reliability in production.

It translates architecture and non-functional requirements into measurable targets, dashboards, alerts, and response expectations. Without it, the system can be deployed but not responsibly operated, audited, or gate-approved.
