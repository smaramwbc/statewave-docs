# Development Conventions

Version: **1.3.x**

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
- Server: ~944 tests (unit + integration; integration requires Postgres)
- Python SDK: 80 tests
- TypeScript SDK: 50 tests
- Integration tests use a separate test database via `conftest.py` with `NullPool`
- New features should include unit tests; integration tests for data-path changes

## CI

All repos have GitHub Actions CI workflows:
- Server: lint + unit tests + integration tests on push/PR
- Python SDK (`statewave`): lint + tests on push/PR
- TypeScript SDK (`@statewavedev/sdk`): build + tests on push/PR

## Versioning

Each package is versioned **independently, per semver, per repo**. There is no
single workspace version that every package must match:

- The Python SDK (`statewave`, PyPI), the TypeScript SDK (`@statewavedev/sdk`,
  npm), and the server release on their own cadences. A TS-only change bumps
  only the TS SDK; it does not force a Python or server release.
- The cross-repo **compatibility axis is the `/v1` API contract** — any SDK
  that speaks `/v1` works against any server that serves `/v1`. That guarantee
  lives in [the API contract](../api/v1-contract.md), not in matching version
  numbers. SDK ↔ server compatibility never depends on equal version strings.
- `statewave/pyproject.toml` is the **server / reference-implementation
  version**. It backs only the server repo's own status surfaces and the
  conceptual-doc banners ("the system as implemented at server vX.Y").
- Tooling: `tools/check-versions.py` (run as a release gate in `statewave`
  `.github/workflows/release.yml`) verifies that server/contract self-reference
  *only*. It never asserts SDK-package-number equality — independent SDK
  versions are reported, never failed. `tools/bump-version.py` propagates a
  *server* bump to server surfaces; SDK packages are bumped in their own repos.

SDK feature surface (current version is whatever each registry last published):

| SDK | Key features |
|-----|--------------|
| `statewave` (Python) | Sync + async clients, typed exceptions, auth, tenant, semantic search, batch ingestion, subject listing, receipts + label / policy methods |
| `@statewavedev/sdk` (TypeScript) | Typed errors, auth, tenant, semantic search, batch ingestion, subject listing, ESM, receipts + label / policy methods |

## Configuration

All server settings via `STATEWAVE_` prefixed env vars or `.env` file. See [API contract](../api/v1-contract.md) for the full configuration reference.

## Git

- Conventional commits preferred
- One logical change per commit
- PRs should reference the target repo clearly
- Version tags: each repo tags its **own independent** `vX.Y.Z` when *it*
  releases; there is no synchronized workspace-wide tag (see Versioning above)
