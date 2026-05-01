# Privacy & Data Flow

Statewave is honest about what stays local and what leaves your network. Privacy in a memory system depends on **four independent layers**, not just where Postgres runs. This page lists each layer, what runs where, and what content (if any) leaves your infrastructure.

---

## Layer-by-layer

| Layer | Where it runs | What leaves your network |
|-------|---------------|--------------------------|
| **Storage** (Postgres + pgvector) | Your infrastructure | Nothing. Episodes, compiled memories, embeddings, and provenance all live in the database you control. |
| **Retrieval / ranking** | Your infrastructure (Statewave server) | Nothing. Ranking is local, deterministic, and inspectable. |
| **Compilation — heuristic** | Your infrastructure | Nothing. Default mode. |
| **Compilation — LLM** | Configured provider via LiteLLM | Episode batches (up to ~6000 chars) sent to the provider you choose. Self-hosted models (Ollama, vLLM, …) keep this local. |
| **Embeddings** | Configured provider | Episode/memory text sent for vectorization. The default `OpenAIEmbeddingProvider` calls OpenAI; switch to a self-hosted embedding endpoint via LiteLLM, or disable embeddings to use text-only retrieval. |
| **Your agent's LLM** | Wherever you host it | Statewave returns the assembled context bundle to your agent. What your agent sends to its model is governed by your agent — not by Statewave. |

---

## Configuration matrix

| Goal | Compiler | Embeddings | What leaves the network |
|------|----------|------------|-------------------------|
| **Fully local** | `heuristic` | self-hosted (Ollama/vLLM) or `stub` (text-only) | Nothing driven by Statewave |
| **Local extraction, hosted vectors** | `heuristic` | OpenAI / Cohere / etc. | Episode/memory text → embedding provider |
| **Hosted extraction, local vectors** | `llm` (self-hosted model) | self-hosted | Nothing leaves (if both LLMs are in your VPC) |
| **Default cloud setup** | `llm` (OpenAI etc.) | OpenAI | Episode batches + embedding text → providers |

Your agent's LLM choice is independent of all of the above.

---

## Practical guidance

- **Compliance-driven deployments:** start on `heuristic` + a self-hosted embedding model (or no embeddings). Storage stays in your VPC; retrieval is local. The only remaining egress is whatever your agent's own LLM does.
- **Hybrid:** keep storage local, choose providers per layer based on data sensitivity. The compiler and embedder are configurable independently.
- **Audit:** every memory carries `source_episode_ids`. Provenance is preserved regardless of compiler choice.

---

## What we do *not* claim

- We do **not** claim "your data never leaves your infrastructure" as a blanket statement. Whether content leaves depends on your compiler and embedding configuration.
- We do **not** ship a managed Statewave cloud. There is no Statewave-hosted backend that customer data passes through in a self-hosted deployment.
- We do **not** control your agent's LLM choice. If your agent calls a hosted model with the context Statewave returns, that model sees the context.

---

## See also

- [Compiler Modes](compiler-modes.md) — heuristic vs LLM
- [Deployment Guide](../deployment/guide.md)
- [Architecture Overview](overview.md)
