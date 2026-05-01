# Architecture Overview

Version: **0.6.x**

Statewave is a **Memory OS** — a trusted context runtime for AI agents and applications.

## Core loop

```
RECORD → COMPILE → CONTEXT → GOVERN
```

1. **Record** — immutable episodes capture raw interaction truth
2. **Compile** — pluggable compilers (heuristic or LLM) derive typed memories with provenance, embeddings, and conflict resolution
3. **Context** — assembly service builds ranked, token-bounded, deterministic context bundles using temporal reasoning and semantic similarity
4. **Govern** — provenance inspection, delete-by-subject, authentication, rate limiting, webhook notifications

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
- **Embeddings:** `StubEmbeddingProvider` (deterministic hash vectors for dev/test) and `OpenAIEmbeddingProvider` (real semantic vectors via LiteLLM — supports OpenAI, Azure, Cohere, Bedrock, etc.)
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
| **Memory** | Derived typed memory | id, subject_id, kind, content, summary, confidence, valid_from, valid_to, source_episode_ids, status, embedding |
| **ContextBundle** | Runtime output | subject_id, task, facts, episodes, procedures, provenance, assembled_context, token_estimate |

## Version history

### v0.5 — Reliability & Trust
- True multi-tenant isolation (tenant_id on all tables, query-scoped)
- Distributed rate limiting (Postgres-backed)
- Backup/restore tooling (subject-level export/import)
- Durable async compilation (Postgres-backed job queue)
- Admin introspection endpoints (jobs, webhooks, tenant audit)

### v0.6 — Support-Agent Superiority
- Session-aware context assembly (active session boosted, resolved deprioritized)
- Resolution tracking (open/resolved/unresolved per session)
- Handoff context packs (structured escalation briefs with health + SLA)
- Customer health scoring (0–100, explainable factors)
- Repeat-issue detection (prior resolution surfacing)
- Proactive health alerts (webhooks on state transitions)
- SLA tracking (response time, resolution time, breach flags)

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
