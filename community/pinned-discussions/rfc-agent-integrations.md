# RFC: Agent Framework Integrations

> Suggested category: **RFCs**. Pin while feedback window is open; unpin once shape is decided.
>
> **Status:** scoping RFC. Statewave is framework-neutral and works with any of these stacks via the REST API and the typed Python / TypeScript SDKs today. This RFC is about whether (and how) to invest in **first-party** integration packages on top.

---

## Title

RFC: Agent Framework Integrations

## Body

### Summary

Statewave is intentionally framework-neutral: the API is a thin contract, and the [Python](https://github.com/smaramwbc/statewave-py) and [TypeScript](https://github.com/smaramwbc/statewave-ts) SDKs make it usable from any agent stack. That's enough for advanced users — but the bar for adoption is "drop into my framework with five lines and it just works."

This RFC asks: **which framework integrations are worth shipping as first-party packages, and what should each one look like?**

### Motivation

Right now, integrating Statewave with a popular agent framework means writing:
- A small adapter that wraps the SDK
- Hooks into the framework's memory / state / context interface
- A handful of conventions for how subjects, episode kinds, and retrieval map to the framework's concepts

Most teams figure this out quickly, but it's repeated work, and the conventions diverge. A first-party integration would:

- Cut adoption time from an afternoon to minutes
- Make the right defaults the easy defaults (subject scoping, token budgets, retrieval shape)
- Surface Statewave inside framework-native docs and examples
- Reduce the surface area for "I integrated it, but my retrieval looks weird" support questions

### Candidates

Tell us where you'd put your weight. Order is alphabetical, not priority.

#### [AutoGen](https://microsoft.github.io/autogen/)
- Multi-agent conversations with shared memory
- Natural fit for handoff context packs
- Open question: per-agent vs. per-conversation subject scoping

#### [CrewAI](https://www.crewai.com/)
- Crew-level memory shared across agents
- Task-bounded retrieval ("what does the crew remember about this customer?")

#### [LangChain](https://www.langchain.com/)
- Memory class implementing LangChain's `BaseMemory` interface
- Retriever wrapping `/v1/context` for LangChain chains
- LangGraph state integration as a separate question

#### [LlamaIndex](https://www.llamaindex.ai/)
- `Memory` integration plus a retriever node
- Episode ingestion from LlamaIndex events / callbacks

#### [OpenAI Agents SDK](https://platform.openai.com/docs/agents)
- Tool-style integration so the agent can read its own memory
- Conversation-scoped subject mapping

#### [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- A Statewave MCP server exposing the read endpoints (and selected write endpoints, gated)
- Lets any MCP-compatible client treat Statewave as a memory tool with no custom code

#### [LiteLLM](https://github.com/BerriAI/litellm)
- Statewave already uses LiteLLM for provider-neutral LLM and embedding calls
- Worth exploring: a LiteLLM proxy plugin that auto-injects Statewave context into chat completions

**Local LLMs** (Ollama, llama.cpp, vLLM, LM Studio)
- Already supported via LiteLLM today
- Question: do we need a "local-first" preset that picks compiler and embedding defaults known to work well CPU-only?

#### Custom agent frameworks
- For teams running a homegrown loop, what would a "minimum-effort" SDK helper look like?
- Hooks: pre-prompt context fetch, post-response episode ingest, optional auto-compile

### Proposed shape

A first-party integration package would, at minimum:

- Live in its own repo or subdirectory under the relevant SDK (`statewave-py/integrations/<framework>/`)
- Pin a tested version range against the framework
- Ship with a worked example in [statewave-examples](https://github.com/smaramwbc/statewave-examples)
- Document the convention for: subject naming, episode kinds, retrieval shape, when to compile
- Stay thin — wrap the SDK, don't fork its concepts

Anti-goals:
- A "Statewave plugin for everything" layer that drifts behind framework releases
- Heavy abstractions that hide what's actually being sent to the API

### Risks / tradeoffs

- **Maintenance debt** — frameworks evolve fast. Each integration is an ongoing commitment.
- **Concept mismatch** — some frameworks treat memory as ephemeral conversation state; mapping that to Statewave's episode/memory split needs care.
- **Lock-in optics** — first-party integrations should *not* feel like they hide the API from users. Anyone should still be able to drop down to raw HTTP at any point.

### Open questions

1. **Top 2–3 to ship first** — given finite maintenance budget, which integrations move the needle most?
2. **Owned vs. community-contributed** — are there frameworks where a community-maintained integration is better than a first-party one?
3. **MCP first?** — would an MCP server cover enough of the need that several of the per-framework integrations become unnecessary?
4. **Versioning strategy** — pin against framework majors, or float and break loudly?
5. **Examples vs. packages** — when is a worked example in `statewave-examples` enough, vs. when is a real package required?
6. **Telemetry** — do integrations need to emit framework-specific spans / events for debuggability?

### Feedback requested

Most useful comments:

- "I use **&lt;framework&gt;** and the integration that would unblock me looks like this: …"
- "I tried integrating Statewave with **&lt;framework&gt;** myself; the friction was X, Y, Z."
- "Skip framework X, ship MCP first — here's why."
- "I'd help maintain the **&lt;framework&gt;** integration."

If you've already built an unofficial Statewave + `<framework>` adapter, please drop a link — that's gold for prioritization.

> This is a scoping discussion. No integration is committed until the use case and maintenance plan are clear.
