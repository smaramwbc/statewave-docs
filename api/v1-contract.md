# Statewave API v1 Contract

Base URL: `http://localhost:8100`
Version: **0.9.x**

> **Pre-built ingestion paths:** [Statewave Connectors](../connectors/index.md) wrap this contract for common sources — GitHub, Markdown/ADRs, MCP, and more — so you don't have to hand-build episode payloads from each source.

---

## Authentication

When `STATEWAVE_API_KEY` is configured, all requests (except `/healthz`, `/readyz`, `/docs`, `/redoc`, `/openapi.json`) must include a valid API key.

**Header:** `X-API-Key: <your-key>`

Unauthenticated requests receive `401`:

```json
{ "error": { "code": "missing_api_key", "message": "X-API-Key header is required." } }
```

Invalid keys receive `403`:

```json
{ "error": { "code": "invalid_api_key", "message": "Invalid API key." } }
```

When no `STATEWAVE_API_KEY` is set, authentication is disabled (open access — suitable for local dev).

---

## Multi-tenant isolation

When `STATEWAVE_REQUIRE_TENANT=true`, requests must include an `X-Tenant-ID` header. The tenant ID is persisted on all data (episodes, memories, compile jobs) and **all queries are scoped to the requesting tenant**.

Guarantees (v0.5):
- Episodes, memories, subjects, compile jobs, search, context, and timeline are all tenant-scoped
- Tenant A cannot read, search, or delete tenant B's data
- `tenant_id` is stored on every row; composite indexes ensure efficient scoped queries
- Admin endpoints (`/admin/*`) can optionally filter by tenant but are not restricted (operator access)

Not yet implemented:
- PostgreSQL row-level security (RLS) — data isolation is enforced at the application query layer, not the database policy layer
- Per-tenant webhook URLs — webhooks fire to a single configured URL regardless of tenant
- Per-tenant rate limits — rate limiting is still per-IP, not per-tenant

When `REQUIRE_TENANT=false` (default), the system operates in single-tenant mode with no isolation.

### Upgrade path: pre-tenant data

When enabling tenant isolation on an existing deployment, rows created before the migration will have `tenant_id=NULL`. Statewave treats these as follows:

- **Queries with a tenant_id filter will NOT return NULL-tenant rows.** This means pre-existing data becomes invisible to tenant-scoped requests.
- **Queries without a tenant_id (single-tenant mode) will return all rows regardless of tenant_id value.**

Operators upgrading to tenant-aware usage should either:
1. **Backfill** existing rows with the correct tenant_id:
   ```sql
   UPDATE episodes SET tenant_id = 'your-tenant' WHERE tenant_id IS NULL;
   UPDATE memories SET tenant_id = 'your-tenant' WHERE tenant_id IS NULL;
   UPDATE compile_jobs SET tenant_id = 'your-tenant' WHERE tenant_id IS NULL;
   ```
2. **Accept NULL rows as legacy/shared** and start fresh with tenant-scoped data going forward.

Use `GET /admin/tenant-audit` to inspect how many rows lack a tenant_id.

---

## Rate limiting

When `STATEWAVE_RATE_LIMIT_RPM` is set to a positive integer, each client IP is limited to that many requests per minute. Exceeding the limit returns `429` with a `Retry-After` header:

```json
{ "error": { "code": "rate_limited", "message": "Rate limit exceeded. Max 120 requests per minute." } }
```

Health endpoints (`/healthz`, `/readyz`) are exempt.

### Strategy

| Strategy | Config | Behavior |
|----------|--------|----------|
| `distributed` (default) | `STATEWAVE_RATE_LIMIT_STRATEGY=distributed` | Postgres-backed fixed-window. Shared across workers, survives restarts. |
| `memory` | `STATEWAVE_RATE_LIMIT_STRATEGY=memory` | Per-process in-memory sliding window. Resets on restart, single-worker only. |

