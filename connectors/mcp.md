# Statewave MCP server

The Statewave MCP server exposes Statewave memory to any [MCP](https://modelcontextprotocol.io/)-compatible client — coding assistants, agent frameworks, IDE extensions, custom agents. It is intentionally **vendor-neutral**: there are no client-specific assumptions, no model-provider assumptions, no hosted dependencies.

> **Status:** Available on npm — `@statewavedev/mcp-server`. Ships the canonical tool surface, the `statewave-connectors mcp start` entry point, and the **stdio** JSON-RPC 2.0 transport; an HTTP transport is a planned follow-up. Inspect the tool surface programmatically via `listTools()`. Track progress on the [connectors roadmap](roadmap.md).

## Why this exists

Most "agent memory" implementations are limited to whatever the host application keeps in scrollback. The MCP server lets any client speak the same memory protocol, so:

- A coding agent can ask for **repo memory** while you work on a PR.
- An assistant tool can ask for **customer memory** before answering a support question.
- A custom agent loop can ask for **decision memory** before suggesting an architectural change.
- Any of these can also write episodes back through the same protocol.

The agent never sees raw chat history or a fresh RAG dump. It sees compact, ranked, token-bounded context for the subject it cares about — assembled by Statewave.

## Tools exposed

The server registers exactly five tools — the smallest set that covers ingestion, recall, timeline, and compilation.

### `statewave_ingest_episode`

Ingest a single normalized [episode](concepts.md) into Statewave. Episodes are deduplicated on `idempotency_key`. Useful when an agent has just learned something and wants to record it (e.g. "the user confirmed they're on plan tier B").

### `statewave_search_memories`

Search compiled memories — not raw episodes — by free-text query, optionally scoped to a subject. Returns ranked memories. This is the right tool when an agent wants to find *what's known* about something.

### `statewave_get_context`

Retrieve compact, ranked context for a subject. This is the **default** tool to call inside an agent prompt instead of stuffing raw chat history. The agent specifies the subject (and optionally a focusing query), and Statewave returns a compact context bundle bounded by `max_tokens`.

### `statewave_get_timeline`

Retrieve a chronological timeline of episodes for a subject — useful for audit, change-log, and replay use cases. Filterable by `since`, `until`, and event `kinds`.

### `statewave_compile_subject`

Trigger compilation for a subject so newly-ingested episodes turn into durable memories. Most deployments compile automatically; this tool is for the case where an agent wants to "make sure my recent ingestion is queryable" before retrieving.

## Vendor neutrality

The Statewave MCP server makes **no** assumptions about:

- Which IDE or assistant is connecting to it
- Which model provider is in use
- Whether you're running locally, on a VPS, or in your enterprise cloud

It is a process you launch (`statewave-connectors mcp start`) and a tool surface you call. Configure it the same way you'd configure any other MCP server in your client — point the client at the launcher (stdio) or at the HTTP endpoint when transport lands.

## What this is **not**

- **Not** a hosted dependency. It runs where you run it.
- **Not** locked to one client family — Copilot, Claude, Cursor, custom agents all speak the same protocol.
- **Not** a replacement for ingestion. You still need at least one connector ([GitHub](github.md), [Markdown](markdown.md), …) so there's something to retrieve. The MCP server is the **read path** for agents — and a thin write path via `statewave_ingest_episode`.

## See also

- [Quickstart](quickstart.md) — start the server and call a tool
- [Concepts](concepts.md) — what episodes, subjects, and context bundles actually are
- [API v1 Contract](../api/v1-contract.md) — the underlying HTTP API the MCP server adapts
- [Architecture Overview](../architecture/overview.md) — record → compile → context → govern
