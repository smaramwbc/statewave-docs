# Statewave vs Zep

> **TL;DR** — Zep models memory as a **knowledge graph** of entities and edges, with valid/invalid timestamps on relationships, and returns retrieval as an opaque "Context Block" string. Statewave models memory as **typed, provenance-traced facts and episodes**, returns ranked bundles with explicit metadata per memory, and stays out of the graph-reasoning business. Pick Zep if you need explicit entity-relationship reasoning over memory; pick Statewave if you want deterministic, inspectable retrieval with a smaller operational footprint.

---

## What Zep is

From [help.getzep.com](https://help.getzep.com/concepts), Zep is a **Graph RAG memory product**: nodes represent entities, edges represent facts/relationships, **"the graph updates dynamically in response to new data."**

Two retrieval surfaces:

- **Low-level**: `graph.search` returns nodes/edges matching a query — useful when you want to traverse the graph yourself.
- **High-level**: `thread.get_user_context` returns **"Zep's Context Block"**, an optimised string with a user summary plus relevant facts. This is the typical agent-side call.

Memory primitives:

- **Facts and edges** with **"dates when facts became valid and invalid"** — Zep tracks temporal validity per relationship rather than per memory.
- **User summaries** — customisable via *User Summary Instructions*.
- **Conversation threads** — message history per user.
- **Custom entity / edge types** — defined via Pydantic-like classes so you can model your domain.

Zep emphasises **"reduces hallucinations and improves accuracy"** by composing personalised context.

## What Statewave is

Statewave is a **typed-memory runtime** rather than a graph product. Episodes are immutable raw events; memories are typed extractions (`profile_fact`, `episode_summary`, `procedure`, `artifact_ref`) with confidence, validity windows, and `source_episode_ids`. Retrieval returns a structured bundle: per-memory content, kind, confidence, source episode IDs, plus `assembled_context` for prompts and `token_estimate` against the requested budget.

Statewave does not maintain a graph. If your domain needs entity-relationship reasoning ("everyone Alice has spoken with"), that's not Statewave's shape — you'd model it in your own data layer.

---

## Side-by-side

| | **Zep** | **Statewave** |
|---|---|---|
| **Memory model** | Knowledge graph: nodes (entities) + edges (facts) with valid/invalid timestamps | Typed memories (4 kinds) with `valid_from` / `valid_to` windows, plus immutable episodes |
| **Retrieval primary path** | `thread.get_user_context` → opaque Context Block (string) | `POST /v1/context` → structured bundle with per-memory metadata |
| **Custom domain modelling** | First-class: define entity / edge types via Pydantic-like classes | Free-form `metadata_` JSONB on episodes and memories — you carry typing in your application code |
| **Determinism** | Not advertised; graph traversal + reranker behaviour is part of the managed retrieval | Deterministic — same `(subject, task, budget)` returns the same bundle |
| **Provenance** | Edge timestamps for temporal lineage; node history is part of the graph | `source_episode_ids` per memory; immutable episode chain. Direct citation from memory back to the source event |
| **Token-bounded output** | Context Block size shaped by Zep | Explicit `max_tokens` request parameter; bundle reports `token_estimate` |
| **Deployment** | Hosted (Zep Cloud) + self-hosted (Zep Community / open-source). Refer to [getzep.com](https://www.getzep.com/) for current options | Self-hosted only |
| **Storage** | Custom graph store under the hood | Postgres + pgvector — no proprietary store |
| **Best for** | Graph-shaped reasoning over user history; explicit entity modelling; users who want temporal-relationship semantics for free | Engineering teams wanting eval-driven, inspectable retrieval and a single-Postgres footprint |

---

## When Zep is the right call

- Your domain naturally has **entities and explicit relationships** that the agent should reason about. *"What's the relationship between Alice's account and BluePeak Corp?"* — that's a graph question, and a graph is the natural shape.
- You want **temporal validity on relationships** without writing it yourself. Zep's edge-level valid/invalid timestamps handle "Alice was at Acme until 2024" cleanly.
- You're comfortable with **opaque Context Block** retrieval — your agent gets a well-shaped string and you don't need per-fact metadata in the response.
- You prefer **defining custom entity types** (Pydantic-style) over carrying type information in metadata.

## When Statewave is the right call

- **Inspectable retrieval matters.** Statewave returns a list of memories with explicit `kind`, `confidence`, `valid_from`, `valid_to`, and `source_episode_ids` per row. You can render that in an admin UI, log it for evaluation, or feed it to a tool other than the prompt assembler.
- **Determinism is part of the contract.** Same task + same subject + same budget → same bundle. Vector-only or graph-traversal-with-rerankers can't make that claim because index state and reranker variation introduce drift; Statewave's compile-time scoring + ranked-pack assembly does.
- **A single-Postgres footprint is operationally cheaper.** Adding a graph store is a real ops cost. Statewave runs on `postgres + pgvector` — usually already present.
- **You don't need graph reasoning.** Most support / coding / sales / devops agent use cases don't need *"trace the path from this user through three accounts to that incident"* — they need *"what did this user say last week, what's their plan, what's open?"*. Typed-fact retrieval covers that surface and skips the graph operational tax.
- **Provenance for compliance.** "Why did the agent say X?" is a query, not a forensic walk: `provenance.fact_ids → memories → source_episode_ids → episodes` is a finite chain.

---

## Migration recipe — from Zep to Statewave

If you're moving from Zep, the conceptual translation is straightforward but the data shapes differ. Plan a parallel-run period; the cutover is typically read-then-write rather than a flag flip.

### Conceptual mapping

| Zep concept | Statewave concept |
|---|---|
| User (graph node) | Subject (`user-<id>`, see [subject-design.md](../subject-design.md)) |
| Thread / conversation | Episodes with `metadata.session_id` on the user's subject (Statewave doesn't split sessions into separate subjects) |
| Edge (fact connecting nodes) | A `profile_fact` memory on the relevant subject — relational endpoints either become other subjects or get encoded in the memory content |
| Edge `valid_at` / `invalid_at` | `valid_from` / `valid_to` on the memory |
| Custom entity type | Free-form `metadata_.entity_type` on the episode + a convention for how your application interprets it |
| `thread.add_messages` | `POST /v1/episodes` with `payload.messages` |
| `thread.get_user_context` | `POST /v1/context` |
| `graph.search` | No direct equivalent. Statewave doesn't expose a graph-traversal surface — you'd query memories by `subject_id` + `kind` + `metadata.entity_type` filters, or build a graph layer on top. |

### What survives, what doesn't

**Survives**: identity (user → subject), episodes (messages → episodes), facts that are about a single subject (profile facts, preferences), temporal validity (edge timestamps → memory valid_from/valid_to).

**Doesn't survive directly**: relational facts that explicitly link two entities ("Alice works at Acme"). In Statewave, you have a few choices:

1. Encode the relationship in the memory content of the user's subject: `"Alice works at Acme Corp (since 2024-01)."` — the memory is about Alice, not the relationship.
2. Write the same memory to *both* subjects (Alice's and Acme's) with cross-references in metadata. Higher write cost; both retrieval paths see it.
3. Keep relationships in your application's graph (Postgres relations, Neo4j, etc.) and use Statewave only for episode/memory storage. This is the closest in spirit to "use the right tool for each job."

### Code sketch

```python
# Before — Zep
import zep_python
zep = zep_python.ZepClient(api_key=...)
zep.thread.add_messages(thread_id="alice-1", messages=[{"role": "user", "content": "I run dispatch automation at Northwind."}])
ctx = zep.thread.get_user_context(thread_id="alice-1")
# ctx.context — the Context Block string

# After — Statewave
from statewave import StatewaveClient
sw = StatewaveClient("https://your-statewave.example.com", api_key=...)

sw.add_episode(
    subject_id="user-alice",
    source="chat",
    type="conversation",
    payload={"messages": [{"role": "user", "content": "I run dispatch automation at Northwind."}]},
    metadata={"session_id": "alice-thread-1"},
)
bundle = sw.get_context(subject_id="user-alice", task="who is alice?", max_tokens=600)
# bundle.assembled_context  → string ready to prompt
# bundle.facts              → list with kind, confidence, valid_from, source_episode_ids per fact
# bundle.provenance         → fact_ids + episode_ids included
```

### Bulk migration

1. Export Zep facts per user (their export tooling, or paginated `graph.search`).
2. For each fact, write a Statewave memory directly via the admin import path (`/admin/memory/payload-import`) with `kind="profile_fact"`, original Zep edge timestamps mapped to `valid_from` / `valid_to`, and `metadata.migrated_from="zep"`.
3. Export Zep messages per user; ingest as episodes with `source="chat"`, `type="conversation"`, original timestamps preserved on `created_at`.
4. Run `/v1/memories/compile` per migrated subject to let Statewave's compiler observe the imported episodes (and produce additional summaries).
5. Spot-check retrieval before flipping the read path.

---

## Honest gaps

- **No graph traversal.** If your application's prompt strategy is *"find facts about everything Alice is connected to within 2 hops"*, Statewave doesn't do that natively. You'd model the graph in your app.
- **No automatic entity extraction across subjects.** Zep's graph treats "Acme" mentioned across many users as a node it recognises. Statewave doesn't auto-link entity references across subjects — that's an application-side decision.
- **Memory shape is typed, not freely structured.** The four memory kinds (`profile_fact`, `episode_summary`, `procedure`, `artifact_ref`) are deliberate constraints. If you want richer types, you encode them in `metadata`. Zep's Pydantic-style custom types are more ergonomic for heavily relational domains.
- **No managed plane.** You operate Postgres and a container. Zep Cloud removes that; Statewave doesn't.

---

## References

- Zep concepts — [help.getzep.com/concepts](https://help.getzep.com/concepts)
- Zep on GitHub — [github.com/getzep/zep](https://github.com/getzep/zep)
- Statewave architecture — [architecture/overview.md](../architecture/overview.md)
- Statewave ranking model — [architecture/ranking.md](../architecture/ranking.md)
- Statewave subject design — [subject-design.md](../subject-design.md)
- Why Statewave — [why-statewave.md](../why-statewave.md)

*Comparison drafted against Zep documentation as of May 2026. Verify Cloud / Community edition feature parity, license terms, and current API surface against [help.getzep.com](https://help.getzep.com/) before procurement decisions.*
