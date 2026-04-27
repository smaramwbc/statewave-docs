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
- [x] Webhooks (fire-and-forget), multi-tenant (experimental)
- [x] Middleware ordering, validation, LLM thread-pool fix

## v0.4 — Adoption Readiness ✅

- [x] Batch episode ingestion (up to 100)
- [x] OpenTelemetry tracing (optional)
- [x] Deployment guide (Docker, Fly.io, Railway)
- [x] SDK publish readiness, getting started guide
- [x] Support-agent benchmark & "Why Statewave" comparison doc

---

## v0.5 — Reliability & Trust ← CURRENT

**Goal:** Make Statewave trustworthy enough that an operator can run it for real support workloads without worrying about lost events, silent failures, or mystery state.

| # | Feature | Why |
|---|---------|-----|
| 1 | **Reliable webhook delivery** — persistent queue, exponential backoff, dead-letter, delivery status | Current fire-and-forget drops events silently |
| 2 | **SDK retry with backoff** — automatic retry on 429/5xx with jitter in both SDKs | Clients shouldn't crash on transient failures |
| 3 | **Durable async compilation** — background job with status tracking | Large compiles can timeout or get lost |
| 4 | **True multi-tenant isolation** — row-level security, not just header trust | Current tenant support is cosmetic |
| 5 | **Distributed rate limiting** — Postgres-backed, survives restarts | In-memory limiter resets on deploy |
| 6 | **Backup/restore tooling** — `statewave export` / `statewave import` for subject data | Operators need confidence before upgrades |
| 7 | **Admin introspection** — `/admin/subjects`, `/admin/jobs`, `/admin/webhooks` with stats | Operators can't see what's happening |
| 8 | **Compilation status API** — `GET /v1/memories/compile/{job_id}` | Callers need to know when compilation finishes |
| 9 | **Deep health checks** — `/readyz` checks DB, queue, LLM reachability | Current readyz only checks process is up |
| 10 | **Migration safety** — pre/post checks, rollback docs | Operators fear schema migrations |

## v0.6 — Support-Agent Superiority

**Goal:** Make Statewave the obvious best choice for teams building support agents.

- [ ] Session-aware context assembly (group by session, surface arcs)
- [ ] Resolution tracking (mark issues resolved, surface only open by default)
- [ ] Customer health scoring (derive satisfaction signals)
- [ ] Handoff context packs (structured bundle for agent-to-agent/human)
- [ ] Memory templates for support patterns (identity, preferences, issues, resolutions)
- [ ] Webhook filters (subscribe to specific event types)
- [ ] SDK convenience: `sw.support_context(subject, task)` with opinionated defaults
- [ ] Benchmark: 50-session customer at production scale

## v0.7 — Operator & Cloud Experience

**Goal:** Make Statewave easy to operate at scale for teams shipping support products.

- [ ] Admin dashboard (read-only: subjects, jobs, webhooks, health)
- [ ] Horizontal scaling (read replicas, connection pooling, tested patterns)
- [ ] Memory TTL / expiry policies
- [ ] Usage metering (episodes/month, compiles/month per tenant)
- [ ] Helm chart + Kubernetes guide
- [ ] Compliance readiness documentation

---

## Design principles

1. **Raw truth first** — episodes are immutable, memories are derived
2. **Self-hosted, operator-friendly** — you own your data and infra
3. **Support-agent wedge** — optimize here, prove it, then expand
4. **Multi-provider** — LiteLLM means no vendor lock-in
5. **Trust over features** — reliability beats feature count
6. **Honest about limitations** — document what doesn't work yet