The distributed strategy uses a single atomic `INSERT ... ON CONFLICT UPDATE` per request. Expired windows are cleaned up by the background task every hour. If the database is unreachable, the limiter fails open (requests are allowed).

---

## Request IDs

Every response includes an `X-Request-ID` header. Clients may send their own; if omitted the server generates one. The ID is included in structured error responses and all structlog entries for correlation.

---

## Error format

All error responses use a consistent structured shape:

```json
{
  "error": {
    "code": "not_found",
    "message": "Subject sub-99 has no episodes",
    "details": null,
    "request_id": "abc123def456"
  }
}
```

Standard error codes: `validation_error`, `not_found`, `conflict`, `internal_error`, `missing_api_key`, `invalid_api_key`, `rate_limited`, `missing_tenant`.

---

## Webhooks

When `STATEWAVE_WEBHOOK_URL` is configured, the server fires async HTTP POST callbacks on key events. Delivery is persistent with exponential backoff, dead-letter queue, and configurable timeout.

| Event | Trigger | Payload |
|-------|---------|---------|
| `episode.created` | After episode ingestion | `{ "id": "...", "subject_id": "..." }` |
| `episodes.batch_created` | After batch episode ingestion | `{ "count": N, "subject_ids": ["..."] }` |
| `memories.compiled` | After memory compilation | `{ "subject_id": "...", "memories_created": N }` |
| `subject.deleted` | After subject deletion | `{ "subject_id": "...", "episodes_deleted": N, "memories_deleted": N }` |
| `subject.health_degraded` | Customer health state worsened | `{ "subject_id": "...", "previous_state": "...", "current_state": "...", "score": N, "factors": [...], "generated_at": "..." }` |
| `subject.health_improved` | Customer health state recovered | `{ "subject_id": "...", "previous_state": "...", "current_state": "...", "score": N, "factors": [...], "generated_at": "..." }` |

Webhook body:

```json
{
  "event": "episode.created",
  "timestamp": "2026-04-24T12:00:00Z",
  "data": { "id": "...", "subject_id": "..." }
}
```

### Event-type filter

By default every event above is delivered to the configured webhook URL. Set `STATEWAVE_WEBHOOK_EVENTS` to a comma-separated allowlist to restrict delivery to specific event types:

```
STATEWAVE_WEBHOOK_EVENTS=memories.compiled,subject.health_degraded
```

A filtered-out event is dropped before it is enqueued — it consumes no storage and no delivery attempts. An empty or unset value delivers every event (the default), so the filter is fully backward-compatible. Unknown event types are rejected at startup, so a typo fails fast rather than silently dropping every webhook.

---

## Health endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Liveness — returns `{"status": "ok"}` |
| GET | `/readyz` | Readiness — checks DB, returns `{"status": "ready"}` |

---

## Input validation

- `subject_id`: 1–256 chars, non-empty
- `source`: 1–256 chars, non-empty
- `type`: 1–128 chars, non-empty
- `task`: 1–4000 chars, non-empty
- `max_tokens`: 1–128,000 (optional)
- `limit`: 1–100

Validation failures return `422` with `code: "validation_error"` and per-field `details`.

---

## Endpoints

### POST /v1/episodes

Create an immutable episode (append-only).

**Request:**

```json
{
  "subject_id": "user-42",
  "source": "chat",
  "type": "conversation",
  "payload": { "messages": [{"role": "user", "content": "Hello"}] },
  "metadata": {},
  "provenance": {}
}
```

**Response:** `201` — EpisodeResponse

```json
{
  "id": "550e8400-...",
  "subject_id": "user-42",
  "source": "chat",
  "type": "conversation",
  "payload": { ... },
  "metadata": {},
  "provenance": {},
  "created_at": "2026-04-24T12:00:00Z"
}
```

**Webhook:** `episode.created`

---

### POST /v1/memories/compile

Compile memories from unprocessed episodes. **Idempotent.**

