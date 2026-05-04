# Statewave vs LangChain / LangGraph Memory

> **TL;DR** — LangChain's modern memory story is **LangGraph persistence**: per-thread `checkpointer`s persist graph state, and a separate `Store` interface holds key-value memory across threads with optional semantic search via embeddings. Both are deliberately low-level primitives — ranking, scoring, token-budgeting, and provenance are left to the developer. Statewave is the opposite tradeoff: a higher-level memory runtime that ships those decisions baked in, deterministically. Pick LangGraph if your agent loop is already there and you want primitives you control end-to-end; pick Statewave if you want ranked, provenance-traced context bundles without writing them yourself.

---

## What LangGraph persistence is

From [docs.langchain.com](https://docs.langchain.com/oss/python/langgraph/persistence), LangGraph splits persistence into two layers:

### Per-thread state — `Checkpointer`

> *"When you compile a graph with a checkpointer, a snapshot of the graph state is saved at every step of execution, organised into threads."*

Each checkpoint captures full state channel values, pending node writes, source/step metadata, and a `parent_config` pointer to the prior checkpoint. A `thread_id` is mandatory for persistence and resumption.

Implementations:

- `InMemorySaver` (development)
- `SqliteSaver` / `AsyncSqliteSaver` (via `langgraph-checkpoint-sqlite`)
- `PostgresSaver` / `AsyncPostgresSaver` (production)
- `CosmosDBSaver` (Azure)

### Cross-thread memory — `Store`

> *"What if we want to retain some information across threads?"*

The `Store` interface is namespaced by tuple (e.g. `(user_id, "memories")`):

- `store.put(namespace, key, value)` — write
- `store.search(namespace, query=...)` — read, with optional **"semantic search using embeddings (requires `index` configuration with embedding provider)."**

You configure which fields get embedded via the `fields` parameter, pass a `limit` on search, and manage the lifecycle yourself.

### What LangGraph deliberately doesn't do

> *"You can control which parts of your memories get embedded by configuring the `fields` parameter."*

Per LangGraph's docs:

- **No automatic ranking / scoring pipeline.** Retrieval is `store.search()` — you pick `limit`, you compose results, you handle relevance trade-offs.
- **No token-budgeting.** What fits in your prompt is your responsibility.
- **Limited automatic provenance.** Each memory `Item` has `created_at`, `updated_at`, `key`, `namespace`. There's **no automatic lineage tracking** of which conversation turn or LLM reasoning produced the memory; the docs are explicit that *"users must implement custom provenance logic in node functions."*

This is a deliberate design — LangGraph wants to be a substrate, not an opinionated runtime. The trade-off is that "memory that works well across multi-session usage" is a thing you build, not a thing you import.

## What Statewave is

Statewave is a memory runtime with the opinions baked in:

- **Ranking is a first-class output.** Every memory in a context bundle has been scored against the task and packed against a `max_tokens` budget. Scoring formula is documented in [architecture/ranking.md](../architecture/ranking.md).
- **Provenance is not optional.** Every memory carries `source_episode_ids`. Every episode carries timestamps and metadata. Citation chains are queryable.
- **Determinism is the contract.** Same `(subject_id, task, max_tokens)` returns the same bundle. That's what makes retrieval testable.
- **Compilation is explicit.** Episodes (raw events) and memories (compiled facts) are different things; `/v1/memories/compile` is the boundary. No magic auto-extraction in `put()`.

LangGraph: **substrate**. Statewave: **runtime that opinionated-up the substrate.**

The two compose well. A LangGraph agent can call Statewave for cross-session memory while keeping its checkpointer for in-graph state.

---

## Side-by-side

| | **LangGraph persistence** | **Statewave** |
|---|---|---|
| **Primary scope** | Per-thread state + cross-thread KV | Cross-session typed memory |
| **Thread state** | Yes — `Checkpointer` saves full graph state per step | Out of scope — Statewave has no graph; thread/session is metadata on episodes |
| **Cross-thread memory** | Yes — `Store` interface, namespaced KV with optional embedding search | Yes — subjects with episodes + compiled memories + ranked retrieval |
| **Ranking** | Not built-in — `store.search()` returns results, you order/score them | First-class: kind priority × recency × task relevance × temporal validity × semantic similarity |
| **Token budgeting** | Not built-in — you slice results to fit your prompt | First-class: `max_tokens` parameter on every context request |
| **Provenance** | Not built-in — implement in node functions | First-class: `source_episode_ids` per memory, immutable episode chain |
| **Determinism** | Not advertised; depends on your retrieval logic + embedding state | Contracted — same inputs return same bundle |
| **Storage** | InMemory / SQLite / Postgres / Cosmos via swappable backends | Postgres + pgvector |
| **Orchestrates the agent loop?** | Yes — that's its primary job | No |
| **Best at** | Being a flexible substrate for agent state | Being a focused runtime for cross-session memory |

The two products **compose** rather than compete head-to-head. LangGraph for graph state and orchestration; Statewave for cross-session, ranked, typed memory.

---

## When LangGraph alone is the right call

- You're building a single-turn or single-thread agent where memory across conversations isn't a requirement.
- Your "memory" is really just **graph state** — recent tool outputs, scratchpad, work-in-progress — and a `Checkpointer` is exactly the right shape.
- You want full control over retrieval logic and don't want a runtime making opinionated choices about ranking / budgeting / provenance.
- Your team is already deep in LangGraph and wants to keep one mental model.
- Your "long-term memory" needs are simple — a list of facts per user that you semantic-search at retrieval time. `Store` covers this.

## When Statewave (alongside LangGraph) is the right call

- **Your agent runs across many sessions** and the value is in long-term memory: identity facts, preferences, prior issues, learned procedures. Building ranking + budgeting + provenance over `Store` is real work — Statewave ships it.
- **You want one memory layer across multiple agent stacks.** A LangGraph support agent + an OpenAI-Agents-SDK sales copilot + a custom Express coding assistant should share one memory surface. HTTP-API memory works everywhere; LangGraph `Store` only works inside LangGraph.
- **Eval-driven memory matters.** Statewave's deterministic retrieval is regression-testable. LangGraph's `store.search()` plus your scoring code is testable too — but you write all that yourself.
- **Provenance is a compliance or product requirement.** When a customer asks "why did the agent say this about my account?" you need a finite, queryable chain. Statewave's `source_episode_ids → episodes` is that chain by default.
- **Memory operations should outlive the agent framework.** If you migrate from LangGraph to a different orchestrator next year, your subject memory survives — it lives in Statewave's Postgres, not bound to LangGraph's internal state model.

---

## Migration recipe — adding Statewave to a LangGraph agent

You don't replace LangGraph. You delegate cross-session memory operations to Statewave while keeping LangGraph for orchestration and per-thread state.

### Conceptual mapping

| LangGraph concept | Statewave concept |
|---|---|
| `thread_id` (per-conversation) | `metadata.session_id` on a Statewave episode (carried for context, not for splitting subjects) |
| `Store` namespace `(user_id, "memories")` | `subject_id = "user-<id>"` |
| `store.put(namespace, key, value)` | `POST /v1/episodes` (raw fact as an event) followed by automatic compilation, OR `POST /v1/memories/compile` |
| `store.search(namespace, query=, limit=N)` | `POST /v1/context` (ranked, token-bounded) |
| Checkpointer-managed graph state | Stays in LangGraph; not a Statewave concern |

### Code sketch — node functions

```python
from langgraph.graph import StateGraph
from statewave import StatewaveClient

sw = StatewaveClient("https://your-statewave.example.com", api_key=...)

def remember_node(state):
    """Persist what the user just said to Statewave."""
    last_user_msg = state["messages"][-1].content
    sw.add_episode(
        subject_id=f"user-{state['user_id']}",
        source="chat",
        type="conversation",
        payload={"messages": [{"role": "user", "content": last_user_msg}]},
        metadata={"session_id": state["thread_id"]},
    )
    return state

def recall_node(state):
    """Pull relevant cross-session context for the current task."""
    bundle = sw.get_context(
        subject_id=f"user-{state['user_id']}",
        task=state["current_task"],
        max_tokens=600,
    )
    return {**state, "memory_context": bundle.assembled_context}

# Wire them into your graph however you'd normally compose nodes:
graph = StateGraph(State)
graph.add_node("recall", recall_node)
graph.add_node("agent", agent_node)  # your existing agent node
graph.add_node("remember", remember_node)
graph.add_edge("recall", "agent")
graph.add_edge("agent", "remember")
```

The LangGraph checkpointer continues to handle per-thread graph state. Statewave handles long-term subject memory. They don't conflict.

### When to keep using `Store` AND Statewave

Some things genuinely belong in `Store`:

- Ephemeral session caches (you don't want them surviving forever)
- Tool-call results that the graph re-uses within a single thread
- Configuration that's per-graph-execution, not per-subject

For those, keep `Store`. Use Statewave only for cross-session memory that should outlive the LangGraph thread.

---

## Honest gaps

- **Statewave doesn't orchestrate.** If you don't want a graph framework, fine — but you'll need *some* loop. LangGraph is one good choice; the OpenAI Agents SDK and Vercel AI SDK are others. Statewave doesn't replace any of them.
- **No graph state persistence.** Within-thread state is LangGraph's job; Statewave doesn't try to do it. Don't write graph state into Statewave episodes.
- **More moving parts.** A LangGraph + Statewave deployment has two services to operate (LangGraph's chosen checkpoint store + Statewave's Postgres). For simple cases the operational overhead isn't justified.
- **Different mental models.** LangGraph thinks in *graphs* and *threads*; Statewave thinks in *subjects* and *episodes*. Teams need to be comfortable holding both.

---

## References

- LangGraph persistence — [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- LangGraph Store interface — [reference.langchain.com/python/langgraph/store](https://reference.langchain.com/python/langgraph/store/)
- LangChain overview — [docs.langchain.com/oss/python/langchain/overview](https://docs.langchain.com/oss/python/langchain/overview)
- Statewave architecture — [architecture/overview.md](../architecture/overview.md)
- Statewave ranking model — [architecture/ranking.md](../architecture/ranking.md)
- Statewave subject design — [subject-design.md](../subject-design.md)
- Why Statewave — [why-statewave.md](../why-statewave.md)

*Comparison drafted against LangChain / LangGraph documentation as of May 2026. The LangChain ecosystem moves fast; verify the current shape of `Store` and `Checkpointer` against the live docs before adopting either.*
