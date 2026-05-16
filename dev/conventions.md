# Development Conventions

Version: **0.8.x**

## Code style

- **Python:** type hints everywhere, ruff for formatting/linting, Python 3.11+
- **TypeScript:** strict mode, ESM, Node 18+
- Docstrings on public APIs and modules

## Architecture rules

- Route handlers must be thin — delegate to services
- Business logic in `server/services/`
- Data access in `server/db/repositories.py` — all SQL lives here
- Domain types in `server/domain/models.py`
- API schemas in `server/schemas/` (requests.py, responses.py)
- Error definitions in `server/core/errors.py`
- Middleware in `server/core/` (middleware.py, auth.py, ratelimit.py, tenant.py)
- Compilers implement `server/services/compilers.BaseCompiler` protocol
- Embedding providers implement `server/services/embeddings.BaseEmbeddingProvider` protocol

## Error handling

- All errors return structured `{"error": {"code", "message", "details", "request_id"}}` shape
- Custom exceptions (`NotFoundError`, `ConflictError`, `ValidationError`) in `server/core/errors.py`
- Middleware errors (auth, rate limit, tenant) use the same JSON shape
- SDKs parse these into typed exception classes

## Testing

- **pytest** for Python repos (server + SDK), `asyncio_mode = "auto"`
- **vitest** for TypeScript SDK
- Server: ~680 tests (unit + integration; integration requires Postgres)
- Python SDK: 34 tests
- TypeScript SDK: 23 tests
- Integration tests use a separate test database via `conftest.py` with `NullPool`
- New features should include unit tests; integration tests for data-path changes

## CI

All repos have GitHub Actions CI workflows:
- Server: lint + unit tests + integration tests on push/PR
- Python SDK (`statewave`): lint + tests on push/PR
- TypeScript SDK (`@statewavedev/sdk`): build + tests on push/PR

## SDK versions

| SDK | Version | Key features |
|-----|---------|-------------|
| `statewave` (Python) | 0.7.x | Sync + async clients, typed exceptions, auth, tenant, semantic search, batch ingestion, subject listing |
| `@statewavedev/sdk` (TypeScript) | 0.7.x | Typed errors, auth, tenant, semantic search, batch ingestion, subject listing, ESM |

## Configuration

All server settings via `STATEWAVE_` prefixed env vars or `.env` file. See [API contract](../api/v1-contract.md) for the full configuration reference.

## Git

- Conventional commits preferred
- One logical change per commit
- PRs should reference the target repo clearly
- Version tags: `v0.X.Y` on each repo
