# Getting Started with Statewave

This guide walks you through deploying Statewave, ingesting data, and retrieving context — everything a developer needs to start building with Statewave in under 10 minutes.

> **Prerequisites:** Docker Desktop (or any Docker engine + `docker compose`). Nothing else is required for the server itself. Python ≥3.11 / Node ≥18 are only needed if you also want the SDKs or the local website / admin console.

---

## 1. Start the server

The quickest path uses Docker Compose:

```bash
git clone https://github.com/smaramwbc/statewave.git
cd statewave
cp .env.example .env
```

**Set your LLM provider key** in `.env` (recommended — without it, Statewave runs in demo mode with regex-based extraction and hash-based embeddings, no real semantic search):

```bash
# In .env — uncomment and fill in:
STATEWAVE_COMPILER_TYPE=llm
STATEWAVE_EMBEDDING_PROVIDER=litellm
STATEWAVE_LITELLM_API_KEY=sk-...           # OpenAI key, or any LiteLLM-supported provider
# STATEWAVE_LITELLM_MODEL=gpt-4o-mini        # any LiteLLM model identifier
# STATEWAVE_LITELLM_EMBEDDING_MODEL=text-embedding-3-small
```

Statewave routes every LLM and embedding call through [LiteLLM](https://github.com/BerriAI/litellm), so the same `STATEWAVE_LITELLM_*` config works for OpenAI, Anthropic, Azure, Bedrock, Ollama (no key — runs locally), Cohere, Voyage, Mistral, Groq, and 100+ others. See [`server/services/llm.py`](https://github.com/smaramwbc/statewave/blob/main/server/services/llm.py) for the full env-var contract.

Then bring it up:

```bash
docker compose up -d
```

Migrations run automatically on container start (the `start.sh` entrypoint waits for Postgres, runs `alembic upgrade head`, then launches uvicorn). Verify it's running:

```bash
curl http://localhost:8100/healthz
# → {"status":"ok"}

curl http://localhost:8100/readyz
# → {"status":"ready","checks":[
#      {"name":"database","status":"ok","latency_ms":...},
#      {"name":"queue","status":"ok"},
#      {"name":"llm","status":"ok","latency_ms":...}     ← real provider call
#    ]}
```

If `llm` shows `"detail":"not configured (skip)"`, your `STATEWAVE_LITELLM_API_KEY` isn't being read — re-check `.env` and `docker compose up -d` again to pick it up.

> **Alternative:** See the [Deployment Guide](deployment/guide.md) for bare-metal, Fly.io, or Railway setups.

---

## 2. Configure authentication (optional)

For local dev, Statewave runs in open-access mode. To enable auth, set an API key:

```bash
# In your .env file:
STATEWAVE_API_KEY=my-secret-key-123
```

Restart the server, then include the key in all requests:

```bash
curl -H "X-API-Key: my-secret-key-123" http://localhost:8100/healthz
```

---

## 3. Install the SDK

**Python:**

```bash
pip install statewave-py
```

**TypeScript:**

```bash
npm install statewave-ts
```

---

## 4. Ingest episodes

Episodes are raw interaction records — the ground truth that Statewave remembers.

```python
from statewave import StatewaveClient

sw = StatewaveClient("http://localhost:8100")
# sw = StatewaveClient("http://localhost:8100", api_key="my-secret-key-123")

# Record a conversation
episode = sw.create_episode(
    subject_id="user-42",
    source="support-chat",
    type="conversation",
    payload={
        "messages": [
            {"role": "user", "content": "My name is Alice and I work at Globex Corp."},
            {"role": "assistant", "content": "Welcome Alice! How can I help?"},
        ]
    },
)
print(f"Episode created: {episode.id}")
```

For bulk data, use batch ingestion (up to 100 per call):

```python
result = sw.create_episodes_batch([
    {
        "subject_id": "user-42",
        "source": "support-chat",
        "type": "conversation",
        "payload": {"messages": [{"role": "user", "content": "I prefer email over Slack."}]},
    },
    {
        "subject_id": "user-42",
        "source": "support-chat",
        "type": "conversation",
        "payload": {"messages": [{"role": "user", "content": "We had a billing issue last week."}]},
    },
])
print(f"Batch ingested: {result.episodes_created} episodes")
```

---

## 5. Compile memories

Compilation extracts structured memories from raw episodes — facts, summaries, and procedures — with provenance back to the source.

```python
result = sw.compile_memories("user-42")
print(f"Compiled {result.memories_created} memories:")
for m in result.memories:
    print(f"  [{m.kind}] {m.content} (confidence: {m.confidence})")
```

Compilation is **idempotent** — calling it again only processes new episodes.

---

## 6. Retrieve context

The context endpoint assembles a ranked, token-bounded bundle for your AI task:

```python
ctx = sw.get_context(
    subject_id="user-42",
    task="Help the user with their billing question",
    max_tokens=2000,
)

print(f"Token estimate: {ctx.token_estimate}")
print(f"Facts: {len(ctx.facts)}")
print(f"Procedures: {len(ctx.procedures)}")
print()
print(ctx.assembled_context)  # Ready to inject into an LLM prompt
```

The `assembled_context` string is ready to paste into any LLM system prompt. Statewave ranks memories by:
- **Kind priority** — facts > procedures > summaries > raw episodes
- **Recency** — recent memories score higher
- **Task relevance** — keyword overlap with your task description
- **Temporal validity** — expired/superseded memories are deprioritized

---

## 7. Explore the timeline

See everything Statewave knows about a subject:

```python
timeline = sw.get_timeline("user-42")
print(f"Episodes: {len(timeline.episodes)}")
print(f"Memories: {len(timeline.memories)}")
```

---

## 8. Search memories

Find specific memories by kind or text:

```python
results = sw.search_memories("user-42", kind="profile_fact")
for m in results.memories:
    print(f"  {m.content}")
```

---

## 9. Delete a subject

Remove all data for a subject (GDPR, data governance):

```python
result = sw.delete_subject("user-42")
print(f"Deleted {result.episodes_deleted} episodes, {result.memories_deleted} memories")
```

---

## Optional: run the full local stack (server + admin + website)

If you also want the operator console and the marketing/demo website running locally — useful for end-to-end testing of the chat widget and admin flows — you'll need Node ≥18.

```bash
# Already running: server on :8100 (from §1)

# Operator console — http://localhost:5173
git clone https://github.com/smaramwbc/statewave-admin.git
cd statewave-admin
cat > .env.local << 'EOF'
STATEWAVE_API_URL=http://localhost:8100
ADMIN_AUTH_DISABLED=true
EOF
npm install
npm run dev

# Website (in a separate shell) — http://localhost:5173 (or next free port)
git clone https://github.com/smaramwbc/statewave-web.git
cd statewave-web
npm install
npm run dev
```

Both admin and web are Vite SPAs and run via `npm run dev`. There's no Docker path for them today — they're development surfaces against your already-running Statewave server.

> **Why `ADMIN_AUTH_DISABLED=true`?** The admin console ships with a built-in password gate that's required in production. For local-only dev, this flag short-circuits the gate. See [statewave-admin SECURITY.md](https://github.com/smaramwbc/statewave-admin/blob/main/SECURITY.md) before exposing the console anywhere beyond your laptop.

Total time from `git clone` to all three running: typically **5–8 minutes** on a machine with Docker and Node already installed.

---

## Next steps

- **Run a full example:** See [minimal-quickstart](https://github.com/smaramwbc/statewave-examples/tree/main/minimal-quickstart) or [support-agent](https://github.com/smaramwbc/statewave-examples/tree/main/support-agent-python)
- **API reference:** Interactive docs at `http://localhost:8100/docs`
- **Configuration:** See [.env.example](https://github.com/smaramwbc/statewave/blob/main/.env.example) for all options
- **Architecture:** [Architecture Overview](architecture/overview.md) · [Compiler Modes](architecture/compiler-modes.md) · [Privacy & Data Flow](architecture/privacy-and-data-flow.md)
- **Operators:** [Hardware & Scaling](deployment/hardware-and-scaling.md) — GPU is never required by Statewave itself · [Deployment Sizing Guide](deployment/sizing.md) — what size box to run from local to enterprise

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Connection refused` on port 8100 | Check `docker compose ps` — is the `api` container running? Logs: `docker compose logs api` |
| `readyz` returns `{"status":"ready",...,"llm":{"detail":"not configured (skip)"}}` | `STATEWAVE_LITELLM_API_KEY` isn't set. Edit `.env` and run `docker compose up -d` to pick it up. |
| `readyz` returns 503 with a DB error | Database not ready. Check `docker compose logs db` — first start can take 5–10s for the pgvector image. |
| `401 missing_api_key` | Set `X-API-Key` header or remove `STATEWAVE_API_KEY` from `.env` |
| `422 validation_error` | Check request body — `subject_id`, `source`, `type`, `payload` are required |
| No memories after compile | Heuristic compiler extracts from conversation payloads with `messages[].content`. Switch to `STATEWAVE_COMPILER_TYPE=llm` for richer extraction. |
| Admin shows "ADMIN_PASSWORD and ADMIN_SESSION_SECRET are required" on login | Set `ADMIN_AUTH_DISABLED=true` in `statewave-admin/.env.local` and restart `npm run dev`. Production deploys must set the password instead. |
