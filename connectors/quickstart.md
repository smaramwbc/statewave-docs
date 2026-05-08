# Connectors Quickstart

This page walks you through installing the Statewave connector CLI, running a connector against a real source, and wiring up the MCP server — all dry-run-first so nothing is ingested without your say-so.

> **Prerequisites:** A running Statewave instance — see [Getting Started](../getting-started.md). Node 20+ for the connector tooling. Phase-1 connector packages live in [statewave-connectors](https://github.com/smaramwbc/statewave-connectors).

---

## 1. Install

Phase-1 packages are scoped under `@statewavedev/`. Until they're published to npm, install from the connector repo by cloning and building locally:

```bash
git clone https://github.com/smaramwbc/statewave-connectors.git
cd statewave-connectors
pnpm install
pnpm build
```

When the packages publish, the install path will be:

```bash
# Planned — coming soon
npm install -g @statewavedev/connectors-cli
npm install @statewavedev/connectors-github
npm install @statewavedev/connectors-markdown
npm install @statewavedev/mcp-server
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
