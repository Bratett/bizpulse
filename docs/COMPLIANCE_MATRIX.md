# COMPLIANCE_MATRIX.md

# BizPulse AI — Compliance Matrix

**Document Type:** Regulatory Control Mapping  
**Status:** Canonical implementation reference  
**Owner:** Compliance Officer + Lead Architect + Engineering Leads  
**Update Trigger:** At each phase gate, upon new regulator guidance, partner onboarding, or any material architecture change

---

## 1. Purpose

This document maps BizPulse AI’s regulatory, policy, and control obligations to the services, modules, operational procedures, and evidence artefacts responsible for satisfying them.

It is intended to answer six implementation questions clearly:

1. **What obligation exists?**
2. **Which regulator / framework imposes it?**
3. **Which service or team owns implementation?**
4. **What concrete control satisfies it?**
5. **What evidence proves compliance?**
6. **In which phase / gate must it be complete?**

This file is a delivery tool, not a legal opinion. All statutory interpretation must be validated by qualified Ghanaian legal and compliance personnel before production launch or any regulated feature expansion.

---

## 2. How to Use This Matrix

- Treat this document as the delivery-facing compliance control register.
- Use it together with:
  - `ARCHITECTURE.md`
  - `DATA_MODEL.md`
  - `API_CONTRACT.md`
  - `SECURITY_BASELINE.md`
  - `INTEGRATION_MANIFEST.md`
  - `DECISIONS.md`
- Every control below should map to one or more:
  - backlog items
  - test cases
  - audit artefacts
  - runbooks
  - monitoring alerts
  - sign-off checkpoints
- Where a regulator API, filing format, or licensing process is still pending external confirmation, the matrix marks the item as **Partner / Regulator dependent**.

---

## 3. Regulatory Scope Summary

BizPulse AI operates across a multi-agency compliance surface. The core implementation set includes:

- **Data Protection Commission (DPC)** — Act 843 privacy, registration, processing safeguards, auditability
- **Ghana Revenue Authority (GRA)** — tax computation, VAT returns, PAYE workflows, filing readiness, tax rate accuracy
- **SSNIT** — payroll contribution workflows and filing/export readiness
- **Bank of Ghana (BoG)** — licensing assessment and financial-services perimeter controls for payments / money movement related functions
- **National Communications Authority (NCA)** — USSD short code and channel licensing obligations
- **Accounting / reporting frameworks** — IFRS for SMEs, Ghana Companies Act / GACC / ICAG-aligned reporting outputs
- **Security and assurance obligations** — penetration testing, audit logging, retention, incident response, encryption, access control
- **AI governance obligations** — fairness, explainability, hallucination containment, language-risk controls, human escalation

---

## 4. Control Status Legend

| Status | Meaning |
|---|---|
| Required at Gate 1 | Must be complete before MVP transition to Phase 2 |
| Required by Gate 2 | Needed before public launch |
| Required by Gate 3 | Needed for national scale |
| Required by Gate 4/5 | Expansion / ecosystem / regional readiness |
| External dependency | Cannot be completed without regulator, partner, or legal confirmation |
| ADR required | Must be captured in `DECISIONS.md` before implementation proceeds |

---

## 5. Compliance Ownership Model

| Domain | Primary Owner | Secondary Owners |
|---|---|---|
| Privacy / Act 843 | Compliance Service + DPO / Compliance Officer | User Service, Security, Data Engineering |
| Tax / GRA | Compliance Service | Transaction Engine, Analytics Service, Finance Ops |
| Payroll / SSNIT | Compliance Service | User Service, Reporting Layer |
| Financial records integrity | Transaction Engine | Data Engineering, Compliance Service |
| Security controls | Platform / Security Engineering | All service owners |
| Channel licensing | Product Ops / Legal | Notification Service, USSD Gateway team |
| AI governance | NLP Service + Analytics Service | Compliance Officer, Product, QA |
| Audit evidence | Platform Engineering + Compliance Officer | All teams |

---

## 6. Master Compliance Matrix

