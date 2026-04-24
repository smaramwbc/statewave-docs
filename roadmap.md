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

## v0.2 — Production hardening (current) 🔄
- [x] Idempotent memory compilation (no duplicates on recompile)
- [x] Pluggable compiler abstraction (`BaseCompiler` interface)
- [x] Token-bounded context assembly with configurable budget
- [x] Ranked retrieval (kind priority × recency × task relevance)
- [x] Structured error responses (`{error: {code, message, details}}`)
- [x] Request ID middleware (X-Request-ID header)
- [x] CORS configuration
- [x] Health endpoints (`/healthz`, `/readyz`)
- [x] Python SDK v0.2.0 — typed exceptions, async client, 14 tests
- [x] TypeScript SDK v0.2.0 — typed errors, 10 tests
- [x] Support-agent example (polished 2-session demo)
- [ ] LLM-backed memory compilation
- [ ] Embedding generation (OpenAI / local)
- [ ] Semantic search via pgvector
- [ ] Authentication / API keys
- [ ] Rate limiting

## v0.3 — Advanced features
- [ ] Temporal reasoning in context assembly
- [ ] Memory conflict resolution
- [ ] Webhooks / event hooks
- [ ] Multi-tenant support
- [ ] Dashboard UI
- [ ] Coding agent example
