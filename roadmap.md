# Roadmap

Statewave is purpose-built for **support-agent workflows** — the first use case where structured memory clearly outperforms naive history stuffing and simple RAG. The roadmap reflects this: trust and reliability first, then support-agent superiority, then operator experience.

---

## v0.1 — Local MVP ✅

- [x] Core domain model (Episode, Memory, ContextBundle)
- [x] FastAPI server with the core v1 endpoint surface
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
- [x] Proof layer: 3 eval suites (55 assertions), 2 benchmarks (8/8 vs 2/8)

---

## v0.7 — Operator & Cloud Experience

**Goal:** Make Statewave trustworthy to operate at scale. An operator should be able to deploy, monitor, upgrade, and scale Statewave without surprises.

- [x] Deep health checks — `/readyz` verifies DB connectivity, queue health, LLM reachability (per-check status + latency_ms; 503 on `not_ready`)
- [x] Migration safety — preflight script, startup schema guard, `/ops/migrations` endpoint, runbook
- [x] Admin dashboard (read-only) — system health, jobs, webhooks, counts, health distribution
- [x] Usage metering — episodes/month, compiles/month, per-tenant usage
- [x] **Memory TTL / expiry policies** — per-kind global expiry windows configured via `STATEWAVE_KIND_TTL_DAYS` (JSON). Compilers stamp `valid_to = valid_from + ttl_days` on insert; `/v1/context` retrieval filters expired rows out immediately (`(valid_to IS NULL OR valid_to > now())`); the hourly cleanup loop tombstones expired rows so the status surface stays current. Soft-delete only — rows persist for [#49 receipt](https://github.com/smaramwbc/statewave/issues/49) lookup. Status vocabulary aligned with #49 (`active | superseded | tombstoned`); the previous unused `deleted` enum value was renamed (alembic 0016). Per-subject / per-tenant / per-policy expiry is deferred to the policy layer in [#50](https://github.com/smaramwbc/statewave/issues/50) — TTL ships the simple primitive so it composes cleanly. Operator config + design notes in [`deployment/memory-ttl.md`](deployment/memory-ttl.md).
- [x] **Horizontal scaling guide** — multi-instance reference topologies, connection-budget runbook, PgBouncer guidance, multi-instance diagnostics, and the design properties that hold across replicas (Postgres-backed compile queue, webhook DLQ, rate limit, L2 query embedding cache). See [`deployment/horizontal-scaling.md`](deployment/horizontal-scaling.md). Honest framing: the guide is derived from architectural design points and operational arithmetic, not a load-test campaign — see "What we have not validated".
- [x] **Helm chart + Kubernetes deployment guide** — in-tree Helm chart at [`helm/statewave/`](https://github.com/smaramwbc/statewave/tree/main/helm/statewave) in the `statewave` repo (API-only; operators bring a pgvector-capable Postgres). Schema migrations run as a Helm pre-install + pre-upgrade Job; the Deployment bypasses `start.sh` and runs `uvicorn` directly so each pod is a clean stateless API process. Companion deployment guide at [`deployment/kubernetes.md`](deployment/kubernetes.md) covers Postgres options, secret-management patterns (inline vs External Secrets Operator / Sealed Secrets / SOPS), per-controller Ingress timeout cheatsheet, HPA + connection-budget guidance, and k8s-specific troubleshooting.
- [x] In-process query embedding cache (LRU + TTL) — eliminates repeat provider calls on identical task text in `/v1/context`
- [x] **Native pgvector similarity path** — `memories.embedding` migrated from `TEXT` to `vector(1536)` (alembic `0013_pgvector_native`); `search_memories_by_embedding` rewritten to use the `<=>` cosine-distance operator with an HNSW index. Removes the in-Python cosine compute that was the ~1.5s floor per `/v1/context`. Requires pgvector-bundled Postgres image — see `infra/postgres-pgvector/` for the Dockerfile + deployment runbook.
- [x] **`/v1/context` candidate-pool union** — `/v1/context` now feeds the rows from `search_memories_by_embedding` into the per-kind candidate pool alongside the recency-fetched rows (deduped by id). Previously, candidates were preselected by `created_at DESC LIMIT 50` per kind and the semantic-search call only contributed scores for those already-fetched rows; semantically-relevant memories outside the recency window could never enter ranking. Live evidence: docs-grounded eval `doc_match` 25%→100%, `groundable` 50%→100% with no other change. Stub-provider deployments unchanged (semantic results empty → union is a no-op).
- [x] **Cross-machine query embedding cache** — Postgres-backed `query_embedding_cache` table (alembic `0014_query_embedding_cache`) shared across all backend instances. Wraps the in-process LRU as L2: L1 hit → L2 → API. A 30s cross-instance provider-latency spike on the first hit per instance is eliminated; warm calls are sub-second regardless of which instance handles them. 24h TTL, composite (text, model) key so model rotations don't alias, opportunistic cleanup on write.
- [x] **Single LiteLLM adapter for all provider calls** — `server/services/llm.py` is the only module that imports LiteLLM; compilers, embeddings, and the readiness check all route through it. Provider/model/api-base/timeout/retries/temperature are configured via `STATEWAVE_LITELLM_*` env vars (clean break from the prior `STATEWAVE_OPENAI_*` naming). Typed error hierarchy (`LLMTimeoutError` / `LLMResponseError` / `LLMProviderError`); api_key passed explicitly to every LiteLLM call instead of mutating `os.environ`. AST-based isolation test (`tests/test_llm_adapter_isolation.py`) fails CI if any module under `server/` other than the adapter imports `litellm`, `openai`, `anthropic`, `cohere`, `voyageai`, `mistralai`, or `google.generativeai`.
- [x] **Docs-only support memory pack** — read-only memory pack derived from the official Statewave docs corpus (see [`default-support-docs-pack.md`](default-support-docs-pack.md)). Powers the docs-grounded "Statewave Support" persona on [statewave.ai](https://statewave.ai/?ask=support) and the `support-agent-docs` example. Pack content is built once at release time by `statewave/scripts/build_support_pack.py` (chunks docs, runs ingest + compile, serialises to bundled JSONL) and shipped inside the API image; container restart auto-applies via a version-aware reseed that selectively purges only pack-owned rows so operator-added content survives. The legacy live-refresh workflow in `statewave/scripts/bootstrap_docs_pack.py` is retained for hot-refreshing production between image rebuilds.
- [x] **Visible citations on retrieval responses** — docs-grounded `/v1/context` and the `support-agent-docs` SDK path return resolved citations (doc_path + breadcrumb + URL) alongside the assembled context. Resolved server-side from the same context bundle the model receives, never parsed from model output — no fabrication path. Surfaced in the website widget as inline source pills under each docs-grounded reply.

---

## v0.8 — Governance & Adoption ✅

**Goal:** Make Statewave deployable in compliance-grade settings (regulated industries, multi-tenant SaaS) and make adoption trivial for teams integrating it into existing stacks.

### Governance & audit — shipped

- [x] **State-assembly receipts** ([#49](https://github.com/smaramwbc/statewave/issues/49)) — every `/v1/context` and `/v1/handoff` call can emit an immutable, ULID-addressable audit artifact recording exactly which memories + episodes influenced the bundle, with a SHA-256 hash of the bytes delivered to the agent and per-entry supersession status. `GET /v1/receipts/{id}` + cursor-paginated list per subject. Strict-superset schema with a `mode` discriminator so future modes (`as_of_replay`, `eval_run`) can extend without breaking. Emission gate: per-request flag → per-tenant config (`always | on_request | never`) → env kill-switch. Tenant-controlled retention surface (`receipt_retention_days` in `tenant_configs`; purge worker is v0.9). Full design + six negative-test acceptance criteria in [`receipts.md`](receipts.md).
- [x] **Sensitivity labels + per-memory policy bindings** ([#50](https://github.com/smaramwbc/statewave/issues/50)) — per-memory capability tags (`pii`, `financial`, `secret`, …) carried as a `TEXT[]` column with a GIN index; set via `PATCH /v1/memories/{id}/labels`. Policy bundles are YAML/JSON, content-hashed, immutable, stored in `policy_bundles`; six predicates (`memory_has_any_label`, `memory_has_all_labels`, `caller_type`, `caller_type_in`, `caller_type_not_in`, `caller_id`) and two actions (`deny`, `redact`); first-match-wins evaluation, default-allow on no match. Per-tenant `policy_mode: log_only | enforce` — `log_only` records decisions into receipts without filtering (safe rollout), `enforce` drops denied memories before ranking. Receipts surface every fired decision via `policy.filters_applied` and the unfired-rule summary via `policy.filters_skipped`. Full reference in [`sensitivity-labels.md`](sensitivity-labels.md).
- [x] **Caller identity** — `caller_id` and `caller_type` on `/v1/context` and `/v1/handoff` feed the policy evaluator. Tenant config `require_caller_identity: true` 401s anonymous calls — the lever compliance-grade tenants flip to make policy enforcement non-bypassable.
- [x] **Per-tenant configuration endpoint** — `GET / PATCH /admin/tenants/{tenant_id}/config` for receipts emission policy, retention, policy_mode, caller-identity gating. PATCH-shape merge (only touches supplied keys, preserves the rest), enum/bound validation at the API boundary, optimistic concurrency via `expected_version`. Makes `policy_mode: enforce` and `require_caller_identity: true` reachable via API without a SQL shell — the gap caught in the enforce-mode prod smoke.
- [x] **Cross-tenant policy bundle uniqueness** ([#79](https://github.com/smaramwbc/statewave/issues/79)) — `policy_bundles` keyed on `(tenant_id, bundle_hash)` composite uniqueness (PG15+ `NULLS NOT DISTINCT`). Two tenants installing the IDENTICAL YAML produce two independently-resolvable rows. Pre-fix the second tenant's upload silently re-bound the first's row.

### Adoption — shipped

- [x] **SDK convenience methods for support endpoints** — ergonomic wrappers on both `statewave-py` and `@statewavedev/sdk` for `/v1/subjects/{id}/health`, `/v1/subjects/{id}/sla`, `/v1/handoff`, and resolution create/list. Same auth, tenant-scoping, and retry as the rest of the client; HTTP wire contract unchanged. Sync + async on the Python side. Shipped in `statewave-py` 0.10.0 and `@statewavedev/sdk` 0.10.0 (statewave-py#15, statewave-ts#16).
- [x] **Framework integrations (LangChain, CrewAI, AutoGen)** — three runnable quickstart examples in [`statewave-examples`](https://github.com/smaramwbc/statewave-examples) (`langchain-quickstart/`, `crewai-quickstart/`, `autogen-quickstart/`). Each ships a small adapter (`StatewaveMemory(BaseMemory)` for LangChain; pure-function helpers for CrewAI and AutoGen), a runnable demo, and mock-based smoke tests. Dependency strategy: **zero framework deps in the core SDKs** — adapters live inside each example, framework versions pinned only in the example READMEs, so SDK releases don't chase framework churn (statewave-examples#12).
- [x] **Webhook event filters** — `STATEWAVE_WEBHOOK_EVENTS` (comma-separated) is an event-type allowlist on the global webhook URL. Filtered-out events are dropped before they reach the delivery queue. Unknown event types fail the server at startup, so a typo can't silently drop every webhook. Fully backward-compatible: empty filter delivers every event (statewave#150).
- [x] **Memory templates for common patterns** — declarative, versioned scaffolds for recurring information patterns. Five bundled templates ship today (customer support handoff, user preference, project decision log, incident summary, account onboarding); `GET /v1/memory-templates` is fully inspectable, `POST /v1/memory-templates/{id}/apply` validates field values and ingests an ordinary episode with `template_id` / `template_version` recorded in `metadata.template`. Pure data — no code runs inside a template; rendering is deterministic string substitution. See [`docs/memory-templates.md`](https://github.com/smaramwbc/statewave/blob/main/docs/memory-templates.md) in the server repo (statewave#152).
- [x] **Design partner onboarding package** — a single-page guide in [`design-partners.md`](design-partners.md) covering overview, who Statewave is for, a 30-minute setup path, recommended first use cases, data/privacy expectations, the support and feedback loop, an evaluation checklist (functional, performance, governance, operational), 30 / 60 / 90-day success criteria with benchmark reference numbers, and a 9-entry FAQ. Linked from `README.md` and `SUPPORT.md` (statewave-docs#42).
- [x] **Head-to-head benchmark against Mem0 / Zep** — complete equal-budget sweep on the public [LoCoMo](https://github.com/snap-research/LoCoMo) dataset across **four token tiers (512 / 1024 / 2048 / 4096)**, **5 systems** (statewave, mem0, zep, naive, no_memory), 10 conversations, 1,986 questions/system. Publication-safety harness — `swb report` refuses headline rankings without 100% coverage, same question set across systems, no judge_failed rows, measured input tokens shown beside every score, vendor-correction standing invitation. **Statewave wins every tier and every category.** Full methodology + per-tier results live in [`RESULTS.md`](https://github.com/smaramwbc/statewave-bench/blob/main/RESULTS.md) on `statewave-bench` `main` (statewave-bench#14).
- [x] **Connector ecosystem — fully shipped** ✅ Modular packages for GitHub, Markdown/ADRs, MCP, Slack, Discord, Zendesk, Intercom, Freshdesk, Notion, Gmail, n8n, Zapier. v0.6.0 added cursor-based delta sync (Zendesk Incremental Tickets Export, Gmail History API) and Notion database scoping. **Tier 2 push receivers shipped (v0.7.0–v0.11.0)** — every connector with a meaningful push surface in its source system now has a real-time receiver alongside its pull connector: Slack DM/MPIM dispatch (`slack.dm.*`, `slack.mpim.*`), Freshdesk webhook, Zendesk webhook, Intercom webhook, and Gmail Cloud Pub/Sub push. `statewave-connectors listen <connector>` is the unified daemon; the same `(Request) => Promise<Response>` factory mounts on Vercel / Cloudflare / Express identically across the lineup. **Tier 3 operator/cloud productization shipped (v0.12.0–v0.17.0)** — TOML config file (multi-instance), hosted runner (`statewave-connectors run`), persistent state adapters (file / Postgres / Redis), built-in OIDC verification for Gmail Pub/Sub, auth-gated Prometheus `/metrics`, and deployment recipes (Docker / Compose / Helm / Fly / Railway). See [Connectors → Roadmap](connectors/roadmap.md) for the full release timeline and what's queued next (long-running daemon shapes — Slack Socket Mode, Discord Gateway, Gmail service-account auth).

---

## v0.9 — Replay, Signing, & Auto-Labeling ← CURRENT

Building on the v0.8 governance foundation:

- [ ] **Receipt-driven replay** — new receipt `mode: as_of_replay` lets `/v1/replay` re-run assembly against historical state (using receipt's recorded selected entries + bundle hash) and emit a "what would have happened" receipt for time-travel debugging.
- [ ] **HMAC signing for receipts** — the `receipt_signature` column reserved in v0.8 lights up with a tenant-key-signed digest of the canonical receipt body. Lets compliance reviewers verify a receipt wasn't tampered with after the fact.
- [ ] **Scheduled retention-purge worker** — reads `tenant_configs.receipt_retention_days` and tombstones expired receipts. Surface shipped in v0.8; worker is the implementation.
- [ ] **Compiler/connector heuristic auto-labeling** — opt-in regex/LLM detection of PII, financial identifiers, etc. during memory compilation. Surfaces as `suggested_labels` (separate from authoritative operator-supplied `sensitivity_labels`) so false positives never silently filter memories.
- [ ] **Visual policy editor** — operator-friendly form on the admin app to build rule sets without writing YAML by hand (YAML still ships as the canonical artifact for git review).
- [ ] **Cross-region data residency** — `region` column reserved on receipts in v0.8 lights up with per-tenant region pinning so EU-only tenants can guarantee assembly artifacts stay in EU storage.

---

## Design principles

1. **Raw truth first** — episodes are immutable, memories are derived
2. **Self-hosted, operator-friendly** — you own your data and infra
3. **Support-agent wedge** — optimize here, prove it, then expand
4. **Multi-provider** — LiteLLM means no vendor lock-in
5. **Trust over features** — reliability beats feature count
6. **Honest about limitations** — document what doesn't work yet
