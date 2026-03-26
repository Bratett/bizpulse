# API_CONTRACT.md

## BizPulse AI — Canonical API Contract Reference

**Document Type:** Human-readable API contract baseline + OpenAPI/Avro generation guide  
**Status:** Authoritative working reference for Phase 1 and subsequent service sprints  
**Primary Use:** Endpoint design, auth boundary enforcement, webhook normalization, async workflow design, OpenAPI generation, contract testing

---

## 1. Purpose

This document defines the canonical API contract layer for BizPulse AI. It sits between `ARCHITECTURE.md` and machine-readable interface files such as OpenAPI 3.0 YAML, Avro IDL, and generated SDKs.

It is intended to ensure that all service-to-client, service-to-service, webhook, and event contracts are:

- consistent across channels and microservices
- aligned with BizPulse architectural decisions
- compatible with offline-first and multi-channel delivery
- enforceable through contract tests and code generation
- explicit about authentication, idempotency, retries, and audit requirements

This document is not the final machine-readable specification. Instead, it is the **canonical human-readable source** from which the following artefacts should be produced:

- `openapi/public-api.yaml`
- `openapi/internal/*.yaml`
- `shared/avro/*.avdl`
- generated client SDKs in `shared/sdk/`
- Pact/contract test fixtures

---

## 2. Contract Principles

### 2.1 API style

BizPulse APIs use:

- **JSON over HTTPS** for synchronous APIs
- **REST-style resource design** for client-facing and administrative surfaces
- **command-oriented endpoints** where domain safety is more important than CRUD purity
- **Avro-typed Kafka events** for asynchronous workflows
- **XML payloads** only at external compliance boundaries where government schemas require them

### 2.2 Canonical design rules

1. **All APIs are versioned via URL path** using `/v1/`, `/v2/`, etc.
2. **Gateway-first enforcement** applies: Kong terminates edge auth, rate limiting, and routing.
3. **JWTs are validated at Kong**, not re-verified independently by every service except where zero-trust internal policy explicitly requires it.
4. **Financial writes are command-based and append-only.** Never design mutable “update transaction amount” endpoints.
5. **Idempotency is mandatory** for all write operations that can be retried by client, gateway, queue worker, or external provider.
6. **Async over sync** for rate-limited or slow upstream integrations. GRA, MoMo, bank feeds, Claude API, and similar upstream calls are queued through Asynq-backed job orchestration.
7. **Error envelopes are standardized** across all services.
8. **Timestamps use ISO 8601 / RFC 3339 UTC** unless a business-local timezone field is explicitly modeled.
9. **Monetary values use integer minor units** with explicit currency code.
10. **Sensitive fields are minimized in responses** and redacted in logs.

### 2.3 Contract hierarchy

When there is a conflict, the source of truth is:

1. statutory / vendor schema obligation (for example GRA XML)
2. approved ADR in `DECISIONS.md`
3. this document
4. service-local OpenAPI YAML
5. implementation code

---

## 3. API Surface Overview

BizPulse exposes four contract categories:

| Category | Audience | Transport | Primary Owner |
|---|---|---|---|
| Client APIs | Mobile app, PWA, admin UI, USSD orchestration, WhatsApp orchestration | HTTPS JSON | Gateway + domain service owners |
| Internal service APIs | Service-to-service calls inside trusted platform boundary | HTTPS JSON / gRPC only if later adopted by ADR | Service owners |
| External integration adapters | Upstream/downstream partner APIs and callback handlers | HTTPS JSON/XML, webhooks, file export | Integration-owning service |
| Event contracts | Internal async messages over Kafka | Avro | Domain event owners |

---

## 4. Bounded Service Contracts

### 4.1 Service inventory

| Service | Language | Core contract domains |
|---|---|---|
| `user-svc` | Go | identity profile, business membership, consent, subscriptions, device registration |
| `transaction-svc` | Go | transaction ingestion, ledger events, reconciliation, sync intake, inventory movements |
| `analytics-svc` | Python | forecasts, KPI aggregates, credit scores, statement generation requests/results |
| `compliance-svc` | Python | tax calculations, filing jobs, payroll compliance, rates configuration, audit evidence |
| `nlp-svc` | Python | multilingual query interpretation, assistant responses, intent classification, document query |
| `notification-svc` | Go | notification templates, outbound jobs, delivery status, callback normalization |
| `api-gateway` | Kong | auth enforcement, routing, throttling, request policy |

