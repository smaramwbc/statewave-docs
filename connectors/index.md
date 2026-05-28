# Connectors

Statewave Connectors feed real-world events into Statewave so agents can remember projects, customers, communities, docs, tickets, emails, and workflows — not just live chat transcripts.

A connector is a small, focused package that reads from one source, normalizes its events into the Statewave [episode schema](concepts.md), and lets the CLI or your own code ingest them. Statewave compiles those episodes into durable memories per subject, and serves compact context to your agents on demand.

> **Status:** the v0.1 connector matrix is fully shipped, plus two polish waves (v0.5.x, v0.6.0), the **Tier 2 push-receiver wave (v0.7.0–v0.11.0)**, and the **Tier 3 operator/cloud productization wave (v0.12.0–v0.17.0)** — TOML config file (multi-instance), hosted runner (`statewave-connectors run`), persistent state adapters (file / Postgres / Redis), built-in OIDC verification for Gmail Pub/Sub, auth-gated Prometheus `/metrics`, and deployment recipes (Docker / Compose / Helm / Fly / Railway). All packages — GitHub, Markdown, MCP, Slack (pull + Events-API webhook + DM/MPIM dispatch), n8n, Zapier helper, Discord, Zendesk (pull + webhook receiver), Intercom (pull + webhook receiver), Freshdesk (pull + webhook receiver), Notion, Gmail (pull + Cloud Pub/Sub push receiver), Jira (preview), and database (preview; PostgreSQL / MySQL / MariaDB / MSSQL) — are on npm with provenance attestation. `statewave-connectors listen <connector>` is the unified push-receiver daemon; `statewave-connectors run` is the hosted runner for long-running connectors. Long-running daemon shapes (Slack Socket Mode, Discord Gateway, Gmail service-account auth) are still queued. See the [roadmap](roadmap.md) for the full release timeline.

## What's available

### MCP server

Connect Statewave memory to any MCP-compatible client — coding assistants, agent loops, custom tools. Vendor-neutral by design. → [MCP server](mcp.md)

### GitHub

Turn issues, pull requests, reviews, releases, and discussions into **repo memory**. → [GitHub connector](github.md)

### Markdown / docs

Turn local docs, ADRs, RFCs, and decision notes into **project memory** — the team's actual reasoning, not a re-derivation of it. → [Markdown connector](markdown.md)

### Slack

Turn channel and thread history into **team memory** under `team:<team_id>`. Pull mode (Web API + bot token + `--channels` allowlist) and an Events-API webhook receiver (`statewave-connectors listen slack`) that ingests messages, replies, reactions, and pins in real time, with opt-in DMs and group DMs (subjects `dm:<user>` / `mpim:<channel>`). `slack.message.posted`, `slack.thread.replied`, `slack.dm.*`, `slack.mpim.*`. → [`@statewavedev/connectors-slack` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/slack/README.md)

### n8n

Turn workflow executions, failures, and per-node errors into **workflow memory** under `workflow:<id>`. Pull-mode against the n8n REST API; API-key auth. `n8n.workflow.executed`, `n8n.workflow.failed`, `n8n.node.errored`. → [`@statewavedev/connectors-n8n` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/n8n/README.md)

### Zapier — helper

Push-mode helper rather than a sync connector — Zapier deliberately doesn't expose a public API for enumerating other zaps' run history. The package ships `formatZapToEpisode()` for users who want to receive Zap webhooks server-side, plus integration docs for the no-code "POST straight to `/v1/episodes/batch`" path. → [`@statewavedev/connectors-zapier` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/zapier/README.md)

### Discord

Turn server channel + thread history into **community memory** under `community:<guild_id>`. Bot-token auth; required `--guild` + `--channels`. `discord.message.posted`, `discord.thread.replied`. → [`@statewavedev/connectors-discord` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/discord/README.md)

### Zendesk

Turn tickets + public replies + internal notes into **customer memory** under `customer:<org_or_requester_id>`. Pull mode (API token + OAuth bearer auth, `--brands` / `--statuses` allowlists, Incremental Tickets Export delta sync via `--cursor` / `--use-incremental`) plus a webhook receiver (`statewave-connectors listen zendesk`) with HMAC-SHA256 signature verification, replay-window protection, and support for both trigger-driven and event-driven payloads. `zendesk.ticket.created`, `zendesk.ticket.solved`, `zendesk.comment.posted`, `zendesk.comment.internal_note`. → [`@statewavedev/connectors-zendesk` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/zendesk/README.md)

### Intercom

