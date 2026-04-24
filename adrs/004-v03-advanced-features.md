# ADR-004: v0.3 advanced features decisions

**Status:** Accepted
**Date:** 2026-04-24

## Context

After shipping v0.2 (production hardening), v0.3 added advanced features: LLM-backed compilation, embeddings, semantic search, temporal reasoning, memory conflict resolution, webhooks, authentication, rate limiting, and multi-tenant scaffolding. A subsequent v0.3.5 stabilization pass fixed correctness issues and aligned SDKs/docs.

## Decisions

### 1. LLM-backed memory compiler

Added `LLMCompiler` using OpenAI chat completions (`gpt-4o-mini` by default). The compiler sends episode text to an LLM with a structured system prompt and parses the JSON array response into typed `MemoryRow` objects.

**Key choice:** The `BaseCompiler` protocol remains synchronous. The `LLMCompiler` uses a `ThreadPoolExecutor` internally so it doesn't block the async event loop. This avoids changing the protocol contract that the heuristic compiler also implements.

**Fallback:** LLM failures (API errors, parse errors) return an empty list — no memories rather than bad memories. This is logged but does not fail the request.

### 2. Embedding generation and semantic search

Added a pluggable `BaseEmbeddingProvider` protocol with two implementations:
- `StubEmbeddingProvider` — deterministic hash-based vectors for local dev and testing
- `OpenAIEmbeddingProvider` — real semantic vectors via `text-embedding-3-small`

Embeddings are generated during memory compilation and stored on the `MemoryRow.embedding` column (pgvector `Vector(1536)`). The search endpoint accepts `semantic=true` to use cosine distance ranking.

**Fallback:** Embedding generation failures during compilation are logged and skipped — memories are stored without embeddings. Semantic search failures fall back to text ILIKE search.

### 3. Temporal reasoning in context assembly

Context scoring now includes a temporal validity signal:
- Memories with no `valid_to` (still current) or `valid_to` in the future: +3 bonus
- Memories with `valid_to` in the past (expired/superseded): -4 penalty

This causes the context assembler to naturally prefer current facts over stale ones.

### 4. Memory conflict resolution

Added `server/services/conflicts.py`. After compilation, the system detects conflicting memories within the same `(subject_id, kind)` group using Jaccard word similarity (threshold: 0.6 for profile_facts, 0.8 for other kinds). The older memory is marked `superseded` with `valid_to` set to the newer memory's `valid_from`.

**Key choice:** Conflict resolution runs in the same transaction as compilation. This was a v0.3.5 fix — the original v0.3 implementation used two separate commits, creating a data-consistency risk.

### 5. Webhooks

Added `server/services/webhooks.py`. When `STATEWAVE_WEBHOOK_URL` is configured, the server fires async HTTP POST callbacks on `episode.created`, `memories.compiled`, and `subject.deleted` events. Delivery is fire-and-forget via `asyncio.create_task`.

**Trade-off:** No retry, no delivery guarantee, no dead-letter queue. This is intentional for MVP — reliable webhook delivery is deferred to a future version.

### 6. Authentication via API keys

Added `APIKeyMiddleware` checking the `X-API-Key` header. When `STATEWAVE_API_KEY` is not configured, auth is disabled (open access for local dev). Health and docs endpoints are exempt.

**Trade-off:** Single shared API key, not per-user/per-tenant. Sufficient for design-partner deployments; proper key management is deferred.

### 7. Rate limiting

Added `RateLimitMiddleware` with a per-IP sliding window counter. Configurable via `STATEWAVE_RATE_LIMIT_RPM`. In-memory only — not suitable for multi-process deployments.

### 8. Multi-tenant scaffolding (experimental)

Added `TenantMiddleware` that extracts `X-Tenant-ID` from request headers and binds it to structlog context. **This does NOT enforce data isolation.** No `tenant_id` column exists on any table. The middleware is documented as experimental.

**Rationale:** We wanted to establish the header convention and log correlation early, but full tenant-scoped queries require schema changes and migration that we deferred.

## Consequences

- LLM compilation works but requires OpenAI API key — heuristic remains the safe default
- Semantic search is real and useful, with correct fallback behavior
- Temporal scoring naturally ages out superseded facts
- Conflict resolution + compilation are transactionally safe
- Webhooks are useful for dev workflows but not production-grade
- Auth works for single-key scenarios; SDKs support it
- Multi-tenant is scaffolding only — must not be treated as data isolation
- All SDKs (Python, TypeScript) and examples were updated for auth/semantic/tenant support in v0.3.5
