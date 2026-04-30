# Repo Map

Version: **0.6.x**

## Ecosystem

| Repo | Purpose | Version | License |
|------|---------|---------|----------|
| `statewave` | Core server — API, domain model, DB, services, deployment | 0.6.x | AGPL-3.0 |
| `statewave-py` | Official Python SDK (sync + async, typed exceptions, auth, batch) | 0.4.x | Apache-2.0 |
| `statewave-ts` | Official TypeScript SDK (typed errors, auth, batch, ESM) | 0.4.x | Apache-2.0 |
| `statewave-examples` | Runnable demos, evals, benchmarks | — | Apache-2.0 |
| `statewave-docs` | Architecture, specs, ADRs, coordination (no runtime code) | — | Apache-2.0 |
| `statewave-demo` | Interactive public demo (side-by-side stateless vs memory) | — | Apache-2.0 |
| `statewave-web` | Marketing website (statewave.ai) | — | Apache-2.0 |
| `statewave-admin` | Operator console — system health, jobs, usage (early, read-only) | — | Apache-2.0 |

## Dependency direction

```
statewave-examples → statewave-py / statewave-ts → statewave (API)
statewave-demo → statewave-ts → statewave (API)
statewave-admin → statewave (API)
statewave-web (static, no server dependency)
```

SDKs depend on the API contract. Examples and demo depend on SDKs. Admin calls the API directly. Docs depend on nothing. Web is a static marketing site.

## Frontend repos explained

| Repo | Purpose | Audience |
|------|---------|----------|
| `statewave-web` | Public marketing site — what is Statewave, why it matters, how to start | Everyone |
| `statewave-demo` | Interactive demo — see AI with vs without memory, no setup required | Evaluators, developers |
| `statewave-admin` | Operator console — system health, job status, usage metering, internal | Operators running Statewave |

## Server structure

```
statewave/
  server/
    api/          # Route handlers (thin — delegate to services)
      episodes.py, memories.py, context.py, timeline.py, subjects.py
    core/         # Cross-cutting: config, errors, middleware, auth, rate limit, tenant
    db/           # ORM tables, repositories, engine
    domain/       # Pure domain models (Pydantic, no ORM coupling)
    schemas/      # API request/response schemas
    services/     # Business logic
      compilers/  # BaseCompiler protocol, HeuristicCompiler, LLMCompiler
      embeddings/ # BaseEmbeddingProvider, StubProvider, LiteLLMProvider
      context.py  # Ranked, token-bounded, temporal context assembly
      conflicts.py # Memory conflict resolution
      webhooks.py # Event hook delivery
  alembic/        # DB migrations (3 versions)
  tests/          # Unit + integration tests
```

## Test counts (as of v0.6.1)

| Repo | Tests | Framework |
|------|-------|----------|
| `statewave` | 232+ | pytest + pytest-asyncio |
| `statewave-py` | 14 | pytest |
| `statewave-ts` | ~10 | vitest |
| `statewave-examples` | 3 eval suites (54 assertions), 2 benchmarks | pytest |

## Available examples

| Example | Language | Description |
|---------|----------|-------------|
| `minimal-quickstart` | Python | Basic record → compile → context loop |
| `support-agent-python` | Python | 2-session support agent with ranked context and provenance |
| `support-agent-llm` | Python | Full LLM loop — Statewave context → LLM → side-by-side response |
| `coding-agent-python` | Python | Coding assistant with project context recall across sessions |
| `eval-support-agent` | Python | Context quality eval (7 tests, 14 assertions) |
| `benchmark-support-agent` | Python | Statewave vs history stuffing vs RAG comparison |

All examples support `STATEWAVE_API_KEY` and `STATEWAVE_URL` environment variables.
