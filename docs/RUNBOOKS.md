# BizPulse AI — RUNBOOKS.md

## Purpose

This document is the operational runbook reference for BizPulse AI. It defines the standard operating procedures for incident detection, triage, containment, recovery, communication, evidence capture, and post-incident follow-up across critical platform scenarios.

Use this file together with:
- `ARCHITECTURE.md`
- `OBSERVABILITY_SLO.md`
- `SECURITY_BASELINE.md`
- `INTEGRATION_MANIFEST.md`
- `COMPLIANCE_MATRIX.md`
- `OFFLINE_SYNC_SPEC.md`
- `DECISIONS.md`

This file is not a policy narrative. It is an execution guide for operators, on-call engineers, incident leads, compliance owners, and service teams.

---

## Operational Principles

1. **Protect financial integrity first.** Append-only financial records must not be overwritten or silently repaired.
2. **Prefer graceful degradation over hard outage.** Offline mode, queued retries, and fallback channels are first-class recovery paths.
3. **Never bypass queueing controls for upstream providers.** Calls to GRA, MTN MoMo, Vodafone Cash, bank feeds, and Anthropic must remain routed through Asynq.
4. **Preserve evidence.** Every major incident must leave behind logs, metrics, timelines, and actions sufficient for audit and root-cause analysis.
5. **Escalate compliance-relevant failures early.** GRA DLQ events, filing failures, and PII exposure events require compliance-aware escalation.
6. **Use runbooks, not improvisation.** Deviations must be explicitly recorded in the incident timeline.

---

## Roles and Incident Command

### Core Roles

- **On-call Engineer:** First responder for alerts; validates signal; starts incident record.
- **Incident Commander (IC):** Owns coordination, priorities, timeline, and decision log.
- **Service Owner:** Leads diagnosis and remediation for affected service.
- **SRE Lead / Platform Engineer:** Leads infra, networking, Kubernetes, gateway, and failover actions.
- **Compliance Officer / DPO:** Engaged for GRA filing incidents, audit-trace issues, and privacy incidents.
- **Customer Success Lead:** Coordinates external user communications.
- **CTO / Exec Escalation:** Engaged for P1 incidents, DR declarations, or regulatory-risk events.

### Severity Model

- **P1 — Critical:** Revenue-impacting outage, financial integrity risk, regional outage, GRA filing pipeline failure near deadline, confirmed security breach.
- **P2 — High:** Material degradation of core flows, elevated queue failures, provider outage with partial fallback available.
- **P3 — Medium:** Localized degradation, non-critical feature outage, elevated latency without core transaction failure.
- **P4 — Low:** Minor issue, cosmetic monitoring drift, documentation or tooling issue without production impact.

### Escalation Expectations

- P1: Immediate paging; IC assigned immediately; executive visibility required.
- P2: Page responsible team and SRE; IC required if user-visible >15 minutes.
- P3: Ticket plus owner acknowledgement; no war room unless trend worsens.
- P4: Backlog unless tied to a gate criterion or audit requirement.

---

## Standard Incident Workflow

### 1. Detect

Signals may originate from:
- Datadog APM alerts
- InfluxDB-backed infrastructure metrics
- PagerDuty pages
- DLQ alarms from Asynq tasks
- CloudWatch regional health alarms
- Synthetic checks / smoke tests
- User reports or support escalations

### 2. Triage

Within the first 5 minutes:
- Confirm whether the alert is real, duplicate, or noisy.
- Identify affected services, channels, regions, and user segments.
- Classify severity.
- Open or update incident record.
- Assign Incident Commander for P1/P2.

### 3. Stabilize

Choose the fastest safe action that reduces user harm:
- trigger fallback provider path
- reduce concurrency
- pause outbound queue consumers
- disable failing integration route
- shift traffic to standby
- force read-only mode for affected admin workflows
- preserve append-only transaction integrity

### 4. Recover

- Restore minimum viable service.
- Validate via smoke tests and dashboards.
- Confirm backlog drain or sync recovery.
- Resume paused workflows in controlled order.

### 5. Communicate

- Update internal stakeholders on current impact, ETA-free status, and next action.
- Update users when degradation is material or exceeds defined thresholds.
- Preserve all communications in the incident timeline.

### 6. Close and Review

Before closure:
- confirm service recovery
- collect root-cause evidence
- identify data repair needs
- log actions taken
- create follow-up tasks and ADRs if architecture changes are needed

---

## Standard Evidence Checklist

