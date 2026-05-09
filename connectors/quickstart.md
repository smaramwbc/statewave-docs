# Connectors Quickstart

This page walks you through installing the Statewave connector CLI, running a connector against a real source, and wiring up the MCP server — all dry-run-first so nothing is ingested without your say-so.

> **Prerequisites:** A running Statewave instance — see [Getting Started](../getting-started.md). Node 20+ for the connector tooling. All packages below ship from [statewave-connectors](https://github.com/smaramwbc/statewave-connectors).

---

## 1. Install

Pick what you need — every package is independent.

```bash
npm install -g @statewavedev/connectors-cli       # the `statewave-connectors` CLI

npm install @statewavedev/connectors-github       # repo memory
npm install @statewavedev/connectors-markdown     # docs / ADR / RFC memory
npm install @statewavedev/connectors-slack        # team / channel / DM / group-DM memory + Events-API webhook
npm install @statewavedev/connectors-discord      # community memory (servers + threads)
npm install @statewavedev/connectors-zendesk      # customer memory (tickets + comments)
npm install @statewavedev/connectors-intercom     # customer memory (conversations + notes)
npm install @statewavedev/connectors-freshdesk    # customer memory (tickets + conversations)
npm install @statewavedev/connectors-notion       # decision memory (pages + databases + comments)
npm install @statewavedev/connectors-gmail        # relationship memory (messages + History API delta)
npm install @statewavedev/connectors-n8n          # workflow memory
npm install @statewavedev/connectors-zapier       # helper for Webhooks-by-Zapier flows

npm install @statewavedev/mcp-server              # expose Statewave to MCP clients
```

Each package is independent — install only what you need. The convenience meta-package `@statewavedev/connectors` re-exports all of the above for callers who genuinely want every connector at once; it is **not** required for normal usage.

Or build from source if you want the latest unreleased work:

```bash
git clone https://github.com/smaramwbc/statewave-connectors.git
cd statewave-connectors
pnpm install
pnpm build
```

---

## 2. Point the CLI at Statewave

```bash
export STATEWAVE_URL=http://localhost:8000
export STATEWAVE_API_KEY=...        # only required if your instance enforces auth
```

The CLI will refuse to ingest unless `STATEWAVE_URL` is set. There is no auto-detection.

Verify everything is wired up:

```bash
statewave-connectors doctor
```

You'll get a per-variable diagnostic — green for set, yellow for "not set, only required if you use X".

---

## 3. Dry-run first

Every connector supports `--dry-run`, which runs the read path and prints the mapped episodes **without** calling the Statewave ingest API. Use it before every first-time sync.

### GitHub

```bash
export GITHUB_TOKEN=ghp_...   # only used by the GitHub connector

statewave-connectors sync github \
  --repo smaramwbc/statewave \
  --subject repo:smaramwbc/statewave \
  --dry-run
```

You'll see `github.issue.opened`, `github.pr.merged`, `github.release.published`, etc., printed as normalized [episodes](concepts.md).

### Markdown / docs

```bash
statewave-connectors sync markdown \
  --path ./docs \
  --subject repo:smaramwbc/statewave \
  --dry-run
```

ADRs under `adrs/`, RFCs under `rfcs/`, and decision/architecture docs are detected and mapped to `docs.adr`, `docs.rfc`, `docs.decision`. Everything else becomes `docs.page`.

### Slack

```bash
export SLACK_BOT_TOKEN=xoxb-...   # only used by the Slack connector

statewave-connectors sync slack \
  --channels general,support \
  --subject team:acme \
  --since 2026-01-01 \
  --dry-run
```

The bot needs `channels:history` + `channels:read` (and the `groups:*` equivalents for private channels — invite the bot first). Top-level messages map to `slack.message.posted`; thread replies to `slack.thread.replied`.

### n8n

```bash
export N8N_API_KEY=...

statewave-connectors sync n8n \
  --workflows "Daily ETL,42" \
  --instance-url https://n8n.example.com \
  --since 2026-01-01 \
  --dry-run
```

`--workflows` accepts ids (visible in the n8n URL) or names. Successful runs become `n8n.workflow.executed`; failed runs become `n8n.workflow.failed`; per-node errors are extracted from the execution's `runData` blob and emitted as `n8n.node.errored`.

### Zapier — push-mode helper

Zapier doesn't expose a public API for enumerating other zaps' run history, so it's not a `sync` source. Instead, configure a **"Webhooks by Zapier → POST"** step at the end of your zap and POST directly to `/v1/episodes/batch`, or use [`formatZapToEpisode()`](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/zapier/README.md) on a server you run to massage payloads first.

---

## 4. Ingest for real

When the dry-run output looks right, drop the flag:

```bash
statewave-connectors sync github \
  --repo smaramwbc/statewave \
  --subject repo:smaramwbc/statewave
```

Re-running the same command is safe: every episode has a stable [`idempotency_key`](concepts.md#idempotency-key), so Statewave deduplicates instead of double-storing.

Use `--since 2026-01-01` to limit to recent activity, `--max-items 50` to cap the run, and `--include` / `--exclude` to slice (e.g. `--include prs,releases`).

---

## 5. Connect an agent over MCP

```bash
statewave-connectors mcp start
```

This launches the [Statewave MCP server](mcp.md), which exposes `statewave_ingest_episode`, `statewave_search_memories`, `statewave_get_context`, `statewave_get_timeline`, and `statewave_compile_subject`. Any MCP-compatible client — coding assistant, custom agent, IDE extension — can call those tools.

Once connected, ask the agent something it would otherwise have no way to know:

> "What's currently blocking on smaramwbc/statewave?"

The agent calls `statewave_get_context` with `subject=repo:smaramwbc/statewave` and answers from compact, ranked context — not raw chat history.

---

## What's next

- [Concepts](concepts.md) — episodes, subjects, kinds, idempotency keys
- [Subject strategy](subject-strategy.md) — pick subjects your agents will actually ask about
- [Privacy & redaction](privacy-redaction.md) — dry-run, secret scrubbing, include/exclude
- [Roadmap](roadmap.md) — what's shipping when
