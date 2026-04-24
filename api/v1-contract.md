# Statewave API v1 Contract

Base URL: `http://localhost:8100`
Version: **0.4.x**

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

## Multi-tenant (experimental)

When `STATEWAVE_REQUIRE_TENANT=true`, requests must include an `X-Tenant-ID` header. The header value is bound to the structlog context for log correlation.

> **⚠️ Experimental:** Tenant isolation is currently header-extraction only. Tenant IDs are NOT enforced in data-access queries. Do not rely on this for data isolation in production. Full tenant-scoped queries are planned for a future release.

---

## Rate limiting

When `STATEWAVE_RATE_LIMIT_RPM` is set to a positive integer, each client IP is limited to that many requests per minute. Exceeding the limit returns `429` with a `Retry-After` header:

```json
{ "error": { "code": "rate_limited", "message": "Rate limit exceeded. Max 120 requests per minute." } }
```

Health endpoints (`/healthz`, `/readyz`) are exempt.

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

When `STATEWAVE_WEBHOOK_URL` is configured, the server fires async HTTP POST callbacks on key events. Delivery is fire-and-forget with configurable timeout.

| Event | Trigger | Payload |
|-------|---------|---------|
| `episode.created` | After episode ingestion | `{ "id": "...", "subject_id": "..." }` |
| `memories.compiled` | After memory compilation | `{ "subject_id": "...", "memories_created": N }` |
| `subject.deleted` | After subject deletion | `{ "subject_id": "...", "episodes_deleted": N, "memories_deleted": N }` |

Webhook body:

```json
{
  "event": "episode.created",
  "timestamp": "2026-04-24T12:00:00Z",
  "data": { "id": "...", "subject_id": "..." }
}
```

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

**Request:**

```json
{ "subject_id": "user-42" }
```

**Response:** `200`

```json
{
  "subject_id": "user-42",
  "memories_created": 3,
  "memories": [
    {
      "id": "...",
      "subject_id": "user-42",
      "kind": "profile_fact",
      "content": "Name is Alice",
      "summary": "Name is Alice",
      "confidence": 0.8,
      "valid_from": "2026-04-24T12:00:00Z",
      "valid_to": null,
      "source_episode_ids": ["..."],
      "metadata": {},
      "status": "active",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

Memory kinds: `profile_fact`, `episode_summary`, `procedure`.
Memory statuses: `active`, `superseded`, `deleted`.

**Webhook:** `memories.compiled`

---

### GET /v1/memories/search

Search memories for a subject.

| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `subject_id` | yes | — | Subject to search |
| `kind` | no | — | Filter by memory kind |
| `q` | no | — | Text search (ILIKE) or semantic query text |
| `semantic` | no | `false` | `true` to use vector cosine similarity via pgvector |
| `limit` | no | 20 | Max results (1–100) |

When `semantic=true` and `q` is provided, the server generates a query embedding and searches by cosine distance. Falls back to text search on failure or when embeddings are unavailable.

**Response:** `200` — `{ "memories": [ ...MemoryResponse ] }`

---

### POST /v1/context

Assemble a ranked, token-bounded context bundle.

**Request:**

```json
{
  "subject_id": "user-42",
  "task": "Help the user with billing",
  "max_tokens": 4000
}
```

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
  "token_estimate": 312
}
```

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

## Configuration reference

All settings use the `STATEWAVE_` env prefix. A `.env` file is supported.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://statewave:statewave@localhost:5432/statewave` | Postgres connection |
| `HOST` | `0.0.0.0` | Bind host |
| `PORT` | `8100` | Bind port |
| `DEBUG` | `false` | Debug logging (console renderer) |
| `COMPILER_TYPE` | `heuristic` | `heuristic` or `llm` |
| `EMBEDDING_PROVIDER` | `stub` | `stub`, `openai`, or `none` |
| `EMBEDDING_DIMENSIONS` | `1536` | Vector dimensions |
| `OPENAI_API_KEY` | — | Required for `llm` compiler and `openai` embeddings |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `LLM_COMPILER_MODEL` | `gpt-4o-mini` | Chat model for LLM compiler |
| `DEFAULT_MAX_CONTEXT_TOKENS` | `4000` | Default context budget |
| `API_KEY` | — | Auth key (empty = open access) |
| `RATE_LIMIT_RPM` | `0` | Requests/min/IP (0 = disabled) |
| `WEBHOOK_URL` | — | Webhook callback URL (empty = disabled) |
| `WEBHOOK_TIMEOUT` | `5.0` | Webhook timeout (seconds) |
| `CORS_ORIGINS` | `["*"]` | CORS allowed origins |
| `REQUIRE_TENANT` | `false` | Require `X-Tenant-ID` (experimental) |
| `TENANT_HEADER` | `X-Tenant-ID` | Tenant header name |