| ID | Obligation Area | Regulator / Framework | Requirement | System / Team Owner | Implementation Control | Evidence Artefacts | Phase / Gate | Notes |
|---|---|---|---|---|---|---|---|---|
| CM-001 | Data controller registration | DPC / Act 843 | BizPulse must complete required data protection registration before operating in-scope processing | Compliance Officer | Registration workflow initiated Week 1; track status in launch checklist | DPC registration confirmation, compliance sign-off | **Gate 1** | Launch blocker |
| CM-002 | Lawful processing basis | DPC / Act 843 | Each personal-data workflow must have documented lawful basis and purpose | Compliance Service + Product | Data inventory + purpose mapping + privacy notices | RoPA, privacy notice, lawful basis register | Gate 1 | Must cover app, web, WhatsApp, USSD |
| CM-003 | Data minimization | DPC / Act 843 | Collect only fields required for service delivery, reporting, or legal retention | User Service + Product | Schema review, DTO validation, form design constraints | Data dictionary, API schema review, field approval log | Gate 1 | Applies to onboarding and sync |
| CM-004 | Consent capture where required | DPC / Act 843 | Consent-dependent processing must be explicit, versioned, and revocable | User Service | Consent ledger with timestamp, channel, policy version | Consent records, revocation logs, UX screenshots | Gate 1 | Especially marketing, optional data sharing |
| CM-005 | Data subject rights handling | DPC / Act 843 | Access, correction, deletion / restriction requests must be operationally supported where legally permitted | User Service + Compliance Service | DSAR workflow, ticketing state machine, legal exception handling | SOP, request logs, response SLAs, test cases | Gate 2 | Financial retention may limit deletion |
| CM-006 | Retention & deletion policy | DPC / Act 843 + tax / audit obligations | Retain data per legal need; dispose when allowed; hold when litigation/audit applies | Compliance Service + Data Engineering | Retention matrix, scheduled purge/archive jobs, legal hold flags | Retention policy, job logs, audit trail | Gate 1 | Needs table-by-table mapping |
| CM-007 | Encryption at rest | Security baseline | Sensitive data must be encrypted at rest | Platform / Security | AES-256 at rest across data stores; field-level encryption for PII | Infra config, KMS setup, test evidence | Gate 1 | Mandatory baseline |
| CM-008 | Encryption in transit | Security baseline | All in-transit communications must use TLS 1.3 where supported | Platform / Security | TLS 1.3, cert lifecycle automation, mTLS internally where adopted | TLS config, cert inventory, monitoring alerts | Gate 1 | Include cert rotation runbook |
| CM-009 | Field-level protection of PII | DPC / security | Sensitive personal fields require stronger protection than ordinary business metadata | User Service + Data Engineering | Field-level encryption / tokenization for high-risk fields | Schema annotations, key policies, tests | Gate 1 | ADR if tokenization pattern changes |
| CM-010 | Role-based access control | Security / privacy | Least-privilege access across admin and support roles | Keycloak + Kong + service owners | RBAC matrices, scoped claims, admin MFA, service authorization checks | RBAC table, test suite, access reviews | Gate 1 | Mandatory for all staff/admin roles |
| CM-011 | MFA for privileged access | Security baseline | Admin and privileged operators must use MFA | Identity / Platform | Enforce MFA in Keycloak admin/user groups | IdP policy export, test screenshots | Gate 1 | Launch blocker for admin console |
| CM-012 | Audit logging | DPC / security / financial controls | Sensitive actions must be tamper-evident and traceable | All services + Platform | Immutable audit trail, actor/action/object/result logging | Audit tables, retention config, alert rules | Gate 1 | Include config changes + data export |
| CM-013 | Incident detection & alerting | Security baseline | Security and service incidents must be detectable and routed | Platform / Security | SIEM integration, anomaly alerts, on-call runbooks | Alert config, incident drill records | Gate 2 | Core baseline in Phase 1 |
| CM-014 | Penetration testing | Security assurance | Quarterly penetration testing and annual security audits | Security / Leadership | External testing cadence and remediation tracking | Pentest report, remediation backlog, sign-offs | Gate 2 onward | Required operating discipline |
| CM-015 | Cross-border transfer decision | DPC / Act 843 | External vector / AI vendors affecting data residency require DPIA and adequacy review | Compliance Officer + Architecture | Default to pgvector; no Pinecone until DPIA conclusion | DPIA report, ADR, sign-off | **Gate 1** | Launch blocker for Pinecone use |
| CM-016 | Data residency | Privacy / architecture | Primary operational data resides in AWS af-south-1; DR replication only to approved region | Platform + Architecture | Region lock, backup / replication controls | Terraform, cloud config, DR diagrams | Gate 1 | Check vendor sub-processors too |
| CM-017 | Privacy by design in offline sync | DPC / Act 843 | Offline storage must not weaken privacy controls | Mobile / PWA teams + Sync layer | Encrypted local stores, scoped caches, device logout wipe | Mobile config, sync tests, logout tests | Gate 1 | Applies to SQLite / browser storage |
| CM-018 | Vendor / processor inventory | DPC / governance | Third-party processors must be documented with purpose and data categories | Compliance Officer + Platform | `INTEGRATION_MANIFEST.md`, vendor register, contract review | Vendor inventory, DPAs, risk ratings | Gate 1 | Update per integration |
| CM-019 | Tax rate accuracy | GRA / Finance Act | VAT/CST and other rates must be verified against current law before every release | Compliance Service + Compliance Officer | Config-table-driven rates; release sign-off checklist | Signed verification log, config history | Gate 1 and every release | No hardcoded rates |
| CM-020 | Config-driven tax engine | GRA / change control | Tax rules must change via controlled configuration, not code literals | Compliance Service | `compliance_rates` table + effective-dating + audit history | DB schema, admin audit log, tests | Gate 1 | PR rejection for hardcoded tax rates |
| CM-021 | VAT return readiness | GRA | System must generate VAT computations and filing-ready outputs | Compliance Service + Transaction Engine | VAT ledger derivation, return assembly, validation rules | Sample returns, test fixtures, reconciliation reports | Gate 1 | API submission depends on GRA access |
| CM-022 | PAYE computation readiness | GRA | Payroll tax calculations and employee tax outputs must be correct and reproducible | Compliance Service | PAYE calculation engine, bracket tables, payslip support | Test vectors, payroll exports, reconciliation logs | Gate 2 | Legal review needed |
| CM-023 | Withholding tax handling | GRA | Transaction-specific withholding logic must be configurable and traceable | Compliance Service + Transaction Engine | WHT rule config, withholding certificate generation | Config evidence, certificates, audit trail | Gate 2 | Sector rules may vary |
| CM-024 | Corporate income tax support | GRA | CIT estimates and annual computation workflows must be supported | Compliance Service + Analytics | Annual estimation module, adjustment workflow | Calculation reports, scenario tests | Gate 2 | Filing integration may lag |
| CM-025 | Filing evidence retention | GRA / audit | Submitted returns and source evidence must be retained in durable, exportable form | Compliance Service + Document store | PDF/A / XBRL where applicable, immutable filing records | Stored documents, hashes, export tests | Gate 1 | Critical for audit defense |
| CM-026 | GRA integration onboarding | GRA | Certified Tax Software registration / API onboarding must be initiated early | Compliance Officer + Partnerships | Week 1 dependency tracking, sandbox contract management | Application records, approval emails, manifest | External dependency / Gate 1 | Long lead-time item |
| CM-027 | SSNIT payroll contribution readiness | SSNIT | Payroll contribution calculations and submission-ready outputs must be supported | Compliance Service | SSNIT contribution rules, employer reports, export workflows | Sample files, calculation test cases | Gate 2 | Depends on SSNIT access |
| CM-028 | SSNIT integration onboarding | SSNIT | API / portal integration access must be pursued ahead of need | Compliance Officer + Partnerships | Partner dependency tracking, sandbox config | Approval records, credentials manifest | External dependency | Start Week 3 |
| CM-029 | Financial record immutability | Accounting / audit / fraud control | Transactions must be append-only, not destructive CRUD | Transaction Engine | Event-sourced ledger, reversal entries only, idempotency keys | Schema, migration history, tests, audit evidence | Gate 1 | Architectural non-negotiable |
| CM-030 | Reconciliation integrity | Accounting / audit | Statements, tax outputs, and analytics must reconcile back to source ledger | Transaction Engine + Analytics + Compliance | Reconciliation jobs, balance checks, exception queues | Daily recon reports, alert logs | Gate 1 | High materiality |
| CM-031 | Idempotent financial writes | Financial control | Retries must not create duplicate financial events | Transaction Engine + API Gateway | Idempotency keys, unique constraints, replay-safe consumers | API tests, load tests, duplicate suppression metrics | Gate 1 | Applies to sync and provider callbacks |
| CM-032 | Statement generation format compliance | IFRS for SMEs / GACC / ICAG | Financial statements must be exportable in accepted business reporting formats | Reporting / Compliance | Template library, note generation, controlled exports | Sample statements, reviewer sign-off | Gate 1 | Full ICAG polish may continue |
| CM-033 | Annual return / statutory records support | Companies Act 2019 (Act 992) | Company reporting outputs and registers must be supportable | Compliance Service | Annual return assembly, statutory register storage | Sample annual return packs, data extracts | Gate 2 | Legal review recommended |
| CM-034 | External auditor support | Accounting assurance | Platform must generate export-ready audit files / working papers | Reporting + Document service | Export bundle generation, source references | Audit file exports, sample workpapers | Gate 2 | Useful for accountant users |
| CM-035 | BoG perimeter assessment | Bank of Ghana | Product must document whether any workflows trigger licensing obligations | Legal / Compliance + Architecture | Licensing assessment memo, feature perimeter review | Legal memo, ADR, scope controls | Gate 1 | Start Week 2 |
| CM-036 | Payment partner controls | BoG / partner contracts | Money movement integrations must be contractually and technically bounded | Transaction Engine + Partnerships | Provider-specific scopes, reconciliation, callback verification | Partner contracts, callback tests, runbooks | Gate 1/Gate 2 | Depends on feature activation |
| CM-037 | MoMo / wallet agreement readiness | MTN / Vodafone / partners | Commercial API agreements must be in place before live transaction sync | Partnerships + Transaction Engine | Sandbox-to-production promotion checklist | Signed agreements, manifest, test evidence | External dependency / Gate 1 | Week 1 initiation |
| CM-038 | Callback authenticity | Financial/security | Provider callbacks must be authenticated and replay-protected | Transaction Engine + Notification Service | Signature verification, nonce / timestamp checks, dedupe | Callback tests, failed-auth logs | Gate 1 | Mandatory for financial events |
| CM-039 | USSD short code licensing | NCA | USSD number range / channel approvals must be secured for launch | Product Ops / Legal | Licensing tracker, launch dependency register | Approval letters, operator agreements | Gate 1 | Week 4 initiation |
| CM-040 | USSD/SMS fallback legality | NCA / channel operations | Aggregator fallback must preserve channel ownership and approved routing conditions | Notification / USSD team + Legal | Africa’s Talking fallback architecture with same short code governance | Architecture docs, partner contracts, runbooks | Gate 1 | Confirm no extra license required |
| CM-041 | Message delivery recordkeeping | NCA / customer communications | Notification delivery outcomes must be logged across providers | Notification Service | Normalized callback schema, status retention, DLQ monitoring | Delivery logs, dashboards, callback tests | Gate 1 | Covers SMS / WhatsApp where relevant |
| CM-042 | WhatsApp template compliance | Meta / platform policy | Approved message templates and opt-in handling must be enforced | Notification Service + Product Ops | Template registry, opt-in records, send policy checks | Template approvals, opt-in evidence | Gate 2 | Platform policy, not Ghana law |
| CM-043 | Access logging for support staff | Privacy / internal control | Support tooling must log data views and exports by internal staff | Admin tools + Platform | Admin access audit, export logging, justifications | Audit logs, support SOP | Gate 1 | Sensitive for DSAR and investigations |
| CM-044 | Backup and disaster recovery | Continuity / audit | Restore capability and recovery objectives must be provable | Platform | Backups, cross-region DR, restore drills, RTO/RPO monitoring | Backup reports, restore drill evidence | Gate 1 design / Gate 2 full proof | RTO ≤15 min, RPO 0 for transactions |
| CM-045 | Certificate lifecycle management | Security baseline | Certificate issuance, renewal, monitoring, and pin rotation must be managed | Platform / Security + Mobile | ACM / Let’s Encrypt automation, pin overlap policy, alerts | Cert inventory, alert config, OTA records | Gate 1 | Include mobile pin update process |
| CM-046 | API rate limiting & abuse control | Security / platform | Public APIs and auth surfaces must have rate limits and abuse protections | Kong + Platform | Gateway rate limits, WAF, throttling, anomaly rules | Kong config, load tests, alert logs | Gate 1 | Required for channel resilience |
| CM-047 | Outbound provider rate-limit handling | Partner / technical control | Calls to rate-limited upstream providers must be queued and retried safely | Asynq workers + service owners | Exponential backoff, concurrency limits, DLQ alerts | Queue config, worker metrics, runbooks | Gate 1 | Applies to GRA, MoMo, Claude, banks |
| CM-048 | AI output explainability | AI governance / consumer trust | High-impact advisory and scoring outputs must expose understandable rationale | Analytics + NLP + Product | Reason codes, model output metadata, confidence bands | UI evidence, model cards, test cases | Gate 2 | Especially credit / tax advice |
| CM-049 | Human escalation for risky advice | AI governance / compliance | High-risk or low-confidence outputs must trigger safe fallback or escalation | NLP Service + Compliance Service | Confidence thresholds, policy rules, human-review queues | Routing rules, escalation logs, QA tests | Gate 1 | Financial / legal advice boundary |
| CM-050 | Hallucination containment | AI governance / safety | Advice engines must avoid unsupported assertions and cite source basis where possible | NLP / Advisory | RAG on approved sources, refusal rules, answer templates | Prompt policies, evals, incident logs | Gate 1 | Important for compliance queries |
| CM-051 | Bias and fairness evaluation | AI governance / ethics | Credit and decision-support models must be tested for disparate impact and local bias | Analytics + Compliance Officer | Fairness test suite, demographic validation, release gate | Bias reports, sign-offs, retraining records | Gate 2 | Expanded rigor by Gate 3 |
| CM-052 | Local language validation | Consumer protection / AI quality | Twi/Ga/Ewe/Hausa/Dagbani outputs require native-speaker validation before production claims | NLP team + QA | Language test corpora, reviewer workflow, beta labelling | Linguistic QA reports, release notes | Gate 1 for English/Twi; later for others | Prevents misleading guidance |
| CM-053 | Beta feature disclosure | Product / trust | Beta-language and beta-voice features must be clearly labeled to users | Product + NLP | UI labels, release gating, fallback behavior | Screenshots, release checklist | Gate 1/2 | Required for Ga/Ewe voice, Hausa/Dagbani |
| CM-054 | Document authenticity and preservation | Audit / reporting | Stored filings and reports must preserve integrity and version history | Document service + Compliance | Content hashing, versioning, PDF/A storage, export metadata | Hash logs, storage tests, version history | Gate 1 | Supports audits |
| CM-055 | Change management on compliance logic | Governance | Any change to rates, filing rules, or validation logic requires controlled review | Compliance Service + Engineering | Dual approval workflow, release checklist, audit logs | PR records, approval logs, release evidence | Gate 1 | Compliance officer sign-off required |
| CM-056 | Naming and regulatory terminology control | Governance / accuracy | User-facing terminology must follow approved regulatory naming standards | Product + Compliance | Copy review checklist, glossary management | Glossary, content QA sign-off | Gate 1 | Includes “Ghana Enterprises Agency (GEA)” |
| CM-057 | Model/version control | AI governance | Pinned model identifiers must be reviewed at major releases and changes assessed | Architecture + NLP team | Version pin registry, release review checklist | ADRs, release notes, test diffs | Gate 1 and ongoing | Breaking changes require review |
| CM-058 | Release gating on regulatory sign-off | Governance | Production releases affecting compliance functions need explicit compliance approval | Engineering + Compliance Officer | Release checklist includes regulatory sign-off | Signed release checklist, deployment records | Gate 1 onward | Especially tax and privacy |
| CM-059 | Evidence portability | Audit / customer trust | Compliance evidence must be exportable for auditors, partners, and investigations | Platform + Compliance | Standard export bundles, immutable logs, document index | Export samples, audit pack generation tests | Gate 2 | Important for enterprise sales |
| CM-060 | Regional expansion readiness | Expansion governance | Country-by-country regulatory assessment required before expansion beyond Ghana | Compliance Officer + Strategy | Country assessment template, no dark launch into new markets | Assessment reports, gate approvals | Gate 4/5 | Kenya/East Africa terminology standard |