Capture for every P1/P2 incident and any compliance/security event:
- incident start and detection timestamps
- alert source and trace IDs
- impacted services, regions, channels, and providers
- exact error messages and sample payloads with PII removed/masked
- Datadog traces and dashboards used
- InfluxDB metrics / queue depth / DLQ counts
- Kubernetes events / pod restarts / deploy diff
- gateway logs and auth failures if relevant
- user impact estimate
- mitigation actions and timestamps
- compliance/regulatory exposure assessment
- final root cause (or current best hypothesis)

---

## Communications Templates

### Internal Status Update

```
Incident: [title]
Severity: [P1/P2/P3]
Start time: [timestamp]
Current status: [investigating / mitigated / recovering / resolved]
Impact: [who/what is affected]
Scope: [services/channels/regions/providers]
Current action: [what team is doing now]
Next update: [time or event-based checkpoint]
Owner: [IC name]
```

### User-Facing Degradation Notice

```
We are currently experiencing a service disruption affecting [service/channel].
Some users may see [symptom]. Our team is actively working to restore normal operation.
Where possible, the system is continuing through fallback or queued processing.
We will share another update once the issue is mitigated.
```

### Regulator/Compliance Internal Escalation Note

```
Compliance-impacting incident detected.
Affected process: [GRA filing / tax computation / audit log / PII / payroll submission]
Potential exposure: [missed submission / delayed filing / traceability gap / privacy risk]
Current containment: [action]
Evidence preserved: [yes/no]
Compliance owner engaged: [name]
```

---

## Runbook 1 — Regional Outage / Disaster Recovery Failover

### Trigger Conditions

Initiate this runbook when:
- CloudWatch reports primary region health degradation.
- Datadog shows sustained critical API failure/latency consistent with region failure.
- Primary region unavailability exceeds 10 minutes.

### Objective

Restore P1 services in DR standby with RTO/RPO obligations respected.

### Key Targets

- DR declaration threshold: 10 minutes of primary region unavailability.
- Route 53 automated shift for P1 services: within 15 minutes.
- Switchback only after 30-minute primary stability window.

### Immediate Actions (0–10 Minutes)

1. Confirm whether issue is AZ-local, service-local, or full-region.
2. Page SRE lead and assign IC.
3. Freeze non-essential deploys.
4. Confirm current health of:
   - Kong gateway cluster
   - PostgreSQL primary and replicas
   - Kafka brokers and consumer lag
   - Redis
   - compliance-svc and transaction-svc
5. If recoverable in-region within 10 minutes, pursue local recovery.
6. If not, escalate to DR declaration.

### DR Declaration (Minute 10)

1. IC informs CTO, compliance officer, and customer success lead.
2. Declare P1 regional incident.
3. Open incident command channel and shared timeline.

### Automated / Manual Failover Steps

1. Confirm Route 53 health checks have shifted P1 service DNS toward DR standby.
2. Promote PostgreSQL read replica in `eu-west-1` to primary when declaration is confirmed.
3. Update application configuration via ArgoCD.
4. Scale warm standby instances to production capacity.
5. Verify Kafka consumer groups in DR are healthy.
6. Rehydrate Redis from source-of-truth stores as needed.
7. Confirm Kong and Keycloak dependencies in DR path are healthy.

### Validation Checklist

- Smoke test transaction flow end-to-end.
- Validate one compliance computation on test dataset.
- Confirm NLP service health endpoint.
- Confirm queue processing and DLQ alarms are operational.
- Confirm user authentication works.

### User Communication

If degradation exceeds 30 minutes:
- update status page
- send WhatsApp/SMS notice to active users where configured

### Switchback Procedure

1. Verify restored primary stability for 30 continuous minutes.
2. Confirm replication integrity back to primary.
3. Repoint Route 53 health checks to primary.
4. Revert ArgoCD configuration.
5. Monitor elevated metrics for 2 hours.
6. Record any data reconciliation actions.

### Required Artefacts

- DR declaration timestamp
- failover timeline
- smoke test evidence
- switchback approval record
- post-incident review
- annual drill/tabletop references if relevant

---

## Runbook 2 — GRA Submission Failures / Filing Backlog

### Trigger Conditions

Use this runbook when:
- GRA submission success rate drops below SLO.
- Asynq tasks to GRA begin retry storming.
- GRA tasks enter DLQ.
- A statutory filing window is at risk.

### Objective

Prevent silent compliance failure, preserve auditability, and restore filing throughput safely.

### Immediate Actions

