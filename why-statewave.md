# Why Statewave

A technical comparison for teams building AI support agents that need durable, structured memory.

---

## The problem

AI support agents forget. Every session starts from zero. Returning customers re-explain who they are, what plan they're on, what they asked last time. Agents make the same mistakes they made before. Context degrades as conversation history grows.

This isn't a capability gap in the LLM — it's an infrastructure gap. Most AI applications have no memory layer.

---

## Common approaches and their weaknesses

### Stateless prompting

The agent receives only the current message. No history, no identity, no memory.

- ✗ Cannot recognise a returning customer
- ✗ Cannot recall prior issues or preferences
- ✗ Every session starts cold
- ✗ Fails completely for multi-session workflows

### Prompt stuffing (full history replay)

Concatenate the entire conversation history into the prompt.

- ✗ Blows token budgets on long-running subjects (support customers often have 10–50+ sessions)
- ✗ No ranking — irrelevant history competes with critical facts
- ✗ No provenance — you can't trace why the agent said something
- ✗ Cost scales linearly with customer lifetime
- ✗ Context window limits force arbitrary truncation

### Naive vector search / RAG over messages

Embed all messages, retrieve top-k by similarity to the current query.

- ✗ Non-deterministic — same query can return different results depending on index state
- ✗ No structured extraction — "Alice is on the Enterprise plan" is just a substring in a chunk
- ✗ No confidence scoring — all retrieved chunks are treated equally
- ✗ No temporal reasoning — superseded information (old email, resolved issue) has equal weight to current facts
- ✗ No provenance — retrieved chunks aren't traced back to specific interactions
- ✗ Token budget is managed by truncation, not by ranked priority

---

## What Statewave does differently

Statewave is a structured memory runtime. It doesn't store raw text and hope retrieval works — it compiles durable memories from raw events, scores them, and assembles ranked, token-bounded context bundles with full provenance.

### Data lifecycle

```
Episodes (raw events) → Compilation → Memories (typed, scored) → Context assembly → Bundle (prompt-ready)
```

1. **Episodes** — immutable, append-only records of interactions. The raw truth.
2. **Memories** — compiled, typed facts with confidence scores, validity windows, and provenance back to source episodes.
3. **Context bundles** — ranked, token-bounded output with sections (identity facts, procedures, history, recent interactions) ready to inject into any prompt.

### Key technical properties

| Property | What it means |
|----------|--------------|
| **Deterministic** | Same subject + task + budget → same context bundle. No non-determinism from vector-only retrieval. |
| **Token-bounded** | Context assembly respects a configurable token budget. Items are packed by ranked score, not truncated arbitrarily. |
| **Ranked** | Scoring formula: kind priority × recency × task relevance × temporal validity × semantic similarity (when available). |
| **Provenance-traced** | Every memory traces to its source episode IDs. Every context bundle reports which facts, summaries, and episodes were included. |
| **Idempotent** | Recompiling the same subject produces no duplicate memories. |
| **Subject-centric** | Everything is organised around subjects (customer, account, workspace). Full lifecycle: ingest → compile → retrieve → inspect → delete. |

---

## Provable today

