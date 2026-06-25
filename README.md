# Statewave Documentation

[![CI](https://github.com/smaramwbc/statewave-docs/workflows/CI/badge.svg)](https://github.com/smaramwbc/statewave-docs/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**Statewave is the open-source memory runtime for AI agents.** It compiles raw events into ranked, token-bounded context bundles with full provenance — so your AI stops forgetting across sessions. Self-hosted on Postgres, no vendor lock-in.

This repo contains the architecture docs, product specs, API contracts, and development coordination for the Statewave workspace.

> This repo contains no production runtime code.
>
> 📋 **Issues & feature requests:** [statewave/issues](https://github.com/smaramwbc/statewave/issues) (centralized tracker)

## Install

Fastest — one line to a running server:

```bash
# macOS / Linux
npx @statewavedev/statewave
# or
curl -fsSL https://www.statewave.ai/install | sh
```

```powershell
# Windows (PowerShell)
irm https://www.statewave.ai/install.ps1 | iex
```

Prefer to run it yourself? The [Getting Started guide](getting-started.md) walks through the manual `git clone` + `docker compose up -d` path in about 5 minutes.

## 🎯 Try it

> The interactive comparison demo is embedded directly in the website at **[statewave.ai](https://statewave.ai)** — open the chat widget to see two identical AI agents answer side by side, one stateless and one backed by Statewave.
>
> **Got a question about Statewave?** **[Ask Statewave Support →](https://statewave.ai/?ask=support)** — a docs-grounded agent that answers from this very docs corpus and cites the pages it used (read-only; built on the [docs memory pack](default-support-docs-pack.md)).

## Contents

- **[Getting Started](getting-started.md)** ← start here
- [What is Statewave?](product.md)
- [Why Statewave?](why-statewave.md) — technical comparison for support-agent workflows
- **[Design partner onboarding](design-partners.md)** — 30-minute setup, evaluation checklist, success criteria, FAQ — for teams adopting Statewave early
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

**v1.3.0** — hybrid retrieval (pgvector + Postgres BM25, on by default with a `hybrid=false` opt-out) and compile-pipeline recall improvements (dedup/reconcile), plus provider-aware LLM key routing. The `/v1/*` API contract and governance surfaces (HMAC-signed [receipts](receipts.md), receipt-driven replay, per-memory [sensitivity labels](sensitivity-labels.md) + declarative YAML policy, opt-in detector-suggested labels, per-region data residency) remain stable, as do the v1.2 additions (dynamic settings endpoint for topology-agnostic hot-reload, a production-readiness probe, SSRF + DNS-rebinding protection on the webhook URL probe, LIKE metachar escaping in admin search, and six admin inspection endpoints). Both SDKs ship alongside: `statewave` (PyPI) v1.2.0 adds per-call timeout overrides and `CancelledError` propagation; `@statewavedev/sdk` (npm) v1.2.0 adds `AbortSignal` support on all HTTP methods. See [roadmap](roadmap.md) and [CHANGELOG](CHANGELOG.md).
