# Roadmap

## v0.1 — Local MVP ✅
- [x] Core domain model (Episode, Memory, ContextBundle)
- [x] FastAPI server with all 6 endpoints
- [x] Heuristic memory compiler
- [x] Context assembly with token estimation
- [x] PostgreSQL + pgvector schema
- [x] Docker Compose local deployment
- [x] Python SDK v0.1.0
- [x] TypeScript SDK v0.1.0
- [x] Minimal quickstart example
- [x] Alembic initial migration
- [x] Integration tests (15 integration + 25 unit)
- [x] CI/CD pipeline (GitHub Actions for server + both SDKs)

## v0.2 — Production hardening ✅
- [x] Idempotent memory compilation (no duplicates on recompile)
- [x] Pluggable compiler abstraction (`BaseCompiler` interface)
- [x] Token-bounded context assembly with configurable budget
- [x] Ranked retrieval (kind priority × recency × task relevance)
- [x] Structured error responses (`{error: {code, message, details}}`)
- [x] Request ID middleware (X-Request-ID header)
- [x] CORS configuration
- [x] Health endpoints (`/healthz`, `/readyz`)
- [x] Structured logging (structlog, JSON in prod, console in dev)
- [x] Python SDK v0.2.0 — typed exceptions, async client, 14 tests
- [x] TypeScript SDK v0.2.0 — typed errors, 10 tests
- [x] Support-agent example (polished 2-session demo)
- [x] LLM-backed memory compilation
- [x] Embedding generation (OpenAI / local)
- [x] Semantic search via pgvector
- [x] Authentication / API keys
- [x] Rate limiting

## v0.3 — Advanced features ✅
- [x] Temporal reasoning in context assembly
- [x] Memory conflict resolution
- [x] Webhooks / event hooks
- [x] Multi-tenant support (experimental — header extraction only)
- [x] Coding agent example

## v0.3.5 — Stabilization ✅
- [x] Fix middleware execution order (CORS → RequestID → Auth → RateLimit → Tenant)
- [x] Fix compile + conflict resolution transaction split (single commit)
- [x] Add request validation (min/max lengths, payload not empty, bounded limits)
- [x] Fix LLM compiler event loop blocking (ThreadPoolExecutor)
- [x] Episode route uses repository layer
- [x] Add auth support to Python SDK (`api_key` constructor param)
- [x] Add auth support to TypeScript SDK (`apiKey` constructor option)
- [x] Add semantic search param to both SDKs
- [x] Add tenant header support to both SDKs
- [x] Update examples with auth support via env vars
- [x] Add coding-agent to examples README
- [x] Demote multi-tenant to experimental with clear docs
- [x] Align all version numbers to 0.3.5
- [x] Update API contract doc to match v0.3 reality
- [x] Update architecture docs and write v0.3 ADR
- [x] Update repo-map and conventions docs

## v0.4 — Next
- [ ] Dashboard UI
- [ ] Memory expiry / TTL policies
- [ ] Batch episode ingestion
- [ ] SDK webhook listener helpers
- [ ] OpenTelemetry tracing
- [ ] Deployment guides (Docker, fly.io, Railway)