1. Confirm whether issue is schema validation, auth, upstream outage, rate limiting, or network instability.
2. Check Asynq queue depth for GRA tasks.
3. Check DLQ size and time-to-deadline for pending filings.
4. Notify compliance owner immediately.
5. If any GRA task hits DLQ, alert DPO in addition to PagerDuty.

### Containment

- Pause new non-urgent filing submissions if they worsen backlog.
- Preserve all pending payloads and audit records.
- Prevent duplicate resubmissions by confirming idempotency handling.
- If issue is schema-related, halt further sends until validation patch exists.

### Diagnosis Paths

**Schema errors**
- Validate generated XML against GRA schema.
- Compare latest code/deploy changes in compliance-svc.
- Confirm tax rates are sourced from `compliance_rates` only.

**Auth / credential issues**
- Verify secrets validity and token exchange.
- Check credential rotation logs.

**Rate limiting / upstream instability**
- Confirm backoff and per-provider concurrency settings.
- Inspect requeue behavior and retry jitter.

**Internal queue/worker issues**
- Check worker concurrency, Redis health, poison messages, and DLQ growth.

### Recovery

1. Fix root issue.
2. Re-run schema validation or auth checks on sample payload.
3. Replay queued tasks in controlled batches.
4. Monitor receipt creation and success metrics.
5. Reconcile all pending filings against audit log and user-facing status.

### User / Internal Communication

- Inform customer success if deadline-sensitive users are affected.
- Inform compliance officer of expected filing delay risk.
- Preserve a list of impacted filings and periods.

### Required Artefacts

- count of impacted filings
- filing periods/business IDs affected
- receipt IDs for successful replay
- DLQ evidence
- DPO alert evidence if triggered

---

## Runbook 3 — Asynq DLQ Growth / Upstream Rate-Limit Cascade

### Trigger Conditions

- DLQ rate exceeds threshold.
- Queue depth grows faster than workers drain it.
- Multiple upstream providers begin returning 429/503.
- Provider rate-limit cascade threatens transaction or compliance pipelines.

### Objective

Stop cascading failure and restore controlled outbound processing.

### Immediate Actions

1. Identify affected provider(s): GRA, MoMo, Vodafone, bank feed, Anthropic.
2. Confirm whether spike is provider-specific or shared infrastructure.
3. Review concurrency limits and retry profile.
4. Check Redis health and worker saturation.
5. Freeze deploys touching queue workers.

### Containment Options

- Reduce worker concurrency per provider.
- Pause low-priority queues.
- Preserve critical queues (GRA first, then money movement).
- Route non-urgent NLP jobs to lower-cost/fallback mode if Anthropic throttling is involved.
- Increase backlog visibility with temporary dashboards if needed.

### Recovery Steps

1. Tune concurrency to provider-safe levels.
2. Allow retry queues to drain gradually.
3. Replay DLQ items in bounded batches after cause is addressed.
4. Confirm DLQ metric trend returns below target.
5. Validate no duplicate financial side effects occurred.

### Special Notes

- Never bypass Asynq with direct synchronous calls.
- GRA DLQ remains compliance-sensitive and requires DPO awareness.
- Monitor for secondary impact on user-facing status screens.

---

## Runbook 4 — Mobile Money Provider Outage / Transaction Sync Gap

### Trigger Conditions

- MTN MoMo or Vodafone Cash webhook failure spike.
- Transaction ingestion gap detected.
- Provider timeout or auth failure causing sync backlog.

### Objective

Maintain financial integrity and restore provider synchronization without duplicate postings.

### Immediate Actions

1. Determine provider(s) affected.
2. Compare inbound webhook volume vs historical baseline.
3. Confirm status of outbound reconciliation tasks.
4. Inspect transaction-svc idempotency key handling.
5. Notify finance/compliance stakeholders if settlement visibility is impacted.

### Containment

- Keep accepting local/user-side entries where safe.
- Mark provider-linked transaction sync as delayed, not failed, unless explicitly exhausted.
- Prevent duplicate ledger entries.
- If one provider is down, preserve operation for other providers.

### Recovery

1. Restore provider connectivity or credentials.
2. Reprocess missed webhooks or statement pulls from checkpoint.
3. Reconcile provider transaction IDs against internal append-only records.
4. Confirm balances, cashbook views, and downstream analytics consistency.

### Validation Checklist

- no duplicate transaction records
- reconciled gap window documented
- user-facing sync status corrected
- audit trail preserved

---

## Runbook 5 — USSD Failure / Africa’s Talking Fallback Activation

### Trigger Conditions

- Direct telco USSD path fails.
- USSD availability alert fires.
- Failover activation metric missing during known outage.

