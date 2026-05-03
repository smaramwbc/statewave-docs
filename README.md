# Statewave Documentation

Architecture docs, product specs, API contracts, and development coordination for the Statewave workspace.

> This repo contains no production runtime code.
>
> 📋 **Issues & feature requests:** [statewave/issues](https://github.com/smaramwbc/statewave/issues) (centralized tracker)

## 🎯 Try it

> The interactive comparison demo is embedded directly in the website at **[statewave.ai](https://statewave.ai)** — open the chat widget to see two identical AI agents answer side by side, one stateless and one backed by Statewave.
>
> **Got a question about Statewave?** **[Ask Statewave Support →](https://statewave.ai/?ask=support)** — a docs-grounded agent that answers from this very docs corpus and cites the pages it used (read-only; built on the [docs memory pack](default-support-docs-pack.md)).

## Contents

- **[Getting Started](getting-started.md)** ← start here
- [What is Statewave?](product.md)
- [Why Statewave?](why-statewave.md) — technical comparison for support-agent workflows
- [Use Cases map](https://statewave.ai/use-cases) — categorized inventory of what you can build (support, coding, workspace, account, voice, agent infrastructure, connectors, frontier ideas)
- [Architecture Overview](architecture/overview.md)
- [Repo Map](architecture/repo-map.md)
- [API v1 Contract](api/v1-contract.md)
- [Deployment Guide](deployment/guide.md)
- [Deployment Sizing Guide](deployment/sizing.md) — hardware profiles by tier, topology patterns, bottleneck guidance
- [Capacity Planning & Tuning Checklist](deployment/capacity-planning.md) — diagnostic flow when load grows, tuning order, when to move up a tier
- [Default support docs memory pack](default-support-docs-pack.md) — the docs-only knowledge base shipped for out-of-the-box support agents
- [Roadmap](roadmap.md)
- [Development Conventions](dev/conventions.md)

## Community

- **[Community guide](community/discussions.md)** — where to post what, how to write good questions and RFCs, tone and moderation
- [Discussion templates](community/discussion-templates.md) — Q&A, feature request, RFC, show-and-tell, integration, research
- [Pinned discussion drafts](community/pinned-discussions/) — ready-to-copy posts (welcome, what-are-you-building, roadmap priorities, RFCs)
- [Operator setup checklist](community/discussions-setup.md) — for maintainers configuring categories, pins, and recurring review

GitHub Discussions live on the core repo: **[statewave/discussions](https://github.com/smaramwbc/statewave/discussions)**.

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
