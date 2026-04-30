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
- [x] Product website (statewave.dev)
- [x] Proof layer: 3 eval suites (54 assertions), 2 benchmarks (9/9 vs 2/9)

---

## v0.7 — Operator & Cloud Experience ← CURRENT

**Goal:** Make Statewave trustworthy to operate at scale. An operator should be able to deploy, monitor, upgrade, and scale Statewave without surprises.

- [ ] Deep health checks — `/readyz` verifies DB connectivity, queue health, LLM reachability
- [x] Migration safety — preflight script, startup schema guard, `/ops/migrations` endpoint, runbook
- [x] Admin dashboard (read-only) — system health, jobs, webhooks, counts, health distribution
- [x] Usage metering — episodes/month, compiles/month, per-tenant usage
- [ ] Memory TTL / expiry policies — automatic cleanup of stale memories
- [ ] Horizontal scaling guide — read replicas, connection pooling, tested patterns
- [ ] Helm chart + Kubernetes deployment guide

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