### 4.2 Public vs internal exposure

Only a subset of endpoints are user-facing. Internal-only APIs must not be exposed directly through public gateway routes unless explicitly approved.

| Exposure class | Description |
|---|---|
| Public | Callable by mobile, PWA, USSD orchestration layer, or WhatsApp orchestration layer |
| Protected internal | Callable only by trusted services via gateway/internal mesh policy |
| Admin internal | Restricted to operator/admin surfaces and support tooling |
| Partner callback | Exposed for signed webhook delivery from upstream providers |
| Batch/export | File-based or long-running job interface |

---

## 5. Common Request/Response Standards

### 5.1 Headers

Every request should support the following headers where applicable:

| Header | Required | Purpose |
|---|---|---|
| `Authorization: Bearer <token>` | public + internal user-context APIs | OIDC/JWT bearer token |
| `X-Request-Id` | yes | end-to-end trace correlation |
| `X-Correlation-Id` | recommended | cross-service workflow correlation |
| `Idempotency-Key` | mandatory for retryable writes | de-duplicate repeated writes |
| `X-Client-Version` | client apps | rollout support and debugging |
| `X-Device-Id` | mobile/offline flows | device-aware sync and security checks |
| `X-Business-Id` | multi-tenant scoped calls where not implied by path | explicit tenant context |
| `X-Signature` / provider-specific signature header | webhook callbacks | request authenticity verification |

### 5.2 Success envelope

For simple resource endpoints:

```json
{
  "data": {},
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-03-19T15:00:00Z"
  }
}
```

For list endpoints:

```json
{
  "data": [],
  "meta": {
    "request_id": "req_123",
    "page": 1,
    "page_size": 50,
    "next_cursor": "abc",
    "timestamp": "2026-03-19T15:00:00Z"
  }
}
```

### 5.3 Error envelope