These claims are backed by the [support-agent context quality eval](https://github.com/smaramwbc/statewave-examples/tree/main/eval-support-agent), which runs 7 tests with 14 binary assertions against a live Statewave instance:

| Claim | Evidence |
|-------|----------|
| Identity facts persist across sessions | Eval test 1: name, company, plan recalled correctly for a billing task |
| Relevant preferences surface for matching tasks | Eval test 2: integration preferences (Python SDK, webhooks) appear for integration task |
| Issue history surfaces for follow-up tasks | Eval test 3: SSO issue + ticket number appear for follow-up task |
| Token budget is respected | Eval test 4: token estimate ≤ configured budget |
| Identity persists even for unrelated tasks | Eval test 4: identity facts included regardless of task topic |
| Provenance traces facts to source episodes | Eval test 5: bundle contains fact_ids, each fact has source_episode_ids |
| Compilation is idempotent | Eval test 6: recompile produces 0 new memories |
| Memory extraction is reasonable | Eval test 7: 8–30 memories from 8 episodes, ≥3 profile facts |

The eval exits non-zero on failure and is CI-friendly.

### Integration ergonomics

Getting context for a support agent prompt is one SDK call:

```python
from statewave import StatewaveClient

client = StatewaveClient()
context = client.get_context_string("customer-123", "Help with billing question")
# → structured text ready to inject into your system prompt
```

Or the full bundle with provenance:

```python
bundle = client.get_context("customer-123", "Help with billing question")
# bundle.assembled_context → prompt text
# bundle.facts → list of memory objects with source_episode_ids
# bundle.provenance → {"fact_ids": [...], "summary_ids": [...], "episode_ids": [...]}
# bundle.token_estimate → integer
```

---

## Current strengths

- **Self-hosted** — Postgres-only, no external services required. Customer data never leaves your infrastructure.
- **No vendor lock-in** — heuristic compiler works without any LLM API key. Embeddings and LLM compilation are optional enhancements.
- **Operator-friendly** — Docker Compose, health endpoints, structured logging, OpenTelemetry tracing, configurable via environment variables.
- **Clean API** — 8 endpoints, REST, OpenAPI docs, structured error responses with request-ID correlation.
- **Typed SDKs** — Python (sync + async, Pydantic models) and TypeScript (full type definitions), both with proper error handling.
- **Transparent scoring** — the ranking formula is documented, deterministic, and inspectable. No black-box relevance.

---

## Still in progress / not yet proven

| Area | Status |
|------|--------|
| Production scale (>10k subjects, high throughput) | Not load-tested. Single-node only. |
| Multi-tenant isolation | Experimental — header-based extraction, not battle-tested. |
| LLM compiler vs heuristic compiler quality | LLM compiler exists but no comparative eval published. |
| Comparison against Mem0 or similar products | No head-to-head benchmark exists. |
| Dashboard / UI for operators | API-only today. |
| Reliable webhook delivery | Fire-and-forget, no retries. |
| Memory TTL / expiry policies | Not implemented. |
| SDK retry/backoff | Not implemented. |

We are honest about these gaps. If any of these are blockers for your use case, Statewave may not be ready for you yet.

---

## Current limitations

- PostgreSQL required (no alternative backends)
- Single-node only (no clustering)
- No built-in auth provider (validates keys you configure, doesn't issue them)
- No streaming (context returned as complete JSON)
- No UI (API-only)
- Rate limiting is in-memory (single-worker, resets on restart)

---

## Who this is for

- **Teams building AI support agents** that interact with returning customers across sessions
- **Engineering leads** who want structured, measurable context quality instead of "we hope RAG works"
- **Teams that need provenance** — "why did the agent say X?" must be answerable
- **Self-hosted requirements** — customer data cannot leave your infrastructure
- **Small, capable teams** using AI coding tools who want a focused product, not an enterprise platform

## Who this is NOT for

- Teams that need a hosted SaaS (Statewave is self-hosted infrastructure)
- Teams that just need a vector database (use pgvector/Pinecone/Weaviate directly)
- Teams building chatbots with no multi-session requirement
- Teams that need horizontal scaling today (not yet supported)
- Teams looking for a complete agent framework (Statewave is a memory/context layer, not an orchestrator)

---

## Try it

| Resource | Link |
|----------|------|
| Getting started | [getting-started.md](getting-started.md) |
| Product overview | [product.md](product.md) |
| API contract | [api/v1-contract.md](api/v1-contract.md) |
| Support agent example | [statewave-examples/support-agent-python](https://github.com/smaramwbc/statewave-examples/tree/main/support-agent-python) |
| Context quality eval | [statewave-examples/eval-support-agent](https://github.com/smaramwbc/statewave-examples/tree/main/eval-support-agent) |
| Live demo | [statewave-demo.vercel.app](https://statewave-demo.vercel.app) |
| Python SDK | [statewave-py](https://github.com/smaramwbc/statewave-py) |
| TypeScript SDK | [statewave-ts](https://github.com/smaramwbc/statewave-ts) |
