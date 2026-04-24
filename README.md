# Statewave Documentation

Architecture docs, product specs, API contracts, and development coordination for the Statewave workspace.

> This repo contains no production runtime code.

## Contents

- [Architecture Overview](architecture/overview.md)
- [Repo Map](architecture/repo-map.md)
- [API v1 Contract](api/v1-contract.md)
- [Roadmap](roadmap.md)
- [Development Conventions](dev/conventions.md)

## ADRs

- [ADR-001: PostgreSQL + pgvector as sole data store](adrs/001-postgres-pgvector.md)
- [ADR-002: Heuristic compilation for v1](adrs/002-heuristic-compilation.md)
- [ADR-003: v0.2 production hardening decisions](adrs/003-v02-production-hardening.md)

## Current status

**v0.2** — Production hardening in progress. Server, both SDKs, and examples are at v0.2.0 with idempotent compilation, token-bounded ranked context, structured errors, and typed SDK exceptions. See [roadmap](roadmap.md) for details.
