# Statewave vs Letta

> **TL;DR** — Letta (the company that grew out of the [MemGPT](https://arxiv.org/abs/2310.08560) research project) is a stateful-agent runtime: an LLM-as-OS architecture where the model manages its own memory, context, and reasoning loop, exposed via a hosted platform and a desktop "Letta Code" app. Statewave is a memory layer that any agent stack can call — it does not run the agent loop. Pick Letta if you want a complete agent runtime out of the box; pick Statewave if you've already built (or chosen) your agent orchestration and just need durable, ranked context that survives sessions.

---

## What Letta is

From [docs.letta.com](https://docs.letta.com/concepts/letta/) and [letta.com/blog](https://www.letta.com/blog/letta-v1-agent), Letta positions itself for **"stateful agents that remember, learn, and improve over time."** Two product surfaces:

- **Letta API Platform** — REST + Python/TypeScript SDKs for building agents that retain memory across sessions.
- **Letta Code** — a desktop app/runtime with **MemFS, "our latest memory system which is git-tracked"** for personal-use deeply personalised agents.

Letta is the continuation of [MemGPT](https://research.memgpt.ai/), the academic project that pioneered the OS-style virtual-memory analogy for LLMs. The Letta team has since rearchitected the agent loop around modern reasoning-model patterns (their [v1 architecture post](https://www.letta.com/blog/letta-v1-agent) explains the move from MemGPT's tool-call-everything pattern to a hybrid loop suited for GPT-5-class models).

The crucial framing: Letta is an **agent runtime**, not just a memory store. Memory is one component of a complete loop that also handles tool calling, context management, and reasoning steps. You write your agent inside Letta's runtime; the runtime orchestrates everything.

## What Statewave is

Statewave is a **memory layer** — an HTTP API that records episodes, compiles them into typed memories, and returns ranked, token-bounded context bundles. Statewave does not orchestrate agents. It does not call your LLM. It does not manage tool calls. It exposes one job — *give me the right context for this subject and this task* — and tries to do it well, deterministically, with provenance.

Your agent code (whether built with the Vercel AI SDK, OpenAI's Agents SDK, LangGraph, CrewAI, or your own loop) calls Statewave for context, then calls whatever LLM it likes. See [architecture/overview.md](../architecture/overview.md).

---

## Side-by-side

| | **Letta** | **Statewave** |
|---|---|---|
| **What it is** | Stateful agent runtime (memory + reasoning loop + tools) | Memory runtime (memory only) |
| **Owns the agent loop?** | Yes — agents run inside Letta's runtime. | No — your agent code stays where it is. |
| **Memory model** | MemFS (git-tracked memory in Letta Code); core / archival / recall blocks in the API platform's MemGPT lineage | Episodes (immutable raw events) → Memories (typed, scored, with provenance) → Context bundles (ranked, token-bounded) |
| **Deployment** | Hosted API platform + Letta Code desktop runtime + open-source server ([github.com/letta-ai/letta](https://github.com/letta-ai/letta)) | Self-hosted only |
| **Provider lock-in** | Provider-neutral via the underlying open-source project; the Letta Code app advertises "deployment that works across every model provider" | Provider-neutral via LiteLLM (100+ providers) |
| **Determinism** | Not advertised as a contract; the agent loop's behaviour is governed by the model and tool calls | Deterministic context bundle for `(subject, task, budget)` triples |
| **Tool use, reasoning loops, agent state machines** | First-class | Out of scope — your orchestrator handles this |
| **Pricing** | Platform tiers + open-source server. Refer to [letta.com pricing](https://www.letta.com/) | OSS (AGPLv3) + commercial license — see [LICENSING.md](https://github.com/smaramwbc/statewave/blob/main/LICENSING.md) |
| **Best fit** | Teams without an agent stack who want a complete one | Teams with an agent stack who want a memory layer |

The two products **don't usually compete head-to-head** — they sit at different layers. The honest comparison is "do I want to adopt a runtime, or do I want a memory service my existing runtime can call?"

---

## When Letta is the right call

- You're starting from a blank page on agent infrastructure and want a runtime that handles memory, tool calls, and reasoning loops together.
- You like the LLM-as-OS architectural framing and want an opinionated, integrated take on how stateful agents should work.
- You're building a personal-use agent and want the Letta Code app's git-backed memory and skills system.
- You'd rather have one well-integrated layer than compose your own stack from a memory service + an orchestration framework.
- Your team is comfortable adopting Letta's mental model around memory blocks (core / archival / recall), which differs from typed-fact storage.

## When Statewave is the right call

- **You already have an agent loop** — built on the Vercel AI SDK, OpenAI Agents SDK, LangGraph, CrewAI, your own Express handler, anything else — and don't want to rewrite it. You just want context that survives sessions.
- **You want memory portable across agent stacks.** Statewave's API is HTTP — your support agent, your coding agent, your sales copilot can all call the same memory layer regardless of how each is implemented.
- **You need eval-driven memory.** Deterministic retrieval is a regression-testable surface. Statewave's [docs eval](https://github.com/smaramwbc/statewave-examples/tree/main/eval-docs-support) and [support-agent benchmark](https://github.com/smaramwbc/statewave-examples/tree/main/benchmark-support-agent) show the harness; the same shape works for your domain.
- **Provenance to source events matters.** When the agent says something about a customer, `source_episode_ids` traces back to the exact episodes that produced the fact. Letta's memory blocks are LLM-managed; Statewave's compiled memories are records.
- **You want a small, focused runtime.** One Postgres + one container. No agent loop to operate, no skills system, no model-specific quirks.

---

## Migration recipe — from Letta to Statewave

If you've adopted Letta and want to keep its agent loop while moving memory to Statewave, the migration is *partial* — you don't replace Letta wholesale, you re-route memory operations.

### Conceptual mapping

| Letta concept | Statewave concept |
|---|---|
| Agent (a Letta-managed entity) | Subject (an entity Statewave's memory is *about* — usually `user-<id>` or `account-<id>`, not the agent itself; see [subject-design.md](../subject-design.md)) |
| Core memory block | Compiled `profile_fact` memories on the relevant subject |
| Archival memory | Episodes (immutable, append-only) on the subject |
| Recall memory | Context bundles returned by `/v1/context` |
| MemFS file (in Letta Code) | A `subject_id` namespace + episodes/memories under it |
| Tool call: `archival_memory_insert` | `POST /v1/episodes` |
| Tool call: `archival_memory_search` | `POST /v1/context` |

### Code sketch

If your Letta agent uses the standard MemGPT memory tools, replace them with HTTP calls to Statewave:

```python
# Inside your agent's tool definitions:

def remember(content: str, subject_id: str) -> dict:
    """Tool the agent calls to persist something across sessions."""
    return statewave.add_episode(
        subject_id=subject_id,
        source="agent",
        type="observation",
        payload={"content": content},
    )

def recall(query: str, subject_id: str, budget: int = 600) -> str:
    """Tool the agent calls to fetch relevant context."""
    bundle = statewave.get_context(
        subject_id=subject_id,
        task=query,
        max_tokens=budget,
    )
    return bundle.assembled_context  # ready-to-prompt text
```

The agent's reasoning loop, tool routing, and conversation handling stay in Letta. Only memory crosses to Statewave.

### Full-replacement sketch

If you're replacing Letta entirely (moving the agent loop to a different framework AND moving memory to Statewave), separate the work:

1. Stand up Statewave alongside Letta. Run them in parallel.
2. For each Letta agent, identify the *subject* (the persistent entity its memory is about — typically the user, account, or workspace).
3. Bulk-export Letta's archival memory + core memory blocks; ingest as episodes on the corresponding subject. Tag with `provenance.migrated_from = "letta"` so you can audit.
4. Run `/v1/memories/compile` per migrated subject.
5. Cut your agent's memory tool calls over to Statewave (sketch above).
6. Cut the agent loop itself to your new framework (LangGraph / Agents SDK / etc.) on a separate timeline. Don't try to do both at once.

---

## Honest gaps

- **Statewave doesn't run agents.** If you want one product that does memory + tools + loops, that's not us. Letta does this; we don't.
- **No MemFS-equivalent for personal-use desktop agents.** Letta Code's git-backed local memory is a different product shape. Statewave is server-side.
- **No skills system.** Letta has a skills concept for reusable agent capabilities. That's an agent-runtime feature; Statewave is a memory layer.
- **Different mental model.** Letta operators think in *agents*; Statewave operators think in *subjects*. Teams already fluent in MemGPT-style memory management have non-trivial cognitive cost when switching.

---

## References

- Letta documentation — [docs.letta.com](https://docs.letta.com/)
- Letta v1 agent loop redesign — [letta.com/blog/letta-v1-agent](https://www.letta.com/blog/letta-v1-agent)
- Stateful agents framing — [letta.com/blog/stateful-agents](https://www.letta.com/blog/stateful-agents)
- Letta open-source server — [github.com/letta-ai/letta](https://github.com/letta-ai/letta)
- Original MemGPT paper — [arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560)
- Statewave architecture — [architecture/overview.md](../architecture/overview.md)
- Why Statewave — [why-statewave.md](../why-statewave.md)
- Statewave + LangChain / agent-framework integration — [api/v1-contract.md](../api/v1-contract.md)

*Comparison drafted against Letta documentation as of May 2026. Verify license terms, hosted-platform availability, and current architecture against [docs.letta.com](https://docs.letta.com/) before procurement decisions.*
