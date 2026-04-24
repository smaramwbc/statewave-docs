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

## Testing
- pytest for Python repos
- vitest for TypeScript repos
- Unit tests for services and domain logic
- Integration tests against a test database (future)

## Git
- Conventional commits preferred
- One logical change per commit
- PRs should reference the target repo clearly