All services must emit a standardized error body:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more fields are invalid.",
    "details": [
      {
        "field": "currency",
        "reason": "unsupported_value"
      }
    ],
    "retryable": false
  },
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-03-19T15:00:00Z"
  }
}
```

### 5.4 Standard error codes

| Code | Meaning | Retryable |
|---|---|---|
| `VALIDATION_ERROR` | Request shape or semantic validation failed | No |
| `UNAUTHORIZED` | Missing/invalid auth | No |
| `FORBIDDEN` | Authenticated but not allowed | No |
| `NOT_FOUND` | Resource not found | No |
| `CONFLICT` | Business-state collision or duplicate request | Sometimes |
| `IDEMPOTENCY_REPLAY` | Same idempotency key with same result | Safe replay |
| `RATE_LIMITED` | Throttled by gateway or provider shield | Yes |
| `UPSTREAM_UNAVAILABLE` | Partner/system dependency unavailable | Yes |
| `ASYNC_ACCEPTED` | Work queued; use job status endpoint | Poll |
| `SYNC_CONFLICT` | Offline merge conflict requiring UX resolution | No, requires client action |
| `COMPLIANCE_BLOCKED` | Action blocked by regulatory or policy guardrail | No |
| `INTERNAL_ERROR` | Unhandled service failure | Sometimes |

### 5.5 Pagination

Cursor pagination is preferred for transaction, notification, audit, and event-heavy resources. Page-number pagination is acceptable for stable admin lists.

### 5.6 Filtering and sorting

Use query parameters:

- `?cursor=...`
- `?limit=50`
- `?sort=-created_at`
- `?status=active`
- `?from=2026-03-01T00:00:00Z&to=2026-03-31T23:59:59Z`

### 5.7 Monetary representation

```json
{
  "amount_minor": 125000,
  "currency": "GHS"
}
```

Never expose floating-point monetary fields as authoritative values.

---

## 6. Authentication, Authorization, and Tenant Context

### 6.1 Identity model

- Keycloak is the identity provider.
- Kong validates JWTs at the gateway boundary.
- Verified claims are forwarded to internal services via trusted headers.
- Public APIs require OAuth 2.0 / OIDC bearer tokens.
- Server-to-server integrations may use OAuth client credentials or API keys where documented.

### 6.2 Required claims

At minimum, downstream services should be able to depend on:

- `sub`
- `business_ids`
- `roles`
- `scopes`
- `preferred_language`
- `device_trust_level` where applicable

### 6.3 Authorization model

Authorization decisions must be both:

- **role-aware** (owner/admin/accountant/cashier/etc.)
- **tenant-aware** (`business_id` scope)

### 6.4 Scope naming convention

Suggested scope format:

- `business:read`
- `business:write`
- `transactions:read`
- `transactions:write`
- `compliance:submit`
- `analytics:read`
- `notifications:read`
- `admin:support`

---

## 7. Idempotency, Concurrency, and Offline Guarantees

### 7.1 Idempotency policy

`Idempotency-Key` is mandatory on:

- transaction creation
- sync mutation batches
- filing submissions
- inventory adjustment commands
- payment initiation or settlement confirmation
- notification dispatch requests that could be retried

### 7.2 Idempotency behavior

If the same authenticated principal repeats the same key with an equivalent payload inside the retention window, the service returns the original result with `200`, `201`, or `202` and may include:

```json
{
  "meta": {
    "idempotent_replay": true
  }
}
```

If the same key is reused with a materially different payload, return `409 CONFLICT`.

### 7.3 Offline sync constraints

Offline-first behavior imposes API requirements:

- sync endpoints must accept batches of queued mutations
- each mutation must carry client mutation ID and idempotency key
- server must return per-item results, not only batch-level success/failure
- conflict responses must include enough data for user-facing merge UX
- append-only financial mutations are never overwritten during conflict resolution

---

## 8. Async Work Pattern

### 8.1 When to return 202 Accepted

Return `202 Accepted` when work is delegated to a queue or worker and not yet completed, especially for:

- GRA filing submission
- provider settlement sync
- statement generation
- OCR extraction
- long-running analytics jobs
- NLP jobs that require upstream model execution beyond synchronous SLA
- notification fan-out jobs

### 8.2 Job response shape

```json
{
  "data": {
    "job_id": "job_123",
    "status": "queued",
    "status_url": "/v1/jobs/job_123"
  },
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-03-19T15:00:00Z"
  }
}
```

### 8.3 Generic job states

- `queued`
- `processing`
- `retrying`
- `awaiting_provider`
- `completed`
- `failed`
- `dead_lettered`
- `cancelled`

### 8.4 Outbound provider call rule

No application service should directly issue business-critical synchronous upstream calls to GRA, MoMo, Vodafone Cash, bank feeds, or Anthropic in the request path when that call can be queued safely. Such work must be represented as a durable async job.

---

## 9. Client-Facing API Domains

## 9.1 User and identity APIs (`user-svc`)

Base path: `/v1/users`, `/v1/businesses`, `/v1/consents`, `/v1/subscriptions`, `/v1/devices`

### Primary endpoints

| Method | Path | Exposure | Purpose |
|---|---|---|---|
| `POST` | `/v1/auth/register` | public | assisted or self-service registration bootstrap |
| `GET` | `/v1/users/me` | public | current user profile |
| `PATCH` | `/v1/users/me` | public | profile update |
| `GET` | `/v1/businesses` | public | list businesses user belongs to |
| `POST` | `/v1/businesses` | public | create tenant/business |
| `GET` | `/v1/businesses/{business_id}` | public | get business profile |
| `PATCH` | `/v1/businesses/{business_id}` | public | update business settings/profile |
| `POST` | `/v1/businesses/{business_id}/members` | public/admin | invite/add member |
| `GET` | `/v1/businesses/{business_id}/members` | public/admin | membership list |
| `POST` | `/v1/consents` | public | capture consent |
| `GET` | `/v1/consents` | public | consent history |
| `POST` | `/v1/subscriptions/checkout` | public | start subscription checkout |
| `GET` | `/v1/subscriptions/current` | public | current plan/subscription |
| `POST` | `/v1/devices/register` | public | register mobile device |
| `POST` | `/v1/devices/{device_id}/trust` | protected internal | elevate trust via verification flow |

### Notes

- Consent capture must be append-only.
- Business membership operations must enforce tenant-admin role checks.
- PII updates should return redacted fields where appropriate.

## 9.2 Transaction and ledger APIs (`transaction-svc`)

Base path: `/v1/transactions`, `/v1/ledger`, `/v1/reconciliation`, `/v1/inventory`, `/v1/sync`

### Primary endpoints

| Method | Path | Exposure | Purpose |
|---|---|---|---|
| `POST` | `/v1/transactions` | public | create transaction command |
| `GET` | `/v1/transactions` | public | list transactions |
| `GET` | `/v1/transactions/{transaction_id}` | public | transaction detail |
| `POST` | `/v1/transactions/imports/mobile-money` | protected internal | enqueue provider import |
| `POST` | `/v1/transactions/imports/bank` | protected internal | enqueue bank import |
| `POST` | `/v1/ledger/entries:append` | protected internal | append ledger event |
| `GET` | `/v1/reconciliation/runs` | public/admin | reconciliation status list |
| `POST` | `/v1/reconciliation/runs` | public/admin | start reconciliation job |
| `POST` | `/v1/inventory/adjustments` | public | inventory change command |
| `GET` | `/v1/inventory/items` | public | list inventory items |
| `POST` | `/v1/sync/batches` | public | upload offline mutation batch |
| `GET` | `/v1/sync/batches/{batch_id}` | public | sync batch result |
| `POST` | `/v1/sync/checksum-verify` | public | pre-merge reconciliation/checksum validation |

### Transaction creation request (illustrative)

```json
{
  "business_id": "biz_123",
  "source": "manual",
  "occurred_at": "2026-03-19T10:30:00Z",
  "type": "expense",
  "amount_minor": 240000,
  "currency": "GHS",
  "category_code": "inventory_purchase",
  "counterparty": {
    "name": "Makola Supplier A"
  },
  "references": {
    "client_mutation_id": "mut_123"
  }
}
```

### Sync batch response pattern

```json
{
  "data": {
    "batch_id": "sync_123",
    "results": [
      {
        "client_mutation_id": "mut_1",
        "status": "applied",
        "server_resource_id": "txn_1"
      },
      {
        "client_mutation_id": "mut_2",
        "status": "conflict",
        "conflict_type": "inventory_count_conflict",
        "server_state": {},
        "client_state": {}
      }
    ]
  },
  "meta": {
    "request_id": "req_123"
  }
}
```

### Notes

- No `PUT /transactions/{id}` mutable update endpoint should exist for accounting facts.
- Imports from partners should almost always return `202` and a job resource.
- Inventory adjustments are commands; resulting stock projections are read models.

## 9.3 Analytics APIs (`analytics-svc`)

Base path: `/v1/analytics`, `/v1/forecasts`, `/v1/statements`, `/v1/credit-scores`

### Primary endpoints

| Method | Path | Exposure | Purpose |
|---|---|---|---|
| `GET` | `/v1/analytics/kpis` | public | dashboard KPIs |
| `GET` | `/v1/forecasts/cash-flow` | public | 30/60/90-day cash flow forecast |
| `GET` | `/v1/forecasts/demand` | public | demand/reorder forecast |
| `POST` | `/v1/statements/generate` | public/admin | enqueue statement generation |
| `GET` | `/v1/statements/{statement_id}` | public/admin | statement metadata/result |
| `GET` | `/v1/credit-scores/current` | public | latest business/user score view |
| `POST` | `/v1/credit-scores/recompute` | protected internal | force score recomputation |
| `GET` | `/v1/analytics/trends/revenue` | public | revenue trend series |

### Notes

- Forecast responses must include model timestamp and confidence metadata where available.
- Statement generation is async and returns job references if not immediately available.
- External lender-facing score APIs belong in a separately governed partner API package.

## 9.4 Compliance APIs (`compliance-svc`)

Base path: `/v1/compliance`, `/v1/filings`, `/v1/tax`, `/v1/payroll-compliance`, `/v1/compliance-rates`

### Primary endpoints

| Method | Path | Exposure | Purpose |
|---|---|---|---|
| `GET` | `/v1/tax/obligations` | public | current obligations and deadlines |
| `POST` | `/v1/tax/calculations` | public | calculate tax preview |
| `GET` | `/v1/compliance-rates` | protected internal/admin | active tax/rate configuration |
| `POST` | `/v1/filings/vat` | public/admin | queue VAT filing submission |
| `POST` | `/v1/filings/paye` | public/admin | queue PAYE submission |
| `GET` | `/v1/filings` | public/admin | filing history |
| `GET` | `/v1/filings/{filing_id}` | public/admin | filing detail + receipt state |
| `POST` | `/v1/payroll-compliance/runs` | public/admin | compute payroll obligations |
| `GET` | `/v1/compliance/audit-trail` | admin internal | audit evidence retrieval |

### Filing submission model

- filing requests return `202 Accepted`
- compliance service persists submission intent and audit context before outbound delivery
- external XML/file generation is internal implementation detail
- final receipts and acknowledgment references are retrievable from filing resource

## 9.5 NLP and assistant APIs (`nlp-svc`)

Base path: `/v1/assistant`, `/v1/nlp`, `/v1/documents/query`

### Primary endpoints

| Method | Path | Exposure | Purpose |
|---|---|---|---|
| `POST` | `/v1/assistant/query` | public | business assistant text query |
| `POST` | `/v1/assistant/query-voice` | public | voice query intake |
| `POST` | `/v1/nlp/intents:classify` | protected internal | intent classification |
| `POST` | `/v1/documents/query` | public/internal | semantic retrieval against approved corpora |
| `POST` | `/v1/assistant/feedback` | public | user feedback on response quality |

### Notes

- Responses that contain sensitive compliance or financial guidance should include source attribution metadata when available.
- Device-local conversation history that remains unsynced should not be inferred from server APIs.
- Model routing metadata should be internal by default.

## 9.6 Notification APIs (`notification-svc`)

Base path: `/v1/notifications`, `/v1/notification-jobs`, `/v1/provider-callbacks`

### Primary endpoints

| Method | Path | Exposure | Purpose |
|---|---|---|---|
| `POST` | `/v1/notifications/send` | protected internal | enqueue outbound notification |
| `GET` | `/v1/notifications` | public | user/business notification feed |
| `PATCH` | `/v1/notifications/{notification_id}/read` | public | mark read |
| `GET` | `/v1/notification-jobs/{job_id}` | protected internal/admin | delivery job state |
| `POST` | `/v1/provider-callbacks/sms` | partner callback | normalize SMS delivery receipts |
| `POST` | `/v1/provider-callbacks/whatsapp` | partner callback | normalize WhatsApp callbacks |
| `POST` | `/v1/provider-callbacks/momo` | partner callback | normalize payment/provider event |

### Notes

- provider callback routes must verify signatures, IP allowlists, or shared secret policies as applicable
- callback payloads are normalized into internal canonical event format before domain handling

---

## 10. Webhook and Callback Contract Model

### 10.1 General webhook rules

All webhook handlers must:

1. authenticate the sender
2. persist the raw payload for forensic/audit purposes where permitted
3. normalize to an internal canonical event
4. process idempotently using provider event IDs or derived dedupe keys
5. return fast acknowledgment when possible

### 10.2 Canonical callback envelope (internal normalized form)

```json
{
  "provider": "africas_talking",
  "provider_event_id": "evt_123",
  "event_type": "sms.delivery_report",
  "received_at": "2026-03-19T15:00:00Z",
  "correlation_keys": {
    "job_id": "job_123",
    "external_reference": "ext_456"
  },
  "payload": {}
}
```

### 10.3 In-scope callback families

- mobile money transaction status callbacks
- bank webhook/account activity callbacks where supported
- SMS delivery receipts from direct telco and Africa’s Talking fallback routes
- WhatsApp delivery/read/message callbacks
- GRA/SSNIT acknowledgment callbacks if/when available

---

## 11. Internal Service APIs

### 11.1 Internal call guidelines

Prefer events for decoupled workflows, but internal synchronous APIs are allowed when:

- immediate user response depends on current state read
- orchestration requires authoritative validation before command acceptance
- service dependency is stable and latency-bounded

### 11.2 Suggested internal-only endpoints

| Caller | Callee | Endpoint | Purpose |
|---|---|---|---|
| gateway/client flow | user-svc | `GET /internal/v1/tenants/{business_id}/membership/{user_id}` | tenant/role validation |
| compliance-svc | transaction-svc | `GET /internal/v1/transactions/summary` | tax calculation base data |
| analytics-svc | transaction-svc | `GET /internal/v1/ledger/projections/cashflow` | forecast input retrieval |
| notification-svc | user-svc | `GET /internal/v1/users/{id}/notification-preferences` | routing preferences |
| nlp-svc | analytics-svc | `GET /internal/v1/analytics/context` | structured context for grounded responses |

### 11.3 Internal auth

Internal APIs should require either:

- signed service token with service identity
- mTLS plus trusted gateway headers
- both, if required by later security ADR

---

## 12. Event Contract Model (Kafka / Avro)

### 12.1 Event design rules

All Kafka messages must use Avro schemas and include:

- globally unique event ID
- event type and schema version
- occurred timestamp in UTC
- producer service name
- tenant/business identifier when applicable
- idempotency key where event derives from a command/write
- trace correlation identifiers

### 12.2 Canonical event envelope

```json
{
  "event_id": "evt_123",
  "event_type": "transaction.recorded",
  "schema_version": 1,
  "occurred_at": "2026-03-19T15:00:00Z",
  "producer": "transaction-svc",
  "business_id": "biz_123",
  "idempotency_key": "idem_123",
  "correlation_id": "corr_123",
  "payload": {}
}
```

### 12.3 Priority topics

| Topic | Producer | Primary consumers | Purpose |
|---|---|---|---|
| `transactions.raw.recorded.v1` | transaction-svc | analytics-svc, compliance-svc | append-only source event |
| `transactions.enriched.v1` | Flink pipeline | analytics-svc, compliance-svc, nlp-svc | enriched transaction stream |
| `reconciliation.completed.v1` | transaction-svc | analytics-svc, compliance-svc, notification-svc | reconciliation outcome |
| `filings.submission.requested.v1` | compliance-svc | outbound worker/orchestrator | filing queue intent |
| `filings.submission.completed.v1` | compliance-svc | notification-svc, analytics-svc | filing result |
| `notifications.dispatch.requested.v1` | domain services | notification-svc | notification intent |
| `notifications.delivery.updated.v1` | notification-svc | user-svc, analytics-svc | delivery status |
| `assistant.query.logged.v1` | nlp-svc | analytics-svc | usage/quality telemetry |
| `credit_score.updated.v1` | analytics-svc | notification-svc, partner API layer | new score available |

### 12.4 Enrichment expectations

The enriched transaction event schema should support fields such as:

- merchant category
- normalized payment channel
- currency conversion fields
- geolocation or region tag where lawful and available
- settlement lag metadata
- reconciliation state

---

## 13. External Partner API and Export Boundaries

### 13.1 Mobile money and bank integrations

Integration style:

- outbound polling or job-triggered fetch
- webhook/callback ingestion where partner supports it
- provider-specific raw payload persisted for traceability
- normalized canonical transaction/advice schema inside platform

### 13.2 GRA and SSNIT

These are not ordinary REST integrations. Contract requirements include:

- XML/file generation against official schemas
- durable submission job state
- audit evidence retention
- receipt/acknowledgment attachment to filing resource
- fallback file export path when real-time API unavailable

### 13.3 Partner-facing future APIs

A future B2B/partner API surface for lenders or ecosystem integrators should be packaged separately and gated by:

- commercial agreement
- explicit consent model
- stricter rate limits and audit logging
- separate API key management and usage metering

---

## 14. Offline Sync API Contract Requirements

### 14.1 Required sync resources

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/sync/batches` | submit local mutation batch |
| `GET` | `/v1/sync/batches/{batch_id}` | retrieve server processing results |
| `POST` | `/v1/sync/checksum-verify` | validate divergence before merge |
| `GET` | `/v1/sync/bootstrap` | obtain baseline state/download manifest |
| `POST` | `/v1/sync/conflicts/{conflict_id}:resolve` | submit user-chosen conflict resolution for manual classes |

