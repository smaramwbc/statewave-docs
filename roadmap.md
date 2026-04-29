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

---

## v0.5 — Reliability & Trust ✅

**Goal:** Make Statewave trustworthy enough that an operator can run it for real support workloads without worrying about lost events, silent failures, or mystery state.

| # | Feature | Status |
|---|---------|--------|
| 1 | Reliable webhook delivery — persistent queue, exponential backoff, dead-letter | ✅ Done |
| 2 | SDK retry with backoff — automatic retry on 429/5xx with jitter | ✅ Done |
| 3 | Durable async compilation — Postgres-backed job queue | ✅ Done |
| 4 | True multi-tenant isolation — app-layer query scoping | ✅ Done |
| 5 | Distributed rate limiting — Postgres-backed | ✅ Done |
| 6 | Backup/restore tooling — subject-level export/import | ✅ Done |
| 7 | Admin introspection — jobs + webhooks | ✅ Done |
| 8 | Compilation status API | ✅ Done |
| 9 | Deep health checks | Deferred to v0.7 |
| 10 | Migration safety docs | Deferred to v0.7 |

## v0.6 — Support-Agent Superiority ✅ ← CURRENT (v0.6.1)

**Goal:** Make Statewave the obvious best choice for teams building support agents.

| # | Feature | Status |
|---|---------|--------|
| 1 | Session-aware context assembly | ✅ Done |
| 2 | Resolution tracking (open/resolved/unresolved) | ✅ Done |
| 3 | Handoff context packs (structured escalation briefs) | ✅ Done |
| 4 | Repeat-issue detection (prior resolution surfacing) | ✅ Done |
| 5 | Support-specific ranked retrieval | ✅ Done |
| 6 | Customer health scoring (0–100, explainable factors) | ✅ Done |
| 7 | Health-aware handoff (risk level + factors in briefs) | ✅ Done |
| 8 | Proactive health alerts (webhooks on state transitions) | ✅ Done |
| 9 | SLA tracking (response time, resolution time, breach flags) | ✅ Done |
| 10 | SLA integration into health + handoff | ✅ Done |

Proven by: 232 unit tests, 3 eval suites (54 assertions), 2 benchmarks (Statewave 9/9 vs Naive 2/9).

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
