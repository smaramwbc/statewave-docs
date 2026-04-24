# Architecture Overview

Statewave is a **Memory OS** — a trusted context runtime for AI agents and applications.

## Core loop

```
RECORD → COMPILE → CONTEXT → GOVERN
```

1. **Record** — immutable episodes capture raw interaction truth
2. **Compile** — pluggable compilers (heuristic or LLM) derive typed memories with provenance
3. **Context** — assembly service builds ranked, token-bounded, deterministic context bundles
4. **Govern** — provenance inspection, delete-by-subject, structured error reporting

## Component architecture

```
┌──────────────────────────────────────────────┐
│               FastAPI Server                  │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Episodes  │  │ Memories │  │  Context   │ │
│  │  Route    │  │  Route   │  │   Route    │ │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘ │
│       │              │              │         │
│  ┌────┴──────────────┴──────────────┴──────┐ │
│  │            Service Layer                │ │
│  │  Compiler (pluggable) · ContextAssembler│ │
│  │  (ranked, token-bounded)               │ │
│  └────┬──────────────┬──────────────┬──────┘ │
│       │              │              │         │
│  ┌────┴──────────────┴──────────────┴──────┐ │
│  │         Repository / DB Layer           │ │
│  └──────────────────┬─────────────────────┘  │
│                     │                         │
│  ┌──────────────────┴──────────────────────┐ │
│  │  Middleware: RequestID · CORS · Errors   │ │
│  └─────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────┘
                       │
                ┌──────┴──────┐
                │  PostgreSQL  │
                │  + pgvector  │
                └─────────────┘
```

## Key design decisions

- **Thin routes, strong services** — API handlers delegate to service functions
- **Raw truth first** — episodes are append-only, never mutated
- **Provenance everywhere** — every memory links back to source episodes
- **Idempotent compilation** — recompiling is safe and produces no duplicates
- **Token-bounded context** — context bundles respect configurable token budgets
- **Structured errors** — consistent `{error: {code, message, details, request_id}}` shape
- **Local-first** — `docker compose up` gets you running
- **Framework-neutral** — no AI framework coupling in core

## v0.2 additions

- Pluggable `BaseCompiler` interface for swappable compilation backends
- Ranked retrieval: kind priority × recency × task-keyword relevance
- Request ID middleware for log correlation
- Health endpoints (`/healthz`, `/readyz`)
- SDKs with typed exceptions (Python + TypeScript, both v0.2.0)
