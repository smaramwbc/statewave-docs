# Getting Started with Statewave

This guide walks you through deploying Statewave, ingesting data, and retrieving context — everything a developer needs to start building with Statewave in under 10 minutes.

---

## 1. Start the server

The quickest path uses Docker Compose:

```bash
git clone https://github.com/smaramwbc/statewave.git
cd statewave
cp .env.example .env
docker compose up -d
```

Wait for the database to be ready, then run migrations:

```bash
docker compose exec api alembic upgrade head
```

Verify it's running:

```bash
curl http://localhost:8100/healthz
# → {"status": "ok"}

curl http://localhost:8100/readyz
# → {"status": "ready"}
```

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
| `Connection refused` on port 8100 | Check `docker compose ps` — is the `api` container running? |
| `readyz` returns error | Database not ready. Check `docker compose logs db` |
| `401 missing_api_key` | Set `X-API-Key` header or remove `STATEWAVE_API_KEY` from .env |
| `422 validation_error` | Check request body — `subject_id`, `source`, `type`, `payload` are required |
| No memories after compile | Heuristic compiler extracts from conversation payloads with `messages[].content`. Check payload shape. |
