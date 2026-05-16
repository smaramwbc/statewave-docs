# Statewave Documentation

[![CI](https://github.com/smaramwbc/statewave-docs/workflows/CI/badge.svg)](https://github.com/smaramwbc/statewave-docs/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**Statewave is the open-source memory runtime for AI agents.** It compiles raw events into ranked, token-bounded context bundles with full provenance — so your AI stops forgetting across sessions. Self-hosted on Postgres, no vendor lock-in.

This repo contains the architecture docs, product specs, API contracts, and development coordination for the Statewave workspace.

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
- **[Connectors](connectors/index.md)** — feed real-world events (GitHub, Markdown/ADRs, MCP, and more) into Statewave as normalized episodes
- [Subject Design](subject-design.md) — the architectural treatment of subjects (entity granularity, tenancy, modelling)
- [Architecture Overview](architecture/overview.md)
- [Repo Map](architecture/repo-map.md)
- [API v1 Contract](api/v1-contract.md)
- [State-assembly receipts](receipts.md) — the immutable audit artifact emitted on each context assembly
- [Sensitivity labels & policy](sensitivity-labels.md) — per-memory capability tags + bundled rules consulted on every assembly call
- [Deployment Guide](deployment/guide.md)
- [Deployment Sizing Guide](deployment/sizing.md) — hardware profiles by tier, topology patterns, bottleneck guidance
- [Capacity Planning & Tuning Checklist](deployment/capacity-planning.md) — diagnostic flow when load grows, tuning order, when to move up a tier
- [Default support docs memory pack](default-support-docs-pack.md) — the docs-only knowledge base shipped for out-of-the-box support agents
- [Roadmap](roadmap.md)
- [Development Conventions](dev/conventions.md)
- [License](license.md) — Apache-2.0

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

| Project | Description |
|---|---|
| [Server](https://github.com/smaramwbc/statewave) | Core server — API, domain model, DB, compilation, search |
| [Python SDK](https://github.com/smaramwbc/statewave-py) | `pip install statewave` — sync + async client |
| [TypeScript SDK](https://github.com/smaramwbc/statewave-ts) | `npm install @statewavedev/sdk` — fetch-based client |
| [Connectors](https://github.com/smaramwbc/statewave-connectors) | `@statewavedev/connectors-*` — GitHub, Markdown/docs, MCP server, modular packages |
| [Docs](https://github.com/smaramwbc/statewave-docs) | This repo — architecture, specs, ADRs (no runtime code) |
| [Examples](https://github.com/smaramwbc/statewave-examples) | Runnable examples, evals, benchmarks |
| [Website + demo](https://github.com/smaramwbc/statewave-web) | Marketing website + embedded comparison demo ([statewave.ai](https://statewave.ai)) |
| [Admin](https://github.com/smaramwbc/statewave-admin) | Operator console — system health, jobs, usage (read-only) |

## Current status

**v0.9.0** — Server and API contract are unchanged from v0.8.0; this version aligns the workspace number with the TypeScript SDK's pre-1.0 breaking camelCase rename (statewave-ts#103). See the [statewave-ts CHANGELOG](https://github.com/smaramwbc/statewave-ts/blob/main/CHANGELOG.md) for the migration table. The product surface remains the v0.8.0 governance & audit layer: every context assembly can emit an immutable [state-assembly receipt](receipts.md) (content-hash integrity, ULID-addressable, queryable per subject), per-memory [sensitivity labels](sensitivity-labels.md) feed a declarative YAML policy engine that filters memories by caller identity, and per-tenant config flips enforce mode on without a SQL shell. Builds on the v0.7.x foundation (memory TTL, Helm, cross-machine embedding cache) and the v0.6.x support-agent intelligence stack (session-aware context, resolution tracking, handoff packs, health scoring, SLA tracking, proactive alerts). See [roadmap](roadmap.md) and [CHANGELOG](CHANGELOG.md).
