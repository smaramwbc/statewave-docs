# Changelog

All notable changes to the Statewave workspace.

## v0.6.1 — Support-Agent Superiority (2026-04-29)

### Added
- **Session-aware context assembly** — active session boosted, resolved sessions deprioritized
- **Resolution tracking** — `POST /v1/resolutions`, `GET /v1/resolutions` for open/resolved/unresolved state per session
- **Handoff context packs** — `POST /v1/handoff` generates compact escalation briefs with customer summary, active issue, attempted steps, resolution history, health, and SLA context
- **Customer health scoring** — `GET /v1/subjects/{id}/health` returns deterministic 0–100 score with explainable factors (unresolved issues, repeats, escalations, idle open issues, SLA breaches, slow response)
- **Repeat-issue detection** — surfaces prior resolutions when episode patterns recur
- **Support-specific ranked retrieval** — session awareness, resolution status, and health signals feed into context ranking
- **Health-aware handoff** — risk level, score, and top factors appear in handoff briefs
- **Proactive health alerts** — `subject.health_degraded` and `subject.health_improved` webhooks on state transitions
- **SLA tracking** — `GET /v1/subjects/{id}/sla` computes first-response time, resolution time, and breach flags per session with configurable thresholds
- **SLA integration** — breach signals feed into health scoring; SLA summary appears in handoff packs when relevant

### Proof layer
- 3 eval suites: context quality (7 tests, 14 assertions), handoff (7 tests, 16 assertions), advanced (7 tests, 24 assertions)
- 2 benchmarks: context recall + workflow comparison (Statewave 9/9 vs Naive 2/9)
- 232 unit tests passing

### Changed
- Health scoring now includes SLA breach penalty and slow first-response penalty
- Handoff packs now include conditional SLA section (absent when clean)
- Context ranking formula updated with session and resolution awareness

## v0.5.0 — Reliability & Trust (2026-04-29)

### Added
- **True multi-tenant isolation** — tenant_id persisted on all tables, all queries scoped by tenant
- **Distributed rate limiting** — Postgres-backed fixed-window, survives restarts, multi-worker
- **Backup/restore tooling** — subject-level export/import via admin API with SHA-256 checksum
- **Tenant audit endpoint** — `GET /admin/tenant-audit` for NULL-tenant row discovery
- **Admin export/import** — `GET /admin/export/{subject_id}`, `POST /admin/import`
- Operator upgrade guidance for pre-tenant data backfill

### Changed
- Rate limiting now defaults to `distributed` strategy (Postgres-backed)
- Tenant middleware no longer experimental — real data isolation enforced
- Background cleanup loop now also handles rate limit window pruning

### Migrations
- `0008_add_tenant_id_columns` — tenant_id + indexes on episodes, memories, webhook_events, subject_snapshots
- `0009_add_rate_limit_table` — rate_limit_hits table for distributed rate limiting

## v0.4.3 — Public Release Polish (2026-04-25)

### Improved
- README rewrite across all repos — accurate product framing, docs navigation, current limitations
- Consistent tagline and cross-repo linking
- SDK READMEs updated with batch and subject listing examples
- CI workflows: added tests to TS CI, fixed lint errors
- Release workflows: tag-push trigger, CI gate, no accidental releases
- PUBLISHING.md rewritten for automated release process
- Cleaned up all failed GitHub Actions runs

## v0.4.0 — Operator & Adoption Readiness (2026-04-24)

### Added (server)
- **Batch episode ingestion** — `POST /v1/episodes/batch` accepts up to 100 episodes per request
- **OpenTelemetry tracing** — optional tracing spans on compile, search, and context assembly. Install with `pip install statewave[otel]`
- **Comprehensive `.env.example`** — documents all `STATEWAVE_*` configuration variables with comments

### Added (SDKs)
- **Python SDK 0.4.0** — `create_episodes_batch()` method, `BatchCreateResult` model, `py.typed` marker, PyPI-ready metadata (classifiers, URLs, keywords)
- **TypeScript SDK 0.4.0** — `createEpisodesBatch()` method, `BatchCreateResult` type, npm-ready metadata (exports, files, engines, repository)
- **Publish checklists** — `PUBLISHING.md` in both SDK repos