---

## 7. Gate-Based Compliance Checklist

### Gate 1 — MVP / Phase 1 Exit (Mandatory)
- DPC registration confirmed
- Privacy basis, consent, and retention controls documented
- pgvector default confirmed; Pinecone blocked unless DPIA signed off
- AES-256 at rest, TLS in transit, MFA for admin, RBAC, audit logging implemented
- Append-only transaction architecture and idempotent writes verified
- Tax rates externalized to configuration tables and validated against current law
- VAT-ready computation and filing evidence retention in place
- BoG perimeter review initiated and documented
- GRA, MoMo, and NCA external onboarding initiated within required timeline
- USSD licensing path active; fallback architecture documented
- Offline data protection controls tested
- Release checklist includes compliance sign-off

### Gate 2 — Public Launch
- DSAR workflow operational
- PAYE and SSNIT reporting workflows validated
- Penetration testing complete with critical findings resolved
- WhatsApp template/opt-in compliance operational
- Explainability, fairness, and human-escalation controls matured for advanced AI features
- Restore drills and incident processes evidenced

### Gate 3 — National Scale
- Expanded bias / fairness validation at scale
- Multi-region operational compliance and support auditability
- Mature reconciliation, fraud monitoring, and regulator-facing reporting
- Support and admin access reviews operating on schedule