Pipeline:
1. Fetch uncompiled episodes for the subject
2. Run compiler (heuristic or LLM, per `STATEWAVE_COMPILER_TYPE`)
3. Generate embeddings if provider is configured (graceful fallback)
4. Auto-resolve memory conflicts (supersede older overlapping memories)
5. Mark episodes compiled — all in a single transaction

#### Synchronous mode (default)

**Request:**

```json
{ "subject_id": "user-42" }
```

**Response:** `200`

```json
{
  "subject_id": "user-42",
  "memories_created": 3,
  "memories": [ ...MemoryResponse ]
}
```

#### Async mode (recommended for large subjects)

Pass `"async": true` to return immediately with a job ID. The compilation runs in the background and job state is persisted to Postgres (survives restarts).

**Request:**

```json
{ "subject_id": "user-42", "async": true }
```

**Response:** `202`

```json
{
  "job_id": "a1b2c3d4",
  "status": "pending",
  "subject_id": "user-42"
}
```

Poll `GET /v1/memories/compile/{job_id}` for status.

---

### GET /v1/memories/compile/{job_id}

Poll the status of an async compile job.

**Response:** `200`

```json
{
  "job_id": "a1b2c3d4",
  "status": "completed",
  "subject_id": "user-42",
  "memories_created": 5
}
```

Possible statuses: `pending`, `running`, `completed`, `failed`.

On failure, includes `"error": "..."`.

Job state is durable (Postgres-backed). Jobs are retained for 7 days by default (`STATEWAVE_COMPILE_JOB_RETENTION_HOURS`).

**Webhook:** `memories.compiled`

---

### GET /v1/memories/search

Search memories for a subject.

| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `subject_id` | yes | — | Subject to search |
| `kind` | no | — | Filter by memory kind |
| `q` | no | — | Query text — semantic when `semantic=true`, exact-match text fallback otherwise |
| `semantic` | no | `false` | `true` to use vector cosine similarity via pgvector (the primary retrieval path on `/v1/context`) |
| `limit` | no | 20 | Max results (1–100) |

When `semantic=true` and `q` is provided, the server generates a query embedding and searches via the native pgvector `<=>` cosine-distance operator (HNSW-indexed; see roadmap v0.7). It falls back to a text-match scan only when embeddings are unavailable (e.g. stub provider, embedding generation failure). `/v1/context` always uses the semantic path with the candidate-pool union — see the v0.7 roadmap entries for details.

**Response:** `200` — `{ "memories": [ ...MemoryResponse ] }`

---

### POST /v1/context

Assemble a ranked, token-bounded context bundle.

**Request:**

```json
{
  "subject_id": "user-42",
  "task": "Help the user with billing",
  "max_tokens": 4000,
  "session_id": "sess-xyz",
  "emit_receipt": true,
  "query_id": "req-123",
  "task_id": "task-456",
  "parent_receipt_id": "01ARZ3NDEKTSV4RRFFQ69G5FA0",
  "caller_id": "agent-7",
  "caller_type": "support_agent"
}
```

`session_id`, `emit_receipt`, `query_id`, `task_id`,
`parent_receipt_id`, `caller_id`, and `caller_type` are all optional.
`emit_receipt` controls whether a
[state-assembly receipt](../receipts.md) is written; the ULID of the
resulting receipt is echoed back in `receipt_id`.

`caller_id` and `caller_type` feed the
[sensitivity-label policy layer](../sensitivity-labels.md). When the
tenant config sets `require_caller_identity: true`, both are
**mandatory** — missing values return `401`.

**Scoring model:**

| Signal | Range | Description |
|--------|-------|-------------|
| Kind priority | 3–10 | profile_fact=10, procedure=8, episode_summary=5, raw_episode=3 |
| Recency | 0–5 | Linear: most recent = 5 |
| Task relevance | 0–5 (text) or 0–8 (semantic) | Word overlap or cosine similarity |
| Temporal validity | -4 to +3 | Valid/no-expiry = +3, expired = -4 |

