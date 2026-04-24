# What is Statewave?

Statewave is a **memory runtime for AI agents and AI-powered applications**.

It gives your AI system durable, structured memory — so it can remember what happened, learn from past interactions, and retrieve relevant context at task time.

## Core idea

Most AI applications treat context as disposable. Statewave treats it as infrastructure.

1. **Ingest raw events** (episodes) — conversations, tool calls, decisions, observations
2. **Compile durable memories** — typed, summarised, confidence-scored, with provenance back to source episodes
3. **Retrieve relevant context** — filtered, scored, and token-budgeted for your prompt
4. **Inspect and delete by subject** — full timeline visibility and GDPR-style erasure

Everything is organised around **subjects** — a user, account, workspace, repo, ticket, or agent.

## What Statewave is

- A self-hosted API server you run alongside your application
- A structured memory store backed by Postgres + pgvector
- A context assembly engine that returns prompt-ready bundles with token estimates
- A provenance system that traces every memory back to its source episodes
- Framework-neutral — works with any AI stack, any language

## What Statewave is not

- Not a chatbot or agent framework
- Not a vector database (it uses one internally, but that's an implementation detail)
- Not a RAG pipeline (retrieval is one capability, not the whole product)
- Not an SDK wrapper around an LLM provider
- Not a hosted SaaS (you run it yourself)

## Best current use cases

- **Support agents** that remember customer history across sessions
- **Coding agents** that accumulate project knowledge over time
- **Workflow automation** that needs to recall decisions and outcomes
- **Any AI application** where "what happened before" matters for "what to do next"

## Current limitations

Statewave is in active early development (v0.4.x). Current limitations include:

- **Single-node only** — no clustering or horizontal scaling yet
- **Postgres required** — no alternative storage backends
- **Memory compilation** — heuristic compiler works well for structured data; LLM compiler requires an OpenAI API key
- **No built-in auth provider** — Statewave validates API keys you configure, but doesn't issue them
- **No streaming** — context responses are returned as complete JSON
- **No UI** — API-only; inspect via endpoints or direct DB access

## API surface

| Endpoint | Purpose |
|---|---|
| `POST /v1/episodes` | Ingest a single episode |
| `POST /v1/episodes/batch` | Ingest up to 100 episodes |
| `POST /v1/memories/compile` | Compile memories from episodes |
| `GET /v1/memories/search` | Search memories by query |
| `POST /v1/context` | Assemble a context bundle |
| `GET /v1/timeline` | View subject timeline |
| `GET /v1/subjects` | List subjects with counts |
| `DELETE /v1/subjects/{id}` | Delete all data for a subject |

## SDKs

- **Python**: [`statewave-py`](https://github.com/smaramwbc/statewave-py) — sync and async clients, Pydantic models
- **TypeScript**: [`statewave-ts`](https://github.com/smaramwbc/statewave-ts) — fetch-based client, full type definitions

## Getting started

See the [getting started guide](getting-started.md) for setup instructions, or jump to [examples](https://github.com/smaramwbc/statewave-examples).
