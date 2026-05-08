# Connectors Roadmap

The connector ecosystem ships in phases. Each phase brings a new class of memory online. Connectors are developed in the [statewave-connectors](https://github.com/smaramwbc/statewave-connectors) monorepo and published as separate packages — install only the ones you need.

## Phase 1 — foundation ✅ shipped (v0.1.0)

- `@statewavedev/connectors-core` — connector contract, episode schema, idempotency, retry, redaction, source state
- `@statewavedev/connectors-cli` — `statewave-connectors` CLI: `doctor`, `sync`, `replay`, `test`, `mcp`
- `@statewavedev/mcp-server` — `ingest_episode`, `search_memories`, `get_context`, `get_timeline`, `compile_subject` over stdio JSON-RPC 2.0
- `@statewavedev/connectors-github` — issues, PRs, comments, reviews, releases
- `@statewavedev/connectors-markdown` — local docs, ADRs, RFCs, decision pages

## Phase 2 — community & team (v0.1.1) ✅ partially shipped

- `@statewavedev/connectors-slack` ✅ — channel + thread history pull. Bot-token auth, required `--channels` allowlist, `slack.message.posted` and `slack.thread.replied`. Live Events-API mode, DMs, reactions, pinned, and channel summarization deferred.
- `@statewavedev/connectors-discord` — community memory from servers, channels, forum posts (placeholder)

## Phase 3 — customer support

- `@statewavedev/connectors-zendesk` — ticket and reply memory
- `@statewavedev/connectors-intercom` — conversation and contact-note memory
- `@statewavedev/connectors-freshdesk` — ticket and reply memory

## Phase 4 — knowledge & relationships

- `@statewavedev/connectors-notion` — pages, databases, decision docs
- `@statewavedev/connectors-gmail` — thread-level relationship memory, scoped by label/query

## Phase 5 — workflow (v0.1.1) ✅ shipped

- `@statewavedev/connectors-n8n` ✅ — workflow executions, failures, and per-node errors via the n8n REST API. `n8n.workflow.executed`, `n8n.workflow.failed`, `n8n.node.errored`.
- `@statewavedev/connectors-zapier` ✅ — push-mode helper. Zapier doesn't expose a public API for enumerating other zaps' run history, so the package ships `formatZapToEpisode()` plus integration docs for the Webhooks-by-Zapier path.

## Out of scope (for now)

- **Real-time webhook receivers / long-running daemons.** Every shipped connector is pull-first. A daemon contract (which would back Slack live mode, n8n webhooks, etc.) is a separate design effort once we have signal from real users.
- **Hosted "all-in-one" agent.** Connectors are libraries plus a CLI. We do not ship a hosted ingestion server.
- **Slack App Directory / Zapier Directory listings.** Both require a different SDK and review cycle and live in separate efforts.
- **Telemetry / phone-home.** There is none, and there will not be.

## Tracking

Open issues and milestones in the [statewave-connectors GitHub project](https://github.com/smaramwbc/statewave-connectors) reflect the canonical state. The [roadmap inside that repo](https://github.com/smaramwbc/statewave-connectors/blob/main/docs/roadmap.md) is updated when a phase ships.

## See also

- [Statewave roadmap](../roadmap.md) — the broader product roadmap
- [Quickstart](quickstart.md) — try the shipped connectors today