Items are sorted by composite score, packed into the token budget, and rendered into sections: Task → Facts → Procedures → History → Episodes.

**Response:** `200`

```json
{
  "subject_id": "user-42",
  "task": "Help the user with billing",
  "facts": [ ...MemoryResponse ],
  "episodes": [ ...EpisodeResponse ],
  "procedures": [ ...MemoryResponse ],
  "provenance": {
    "fact_ids": ["..."],
    "summary_ids": ["..."],
    "procedure_ids": ["..."],
    "episode_ids": ["..."]
  },
  "assembled_context": "## Task\nHelp the user...\n\n## About this user\n- ...",
  "token_estimate": 312,
  "receipt_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "receipt_emitted": true
}
```

`receipt_id` is `null` when no receipt was emitted (either the caller
did not request one, the tenant config is `never`, or the kill-switch
is active). `receipt_emitted` distinguishes "no receipt requested"
(both fields default) from "receipt was attempted but the write
failed" (`receipt_id` null, `receipt_emitted` false plus a structured
log on the server).

---

### GET /v1/receipts/{receipt_id}

Fetch one [state-assembly receipt](../receipts.md) by ULID.
Tenant-scoped: a receipt belonging to another tenant returns `404`
with no distinction from a non-existent id, so a tenant cannot probe
another tenant's id space.

**Response:** `200` — the full receipt body (see
[receipts.md](../receipts.md)).

---

### GET /v1/receipts/{receipt_id}/verify  (v0.9)

Verify the HMAC signature on a stored receipt. Tenant-scoped — same
404 semantic as the detail endpoint.

**Response:** `200`

```json
{
  "valid": true,                           // true | false | null
  "key_id": "key-2026-01",                 // operator key id used to sign
  "algorithm": "hmac-sha256-canonical-v1", // algorithm + canonical-form version
  "reason": "ok"                           // ok | signature_mismatch | key_unavailable
                                           //   | no_signature | unsupported_algorithm
}
```

