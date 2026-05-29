# AGENTS.md — guide for contributors and coding agents

A short orientation for humans and AI coding agents (GitHub Copilot, Claude,
Cursor, …) working in **statewave-docs** — the documentation source for
Statewave, and the home of the cross-repo consistency tooling in
[`tools/`](tools/).

## Working on the docs

- Docs are Markdown under this repo. Start from the [README](README.md) and
  [getting-started](getting-started.md).
- **Lint matches CI:** `markdownlint-cli2 "**/*.md"` (not `markdownlint-cli`)
  and a [lychee](https://github.com/lycheeverse/lychee) link check.
- **Consistency checks** (also CI/release gates): `python tools/check-versions.py`
  and `python tools/check-proof-figures.py` — both exit non-zero on drift.

## Conventions

- **Proof figures are mirrored.** Test counts, eval assertion/test counts, and
  the support-workflow benchmark score have a single source of truth in
  [`tools/_proof_figures.py`](tools/_proof_figures.py). Change that, then run
  `python tools/check-proof-figures.py` and fix every surface it flags — never
  hand-edit one doc.
- **Packages version independently.** The server and the SDKs version on
  separate cadences; the compatibility axis is the `/v1` API contract, not a
  shared number. See [`tools/`](tools/README.md) for how that is enforced.
- **Keep claims accurate and modest.** Back any performance or benchmark claim
  with a reproducible source; avoid unqualified superlatives.

## Pull requests

Keep PRs focused and make sure the markdown lint, link check, and the
consistency scripts pass before opening one.

## Optional: give your agent memory of this repo (with Statewave)

This project dogfoods Statewave. The easiest way to give your assistant a
queryable project brain for this repo is the **Statewave IDE Companion**
extension for **VS Code / Cursor** (publisher `statewavedev`) — install it from
your editor's extensions marketplace. It exposes your workspace, docs, git
state, and structure to Copilot / Cursor / Claude over MCP and **registers the
MCP server for you** (no manual config); it just needs a Statewave server to
talk to (a one-file `docker compose up`). See the
[extension README](https://github.com/smaramwbc/statewave-connectors/blob/main/packages/vscode-extension/README.md).

Prefer to wire it up by hand, or use another MCP client? Run the
[Statewave MCP server](connectors/mcp.md) (`@statewavedev/mcp-server`) directly
and query subject `repo:smaramwbc/statewave-docs`.