### Objective

Preserve low-connectivity continuity by shifting to fallback path and confirming availability reporting.

### Immediate Actions

1. Confirm whether issue is telco-side, gateway-side, or session-routing failure.
2. Validate if automatic failover to Africa’s Talking activated.
3. Check metric `ussd.fallback.activated` and related logs.
4. Confirm session continuity and menu rendering for critical journeys.

### Containment

- Keep core USSD menu tree restricted to essential flows if capacity is reduced.
- Disable non-critical menus if needed to maintain responsiveness.
- Inform customer success of channel degradation.

### Recovery

1. Confirm Africa’s Talking fallback is functioning end-to-end.
2. Validate session creation, menu traversal, and response latency.
3. When primary path returns, switch traffic back in controlled manner.
4. Confirm fallback events were captured in observability systems.

### Validation Checklist

- essential USSD flows functional
- fallback events logged
- no silent failover misses
- user communication sent if impact is material

---

## Runbook 6 — Offline Sync Failure / Conflict Storm

### Trigger Conditions

- sync success rate falls below target
- checksum reconciliation failures spike
- conflict prompts surge abnormally
- replay batches rollback repeatedly

### Objective

Protect local user data, restore sync safely, and avoid merge corruption.

### Immediate Actions

1. Identify whether issue is client release-specific, server-side, or network/provider related.
2. Check sync queue backlog and failure reasons.
3. Review affected data types: inventory, settings, tax input, transactions.
4. Confirm whether failures are isolated to a release/channel/tenant segment.

### Containment

- Stop unsafe replay if merge corruption is suspected.
- Preserve device-local queues.
- Maintain read-only access to already-synced data where possible.
- Disable offending sync endpoint version if rollout-specific.

### Recovery

1. Fix endpoint or conflict-resolution bug.
2. Validate checksum reconciliation on test cohort.
3. Re-enable sync in canary batches.
4. Monitor duplicate rejection, conflict prompts, and merge success.
5. Communicate any user actions needed for manual resolution.

### Data-Type Rules Reminder

- financial transactions: append-only, no overwrite
- business settings/profile: last-write-wins
- inventory counts: manual resolution prompt
- tax inputs: server-side merge with audit trail
- NLP conversation history: device-local only

---

## Runbook 7 — Kong / Keycloak Authentication Failure

### Trigger Conditions

- widespread 401/403 spikes
- token validation failures at gateway
- login failure surge
- admin MFA flow unavailable

### Objective

Restore secure access without weakening authentication guarantees.

### Immediate Actions

1. Determine whether issue is Kong, Keycloak, JWT validation, clock skew, or secret/cert rotation.
2. Check if failure affects all tenants or specific clients.
3. Confirm Kong HA node health.
4. Confirm Keycloak realm and signing key state.

### Containment

- Do not disable JWT validation globally.
- If issue is limited to one ingress path, reroute through healthy path.
- If cert/key rotation caused breakage, revert to last known good secret set where valid.

### Recovery

1. Restore token issuance/validation chain.
2. Validate user login, refresh, and admin MFA flow.
3. Check audit logging continuity.
4. Confirm no unauthorized bypass occurred during mitigation.

---

## Runbook 8 — PII Exposure / Security Incident

### Trigger Conditions

- confirmed or suspected PII leakage
- unauthorized access to tenant data
- exposed secret/key
- anomalous audit log or access pattern

### Objective

Contain exposure quickly, preserve evidence, assess legal/regulatory impact, and execute recovery under security leadership.

### Immediate Actions (First 15 Minutes)

1. Assign security incident commander.
2. Preserve logs and forensic evidence.
3. Revoke exposed keys/tokens if applicable.
4. Isolate affected service, host, queue, or tenant path.
5. Notify DPO/compliance officer immediately.
6. Freeze non-essential changes.

### Containment

- Rotate credentials.
- Block suspicious sessions.
- Disable affected integration or endpoint if necessary.
- Increase logging and monitoring on affected scope.

### Assessment

- What data categories were exposed?
- Which tenants/users were affected?
- Was data only viewed, or also altered/exfiltrated?
- Are financial or filing artefacts impacted?
- Are breach-notification obligations triggered?

### Recovery

1. Patch exploited weakness.
2. Validate access controls and encryption paths.
3. Restore only after clean-state verification.
4. Prepare internal breach summary and evidence pack.

### Required Artefacts

- timeline of access
- affected records/classes of data
- secrets rotated
- containment actions
- regulator/customer notification decision record

---

