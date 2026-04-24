# Repo Map

Version: **0.4.x**

| Repo | Purpose | Version | License |
|------|---------|---------|----------|
| `statewave` | Core server, API, domain model, DB, services, deployment | 0.4.x | AGPL-3.0 |
| `statewave-py` | Official Python SDK (sync + async, typed exceptions, auth, batch) | 0.4.x | Apache-2.0 |
| `statewave-ts` | Official TypeScript SDK (typed errors, auth, batch, ESM) | 0.4.x | Apache-2.0 |
| `statewave-examples` | Example apps and quickstarts | — | Apache-2.0 |
| `statewave-docs` | Architecture, specs, ADRs, coordination (no runtime code) | — | Apache-2.0 |

## Dependency direction

```
statewave-examples → statewave-py / statewave-ts → statewave (API)
```

SDKs depend on the API contract. Examples depend on SDKs. Docs depend on nothing.

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
      embeddings/ # BaseEmbeddingProvider, StubProvider, OpenAIProvider
      context.py  # Ranked, token-bounded, temporal context assembly
      conflicts.py # Memory conflict resolution
      webhooks.py # Event hook delivery
  alembic/        # DB migrations (3 versions)
  tests/          # Unit + integration tests
```

## Test counts (as of v0.4.x)

| Repo | Tests | Framework |
|------|-------|----------|
| `statewave` | ~102 (70 unit + 32 integration) | pytest + pytest-asyncio |
| `statewave-py` | 14 | pytest |
| `statewave-ts` | ~10 | vitest |

## Available examples

| Example | Language | Description |
|---------|----------|-------------|
| `minimal-quickstart` | Python | Basic record → compile → context loop |
| `support-agent-python` | Python | 2-session support agent with ranked context and provenance |
| `coding-agent-python` | Python | Coding assistant with project context recall across sessions |

All examples support `STATEWAVE_API_KEY` and `STATEWAVE_URL` environment variables.
