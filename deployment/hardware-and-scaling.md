# Hardware & Scaling

This page answers two questions operators ask most: **do I need a GPU?** and **how does Statewave scale?**

---

## GPU requirements

**Statewave itself never requires a GPU.** The server is a stateless FastAPI process that talks to Postgres + pgvector — both CPU-only.

GPU only enters the picture if **you choose** to:

| Choice | GPU implication |
|--------|-----------------|
| Run the **heuristic compiler** (default) | None. Pure regex. CPU only. |
| Run the **LLM compiler** with a hosted provider (OpenAI, Anthropic, Bedrock, …) | None for you. The provider runs the model. |
| Run the **LLM compiler** with a self-hosted model (Ollama, vLLM, TGI, …) | A GPU is typically required wherever that model runs — but that's separate infrastructure, not Statewave. |
| Use **hosted embeddings** (OpenAI, Cohere, …) | None for you. |
| Use a **self-hosted embedding model** | GPU may improve throughput — same caveat: separate infrastructure. |

In short: the Statewave container is CPU-only and is happy on a `shared-cpu-1x` Fly machine, a small Railway instance, or a 1-CPU container on Kubernetes. GPU questions belong to the model-hosting layer you configure, if any.

---

## Scaling

### What we've validated

- **Single-node deployments** work well for the design point: small-to-medium support / coding / sales agents with thousands of subjects.
- Compilation, retrieval, and ingest are all I/O-bound on Postgres for typical workloads.
- The LLM compiler caps in-flight requests at **4** to avoid hammering providers; this is the dominant throughput limit when LLM compilation is on.

### What we have *not* validated

- Horizontal scaling (multiple Statewave processes against one Postgres) is supported by the design (rate limiting and locks are Postgres-backed) but not load-tested. We have not published throughput numbers.
- We have not benchmarked against >100k subjects or sustained high-RPS production traffic.

### Operator guidance

- **Postgres is the bottleneck.** Connection pool size, vacuum cadence, and pgvector index health matter more than API CPU.
- **LLM compiler latency dominates** when enabled — episode-batch round-trips to the provider determine how fast new memories appear. Heuristic compilation is essentially free in comparison.
- **Embeddings**: if you generate embeddings synchronously on every memory write, embedding-provider latency is in your write path. Consider batching or async generation if write volume is high.
- **Rate limiting** is per-IP, sliding-window, Postgres-backed — shared correctly across multiple workers.
- **Tenant isolation** is app-layer (`tenant_id` scoping in queries). It is not row-level-security; if you have hard-isolation requirements, run separate databases per tenant.

### What's coming

A horizontal-scaling guide with read replicas, connection pool sizing, and tested patterns is on the [roadmap](../roadmap.md). If you have a specific scaling target you need confidence around, open an issue with the workload shape — we'll prioritize what we benchmark.

---

## Compiler choice and scaling

| Compiler | Throughput characteristic | What scales it |
|----------|---------------------------|----------------|
| Heuristic | High; CPU-bound, deterministic per-episode cost | API workers + Postgres write throughput |
| LLM (hosted provider) | Bound by provider rate limits and the in-flight cap of 4 | Provider quota; tune `STATEWAVE_LLM_*` settings |
| LLM (self-hosted) | Bound by your model server's throughput | GPU/inference server capacity |

Pick the compiler that matches your scale and privacy needs first. Don't conflate "we want LLM-quality extraction" with "we need GPUs" — those are decoupled by your choice of provider.

---

## See also

- [Compiler Modes](../architecture/compiler-modes.md)
- [Privacy & Data Flow](../architecture/privacy-and-data-flow.md)
- [Deployment Guide](guide.md)