### 14.2 Mutation item contract

Every mutation item should include:

- `client_mutation_id`
- `entity_type`
- `operation`
- `payload`
- `occurred_at`
- `device_id`
- `idempotency_key`
- optional `base_version`

### 14.3 Conflict classes

| Data class | Expected API behavior |
|---|---|
| financial transactions | either applied or deduplicated; never overwritten |
| settings/profile | server applies LWW rule and returns effective state |
| inventory counts | returns `conflict` with both versions and diff summary |
| tax inputs | merge performed server-side with audit trace |
| documents | create new version rather than overwrite |

---

## 15. Rate Limiting and SLA Semantics

### 15.1 Gateway rate limiting

Kong should enforce tier-aware rate limits at the edge. Contract documentation for public APIs must include:

- burst limit
- sustained limit
- scope of limit (user, business, token, IP, client app)
- headers indicating remaining quota where appropriate

### 15.2 Timeout guidance

- interactive client requests should target low-latency responses
- long-running work should shift to `202 Accepted`
- callback handlers should acknowledge quickly and defer heavy processing

### 15.3 Retry hints

When returning retryable errors, include `Retry-After` where possible.

---

## 16. Contract Testing Requirements

### 16.1 Required test layers

Every API surface must be covered by:

- schema validation tests against OpenAPI
- consumer-driven contract tests for shared interfaces
- idempotency replay tests for retryable writes
- authz tests for tenant and role boundaries
- webhook signature verification tests
- offline conflict-resolution contract tests for sync APIs
- event schema compatibility tests for Avro evolution

