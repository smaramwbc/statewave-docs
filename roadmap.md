# Roadmap

Statewave is purpose-built for **support-agent workflows** — the first use case where structured memory clearly outperforms naive history stuffing and simple RAG. The roadmap reflects this: trust and reliability first, then support-agent superiority, then operator experience.

---

## v0.1 — Local MVP ✅

- [x] Core domain model (Episode, Memory, ContextBundle)
- [x] FastAPI server with all 6 endpoints
- [x] Heuristic memory compiler
- [x] Context assembly with token estimation
- [x] PostgreSQL + pgvector schema
- [x] Docker Compose local deployment
- [x] Python SDK v0.1.0, TypeScript SDK v0.1.0

## v0.2 — Production Hardening ✅

- [x] Idempotent compilation, pluggable compilers, token-bounded context
- [x] Ranked retrieval (kind × recency × relevance)
- [x] Structured errors, request-ID, CORS, health endpoints, structured logging
- [x] LLM compilation via LiteLLM (100+ providers)
- [x] Semantic search via pgvector
- [x] Authentication (API keys), rate limiting (in-memory)
- [x] Python SDK v0.2.0, TypeScript SDK v0.2.0

## v0.3 — Advanced Features ✅

- [x] Temporal reasoning, memory conflict resolution
- [x] Webhooks, multi-tenant (experimental)
- [x] Middleware ordering, validation, LLM thread-pool fix

## v0.4 — Adoption Readiness ✅

- [x] Batch episode ingestion (up to 100)
- [x] OpenTelemetry tracing (optional)
- [x] Deployment guide (Docker, Fly.io, Railway)
- [x] SDK publish readiness, getting started guide
- [x] Support-agent benchmark & "Why Statewave" comparison doc

## v0.5 — Reliability & Trust ✅

- [x] Reliable webhook delivery — persistent queue, exponential backoff, dead-letter
- [x] SDK retry with backoff — automatic retry on 429/5xx with jitter
- [x] Durable async compilation — Postgres-backed job queue
- [x] True multi-tenant isolation — app-layer query scoping
- [x] Distributed rate limiting — Postgres-backed
- [x] Backup/restore tooling — subject-level export/import
- [x] Admin introspection — jobs + webhooks
- [x] Compilation status API

## v0.6 — Support-Agent Superiority ✅

- [x] Session-aware context assembly
- [x] Resolution tracking (open/resolved/unresolved)
- [x] Handoff context packs (structured escalation briefs)
- [x] Repeat-issue detection (prior resolution surfacing)
- [x] Support-specific ranked retrieval
- [x] Customer health scoring (0–100, explainable factors)
- [x] Health-aware handoff (risk level + factors in briefs)
- [x] Proactive health alerts (webhooks on state transitions)
- [x] SLA tracking (response time, resolution time, breach flags)
- [x] SLA integration into health + handoff
- [x] Product website (statewave.ai)
- [x] Proof layer: 3 eval suites (54 assertions), 2 benchmarks (9/9 vs 2/9)

---

## v0.7 — Operator & Cloud Experience ← CURRENT

**Goal:** Make Statewave trustworthy to operate at scale. An operator should be able to deploy, monitor, upgrade, and scale Statewave without surprises.