## Runbook 9 — Data Integrity Incident (Ledger / Audit / Tax Computation)

### Trigger Conditions

- append-only ledger invariant violated
- tax output mismatch vs expected rules
- audit log gap detected
- pesewa precision issue suspected

### Objective

Protect trust in financial and compliance outputs before restoring normal processing.

### Immediate Actions

1. Stop any workflow that may continue producing corrupted results.
2. Identify whether issue is computation logic, rate source, migration, or serialization.
3. Check whether tax/VAT rate came exclusively from `compliance_rates`.
4. Check whether any monetary values were handled as float instead of BIGINT pesewas.
5. Notify compliance owner and service owner.

### Containment

- disable affected calculation path or filing generation route
- preserve faulty outputs for audit, but do not continue issuing them
- prevent destructive repair on financial rows

### Recovery

1. Patch root issue.
2. Recompute on controlled dataset.
3. Compare corrected outputs with prior issued outputs.
4. Determine whether user-visible correction or regulator-facing remediation is required.
5. Record corrective action in audit trail and incident review.

---

## Runbook 10 — Bad Deployment / Release Rollback

### Trigger Conditions

- error rate or latency regression immediately after deployment
- sync failures, auth issues, or queue anomalies correlated to a release
- OTA rollout metrics exceed error threshold

### Objective

Return to last known good state quickly while preserving evidence of the bad release.

### Immediate Actions

1. Confirm correlation between deploy and symptom.
2. Freeze further deploys.
3. Identify whether issue is backend, mobile OTA, web, schema, or infra.
4. Assign rollback owner.

### Rollback Paths

**Backend / infra**
- revert via ArgoCD / GitOps to last known good commit
- verify config drift and migrations

**Mobile OTA**
- halt rollout channel
- roll back to prior stable update
- monitor staged rollout metrics and crash/error rate

**Web / gateway**
- revert ingress/config release
- validate cache invalidation and auth path

### Validation

- p95 latency returns within target
- error rate normalizes
- key smoke tests pass
- no data migration damage remains unresolved

---

## Runbook 11 — Observability Blind Spot / Missing Telemetry

### Trigger Conditions

- service outage with inadequate traces/metrics
- required logging fields missing
- DLQ event occurred without alert
- fallback activated without metric emission

### Objective

Restore measurement coverage and avoid operating blind.

### Immediate Actions

1. Determine missing signal type: logs, traces, metrics, alerts, dashboards.
2. Check recent deploys to instrumentation code.
3. Validate Datadog, InfluxDB, MLflow, and PagerDuty integrations.
4. Create temporary manual dashboards/queries if needed.

### Recovery

1. Restore instrumentation.
2. Backfill incident evidence where possible.
3. Add regression tests or CI checks for telemetry contract.
4. Record as follow-up in `TEST_STRATEGY.md` / `DECISIONS.md` if architecture change is needed.

---

## Operational Checklists

### Incident Open Checklist

- [ ] Severity assigned
- [ ] IC assigned
- [ ] Owner(s) paged
- [ ] Timeline started
- [ ] User impact identified
- [ ] Evidence capture started
- [ ] Compliance/security owner added if applicable

### Incident Resolve Checklist

- [ ] Service restored
- [ ] Smoke tests passed
- [ ] Backlogs drained or explicitly scheduled
- [ ] User/status communications updated
- [ ] Root cause captured or bounded
- [ ] Follow-up issues created
- [ ] Postmortem scheduled for P1/P2

### Postmortem Minimum Fields

- Incident summary
- Root cause
- Trigger and detection path
- Impact window and affected users
- What worked well
- What failed
- Corrective actions
- Preventive actions
- ADR/documentation updates required

---

## Drill and Readiness Cadence

- **Regional failover drill:** annually in Q4
- **DR tabletop exercise:** bi-annually
- **Queue/DLQ game day:** quarterly
- **Security incident tabletop:** quarterly
- **Offline sync conflict simulation:** each major client release train
- **USSD fallback validation:** before pilot and after major telco/fallback changes

Record all drills in `SESSION_LOG.md` and attach resulting changes to:
- `OBSERVABILITY_SLO.md`
- `SECURITY_BASELINE.md`
- `INTEGRATION_MANIFEST.md`
- `DECISIONS.md`

---

## Open Items / ADR Triggers

Create or update an ADR when any of the following occurs:
- failover procedure changes materially
- queue retry or DLQ policy changes materially
- user communication obligations change
- fallback provider strategy changes
- auth/gateway recovery model changes
- breach response workflow changes due to legal review