### 16.2 Backward compatibility rules

Non-breaking changes:

- adding optional response fields
- adding new enum values only if consumers are documented to tolerate them
- adding new endpoints

Breaking changes:

- removing fields
- changing field type/meaning
- altering idempotency semantics
- changing callback signature requirements
- renaming event topics without migration plan

---

## 17. OpenAPI Package Structure Recommendation

```text
openapi/
├── public-api.yaml
├── internal/
│   ├── user-svc.yaml
│   ├── transaction-svc.yaml
│   ├── analytics-svc.yaml
│   ├── compliance-svc.yaml
│   ├── nlp-svc.yaml
│   └── notification-svc.yaml
└── components/
    ├── schemas.yaml
    ├── errors.yaml
    ├── security.yaml
    └── parameters.yaml
```

### 17.1 Shared component families

At minimum, centralize:

- `Money`
- `ErrorEnvelope`
- `PaginationMeta`
- `JobStatus`
- `ConsentRecord`
- `TransactionSummary`
- `ForecastPoint`
- `FilingStatus`
- `NotificationDeliveryStatus`
- `SyncMutationResult`

---

## 18. Initial OpenAPI / Avro Backlog

### 18.1 Phase 1 must-author contracts

1. `user-svc` public profile, business, consent, and subscription APIs
2. `transaction-svc` transaction create/list/detail and sync batch APIs
3. `compliance-svc` tax obligation, tax calculation, VAT filing enqueue/status APIs
4. `analytics-svc` KPI and cash-flow forecast read APIs
5. `notification-svc` send job + callback normalization APIs
6. Kafka Avro schemas for `transaction.recorded`, `transaction.enriched`, `filing.submission.requested`, `notification.dispatch.requested`

