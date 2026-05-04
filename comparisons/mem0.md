# Statewave vs Mem0

> **TL;DR** — Mem0 is a managed memory product with both a hosted SaaS ("Mem0 Platform") and an open-source self-hosted option, focused on personalization for AI assistants. Statewave is a self-hosted-only structured memory runtime focused on deterministic, provenance-traced context for engineering teams that need eval-driven memory. Pick Mem0 if you want a hosted stack with SOC 2 controls and minimal ops; pick Statewave if your data must stay in your infrastructure and you want explainable, reproducible retrieval.

---

## What Mem0 is

Per Mem0's docs ([mem0.ai/overview](https://docs.mem0.ai/overview)), Mem0 is positioned as **"the memory engine for AI"** — a managed service that runs "the vector store, graph services, and rerankers" so you don't have to. It exposes **"add, search, update, and delete workflows"** and persists memory across users, agents, and sessions to "cut prompt bloat and repeat questions."

Two product surfaces:

- **Mem0 Platform** — fully managed SaaS. Mem0 advertises **"SOC 2, audit logs, and workspace governance ship by default."**
- **Mem0 OSS** — the open-source library you can self-host.

Internally, Mem0 combines vector search, a graph layer, and a reranker; the docs don't break down which is primary or how the layers compose. Memory types are referenced as "user, agent, and session memory" but the public overview doesn't formalise an episodic / semantic / procedural taxonomy.

## What Statewave is

Statewave is a **memory runtime** — a single self-hosted service that records raw events as immutable episodes, compiles them into typed memories (`profile_fact`, `episode_summary`, `procedure`, `artifact_ref`) with confidence scores and validity windows, and assembles ranked, token-bounded context bundles with provenance back to source episodes. Postgres + pgvector is the only storage dependency. No managed plane.

The retrieval contract is deliberately deterministic: same `(subject_id, task, max_tokens)` returns the same bundle. That property is what makes Statewave evaluable — you can write a regression test that retrieval still returns the right facts after a code change. See [architecture/ranking.md](../architecture/ranking.md).

---

## Side-by-side

