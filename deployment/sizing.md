# Deployment Sizing Guide

This guide answers: **what do I actually need to run to support my workload?**

It is operator-facing. It is intentionally conservative, ranges over four tiers from local development to enterprise, and is honest about what we have and have not validated.

> **Closely related:** [Hardware & Scaling](hardware-and-scaling.md) answers the GPU question and explains scaling characteristics. This page picks up where that one stops and tells you what shape of box (or boxes) to provision. For the diagnostic companion — *"things are slow, what do I check?"* — see the [Capacity Planning & Tuning Checklist](capacity-planning.md).

---

## How to use this guide

1. Read [What drives sizing](#what-drives-sizing) so you understand the variables.
2. Pick the tier that matches your workload from [Tiers](#tiers) — choose by **workload shape**, not by how big you'd like to feel.
3. Use the per-tier recommendation table as a starting point. The numbers are deliberately a little above what's needed.
4. Watch the **"signs you should upgrade"** signals in each tier.
5. Revisit when your workload shape changes — not on a calendar.

---

## Layers, restated

Statewave is composed of layers that scale independently. **Sizing is per-layer, not per-product.**

| Layer | Where it runs | Hardware-relevant role |
|-------|---------------|------------------------|
| **Statewave API** | Your container / VM | Stateless FastAPI process. CPU and RAM. No GPU, ever. |
| **PostgreSQL + pgvector** | Your DB host (managed or self-run) | The state. Storage, RAM (working set + HNSW), CPU for queries. **This is what gets bigger.** |
| **Heuristic compiler** | Inside the API process | Pure CPU. Negligible cost relative to DB. |
| **LLM compiler** | A model you configure (hosted *or* self-hosted) | If hosted: zero local hardware impact, bound by provider quota. If self-hosted: a separate machine, typically with GPU. **Not the API tier.** |
| **Embedding provider** | Hosted API *or* self-hosted endpoint | Same split as the LLM compiler. |
| **Your agent's LLM** | Wherever your application runs it | Out of scope for Statewave sizing. |

**Two consequences:**

- The Statewave API process is small at every tier. It runs happily on 1 vCPU and a few hundred MB of RAM.
- "Do I need a GPU?" only ever applies to the model layers, and only if you self-host them. See [Hardware & Scaling](hardware-and-scaling.md#gpu-requirements).

---

## What drives sizing

Sizing is not a function of "how big is my company." It is a function of these workload variables:

### Subject cardinality
Total active `subject_id`s in the system. Drives base storage and the working set for indexes (especially the pgvector HNSW index on `memories.embedding`). At small cardinality, almost nothing matters; once the working set stops fitting in RAM, query latency and DB CPU rise quickly.

### Episode write rate
Episodes per day across all subjects. The append-only insert path is cheap and has not been a bottleneck in practice. This variable mostly drives **storage growth**, **WAL volume**, and how quickly the **compile backlog** accumulates if you're not compiling continuously.

### Compile frequency and mode
How often `POST /v1/memories/compile` runs.

- **Heuristic** is CPU-bound, deterministic, and effectively free relative to the DB write it produces.
- **LLM compiler** is bound by provider RTT (or your self-hosted model server's throughput) and an in-process semaphore that caps **4 in-flight LLM calls** at a time per Statewave process. Running more API replicas multiplies that cap.

### Context request rate
`POST /v1/context` calls per second. This is the hot path for most workloads. It drives:

- DB CPU (ranking + semantic search via pgvector).
- Embedding-API spend, if you generate query embeddings.
- A small amount of CPU on the API process for assembly and token counting.

There is an in-process LRU cache for query embeddings — repeat task strings are essentially free; first-time strings pay the embedding-provider RTT.

### Embedding generation pattern
If embeddings are generated synchronously on every memory write and your provider is remote, **embedding latency lives in your write path**. At low write volumes this is fine. As volume grows, consider batching or moving embedding generation to a follow-on step.

### Embedding provider location
- **Hosted** (OpenAI, Cohere, Voyage, …): you pay $$ and RTT; no local hardware impact.
- **Self-hosted** (Ollama, vLLM, TEI, …): you pay capex/opex on a model server. A GPU is typically required for non-trivial throughput. **This server is sized separately from the Statewave API.**

### LLM compiler choice
Same split as embeddings.

- Heuristic only — easiest to size, no external dependency.
- Hosted LLM — bound by provider rate limits and the 4-in-flight cap per Statewave process.
- Self-hosted LLM — bound by your model server's throughput. Statewave's `STATEWAVE_LLM_*` settings tune what you call; the model server itself is the bottleneck.

### Tenant count
Multi-tenant isolation today is **app-layer** (`tenant_id` scoping in queries; v0.5). Tenant count drives connection pool math (concurrent in-flight requests across all tenants) and operational discipline (monitoring per-tenant usage), not extra processes per tenant. If you have a hard isolation requirement, run separate databases per tenant; this is a topology choice, not a sizing one.

### Retention window
Episodes and memories are kept until you delete them (per-subject delete is in-API; TTL/expiry policies are on the [roadmap](../roadmap.md) for v0.7). Long retention compounds storage and HNSW memory.

### Bootstrap / docs pack usage
The default support docs pack (`default-support-docs-pack.md`) is small as text but compiles into many memories. If your design loads it **per-tenant** or **per-subject**, multiply storage and compile cost accordingly. Loading it once globally is cheap.

### Webhook fanout
Webhook delivery is durable and Postgres-backed (v0.5). High-volume episode ingest with subscribed events causes a steady stream of small queue rows. The load is small but real, and shows up as a sustained DB write rate at Tier 4.

### Admin console traffic
Read-only. Adds a small sustained baseline against `/admin/*`. Negligible at all tiers.

---

## Tiers

Pick a tier by **workload shape**. The boundaries below are guidance, not contracts. We have not published throughput benchmarks; if you need numbers tied to a specific RPS target, see [Hardware & Scaling](hardware-and-scaling.md#what-weve-validated) and open an issue with your workload shape.

| Tier | Typical shape | Topology | Compiler | DB |
|------|--------------|----------|----------|----|
| **1. Local / Development** | One developer, ad-hoc traffic | Single container; bundled Postgres via `docker compose` | Heuristic (default) | Bundled |
| **2. Small Production** | Single product, ≤ a few hundred subjects, low sustained traffic | Single API container; managed Postgres | Heuristic, or LLM with hosted provider | Managed (Neon / Supabase / RDS) |
| **3. Growing Production** | Multiple workloads or thousands of subjects, regular compilation | API replicas behind a reverse proxy; managed or dedicated Postgres | Usually LLM with hosted provider | Dedicated; HNSW working set in RAM |
| **4. Enterprise / Heavy Load** | Many tenants and/or many thousands of subjects, frequent compilation, high sustained traffic | API replicas behind a load balancer; dedicated Postgres ± read replica; observability; optional self-hosted model sidecar | Anything; sized per the model layer | Hardened — backups, monitoring, vacuum tuning, possible read replica |

---

## Recommended profiles

These are starting points, not floors. Bias toward "give it more RAM" before adding cores; Postgres usually wants RAM first.

### Tier 1 — Local / Development

| Component | Recommendation |
|-----------|----------------|
| Statewave API | 1 vCPU, 512 MB RAM |
| PostgreSQL | Bundled (Docker), default config |
| Storage | 1–5 GB |
| GPU | Not applicable |

This is exactly what `docker-compose.yml` ships and what the demo `fly.toml` runs on (`shared-cpu-1x`, `512mb`). Good enough to start. Ample headroom for examples and small evals.

**Signs you should upgrade:** you're running multi-tenant scenarios, want persistent observability, or are putting it in front of a real product.

---

### Tier 2 — Small Production

| Component | Recommendation | Notes |
|-----------|----------------|-------|
| Statewave API | 1–2 vCPU, 1 GB RAM, 1 instance | A `shared-cpu-1x` or `s-1vcpu-1gb` is enough to start. |
| PostgreSQL | 2 vCPU, 4 GB RAM, 20 GB SSD, managed | Neon, Supabase, RDS, or a dedicated VM. **Must be a pgvector-capable image.** |
| Connection pool | Default (`pool_size=5, max_overflow=10`) | Tune up only if you see `pool_timeout` errors. |
| GPU | Not applicable unless you self-host models | Hosted LLM and embeddings keep you GPU-free. |
| Reverse proxy / TLS | Optional but recommended | Provided by your platform (Fly, Railway, Render). |

**Good enough to start:** yes, for the design point — small-to-medium support / coding / sales agents with hundreds to a few thousand subjects.

**What usually becomes the bottleneck first:** at this size, **embedding-provider latency** on first-time `/v1/context` task strings is the most visible thing. The query-embedding LRU cache fixes repeats; cold strings pay one provider RTT.

**Signs you should upgrade:**

- Sustained DB CPU > ~60% on the managed instance.
- `/v1/context` p95 climbs past your latency budget for cache-miss requests.
- You start running multiple application teams or tenants on a shared instance.
- Subject count crosses a few thousand and HNSW index size approaches the DB's RAM.

---

### Tier 3 — Growing Production

| Component | Recommendation | Notes |
|-----------|----------------|-------|
| Statewave API | 2 replicas, 1–2 vCPU each, 2 GB RAM | Stateless; horizontal scaling is supported by design (rate limit and webhook queue are Postgres-backed) but not load-tested. |
| PostgreSQL | 4 vCPU, 8–16 GB RAM, 100 GB SSD | Size RAM so the **HNSW index for `memories.embedding` fits in shared buffers + OS cache**. This dominates `/v1/context` latency at scale. |
| Connection pool | Watch total = (replicas × `pool_size + max_overflow`); keep below DB `max_connections` | Default math: 2 × (5 + 10) = 30 concurrent. Tune `pool_size` if you run more replicas. |
| Reverse proxy | Yes — terminate TLS, pin timeouts | `/v1/context` can run several seconds when embedding cold + LLM compile is in flight. Set client and proxy timeouts accordingly. |
| Observability | Logs + DB metrics; OpenTelemetry tracing extra | Optional `[otel]` extra ships spans on key operations. |
| Backups | Required | Per-subject export/import (v0.5) is for migration, not DR. Use the DB's PITR/snapshots. |
| GPU | Not applicable unless self-hosting models | |

**What usually becomes the bottleneck first:**

- **Postgres CPU + I/O** on `/v1/context` semantic search if HNSW is paging from disk.
- **Provider rate limits** if LLM compilation runs at high cadence — the 4-in-flight cap per Statewave process keeps you polite, but you may need to negotiate quota with your provider.

**Signs you should upgrade:**

- DB CPU consistently > 70% during peak; vacuum lagging.
- HNSW recall degrades or query latency rises with subject growth — index no longer hot in RAM.
- Compile backlog grows during the day — provider throughput is the limiter.
- Multiple tenants generate "noisy neighbor" pressure.

---

### Tier 4 — Enterprise / Heavy Load

| Component | Recommendation | Notes |
|-----------|----------------|-------|
| Statewave API | ≥ 3 replicas behind a load balancer, 2 vCPU / 2–4 GB each | Scale replicas with concurrent request volume. |
| PostgreSQL primary | 8+ vCPU, 32+ GB RAM, 500 GB+ NVMe SSD | Tune `shared_buffers`, `work_mem`, `maintenance_work_mem`, autovacuum. Pin a maintenance window. |
| PostgreSQL read replica | Optional but high-leverage | `/v1/context` is read-heavy; a replica offloads ranking/search from the primary. **Statewave does not yet route reads to a replica** — see [roadmap](../roadmap.md) v0.7 horizontal-scaling guide. Today, useful for ad-hoc analytics + safety. |
| Connection pool | Sized to DB `max_connections` with margin for migrations and admin tools | At this size, use a connection pooler (PgBouncer / managed pooler) in **transaction** mode in front of the DB. |
| Compile concurrency | Raise effective concurrency by adding API replicas; the per-process cap of 4 in-flight LLM calls is intentional | Negotiate provider quotas in proportion. |
| Self-hosted model sidecar | Optional — only if privacy or cost demand it | This is where GPUs live. **Sized separately from the Statewave API.** Examples: a single A10/A100 box for vLLM serving a 7B–70B model, or a smaller TEI/Ollama deployment for embeddings. See the [Privacy & Data Flow](../architecture/privacy-and-data-flow.md) configuration matrix. |
| Reverse proxy / WAF | Required | Terminate TLS, rate-limit at the edge, longer timeouts than typical web apps because cold context calls can be 5–30 s. |
| Observability | Logs, metrics, traces, DB-level monitoring | Track: API p95, DB CPU, vacuum lag, pgvector index size, provider 429 rate, webhook DLQ depth. |
| Backups + DR | PITR + tested restore | Standard for any production DB. |
| GPU | Only on the self-hosted model sidecar, if you choose to run one | Never on the Statewave API tier. |

**What usually becomes the bottleneck first:**

- **Postgres I/O / vacuum pressure** under sustained ingest + compile.
- **Provider rate limits** on hosted LLM compilation.
- **Embedding throughput** if synchronous on writes.
- **HNSW index memory** as subject and memory counts grow.

**Signs you should upgrade further (or change topology):**

- DB CPU saturated even after tuning → split read traffic to a replica; consider sharding by tenant if a single primary cannot keep up.
- Webhook DLQ growing → scale subscribers or add filtering (filters are on the v0.8 roadmap).
- Latency floor is the embedding provider → move to a self-hosted endpoint or a faster model.

---

## Topology patterns

Five reference topologies, in upgrade order. Pick the lowest one that meets your requirements; move up only when the bottleneck signals above point to topology, not capacity.

### A. Single container + bundled Postgres
`docker compose up`. Tier 1 only. Simple, ephemeral, fine for development and demos.

### B. Single API container + managed Postgres
The Tier 2 default. Fly / Railway / Render / a small VM, plus Neon / Supabase / RDS for Postgres. **Must use a pgvector-capable Postgres image** — see `infra/postgres-pgvector/` in the core repo for a Dockerfile that bundles the extension.

### C. API replicas + managed Postgres + reverse proxy
Tier 3. Replicas are stateless; the rate limiter is Postgres-backed and shared correctly across them. The reverse proxy terminates TLS and lets you pin timeouts (Statewave's `/v1/context` can be longer than typical HTTP traffic). Horizontal scaling is **supported by design but not load-tested** — measure your own workload and report findings if you push past prior boundaries.

### D. API replicas + dedicated Postgres + read replica + observability
Tier 4 baseline. Add a connection pooler (PgBouncer or your managed equivalent) once total connections × replicas approach the DB's `max_connections`. Use a read replica today as a safety net and for analytics; native replica routing for `/v1/context` is on the roadmap.

### E. Topology D + self-hosted model sidecar
Tier 4 optional layer. The model server (vLLM / TGI / Ollama / TEI) sits beside the Statewave deployment. Statewave talks to it via LiteLLM as if it were any other provider. **GPU sizing belongs to this server, not the API tier.** Treat it as its own product with its own runbook — model warm-up time, batch size, KV cache memory, request queue depth.

A few cross-cutting notes:

- **Workers / cron processes are not required.** Compile jobs are durable and Postgres-backed (v0.5); they are kicked off by API calls. You do not provision a separate worker tier at any tier.
- **TLS belongs at the edge.** Statewave does not terminate TLS itself.
- **Admin console** is a separate deployable (`statewave-admin`); deploy it behind an access gateway. Its load is read-only and small.

---

## Common upgrade paths

| Symptom | First thing to try |
|---------|--------------------|
| `/v1/context` p95 too high | Confirm pgvector HNSW fits in DB RAM. If not, raise DB RAM. If yes, confirm query embeddings are cached (repeat tasks should be fast). |
| Compile backlog growing | Add a Statewave API replica (raises effective LLM concurrency); negotiate provider quota. |
| 429s from your LLM provider | Provider quota — talk to the provider, or move to a self-hosted model. |
| DB CPU > 70% sustained | Tune autovacuum + `work_mem`; consider a read replica for analytics today, native read routing later. |
| `pool_timeout` errors in API logs | Raise SQLAlchemy `pool_size`/`max_overflow` (currently defaults to `5 + 10`); ensure DB `max_connections` accommodates `replicas × pool`. |
| Webhook DLQ accumulating | Scale the subscriber; check the receiver's error rate. |

---

## What we have *not* validated

To be plain:

- We have not benchmarked Statewave above ~100k subjects.
- We have not load-tested horizontal scaling under sustained high-RPS production traffic.
- We have not published per-tier throughput numbers because we do not have credible numbers to publish.

The recommendations above are derived from the architecture's design points and the in-product knobs (DB pool defaults, LLM concurrency cap, batch sizes), not from a load test campaign. If you have a specific scaling target, file an issue with your workload shape — it directly informs what we benchmark next.

---

## See also

- [Capacity Planning & Tuning Checklist](capacity-planning.md) — the diagnostic companion to this guide
- [Hardware & Scaling](hardware-and-scaling.md) — the GPU question and scaling characteristics
- [Compiler Modes](../architecture/compiler-modes.md) — heuristic vs LLM cost/throughput
- [Privacy & Data Flow](../architecture/privacy-and-data-flow.md) — what each layer sends where
- [Deployment Guide](guide.md) — Docker / Fly / Railway recipes
- [Migration & Upgrade Runbook](migrations.md) — operational hygiene
- [Roadmap](../roadmap.md) — horizontal-scaling guide, memory TTL, Helm chart
