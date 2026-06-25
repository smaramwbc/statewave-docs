# Architecture Overview

Version: **1.2.x**

Statewave is an **open-source memory runtime for AI agents**. It compiles raw events into ranked, token-bounded context bundles with full provenance — so your AI stops forgetting across sessions. Self-hosted on Postgres, no vendor lock-in.

## Core loop

```
RECORD → COMPILE → CONTEXT → GOVERN
```

1. **Record** — immutable episodes capture raw interaction truth
2. **Compile** — pluggable compilers (heuristic or LLM) derive typed memories with provenance, embeddings, and conflict resolution
3. **Context** — assembly service builds ranked, token-bounded, deterministic context bundles using temporal reasoning and semantic similarity, gated by the [policy layer](../sensitivity-labels.md) (memory `sensitivity_labels` ✕ caller identity → allow / deny / redact) before ranking
4. **Govern** — provenance inspection, delete-by-subject, authentication, rate limiting, webhook notifications, immutable [state-assembly receipts](../receipts.md) per call (content-hash integrity, ULID-addressable), per-tenant configuration for emission / retention / enforce mode

> **Where do episodes come from?** Either the SDKs (Python / TypeScript) or the [Connectors](../connectors/index.md) — modular packages for GitHub, Markdown/ADRs, MCP-compatible agents, and more. Connectors normalize source events into the same episode shape Statewave records natively.

## Component architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Server                           │
│                                                               │
│  ┌─ Middleware Stack (execution order) ─────────────────────┐ │
│  │  CORS → RequestID → Auth → RateLimit → Tenant           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Episodes │  │ Memories │  │ Context  │  │  Subjects  │  │
│  │  Route   │  │  Route   │  │  Route   │  │   Route    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
│       │              │              │              │          │
│  ┌────┴──────────────┴──────────────┴──────────────┴───────┐ │
│  │                   Service Layer                          │ │
│  │  Compilers (heuristic | LLM)  · Embeddings (stub|LiteLLM)│ │
│  │  ContextAssembler (ranked, semantic, temporal)           │ │
│  │  ConflictResolver  ·  Webhooks                           │ │
│  └────┬──────────────┬──────────────┬──────────────────────┘ │
│       │              │              │                         │
│  ┌────┴──────────────┴──────────────┴──────────────────────┐ │
│  │              Repository / DB Layer                       │ │
│  │   episodes · memories · semantic search (pgvector)       │ │
│  └──────────────────────┬──────────────────────────────────┘ │
└──────────────────────────┼───────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │  PostgreSQL  │
                    │  + pgvector  │
                    └─────────────┘
