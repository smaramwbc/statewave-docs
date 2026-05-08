# Connectors Roadmap

The connector ecosystem ships in phases. Each phase brings a new class of memory online. Connectors are developed in the [statewave-connectors](https://github.com/smaramwbc/statewave-connectors) monorepo and published as separate packages — install only the ones you need.

## Phase 1 — foundation ✅

Available now in the connectors repo (publishing to npm follows in a near-term release).

- `@statewavedev/connectors-core` — connector contract, episode schema, idempotency, retry, redaction, source state
- `@statewavedev/connectors-cli` — `statewave-connectors` CLI: `doctor`, `sync`, `replay`, `test`, `mcp`
- `@statewavedev/mcp-server` — tool surface for `ingest_episode`, `search_memories`, `get_context`, `get_timeline`, `compile_subject` (transport wiring follows)
- `@statewavedev/connectors-github` — issues, PRs, comments, reviews, releases
- `@statewavedev/connectors-markdown` — local docs, ADRs, RFCs, decision pages

## Phase 2 — community & team

- `@statewavedev/connectors-discord` — community memory from servers, channels, forum posts
- `@statewavedev/connectors-slack` — team and shared-channel memory

## Phase 3 — customer support

- `@statewavedev/connectors-zendesk` — ticket and reply memory
- `@statewavedev/connectors-intercom` — conversation and contact-note memory
- `@statewavedev/connectors-freshdesk` — ticket and reply memory

## Phase 4 — knowledge & relationships

- `@statewavedev/connectors-notion` — pages, databases, decision docs
- `@statewavedev/connectors-gmail` — thread-level relationship memory, scoped by label/query

## Phase 5 — workflow

- `@statewavedev/connectors-n8n` — workflow run memory
- `@statewavedev/connectors-zapier` — zap run memory

## Out of scope (for now)

- **Real-time webhook receivers.** Connectors are pull-first today. A separate webhook-receiver package is planned once the contract has stabilized.
- **Hosted "all-in-one" agent.** Connectors are libraries plus a CLI. We do not ship a hosted ingestion server.
- **Telemetry / phone-home.** There is none, and there will not be.

## Tracking

Open issues and milestones in the [statewave-connectors GitHub project](https://github.com/smaramwbc/statewave-connectors) reflect the canonical state. The [roadmap inside that repo](https://github.com/smaramwbc/statewave-connectors/blob/main/docs/roadmap.md) is updated when a phase ships.

## See also

- [Statewave roadmap](../roadmap.md) — the broader product roadmap
- [Quickstart](quickstart.md) — try Phase-1 connectors today
