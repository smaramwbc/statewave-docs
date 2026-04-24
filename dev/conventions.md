# Development Conventions

Version: **0.3.5**

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
- Server: 97 tests (75 unit + 22 integration; integration requires Postgres)
- Python SDK: 14 tests (model parsing + exports)
- TypeScript SDK: ~10 tests (construction + error classes)
- Integration tests use a separate test database via `conftest.py` with `NullPool`
- New features should include unit tests; integration tests for data-path changes

## CI

All repos have GitHub Actions CI workflows:
- `statewave`: lint + unit tests + integration tests on push/PR
- `statewave-py`: lint + tests on push/PR
- `statewave-ts`: build + tests on push/PR

## SDK versions

| SDK | Version | Key features |
|-----|---------|-------------|
| statewave-py | 0.3.5 | Sync + async clients, typed exceptions, auth (`api_key`), tenant (`tenant_id`), semantic search |
| statewave-ts | 0.3.5 | Typed errors, auth (`apiKey`), tenant (`tenantId`), semantic search, full type exports, ESM |

## Configuration

All server settings via `STATEWAVE_` prefixed env vars or `.env` file. See [API contract](../api/v1-contract.md) for the full configuration reference.

## Git

- Conventional commits preferred
- One logical change per commit
- PRs should reference the target repo clearly
- Version tags: `v0.X.Y` on each repo
