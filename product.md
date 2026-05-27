# What is Statewave?

Statewave is an **open-source memory runtime for AI agents**. It compiles raw events into ranked, token-bounded context bundles with full provenance — so your AI stops forgetting across sessions. Self-hosted on Postgres, no vendor lock-in.

It gives your AI system durable, structured memory — so it can remember what happened, learn from past interactions, and retrieve relevant context at task time.

## Core idea

Most AI applications treat context as disposable. Statewave treats it as infrastructure.

1. **Ingest raw events** (episodes) — conversations, tool calls, decisions, observations
2. **Compile durable memories** — typed, summarised, confidence-scored, with provenance back to source episodes
3. **Retrieve relevant context** — filtered, scored, and token-budgeted for your prompt
4. **Inspect and delete by subject** — full timeline visibility and GDPR-style erasure

Everything is organised around **subjects** — a user, account, workspace, repo, ticket, or agent.

## What Statewave is

- A self-hosted API server you run alongside your application
- A structured memory store backed by Postgres + pgvector
- A context assembly engine that returns prompt-ready bundles with token estimates
- A provenance system that traces every memory back to its source episodes
- A governance layer ([receipts](receipts.md) + [sensitivity labels & policy](sensitivity-labels.md)) that records *which memories influenced each agent response* with byte-level integrity hashes, and filters per-memory access by caller identity through declarative YAML policy
- Framework-neutral — works with any AI stack, any language

## What Statewave is not

- Not a chatbot or agent framework
- Not a vector database (it uses one internally, but that's an implementation detail)
- Not a RAG pipeline (retrieval is one capability, not the whole product)
- Not an SDK wrapper around an LLM provider
- Not a hosted SaaS (you run it yourself)

## Best current use cases

- **Support agents** that remember customer history across sessions ← primary focus
- **Coding agents** that accumulate project knowledge over time
- **Workflow automation** that needs to recall decisions and outcomes
- **Any AI application** where "what happened before" matters for "what to do next"

> **Current focus:** Statewave is purpose-built for support-agent workflows first. The [eval](https://github.com/smaramwbc/statewave-examples/tree/main/eval-support-agent) and [benchmark](https://github.com/smaramwbc/statewave-examples/tree/main/benchmark-support-agent) prove context quality for this use case.
>
> **Looking for ideas?** The [Use Cases map at statewave.ai/use-cases](https://statewave.ai/use-cases) is the broader inventory — categorized workflows, connector/import patterns (existing data → episodes → compiled memory → context), and frontier directions. The list above is what's strongest *today*; the map is what the platform makes possible.

## Current limitations

Statewave is in active early development (v0.9.0). We document these honestly:

| Limitation | Impact | Status |
|-----------|--------|--------|
| Multi-tenant is app-layer only | Real query-level isolation, no Postgres RLS yet | Future: row-level security |
| Rate limiting is per-IP only | No per-tenant or per-API-key limits yet | Future: per-tenant limits |
| Single-Postgres only | Multi-replica API deployments supported and verified since v0.8 (Fly multi-machine + Helm HPA); cross-region / multi-Postgres clustering not yet shipped | Future: clustering guide |
| Admin console is early | Dashboards plus policy/tenant-config management; no memory editing or advanced ops | Active development |

**What works well today:**
- Episode ingestion (single + batch, append-only, durable)
- Memory compilation (heuristic or LLM via [LiteLLM](https://github.com/BerriAI/litellm) — 100+ providers)
- Context assembly (ranked, token-bounded, with provenance)
- Memory expiry — per-kind global TTL windows; retrieval filters expired memories immediately, hourly cleanup tombstones soft-deleted rows ([memory-ttl.md](deployment/memory-ttl.md))
- Subject lifecycle (timeline, search, deletion)
- Self-hosted deployment (Docker, Fly.io, bare metal)

## API surface

| Endpoint | Purpose |
|---|---|
| `POST /v1/episodes` | Ingest a single episode |
| `POST /v1/episodes/batch` | Ingest up to 100 episodes |
| `POST /v1/memories/compile` | Compile memories from episodes |
| `GET /v1/memories/search` | Search memories by query |
| `POST /v1/context` | Assemble a context bundle |
| `POST /v1/handoff` | Generate a handoff context pack (health-aware) |
| `GET /v1/subjects/{id}/health` | Customer health score + explainable factors |
| `GET /v1/subjects/{id}/sla` | SLA metrics — response time, resolution time, breach flags |
| `webhook: subject.health_degraded` | Fires when health state worsens (healthy→watch, watch→at_risk) |
| `webhook: subject.health_improved` | Fires when health state recovers (at_risk→watch, watch→healthy) |
| `GET /v1/receipts/{id}` | Fetch one state-assembly receipt by ULID |
| `GET /v1/receipts` | List receipts for a subject (cursor-paginated) |
| `PATCH /v1/memories/{id}/labels` | Set per-memory sensitivity labels |
| `GET /v1/timeline` | View subject timeline |
| `GET /v1/subjects` | List subjects with counts |
| `DELETE /v1/subjects/{id}` | Delete all data for a subject |
| `GET / PATCH /admin/tenants/{id}/config` | Per-tenant config — receipts emission, retention, policy_mode, caller-identity gate |
| `POST /admin/policy/bundles` | Upload (and optionally activate) a YAML policy bundle |
| `POST /admin/policy/activate` | Switch active bundle for a scope |
| `GET /v1/memory-templates` | List bundled memory templates (declarative scaffolds for recurring patterns) |
| `GET /v1/memory-templates/{id}` | Fetch a single memory template — fields, types, content scaffold |
| `POST /v1/memory-templates/{id}/apply` | Validate field values against a template and ingest the resulting episode |

## SDKs

- **Python** — `pip install statewave` · sync and async clients, Pydantic models · [source](https://github.com/smaramwbc/statewave-py)
- **TypeScript** — `npm install @statewavedev/sdk` · fetch-based client, full type definitions · [source](https://github.com/smaramwbc/statewave-ts)

## Getting started

See the [getting started guide](getting-started.md) for setup instructions, or jump to [examples](https://github.com/smaramwbc/statewave-examples).