- [x] Deep health checks — `/readyz` verifies DB connectivity, queue health, LLM reachability (per-check status + latency_ms; 503 on `not_ready`)
- [x] Migration safety — preflight script, startup schema guard, `/ops/migrations` endpoint, runbook
- [x] Admin dashboard (read-only) — system health, jobs, webhooks, counts, health distribution
- [x] Usage metering — episodes/month, compiles/month, per-tenant usage
- [ ] Memory TTL / expiry policies — automatic cleanup of stale memories
- [ ] Horizontal scaling guide — read replicas, connection pooling, tested patterns
- [ ] Helm chart + Kubernetes deployment guide
- [x] In-process query embedding cache (LRU + TTL) — eliminates repeat provider calls on identical task text in `/v1/context`
- [x] **Native pgvector similarity path** — `memories.embedding` migrated from `TEXT` to `vector(1536)` (alembic `0013_pgvector_native`); `search_memories_by_embedding` rewritten to use the `<=>` cosine-distance operator with an HNSW index. Removes the in-Python cosine compute that was the ~1.5s floor per `/v1/context`. Requires pgvector-bundled Postgres image — see `infra/postgres-pgvector/` for the Dockerfile + deployment runbook.
- [x] **`/v1/context` candidate-pool union** — `/v1/context` now feeds the rows from `search_memories_by_embedding` into the per-kind candidate pool alongside the recency-fetched rows (deduped by id). Previously, candidates were preselected by `created_at DESC LIMIT 50` per kind and the semantic-search call only contributed scores for those already-fetched rows; semantically-relevant memories outside the recency window could never enter ranking. Live evidence: docs-grounded eval `doc_match` 25%→100%, `groundable` 50%→100% with no other change. Stub-provider deployments unchanged (semantic results empty → union is a no-op).
- [x] **Cross-machine query embedding cache** — Postgres-backed `query_embedding_cache` table (alembic `0014_query_embedding_cache`) shared across all backend instances. Wraps the in-process LRU as L2: L1 hit → L2 → API. A 30s cross-instance provider-latency spike on the first hit per instance is eliminated; warm calls are sub-second regardless of which instance handles them. 24h TTL, composite (text, model) key so model rotations don't alias, opportunistic cleanup on write.
- [x] **Single LiteLLM adapter for all provider calls** — `server/services/llm.py` is the only module that imports LiteLLM; compilers, embeddings, and the readiness check all route through it. Provider/model/api-base/timeout/retries/temperature are configured via `STATEWAVE_LITELLM_*` env vars (clean break from the prior `STATEWAVE_OPENAI_*` naming). Typed error hierarchy (`LLMTimeoutError` / `LLMResponseError` / `LLMProviderError`); api_key passed explicitly to every LiteLLM call instead of mutating `os.environ`. AST-based isolation test (`tests/test_llm_adapter_isolation.py`) fails CI if any module under `server/` other than the adapter imports `litellm`, `openai`, `anthropic`, `cohere`, `voyageai`, `mistralai`, or `google.generativeai`.
- [x] **Docs-only support memory pack** — bootstrapped read-only memory pack derived from the official Statewave docs corpus (see [`default-support-docs-pack.md`](default-support-docs-pack.md)). Powers the docs-grounded "Statewave Support" persona on [statewave.ai](https://statewave.ai/?ask=support) and the `support-agent-docs` example. Refresh + bootstrap workflows live in `statewave/scripts/bootstrap_docs_pack.py`.
- [x] **Visible citations on retrieval responses** — docs-grounded `/v1/context` and the `support-agent-docs` SDK path return resolved citations (doc_path + breadcrumb + URL) alongside the assembled context. Resolved server-side from the same context bundle the model receives, never parsed from model output — no fabrication path. Surfaced in the website widget as inline source pills under each docs-grounded reply.

---

## v0.8 — Adoption & Ecosystem (planned)

**Goal:** Make it trivial for teams to adopt Statewave and integrate it into existing stacks.

- [ ] SDK convenience methods for support endpoints (health, SLA, handoff, resolutions)
- [ ] Framework integrations (LangChain, CrewAI, AutoGen)
- [ ] Webhook event filters (subscribe to specific event types)
- [ ] Memory templates for common patterns
- [ ] Design partner onboarding package
- [ ] Head-to-head benchmark against Mem0 / Zep

---

## Design principles

1. **Raw truth first** — episodes are immutable, memories are derived
2. **Self-hosted, operator-friendly** — you own your data and infra
3. **Support-agent wedge** — optimize here, prove it, then expand
4. **Multi-provider** — LiteLLM means no vendor lock-in
5. **Trust over features** — reliability beats feature count
6. **Honest about limitations** — document what doesn't work yet
