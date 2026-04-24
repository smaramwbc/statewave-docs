# Statewave API v1 Contract

Base URL: `http://localhost:8100`

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

Compile memories from a subject's episodes.

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

Assemble a context bundle for downstream LLM use.

**Request:**
```json
{ "subject_id": "user-42", "task": "Help the user", "max_tokens": 4000 }
```

**Response:** `200` — ContextBundle with `facts`, `episodes`, `procedures`, `assembled_context`, `token_estimate`, `provenance`.

---

### GET /v1/timeline

Get full timeline for a subject.

**Query params:** `subject_id` (required)

**Response:** `200` — `{ subject_id, episodes: [...], memories: [...] }`

---

### DELETE /v1/subjects/{subject_id}

Delete all data for a subject.

**Response:** `200` — `{ subject_id, episodes_deleted, memories_deleted }`