```

## Key design decisions

- **Thin routes, strong services** — API handlers delegate to service functions
- **Raw truth first** — episodes are append-only, never mutated
- **Compiled memory second** — memories are derived, with provenance to source episodes
- **Provenance everywhere** — every memory links back to source episodes via `source_episode_ids`
- **Idempotent compilation** — recompiling is safe; only uncompiled episodes are processed
- **Token-bounded context** — context bundles respect configurable token budgets
- **Ranked retrieval** — composite scoring: kind priority × recency × relevance × temporal validity
- **Semantic search** — pgvector cosine similarity with graceful fallback to text search
- **Structured errors** — consistent `{error: {code, message, details, request_id}}` everywhere
- **Local-first** — `docker compose up` + `pip install` gets you running
- **Framework-neutral** — no AI framework coupling in core

## Middleware stack

Execution order (outermost to innermost):

1. **CORS** — cross-origin headers
2. **RequestID** — generate/propagate `X-Request-ID`, bind to structlog
3. **Auth** — validate `X-API-Key` (skipped when no key configured)
4. **RateLimit** — per-IP sliding window (skipped when RPM = 0)
5. **Tenant** — extract `X-Tenant-ID`, scope all queries to tenant (app-layer isolation)

## Compilation pipeline

```
Uncompiled Episodes → Compiler → Raw Memories → Embedding → Conflict Resolution → Commit
```

- **Compilers:** `HeuristicCompiler` (regex/pattern, no external deps) and `LLMCompiler` (any provider via LiteLLM, runs in thread pool to avoid blocking)
- **Embeddings:** `StubEmbeddingProvider` (deterministic hash vectors for dev/test) and `LiteLLMEmbeddingProvider` (real semantic vectors via [LiteLLM](https://github.com/BerriAI/litellm) — supports OpenAI, Azure, Cohere, Voyage, Bedrock, Ollama, and any other LiteLLM-compatible embedding model)
- **Conflict resolution:** Jaccard similarity within same (subject, kind) groups; older memory superseded with `valid_to` set
- All steps execute in a single database transaction

## Context scoring model

| Signal | Range | Source |
|--------|-------|--------|
| Kind priority | 3–10 | profile_fact=10, procedure=8, episode_summary=5, raw_episode=3 |
| Recency | 0–5 | Linear scale: most recent = max |
| Task relevance | 0–5 (text) or 0–8 (semantic) | Word overlap or cosine similarity |
| Temporal validity | -4 to +3 | Currently valid = +3, expired = -4 |

In addition to the core signals above, support-agent workloads apply session, urgency, and repeat-issue adjustments. Scoring is deterministic and **not user-configurable today** — see [Ranking & Retrieval](ranking.md) for the full signal list and rationale.

## Data model

| Entity | Description | Key fields |
|--------|-------------|------------|
| **Episode** | Immutable raw event | id, subject_id, source, type, payload, metadata, provenance, created_at, last_compiled_at |
| **Memory** | Derived typed memory | id, subject_id, kind, content, summary, confidence, valid_from, valid_to, source_episode_ids, status, embedding, sensitivity_labels |
| **ContextBundle** | Runtime output | subject_id, task, facts, episodes, procedures, provenance, assembled_context, token_estimate |
| **Receipt** | Immutable audit artifact for a `/v1/context` or `/v1/handoff` call | id (ULID), tenant_id, subject_id, mode, selected_entries, bundle_hash, policy (filters_applied, filters_skipped), parent_receipt_id, created_at |
| **PolicyBundle** | Content-hashed, immutable rule set governing memory access | id, tenant_id (nullable for global), bundle_hash, rules (predicates + actions), source_yaml, created_at |
| **TenantConfig** | Per-tenant operator knobs | tenant_id, receipts (`always \| on_request \| never`), receipt_retention_days, policy_mode (`log_only \| enforce`), require_caller_identity, version |

## Version history

Ordered newest first. See [roadmap.md](../roadmap.md) for the canonical list of shipped items per release.

### v1.3 — hybrid retrieval & compile pipeline
- **Hybrid retrieval** — `/v1/memories/search` blends pgvector cosine similarity with Postgres BM25 (`ts_rank_cd` over a generated `content_tsvector`), on by default; pass `hybrid=false` for the pure-semantic path. An optional entity-boost lane and an LLM reranker are available, both off by default.
- **Compile pipeline** — near-duplicate dedup before reconcile, context-aware reconcile with assistant-fact extraction, technical-spec/metric extraction, and full-conversation windowed compile with chunked reconcile improve recall on multi-hop and long-context retrieval.
- **LLM layer** — provider-aware API-key routing for mixed-vendor deployments, token usage + model returned from `/v1/llm/complete`, and model-aware reasoning-effort / temperature handling.
- **Non-breaking** — existing deployments are unaffected; migrations 0027/0028 add the BM25 tsvector column and the per-subject entity store.

### v1.2 — admin API, dynamic settings & security hardening
- **Admin API expansion** — dynamic settings endpoint lets operators hot-reload topology-agnostic configuration without a restart; new production-readiness endpoint surfaces deployment health for orchestrators and load-balancer probes.
- **Security hardening** — SSRF blocked on webhook URL probe; DNS-rebinding TOCTOU closed so a probe result can no longer be hijacked between validation and use; LIKE metacharacters escaped in admin search and prefix filters to prevent wildcard injection.
- **Admin UI inspection surface** — retrieval simulator, activity timeline, memory provenance graph, and six new inspection endpoints back the operator console's inspector views.
- **Starlette 1.3 compatibility** — route-registration tests updated to handle `_IncludedRouter` wrappers introduced in Starlette 1.3 / FastAPI 0.137.

### v1.1 — idempotent ingest & reasoning-model compilation
- **Idempotent episode ingest** ([#240](https://github.com/smaramwbc/statewave/pull/240)) — `POST /v1/episodes` honours a client-supplied `idempotency_key`: re-ingesting an episode with the same key (re-running a connector seed, retrying a request) returns the existing episode instead of inserting a duplicate. Backed by a partial unique index on `(tenant_id, subject_id, idempotency_key)` (migration 0025, `NULLS NOT DISTINCT`); keyless episodes are never de-duplicated. Both SDKs expose the optional key on `create_episode` / `createEpisode`.
- **Reasoning-model compilation** ([#240](https://github.com/smaramwbc/statewave/pull/240)) — the LLM compiler's output budget is now a configurable ceiling (`STATEWAVE_LITELLM_COMPILE_MAX_TOKENS`, default 16000) floored per call, so reasoning models (which spend budget on hidden reasoning tokens before the JSON) no longer truncate into invalid output. The readiness ping tolerates the same output-limit signal.
- **NUL-byte sanitization** ([#240](https://github.com/smaramwbc/statewave/pull/240)) — compiled memory text strips NUL (U+0000), which Postgres text columns reject, so a single stray byte in generated content can no longer fail a whole compile batch.

### v1.0 — first stable public developer release
- **Stable `/v1` API contract** — the `/v1/*` surface and the v0.9 governance layer (HMAC-signed receipts, receipt-driven replay, sensitivity labels + declarative policy, opt-in detector-suggested labels, per-region residency) are now stable for developer use under a self-hosted model. Backward-compatible additions only from here; carried-forward limitations stay documented in [why-statewave.md](../why-statewave.md).
- **Both SDKs to v1.0.0** — `statewave` (PyPI) and `@statewavedev/sdk` (npm) cut their first stable releases alongside the server, typed surfaces matching the REST contract, semver-stable from 1.0.0 forward.
- **Python SDK governance helpers** ([#176](https://github.com/smaramwbc/statewave/issues/176)) — `list_suggested_labels()` / `promote_suggested_labels()` wrap the v0.9 suggested-label review surface (sync + async, typed result models).
- **Public version-discovery endpoint** ([#178](https://github.com/smaramwbc/statewave/issues/178)) — unauthenticated `GET /v1/version` reports the running server version.
- **`session_id` on `create_episode`** ([#174](https://github.com/smaramwbc/statewave/issues/174)) — both SDKs forward the optional session pin on the wire.
- **Webhook delivery stats + tenant scoping** — optional tenant filter on event-status queries and per-tenant delivery statistics; permanent 4xx deliveries dead-letter instead of retrying.

### v0.9 — Replay, Signing, & Auto-Labeling
- **Scheduled retention-purge worker** ([#156](https://github.com/smaramwbc/statewave/issues/156)) — hourly worker reads `tenant_configs.config.receipt_retention_days` and tombstones expired receipts. Soft-delete only; rows persist for forensic lookup. Closes the loop on the retention surface v0.8 reserved. Migration 0020.
- **HMAC signing for receipts** ([#157](https://github.com/smaramwbc/statewave/issues/157)) — `hmac-sha256-canonical-v1` over the canonical body. Operator-provided keys via `STATEWAVE_RECEIPT_SIGNING_KEYS`, never persisted to DB. Per-tenant active key via `tenant_configs.config.receipt_signing_key_id`. `GET /v1/receipts/{id}/verify` returns `{valid, key_id, algorithm, reason}` with constant-time compare. Pre-v0.9 receipts verify cleanly as `no_signature`. Migration 0021.
- **Compiler heuristic auto-labeling** ([#158](https://github.com/smaramwbc/statewave/issues/158)) — opt-in `STATEWAVE_AUTO_LABELING_ENABLED`. Detectors stamp advisory `suggested_labels`, strictly separate from authoritative `sensitivity_labels`. First wave: `pii.email`, `pii.phone`, `financial.card` (Luhn), `secret.token`. Migration 0022 (GIN-indexed).
- **Receipt-driven replay** ([#159](https://github.com/smaramwbc/statewave/issues/159)) — every v0.9+ receipt embeds the active bundle's YAML (`policy_snapshot`). `POST /v1/receipts/{id}/replay` re-runs against current memories with the original policy and returns a structural diff envelope. Mode `as_of_replay`; child receipts link to the parent. Semantic: *current code + original policy*. Migration 0023.
- **Operator promote endpoint + admin UI** ([#160](https://github.com/smaramwbc/statewave/issues/160)) — `POST /admin/memories/{id}/promote-labels` is review-only, with audit-trail entries on `memory.metadata.label_promotions`. Admin app `/suggested-labels` page + receipt-detail replay button rendering the diff envelope inline.
- **Per-tenant data residency** ([#161](https://github.com/smaramwbc/statewave/issues/161)) — per-region deployment + metadata-pinned tenants. `STATEWAVE_REGION` + `tenant_configs.config.region`. Hard application-layer enforcement on `/v1/` AND `/admin/` (total isolation). HTTP 403 `residency.mismatch` on conflict. Receipts stamp `region` for end-to-end audit.

### v0.8 — Governance & Audit
- **State-assembly receipts** ([#49](https://github.com/smaramwbc/statewave/issues/49)) — `/v1/context` and `/v1/handoff` can emit an immutable, ULID-addressable receipt of which memories + episodes shaped the bundle, with a SHA-256 hash of the bytes delivered. Strict-superset schema with a `mode` discriminator (`retrieval` ships; `as_of_replay` / `eval_run` reserved for v0.9). Emission gated by env kill-switch → per-tenant config (`always | on_request | never`) → per-request flag. Read API in both SDKs and the admin app.
- **Sensitivity labels + per-memory policy bindings** ([#50](https://github.com/smaramwbc/statewave/issues/50)) — `memories.sensitivity_labels TEXT[]` + GIN index, set via `PATCH /v1/memories/{id}/labels`. Declarative YAML/JSON policy bundles (content-hashed, immutable) with six predicates and `deny` / `redact` actions; first-match-wins, default-allow. Per-tenant `policy_mode: log_only | enforce` for safe rollout — `log_only` records decisions into receipts without filtering.
- **Caller identity** — `caller_id` / `caller_type` on `/v1/context` and `/v1/handoff` feed the policy evaluator; tenant config `require_caller_identity: true` 401s anonymous calls.
- **Per-tenant configuration endpoint** — `GET / PATCH /admin/tenants/{tenant_id}/config` for receipts emission, retention, policy mode, and caller-identity gate. PATCH-shape merge, enum/bound validation at the API boundary, optimistic concurrency via `expected_version`.
- **Cross-tenant policy bundle uniqueness** ([#79](https://github.com/smaramwbc/statewave/issues/79)) — `policy_bundles` keyed on `(tenant_id, bundle_hash) NULLS NOT DISTINCT`; two tenants installing identical YAML produce independently-resolvable rows.
- **Connector ecosystem** — modular packages for GitHub, Markdown/ADRs, MCP, Slack, Discord, Zendesk, Intercom, Freshdesk, Notion, Gmail, n8n, Zapier. Tier 2 push receivers (Slack DM/MPIM, Freshdesk/Zendesk/Intercom webhooks, Gmail Pub/Sub) and Tier 3 operator productization (TOML config, hosted runner, persistent state adapters, auth-gated Prometheus `/metrics`, Docker/Compose/Helm/Fly/Railway recipes) shipped via `statewave-connectors`.

### v0.7 — Operator & Cloud Experience
- **Single LiteLLM adapter** — `server/services/llm.py` is the only module that imports LiteLLM; compilers, embeddings, and the readiness check route through it. Provider swaps are config-only via `STATEWAVE_LITELLM_*`. AST-based isolation test enforces the boundary.
- **Native pgvector retrieval** — `memories.embedding` migrated to `vector(1536)` with an HNSW index; `search_memories_by_embedding` uses the `<=>` cosine-distance operator. Eliminates the in-Python cosine compute that floored `/v1/context` at ~1.5s.
- **`/v1/context` candidate-pool union** — semantic-search rows enter the per-kind candidate pool alongside recency rows, so semantically-relevant memories outside the recency window can rank.
- **Two-layer query embedding cache** — in-process LRU+TTL (L1) + Postgres-backed `query_embedding_cache` (L2), shared across all backend instances. Repeat queries hit sub-second regardless of which instance handles them.
- **Deep readiness checks** — `/readyz` verifies DB, job queue, and LLM provider reachability with typed errors and per-check latency.
- **Migration safety** — preflight script, startup schema guard, `/ops/migrations` endpoint, runbook.
- **Admin dashboard (read-only)** — system health, jobs, webhooks, counts, health distribution.
- **Usage metering** — episodes/month, compiles/month, per-tenant.

### v0.6 — Support-Agent Superiority
- Session-aware context assembly (active session boosted, resolved deprioritized)
- Resolution tracking (open/resolved/unresolved per session)
- Handoff context packs (structured escalation briefs with health + SLA)
- Customer health scoring (0–100, explainable factors)
- Repeat-issue detection (prior resolution surfacing)
- Proactive health alerts (webhooks on state transitions)
- SLA tracking (response time, resolution time, breach flags)
- Proof layer: 3 eval suites (56 assertions), 2 benchmarks (8/8 vs 2/8 stateless)

### v0.5 — Reliability & Trust
- True multi-tenant isolation (tenant_id on all tables, query-scoped)
- Distributed rate limiting (Postgres-backed)
- Backup/restore tooling (subject-level export/import)
- Durable async compilation (Postgres-backed job queue)
- Reliable webhook delivery — persistent queue, exponential backoff, dead-letter
- SDK retry with backoff — automatic 429/5xx retry with jitter
- Admin introspection endpoints (jobs, webhooks, tenant audit)
- Compilation status API

### v0.4 — Adoption Readiness
- Batch episode ingestion (up to 100 per request)
- OpenTelemetry tracing (optional)
- Deployment guide (Docker, Fly.io, Railway)
- SDK publish readiness, getting-started guide
- Support-agent benchmark and "Why Statewave" comparison doc

### v0.3.5 stabilization
- Fixed middleware execution order (auth before rate limit)
- Compile + conflict resolution in single transaction
- Request validation (string lengths, bounded limits)
- LLM compiler runs in ThreadPoolExecutor (non-blocking)
- SDKs support auth, tenant headers, and semantic search

### v0.3 additions
- LLM-backed memory compiler (any provider via LiteLLM, thread-pooled)
- Embedding generation (LiteLLM + stub providers)
- Semantic search via pgvector cosine similarity with fallback
- Temporal reasoning in context assembly
- Memory conflict resolution (Jaccard similarity, auto-supersede)
- Webhooks (episode.created, memories.compiled, subject.deleted)
- API key authentication, rate limiting (per-IP)
- Multi-tenant header extraction

### v0.2 additions
- Pluggable `BaseCompiler` protocol
- Ranked retrieval with composite scoring
- Request ID middleware, structured errors, health endpoints
- SDKs with typed exceptions (Python + TypeScript)
