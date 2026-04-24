# ADR-003: v0.2 production hardening decisions

**Status:** Accepted
**Date:** 2026-04-24

## Context

After shipping v0.1 as a working local MVP, we needed to harden the system for real developer adoption: reliable compilation, bounded context, error handling, and SDK quality.

## Decisions

### 1. Idempotent memory compilation

The compile endpoint now checks existing memories before inserting. Recompiling the same subject with unchanged episodes produces zero new memories. This is critical for safe retry and cron-based recompilation workflows.

### 2. Pluggable compiler abstraction

Introduced `BaseCompiler` abstract class with `compile(subject_id, episodes) -> list[Memory]`. The default `HeuristicCompiler` uses regex/truncation. This interface allows LLM-backed compilers to be added without changing routes, services, or the data model.

### 3. Token-bounded ranked context assembly

Context assembly now:
- Scores memories by kind priority (fact=10, procedure=8, episode=5), recency decay, and task-keyword relevance
- Sorts by composite score descending
- Fills sections (facts, episodes, procedures) up to `max_tokens` budget using tiktoken
- Returns `token_estimate` in the response

### 4. Structured error responses

All errors return `{"error": {"code": "...", "message": "...", "details": ..., "request_id": "..."}}`. Custom exception classes (`NotFoundError`, `ConflictError`, `ValidationError`) map to appropriate HTTP status codes. FastAPI validation errors are also wrapped in this format.

### 5. Request ID middleware

Every request gets an `X-Request-ID` (client-provided or server-generated UUID). The ID is included in error responses and log entries for correlation.

### 6. SDK typed exceptions

Both Python and TypeScript SDKs now parse structured error responses into typed exception classes (`StatewaveAPIError`, `StatewaveConnectionError`, `StatewaveTimeoutError`) instead of leaking raw HTTP errors. SDKs are versioned at 0.2.0.

## Consequences

- Compilation is safe to call repeatedly (cron, webhooks, retries)
- Context bundles are predictable and token-safe for LLM injection
- Error handling is consistent across server, SDKs, and examples
- Compiler interface is ready for LLM-backed implementation in v0.3
