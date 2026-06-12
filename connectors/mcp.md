# Statewave MCP server

The Statewave MCP server exposes Statewave memory to any [MCP](https://modelcontextprotocol.io/)-compatible client — coding assistants, agent frameworks, IDE extensions, custom agents. It is intentionally **vendor-neutral**: there are no client-specific assumptions, no model-provider assumptions, no hosted dependencies.

> **Status:** Available on npm — `@statewavedev/mcp-server`. Ships the canonical tool surface, the `statewave-connectors mcp start` entry point, and **two transports**: **stdio** JSON-RPC 2.0 for local clients and **Streamable HTTP** for remote clients and team/hosted memory. Inspect the tool surface programmatically via `listTools()`. Track progress on the [connectors roadmap](roadmap.md).

## Quickstart (one command)

The fastest path from nothing to a working setup:

```sh
npx -y @statewavedev/connectors-cli quickstart
```

It ensures a Statewave server is running (reuses one that's already healthy, otherwise brings up `api + admin + db` via `docker compose` — published images, debug mode, no API keys), waits for it, configures a client (default **Claude Desktop**), and seeds the current repo's git history + README. Then restart the client and ask it about your project. Tear it down with `quickstart --down`.

Flags: `--client claude|claude-desktop|cursor|vscode|codex`, `--subject`, `--statewave-url` (reuse an existing server and skip docker), `--no-admin`, `--no-seed`. The two steps below are what `quickstart` automates, if you'd rather wire things up by hand.

## Quick setup

`statewave-connectors mcp init <client>` wires a client into Statewave in one step — it writes both the MCP server entry and the instruction block that tells the assistant to call `statewave_get_context` before answering and to persist durable facts. Without that instruction block the tools are present but unused.

```sh
# print the config + instruction blocks (writes nothing)
statewave-connectors mcp init claude

# apply them: merges into existing files, never clobbers other servers
statewave-connectors mcp init cursor --subject repo:acme/platform --write
```

| Client | MCP config | Instruction file |
| --- | --- | --- |
| `claude` (Claude Code) | `.mcp.json` | `CLAUDE.md` |
| `claude-desktop` (Claude Desktop) | `claude_desktop_config.json` | — (paste into custom instructions) |
| `cursor` (Cursor) | `.cursor/mcp.json` | `AGENTS.md` |
| `vscode` (VS Code / Copilot) | `.vscode/mcp.json` | `.github/copilot-instructions.md` |
| `codex` (Codex CLI) | `~/.codex/config.toml` | `AGENTS.md` |

These are all **local stdio** clients. Remote clients (Claude.ai, ChatGPT) connect over HTTP — see [Transports](#transports) below.

`--write` is idempotent (re-running replaces the managed block, it doesn't duplicate it). API keys are never written to a config file — the server reads `STATEWAVE_API_KEY` from its environment. Scope memory with `--subject` (default `repo:<dir>`), point at a server with `--statewave-url`, rename the server id with `--name`.

Then **seed** the subject so the first `get_context` isn't empty:

```sh
# reads local git history + README only — no tokens, no network; dry-run by default
statewave-connectors mcp seed --subject repo:acme/platform --write
```

`mcp seed` maps the repo's recent commits and README to episodes, ingests them, and compiles the subject — so the assistant can answer "what changed and why" from the first question. Re-running is safe (commits dedupe on their sha; the README updates in place). Together the two commands are the whole setup: `mcp init <client> --write && mcp seed --write`.

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

## Transports

The server speaks the same five tools over two transports.

### stdio (local)

The default. The client launches the server as a child process and talks JSON-RPC over stdin/stdout. This is what `mcp init` configures for **Claude Code, Claude Desktop, Cursor, VS Code/Copilot, and Codex** — each runs its own local server process. Nothing listens on a port.

### Streamable HTTP (remote)

A single JSON-RPC endpoint (default `POST /mcp`) that **remote** clients call over HTTP — Claude.ai custom connectors, ChatGPT, hosted agents, or a whole team pointing many agents at one shared memory. Start it with:

```sh
STATEWAVE_URL=http://localhost:8100 statewave-connectors mcp start --http --port 8200
# or the standalone bin:
STATEWAVE_URL=http://localhost:8100 npx -y @statewavedev/mcp-server --http --port 8200
```

Then register your server's public `/mcp` endpoint as a custom/remote MCP connector in the client.

It is **stateless** (no session id issued — simple to scale behind a load balancer) and **request/response only** (no server-initiated SSE stream, so `GET /mcp` is 405; `GET /healthz` is an unauthenticated probe). Security defaults are conservative:

- Binds to `127.0.0.1` — pass `--host 0.0.0.0` to expose it, and only behind TLS.
- Validates the `Origin` header (blocks DNS-rebinding from browsers); restrict with `allowedOrigins`.
- Optional bearer token via `--auth-token` / `STATEWAVE_MCP_AUTH_TOKEN` — **required** before going public.

| Transport | Clients | Setup |
| --- | --- | --- |
| stdio | Claude Code, Claude Desktop, Cursor, VS Code/Copilot, Codex | `mcp init <client>` |
| HTTP | Claude.ai, ChatGPT, hosted/team agents | `mcp start --http` + register the URL as a remote connector |

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
