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

These claims are backed by the [support-agent context quality eval](https://github.com/smaramwbc/statewave-examples/tree/main/eval-support-agent), which runs 7 tests with 14 binary assertions against a live Statewave instance, the [handoff eval](https://github.com/smaramwbc/statewave-examples/blob/main/eval-support-agent/eval_handoff.py) (7 tests, 16 assertions), the [advanced eval](https://github.com/smaramwbc/statewave-examples/blob/main/eval-support-agent/eval_support_advanced.py) (7 tests, 24 assertions), and the [support-agent benchmark](https://github.com/smaramwbc/statewave-examples/tree/main/benchmark-support-agent):

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
| Session-aware ranking boosts active session | Advanced eval test 1: active session content outranks unrelated resolved sessions |
| Repeat-issue detection surfaces prior resolutions | Advanced eval test 2: recurring problem triggers prior fix visibility |
| Customer health scoring is explainable | Advanced eval test 3: at-risk state with named factors for open + recurring issues |
| Health-aware handoff shows risk level | Advanced eval test 4: health state, score, and factors appear in handoff pack |
| Resolution-aware ranking works | Advanced eval test 5: open issues prioritized, resolved deprioritized |
| Handoff is compact and deterministic | Advanced eval test 6: token budget respected, identical requests produce identical output |
| Proactive health alerts on degradation | Unit tests: webhook fired on healthy→watch, watch→at_risk, healthy→at_risk; no spam on unchanged |
| Health recovery confirmation | Unit tests: `subject.health_improved` fired on at_risk→watch, watch→healthy, at_risk→healthy |
| Support workflow superiority vs naive | Workflow benchmark: Statewave 9/9 vs Naive 2/9 on active-issue, repeat-detection, health, provenance, resolution-ranking |
| SLA tracking with breach detection | Unit tests: first-response time, resolution time, breach flags, custom thresholds; integrated into health scoring and handoff |
| SLA breaches degrade health score | Unit tests: sla_resolution_breaches and slow_first_response signals penalize health deterministically |
| SLA context in handoff packs | Unit tests: breach flags and open-issue age appear in handoff when relevant, absent when clean |

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
- **Reliable webhook delivery** — persistent queue with retries and dead-letter (v0.5). Proactive health alerts emit `subject.health_degraded` on state transitions.
- **Clean API** — 8 endpoints, REST, OpenAPI docs, structured error responses with request-ID correlation.
- **Typed SDKs** — Python (sync + async, Pydantic models) and TypeScript (full type definitions), both with proper error handling.
- **Transparent scoring** — the ranking formula is documented, deterministic, and inspectable. No black-box relevance.

---

## Still in progress / not yet proven

| Area | Status |
|------|--------|
| Production scale (>10k subjects, high throughput) | Not load-tested. Single-node only. |
| Multi-tenant isolation | App-layer query scoping (v0.5). Not battle-tested at scale. |
| LLM compiler vs heuristic compiler quality | LLM compiler exists but no comparative eval published. |
| Comparison against Mem0 or similar products | No head-to-head benchmark against external products. Internal [benchmark](https://github.com/smaramwbc/statewave-examples/tree/main/benchmark-support-agent) compares Statewave vs history stuffing vs naive RAG. |
| Dashboard / UI for operators | API-only today. |
| Memory TTL / expiry policies | Not implemented. |
| Webhook filters (subscribe to specific event types) | Not yet — all events fire to one URL. |
| 50-session production-scale benchmark | Not yet run. |

We are honest about these gaps. If any of these are blockers for your use case, Statewave may not be ready for you yet.

---

## Current limitations

- PostgreSQL required (no alternative backends)
- Single-node only (no clustering)
- No built-in auth provider (validates keys you configure, doesn't issue them)
- No streaming (context returned as complete JSON)
- No UI (API-only)
- Rate limiting is per-IP (distributed/Postgres-backed, but not per-tenant or per-API-key)

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
| Live demo | Embedded chat widget on [statewave.ai](https://statewave.ai) |
| Python SDK | [statewave-py](https://github.com/smaramwbc/statewave-py) |
| TypeScript SDK | [statewave-ts](https://github.com/smaramwbc/statewave-ts) |
