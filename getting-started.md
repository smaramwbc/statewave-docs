# Getting Started with Statewave

Statewave is an open-source **memory runtime for AI agents**. It records raw
events, compiles them into structured memories, and assembles ranked,
token-bounded context bundles you can drop straight into a prompt — so your
agent stops forgetting across sessions.

This guide gets a local server running with Docker Compose, then stores and
retrieves your first memory. It takes about **5 minutes** and needs **no API
key** — just Docker.

---

## 5-minute quickstart

The fastest path to a running Statewave is Docker Compose. It starts the API
and a Postgres database, and runs the database migrations for you.

**Prerequisites — one thing:**

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS /
  Windows), or [Docker Engine](https://docs.docker.com/engine/install/) with
  the [Compose plugin](https://docs.docker.com/compose/install/) (Linux).

You do **not** need Python, Node, an LLM API key, or any SDK to finish this
guide. Those come later, and every one of them is optional.

### Fastest path — one line to a running server

If you'd rather skip the manual setup, one of these one-liners brings up a
local Statewave server for you:

```bash
# macOS / Linux
npx @statewavedev/statewave
# or
curl -fsSL https://www.statewave.ai/install | sh
```

```powershell
# Windows (PowerShell)
irm https://www.statewave.ai/install.ps1 | iex
```

Once it reports the API is up on `http://localhost:8100`, skip ahead to
[Step 2 — Verify it is running](#step-2--verify-it-is-running). Prefer to drive
the setup yourself (and keep a checkout for editing `.env`)? Follow the manual
Docker Compose path below.

### Step 1 — Start the server

```bash
git clone https://github.com/smaramwbc/statewave.git
cd statewave
cp .env.example .env
docker compose up -d
```

That is the whole setup. `docker compose up -d` pulls the images, starts
Postgres + the API, and runs migrations automatically on first boot. The very
first start can take a minute or two while the images download.

> **Returning user?** If you have run Statewave before, run `docker compose pull`
> before `docker compose up -d` to refresh cached images. `up -d` alone reuses
> whatever is already cached locally, so a host that pulled `:latest` weeks ago
> stays on that older image until you ask for a refresh.
>
> **No API key is needed for this guide.** The copied `.env` leaves the LLM
> key blank, so Statewave starts in **demo mode** — a local regex compiler and
> hash-based embeddings, with no external calls. Every step below works in
> demo mode. You will see one `llm_compiler_missing_api_key` warning line in
> the logs; that is expected, not an error. To switch on real LLM extraction
> and semantic search later, see
> [Turn on a real LLM provider](#turn-on-a-real-llm-provider).

### Step 2 — Verify it is running

```bash
curl http://localhost:8100/healthz
# → {"status":"ok"}

curl http://localhost:8100/readyz
# → {"status":"ready","checks":[ ... ]}
```

- `/healthz` — the API process is alive.
- `/readyz` — the API **and** its database are ready to serve requests.

If `/readyz` is not `ready` yet, wait about 10 seconds (Postgres is still
starting on the first run) and try again. Still stuck? Jump to
[If something goes wrong](#if-something-goes-wrong).

### Step 3 — Store a memory

Statewave's data model is three steps: **ingest** raw episodes → **compile**
them into memories → **retrieve** ranked context. Steps 3 and 4 do all three.

First, ingest an episode — a raw interaction record Statewave will remember:

```bash
curl -X POST http://localhost:8100/v1/episodes \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "user-1",
    "source": "chat",
    "type": "conversation",
    "payload": {"messages": [
      {"role": "user", "content": "My name is Alice and I work at Globex Corp."}
    ]}
  }'
# → {"id":"ecacebed-8c69-44d5-86f1-97746bdd4cd2","subject_id":"user-1","source":"chat","type":"conversation","payload":{"messages":[{"role":"user","content":"My name is Alice and I work at Globex Corp."}]},...}
```

A **subject** is any entity you track — a user, account, agent, or repo. Here
it is `user-1`.

Now compile — turn raw episodes into structured memory:

```bash
curl -X POST http://localhost:8100/v1/memories/compile \
  -H "Content-Type: application/json" \
  -d '{"subject_id": "user-1"}'
# → {"subject_id":"user-1","memories_created":1,"memories":[ ... ]}
```

`memories_created` should be `1` or more. Compilation is **idempotent** —
running it again only processes new episodes.

### Step 4 — Retrieve it

Ask Statewave to assemble context for a task:

```bash
curl -X POST http://localhost:8100/v1/context \
  -H "Content-Type: application/json" \
  -d '{"subject_id": "user-1", "task": "Who is this user?", "max_tokens": 500}'
# → {"subject_id":"user-1","task":"Who is this user?","facts":[...]}
```

The response's `assembled_context` field is a ready-to-use string for an LLM
prompt — it contains what Statewave compiled about `user-1`, including the
facts that Alice works at Globex Corp.

**That is the whole loop — ingest → compile → retrieve.** You now have a
working Statewave server. Everything below is optional.

---

## If something goes wrong

| Symptom | Fix |
|---|---|
| `docker: command not found`, or `Cannot connect to the Docker daemon` | Docker is not installed or not running. Install / open **Docker Desktop**, wait until it reports "running", then retry. |
| `Error ... port is already allocated` / `bind: address already in use` on `8100` | Another process owns port 8100. Free it, or run on a different host port: add `STATEWAVE_API_HOST_PORT=8101` to `.env`, run `docker compose up -d` again, and use `localhost:8101` everywhere below. |
| `curl: (7) Connection refused` on `localhost:8100` | The API container is not up yet. Check `docker compose ps` (the `api` service should be `running`) and `docker compose logs api`. On first boot, also give Postgres ~10 seconds to start. |
| `/readyz` shows the `database` check failing, or returns `503` | Postgres is not healthy yet. Run `docker compose ps` — the `db` service should be `healthy` — and `docker compose logs db`. The first start of the pgvector image can take 10–20 seconds. |
| `cp: .env.example: No such file or directory` | You are not in the `statewave` directory. Run `cd statewave` first (the folder `git clone` created). |
| `.env` is missing | The server still boots on built-in defaults, but `cp .env.example .env` is the documented path. Re-run it from inside the `statewave` directory. |
| `/readyz` shows `"llm" ... "STATEWAVE_LITELLM_API_KEY is not set"` | **Expected in demo mode** — there is no key, so there is nothing to check. Overall status is still `ready`. Set a key only when you want real LLM extraction (see the next section). |
| You set an API key in `.env` but it is not picked up | `.env` must sit next to `docker-compose.yml`, and containers read it only at start. After editing `.env`, run `docker compose up -d` again to recreate the containers. |
| Ollama: `host.docker.internal` does not resolve (Linux) | On Linux without Docker Desktop, add `extra_hosts: ["host.docker.internal:host-gateway"]` to the `api` service in `docker-compose.yml`, or point `STATEWAVE_LITELLM_API_BASE` at your host's LAN IP. |
| `422 validation_error` | The request body is missing a required field — `subject_id`, `source`, `type`, and `payload` are all required on `/v1/episodes`. |
| `401 missing_api_key` | The server has `STATEWAVE_API_KEY` set. Send it as an `X-API-Key` header, or unset it in `.env` for open local dev. |
| Server starts but seems to be missing a feature you read about in newer docs | You may be on a stale cached image. Run `docker compose pull` then `docker compose up -d` to refresh to the current `:latest`. `up -d` alone does not pull if there's already a cached image on the host. |

**Reset everything.** To wipe all containers and data and start clean:

```bash
docker compose down -v
```

The `-v` flag also deletes the Postgres volume, so every episode and memory is
removed. Then run `docker compose up -d` again for a fresh server.

For a fuller walk-through of these first-run issues (Symptom → Cause → Fix),
see the [troubleshooting page](troubleshooting.md). For production-side issues,
see [deployment troubleshooting](deployment/troubleshooting.md).

---

## Build with the SDKs

The quickstart used `curl` so it works with zero install. For real
applications, use a typed SDK — both wrap the same HTTP API. This step is
optional; skip it if you are calling the API directly.

**Python** — `pip install statewave`:

```python
from statewave import StatewaveClient

with StatewaveClient("http://localhost:8100") as sw:
    sw.create_episode(
        subject_id="user-1",
        source="chat",
        type="conversation",
        payload={"messages": [
            {"role": "user", "content": "My name is Alice and I work at Globex Corp."}
        ]},
    )
    sw.compile_memories("user-1")
    ctx = sw.get_context("user-1", task="Who is this user?", max_tokens=500)
    print(ctx.assembled_context)
```

**TypeScript** — `npm install @statewavedev/sdk`:

```typescript
import { StatewaveClient } from "@statewavedev/sdk";

const sw = new StatewaveClient("http://localhost:8100");

await sw.createEpisode({
  subjectId: "user-1",
  source: "chat",
  type: "conversation",
  payload: { messages: [
    { role: "user", content: "My name is Alice and I work at Globex Corp." },
  ]},
});
await sw.compileMemories("user-1");
const ctx = await sw.getContext({
  subjectId: "user-1",
  task: "Who is this user?",
  maxTokens: 500,
});
console.log(ctx.assembledContext);
```

The SDKs also cover batch ingestion, timelines, search, subject deletion,
authentication, multi-tenancy, and audit receipts. Full reference:

- **[statewave-py](https://github.com/smaramwbc/statewave-py)** — Python SDK (sync + async clients)
- **[statewave-ts](https://github.com/smaramwbc/statewave-ts)** — TypeScript SDK
- **[API v1 contract](api/v1-contract.md)** — every endpoint, for any language over plain HTTP

---

## Turn on a real LLM provider

Demo mode is perfect for a first run, but its regex compiler and hash-based
embeddings do not do real semantic search. For production-quality memory, give
Statewave an LLM provider. There are three modes:

| Mode | What you get | Setup |
|---|---|---|
| **Demo mode** *(default)* | Local regex extraction, no semantic search, zero external calls, no key. | Nothing — this is `.env.example` as shipped. |
| **Hosted provider** | Real LLM extraction + semantic search via OpenAI, Anthropic, Azure, Bedrock, and 100+ others. | Set one API key in `.env`. |
| **Ollama (local LLM)** | Real LLM extraction on your own machine — no key, no external calls. | Point Statewave at a local Ollama server. |

To use a **hosted provider**, edit `.env`:

```bash
STATEWAVE_COMPILER_TYPE=llm
STATEWAVE_EMBEDDING_PROVIDER=litellm
STATEWAVE_LITELLM_API_KEY=sk-...                  # your provider key
STATEWAVE_LITELLM_MODEL=gpt-4o-mini               # any LiteLLM model id
STATEWAVE_LITELLM_EMBEDDING_MODEL=text-embedding-3-small
```

Then run `docker compose up -d` again to pick up the change. Statewave routes
every call through [LiteLLM](https://github.com/BerriAI/litellm), so switching
providers is just a different model id.

To use **Ollama** (local LLM, no key), edit `.env`:

```bash
STATEWAVE_COMPILER_TYPE=llm
STATEWAVE_LITELLM_MODEL=ollama/llama3
STATEWAVE_LITELLM_API_BASE=http://host.docker.internal:11434   # API container → host Ollama
```

The `ollama/` model prefix tells Statewave the provider is local, so no API
key is expected. One networking gotcha: `host.docker.internal` resolves
automatically on **Docker Desktop** (macOS/Windows), but **not** on Linux with
Docker Engine. There, add this to the `api` service in `docker-compose.yml`:

```yaml
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

(or point `STATEWAVE_LITELLM_API_BASE` at your host's LAN IP instead). Make
sure the model is pulled first — `ollama pull llama3` — then run
`docker compose up -d` again.

For local embedding dimensions and the full provider matrix, see
**[LLM and embedding provider configuration](deployment/guide.md#llm-and-embedding-provider-configuration)**.

> **Confirm a key was picked up:** run `curl http://localhost:8100/readyz`. When
> a key is set, the `llm` check makes a real provider call. If it still says
> `STATEWAVE_LITELLM_API_KEY is not set`, the key is not being read — check
> that `.env` sits next to `docker-compose.yml` and re-run `docker compose up -d`.

---

## Require an API key

For local development Statewave runs in open-access mode. To require
authentication, set a key in `.env`:

```bash
STATEWAVE_API_KEY=my-secret-key-123
```

Run `docker compose up -d` again, then send the key on every request with the
`X-API-Key` header (`curl -H "X-API-Key: my-secret-key-123" ...`), or pass it
to the SDK client constructor.

---

## Run the full local stack

The default `docker compose up -d` already starts an **operator console**
alongside the API:

- **API** — `http://localhost:8100`
- **Admin console** — `http://localhost:8080` — browse subjects, episodes, and memories

The compose file ships `ADMIN_AUTH_DISABLED=true` so a fresh start needs no
password. **Do not expose this admin to the internet without setting one** —
see [statewave-admin](https://github.com/smaramwbc/statewave-admin) for
production auth.

Want only the core API + database? Run `docker compose up -d api db`.

The marketing website and interactive demo is a separate app — see
[statewave-web](https://github.com/smaramwbc/statewave-web) to run it from
source.

---

## Next steps

- **Runnable examples** — [statewave-examples](https://github.com/smaramwbc/statewave-examples):
  a [minimal quickstart](https://github.com/smaramwbc/statewave-examples/tree/main/minimal-quickstart),
  support agents, a coding agent, evals, and benchmarks.
- **Interactive API docs** — `http://localhost:8100/docs` (Swagger) once the server is running.
- **Feed real data in** — [Connectors](connectors/index.md) ingest GitHub,
  Markdown/docs, Slack, support tickets, email, and more as episodes — with no
  custom ingest code.
- **Understand the design** — [Architecture overview](architecture/overview.md) ·
  [Compiler modes](architecture/compiler-modes.md) ·
  [Privacy & data flow](architecture/privacy-and-data-flow.md).
- **Go to production** — [Deployment guide](deployment/guide.md) ·
  [Sizing guide](deployment/sizing.md) ·
  [Deployment troubleshooting](deployment/troubleshooting.md).
- **Every config option** — [`.env.example`](https://github.com/smaramwbc/statewave/blob/main/.env.example)
  lists all `STATEWAVE_*` settings.
