# BizPulse AI — Comprehensive Requirements Breakdown
## Functional Requirements, Feature Set & Operational Workflows

**Document Type:** Implementation Requirements & Workflow Reference  
**Based On:** BizPulse AI Technical Specification v1.1 (March 2026)  
**Prepared By:** Senior Systems Architecture Review  
**Classification:** Internal — Implementation Reference  
**Status:** Authoritative Implementation Guide

---

## Table of Contents

1. [Document Purpose & Scope](#1-document-purpose--scope)
2. [Functional Requirements — Core AI Capabilities](#2-functional-requirements--core-ai-capabilities)
3. [Functional Requirements — Platform & Channel Delivery](#3-functional-requirements--platform--channel-delivery)
4. [Functional Requirements — Offline & Sync Architecture](#4-functional-requirements--offline--sync-architecture)
5. [Functional Requirements — Compliance & Financial Standards](#5-functional-requirements--compliance--financial-standards)
6. [Functional Requirements — Security & Identity](#6-functional-requirements--security--identity)
7. [Functional Requirements — Data Layer & Ingestion](#7-functional-requirements--data-layer--ingestion)
8. [Functional Requirements — External Integrations](#8-functional-requirements--external-integrations)
9. [Functional Requirements — Business Model & Monetization](#9-functional-requirements--business-model--monetization)
10. [Functional Requirements — Ethics, Bias & AI Governance](#10-functional-requirements--ethics-bias--ai-governance)
11. [Functional Requirements — Disaster Recovery & Business Continuity](#11-functional-requirements--disaster-recovery--business-continuity)
12. [Operational Workflows](#12-operational-workflows)
13. [Phase Gate Requirements & Go/No-Go Criteria](#13-phase-gate-requirements--gono-go-criteria)
14. [Non-Functional Requirements](#14-non-functional-requirements)
15. [Implementation Constraints & Dependencies](#15-implementation-constraints--dependencies)

---

## 1. Document Purpose & Scope

This document constitutes the definitive implementation reference derived from the BizPulse AI Technical Specification v1.1. It is structured to serve engineering teams, product managers, QA engineers, compliance officers, and technical leads as a single source of truth for what must be built, and how the system must behave end-to-end.

Every requirement in this document maps directly to a specification section. Where the specification makes implicit assumptions that carry implementation risk, this document makes them explicit. Requirements are organized into two primary dimensions:

- **Functional Requirements & Feature Set:** What the system must do, down to granular feature level
- **Operational Workflows:** How the system executes those functions end-to-end across technical and user journey dimensions

### 1.1 Requirement Priority Notation

| Label | Meaning |
|-------|---------|
| **P1 — Critical** | Must be present at MVP (Gate 1). Absence blocks launch. |
| **P2 — High** | Required before Gate 2 (public launch at Month 12). |
| **P3 — Standard** | Required before Gate 3 (national scale at Month 24). |
| **P4 — Ecosystem** | Required before Gate 4 (Phase 4 ecosystem maturity). |

---

## 2. Functional Requirements — Core AI Capabilities

### 2.1 Predictive Analytics Engine

#### 2.1.1 Cash Flow Forecasting Module

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-ANA-001 | The system must generate cash flow forecasts for 30-day, 60-day, and 90-day horizons | Forecast output includes projected inflows, outflows, and net position for each time horizon, with confidence intervals |
| FR-ANA-002 | Forecasts must incorporate mobile money settlement cycle patterns as a primary input signal | System correctly identifies and weights MoMo settlement lag (typically T+1 to T+3) in cash flow projections |
| FR-ANA-003 | The forecasting model must account for Ghana-specific seasonal patterns: Homowo, Easter, and Christmas demand cycles | Model training dataset includes at minimum 2 years of seasonally labelled transaction history per sector; seasonal factor applied to base forecast |
| FR-ANA-004 | Forecasts must account for agricultural cycle patterns for agribusiness users | Harvest and planting seasons are encoded as named features; agribusiness cohort achieves measurably lower MAPE than a baseline model without seasonal features |
| FR-ANA-005 | The ML model architecture must support time-series forecasting (e.g., LSTM, Prophet, or comparable) | Model architecture documented; backtesting results show ≥70% directional accuracy on held-out validation set |
| FR-ANA-006 | Business users must be able to view and interact with forecast outputs within the mobile app and web portal | Forecast displayed as a chart and tabular breakdown; user can select forecast horizon; drill-down by category supported |

#### 2.1.2 Demand Prediction Module

**Priority: P2**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-ANA-007 | The system must provide inventory demand predictions using time-series analysis | Demand forecasts generated at SKU level (for retail) or service category level; updated at minimum weekly |
| FR-ANA-008 | Demand model must incorporate market-day cycles (Makola, Kaneshie and equivalent regional markets) | Market-day dummy variables included as features; model trained on sector-specific cohorts with market-day exposure |
| FR-ANA-009 | Model must incorporate regional trade patterns and border activity signals where data is available | Data acquisition plan for border activity indicators documented; integrated where reliable external API exists |
| FR-ANA-010 | Users must receive actionable reorder recommendations derived from demand predictions | Reorder suggestions displayed with quantity, timing, and estimated cost; linked to supplier contact data where available |

#### 2.1.3 Credit Risk Scoring Engine

**Priority: P2**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-ANA-011 | The system must compute alternative credit scores using non-traditional data signals | Score produced for any user with ≥30 days of transaction history; score ranges documented and explainable |
| FR-ANA-012 | Mobile money transaction history must be a primary credit signal | MoMo API data feeds credit scoring model; transaction frequency, regularity, and volume are scored features |
| FR-ANA-013 | Utility payment history must be integrated as a supplementary credit signal where data partnerships permit | Data partnership agreements in place before this feature is activated; placeholder in model for utility signal present from launch |
| FR-ANA-014 | Social commerce activity must be a supplementary credit signal | Social commerce aggregator integration specified; signal weighted appropriately relative to financial signals |
| FR-ANA-015 | Credit score must be displayed to users in a plain-language, accessible format | Score shown with percentile ranking, contributing factors, and improvement recommendations in the user's chosen language |
| FR-ANA-016 | The scoring model must be exposed via a Credit Scoring API for third-party lender consumption | API endpoint operational; per-query pricing implemented; lender authentication and data sharing agreements in place |

#### 2.1.4 Supplier Risk Assessment Module

**Priority: P3**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-ANA-017 | The system must provide supplier risk early warnings for supply chain disruptions | Risk alerts generated for monitored suppliers; user configurable alert thresholds |
| FR-ANA-018 | System must monitor port congestion signals from Tema and Takoradi ports | Integration with GPHA data feed or alternative source; congestion level reflected in supplier risk score for import-dependent businesses |
| FR-ANA-019 | Cedi exchange rate volatility must be reflected in import cost risk projections | GHS/USD and GHS/EUR rate feeds integrated; import cost sensitivity analysis provided per supplier |
| FR-ANA-020 | Regional supplier network mapping must be maintained as structured data | Supplier directory with geographic tagging; risk scores aggregated by supplier location and sector |

---

### 2.2 Natural Language Processing (NLP) Engine

#### 2.2.1 Multilingual Architecture

**Priority: P1 (English + Twi); P2 (Ga, Ewe); P3 (Hausa, Dagbani)**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-NLP-001 | English (Ghanaian variant) must be supported at full production level for both voice and text input | 95%+ intent recognition accuracy on Ghanaian English test set; voice-to-text WER ≤15% |
| FR-NLP-002 | Twi (Akan) must be supported at full production level for both voice and text input | 90%+ intent recognition accuracy on Twi test set; voice-to-text WER ≤20% |
| FR-NLP-003 | Ga must be supported at production level for text, with voice in beta | Text intent recognition ≥85% on Ga test set; voice input available but clearly labelled as beta with fallback to text |
| FR-NLP-004 | Ewe must be supported at production level for text, with voice in beta | Text intent recognition ≥85% on Ewe test set; voice input available but labelled as beta |
| FR-NLP-005 | Hausa must be supported in beta for text-only input | Hausa text queries processed; intent recognition ≥75% on Hausa test set; beta status surfaced to users |
| FR-NLP-006 | Dagbani must be supported in beta for text-only input | Dagbani text queries processed; intent recognition ≥75% on Dagbani test set; beta status surfaced to users |
| FR-NLP-007 | The system must detect and correctly interpret code-switching between English and Twi or Ga within a single user query | Code-switched queries ("Mekɔɔ profit ahen wɔ last month?") correctly resolved to the appropriate intent; not rejected or misclassified |
| FR-NLP-008 | The system must correctly comprehend Pidgin English queries in a business context | Pidgin English query set (minimum 500 examples) maintained as test corpus; ≥80% intent resolution rate |
| FR-NLP-009 | Business terminology must be localized across all supported languages | Glossary of ≥200 SME business terms maintained per language; verified by native speaker reviewers |
| FR-NLP-010 | The voice interface must be optimized for low-literacy users with short, confirmation-based interaction patterns | User testing with low-literacy participants confirms ≥80% task completion without reading; interaction flow uses confirmation prompts before any financial action |

#### 2.2.2 Voice Interface & Speech Processing

**Priority: P1 (English/Twi); P2 (Ga/Ewe)**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-NLP-011 | OpenAI Whisper or equivalent must be used for speech-to-text conversion | STT pipeline integrated; word error rate (WER) measured on Ghana-specific audio test set per language |
| FR-NLP-012 | Text-to-speech output must be available in all production-tier languages | TTS voices available for English, Twi, Ga, and Ewe; voice quality assessed by native speakers |
| FR-NLP-013 | Voice queries must be resolved within 3 seconds for simple intents and 7 seconds for complex multi-step queries | End-to-end latency measured from user speech end to response audio start; SLA met at p95 under expected load |
| FR-NLP-014 | The system must support voice-commanded financial queries including balance inquiries, profit summaries, and expense categorization | Defined intent library covers ≥30 core financial query types in each production language |

#### 2.2.3 NLP Use Cases — Feature Requirements

**Priority: P1 (core); P2 (advanced)**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-NLP-015 | The NLP assistant must handle voice-commanded financial queries | Users can ask questions in natural language about their financial position and receive accurate responses |
| FR-NLP-016 | Automated customer service responses must be deliverable in local languages via the WhatsApp Business API channel | Customer service intents routed to WhatsApp channel; responses generated in the user's registered language |
| FR-NLP-017 | The system must parse contracts and invoices submitted as documents, extracting key financial terms | OCR pipeline integrated; invoice parser extracts vendor, amount, line items, tax, and due date; ≥90% field extraction accuracy on standard Ghanaian invoice formats |
| FR-NLP-018 | Sentiment analysis must be performed on customer feedback submitted in any supported language | Sentiment classification (positive/neutral/negative) with ≥85% accuracy on multilingual feedback corpus |
| FR-NLP-019 | The NLP resolution rate must reach ≥70% without human escalation before Gate 2 | NLP service logs track resolution rate; escalation rate monitored daily |

---

### 2.3 Automated Reporting & Compliance Module

#### 2.3.1 Compliance Report Types

**Priority: P1 (VAT, Financial Statements); P2 (Payroll, Customs); P3 (Annual Audit)**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-COM-001 | The system must automatically calculate and generate monthly or quarterly VAT returns in GRA-compliant format | VAT return output matches GRA schema; composite rate (12.5% VAT + 2.5% NHIL/GETFund) applied from a configuration-driven rate table; GRA submission success rate ≥95% in pilot |
| FR-COM-002 | VAT and CST rates must be stored in configuration tables independent of application code | Rate change requires only a data update, not a code deployment; change history audited with effective dates |
| FR-COM-003 | The system must generate quarterly and annual financial statements in IFRS for SMEs format | Statement of Financial Position, Statement of Comprehensive Income, Statement of Changes in Equity, Statement of Cash Flows, and auto-generated notes produced; ICAG format library maintained |
| FR-COM-004 | Monthly payroll compliance reports must be generated for SSNIT and GRA PAYE obligations | Payroll deduction calculations correct; SSNIT contribution file in required format; PAYE calculation uses current progressive rate table |
| FR-COM-005 | Annual Data Protection audit reporting must be generated to support Act 843 compliance | Audit log exports, data processing records, and DPIA documentation bundled into annual compliance report |
| FR-COM-006 | Customs declaration support must be provided for per-shipment submissions via GCNET/UNIPASS | Customs form templates maintained; HS code lookup integrated; form export in required format |
| FR-COM-007 | Corporate Income Tax provisional estimates and final computation must be supported | CIT computed at 25% standard rate with sector-specific reduced rates applied where configured; computation traceable to underlying transactions |
| FR-COM-008 | Withholding Tax must be automatically calculated and applied per transaction type | WHT rates (3–15%) applied by transaction type from configuration; WHT certificates generated |
| FR-COM-009 | A regulatory alert system must proactively notify users of policy changes affecting their compliance obligations | Alert delivery within 24 hours of a GRA publication or regulatory gazette entry; alerts categorized by urgency and business impact |

---

### 2.4 Intelligent Business Advisory Module

**Priority: P1 (Working Capital, Tax Planning); P2 (Market Intelligence); P3 (Regulatory Alerts — automated)**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-ADV-001 | The Working Capital Optimizer must provide real-time recommendations on receivables collection, payables management, and inventory turnover | Recommendations generated at minimum daily; shown in plain language with estimated cash impact in GHS; actionable steps provided |
| FR-ADV-002 | The Tax Planning Assistant must identify applicable tax incentives and exemptions for the user's sector | Incentive mapping covers Free Zones, 1D1F programme, AgriTech exemptions, and other GRA-published schemes; recommendations verified by compliance specialist before publication |
| FR-ADV-003 | Market Intelligence must aggregate sector trends, competitor pricing signals, and consumer behavior insights | Intelligence reports generated weekly at minimum; sector selection based on user business category; data sourced from aggregated (anonymized) platform data and permissioned external feeds |
| FR-ADV-004 | All AI-generated financial advice must include explainability — a plain-language rationale for each recommendation | Rationale shown alongside every recommendation; ≥3 contributing factors cited; user can request elaboration via NLP assistant |
| FR-ADV-005 | All AI-generated advice must pass through a compliance filter applying financial advice disclaimers | Disclaimer applied to all outputs involving credit, investment, or tax recommendations; disclaimer content reviewed by legal counsel |
| FR-ADV-006 | LLM hallucination mitigation must be implemented for all financial advice outputs | Structured prompts used; fact-checking layer validates numerical outputs against transactional data; human escalation flag triggered when confidence score below threshold |

---

## 3. Functional Requirements — Platform & Channel Delivery

### 3.1 Mobile Application (React Native — Expo)

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-MOB-001 | The mobile application must be built using React Native (Expo) for cross-platform Android and iOS delivery from a single codebase | Single codebase produces both Android (APK/AAB) and iOS (IPA) builds; no native Kotlin/Swift codebase maintained separately |
| FR-MOB-002 | Android support must cover API level 23 (Android 6.0) and above to maximize device coverage in Ghana | App installs and runs on Android 6.0+; tested on mid-range devices (Tecno, Itel, Infinix) representative of Ghana market |
| FR-MOB-003 | The mobile app must implement offline-first operation with full functional parity for core features when disconnected | Offline feature checklist defined; transaction entry, balance view, and report generation operational without network connectivity |
| FR-MOB-004 | TLS certificate pinning must be implemented in the React Native app for all API communication | Certificate pinning active for the BizPulse API domain; pin update delivered via OTA with 30-day overlap window |
| FR-MOB-005 | Biometric authentication (fingerprint/face) must be supported as a login option | Biometric login functional on supported devices; fallback to PIN/OTP where biometric not available |
| FR-MOB-006 | The app must operate within a 200 MB (Starter), 500 MB (Growth/Professional), or 1 GB (Enterprise) device storage budget | Storage usage monitored; user notified at 80% of tier limit; data pruning options provided |
| FR-MOB-007 | The mobile app must support over-the-air (OTA) updates for non-binary changes | OTA update mechanism operational; certificate pin updates deliverable without full app store release |
| FR-MOB-008 | The voice interface must be accessible from the main mobile app navigation | Voice query button present on primary navigation; activates in ≤2 taps from any screen |

### 3.2 USSD Interface

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-USSD-001 | A USSD interface must be built as a channel for users without smartphones or data connectivity | USSD session initiates correctly from *XXX# shortcode; sessions maintained per USSD session ID |
| FR-USSD-002 | NCA licensing must be obtained for the USSD number range before public launch | NCA license documentation on file; shortcode allocated and active |
| FR-USSD-003 | Core financial queries (balance, last transactions, tax deadline) must be accessible via USSD | Feature set formally defined; USSD menu tree documented; all stated queries resolvable within 5 USSD screens |
| FR-USSD-004 | USSD must serve as the fallback channel for LLM service degradation scenarios | USSD fallback activated automatically when LLM API latency exceeds threshold; critical queries (balance, tax deadline) served from structured database layer |
| FR-USSD-005 | USSD sessions must be stateless and resumable within the same session window | State maintained for session duration; no data loss on mid-session network interruption within session timeout |

### 3.3 Web Portal (Progressive Web Application — Next.js)

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-WEB-001 | The web portal must be built as a Progressive Web Application using Next.js with TypeScript | Build output is a PWA with service worker, offline capability, and installable prompt |
| FR-WEB-002 | The PWA must be functional on low-bandwidth connections (2G/Edge) for core features | Core dashboard loads in ≤8 seconds on simulated 2G connection (150 kbps); assets lazy-loaded |
| FR-WEB-003 | The web portal must expose the full compliance dashboard, financial statements, and reporting features | All report types accessible; export to PDF and CSV supported |
| FR-WEB-004 | Multi-user access (up to 5 for Professional tier, unlimited for Enterprise) must be managed through the web portal | User roles and permissions configurable by account admin; RBAC enforced per tier limit |

### 3.4 WhatsApp Business API Integration

**Priority: P2**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-WHAP-001 | WhatsApp Business API must be integrated as a fourth delivery channel | WhatsApp Business account verified; webhook integration active; inbound messages processed |
| FR-WHAP-002 | Customer service queries must be handled via WhatsApp in local languages | Automated response in user's registered language; intent resolution rate ≥60% for WhatsApp-specific query patterns |
| FR-WHAP-003 | Transactional notifications (tax deadlines, payment confirmations, balance alerts) must be deliverable via WhatsApp | Notification templates approved by WhatsApp; opt-in/opt-out managed per user preferences |

---

## 4. Functional Requirements — Offline & Sync Architecture

### 4.1 Local Data Storage

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-OFF-001 | SQLite must be used as the on-device database for React Native, with Write-Ahead Logging (WAL) mode enabled | SQLite initialized with WAL journal mode; confirmed in device diagnostics |
| FR-OFF-002 | All data stored on-device must be encrypted at rest | SQLite database encrypted with AES-256; encryption key stored in OS secure enclave (Keychain/Keystore) |
| FR-OFF-003 | Offline operation must be supported for up to 30 days for Standard/Growth tier users | User can operate without connectivity for the full offline window; data queued for sync; no data loss on reconnect |
| FR-OFF-004 | Offline operation for Free tier users must be supported for up to 7 days | 7-day offline limit enforced; user notified at 5 days with prompt to connect |

### 4.2 Synchronization Protocol

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-SYN-001 | Sync must use a queue-based delta sync approach, transmitting only changed records since last sync | Delta sync confirmed by monitoring sync payload sizes vs. full dataset size; no redundant full-sync transmissions |
| FR-SYN-002 | Every mutation API must enforce idempotency keys | Duplicate submissions within a 24-hour window are rejected with HTTP 409 and original transaction ID returned; tested with replay attack simulation |
| FR-SYN-003 | Pre-sync client-side checksum validation must occur before any write operations commence | Checksum comparison logged for every sync session; mismatches halt sync and trigger reconciliation alert |
| FR-SYN-004 | Offline queues must be replayed as atomic batch transactions | Partial batch failure triggers full batch rollback; no partial state committed; tested with mid-batch failure injection |
| FR-SYN-005 | Users must be notified of any resolved conflicts at next login session with an audit trail | Conflict notification UI shown at login if conflicts occurred; audit trail viewable in account activity |

### 4.3 Conflict Resolution Policy (Implementation-Level Requirements)

**Priority: P1**

| Requirement ID | Requirement | Resolution Strategy | Acceptance Criteria |
|---------------|-------------|---------------------|---------------------|
| FR-CON-001 | Financial transactions must use append-only conflict resolution | No overwrites; duplicates detected by idempotency key | Zero financial records overwritten in post-sync verification; deduplication confirmed by idempotency key matching |
| FR-CON-002 | Business profile and settings conflicts must resolve via Last-Write-Wins with server timestamp authority | Server timestamp is authoritative | Server timestamp always wins on profile field conflicts; confirmed in sync unit tests |
| FR-CON-003 | Inventory count conflicts must trigger a manual resolution prompt with a diff display | Human resolution required | Conflict diff shown to user before merge; user must confirm resolution; no auto-merge for inventory counts |
| FR-CON-004 | Tax computation input conflicts must use server-side merge with full audit trail of both versions | Both versions preserved | Audit trail stores pre- and post-merge values; regulatory significance noted in audit log |
| FR-CON-005 | NLP conversation history must remain device-local and must not be synced | No cross-device sync for NLP history | Sync payload confirmed to contain no NLP session data |

---

## 5. Functional Requirements — Compliance & Financial Standards

### 5.1 Ghana Data Protection Act (Act 843) Compliance

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-DPC-001 | The platform must be registered with the Data Protection Commission before public launch | DPC registration certificate on file; registration confirmed at Gate 1 |
| FR-DPC-002 | A Data Protection Officer (DPO) must be designated | DPO role documented in org chart; DPO contact point registered with DPC |
| FR-DPC-003 | Explicit, granular consent must be obtained for each data processing category at onboarding | Consent UI presents each category separately; consent state stored with timestamp; users can withdraw per-category consent |
| FR-DPC-004 | Data subjects must be able to request access, rectification, erasure, and portability of their data via a self-service portal | All four rights implemented; request processed within statutory timeframe; erasure confirmed for deleted data |
| FR-DPC-005 | Data residency for primary operational data must be within Ghana or the AWS Africa (Cape Town) region | Data residency confirmed by infrastructure audit; Cape Town used as primary region |
| FR-DPC-006 | A 72-hour breach notification pipeline to the DPC and affected users must be implemented and tested | Automated breach detection configured; notification workflow tested; runbook documented |
| FR-DPC-007 | End-to-end AES-256 encryption must be applied for all data at rest | Encryption confirmed on all PostgreSQL volumes, S3 buckets, and device-level SQLite |
| FR-DPC-008 | TLS 1.3 must be enforced for all data in transit | TLS 1.3 enforced on all endpoints; older protocol versions disabled; confirmed by TLS scanner |
| FR-DPC-009 | Audit logging with tamper-evident storage must be maintained | All data access and modification events logged; log integrity mechanism implemented (append-only log with hash chaining or equivalent) |
| FR-DPC-010 | A Data Protection Impact Assessment (DPIA) for the Pinecone vector database must be completed before production deployment | DPIA completed; cross-border transfer adequacy assessed; decision documented; pgvector fallback ready |
| FR-DPC-011 | Quarterly compliance audits must be conducted and documented | Audit schedule established; audit results stored with remediation tracking |

### 5.2 IFRS for SMEs — Financial Statement Engine

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-FIN-001 | Transactions must be mapped to an IFRS-aligned chart of accounts | Chart of accounts implemented; automatic classification suggestions shown on entry; user can override |
| FR-FIN-002 | Multi-currency handling must support GHS, USD, EUR, and GBP with exchange rate conversion | Currency conversion applied on transaction entry; exchange rates sourced from a reliable feed (Bank of Ghana or equivalent); conversion rate stored with transaction |
| FR-FIN-003 | Revenue recognition must implement the 5-step IFRS model | Revenue recognition engine enforces: (1) contract identification, (2) performance obligation identification, (3) transaction price determination, (4) allocation, (5) recognition on satisfaction; auditable per transaction |
| FR-FIN-004 | Asset impairment assessment must be supported | Impairment review prompts generated for fixed assets based on configured review schedule; impairment entries supported in the chart of accounts |
| FR-FIN-005 | Fair value calculations must be supported for applicable asset classes | Fair value input fields available for assets requiring fair value measurement; historical fair values retained |
| FR-FIN-006 | Lease accounting per IFRS 16 principles must be supported | Right-of-use asset and lease liability calculated and posted for qualifying leases; amortization schedules generated |
| FR-FIN-007 | Auto-generated notes accompanying financial statements must cover all mandatory IFRS disclosures | Notes template library covers ≥20 standard disclosure categories; populated from transactional data where possible |
| FR-FIN-008 | XBRL export for financial statements must be supported | XBRL output conforms to IFRS Taxonomy; validated against XBRL validator before release |
| FR-FIN-009 | ICAG-approved format templates must be maintained for all report types | Template library covers all ICAG-specified formats; reviewed and updated annually |
| FR-FIN-010 | Audit-ready working paper export must be generated for external auditors | Export package includes trial balance, transaction detail, supporting schedules, and reconciliations; PDF/A format |

### 5.3 Tax Engine Requirements

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-TAX-001 | All tax rates must be stored in configuration tables, independent of application code | Rate change process documented; rate update requires no code deployment; tested by updating staging rate table |
| FR-TAX-002 | A mandatory pre-launch rate verification step must be defined and executed | Process documented: compliance officer verifies all rates against current GRA publications before each release; sign-off recorded |
| FR-TAX-003 | VAT auto-calculation and GRA portal submission must be implemented | VAT return generated in GRA XML schema; submission API integrated; submission receipt stored; GRA submission success rate ≥95% |
| FR-TAX-004 | Corporate Income Tax must be calculated at 25% standard rate with configurable sector-specific rates | CIT computation engine implemented; sector rate table configurable; provisional and final estimates generated |
| FR-TAX-005 | PAYE calculation must use the current progressive tax rate table (0–35%) | PAYE computed correctly for all salary bands; employee tax certificates generated in GRA format |
| FR-TAX-006 | Withholding Tax must be automatically deducted per transaction type at configured rates (3–15%) | WHT matrix implemented by transaction type; certificates generated per transaction; WHT filing report generated monthly |
| FR-TAX-007 | Communication Service Tax must be supported for telecom-sector users | CST module available for users in the telecom sector; rate configurable; monthly filing report generated |
| FR-TAX-008 | Tax Planning Assistant must identify Free Zones, 1D1F, and AgriTech incentives applicable to each user | Incentive eligibility rules encoded; assistant prompt triggers on relevant user profile attributes |

### 5.4 Companies Act & GACC Requirements

**Priority: P2**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-GACC-001 | The system must support automated preparation of annual returns under Companies Act 2019 (Act 992) | Annual return templates maintained; data pre-populated from platform records; submission-ready output generated |
| FR-GACC-002 | Statutory register maintenance must be supported | Registers of directors, shareholders, and charges maintained; history tracked |
| FR-GACC-003 | GRA tax reconciliation aligned with Income Tax Act 896 must be generated | Tax-to-accounting reconciliation schedule generated; deferred tax positions computed |

---

## 6. Functional Requirements — Security & Identity

### 6.1 Authentication & Identity Management

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-SEC-001 | OAuth 2.0 / OIDC must be implemented via Keycloak as the identity provider | Keycloak deployed; OAuth 2.0 authorization flows operational; OIDC tokens issued |
| FR-SEC-002 | JWT access tokens must be issued with a 15-minute expiry | JWT exp claim set to 15 minutes; token refresh flow implemented; expired tokens rejected at API gateway |
| FR-SEC-003 | Biometric, PIN, and OTP authentication methods must all be supported on the mobile app | All three methods functional; method selection per user preference; fallback chain defined (Biometric → PIN → OTP) |
| FR-SEC-004 | Ghana Card identity verification must be integrated for user identity verification | Ghana Card verification API integrated; KYC check triggered at account creation for regulated features |
| FR-SEC-005 | MFA must be mandatory for all admin-level access | MFA enforcement confirmed for all admin roles; no admin session possible without MFA |
| FR-SEC-006 | Session management must terminate inactive sessions after a defined inactivity timeout | Configurable inactivity timeout (default: 30 minutes for mobile, 15 minutes for web); session termination confirmed |

### 6.2 Role-Based Access Control (RBAC)

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-SEC-007 | RBAC must be implemented with least-privilege enforcement | Role definitions documented; all API endpoints gate-checked against role; privilege escalation not possible without re-authentication |
| FR-SEC-008 | Multi-user access must enforce tier-based user limits (5 for Professional; unlimited for Enterprise) | User count enforced at account tier; addition of user beyond limit blocked with clear error message |
| FR-SEC-009 | Field-level encryption must be applied to all PII data stored in PostgreSQL | PII fields identified and enumerated; field-level encryption applied; verified by schema audit |

### 6.3 Certificate Lifecycle Management

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-CERT-001 | AWS Certificate Manager (ACM) must be used for all AWS-hosted TLS endpoints with auto-renewal enabled | ACM certificates issued; auto-renewal confirmed active; no manual renewal required |
| FR-CERT-002 | Let's Encrypt with Certbot must be used for non-AWS endpoints with 30-day pre-expiry renewal trigger | Certbot configured; renewal trigger at 30 days; renewal tested |
| FR-CERT-003 | Datadog alerts must fire at 60 days, 30 days, and 7 days before certificate expiry | Datadog certificate monitors configured and tested; alert routing confirmed |
| FR-CERT-004 | TLS certificate pinning must be implemented in the mobile app with a 30-day pin overlap window | Certificate pinning code implemented; pin update via OTA; old pin retained for 30 days after new pin deployment |
| FR-CERT-005 | New pin updates must be deployed via staged OTA 45 days before existing pin expiry | Pin rotation schedule maintained; OTA deployment timeline tracked per certificate expiry date |
| FR-CERT-006 | OCSP stapling must be enabled on all server endpoints | OCSP stapling confirmed enabled on all nginx/load balancer configurations |
| FR-CERT-007 | Zero expired certificates in production is a mandatory operational KPI | Automated check confirms zero expired certs monthly; reported in operational KPI dashboard |

### 6.4 Network & Application Security

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-SEC-010 | VPC isolation must be implemented with private subnets for the data tier | Data tier not reachable from public internet; VPC flow logs enabled |
| FR-SEC-011 | CloudFlare WAF and DDoS protection must be active on all public endpoints | CloudFlare WAF rules configured; DDoS protection tier active; tested with simulated attack scenarios |
| FR-SEC-012 | API rate limiting must be enforced at the Kong API gateway, tiered by subscription level | Rate limits defined per tier; limits enforced; 429 responses returned with retry-after header |
| FR-SEC-013 | SIEM integration with real-time alerting must be operational | SIEM platform integrated; alert rules defined for known attack patterns; on-call escalation path documented |
| FR-SEC-014 | Quarterly penetration testing must be conducted by an external party | Penetration test scheduled quarterly; findings tracked to remediation; critical findings remediated within 30 days |
| FR-SEC-015 | An annual bug bounty program must be operated | Bug bounty program published with defined scope and reward structure; submission process operational |
| FR-SEC-016 | Input validation must be enforced on all API endpoints | Validation schemas defined for all endpoints; fuzz testing confirms rejection of malformed inputs |

---

## 7. Functional Requirements — Data Layer & Ingestion

### 7.1 Data Store Routing Rules

**Priority: P1**

All data must be routed to the correct store per the following binding rules. Violating these routing rules creates cross-store consistency risk.

| Requirement ID | Data Category | Target Store | Requirement |
|---------------|--------------|-------------|-------------|
| FR-DAT-001 | All transactional records, user accounts, compliance filings, financial statements | PostgreSQL (primary) | ACID-compliant; all financial writes go to PostgreSQL; no exceptions |
| FR-DAT-002 | Cash flow time-series linked to transaction IDs; revenue trends; user activity metrics | TimescaleDB (PostgreSQL extension) | TimescaleDB extension enabled on PostgreSQL; business metric time-series stored in hypertables; linked to transactional records via transaction ID foreign keys |
| FR-DAT-003 | API latency; Kafka throughput; Kubernetes pod metrics; database query performance; error rates | InfluxDB | Infrastructure telemetry never routed to PostgreSQL/TimescaleDB; InfluxDB retained exclusively for system-level observability |
| FR-DAT-004 | Document embeddings; query embeddings for RAG; semantic search vectors | Pinecone (pending DPIA approval) / pgvector (default fallback) | Pinecone deployment gated on DPIA outcome; pgvector enabled on PostgreSQL as default-safe alternative |
| FR-DAT-005 | JWT sessions; rate-limit counters; real-time leaderboards; short-TTL query cache | Redis | TTL set per data type; Redis not used as persistent store; all Redis data must be recoverable from primary store |

### 7.2 Data Ingestion Pipeline

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-ING-001 | Apache Kafka must serve as the central ingestion bus with defined topic names | Topics created: raw.momo.transactions, raw.vodafone.transactions, raw.bank.statements, raw.manual.entries; topic naming convention documented |
| FR-ING-002 | Apache Flink must perform stream processing for deduplication, schema validation, enrichment, and real-time fraud scoring | Flink job deployed; deduplication confirmed by replay test; schema violations rejected with dead-letter queue routing |
| FR-ING-003 | Merchant categorization must be applied during stream processing | Categorization model deployed in Flink pipeline; categorization accuracy ≥85% on test transaction set |
| FR-ING-004 | Currency conversion must be applied during stream processing using a live exchange rate feed | Exchange rate feed integrated; rate applied at ingestion time; source rate and conversion rate stored with transaction |
| FR-ING-005 | A Data Lake on S3 in Parquet format must receive enriched data from the pipeline | S3 data lake configured; Parquet files partitioned by date and data source; retention policy applied |
| FR-ING-006 | Kafka topics must be configured with 7-day retention and async backup to 30 days | Kafka retention settings applied; backup mechanism operational |

### 7.3 Document & OCR Pipeline

**Priority: P2**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-DOC-001 | An OCR pipeline must extract structured data from uploaded invoices, receipts, and documents | OCR integrated; key field extraction (vendor, amount, line items, tax, due date) ≥90% accuracy on standard Ghanaian invoice formats |
| FR-DOC-002 | Documents must be stored in PDF/A format per ISO 19005 | All stored documents validated against PDF/A standard before storage |
| FR-DOC-003 | Document storage must be retained for 7 years to meet regulatory requirements | S3 lifecycle policy applies 7-year retention to document storage; deletion blocked by retention lock |

---

## 8. Functional Requirements — External Integrations

### 8.1 Mobile Money Integrations

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-INT-001 | MTN MoMo API must be integrated via REST with OAuth 2.0 and webhook subscriptions | Commercial agreement signed before Week 1; integration live by Week 8; real-time webhook events processed; hourly batch fallback operational |
| FR-INT-002 | Vodafone Cash API must be integrated with the same architecture as MTN MoMo | Vodafone Cash commercial agreement signed; integration live by Month 8; transaction sync latency <2 minutes |
| FR-INT-003 | AirtelTigo API integration must be developed | AirtelTigo agreement pursued; integration scope defined; phased delivery if API maturity is limited |
| FR-INT-004 | Multi-provider mobile money redundancy must be maintained | If one MoMo provider API is unavailable, transactions are queued in offline store; sync resumes on provider API recovery; no data loss |
| FR-INT-005 | Mobile money payment integration must support subscription billing | Subscription debits processed via MoMo for all tiers; payment confirmation triggers access provisioning |

### 8.2 Banking Integrations

**Priority: P2**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-INT-006 | GhIPSS integration must be implemented using ISO 20022 protocol for instant payment connectivity | GhIPSS connectivity established; ISO 20022 message format implemented; end-to-end payment flow tested |
| FR-INT-007 | Ecobank Connect and Fidelity Bank API integrations must be developed | Integration documentation received; REST connections implemented; bank statement import operational |
| FR-INT-008 | A hybrid approach (Open Banking API where available; screen scraping as legacy fallback) must be implemented for broader bank coverage | Open Banking API used where bank supports it; screen scraping fallback documented with legal review; user consent explicitly obtained for screen scraping |

### 8.3 Government & Regulatory Integrations

**Priority: P1 (GRA); P2 (SSNIT); P3 (RGD)**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-INT-009 | GRA API integration must be implemented for VAT and tax filings | GRA API access obtained (Lead time: 3–6 months from Week 1); API integration live; XML schema submissions validated |
| FR-INT-010 | GRA Certified Tax Software Provider registration must be obtained | Registration submitted at Week 1; certification achieved before Gate 1 |
| FR-INT-011 | SSNIT portal integration must be implemented for payroll compliance file submission | SSNIT API access obtained (Lead time: 2–4 months from Week 3); payroll file submission operational |
| FR-INT-012 | RGD integration must be planned and specification-ready for Phase 3 delivery | RGD integration specification documented; development deferred to Phase 3 pending RGD API availability |

### 8.4 Commerce & Logistics Integrations

**Priority: P3**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-INT-013 | Jumia API integration must be implemented for order and inventory data ingestion | Jumia API agreement in place; order data ingested in near real-time; mapped to transaction engine |
| FR-INT-014 | Tonaton API integration must be implemented | Tonaton data ingested; social commerce signals available for credit scoring |
| FR-INT-015 | GPHA (port authority) data feed must be integrated for supplier risk monitoring | GPHA data source identified; port congestion signal integrated into supplier risk model |
| FR-INT-016 | Ghana Post GPS integration must be supported for logistics tracking | Ghana Post GPS address system integrated; delivery address validation supported |

---

## 9. Functional Requirements — Business Model & Monetization

### 9.1 Subscription Tier Management

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-BIZ-001 | Four subscription tiers must be implemented: Starter (Free), Growth (GHS 99/mo), Professional (GHS 299/mo), Enterprise (GHS 799+/mo) | All four tiers active; feature gates enforced per tier; upgrade/downgrade flows functional |
| FR-BIZ-002 | Starter tier must include: basic transaction tracking, mobile money sync (1 account), simple P&L, USSD access | Feature availability confirmed by QA against tier spec; multi-account sync blocked on Starter |
| FR-BIZ-003 | Growth tier must include: multi-account sync, cash flow forecasting, VAT automation, basic NLP assistant, email support | All Growth features operational; email support queue active |
| FR-BIZ-004 | Professional tier must include: full compliance suite, multi-user access (up to 5), credit score dashboard, limited API access, priority support | Compliance suite complete; user count enforced at 5; API key issued; SLA for priority support defined |
| FR-BIZ-005 | Enterprise tier must include: unlimited users, custom integrations, dedicated account manager, on-site training option, SLA guarantees | Enterprise onboarding process defined; SLA documentation signed; dedicated AM assigned at account creation |
| FR-BIZ-006 | Mobile money payment processing must support all subscription billing with <2-minute confirmation | MoMo billing tested end-to-end; access provisioning triggered on payment confirmation |

### 9.2 Transaction Revenue Streams

**Priority: P2**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-BIZ-007 | Credit facilitation fee of 1–2% of loan value must be tracked and collected on lending partner referrals | Revenue share agreement in place with lending partners; fee collection mechanism implemented; revenue reported separately in financial dashboard |
| FR-BIZ-008 | Insurance placement fee of 5–10% of premium must be collected | Insurance partner agreements define fee; placement tracking implemented |
| FR-BIZ-009 | Payment processing fee of 0.5% of transaction value must be applied for integrated payment flows | Processing fee applied correctly; fee calculation logged; reconciliation report generated |
| FR-BIZ-010 | Export documentation service must be offered at GHS 50–200 per shipment | Export documentation service operational; fee collected at service initiation; shipment records stored |

### 9.3 B2B API Products

**Priority: P4**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-BIZ-011 | The BizPulse Score API must be available for third-party lenders at GHS 2–10 per query | API endpoint published; authentication for third-party clients implemented; per-query billing operational; ≥5 live integrations before Gate 4 |
| FR-BIZ-012 | A Financial Insights API must be available by subscription for portfolio monitoring | API documented; subscription billing active; data refresh frequency defined |
| FR-BIZ-013 | A Compliance API must be available for third-party tax software providers | Compliance API published; per-filing fee charged; GRA schema served via API |
| FR-BIZ-014 | A Market Data API must be available on a tiered subscription | Market data aggregated from platform; API published; data anonymization layer confirmed |

---

## 10. Functional Requirements — Ethics, Bias & AI Governance

### 10.1 Algorithmic Fairness Framework

**Priority: P2**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-ETH-001 | Credit scoring algorithms must be gender-blind; scoring must be validated on gender-disaggregated datasets | Gender variable excluded from model features; fairness audit reports show <5% score disparity across gender groups for equivalent financial profiles |
| FR-ETH-002 | Region-adjusted models must prevent urban-rural scoring disparities | Region-adjusted scoring factors applied; rural-specific alternative data sources (agricultural cooperatives, farmer associations) integrated |
| FR-ETH-003 | Mobile money transaction history must be the primary scoring signal to avoid formal documentation bias against market traders | Documentation requirements optional in scoring; MoMo history sufficient for a valid score |
| FR-ETH-004 | NLP model training data investment must be equal across all production languages, verified by native speakers | Training dataset size and quality metrics published per language; community validation process documented |
| FR-ETH-005 | Sector-specific model calibration must prevent stereotyping of traditional sectors (chop bars, kiosks) | Representative training data for each sector; sector models calibrated separately; calibration results reviewed by ethics board |
| FR-ETH-006 | Demographic parity analysis and disparate impact testing (80% rule) must be conducted before any model deployment | Pre-deployment assessment report required; 80% rule applied to all protected group comparisons; ethics board sign-off required |
| FR-ETH-007 | Continuous bias drift monitoring must be operational with real-time outcome disparity dashboards | Bias monitoring dashboards live in Datadog or equivalent; automated alerts if disparity metric exceeds threshold |
| FR-ETH-008 | Quarterly fairness audits by an external body must be scheduled | Audit contract in place; first audit conducted before Gate 2; audit reports stored and remediation tracked |
| FR-ETH-009 | A human-in-the-loop escalation mechanism must be implemented for flagged credit and access decisions | Escalation flag triggers review queue; review SLA is 5 working days; user notified of escalation status |
| FR-ETH-010 | An appeals process with a 5-day resolution SLA must be available for users who dispute algorithmic decisions | Appeals portal live; SLA tracked; resolution documented per case |
| FR-ETH-011 | All AI recommendations must include an explainability output accessible to the user | Explainability rationale shown in UI; ≥3 contributing factors cited per recommendation; NLP assistant can elaborate on request |
| FR-ETH-012 | An annual public fairness report must be published | Report published on company website; covers demographic parity analysis, audit results, and remediation actions |

### 10.2 AI Ethics Governance Structure

**Priority: P2**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-ETH-013 | An independent AI Ethics Board must be established with representation from academia, civil society, and industry | Board constituted; members from University of Ghana/KNUST, Ghana Center for Democratic Development, and industry; terms of reference published |
| FR-ETH-014 | An Algorithmic Impact Assessment must be mandatory for all model deployments affecting credit, pricing, or access | AIA process documented; sign-off required before any model goes to production |
| FR-ETH-015 | An anonymous whistleblower channel for reporting bias concerns must be operational | Whistleblower channel live; reports routed to DPO and Ethics Board; anonymity guaranteed by technical design |

---

## 11. Functional Requirements — Disaster Recovery & Business Continuity

### 11.1 RTO & RPO by Service Tier

**Priority: P1**

| Requirement ID | Service | RTO Requirement | RPO Requirement | Priority Tier |
|---------------|---------|----------------|-----------------|---------------|
| FR-DR-001 | Transaction Engine | ≤15 minutes | 0 minutes (synchronous replication) | P1 — Critical |
| FR-DR-002 | Compliance & Tax Filing | ≤1 hour | ≤5 minutes | P1 — Critical |
| FR-DR-003 | NLP / Advisory Service | ≤2 hours | ≤15 minutes | P2 — High |
| FR-DR-004 | Analytics & Reporting | ≤4 hours | ≤1 hour | P2 — High |
| FR-DR-005 | Admin / Back-office | ≤24 hours | ≤4 hours | P3 — Standard |

### 11.2 Backup Architecture Requirements

**Priority: P1**

| Requirement ID | Component | Backup Frequency | Retention | Replication |
|---------------|-----------|-----------------|-----------|-------------|
| FR-BKP-001 | PostgreSQL primary | Continuous WAL streaming | 30 days PITR | AWS Cape Town → AWS EU (West) |
| FR-BKP-002 | Redis session state | RDB snapshot every 15 minutes | 24 hours | Single-region (stateless recovery acceptable) |
| FR-BKP-003 | S3 / Data Lake | Continuous cross-region replication | 7 years (regulatory) | Cross-region to eu-west-1 |
| FR-BKP-004 | Kafka topics | 7-day native retention + async backup | 30 days | Same-region; 3x replication factor |
| FR-BKP-005 | Application configuration / IaC | Git-backed (ArgoCD) | Indefinite | GitHub remote |

### 11.3 Failover Architecture Requirements

**Priority: P1**

| Requirement ID | Requirement | Acceptance Criteria |
|---------------|-------------|---------------------|
| FR-DR-006 | Primary region must be AWS Cape Town (af-south-1) across 3 availability zones | Multi-AZ deployment confirmed; app nodes and database replicas distributed across AZ-a, AZ-b, AZ-c |
| FR-DR-007 | A warm standby DR environment must be maintained in AWS EU-West (eu-west-1) | Warm standby provisioned; S3 cross-region replica active; DB read replica promotion-ready |
| FR-DR-008 | Route 53 health checks must automatically shift DNS to DR standby for P1 services within 15 minutes of primary failure | Route 53 failover configuration tested; automated DNS shift confirmed within 15-minute window in DR drill |
| FR-DR-009 | DR declaration threshold must be defined as 10 minutes of primary region unavailability | CloudWatch alarm configured for 10-minute unavailability; escalation to DR lead documented in runbook |
| FR-DR-010 | Switchback to primary must require a 30-minute stability window before traffic transfer | Switchback procedure documented; stability window enforced in runbook; post-switchback monitoring checklist defined |
| FR-DR-011 | A full failover drill must be conducted annually (Q4) with results documented and reviewed by CTO | Annual drill schedule maintained; drill report template defined; CTO sign-off on each drill report |
| FR-DR-012 | A tabletop DR exercise must be conducted bi-annually | Tabletop exercise facilitated; participants include CTO, SRE lead, and compliance officer |

---

## 12. Operational Workflows

This section maps the end-to-end technical and user workflows required to deliver the platform's functional requirements. Each workflow describes the full sequence of system interactions from initiation to completion.

---

### 12.1 User Onboarding Workflow

**Applicable to:** All new users (all channels)

```
Step 1: Channel Entry
  User arrives via: Mobile App | Web PWA | USSD | WhatsApp
  System: Channel detection; session initialization

Step 2: Account Registration
  User provides: Phone number (required), email (optional), business name
  System: Phone OTP verification; Ghana Card KYC check (for regulated tiers)
  Outcome: Account created in PostgreSQL; user role set to "Starter"

Step 3: Granular Consent Collection
  System: Present consent UI with categories:
    [a] Transaction data processing
    [b] AI-generated advisory (credit scoring, recommendations)
    [c] Data sharing with financial partners (opt-in)
    [d] Marketing communications (opt-in)
  User: Accepts/declines per category
  System: Consent state stored with ISO 8601 timestamp per category

Step 4: Business Profile Setup
  User provides: Business sector, size, region, mobile money account number(s)
  System: Business profile created; Tier = Starter assigned; storage budget initialized

Step 5: Language Preference
  User selects: English / Twi / Ga / Ewe / Hausa / Dagbani
  System: Language preference stored; all subsequent NLP interactions use this language

Step 6: Mobile Money Sync Authorization
  User: Grants MoMo API authorization via telco OAuth flow
  System: Access token stored securely; initial transaction sync triggered

Step 7: Onboarding Confirmation
  System: Sends confirmation via SMS (all users) and push notification (mobile users)
  User: Lands on dashboard with sample data overlay for empty-state guidance

Step 8: Regulatory Notification (Background)
  System: DPC registration reference included in data processing records
  Compliance log: Onboarding event logged with consent state and timestamp
```

---

### 12.2 Transaction Capture & Sync Workflow

**Applicable to:** All users across all channels

```
Step 1: Transaction Event
  Trigger: [a] MoMo webhook event | [b] Manual entry | [c] Bank API batch | [d] POS integration

Step 2a — Online Path (Device has connectivity):
  Transaction → Kafka topic (raw.<provider>.transactions)
  → Apache Flink stream processing:
    - Deduplication check (idempotency key lookup)
    - Schema validation
    - Merchant categorization
    - Currency conversion (if multi-currency)
    - Real-time fraud scoring
  → Write to PostgreSQL (operational record)
  → Write to TimescaleDB (business metric time-series)
  → Publish processed.transactions.enriched topic
  → Notification service: Push alert to user

Step 2b — Offline Path (Device has no connectivity):
  Transaction → SQLite local store (encrypted WAL)
  → Idempotency key generated and stored locally
  → Queued for sync; user sees "Pending Sync" indicator

Step 3 — Reconnection (Offline → Online):
  Client: Run pre-sync checksum comparison against server state
  If mismatch: Reconciliation alert raised; sync paused pending review
  If match: Proceed to batch replay

  Batch replay:
    → For each queued transaction:
      - Submit with idempotency key
      - Server: Accepts (new) or rejects with 409 + original transaction ID (duplicate)
    → All accepted writes committed atomically
    → If any write fails: Full batch rollback; user notified of failure

Step 4: Conflict Handling (if applicable):
  → Financial transactions: Append-only; duplicates rejected; no overwrite
  → Inventory counts: Diff displayed; user must confirm resolution
  → Business settings: Server LWW applied; user notified at next login

Step 5: Post-Sync Confirmation:
  User: Conflict notification displayed at login (if conflicts occurred)
  System: Sync completion logged; audit trail updated
```

---

### 12.3 NLP Query Resolution Workflow

**Applicable to:** All users submitting voice or text queries

```
Step 1: Query Submission
  Input type: Voice (Whisper STT) | Text
  Channel: Mobile App | WhatsApp | Web Portal

Step 2: Language Detection & STT (if voice)
  Whisper model: Transcribes audio to text
  Language detection: Identifies language (including code-switching detection)
  Fallback: If STT confidence <70%, prompt user to repeat or switch to text

Step 3: LangChain Orchestration
  LangChain: Selects prompt template based on business context
  → RAG retrieval from Vector DB (regulations, business documents)
  → Tool selection: Calculator | Database query | External API | Tax engine
  → Memory management: Injects relevant conversation history (device-local)

Step 4: LLM Router (Model Selection)
  Query type routing:
    "What's my balance?" → claude-haiku-4-5-20251001 (<500ms target)
    "Should I take this loan?" → claude-sonnet-4-6 (<3s target)
    "How much VAT do I owe?" → claude-sonnet-4-6 + Tax calculator (<2s target)
    "Summarize this invoice" → claude-sonnet-4-6 + OCR + Document parser (<5s target)

Step 5: Fallback Chain (if LLM unavailable)
  Fallback 1: Redis cached response (TTL 5 minutes, high-confidence matches only)
  Fallback 2: Local fine-tuned classification model (offline-capable; structured queries only)
  Fallback 3: USSD/SMS structured response + human escalation flag

Step 6: Output Processing
  → Response formatted per channel (text | voice TTS | USSD screen)
  → Translation applied (to user's registered language)
  → Compliance filter applied: Financial disclaimer appended where applicable
  → Explainability rationale appended for advisory outputs
  → Hallucination check: Numerical values validated against transaction database

Step 7: Delivery & Logging
  Response delivered to user on originating channel
  Resolution logged: intent, language, resolution status, escalation flag (if any)
  Resolution rate monitored: Target ≥70% without escalation (Gate 2 criterion)

Step 8: Human Escalation (if triggered)
  Escalation queue populated with full context (query, language, failed intents)
  Customer success team resolves within defined SLA
  Resolution fed back as training signal for model improvement
```

---

### 12.4 VAT Filing Workflow

**Applicable to:** Growth, Professional, Enterprise tier users

```
Step 1: Filing Period Trigger
  System: Regulatory alert fires at Day 1 of new filing month/quarter
  User: Notified via push notification, WhatsApp, and email

Step 2: Data Aggregation
  System: Compliance service queries PostgreSQL for all taxable transactions in period
  → Sales transactions extracted; zero-rated and exempt items separated
  → Purchase transactions extracted for input tax computation

Step 3: VAT Calculation Engine
  → Output Tax: Taxable sales × composite rate (from config table — verified against GRA)
  → Input Tax: Qualifying purchases × applicable rate
  → Net VAT Payable: Output Tax − Input Tax
  → Validation: Calculation reviewed by rules engine for anomaly flags

Step 4: Return Generation
  System: VAT return generated in GRA-compliant XML schema
  User: Review screen presented; line items visible; user can dispute or amend

Step 5: User Approval
  User: Reviews and confirms return
  System: Return locked; pre-submission audit record created

Step 6: GRA Submission
  System: XML payload submitted to GRA API
  GRA: Returns submission receipt or error code
  If success: Receipt stored; user notified; next deadline set
  If failure (non-network): Error parsed; user notified with corrective action
  If failure (network): Queued for retry with exponential backoff; user notified of pending status

Step 7: Audit Trail
  Submission event logged with: timestamp, submitted values, receipt ID, submitter identity
  Return stored in PDF/A format; retained for 7 years

Step 8: Payment (if applicable)
  System: VAT payable amount displayed with payment options
  User: Can initiate payment via integrated MoMo or bank transfer
  System: Payment confirmation stored and linked to VAT return record
```

---

### 12.5 Credit Score Generation & Lending Referral Workflow

**Applicable to:** Users with ≥30 days of transaction history; lending partners via API

```
Step 1: Score Eligibility Check
  System: Checks if user has ≥30 days of active transaction history
  If eligible: Score generation triggered

Step 2: Feature Engineering
  → MoMo transaction frequency, regularity, and volume (primary signals)
  → Utility payment data (if data partnership active)
  → Social commerce activity (if aggregator integrated)
  → Business sector, region (for model calibration)
  → Gender-blind signal set: gender variable excluded

Step 3: Fairness Pre-Check
  → Demographic parity check run on model inputs
  → If disparity flag raised: Manual review triggered before score issued
  → Rural/urban adjustment applied per region-adjusted model

Step 4: Score Computation
  → ML model produces score in defined range (e.g., 300–850)
  → Confidence interval computed
  → Contributing factors ranked (≥3 factors identified)
  → Explainability output generated in plain language

Step 5: Score Display to User
  → Score shown with percentile ranking
  → Contributing factors listed in user's language
  → Improvement recommendations provided
  → Disclaimer: "This score is indicative and not a guarantee of credit approval"

Step 6: Lender API Consumption (B2B Path)
  → Lender submits authorized query to BizPulse Score API
  → Authentication verified (OAuth 2.0; server-to-server API key)
  → Per-query fee charged (GHS 2–10); billing event recorded
  → Score, confidence interval, and contributing factors returned in JSON
  → Rate limit applied per lender tier

Step 7: Referral & Lead Generation
  → User opts into lending marketplace (explicit consent required)
  → Pre-qualified lead data shared with matching lending partners (per consent)
  → Credit facilitation fee (1–2% of loan value) tracked on draw-down confirmation
```

---

### 12.6 Disaster Recovery Failover Workflow

**Applicable to:** SRE team and on-call engineers

```
Step 1: Detection
  CloudWatch alarm: Primary region health metric breach detected
  Datadog alert: API error rate or latency spike exceeds threshold
  On-call engineer: Paged via PagerDuty

Step 2: Assessment (0–10 minutes)
  On-call engineer: Assesses scope of impact (AZ failure vs. full region failure)
  If recoverable within 10 minutes: Attempt recovery in primary region
  If primary region unavailable >10 minutes: Proceed to Step 3

Step 3: DR Declaration (Minute 10)
  DR lead: Formally declares DR event
  Stakeholder notification: CTO, compliance officer, customer success lead notified

Step 4: P1 Automated Failover (Minutes 10–15)
  Route 53 health checks: Automatically shift DNS for P1 services to DR standby (eu-west-1)
  Target: DNS propagation complete within 15 minutes of DR declaration
  Transaction Engine and Compliance Service: Serving from warm standby

Step 5: Manual Failover Steps (DR Lead)
  a. Promote PostgreSQL read replica in eu-west-1 to primary
  b. Update application configuration via ArgoCD
  c. Scale up warm standby instances to full production capacity
  d. Verify Kafka consumer groups reconnected to DR brokers
  e. Confirm Redis cache populated from database (stateless recovery)

Step 6: Service Validation
  Run smoke test suite against DR environment
  Confirm transaction engine processes test transaction end-to-end
  Confirm VAT calculation returns correct output on test dataset
  NLP service health check confirmed

Step 7: User Communication
  Status page updated with incident notice
  WhatsApp / SMS notification sent to active users if service degradation >30 minutes

Step 8: Switchback (Primary Restored)
  Primary region stabilization confirmed over 30-minute observation window
  Route 53 health checks re-point to primary region
  PostgreSQL: DR transactions replicated back to primary; promote primary
  ArgoCD: Application configuration reverted to primary region settings
  Monitoring: 2-hour elevated monitoring post-switchback

Step 9: Post-Incident Review
  Incident report completed within 5 business days
  Root cause analysis documented
  RTO/RPO targets measured against actuals; any shortfalls remediated
  DR drill record updated (if this was a declared drill)
```

---

### 12.7 Offline Sync Conflict Resolution Workflow

**Applicable to:** Users reconnecting after an offline period

```
Step 1: Connectivity Restored
  Device: Detects network availability
  Sync service: Initiates pre-sync checksum comparison

Step 2: Checksum Validation
  Client: Computes checksum of local SQLite state for sync-eligible records
  Server: Returns server-side checksum for same record set
  If checksums match: Proceed to Step 3
  If mismatch: Alert raised; sync paused; user prompted to contact support

Step 3: Delta Sync Upload
  Client: Transmits queued delta records (changes since last successful sync)
  Each record includes: idempotency key, timestamp, record type, payload

Step 4: Per-Record Conflict Evaluation (Server-side)
  For each record:
    Financial transaction:
      → Idempotency key lookup
      → If new: Accept and persist; return 200
      → If duplicate: Reject with 409; return original transaction ID
    Business profile / settings:
      → Compare server timestamp vs. client timestamp
      → Server timestamp wins (LWW); client value discarded if server is newer
    Inventory count:
      → Conflict logged; deferred to manual resolution queue
    Tax computation input:
      → Both versions preserved in audit table
      → Server-side merge computed; both values retained

Step 5: Atomic Batch Commit
  All accepted writes committed as a single transaction
  If any write fails: Full batch rolled back; client notified to retry
  No partial commits permitted

Step 6: Conflict Notification to User
  At next user login: Summary of resolved conflicts displayed
  User can view: What changed, which version was applied, audit trail
  Inventory conflicts: User presented with diff and must confirm resolution before dashboard loads

Step 7: Post-Sync Audit
  Sync completion event logged with record count, conflict count, resolution types
  Any manual-resolution items remain in pending state until user confirms
```

---

### 12.8 New Feature Deployment Workflow (CI/CD with Phase Gate Control)

**Applicable to:** Engineering team on all deployments

```
Step 1: Development
  Engineer: Feature developed on feature branch
  Unit tests: Coverage ≥80% required before PR merge
  Security scan: SAST tool runs on PR; critical findings block merge

Step 2: Code Review & Merge
  Peer review: ≥1 senior engineer sign-off required
  Merge to main: Triggers CI pipeline

Step 3: CI Pipeline (Automated)
  → Unit tests
  → Integration tests (against staging database)
  → Container build (Docker)
  → SAST security scan
  → Dependency vulnerability scan
  → Compliance check: Rate table changes require compliance officer sign-off
  → If all pass: Artefact pushed to container registry

Step 4: Staging Deployment (ArgoCD)
  → ArgoCD deploys to staging environment
  → Smoke tests run against staging
  → NLP resolution rate validated on test query set
  → Tax computation validated against GRA test cases

Step 5: Performance Testing (for significant changes)
  → Load test run at 200 concurrent users (Gate 1 baseline)
  → p95 API response time must be <500ms under test load
  → Results reviewed by SRE lead

Step 6: Production Deployment (Rolling Update)
  → ArgoCD applies rolling update strategy via Kubernetes
  → Old pods kept alive until new pods pass readiness probes
  → Zero-downtime deployment confirmed
  → Rate table changes deployed as data-only update (no pod restart required)

Step 7: Post-Deployment Monitoring
  → Datadog monitors: Error rate, API latency, NLP resolution rate
  → Alerting: Error rate >1% triggers PagerDuty page to on-call engineer
  → 30-minute elevated monitoring window post-deployment
  → Certificate expiry checks: Confirm no certificate changes caused pinning issues

Step 8: Phase Gate Compliance Check (at gate milestones)
  Product manager: Verifies all gate criteria against telemetry and documented evidence
  QA: Confirms MVP feature completeness percentage
  Security: Confirms zero critical findings from latest penetration test
  Compliance: Confirms DPC registration, GRA certification status
  Gate decision: Go / No-Go documented with supporting evidence
```

---

## 13. Phase Gate Requirements & Go/No-Go Criteria

### Gate 1 — Phase 1 → Phase 2 (Month 6)

| Criterion | Threshold | Evidence Required | Owner |
|-----------|-----------|------------------|-------|
| MVP feature completeness | ≥80% of defined core features passing acceptance testing | QA completion report | Product Manager |
| Security audit | Zero critical findings; all high findings remediated or risk-accepted | External penetration test report | CTO / Security Lead |
| Partnership letters of intent | ≥2 signed LOIs (at least 1 telco or bank) | Signed LOI documents | CEO / Partnerships |
| Data Protection Commission registration | Registration confirmed | DPC registration certificate | Compliance Officer |
| API performance baseline | API p95 <500ms under 200 concurrent users | Load test report | SRE Lead |
| GRA Certified Tax Software registration initiated | Application submitted | GRA submission acknowledgement | Compliance Officer |
| MTN MoMo API commercial agreement | Agreement signed or in final negotiation | Signed agreement or term sheet | Technical Lead |

### Gate 2 — Phase 2 → Phase 3 (Month 12)

| Criterion | Threshold | Evidence Required | Owner |
|-----------|-----------|------------------|-------|
| Registered pilot users | ≥5,000 | Platform analytics dashboard | Product Manager |
| Paying subscribers | ≥500 | Revenue report | Finance |
| NLP query resolution rate | ≥70% without human escalation | NLP service logs | ML Engineering Lead |
| GRA submission success rate | ≥95% successful submissions in pilot | Compliance module logs | Compliance Officer |
| Monthly churn (pilot cohort) | ≤10% | Subscription analytics | Product Manager |
| Net Promoter Score | ≥30 | User survey results | Customer Success |
| Multilingual NLP expansion (Ga, Ewe) | Production text; beta voice | NLP evaluation report | ML Lead |

### Gate 3 — Phase 3 → Phase 4 (Month 24)

| Criterion | Threshold | Evidence Required | Owner |
|-----------|-----------|------------------|-------|
| Registered users | ≥150,000 nationally | Platform analytics | Product Manager |
| Paying subscribers | ≥15,000 | Revenue report | Finance |
| National region coverage | All 16 regions with ≥50 active paying users each | Regional dashboard | Regional Ops Managers |
| ISO 27001 progress | Stage 1 audit completed; gap remediation in execution | ISO 27001 Stage 1 audit report | Security Lead |
| API uptime | ≥99.5% over trailing 90 days | Datadog SLA report | SRE Lead |
| Infrastructure scaling | 2M daily transactions; 25,000 concurrent users | Load test and production metrics | SRE Lead |

### Gate 4 — Phase 4 → Phase 5 (Month 36)

| Criterion | Threshold | Evidence Required | Owner |
|-----------|-----------|------------------|-------|
| Active B2B API partners | ≥5 live integrations | Partner dashboard | Partnerships |
| ARR run rate | ≥GHS 15,000,000 (~$1M USD) | Finance report | CFO |
| LTV/CAC ratio | ≥3x across Growth and Professional tiers | Unit economics model | Finance |
| Gross margin | ≥75% | P&L statement | CFO |
| Country entry readiness | ≥1 target market regulatory assessment complete | Legal memo | Legal Counsel |
| ISO 27001 certification status | Certification achieved or Stage 2 audit in progress | Certification / audit documentation | Security Lead |

---

## 14. Non-Functional Requirements

### 14.1 Performance

| Requirement ID | Requirement | Target |
|---------------|-------------|--------|
| NFR-PERF-001 | API response time (p95) under normal load | <500ms (Gate 1); scalable to production load at Gate 3 |
| NFR-PERF-002 | NLP simple query resolution time | <500ms (Haiku model path) |
| NFR-PERF-003 | NLP complex advisory query resolution time | <3–5 seconds (Sonnet model path) |
| NFR-PERF-004 | Voice query end-to-end resolution (speech end to audio response start) | <3s (simple); <7s (complex) |
| NFR-PERF-005 | Mobile money transaction sync latency | <2 minutes |
| NFR-PERF-006 | PWA core dashboard load on 2G connection | <8 seconds |
| NFR-PERF-007 | Concurrent user capacity | 1,000 (Phase 2); 25,000 (Phase 3) |
| NFR-PERF-008 | Daily transaction processing capacity | 50,000 (Phase 2); 2,000,000 (Phase 3) |

### 14.2 Reliability & Availability

| Requirement ID | Requirement | Target |
|---------------|-------------|--------|
| NFR-REL-001 | System uptime (overall platform) | 99.9% |
| NFR-REL-002 | API uptime (trailing 90 days, Gate 3 criterion) | ≥99.5% |
| NFR-REL-003 | Transaction Engine RTO | ≤15 minutes |
| NFR-REL-004 | Transaction Engine RPO | 0 minutes (synchronous replication) |
| NFR-REL-005 | Zero expired TLS certificates in production | Mandatory operational KPI |
| NFR-REL-006 | Kong API Gateway single-instance SPOF risk | Eliminated by HA cluster (3 instances min) |

### 14.3 Scalability

| Requirement ID | Requirement | Target |
|---------------|-------------|--------|
| NFR-SCA-001 | Auto-scaling in response to load spikes | Kubernetes HPA configured; scale-out within 3 minutes of threshold breach |
| NFR-SCA-002 | Data storage scaling | 500 GB (Phase 2) → 10 TB (Phase 3) |
| NFR-SCA-003 | API call handling | 100,000/day (Phase 2) → 5,000,000/day (Phase 3) |

### 14.4 Maintainability

| Requirement ID | Requirement | Target |
|---------------|-------------|--------|
| NFR-MAI-001 | Tax rate changes must not require code deployment | Rate table update is the only required change; tested in staging before production |
| NFR-MAI-002 | Model versioning and experiment tracking | MLflow operational; all deployed models tracked with version, training date, and evaluation metrics |
| NFR-MAI-003 | Infrastructure as Code | All infrastructure defined in Terraform; all deployments via ArgoCD; no manual infrastructure changes |
| NFR-MAI-004 | Zero-downtime deployments | Rolling update strategy via Kubernetes; no downtime on any deployment |

### 14.5 Observability

| Requirement ID | Requirement | Target |
|---------------|-------------|--------|
| NFR-OBS-001 | Centralized observability platform | Datadog; all services instrumented |
| NFR-OBS-002 | Infrastructure metrics (InfluxDB) | API latency, Kafka throughput, Kubernetes pod metrics, DB query performance, error rates |
| NFR-OBS-003 | Business metrics (TimescaleDB) | Cash flow, revenue trends, user activity — linked to transaction records |
| NFR-OBS-004 | NLP resolution rate monitoring | Real-time dashboard; daily report; alert if rate drops below threshold |
| NFR-OBS-005 | Bias drift monitoring | Real-time disparity dashboards; automated alert on threshold breach |
| NFR-OBS-006 | DR test results tracking | Annual drill results documented and CTO-reviewed |

---

## 15. Implementation Constraints & Dependencies

### 15.1 Long Lead-Time External Dependencies

These must be initiated at Week 1 of Phase 1. Failure to initiate these in parallel with technical development will create critical-path delays.

| Dependency | Estimated Lead Time | Initiate By | Risk if Delayed |
|------------|--------------------|-----------|-----------------| 
| GRA API access & Certified Tax Software registration | 3–6 months | Week 1 | VAT filing feature cannot go live; Gate 1 criterion jeopardized |
| MTN MoMo & Vodafone Cash API commercial agreements | 2–4 months | Week 1 | Core transaction sync blocked; fundamental product capability at risk |
| Data Protection Commission registration | 4–8 weeks | Week 1 | Gate 1 criterion; operating without registration is a regulatory violation |
| Bank of Ghana licensing consultation | 3–6 months | Week 2 | E-money licensing requirements unclear; financial services feature scope undefined |
| SSNIT API access | 2–4 months | Week 3 | Payroll compliance module delayed; Gate 2 feature completeness at risk |
| NCA USSD licensing (number range) | 2–3 months | Week 4 | USSD channel unavailable at launch; low-connectivity users underserved |

### 15.2 Technology Constraints

| Constraint | Specification | Implication |
|------------|--------------|-------------|
| Mobile framework | React Native (Expo) exclusively; no native Kotlin/Swift | All mobile developers must have React Native expertise; native bridging used only where unavoidable |
| Claude model versions | `claude-sonnet-4-6` (complex); `claude-haiku-4-5-20251001` (simple) — pinned | Model versions reviewed and updated at each major release cycle; breaking changes assessed |
| Vector database | Pinecone gated on DPIA; pgvector is production-safe default | Pinecone not deployed until DPIA concludes adequacy; pgvector must be ready at MVP |
| Primary cloud region | AWS Africa (Cape Town, af-south-1) | All primary data residency in Cape Town; cross-region replication to eu-west-1 for DR only |
| API Gateway | Kong — HA cluster (minimum 3 instances), PostgreSQL-backed | Single-instance Kong deployment is not acceptable; HA topology required from Phase 1 |

### 15.3 Hiring Constraints

ML Engineers and Compliance Specialists carry 3–5 month hiring lead times in the Ghana market. These roles must begin recruitment during Phase 1 for Phase 2 readiness.

| Critical Hire | Hiring Lead Time | Required By |
|--------------|-----------------|-------------|
| ML Engineers (Phase 3 expansion) | 3–5 months | Must recruit in Phase 2 for Phase 3 readiness |
| Compliance Specialists (expanding regulatory scope) | 3–5 months | Must recruit in Phase 2 for Phase 3 national coverage |
| Regional Operations Managers (3 required in Phase 3) | 2–3 months | Must recruit in Phase 2 Q2 |

### 15.4 Data Accuracy & Version Control Obligations

| Constraint | Requirement |
|------------|-------------|
| VAT/CST rate accuracy | Rates must be verified against current GRA Finance Act publication before every release; verification sign-off required from compliance officer; stored in configuration tables only |
| Claude model version identifiers | Model strings (`claude-sonnet-4-6`, `claude-haiku-4-5-20251001`) must be reviewed at every major release cycle; breaking API changes must be assessed before version pinning is updated |
| GEA naming | The agency is referred to exclusively as "Ghana Enterprises Agency (GEA)" in all platform text and documentation; prior naming "NBSSI" must not appear in any user-facing surface |
| Kenya classification | Kenya is an East African Community (EAC) member; Phase 5 documentation and regulatory planning must use "East Africa Track" nomenclature, not ECOWAS |

---

*End of Document — BizPulse AI Comprehensive Requirements Breakdown*

*This document is a living reference. It must be updated at each phase gate to reflect completed, modified, or newly identified requirements. All changes require review sign-off from the Technical Lead, Product Manager, and Compliance Officer.*

*Based on: BizPulse AI Technical Specification v1.1 — March 2026*
