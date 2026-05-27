# Repo Map

Version: **0.9.x**

## Ecosystem

| Project | Purpose | Version | License |
|---|---|---|---|
| Server | Core server — API, domain model, DB, services, deployment | 0.9.2 | Apache-2.0 |
| `statewave` (Python SDK) | Sync + async clients, typed exceptions, auth, batch, receipts + label / policy methods | 0.10.1 | Apache-2.0 |
| `@statewavedev/sdk` (TypeScript SDK) | Typed errors, auth, batch, ESM, receipts + label / policy methods | 0.10.1 | Apache-2.0 |
| Examples | Runnable demos, evals, benchmarks | — | Apache-2.0 |
| `@statewavedev/connectors-*` | Connector ecosystem — 11 source connectors (GitHub, Markdown, Slack, Discord, n8n, Zapier, Zendesk, Intercom, Freshdesk, Notion, Gmail) feeding real-world events into Statewave as normalized episodes, plus shared Core, CLI, Config, MCP-server, IDE-core, and Runner packages. Latest release wave: v0.17.0 (Tier 3 operator/cloud productization — config file, hosted runner, persistent state, OIDC, metrics, deployment recipes). | latest wave v0.17.0 | Apache-2.0 |
| Docs | Architecture, specs, ADRs, coordination (no runtime code) | — | Apache-2.0 |
| Website | Marketing website + embedded comparison demo (statewave.ai) | — | Apache-2.0 |
| Admin | Operator console — system health, jobs, usage (read-only) | — | Apache-2.0 |

## Dependency direction

```
Examples → SDKs (statewave / @statewavedev/sdk) → Server (HTTP API)
@statewavedev/connectors-*  → @statewavedev/connectors-core → Server (HTTP API)
Admin → Server (HTTP API)
Website → Server (HTTP API, via /api proxy for the embedded demo)
```

SDKs depend on the API contract. Examples depend on SDKs. Connectors depend on the API contract via the connector-core package — a connector for source X cannot pull in dependencies for source Y. Admin calls the API directly. Docs depend on nothing. Web is a static marketing site whose embedded chat-widget demo proxies to the live Statewave backend.

## Frontend repos explained

| Repo | Purpose | Audience |
|------|---------|----------|
| `statewave-web` | Public marketing site + embedded chat-widget comparison demo | Everyone (visitors and evaluators) |
| `statewave-admin` | Operator console — system health, job status, usage metering, internal | Operators running Statewave |

## Server structure

```
statewave/
  server/
    api/          # Route handlers (thin — delegate to services)
      episodes.py, memories.py, context.py, timeline.py, subjects.py
      handoff.py, resolutions.py, sla.py, health.py
      receipts.py, admin.py    # receipts read API + admin policy/tenant-config surface
    core/         # Cross-cutting: config, errors, middleware, auth, rate limit, tenant
    db/           # ORM tables, repositories, engine
    domain/       # Pure domain models (Pydantic, no ORM coupling)
    schemas/      # API request/response schemas
    services/     # Business logic
      compilers/  # BaseCompiler protocol, HeuristicCompiler, LLMCompiler
      embeddings/ # BaseEmbeddingProvider, StubProvider, LiteLLMProvider
      context.py    # Ranked, token-bounded, temporal context assembly
      handoff.py    # Handoff context-pack assembly
      conflicts.py  # Memory conflict resolution
      webhooks.py   # Event hook delivery
      receipts.py   # State-assembly receipt — emission decision, ULID, canonicalization, write
      policy.py     # Sensitivity-label policy — YAML bundle loader, evaluator, decision projection
  alembic/        # DB migrations (latest: 0019_per_tenant_bundles)
  tests/          # Unit + integration tests
```

## Test counts (as of v0.9.2)

| Project | Tests | Framework |
|---|---|---|
| Server | 869 | pytest + pytest-asyncio |
| `statewave` (Python SDK) | 73 | pytest |
| `@statewavedev/sdk` (TypeScript SDK) | 47 | vitest |
| `@statewavedev/connectors-*` | 606 | vitest |
| Examples | 3 eval suites (56 assertions), 2 benchmarks | pytest |

## Available examples

| Example | Language | Description |
|---------|----------|-------------|
| `minimal-quickstart` | Python | Basic record → compile → context loop |
| `support-agent-python` | Python | 2-session support agent with ranked context and provenance |
| `support-agent-llm` | Python | Full LLM loop — Statewave context → LLM → side-by-side response |
| `coding-agent-python` | Python | Coding assistant with project context recall across sessions |
| `eval-support-agent` | Python | Context quality eval (7 tests, 15 assertions) |
| `benchmark-support-agent` | Python | Statewave vs history stuffing vs RAG comparison |

All examples support `STATEWAVE_API_KEY` and `STATEWAVE_URL` environment variables.
