# ADR-001: PostgreSQL + pgvector as the sole data store

**Status:** Accepted — confirmed as permanent architecture (2026-05-26)
**Date:** 2026-04-24 · **Reaffirmed:** 2026-05-26 (v0.9 release-hardening pass)

## Context

We need a durable store for episodes, memories, and embeddings. Options considered: Postgres, Postgres+pgvector, dedicated vector DB, Redis, multi-store.

## Decision

Use PostgreSQL with the pgvector extension as the single data store. PostgreSQL is the supported storage layer for Statewave; other database backends are not on the roadmap.

## Rationale

- One database to operate, backup, and reason about
- pgvector handles embedding similarity search at the scales Statewave targets (native `<=>` cosine with HNSW indexes since alembic `0013_pgvector_native`)
- Postgres JSONB handles flexible payloads
- Alembic provides reliable migrations
- Avoids the operational complexity of multiple stores or a separate vector DB
- The whole governance + audit story (state-assembly receipts, HMAC signing, policy snapshots, residency stamps) is rooted in Postgres-native primitives — JSONB, partial indexes, GIN indexes, transactional `UPDATE`s. Splitting storage would weaken those guarantees.

## Consequences

- Embedding search performance is bounded by pgvector capabilities. The native pgvector path in v0.7 (alembic `0013`) removed the in-Python cosine compute that was the ~1.5s floor per `/v1/context`; further scaling is via Postgres + pgvector tuning, not a different backend.
- All deployment, operator, and ops documentation focuses on Postgres only — there is no abstraction layer to maintain for an alternative backend.
- A dedicated vector DB (or alternative storage) is **not** a planned future option. Operators choosing Statewave choose PostgreSQL + pgvector as the data layer.