| | **Mem0** | **Statewave** |
|---|---|---|
| **Deployment** | Hosted SaaS (Mem0 Platform) + self-hosted (Mem0 OSS) | Self-hosted only. Postgres + your container platform. |
| **Retrieval model** | Vector + graph + reranker stack (managed under the hood). Composition not exposed in public docs. | Typed-memory ranking: kind priority × recency × task relevance × temporal validity × semantic similarity. Formula and signals documented per memory in the response. |
| **Determinism** | Not advertised. Reranker behaviour is part of the managed stack. | Deterministic by design — same inputs return the same context bundle. Documented in [why-statewave.md](../why-statewave.md). |
| **Memory types** | "User / agent / session memory" (per the public overview). | `profile_fact`, `episode_summary`, `procedure`, `artifact_ref` enums in the response model. |
| **Provenance** | Not surfaced in the public overview. | Every memory returns `source_episode_ids`. Every episode is immutable and timestamped. Citation chain is queryable. |
| **Token-bounded context** | Not advertised as a contract. | First-class: `max_tokens` is part of the context request; bundle reports `token_estimate` against budget. |
| **Compliance** | "SOC 2, audit logs, workspace governance" advertised on the platform tier. | Customer-side — you self-host, you own the controls. No managed plane to audit. |
| **Pricing** | Tiered platform plans + free OSS. Refer to [mem0.ai pricing](https://mem0.ai/pricing). | OSS (AGPLv3) free; commercial license for proprietary use. See [LICENSING.md](https://github.com/smaramwbc/statewave/blob/main/LICENSING.md). |
| **API surface** | `add`, `search`, `update`, `delete` per Mem0's overview. | `POST /v1/episodes`, `POST /v1/memories/compile`, `POST /v1/context`, `GET /v1/timeline`, `DELETE /v1/subjects/{id}`. See [api/v1-contract.md](../api/v1-contract.md). |
| **Compilation** | Implicit — the platform manages extraction. | Explicit `/v1/memories/compile` step; pluggable heuristic or LLM compiler. See [architecture/compiler-modes.md](../architecture/compiler-modes.md). |

---

## When Mem0 is the right call

- You want a **managed plane** and don't want to operate Postgres + a runtime yourself.
- You need **SOC 2-ready memory** out of the box and would otherwise have to layer compliance controls onto your own stack.
- Your team values speed-to-personalization over reproducibility — typical chat-assistant use cases where "remember the user said X" is the goal and the exact ranking math doesn't matter.
- You're already inside the Mem0 Platform's hosting region requirements.

## When Statewave is the right call

- **Self-hosted is non-negotiable.** Your data residency, vendor restriction, or compliance posture rules out a managed plane. Statewave runs entirely inside your infrastructure (heuristic compilation has zero data egress; LLM/embedding choices control the rest — see [privacy-and-data-flow.md](../architecture/privacy-and-data-flow.md)).
- **You want eval-driven memory.** Deterministic retrieval means you can regression-test context quality. Statewave ships a [docs-grounded eval](https://github.com/smaramwbc/statewave-examples/tree/main/eval-docs-support) and [support-agent benchmark](https://github.com/smaramwbc/statewave-examples/tree/main/benchmark-support-agent) as runnable examples; the same harness pattern works for your own subject schemes.
- **Provenance is load-bearing.** When a customer asks "why did the agent say X about my account?", you need to trace back to the conversation that produced the fact. Statewave's `source_episode_ids` chain makes that a query, not a forensic exercise.
- **Token-bounded retrieval is part of the contract.** When prompt budget matters (cost, latency, context-window pressure), Statewave packs by ranked score against an explicit `max_tokens` instead of leaving truncation to the caller.

---

## Migration recipe

Mem0's primary primitives are *user memories* indexed by `user_id` plus messages. Statewave's primary primitive is the *subject* — an entity any episode can be written to.

### Conceptual mapping

| Mem0 concept | Statewave concept |
|---|---|
| `user_id` (Mem0 user-scoped memory) | `subject_id` (Statewave subject — typically `user-<id>`, see [subject-design.md](../subject-design.md)) |
| `agent_id` | A separate subject per agent if you want shared agent memory across users; otherwise carry as episode metadata. |
| `session_id` | `metadata.session_id` on the episode. Statewave does not split sessions into separate subjects — sessions are spans inside a subject. |
| `add(messages, user_id=...)` | `POST /v1/episodes` with `subject_id`, `payload.messages`, `source="chat"`, `type="conversation"` |
| `search(query, user_id=...)` | `POST /v1/context` with `subject_id`, `task=query`, `max_tokens` |
| Mem0-extracted facts | Statewave-compiled memories — call `/v1/memories/compile` after batch ingest, or rely on automatic compile after each episode |
| Memory metadata | Statewave `metadata_` JSONB on each row (free-form) |

### Code sketch (Python SDK)

```python
# Before — Mem0
from mem0 import Memory
m = Memory()
m.add([{"role": "user", "content": "I prefer Python with type hints"}], user_id="alice")
results = m.search("what does alice prefer?", user_id="alice")

# After — Statewave
from statewave import StatewaveClient
sw = StatewaveClient("https://your-statewave.example.com", api_key=...)

# Ingest as an episode
sw.add_episode(
    subject_id="user-alice",
    source="chat",
    type="conversation",
    payload={"messages": [{"role": "user", "content": "I prefer Python with type hints"}]},
)

# Retrieve as a context bundle
bundle = sw.get_context(
    subject_id="user-alice",
    task="what does alice prefer?",
    max_tokens=600,
)
# bundle.assembled_context  → drop into your prompt
# bundle.facts              → list of compiled memories
# bundle.provenance         → fact_ids + episode_ids cited
```

### Bulk migration

If you already have a Mem0 corpus to import:

1. Export Mem0 memories per user (refer to Mem0's export/dump tooling).
2. For each Mem0 memory, write a Statewave episode with the original text in the payload and Mem0's metadata in the episode's `metadata_` field. Carry the original Mem0 memory id in `provenance.original_id` so you can reverse-trace if needed.
3. Run `POST /v1/memories/compile` once per migrated subject. Compilation is idempotent.
4. Spot-check retrieval on representative queries before flipping the read path.

---

## Honest gaps

Statewave does not match Mem0 on every axis. If any of these are blockers, factor them in:

- **No hosted SaaS.** You run it. Cost of ops is yours.
- **No managed compliance plane.** SOC 2 / HIPAA / etc. are your responsibility. Statewave gives you the technical controls (delete-by-subject, no required outbound calls in heuristic mode); you supply the audit programme.
- **No graph-of-entities first-class concept.** Statewave is typed-memory, not a knowledge graph. If you need relational reasoning across entities (e.g. "find every account Sarah is connected to"), you'd build that on top.
- **Single-node only today.** Horizontal scaling is roadmap, not shipped. Statewave is honest about this — see the *Current limitations* section in [why-statewave.md](../why-statewave.md).

---

## References

- Mem0 overview — [docs.mem0.ai/overview](https://docs.mem0.ai/overview)
- Mem0 OSS on GitHub — [github.com/mem0ai/mem0](https://github.com/mem0ai/mem0)
- Statewave architecture — [architecture/overview.md](../architecture/overview.md)
- Statewave ranking model — [architecture/ranking.md](../architecture/ranking.md)
- Statewave subject design — [subject-design.md](../subject-design.md)
- Why Statewave (the broader framing) — [why-statewave.md](../why-statewave.md)

*Comparison drafted against Mem0 documentation as of May 2026. Verify pricing, feature flags, and license terms against the live Mem0 docs before procurement decisions — these things move.*
