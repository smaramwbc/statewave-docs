# Getting Started with Statewave

This guide walks you through deploying Statewave, ingesting data, and retrieving context — everything a developer needs to start building with Statewave in under 10 minutes.

> **Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac/Windows) or a [Docker Engine](https://docs.docker.com/engine/install/) install with the [Compose plugin](https://docs.docker.com/compose/install/) (Linux/servers). Nothing else is required for the server itself. [Python ≥3.11](https://www.python.org/downloads/) / [Node ≥18](https://nodejs.org/en/download) are only needed if you also want the SDKs or the local website / admin console.

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

If `llm` shows `"detail":"STATEWAVE_LITELLM_API_KEY is not set"`, the key isn't being read — re-check `.env` and re-run `docker compose up -d` to pick it up. (Using a local `ollama/*` model? No API key is needed, and this message won't appear for Ollama.)

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
curl -H "X-API-Key: my-secret-key-123" http://localhost:8100/admin/webhooks/stats
```

---

## 3. Install the SDK

**Python:**

```bash
pip install statewave
```

**TypeScript:**

```bash
npm install @statewavedev/sdk
```

> **Not just live chats:** if your data lives in GitHub, a `docs/` folder, Slack, support tickets, email, or workflow runs, the [Statewave Connectors](connectors/index.md) feed those sources into Statewave as normalized episodes — modular packages, dry-run-first, no all-in-one install.

---

## 4. Ingest episodes

Episodes are raw interaction records — the ground truth that Statewave remembers.

**Python:**

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

**TypeScript:**

```typescript
import { StatewaveClient } from "@statewavedev/sdk";

const sw = new StatewaveClient("http://localhost:8100");
// const sw = new StatewaveClient({ baseUrl: "http://localhost:8100", apiKey: "my-secret-key-123" });

// Record a conversation
const episode = await sw.createEpisode({
  subjectId: "user-42",
  source: "support-chat",
  type: "conversation",
  payload: {
    messages: [
      { role: "user", content: "My name is Alice and I work at Globex Corp." },
      { role: "assistant", content: "Welcome Alice! How can I help?" },
    ],
  },
});
console.log(`Episode created: ${episode.id}`);
```

For bulk data, use batch ingestion (up to 100 per call):

**Python:**

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

**TypeScript:**

```typescript
const result = await sw.createEpisodesBatch([
  {
    subjectId: "user-42",
    source: "support-chat",
    type: "conversation",
    payload: { messages: [{ role: "user", content: "I prefer email over Slack." }] },
  },
  {
    subjectId: "user-42",
    source: "support-chat",
    type: "conversation",
    payload: { messages: [{ role: "user", content: "We had a billing issue last week." }] },
  },
]);
console.log(`Batch ingested: ${result.episodesCreated} episodes`);
```

---

## 5. Compile memories

Compilation extracts structured memories from raw episodes — facts, summaries, and procedures — with provenance back to the source.

**Python:**

```python
result = sw.compile_memories("user-42")
print(f"Compiled {result.memories_created} memories:")
for m in result.memories:
    print(f"  [{m.kind}] {m.content} (confidence: {m.confidence})")
```

**TypeScript:**

```typescript
const result = await sw.compileMemories("user-42");
console.log(`Compiled ${result.memoriesCreated} memories:`);
for (const m of result.memories) {
  console.log(`  [${m.kind}] ${m.content} (confidence: ${m.confidence})`);
}
```

Compilation is **idempotent** — calling it again only processes new episodes.

---

## 6. Retrieve context

The context endpoint assembles a ranked, token-bounded bundle for your AI task:

**Python:**

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

**TypeScript:**

```typescript
const ctx = await sw.getContext({
  subjectId: "user-42",
  task: "Help the user with their billing question",
  maxTokens: 2000,
});

console.log(`Token estimate: ${ctx.tokenEstimate}`);
console.log(`Facts: ${ctx.facts.length}`);
console.log(`Procedures: ${ctx.procedures.length}`);
console.log();
console.log(ctx.assembledContext); // Ready to inject into an LLM prompt
```

The `assembled_context` string is ready to paste into any LLM system prompt. Statewave ranks memories by:
- **Kind priority** — facts > procedures > summaries > raw episodes
- **Recency** — recent memories score higher
- **Task relevance** — keyword overlap with your task description
- **Temporal validity** — expired/superseded memories are deprioritized

---

## 7. Explore the timeline

See everything Statewave knows about a subject:

**Python:**

```python
timeline = sw.get_timeline("user-42")
print(f"Episodes: {len(timeline.episodes)}")
print(f"Memories: {len(timeline.memories)}")
```

**TypeScript:**

```typescript
const timeline = await sw.getTimeline("user-42");
console.log(`Episodes: ${timeline.episodes.length}`);
console.log(`Memories: ${timeline.memories.length}`);
```

---

## 8. Search memories

Find specific memories by kind or text:

**Python:**

```python
results = sw.search_memories("user-42", kind="profile_fact")
for m in results.memories:
    print(f"  {m.content}")
