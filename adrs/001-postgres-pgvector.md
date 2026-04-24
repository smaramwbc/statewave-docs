# ADR-001: Use PostgreSQL + pgvector as sole data store for v1

**Status:** Accepted  
**Date:** 2026-04-24

## Context

We need a durable store for episodes, memories, and embeddings. Options considered: Postgres, Postgres+pgvector, dedicated vector DB, Redis, multi-store.

## Decision

Use PostgreSQL with the pgvector extension as the single data store for v1.

## Rationale

- One database to operate, backup, and reason about
- pgvector handles embedding similarity search adequately for MVP scale
- Postgres JSONB handles flexible payloads
- Alembic provides reliable migrations
- Avoids operational complexity of multiple stores
- Easy to swap or add a dedicated vector DB later if needed

## Consequences

- Embedding search performance is bounded by pgvector capabilities
- Acceptable for MVP; revisit at scale
