# Architecture Overview

Statewave is a **Memory OS** — a trusted context runtime for AI agents and applications.

## Core loop

```
RECORD → COMPILE → CONTEXT → GOVERN
```

1. **Record** — immutable episodes capture raw interaction truth
2. **Compile** — heuristic/LLM compilers derive typed memories with provenance
3. **Context** — assembly service builds token-bounded, deterministic context bundles
4. **Govern** — provenance inspection, delete-by-subject, retention controls

## Component architecture

```
┌──────────────────────────────────────────┐
│              FastAPI Server               │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Episodes  │  │ Memories │  │Context │ │
│  │  Route    │  │  Route   │  │ Route  │ │
│  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       │              │            │       │
│  ┌────┴──────────────┴────────────┴────┐ │
│  │           Service Layer             │ │
│  │  Compiler · ContextAssembler        │ │
│  └────┬──────────────┬────────────┬────┘ │
│       │              │            │       │
│  ┌────┴──────────────┴────────────┴────┐ │
│  │        Repository / DB Layer        │ │
│  └─────────────────┬──────────────────┘  │
└────────────────────┼─────────────────────┘
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
- **Local-first** — `docker compose up` gets you running
- **Framework-neutral** — no AI framework coupling in core
