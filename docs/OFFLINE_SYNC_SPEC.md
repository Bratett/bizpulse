# OFFLINE_SYNC_SPEC.md

## 1. Purpose

This document defines the canonical offline-first and synchronization behavior for BizPulse mobile and low-connectivity client surfaces. It is the implementation reference for local storage, sync orchestration, conflict handling, reconnect semantics, quota rules, integrity checks, observability, and test requirements.

This specification is binding for:
- React Native mobile clients
- PWA features that support degraded or cached operation
- Backend sync endpoints and reconciliation workflows
- Notification and USSD fallback interactions that must remain usable during intermittent connectivity

This document complements:
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/API_CONTRACT.md`
- `docs/SECURITY_BASELINE.md`
- `docs/INTEGRATION_MANIFEST.md`

---

## 2. Goals

BizPulse is designed for users operating in environments with unreliable, slow, or expensive connectivity. Offline operation is therefore a product requirement, not a convenience feature.

The offline system must:
- preserve user productivity during connectivity loss
- maintain a fully functional local working state on device for supported features
- queue mutations safely until connectivity is restored
- reconcile without silent data corruption
- enforce idempotent server-side writes
- protect financial integrity and auditability
- degrade gracefully across mobile, PWA, USSD, and SMS-supported workflows

---

## 3. Non-Negotiable Rules

The following are platform rules and must not be overridden without a formal ADR:

1. **Offline-first is mandatory.** All mobile features must degrade gracefully without connectivity.
2. **Local store on device is SQLite with encrypted WAL.**
3. **Sync protocol is queue-based delta sync with server-side idempotency keys.**
4. **Financial transactions are append-only.** No overwrite and no delete semantics are allowed in normal sync paths.
5. **Conflict resolution is defined per data type, not globally.**
6. **Full checksum reconciliation is required before merge commit on reconnect.**
7. **Maximum offline duration is tier-bound:**
   - Free/Starter tier: 7 days
   - Standard/Growth and above: 30 days
8. **Local device storage budgets are tier-bound:**
   - Starter: 200 MB
   - Growth/Professional: 500 MB
   - Enterprise: 1 GB
9. **All mutation APIs participating in sync must enforce idempotency keys.**
10. **Redis is not a source of truth.** Offline sync durability lives in client SQLite and server-side PostgreSQL-backed records.

---

## 4. Scope by Channel

### 4.1 Mobile App (React Native)

The mobile app is the primary offline-capable rich client.

Required behaviors:
- full local persistence for supported entities
- local read/write while disconnected
- background sync when connectivity returns
- resumable upload/download batches
- conflict surfacing for data types that require manual intervention
- encrypted local database and secure credential handling

### 4.2 PWA (Next.js)

The PWA is not expected to match full native offline depth, but it must still degrade gracefully.

Required minimum behaviors:
- cache last-known dashboards and recently accessed records where safe
- queue low-risk drafts when feasible
- block unsupported sensitive mutations with explicit messaging rather than failing silently
- respect device/network capability constraints
- meet the low-bandwidth target for core dashboard load on 2G

### 4.3 USSD / SMS

USSD is a low-connectivity access channel, not a general offline datastore. It cannot provide persistent local state, but it must support continuity when richer channels are unavailable.

Required behaviors:
- route primary USSD/SMS traffic through direct telco integrations
- automatically fail over to Africa's Talking when primary gateway health triggers failover
- normalize delivery/status callbacks into the same internal notification schema
- preserve business continuity for essential low-data operations when app/PWA are not viable

---

## 5. Supported Offline Capability Classes

Not every feature has the same offline behavior. Each product capability must be classified before implementation.

### Class A — Full Offline Create/Read/Update

Use for entities where local drafting/editing is safe and can reconcile deterministically.

Examples:
- business profile drafts
- customer records
- expense capture drafts
- notes and workflow tasks
- settings screens with low security sensitivity

### Class B — Offline Read + Queued Mutation

Use where local mutation is allowed, but server validation is authoritative.

Examples:
- invoice drafts pending numbering/validation
- inventory adjustments
- tax input drafts
- transaction tagging or categorization changes

### Class C — Offline Read Only

Use where mutation without server confirmation would create risk.

Examples:
- finalized filings
- compliance submissions
- external-provider settlement states
- some approval workflows

### Class D — Connectivity Required

Use sparingly and only when required by compliance, identity assurance, or external dependency semantics.

Examples:
- MFA enrollment/reset
- regulated submission finalization
- some payment initiation steps
- external account linking flows

---

## 6. Local Data Architecture

### 6.1 Local Storage Engine

Mobile clients must use SQLite with encrypted WAL journaling.

Requirements:
- database encryption enabled at rest on device
- WAL mode enabled for crash resilience and concurrent access patterns
- schema version tracked explicitly
- migration scripts versioned and reversible where practical
- local records include sync metadata fields

### 6.2 Required Local Metadata Per Synced Record

Every locally stored synced entity must carry, at minimum:
- `local_id`
- `server_id` (nullable until server assignment)
- `tenant_id`
- `entity_type`
- `local_version`
- `server_version` (last known)
- `sync_status`
- `updated_at_local`
- `updated_at_server_last_known`
- `idempotency_key` for pending mutation, where applicable
- `checksum_hash`
- `deleted_tombstone` flag where tombstones are allowed
- `conflict_state` if reconciliation requires attention

### 6.3 Local Queue Tables

The client must maintain explicit durable local queues, not ad hoc in-memory retry lists.

Minimum queue tables:
- `sync_outbox`
- `sync_inbox_cursor`
- `conflict_queue`
- `attachment_transfer_queue`
- `device_sync_state`

### 6.4 File and Attachment Strategy

Attachments must not be treated the same as structured records.

Rules:
- store attachment metadata separately from binary payload state
- support resumable transfer where feasible
- enforce size ceilings by subscription tier and device budget
- checksum files independently from parent record payloads
- preserve version history for documents rather than mutating in place

---

## 7. Sync Model

### 7.1 Canonical Protocol

BizPulse uses a **queue-based delta sync protocol with server-side idempotency keys**.

The sync model has two independent flows:
- **Outbound sync:** client-created mutations are drained from local outbox to server
- **Inbound sync:** server-side deltas since the client cursor are fetched and applied locally

The system must not require full database replacement except in recovery scenarios.

### 7.2 Sync Unit

The smallest sync unit is a **mutation envelope** or **delta envelope**, not a whole table.

Each outbound mutation envelope should include:
- entity type
- operation type
- tenant scope
- actor/device metadata
- idempotency key
- payload
- local base version
- client timestamp
- checksum/hash

### 7.3 High-Level Sync Sequence

1. Client detects connectivity restoration.
2. Client acquires sync lease locally to avoid duplicate concurrent sync runs.
3. Client verifies auth/session validity.
4. Client uploads pending outbound mutations in ordered batches.
5. Server processes each mutation idempotently.
6. Server returns per-item results: accepted, rejected, conflict, duplicate, deferred.
7. Client updates local outbox and entity states.
8. Client requests inbound deltas since last successful cursor.
9. Client applies deltas to local store.
10. Client runs checksum reconciliation.
11. If checksums pass, client commits sync watermark.
12. If checksums fail, client enters reconciliation flow and blocks final merge commit for affected entities.

### 7.4 Ordering Rules

Ordering matters for some entity families.

Required ordering behavior:
- preserve causal order within a record stream
- upload dependent parent records before child records when dependency exists
- group append-only financial events by account or ledger stream where necessary
- permit safe parallelism only across independent entity partitions

---

## 8. Sync State Machine

Each locally mutable record must use an explicit sync state.

Minimum states:
- `LOCAL_ONLY`
- `PENDING_UPLOAD`
- `IN_FLIGHT`
- `SYNCED`
- `SYNCED_WITH_REMOTE_UPDATE`
- `CONFLICT`
- `REJECTED`
- `REQUIRES_REAUTH`
- `EXPIRED_OFFLINE_WINDOW`

### 8.1 Transition Rules

- `LOCAL_ONLY` → `PENDING_UPLOAD` when user commits local change
- `PENDING_UPLOAD` → `IN_FLIGHT` when sync worker submits batch
- `IN_FLIGHT` → `SYNCED` on successful acceptance
- `IN_FLIGHT` → `CONFLICT` when server detects version/data conflict
- `IN_FLIGHT` → `REJECTED` when mutation fails validation/business rule checks
- any sync-capable state → `REQUIRES_REAUTH` when token/session prevents safe sync
- any local state → `EXPIRED_OFFLINE_WINDOW` when plan-specific offline duration exceeded

---

## 9. Conflict Resolution Matrix

Conflict resolution is **per data type**, and this rule is already locked in the implementation specification.

### 9.1 Financial Transactions

**Policy:** Append-only

Rules:
- never overwrite a prior financial event to resolve conflict
- submit compensating or reversing entries if correction is required
- preserve immutable audit trail
- duplicates must be detected by idempotency key and domain duplicate guards
- server is authoritative for ledger ordering and final accepted event sequence

### 9.2 Settings

**Policy:** Last-Write-Wins (LWW)

Rules:
- acceptable only for low-risk settings data
- both timestamps and actor/device metadata should be retained for audit visibility
- use server-accepted write timestamp as final arbitration source where needed

### 9.3 Inventory Counts

**Policy:** Manual resolution prompt

Rules:
- conflicting inventory counts must not auto-merge silently
- show local value, remote value, timestamps, and actor context
- require explicit user choice or supervised merge workflow
- preserve decision audit log

### 9.4 Tax Inputs

**Policy:** Merge with audit log

Rules:
- merge field-level changes where safe
- preserve source provenance of each merged field
- maintain audit trail of pre-merge and post-merge states
- do not hardcode tax logic or rates in merge routines

### 9.5 Documents

**Policy:** Version history

Rules:
- conflicting edits create new versions rather than destructive overwrite
- retain lineage between document versions
- support user-visible recovery and comparison flows where relevant

### 9.6 Reference Table

| Data Type | Conflict Policy | Auto-Resolve Allowed | Audit Required |
|---|---|---:|---:|
| Financial transactions | Append-only | No | Yes |
| Settings | Last-Write-Wins | Yes | Yes |
| Inventory counts | Manual resolution prompt | No | Yes |
| Tax inputs | Merge with audit log | Partial | Yes |
| Documents | Version history | Partial | Yes |

---

## 10. Idempotency Requirements

Server-side idempotency is mandatory for all sync mutation APIs.

### 10.1 Key Rules

- every mutation envelope must include an idempotency key
- server stores idempotency outcome in durable store
- duplicate retries must return the original result or equivalent safe response
- idempotency windows must outlast realistic client retry behavior
- idempotency records must be tenant-scoped and endpoint-scoped where appropriate

### 10.2 Client Rules

- never regenerate a new idempotency key for the same logical mutation retry
- generate a new key only when the user intentionally creates a new logical action
- persist keys in local SQLite until terminal server outcome is known

---

## 11. Integrity and Reconciliation

### 11.1 Checksum Requirement

The platform requires **full checksum reconciliation before merge commit** on reconnect.

This means:
- sync is not considered fully committed merely because HTTP requests succeeded
- client and server must compare computed integrity references for synchronized data segments
- checksum mismatch triggers reconciliation workflow for affected scope

### 11.2 Reconciliation Levels

Reconciliation may occur at multiple levels:
- record level
- entity-stream level
- account/ledger partition level
- attachment/file level
- sync batch level

### 11.3 Mismatch Handling

On checksum mismatch:
1. mark affected scope as reconciliation-required
2. avoid destructive overwrite of local store
3. fetch authoritative deltas or snapshot for affected scope
4. re-run merge using policy for relevant data type
5. emit observability event and retain forensic evidence

---

## 12. Offline Window and Data Retention on Device

### 12.1 Maximum Offline Duration

The device may continue to function locally beyond the window, but sync behavior must enforce plan rules.

| Tier | Maximum Offline Duration |
|---|---|
| Starter / Free | 7 days |
| Standard / Growth / Professional | 30 days |
| Enterprise | 30 days unless contract-specific override is approved |

### 12.2 Behavior on Expiry

When the allowed offline window is exceeded:
- block further high-risk mutable actions until successful re-sync
- permit limited read access where safe
- preserve unsynced data locally
- surface clear user action guidance
- do not silently discard pending records

### 12.3 Device Storage Budget

| Tier | Local Device Storage Budget |
|---|---:|
| Starter | 200 MB |
| Growth / Professional | 500 MB |
| Enterprise | 1 GB |

When approaching budget ceilings:
- prioritize metadata over bulky attachments
- evict re-downloadable cached views before durable unsynced content
- compress or defer non-critical media
- prompt user before large offline downloads

---

## 13. Network and Retry Strategy

### 13.1 Client Sync Retry

Client sync retries should use bounded exponential backoff with jitter and awareness of connectivity class changes.

Rules:
- do not hammer network on unstable mobile data
- suspend aggressive retries while device is explicitly offline
- resume quickly on confirmed reconnection
- surface stale-sync status when thresholds are exceeded

### 13.2 Server-Side Upstream Dependencies

Sync success for local data must be decoupled from unstable upstream providers wherever possible.

Rules:
- accept local authoritative business events first when domain-safe
- enqueue outbound provider calls through Asynq for rate-limited upstream integrations
- do not block every client sync on external provider immediacy
- represent external follow-up state separately from local event acceptance where domain semantics allow

This is especially important for GRA, MoMo, Vodafone Cash, bank feeds, and other rate-limited providers.

---

## 14. Authentication and Session Handling During Sync

### 14.1 Auth Expectations

- gateway-validated JWT remains the API auth mechanism
- short-lived tokens are expected
- clients must support token refresh before long sync sessions
- failed refresh must transition pending work into `REQUIRES_REAUTH`, not drop queues

### 14.2 Tenant Safety

- every local record and queued mutation must carry tenant scope
- sync endpoints must reject cross-tenant leakage or ambiguous tenant context
- device caches must be wiped or cryptographically isolated on tenant/account switch

---

## 15. Error Classes and User Experience

### 15.1 Error Categories

Sync outcomes must distinguish between:
- transient network failure
- authentication/session failure
- validation error
- business rule rejection
- duplicate/idempotent replay
- conflict requiring user action
- checksum mismatch / reconciliation required
- offline window expired
- local storage budget exceeded

### 15.2 UX Principles

- never present a generic “sync failed” without actionable state
- show pending count and last successful sync timestamp
- show entity-level conflict badges where relevant
- allow users to continue safe work even when some items are blocked
- never imply a provider-side action completed if it is only queued internally

---

## 16. API Contract Requirements

The following endpoint families must exist in machine-readable contracts and be summarized in `API_CONTRACT.md`:

1. `POST /sync/outbox/batch`
2. `GET /sync/inbox/deltas`
3. `POST /sync/reconcile/checksum`
4. `POST /sync/conflicts/{id}/resolve`
5. `GET /sync/state`
6. `POST /sync/attachments/upload-session`
7. `GET /sync/bootstrap`

### 16.1 Outbound Batch Response Semantics

Per-item result codes should include at least:
- `accepted`
- `duplicate`
- `conflict`
- `rejected_validation`
- `rejected_business_rule`
- `deferred`

### 16.2 Inbound Delta Requirements

Inbound delta responses must support:
- cursor-based retrieval
- pagination
- per-entity version metadata
- tombstones where allowed
- optional scoped rehydration for reconciliation repair

---

## 17. Observability and Auditability

### 17.1 Metrics

Required metrics include:
- sync success rate
- average sync latency
- outbox depth per device
- conflict rate by entity type
- checksum mismatch rate
- offline-window-expiry count
- attachment retry rate
- reauth-required sync failures
- USSD fallback activation count where relevant for continuity metrics

### 17.2 Logs

Structured logs must include:
- tenant identifier or safe surrogate
- device/session identifier
- sync batch identifier
- idempotency key or surrogate reference
- entity type
- result status
- retry count
- reconciliation trigger indicators

### 17.3 Audit

The platform must preserve evidence for:
- manual conflict decisions
- tax-input merge provenance
- document version branching
- transaction duplicate suppression outcomes
- offline window enforcement

---

## 18. Security Requirements Specific to Offline Operation

- local SQLite database must be encrypted
- WAL and temp files must not leak plaintext-sensitive data
- device logout must clear or cryptographically orphan protected local data
- attachments containing regulated or sensitive information must respect download policy
- integrity checks must be tamper-aware where feasible
- no secrets may be stored in plaintext local preferences
- cached auth material must follow mobile platform secure storage practices

---

## 19. Test Strategy

Offline sync is safety-critical and must not be validated with happy-path tests alone.

### 19.1 Minimum Automated Test Categories

1. local queue durability after app crash
2. repeated retry with same idempotency key
3. reconnect after long offline period
4. checksum mismatch reconciliation
5. out-of-order delta application resistance
6. manual inventory conflict path
7. append-only financial conflict handling
8. tax-input merge correctness with audit trail
9. document version branching on conflict
10. token expiry mid-sync
11. storage budget pressure behavior
12. tenant switch cache isolation
13. attachment partial upload resume
14. USSD/SMS continuity metrics under telco failover where relevant

### 19.2 Non-Functional Tests

- degraded network simulation: 2G, packet loss, intermittent disconnects
- soak test with large outbox accumulation
- corruption recovery test for local store and WAL journal
- concurrency test with multiple local edits before reconnect
- replay/idempotency storm test

---

## 20. Delivery Order and Phase Guidance

### Phase 1 Minimum

Must exist before Gate 1 completion:
- local SQLite schema and encrypted WAL setup
- durable outbox/inbox cursor tables
- sync batch endpoints with idempotency support
- checksum reconciliation flow
- per-data-type conflict engine skeleton
- append-only transaction handling
- settings LWW handling
- inventory manual conflict flow
- tax merge audit log path
- document version branching path
- offline window enforcement
- core observability dashboards

### Phase 2 Enhancements

- richer PWA offline/degraded support
- attachment resumability improvements
- more advanced conflict UX
- Expo OTA update-safe migration handling

### Phase 3+

- scale tuning for large fleet/device populations
- advanced selective sync policies
- deeper partner-state decoupling and recovery tooling

---

## 21. Open ADR Candidates

Raise an ADR before implementation if any of the following change:
- replacing SQLite or encrypted WAL approach
- changing checksum strategy or merge-commit semantics
- introducing global LWW across all entities
- allowing destructive overwrite of financial events
- changing plan-based offline duration caps
- introducing third-party sync middleware as a source of truth
- widening PWA offline mutation classes for regulated workflows

---

## 22. Summary of Locked Decisions

The following are already locked by the uploaded specifications and are reflected here:
- offline-first is a core differentiator and implementation requirement
- mobile local store is SQLite with encrypted WAL
- sync uses queue-based delta protocol with server-side idempotency keys
- financial transactions are append-only
- conflict strategy is per data type
- conflict matrix is: financial transactions append-only, settings LWW, inventory manual prompt, tax inputs merge with audit log, documents version history
- checksum reconciliation is required before merge commit
- offline duration and storage budgets are tier-specific
- USSD is a primary continuity channel for low-connectivity users, with automatic fallback to Africa's Talking when primary telco routing fails