### Added (docs)
- **Deployment guide** — Docker Compose, bare metal, single container, Fly.io, Railway instructions with production checklist
- **SDK changelogs** — `CHANGELOG.md` in both SDK repos

### Deferred
- **TTL/auto-expiry** — deferred to v0.5. `valid_to` on memories provides manual expiry semantics. Automatic sweep requires a background scheduler not yet justified.

## v0.3.5 — Stabilization (2026-04-24)

### Fixed (server)
- **Middleware execution order** — corrected Starlette reverse-ordering so auth runs before rate limiting and request ID is set outermost
- **Compile + conflict resolution transaction** — both now execute in a single commit, preventing data inconsistency on partial failure
- **LLM compiler event loop blocking** — `LLMCompiler` now uses `ThreadPoolExecutor` so synchronous OpenAI calls don't block async request handling
- **Episode route uses repository layer** — previously bypassed `repo.insert_episode()` and used raw session directly
- **Request validation** — added `min_length`/`max_length` on string fields, bounded `max_tokens` (1–128,000) and `limit` (1–100)

### Changed (SDKs)
- **Python SDK 0.3.5** — added `api_key` and `tenant_id` constructor params, `semantic` param on `search_memories()`
- **TypeScript SDK 0.3.5** — added `ClientOptions` with `apiKey`/`tenantId`, `semantic` param on `searchMemories()`

### Changed (examples)
- All examples now accept `STATEWAVE_API_KEY` and `STATEWAVE_URL` environment variables
- Coding agent example added to examples README

### Changed (docs)
- API contract doc fully rewritten to match v0.3.5 server behavior (auth, semantic, webhooks, validation, config reference)
- Architecture overview updated with v0.3 component diagram, scoring model, middleware stack
- Repo map updated with current versions, test counts, and server structure
- Development conventions refreshed with current SDK features and test counts
- ADR-004 written documenting all v0.3 architectural decisions
- Multi-tenant demoted to "experimental" with clear documentation that data isolation is not implemented

---

## v0.3.0 — Advanced Features (2026-04-24)

### Added (server)
- LLM-backed memory compiler (`LLMCompiler` using OpenAI chat completions)
- Embedding generation during compilation (OpenAI + stub providers)
- Semantic search via pgvector cosine similarity with `semantic=true` query param
- Temporal reasoning in context assembly (+3 bonus for valid, -4 penalty for expired memories)
- Memory conflict resolution (Jaccard similarity, auto-supersede older overlapping memories)
- Webhook event hooks (`episode.created`, `memories.compiled`, `subject.deleted`)
- API key authentication middleware (`X-API-Key` header)
- Rate limiting middleware (per-IP sliding window)
- Multi-tenant header extraction middleware (`X-Tenant-ID`, experimental)
- Coding agent example (`coding-agent-python/`)

---

## v0.2.0 — Production Hardening (2026-04-24)

### Added (server)
- Idempotent memory compilation (only uncompiled episodes processed)
- Pluggable `BaseCompiler` protocol with `HeuristicCompiler`
- Token-bounded context assembly with configurable budget
- Ranked retrieval (kind priority × recency × task-keyword relevance)
- Structured error responses with consistent JSON shape
- Request ID middleware (`X-Request-ID` header)
- CORS configuration
- Health endpoints (`/healthz`, `/readyz`)
- Structured logging via structlog (JSON in production, console in dev)

### Added (SDKs)
- Python SDK 0.2.0 — typed exceptions (`StatewaveAPIError`, `StatewaveConnectionError`, `StatewaveTimeoutError`), async client
- TypeScript SDK 0.2.0 — typed errors, full type exports

### Added (examples)
- Support agent example (2-session demo with ranked context)

---

## v0.1.0 — Local MVP (2026-04-24)

### Added
- Core domain model (Episode, Memory, ContextBundle)
- FastAPI server with 6 endpoints
- Heuristic memory compiler (regex/pattern extraction)
- Context assembly with token estimation
- PostgreSQL + pgvector schema with Alembic migrations
- Docker Compose local deployment
- Python SDK 0.1.0
- TypeScript SDK 0.1.0
- Minimal quickstart example
- CI/CD pipeline (GitHub Actions)