### Gate 4 / 5 — Ecosystem and Regional Expansion
- Country-by-country regulatory assessments completed before rollout
- Third-party API / lender ecosystem controls formalized
- Enterprise audit-pack automation mature
- Regional data transfer reviews completed and approved

---

## 8. Evidence Pack Structure

Recommended evidence folders:

```text
/docs/compliance-evidence/
  /privacy/
  /security/
  /tax/
  /payroll/
  /filings/
  /audit-logs/
  /vendor-risk/
  /dr-bcp/
  /ai-governance/
  /language-validation/
  /release-signoff/
```

Suggested evidence index fields:
- control ID
- description
- owner
- latest evidence date
- next review date
- linked artefact path
- linked ticket / PR
- approver
- status

---

## 9. Open Items Requiring Legal / Compliance Confirmation

| Item | Why It Is Open | Owner | Needed By |
|---|---|---|---|
| Detailed Act 843 retention periods by record class | Needs legal interpretation and regulator guidance alignment | Compliance Officer | Before Gate 1 launch readiness |
| GRA submission API schemas and certification constraints | External dependency | Compliance Officer + Partnerships | During Phase 1 |
| SSNIT file/API technical requirements | External dependency | Compliance Officer + Partnerships | Before payroll launch |
| BoG licensing perimeter for any embedded finance features | Legal assessment required | Legal + Product + Architecture | Phase 1 |
| NCA implications of fallback routing specifics | Contractual / licensing confirmation needed | Legal + Product Ops | Before USSD launch |
| Cross-border processor adequacy for any future Pinecone or non-local AI vendor expansion | DPIA + legal assessment required | Compliance Officer | Before any non-default deployment |
| Country-specific expansion obligations outside Ghana | Market-specific legal work required | Strategy + Legal | Before each new market |

---

## 10. Operating Rules

1. No production launch occurs with unresolved **Gate 1** launch blockers.
2. No Pinecone deployment occurs before DPIA conclusion and written sign-off.
3. No hardcoded tax rate is permitted anywhere in code.
4. No destructive mutation of financial transactions is permitted.
5. No compliance-affecting release ships without compliance approval.
6. No new external integration goes live before it is added to `INTEGRATION_MANIFEST.md` and risk-reviewed.
7. No AI feature may make high-risk claims without fallback, confidence handling, and auditability.

---

## 11. Suggested Backlog Labels

Use consistent labels in issue tracking:

- `compliance:privacy`
- `compliance:tax`
- `compliance:ssnit`
- `compliance:bog`
- `compliance:nca`
- `compliance:security`
- `compliance:ai-governance`
- `compliance:release-gate`
- `dependency:regulator`
- `dependency:partner`
- `evidence-required`
- `legal-review`

---

## 12. Revision History

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0 | 2026-03-19 | OpenAI | Initial implementation-aligned compliance matrix generated from BizPulse specifications |

