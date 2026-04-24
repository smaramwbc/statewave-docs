# Statewave API v1 Contract

Base URL: `http://localhost:8100`

## Common behavior

### Request IDs

Every response includes an `X-Request-ID` header. Clients may send their own `X-Request-ID`; if omitted the server generates one. Use this for log correlation and error reporting.

### Error format

All error responses use a structured shape:

```json
{
  "error": {
    "code": "not_found",
    "message": "Subject sub-99 has no episodes",
    "details": null,
    "request_id": "abc-123"
  }
}
```

Standard error codes: `validation_error`, `not_found`, `conflict`, `internal_error`.

### Health endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Liveness — always returns `{"status": "ok"}` |
| GET | `/readyz` | Readiness — checks DB connectivity |

## Endpoints

### POST /v1/episodes

Create an immutable episode.

**Request:**

```json
{
  "subject_id": "user-42",
  "source": "chat",
  "type": "conversation",
  "payload": { "messages": [...] },
  "metadata": {},
  "provenance": {}
}
```

**Response:** `201` — Episode object with `id`, `created_at`.

---

### POST /v1/memories/compile

Compile memories from a subject's episodes. **Idempotent** — recompiling the same subject produces no duplicate memories.

**Request:**

```json
{ "subject_id": "user-42" }
```

**Response:** `200` — `{ subject_id, memories_created, memories: [...] }`

---

### GET /v1/memories/search

Search memories for a subject.

**Query params:** `subject_id` (required), `kind`, `q`, `limit`

**Response:** `200` — `{ memories: [...] }`

---

### POST /v1/context

Assemble a ranked, token-bounded context bundle for downstream LLM use.

**Request:**

```json
{
  "subject_id": "user-42",
  "task": "Help the user with their billing question",
  "max_tokens": 4000
}
```

`max_tokens` is optional (default: 4000). The assembler ranks memories by kind priority (facts > procedures > episodes), recency, and task-keyword relevance, then fills the bundle up to the token budget.

**Response:** `200` — ContextBundle:

```json
{
  "subject_id": "user-42",
  "task": "Help the user...",
  "facts": ["Name: Alice", "Company: Acme Corp"],
  "episodes": [{ "summary": "...", "when": "..." }],
  "procedures": ["Prefers email communication"],
  "assembled_context": "## Known facts\n- Name: Alice\n...",
  "token_estimate": 312,
  "provenance": { "source_episode_ids": ["..."], "memory_ids": ["..."] }
}
```

---

### GET /v1/timeline

Get full timeline for a subject.

**Query params:** `subject_id` (required)

**Response:** `200` — `{ subject_id, episodes: [...], memories: [...] }`

---

### DELETE /v1/subjects/{subject_id}

Delete all data for a subject (episodes + memories). Permanent.

**Response:** `200` — `{ subject_id, episodes_deleted, memories_deleted }`
