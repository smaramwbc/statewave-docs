# Statewave Documentation

Architecture docs, product specs, API contracts, and development coordination for the Statewave workspace.

> This repo contains no production runtime code.

## 🎯 Live Demo

> **[▶ Try the interactive demo →](https://statewave-demo.vercel.app)**
>
> See two identical AI agents answer side by side — one stateless, one with full customer history powered by Statewave. No setup required.

## Contents

- **[Getting Started](getting-started.md)** ← start here
- [What is Statewave?](product.md)
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

## Repositories

| Repo | Description |
|------|-------------|
| [statewave](https://github.com/smaramwbc/statewave) | Server — API, domain model, DB, compilation, search |
| [statewave-py](https://github.com/smaramwbc/statewave-py) | Python SDK (sync + async) |
| [statewave-ts](https://github.com/smaramwbc/statewave-ts) | TypeScript SDK |
| [statewave-demo](https://github.com/smaramwbc/statewave-demo) | **[Live interactive demo](https://statewave-demo.vercel.app)** |
| [statewave-examples](https://github.com/smaramwbc/statewave-examples) | Runnable examples and quickstarts |

## Current status

**v0.4.x** — Batch episode ingestion, OpenTelemetry tracing, subject listing, deployment guides, SDK publish readiness. See [roadmap](roadmap.md) and [CHANGELOG](CHANGELOG.md) for details.