Turn conversations + replies + admin notes into **customer memory** under `customer:<company_or_contact_id>`. Pull mode (bearer auth — personal-access or OAuth, US/EU/AU regions, `--tags` / `--teams` allowlists) plus a webhook receiver (`statewave-connectors listen intercom`) that verifies Intercom's `X-Hub-Signature` HMAC-SHA1 and dispatches all five `conversation.*` notification topics. `intercom.conversation.created`, `intercom.conversation.closed`, `intercom.conversation.replied`, `intercom.conversation.note_added`. → [`@statewavedev/connectors-intercom` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/intercom/README.md)

### Freshdesk

Turn tickets + public replies + private notes into **customer memory** under `customer:<company_or_requester_id>`. Pull mode (API key Basic auth, native `updated_since` server-side `--since` filter, status-code normalization) plus a webhook receiver (`statewave-connectors listen freshdesk`) that verifies a configurable shared-secret header set on the Freshdesk Automation step. `freshdesk.ticket.created`, `freshdesk.ticket.resolved`, `freshdesk.conversation.posted`, `freshdesk.conversation.internal_note`. → [`@statewavedev/connectors-freshdesk` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/freshdesk/README.md)

### Notion

Turn pages, optional body content, and (opt-in) page-level discussion comments into **decision memory** under `workspace:notion` (or any operator-supplied subject). Bearer auth; pinned to `Notion-Version: 2022-06-28`; `--databases` allowlist for database-scoped pulls. `notion.page.created`, `notion.page.updated`, `notion.comment.posted`. → [`@statewavedev/connectors-notion` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/notion/README.md)

### Gmail

Turn messages matching a required Gmail search query into **relationship memory** under `relationship:<other_email>`. Pull mode (OAuth 2.0 refresh-token flow, History API delta sync via `--cursor`, `--label-ids` server-side filter, MIME body extraction text/plain → text/html → snippet) plus a Cloud Pub/Sub push receiver (`statewave-connectors listen gmail`) — Gmail's `users.watch` publishes a `{ emailAddress, historyId }` pointer to a Pub/Sub topic; the receiver walks the History API from a persistent per-mailbox cursor and emits the same episode kinds the pull connector does. `gmail.message.received`, `gmail.message.sent`. → [`@statewavedev/connectors-gmail` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/gmail/README.md)

### Jira (preview)

Turn Jira Cloud issues and (opt-in) comments into **project memory** under `project:<KEY>`. Jira Cloud REST v3, API-token auth, pull-mode; project allowlist; no-email user fields (displayName / accountId); ADF → plain-text; redaction. `jira.issue.created`, `jira.issue.resolved`, `jira.comment.created`. → [`@statewavedev/connectors-jira` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/jira/README.md)

### Database (preview)

Ingest **selected external rows** from a relational database into Statewave memory. One package, four dialects — **PostgreSQL, MySQL, MariaDB, MSSQL**. Read-only, allowlisted table or operator `SELECT`, selected columns, required `--max-rows`, `${ENV}` secrets, no schema-wide dump, no mutation queries, no binary ingestion. This is a **source connector**, not a Statewave storage backend — Statewave's own storage remains PostgreSQL + pgvector. `database.row`. All four dialects — PostgreSQL, MySQL, MariaDB, and MSSQL — are live-verified (MSSQL has no per-session read-only flag, so use a least-privilege read-only login). → [`@statewavedev/connectors-database` README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/database/README.md)

## Modular by design

Connectors are developed as a monorepo but published as **separate, independent packages**. You install only what you need.

```bash
npm install @statewavedev/connectors-github
npm install @statewavedev/connectors-markdown
npm install @statewavedev/connectors-slack
npm install @statewavedev/connectors-n8n
npm install @statewavedev/connectors-zapier
npm install @statewavedev/mcp-server
```

A convenience meta-package `@statewavedev/connectors` re-exports the official connectors for the rare case where you want them all at once. **It is not required for normal usage** and not the recommended install path.

You never need to install Slack, n8n, or Zapier to use the GitHub connector. Each connector pulls only the credentials and dependencies it actually uses.

## Where to start

- New here? **[Quickstart →](quickstart.md)**
- Want the model? **[Concepts: episode, subject, kind →](concepts.md)**
- Picking subjects? **[Subject strategy →](subject-strategy.md)**
- Worried about data? **[Privacy & redaction →](privacy-redaction.md)**
- Building a new connector? See [contributing in the connectors repo](https://github.com/smaramwbc/statewave-connectors/blob/main/docs/contribution-guide.md).

## See also

- [Subject Design](../subject-design.md) — the deep architectural treatment of subjects in Statewave
- [API v1 Contract](../api/v1-contract.md) — the underlying ingest and context APIs that connectors call
- [Architecture Overview](../architecture/overview.md) — how episodes become memory becomes context
