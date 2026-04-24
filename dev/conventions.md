# Development Conventions

## Code style

- Python: type hints everywhere, ruff for formatting/linting
- TypeScript: strict mode, ESM
- Docstrings on public APIs

## Architecture rules

- Route handlers must be thin — delegate to services
- Business logic in `server/services/`
- Data access in `server/db/repositories.py`
- Domain types in `server/domain/models.py`
- API schemas in `server/schemas/`
- Error definitions in `server/core/errors.py`
- Middleware in `server/core/middleware.py`
- Compilers implement `server/services/compilers/base.BaseCompiler`

## Error handling

- All errors return structured `{"error": {"code", "message", "details", "request_id"}}` shape
- Custom exceptions (`NotFoundError`, `ConflictError`, `ValidationError`) in `server/core/errors.py`
- SDKs parse these into typed exception classes

## Testing

- **pytest** for Python repos (server + SDK)
- **vitest** for TypeScript SDK
- Server: 25 unit tests + 15 integration tests (requires Postgres)
- Python SDK: 14 tests
- TypeScript SDK: 10 tests
- Integration tests use a separate test database with NullPool to avoid connection leaks

## CI

All repos have GitHub Actions CI workflows:
- `statewave`: lint + unit tests on push/PR
- `statewave-py`: lint + tests on push/PR
- `statewave-ts`: build + tests on push/PR

## SDK versions

| SDK | Version | Key features |
|-----|---------|-------------|
| statewave-py | 0.2.0 | Sync + async clients, typed exceptions, Pydantic models |
| statewave-ts | 0.2.0 | Typed errors, full type exports, ESM |

## Git

- Conventional commits preferred
- One logical change per commit
- PRs should reference the target repo clearly
