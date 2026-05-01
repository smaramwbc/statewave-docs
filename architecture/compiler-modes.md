# Compiler Modes

Statewave's compilation step turns raw episodes into typed memories. Two compilers ship today:

| Mode | What it does | External calls? | Default? |
|------|--------------|-----------------|----------|
| **Heuristic** | Regex/pattern-based extraction of profile facts, procedures, and summaries | None — fully local | Yes |
| **LLM** | Calls a configured LLM (via LiteLLM) to extract structured memories from episode batches | Yes, to whichever provider you configure | No |

Configured via `STATEWAVE_COMPILER_TYPE=heuristic|llm` in `.env`.

---

## When to choose heuristic

- You want **zero external dependencies** for compilation.
- Your episodes follow predictable shapes (chat-style `messages[].content`, support tickets).
- You need **deterministic** behavior (regex output is stable across runs).
- You care about cost — there are no LLM API charges.
- You need fully local data flow (see [Privacy & Data Flow](privacy-and-data-flow.md)).

The heuristic compiler covers the common cases: name, company, location, preferences, repeated procedures, and per-episode summaries. Confidence scores range 0.6–0.8.

## When to choose LLM

- You have **diverse, unstructured** episode content where regex misses signal.
- You're willing to send episode content to an external (or self-hosted) LLM.
- You need richer extraction than the heuristic patterns — implicit goals, multi-step procedures, long-form summaries.
- You can absorb API latency and cost.

The LLM compiler:

- Batches episodes (up to ~6000 chars per batch).
- Concurrency is capped at **4 in-flight requests** to avoid hammering providers.
- Runs in a `ThreadPoolExecutor` so it does not block the async event loop.
- **Falls back to the heuristic compiler** on any provider error or parse failure — compilation never silently drops episodes.

Provider is whatever LiteLLM supports: OpenAI, Azure, Anthropic, Bedrock, Cohere, Ollama, vLLM, etc. Self-hosted models keep compilation local; hosted providers send batches off-network.

---

## Switching at runtime

Compilation reads `settings.compiler_type` at startup. To switch:

```bash
# In .env
STATEWAVE_COMPILER_TYPE=llm
STATEWAVE_LLM_MODEL=gpt-4o-mini  # any LiteLLM model id
```

Restart the API container. Existing memories are not re-compiled automatically — call `compile_memories(subject_id)` to recompile uncompiled episodes (compilation is idempotent).

---

## Quality and cost — what we know

- **Heuristic** has stable behavior, well-defined recall on the patterns it knows. We have not published a comparative quality eval against the LLM compiler.
- **LLM** has higher recall on unstructured content. Cost scales linearly with episode volume × tokens per batch × provider price.
- Both write to the same `memories` table with identical schema and provenance.

When in doubt: **start on heuristic.** It's the default for a reason — zero ops cost, zero data egress, fast. Switch to LLM when you have evidence that heuristic is missing the signal you need.

---

## See also

- [Privacy & Data Flow](privacy-and-data-flow.md) — what each compiler sends where
- [Architecture Overview](overview.md)
- [ADR 002 — Heuristic Compilation](../adrs/002-heuristic-compilation.md)
- [ADR 004 — v0.3 LLM Compiler](../adrs/004-v03-advanced-features.md)