`valid: null` is for the cases where the verdict cannot be
determined — `no_signature` (pre-v0.9 receipt or tenant didn't
opt in), `key_unavailable` (the key id rotated out of operator
config), `unsupported_algorithm` (a forward-compat scenario where
this binary doesn't implement the algorithm). `valid: false` is
reserved for "we checked the math and the signature doesn't cover
the body." Comparison is constant-time. The signing key bytes never
appear in the response.

---

### POST /v1/receipts/{receipt_id}/replay  (v0.9)

Re-run the original retrieval against the **current** memory state
using the **original** policy bundle captured in the receipt's
`policy_snapshot`. Emits a new receipt with `mode="as_of_replay"`
and `parent_receipt_id` pointing at the source. Returns a structural
diff envelope.

**Response:** `200`

```json
{
  "original_receipt_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "replay_receipt_id":   "01ARZ3NDEKTSV4RRFFQ69G5FAW",
  "diff": {
    "context_hash":     { "original": "…", "replay": "…", "changed": true },
    "selected_entries": { "added": [ … ], "removed": [ … ], "common": 3 },
    "filters_applied":  { "added": [ … ], "removed": [ … ] }
  }
}
```

Refusal codes (`422` with the standard `error.code` envelope):

| `error.code`                            | When |
|-----------------------------------------|------|
| `unreplayable.missing_policy_snapshot`  | Pre-v0.9 receipt — no snapshot was captured at emission. |
| `unreplayable.nested_replay`            | The receipt is itself a replay. v0.9 ships one level only; replay the parent. |
| `unreplayable.invalid_snapshot`         | The snapshot YAML failed to parse (corruption or tampering). |

`404` for unknown / cross-tenant. The original receipt is **never**
modified — replay only appends a new linked row. See
[the replay design doc](https://github.com/smaramwbc/statewave/blob/main/docs/replay.md)
for the semantic rationale (*current code + original policy*) and
the operator workflow.

---

### GET /v1/receipts

List receipts for a subject, newest first.

**Query params:**

| Param | Required | Description |
|-------|----------|-------------|
| `subject_id` | yes | Subject the receipts were written for |
| `since` | no | Lower bound on `created_at` (ISO 8601) |
| `until` | no | Upper bound on `created_at` (ISO 8601) |
| `cursor` | no | Last `receipt_id` from the previous page — ULIDs sort lexically by time, so this is a stable cursor |
| `limit` | no | 1–200, default 50 |

**Response:** `200`

```json
{
  "receipts": [ ...Receipt ],
  "next_cursor": "01ARZ3NDEKTSV4RRFFQ69G5FA0"
}
```

`next_cursor` is `null` when there are no further results.

---

### PATCH /v1/memories/{memory_id}/labels

Replace a memory's `sensitivity_labels` — the per-memory capability
tags consumed by the [policy layer](../sensitivity-labels.md).

**Request:**

```json
{ "sensitivity_labels": ["pii", "financial"] }
```

Server normalises labels (deduplicate, lowercase, trim) and caps at
32 entries. An empty list clears all labels (memory becomes untagged
→ policy default-allow). Tenant-scoped: PATCHing a memory belonging
to another tenant returns `404`, not `403`.

**Response:** `200` — the updated `MemoryResponse` with the canonical
label set.

---

### GET /v1/timeline

Get full timeline for a subject.

**Query params:** `subject_id` (required)

**Response:** `200` — `{ "subject_id", "episodes": [...], "memories": [...] }`

---

### DELETE /v1/subjects/{subject_id}

Delete all data for a subject (episodes + memories). Permanent and irreversible.

**Response:** `200`

```json
{ "subject_id": "user-42", "episodes_deleted": 5, "memories_deleted": 12 }
```

**Webhook:** `subject.deleted`

---

### GET /v1/subjects/{subject_id}/health

Compute customer health score with explainable factors.

**Response:** `200`

```json
{
  "subject_id": "user-42",
  "score": 55,
  "state": "watch",
  "factors": [
    { "signal": "unresolved_issues", "impact": -15, "detail": "1 open session(s)" },
    { "signal": "sla_resolution_breaches", "impact": -10, "detail": "1 session(s) exceeded 24h resolution SLA" }
  ]
}
```

States: `healthy` (≥70), `watch` (40–69), `at_risk` (<40).

---

### GET /v1/subjects/{subject_id}/sla

Compute SLA metrics for a subject — first response time, resolution time, and breach flags per session.

**Query params:**

| Param | Default | Description |
|-------|---------|-------------|
| `first_response_threshold_minutes` | `5.0` | Minutes before first response is considered breached |
| `resolution_threshold_hours` | `24.0` | Hours before resolution is considered breached |

**Response:** `200`

```json
{
  "subject_id": "user-42",
  "total_sessions": 3,
  "resolved_sessions": 2,
  "open_sessions": 1,
  "avg_first_response_seconds": 145.0,
  "avg_resolution_seconds": 3600.0,
  "first_response_breach_count": 1,
  "resolution_breach_count": 0,
  "sessions": [
    {
      "session_id": "sess-abc",
      "status": "resolved",
      "first_message_at": "2026-04-29T10:00:00+00:00",
      "first_response_at": "2026-04-29T10:02:25+00:00",
      "resolved_at": "2026-04-29T11:00:00+00:00",
      "first_response_seconds": 145.0,
      "resolution_seconds": 3600.0,
      "open_duration_seconds": null,
      "first_response_breached": false,
      "resolution_breached": false
    }
  ]
}
```

---

### POST /v1/resolutions

Create or update resolution state for a support session. Upserts by `subject_id` + `session_id`.

**Body:**

```json
{
  "subject_id": "user-42",
  "session_id": "sess-abc",
  "status": "resolved",
  "resolution_summary": "Issued refund for duplicate charge",
  "metadata": { "category": "billing" }
}
```

- `status`: one of `open`, `resolved`, `unresolved`

**Response:** `200` — the resolution record.

### GET /v1/resolutions?subject_id=X

List resolutions for a subject. Optional `status` query param to filter.

**Response:** `200` — array of resolution records.

---

### POST /v1/handoff

Generate a compact handoff context pack for agent escalation, shift change, or transfer.

**Body:**

```json
{
  "subject_id": "user-42",
  "session_id": "sess-abc",
  "reason": "escalation to billing specialist",
  "max_tokens": 4000
}
```

**Response:** `200`

```json
{
  "subject_id": "user-42",
  "session_id": "sess-abc",
  "reason": "escalation to billing specialist",
  "generated_at": "2026-04-29T12:00:00Z",
  "customer_summary": "user-42 — Enterprise plan; Globex Corp",
  "active_issue": "[chat/message] My billing is incorrect",
  "attempted_steps": ["Checked account status", "Verified payment method"],
  "key_facts": ["Enterprise plan", "Globex Corporation", "Account since 2023"],
  "resolution_history": [
    { "session_id": "sess-old", "status": "resolved", "summary": "Issued refund" }
  ],
  "recent_context": ["[chat/message] [sess-old] Previous billing question"],
  "handoff_notes": "# Handoff Brief — user-42\n...",
  "token_estimate": 280,
  "provenance": { "fact_ids": [...], "episode_ids": [...], "resolution_ids": [...] }
}
```

The `handoff_notes` field is a pre-rendered markdown brief optimized for both human and LLM consumption.

---

### GET /v1/memory-templates

List the bundled memory templates — declarative, versioned scaffolds for common information patterns (support handoffs, project decisions, incident summaries, …). The response carries each template's full field schema, so callers can render their own forms from it.

**Response:** `200`

```json
{
  "templates": [
    {
      "id": "customer-support-handoff",
      "version": 1,
      "title": "Customer support handoff",
      "description": "...",
      "episode_type": "support.handoff_note",
      "fields": [
        { "name": "customer", "type": "string", "required": true, "description": "..." },
        { "name": "issue", "type": "text", "required": true, "description": "..." }
      ],
      "content_template": "Customer support handoff — {customer}.\n\nActive issue: {issue}"
    }
  ]
}
```

### GET /v1/memory-templates/{template_id}

Fetch one template by id. `404` if there is no such template.

### POST /v1/memory-templates/{template_id}/apply

Validate caller-supplied field values against a template and ingest the resulting episode. The episode flows through the normal compile/context pipeline; the compiler is not involved in templating.

**Request:**

```json
{
  "subject_id": "customer:globex",
  "session_id": "ticket-8842",
  "values": {
    "customer": "Globex Corp",
    "issue": "Duplicate charge on the May invoice"
  }
}
```

| Field | Required | Constraints |
|-------|----------|-------------|
| `subject_id` | yes | Non-empty subject id |
| `values` | no | Map of template field name → string value; validated against the template's field schema |
| `session_id` | no | Session the episode belongs to |

Validation is strict — an unknown field, a missing required field, or a non-string value is rejected with `422`. `404` if the template does not exist.

**Response:** `201` — the created episode. Its `payload` carries `template_id`, `template_version`, the supplied `fields`, and the deterministically-rendered `content`; `metadata.template` records `{ id, version }` for provenance.

See `docs/memory-templates.md` in the [`statewave`](https://github.com/smaramwbc/statewave) server repo for the template file format and how to add one.

---

### POST /v1/llm/complete

Internal chat-completion pass-through used by Statewave's own demo / website flows. Accepts a list of chat messages and runs a single completion via the configured LiteLLM provider (`STATEWAVE_LITELLM_MODEL`, etc.).

This endpoint is intentionally narrow:
- The caller **cannot** specify a model — provider/model selection lives entirely in server config.
- No streaming, no function-calling, no tool use, no usage/token metadata in the response.
- Authentication uses the same `X-API-Key` as every other `/v1/*` endpoint.

**Request:**

```json
{
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Hello" }
  ],
  "max_tokens": 200,
  "temperature": 0.7
}
```

| Field | Required | Constraints |
|-------|----------|-------------|
| `messages` | yes | 1–50 entries, each `{role, content}`; role ∈ `{system, user, assistant, tool}`; content ≤ 16000 chars |
| `max_tokens` | no | 1–4096 |
| `temperature` | no | 0.0–2.0 |

**Response:** `200`

```json
{ "reply": "Hi! How can I help?" }
```

**Errors:**
- `503 llm_not_configured` — `STATEWAVE_LITELLM_MODEL` is unset.
- `502 upstream_llm_error` — provider call failed (auth, rate limit, network, malformed response).
- `504 upstream_llm_timeout` — provider call exceeded `STATEWAVE_LITELLM_TIMEOUT_SECONDS`.

> **Why is this not a generic public LLM API?** Because that's a much bigger product surface — streaming, tool calls, structured output, prompt caching, model picking, abuse rate limits — and we don't want to commit to that contract today. If you find yourself reaching for this endpoint as a generic LLM proxy, run LiteLLM's own proxy server instead.

---

## Admin endpoints (operator)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/jobs` | List compile jobs (filterable by status, subject, tenant) |
| `GET` | `/admin/tenant-audit` | Count rows with NULL tenant_id |
| `GET` | `/admin/export/{subject_id}` | Export subject as portable JSON with checksum |
| `POST` | `/admin/import` | Import a previously exported subject document |
| `GET` | `/admin/webhooks/stats` | Webhook delivery statistics |
| `GET` | `/admin/webhooks/{event_id}` | Single webhook event status |

See [backup/restore docs](../dev/backup-restore.md) for export/import usage guide.

---

## Configuration reference

All settings use the `STATEWAVE_` env prefix. A `.env` file is supported.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://statewave:statewave@localhost:5432/statewave` | Postgres connection |
| `HOST` | `0.0.0.0` | Bind host |
| `PORT` | `8100` | Bind port |
| `DEBUG` | `false` | Debug logging (console renderer) |
| `COMPILER_TYPE` | `heuristic` | `heuristic` or `llm` |
| `EMBEDDING_PROVIDER` | `stub` | `stub`, `litellm`, or `none` |
| `EMBEDDING_DIMENSIONS` | `1536` | Vector dimensions |
| `LITELLM_API_KEY` | — | Provider-neutral API key — passed through to whichever provider `LITELLM_MODEL` selects |
| `LITELLM_MODEL` | `gpt-4o-mini` | Chat-completion model — any [LiteLLM identifier](https://docs.litellm.ai/docs/providers) |
| `LITELLM_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model — any LiteLLM-supported |
| `LITELLM_API_BASE` | — | Custom base URL (Ollama, self-hosted gateway, …) |
| `DEFAULT_MAX_CONTEXT_TOKENS` | `4000` | Default context budget |
| `API_KEY` | — | Auth key (empty = open access) |
| `RATE_LIMIT_RPM` | `0` | Requests/min/IP (0 = disabled) |
| `RATE_LIMIT_STRATEGY` | `distributed` | `distributed` (Postgres) or `memory` (in-process) |
| `WEBHOOK_URL` | — | Webhook callback URL (empty = disabled) |
| `WEBHOOK_TIMEOUT` | `5.0` | Webhook timeout (seconds) |
| `WEBHOOK_EVENTS` | — | Comma-separated event-type allowlist (empty = deliver every event) |
| `COMPILE_JOB_RETENTION_HOURS` | `168` | Hours to retain completed/failed compile jobs (0 = no cleanup) |
| `CORS_ORIGINS` | `["*"]` | CORS allowed origins |
| `REQUIRE_TENANT` | `false` | Require `X-Tenant-ID` — enables real tenant isolation |
| `TENANT_HEADER` | `X-Tenant-ID` | Tenant header name |
