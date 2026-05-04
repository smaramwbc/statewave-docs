# Migrating from the OpenAI Assistants API

> **TL;DR** — The Assistants API was deprecated on **August 26, 2025** and is **scheduled for sunset on August 26, 2026** ([OpenAI deprecations page](https://developers.openai.com/api/docs/deprecations)). OpenAI's recommended migration path is the **Responses API** + the **Conversations API**. That migration is itself a good moment to reconsider whether your "memory layer" should be tied to a single LLM provider at all. This page lays out both paths — Responses API (stay with OpenAI's stack) and Statewave (vendor-neutral memory layer) — and when each makes sense.

---

## Where things stand today (May 2026)

From OpenAI's announcements and migration guide:

> **"Assistants API beta deprecation — August 26, 2026 sunset."**
>
> *"When OpenAI released the Responses API in March 2025, they announced plans to bring all Assistants API features to the easier to use Responses API, with a sunset date in 2026. After achieving feature parity in the Responses API, OpenAI has deprecated the Assistants API."*

If you're running on the Assistants API today, you have a hard deadline. The two questions are *what to migrate to* and *what to take the chance to fix while you're already touching the integration*.

The Responses API + Conversations API replaces Threads + Messages with a different shape:

| Assistants API | Responses API + Conversations API |
|---|---|
| Thread (collection of messages, server-side) | Conversation (collection of items: messages, tool calls, tool outputs, other data) |
| `previous_response_id` chaining | Manage conversations as first-class objects |
| Threads-as-memory | Conversations-as-state; long-term memory not provided |

Per OpenAI's [migration guide](https://platform.openai.com/docs/guides/migrate-to-responses), the new shape *"moves to a simpler mental model where you send input items and get output items back."*

## The decision the migration forces

When the deprecation fired, every Assistants-API user inherited a choice:

1. **Migrate to Responses + Conversations API.** Stay with OpenAI's stack, port your thread-based code to conversation items, ship.
2. **Move memory out of the model provider entirely.** Use the Responses API (or any other LLM API) for completions, but persist memory in a vendor-neutral layer. Statewave is one such layer; there are others.

Both are valid. The right choice depends on whether your application's persistent memory is **bound to OpenAI or not**.

---

## Side-by-side

| | **Responses + Conversations API** | **Statewave** |
|---|---|---|
| **What it is** | OpenAI's successor to the Assistants API | Self-hosted vendor-neutral memory runtime |
| **Vendor lock-in** | OpenAI-only. Your conversation items live in OpenAI's infrastructure. | None — call any LLM (Anthropic, Mistral, Bedrock, Ollama, Google, OpenAI) for completions; memory stays in your Postgres. |
| **Memory model** | Conversation items (messages, tool calls, tool outputs); state across calls via conversation chaining | Episodes (immutable raw events) → typed Memories (compiled, scored, with provenance) → ranked, token-bounded Context bundles |
| **Cross-session continuity** | A conversation persists; long-term identity facts about a user across many conversations are not first-class | First-class. Subjects (per user / account / workspace) accumulate facts and procedures across every session |
| **Ranked retrieval** | Implicit in the conversation history's recency; no exposed ranking signals | Explicit: kind priority × recency × task relevance × temporal validity × semantic similarity, with `source_episode_ids` returned per fact |
| **Token-bounded context** | The completion API handles context windowing; managed by OpenAI | First-class: `max_tokens` parameter, `token_estimate` returned with every bundle |
| **Provenance** | Conversation items carry their own metadata; OpenAI doesn't expose a fact-to-source citation chain | Every memory traces to its source episodes by ID |
| **Self-hosted option** | No (OpenAI-managed) | Yes (only) |
| **Dependency on a model provider** | Hard — OpenAI is the platform | None — Statewave's heuristic compiler is fully local; LLM compilation routes through LiteLLM (100+ providers) |

---

## When Responses + Conversations API alone is the right call

- Your application is and will remain **OpenAI-first**. You've factored OpenAI as a strategic dependency and a single migration is acceptable.
- Your memory needs are **session-shaped**, not subject-shaped. Conversations naturally end; you don't have a *"what did Alice tell me six months ago"* requirement.
- You don't need **fact-level provenance** for compliance or product reasons.
- Your team values **a single hosted stack** and the Responses + Conversations APIs cover that.
- Your traffic and budget make the OpenAI Conversations storage costs reasonable for your retention requirements.

## When moving memory to Statewave (or any vendor-neutral layer) is the right call

- **Multi-provider strategy.** You want to call Claude for some tasks, Gemini for others, a local Llama for cheap ones. Memory must follow the user, not the provider. Statewave is provider-agnostic at the memory layer; the model swap is a one-line change in your prompt code.
- **Self-hosted is required.** Data residency, compliance, or a vendor-restriction policy precludes OpenAI hosting your memory.
- **Long-term identity matters.** Customers return weeks or months later. The conversation thread is the *wrong* unit — you need *subject* memory that persists across many threads. Statewave is built around subjects; the Responses API is built around conversations.
- **Eval-driven memory matters.** When the agent's reply changes between runs, you need to know whether your retrieval changed or whether the model changed. Statewave's deterministic retrieval gives you a regression test surface; OpenAI's hosted memory doesn't expose one.
- **Provenance for support and trust.** *"Show me the conversations that produced this fact about the customer"* is a load-bearing query in support workflows. Statewave's `source_episode_ids` makes that two clicks; OpenAI's APIs don't surface it as a first-class chain.

---

## Migration recipe — Assistants API → Statewave

This is *one* path. The other path (Assistants → Responses + Conversations) is documented in [OpenAI's migration guide](https://platform.openai.com/docs/guides/migrate-to-responses); the two aren't exclusive — you'll move to the Responses API for completions either way.

### Conceptual mapping

| Assistants API concept | Statewave concept |
|---|---|
| Assistant (an AI personality + tools) | Stays in your application code. Statewave doesn't model assistants — they're an orchestration concern. |
| Thread (a conversation) | Episodes on a subject, scoped by `metadata.session_id`. The subject is the user/account, *not* the thread. |
| Message in a thread | A `payload.messages` entry on an episode |
| `assistant.tools` configuration | Stays in your code (Responses API tool config, OpenAI Agents SDK tool definitions, etc.) |
| File attachments / `file_ids` | Statewave doesn't host files. Carry references in episode metadata; store the file content wherever you do today. |

### Choosing the subject

The hard step is identifying the *subject*. Don't make threads your subjects — that loses the cross-session value you're migrating for. Pick the persistent entity (user, account, workspace, agent role) whose history you'd want recalled together. See [subject-design.md](../subject-design.md) for the full pattern guide.

### Migration steps

1. **Stand up Statewave.** Single-Postgres + a container; ~10 minutes via [getting-started.md](../getting-started.md).
2. **For each Assistants thread you want to preserve**, identify its subject (typically the authenticated user — `subject_id = f"user-{user_id}"`).
3. **Bulk-export thread messages** via the Assistants API while it's still alive.
4. **Replay each message as a Statewave episode** under the right subject:

   ```python
   sw.add_episode(
       subject_id=f"user-{user_id}",
       source="chat",
       type="conversation",
       payload={"messages": [{"role": msg.role, "content": msg.content[0].text.value}]},
       metadata={
           "session_id": thread.id,           # preserve thread identity for traceability
           "migrated_from": "openai-assistants",
           "original_message_id": msg.id,
       },
       created_at=msg.created_at,             # preserve original timestamp
   )
   ```

5. **Run `/v1/memories/compile` per migrated subject** — Statewave extracts profile facts, summaries, and procedures from the imported episodes.
6. **Cut over your application's prompt-assembly path** to call Statewave for context instead of relying on OpenAI's thread state:

   ```python
   bundle = sw.get_context(subject_id=f"user-{user_id}", task=user_question, max_tokens=600)
   prompt = bundle.assembled_context + "\n\nUser: " + user_question
   reply = openai.responses.create(model="gpt-4o-mini", input=prompt)
   ```

7. **Verify on representative queries** before turning off Assistants API access. Spot-check that retrieved facts match what the old agent recalled.

### What you stop paying for

- OpenAI's Assistants thread storage costs (sunsetting anyway, but worth noting for the budget conversation).
- Per-message context-window inflation — the Assistants API replays threads for context; Statewave returns ranked, token-bounded bundles that fit a tighter budget.

### What you start paying for

- Postgres + container hosting wherever you run Statewave.
- LLM compilation costs if you use the LLM compiler (heuristic compiler is free).
- Embedding API calls if you use a hosted embedding provider (or run Ollama locally for zero egress).

---

## A pragmatic middle path

You don't have to migrate to Statewave to escape the Assistants API sunset. The realistic deadline-driven path:

1. **Migrate completions** from Assistants API to Responses API (per OpenAI's migration guide). This unblocks the August 2026 sunset.
2. **Separately, on your own timeline**, decide whether to keep memory in OpenAI (Conversations API) or move it to a vendor-neutral layer (Statewave or otherwise). This decision is independent of the deprecation deadline — Conversations API works fine.

Bundling both decisions creates risk of slipping the sunset deadline. Decoupling them lets you ship the urgent thing first and re-evaluate the architectural thing under less pressure.

---

## Honest gaps

- **Statewave is not a chat platform.** It doesn't run conversations, manage tool calls, host files, or invoke models. Your application code (or an SDK like the OpenAI Agents SDK) does those things; Statewave just supplies context.
- **You still need a completion API.** Migrating away from the Assistants API doesn't mean leaving OpenAI. Most Statewave users keep using OpenAI (or another provider) via the Responses API for completions; Statewave just means the *memory* is portable.
- **No managed plane.** OpenAI's hosted memory is operationally simple — you don't run anything. Statewave is self-hosted, period. Factor the ops cost honestly.

---

## References

- OpenAI deprecations page — [developers.openai.com/api/docs/deprecations](https://developers.openai.com/api/docs/deprecations)
- Migrate to the Responses API — [platform.openai.com/docs/guides/migrate-to-responses](https://platform.openai.com/docs/guides/migrate-to-responses)
- Assistants migration guide — [developers.openai.com/api/docs/assistants/migration](https://developers.openai.com/api/docs/assistants/migration)
- Statewave getting started — [getting-started.md](../getting-started.md)
- Statewave subject design — [subject-design.md](../subject-design.md)
- Why Statewave — [why-statewave.md](../why-statewave.md)

*Deprecation timeline confirmed against OpenAI's deprecations page as of May 2026. Verify the current sunset date and migration guide before planning the cutover — these dates can shift.*