```

**TypeScript:**

```typescript
const results = await sw.searchMemories({ subjectId: "user-42", kind: "profile_fact" });
for (const m of results.memories) {
  console.log(`  ${m.content}`);
}
```

---

## 9. Delete a subject

Remove all data for a subject (GDPR, data governance):

**Python:**

```python
result = sw.delete_subject("user-42")
print(f"Deleted {result.episodes_deleted} episodes, {result.memories_deleted} memories")
```

**TypeScript:**

```typescript
const result = await sw.deleteSubject("user-42");
console.log(`Deleted ${result.episodesDeleted} episodes, ${result.memoriesDeleted} memories`);
```

---

## Optional: run the full local stack (server + admin + website)

### Recommended — server + admin via `docker compose up -d`

The default `docker-compose.yml` in [statewave](https://github.com/smaramwbc/statewave) brings up **both** the API and the admin console (using the published [`statewavedev/statewave-admin`](https://hub.docker.com/r/statewavedev/statewave-admin) Docker Hub image) with one command:

```bash
git clone https://github.com/smaramwbc/statewave.git
cd statewave
docker compose up -d
# → API:   http://localhost:8100
# → Admin: http://localhost:8080
```

The compose file ships `ADMIN_AUTH_DISABLED=true` by default for the same reason it ships `STATEWAVE_DEBUG=true` — a fresh `docker compose up -d` should work without you having to invent a password first. **Don't expose this admin to the internet without overriding** (see the production-override block below).

If you only want the core API + DB, skip the admin service: `docker compose up -d api db`.

### Production override for the admin console

When you're not on localhost any more, the compose stack reads two env vars from your `.env` (or shell):

```bash
# in your .env (next to docker-compose.yml)
ADMIN_AUTH_DISABLED=          # leave empty to require auth
ADMIN_PASSWORD=$(openssl rand -base64 32)
ADMIN_SESSION_SECRET=$(openssl rand -hex 32)
```

`docker compose up -d` then forwards them through to the admin container, the auth-disabled flag is no longer set, and the login form gates access. See [statewave-admin SECURITY.md](https://github.com/smaramwbc/statewave-admin/blob/main/SECURITY.md) before exposing the console anywhere beyond your laptop.

### Marketing site / demo widget

The marketing/demo website is a Vite SPA — it doesn't have a Docker image, run it from source:

```bash
git clone https://github.com/smaramwbc/statewave-web.git
cd statewave-web
npm install
npm run dev
# → http://localhost:5173 (or next free port)
```

### Hacking on the admin from source (contributors)

If you're working on the admin codebase itself, you can still run it from source instead of pulling the image:

```bash
git clone https://github.com/smaramwbc/statewave-admin.git
cd statewave-admin
cat > .env.local << 'EOF'
STATEWAVE_API_URL=http://localhost:8100
ADMIN_AUTH_DISABLED=true
EOF
npm install
npm run dev
# → http://localhost:5173
```

Total time from `git clone` to API + admin running: typically **2–3 minutes** with Docker already installed (just one image pull).

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
| `readyz` `llm` check shows `"detail":"STATEWAVE_LITELLM_API_KEY is not set"` | The key isn't set/loaded. Edit `.env`, re-run `docker compose up -d`. Not applicable to local `ollama/*` models (no key needed). |
| `readyz` `database` check `"detail":"DATABASE_URL is not set"` | No DB URL configured. Set `STATEWAVE_DATABASE_URL` in `.env` (or use the bundled compose `db` service) and re-run `docker compose up -d`. |
| `readyz` `database` check `"detail":"DATABASE_URL is set but couldn't be parsed: …"` | The URL is malformed. Expected form: `postgresql+asyncpg://user:pass@host:5432/dbname`. |
| `readyz` `database` check `"detail":"Postgres unreachable: …"` | URL is valid but Postgres isn't responding. Check `docker compose logs db` — first start can take 5–10s for the pgvector image. |
| `401 missing_api_key` | Set `X-API-Key` header or remove `STATEWAVE_API_KEY` from `.env` |
| `422 validation_error` | Check request body — `subject_id`, `source`, `type`, `payload` are required |
| No memories after compile | Heuristic compiler extracts from conversation payloads with `messages[].content`. Switch to `STATEWAVE_COMPILER_TYPE=llm` for richer extraction. |
| Admin shows "ADMIN_PASSWORD and ADMIN_SESSION_SECRET are required" on login | **Compose path:** the default already sets `ADMIN_AUTH_DISABLED=true` — if you removed it or set it empty, either restore that or supply both `ADMIN_PASSWORD` + `ADMIN_SESSION_SECRET` in your `.env` and run `docker compose up -d --force-recreate admin`. **From source:** set `ADMIN_AUTH_DISABLED=true` in `statewave-admin/.env.local` and restart `npm run dev`. Production deploys must set the password instead. |
