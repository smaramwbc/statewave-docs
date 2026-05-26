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
| **Auditable** | Every assembly call can emit an immutable [state-assembly receipt](receipts.md) — a ULID-addressable record of which memories and episodes influenced the bundle, with a SHA-256 hash of the bytes delivered to the agent. Compliance reviewers can answer "what state did the agent actually see at decision time?" without trusting application logs. |
| **Governable** | Per-memory [sensitivity labels](sensitivity-labels.md) feed a declarative YAML policy engine. Operators express rules like "PII memories cannot be read by marketing tools" once, and `/v1/context` enforces them per call — with the decision recorded into the receipt either way (`log_only` for audit-without-filtering, `enforce` for hard blocking). |
| **Idempotent** | Recompiling the same subject produces no duplicate memories. |
| **Subject-centric** | Everything is organised around subjects (customer, account, workspace). Full lifecycle: ingest → compile → retrieve → inspect → delete. |

---

## Provable today

These claims are backed by the [support-agent context quality eval](https://github.com/smaramwbc/statewave-examples/tree/main/eval-support-agent), which runs 7 tests with 14 binary assertions against a live Statewave instance, the [handoff eval](https://github.com/smaramwbc/statewave-examples/blob/main/eval-support-agent/test_handoff.py) (6 tests, 15 assertions), the [advanced eval](https://github.com/smaramwbc/statewave-examples/blob/main/eval-support-agent/test_support_advanced.py) (10 tests, 26 assertions), and the [support-agent benchmark](https://github.com/smaramwbc/statewave-examples/tree/main/benchmark-support-agent):

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
| Session-aware ranking surfaces active-session content | Advanced eval: the active month-end-update thread appears in context |
| Open/escalated issues surface in context | Advanced eval: escalation + connection-pool details appear for the open issue |
| Task-relevant facts outrank off-topic ones | Advanced eval: billing/gateway facts rank above an unrelated password reset |
| Repeat-issue signal surfaces the prior fix | Advanced eval: a recurring timeout brings back the earlier "restart" resolution |
| Customer health scoring is explainable | Advanced eval: at_risk/watch state, score < 70, named factors (unresolved, repeated, escalations) |
| Health-aware handoff carries risk level | Advanced eval: handoff health_state/score match the health endpoint, with icon + label in notes |
| Handoff health factors stay compact | Advanced eval: at most 3 health factors in the handoff pack |
| Resolution-aware ranking works | Advanced eval: open billing issue is the active issue; resolution history (≥2) present |
| Handoff is compact and deterministic | Advanced eval: ≤4000-token pack; identical requests produce identical notes + score |
| Handoff carries provenance | Advanced eval: handoff provenance includes episode_ids and resolution_ids |
| Proactive health alerts on degradation | Unit tests: webhook fired on healthy→watch, watch→at_risk, healthy→at_risk; no spam on unchanged |
| Health recovery confirmation | Unit tests: `subject.health_improved` fired on at_risk→watch, watch→healthy, at_risk→healthy |
| Support workflow superiority vs naive | Workflow benchmark: Statewave 8/8 vs Naive 2/8 on active-issue, repeat-detection, health, provenance, resolution-ranking |
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

- **Self-hosted storage** — Postgres-only, no external services required. Episodes and compiled memories stay in your infrastructure. Whether content leaves the network during compilation or embedding depends on the provider you configure — see [Privacy & Data Flow](architecture/privacy-and-data-flow.md).
- **No vendor lock-in** — heuristic compiler works without any LLM API key (and is the default). Embeddings and LLM compilation are optional enhancements; the heuristic path runs fully local with zero data egress.
- **Operator-friendly** — Docker Compose, health endpoints, structured logging, OpenTelemetry tracing, configurable via environment variables.
- **Reliable webhook delivery** — persistent queue with retries and dead-letter (v0.5). Proactive health alerts emit `subject.health_degraded` on state transitions.
- **Clean API** — versioned REST, OpenAPI docs, structured error responses with request-ID correlation.
- **Typed SDKs** — Python (sync + async, Pydantic models) and TypeScript (full type definitions), both with proper error handling.
- **Transparent scoring** — the ranking formula is documented, deterministic, and inspectable. No black-box relevance.

---

## Still in progress / not yet proven

| Area | Status |
|------|--------|
| Production scale (>10k subjects, high throughput) | Not load-tested. Single-node only. |
| Multi-tenant isolation | App-layer query scoping; no Postgres RLS yet. Not battle-tested at scale. |
| LLM compiler vs heuristic compiler quality | LLM compiler exists but no comparative eval published. |
| 50-session production-scale benchmark | Not yet run. |

We are honest about these gaps. If any of these are blockers for your use case, Statewave may not be ready for you yet.

---

## Current limitations

- Single-node only (no clustering)
- No built-in auth provider (validates keys you configure, doesn't issue them)
- No streaming (context returned as complete JSON)
- Operator admin console is early — dashboards plus policy and per-tenant config management; no memory editing or advanced ops yet
- Rate limiting is per-IP (distributed/Postgres-backed, but not per-tenant or per-API-key)

---

## Who this is for

- **Teams building AI support agents** that interact with returning customers across sessions
- **Engineering leads** who want structured, measurable context quality instead of "we hope RAG works"
- **Teams that need provenance** — "why did the agent say X?" must be answerable
- **Self-hosted storage requirements** — episodes and memories must stay in your infrastructure (heuristic compiler keeps the entire pipeline local; LLM/embedding choices determine whether content leaves)
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
| Python SDK | `pip install statewave` · [source](https://github.com/smaramwbc/statewave-py) |
| TypeScript SDK | `npm install @statewavedev/sdk` · [source](https://github.com/smaramwbc/statewave-ts) |
