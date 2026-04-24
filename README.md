# Statewave Documentation

Architecture docs, product specs, API contracts, and development coordination for the Statewave workspace.

> This repo contains no production runtime code.

## Contents

- **[Getting Started](getting-started.md)** ← start here
- [Architecture Overview](architecture/overview.md)
- [Repo Map](architecture/repo-map.md)
- [API v1 Contract](api/v1-contract.md)
- [Roadmap](roadmap.md)
- [Development Conventions](dev/conventions.md)

## ADRs

- [ADR-001: PostgreSQL + pgvector as sole data store](adrs/001-postgres-pgvector.md)
- [ADR-002: Heuristic compilation for v1](adrs/002-heuristic-compilation.md)
- [ADR-003: v0.2 production hardening decisions](adrs/003-v02-production-hardening.md)
- [ADR-004: v0.3 advanced features decisions](adrs/004-v03-advanced-features.md)

## Current status

**v0.3.5** — Stabilization complete. Server, both SDKs, and examples are at v0.3.5 with LLM compilation, semantic search, temporal reasoning, conflict resolution, webhooks, authentication, rate limiting, and experimental multi-tenant support. All repos are aligned on version numbers, auth support, and documentation. See [roadmap](roadmap.md) for details.