### 18.2 Phase 2 additions

- statement generation
- demand forecasting
- payroll compliance
- deeper MoMo/bank reconciliation workflows
- voice assistant APIs

### 18.3 Deferred until separate package/governance

- lender-facing third-party credit scoring API
- public developer platform/API monetization surface
- cross-border regional partner API variants

---

## 19. Non-Negotiable Constraints

1. No mutable CRUD contract for accounting facts.
2. No hardcoded tax-rate assumptions in request handling.
3. No undocumented callback route may go live.
4. No partner integration may bypass canonical normalization.
5. No public endpoint may be exposed without auth, rate limit, audit logging, and OpenAPI documentation.
6. No Pinecone-specific API contract should be introduced in production-facing docs unless a formal ADR changes the vector-store decision.
7. No provider-dependent SMS delivery status model should leak into downstream domain logic; normalize first.
8. No sync API may return only batch-level success when per-item status is required for offline recovery UX.

---

## 20. Companion Artefacts

This document should be maintained alongside:

- `ARCHITECTURE.md`
- `DATA_MODEL.md`
- `COMPLIANCE_MATRIX.md`
- `OFFLINE_SYNC_SPEC.md`
- `SECURITY_BASELINE.md`
- `INTEGRATION_MANIFEST.md`
- `shared/avro/*.avdl`
- `openapi/**/*.yaml`

---

## 21. Next Authoring Steps

1. Generate machine-readable OpenAPI YAML files from Sections 9–17.
2. Define shared schema components and security schemes.
3. Write Avro IDL for the Phase 1 event topics.
4. Produce contract tests for idempotency, authz, and sync conflict flows.
5. Map these contracts to gateway routes and service repositories.

