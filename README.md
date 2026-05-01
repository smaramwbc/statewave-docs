# Statewave Documentation

Architecture docs, product specs, API contracts, and development coordination for the Statewave workspace.

> This repo contains no production runtime code.
>
> 📋 **Issues & feature requests:** [statewave/issues](https://github.com/smaramwbc/statewave/issues) (centralized tracker)

## 🎯 Try it

> The interactive comparison demo is embedded directly in the website at **[statewave.ai](https://statewave.ai)** — open the chat widget to see two identical AI agents answer side by side, one stateless and one backed by Statewave.

## Contents

- **[Getting Started](getting-started.md)** ← start here
- [What is Statewave?](product.md)
- [Why Statewave?](why-statewave.md) — technical comparison for support-agent workflows
- [Architecture Overview](architecture/overview.md)
- [Repo Map](architecture/repo-map.md)
- [API v1 Contract](api/v1-contract.md)
- [Deployment Guide](deployment/guide.md)
- [Roadmap](roadmap.md)
- [Development Conventions](dev/conventions.md)

## ADRs

- [ADR-001: PostgreSQL + pgvector as sole data store](adrs/001-postgres-pgvector.md)
- [ADR-002: Heuristic compilation for v1](adrs/002-heuristic-compilation.md)
- [ADR-003: v0.2 production hardening decisions](adrs/003-v02-production-hardening.md)
- [ADR-004: v0.3 advanced features decisions](adrs/004-v03-advanced-features.md)

## Ecosystem

| Repo | Description |
|------|-------------|
| [statewave](https://github.com/smaramwbc/statewave) | Core server — API, domain model, DB, compilation, search |
| [statewave-py](https://github.com/smaramwbc/statewave-py) | Python SDK (sync + async) |
| [statewave-ts](https://github.com/smaramwbc/statewave-ts) | TypeScript SDK |
| [statewave-docs](https://github.com/smaramwbc/statewave-docs) | This repo — architecture, specs, ADRs (no runtime code) |
| [statewave-examples](https://github.com/smaramwbc/statewave-examples) | Runnable examples, evals, benchmarks |
| [statewave-web](https://github.com/smaramwbc/statewave-web) | Marketing website + embedded comparison demo ([statewave.ai](https://statewave.ai)) |
| [statewave-admin](https://github.com/smaramwbc/statewave-admin) | Operator console — system health, jobs, usage (read-only) |

## Current status

**v0.6.1** — Full support-agent intelligence stack: session-aware context, resolution tracking, handoff packs, health scoring, SLA tracking, proactive alerts. Proven by 232 unit tests, 3 eval suites, 2 benchmarks. See [roadmap](roadmap.md) and [CHANGELOG](CHANGELOG.md).
