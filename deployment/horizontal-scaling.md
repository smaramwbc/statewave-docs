# Horizontal Scaling

This guide covers running **more than one Statewave API instance** against a shared Postgres. It is the operator-facing companion to the existing single-instance docs:

- **Need to size a single instance?** → [Deployment Sizing Guide](sizing.md)
- **Single instance feels slow?** → [Capacity Planning & Tuning Checklist](capacity-planning.md)
- **GPU question / scaling characteristics overview?** → [Hardware & Scaling](hardware-and-scaling.md)

This page assumes you have read at least the Sizing tier table and have decided you actually need replicas. Most workloads do not. **Add an API replica only after you have tuned the database** (see [capacity-planning.md → Tune before you scale](capacity-planning.md#tune-before-you-scale)). Replicas absorb burstier traffic and multiply effective LLM-compile concurrency; they do **not** help a Postgres-bound system.

---

## What this guide is, and is not

**Is:** a description of which architectural properties hold across replicas, the connection-budget math you need to get right, multi-instance-specific diagnostics, and reference topologies you can adapt.

**Is not:** a benchmark report. Statewave's horizontal-scaling path is supported by design (everything coordinates through Postgres) but has not been load-tested at high RPS by the project. The numbers in this guide are deployment-math defaults, not measured throughput. If you need throughput numbers tied to a specific RPS target, [open an issue](https://github.com/smaramwbc/statewave/issues) with your workload shape.

---

## What stays correct across replicas

Statewave's API process is stateless by design. The following pieces of state and coordination are **already shared correctly** across any number of replicas pointed at the same Postgres:

| Concern | Where it lives | Why it's safe across replicas |
|---|---|---|
| **Compile job queue** | Postgres-backed (v0.5: durable async compilation) | Jobs are claimed atomically; any replica can pick up any job. No leader election needed. |
| **Webhook delivery + DLQ** | Postgres-backed (v0.5: reliable webhook delivery) | Events are written once; the delivery worker on any replica drains the same queue with retry + backoff. |
| **Rate limiting** | Postgres-backed (v0.5: distributed rate limiting) | Sliding-window counters are atomic Postgres operations — totals are correct regardless of which replica handled the request. |
| **Multi-tenant isolation** | App-layer `tenant_id` scoping (v0.5) | Identical on every replica — no cache to invalidate. |
| **Query embedding cache (L2)** | Postgres `query_embedding_cache` table (v0.7: cross-machine query embedding cache) | All replicas read and write the same warm cache; first hit on any instance warms all subsequent hits on every instance. |
| **Migrations** | Alembic against the same DB | Run once at deploy, not per-replica. See "Migrations under multi-instance deploys" below. |

You do **not** need to add Redis, a job broker, a leader election layer, or any other infrastructure to scale horizontally. The contract is: **replicas + one Postgres**.

---

## What does *not* scale automatically

Be explicit about the constraints. None of these block horizontal scaling, but each shapes how you configure it.

### Read replicas are not auto-routed
Statewave does not currently route read traffic to a Postgres read replica. All API queries — including the read-heavy `/v1/context` semantic-search path — go to the primary. A read replica is still useful at Tier 4 for **safety** (failover target) and **analytics** (run heavy ad-hoc queries off the primary), but it does **not** offload `/v1/context`. Native replica routing is on the [roadmap](../roadmap.md).

### In-process LLM concurrency cap is per-replica
The cap of **4 in-flight LLM-compile calls per Statewave process** is intentional politeness against your provider. With `R` replicas, your effective concurrency is `4 × R`. This **multiplies, not consolidates** — make sure your provider quota covers `4 × R` concurrent calls before you scale out, or you will replace "Statewave is the bottleneck" with "the provider is the bottleneck" and `429`s.

### L1 query embedding cache is per-replica
The in-process LRU is per-instance; the L2 Postgres-backed cache (v0.7) is shared. A **fresh replica** (after deploy or autoscale-up) will see L1 misses on every task string until L2 warms it on first hit. Symptom: a brief, instance-local latency spike right after a new replica starts taking traffic. Mitigation: pre-warm with a few representative `/v1/context` calls before adding the replica to the load balancer, or accept the short transient.

### Sticky sessions are unnecessary — and unhelpful
There is no in-memory per-session state on the API. Round-robin (or any load-balancing strategy) is correct. Sticky sessions add no benefit and reduce cache utilization on the L1 embedding cache.

---

## The connection-budget runbook

The single most common multi-instance failure mode is **exhausting Postgres `max_connections`**. This is also the easiest to prevent — it is arithmetic, not measurement.

### The formula

```
required = replicas × (pool_size + max_overflow)
         + headroom
         + admin/migration/monitoring slots
```

Defaults shipped by Statewave (per process, via SQLAlchemy):

- `pool_size = 5`
- `max_overflow = 10`
- → **15 connections per replica** as the absolute upper bound under burst.

### Worked example

| Topology | Replicas | Per-replica pool | API-side max | Headroom (admin, migrations, backups, monitoring) | **DB `max_connections` you need** |
|---|---|---|---|---|---|
| Tier 2 single instance | 1 | 15 | 15 | 10 | **≥ 25** |
| Tier 3 (2 replicas) | 2 | 15 | 30 | 15 | **≥ 45** |
| Tier 3 (3 replicas) | 3 | 15 | 45 | 15 | **≥ 60** |
| Tier 4 (5 replicas, no pooler) | 5 | 15 | 75 | 25 | **≥ 100** |
| Tier 4 (10 replicas, **with PgBouncer transaction mode**) | 10 | 15 (to pooler) | 150 (logical) | — | **PgBouncer pool sized to ~30–60 actual DB connections** |

The "10 replicas with PgBouncer" row is the point of the table: once your replicas × 15 starts crowding `max_connections`, **add a transaction-mode connection pooler in front of Postgres** instead of raising `max_connections` indefinitely. Postgres connection overhead is real; a pooler decouples logical client connections from physical backend connections.

### When to switch to PgBouncer (or a managed equivalent)

Concrete signals, in order of urgency:

1. `pool_timeout` errors appearing in API logs under burst → SQLAlchemy pool is exhausted (raise `pool_size` first).
2. `connection_limit_exceeded` / `too many connections for role` errors from Postgres → `max_connections` exhausted (need a pooler, or fewer replicas).
3. Per-request connection acquisition latency rising in your DB metrics → backend is spending non-trivial time on connection setup.
4. Total `replicas × 15` approaching 70% of `max_connections` → you are one autoscale event away from #2.

PgBouncer **transaction mode** is the right setting for Statewave (sessions are short, no `LISTEN`/`NOTIFY`, no prepared statements held across transactions). Statewave does not currently issue session-level state that breaks under transaction pooling.

### Tuning `pool_size` upward

Before adding a pooler, raising `pool_size` is the cheap first move when individual replicas show `pool_timeout` under steady load. Defaults assume Tier 2; at Tier 3+ you will commonly want `pool_size=10, max_overflow=20` per replica. **Recompute the connection budget every time you change either knob or the replica count.**

---

## Reference topologies

Three topologies, in upgrade order. Pick the lowest one that meets your requirements; move up only when the signals in [capacity-planning.md](capacity-planning.md) point to topology, not capacity.

### Topology H1: Two API replicas + managed Postgres + reverse proxy

The Tier 3 starting point. This is the smallest topology that exercises every horizontally-scaled code path (Postgres-backed rate limit, shared compile queue, shared webhook DLQ, shared L2 embedding cache).

**What runs where:**
- Two Statewave API containers behind a reverse proxy / load balancer (Fly machine group, k8s `Deployment` with `replicas: 2`, ECS service with `desired_count: 2`, etc.).
- One managed Postgres (Neon / Supabase / RDS / Cloud SQL) — pgvector-capable image required.
- TLS terminated at the proxy. Per-request timeouts long enough for cold-start `/v1/context` (5–30 s).

**Connection budget:** see "Worked example" row 2 above — DB `max_connections ≥ 45`. Most managed Postgres tiers ship 100+, so this is comfortable.

**Diagnostics specific to this topology:**
- A new replica's first few minutes of `/v1/context` requests will be slower (cold L1 embedding cache) until it has hit L2 a few times. Expected.
- Compile-job throughput is `4 × 2 = 8` concurrent LLM calls. Confirm your provider quota covers this.
- Rate-limit decisions are correct globally — do **not** add a per-replica rate limit on top.

### Topology H2: ≥3 API replicas + dedicated Postgres + PgBouncer + read replica (analytics)

Tier 4 baseline. Adds a connection pooler and a read replica.

**What runs where:**
- ≥3 Statewave API containers behind a load balancer.
- Dedicated Postgres primary (8+ vCPU, 32+ GB RAM, NVMe).
- PgBouncer (or managed pooler) in front of Postgres in **transaction mode**. Statewave's `STATEWAVE_DATABASE_URL` points at the pooler, not the primary.
- Postgres read replica — used today for **DR safety** and **ad-hoc analytics queries**, not for `/v1/context`. (See [What does not scale automatically → Read replicas](#read-replicas-are-not-auto-routed).)
- Observability: at this size, OpenTelemetry tracing (`pip install statewave[otel]`) is no longer optional in practice — without it, multi-instance diagnostics get expensive fast.

**Connection budget:** PgBouncer absorbs the `replicas × 15` into a smaller pool of actual backend connections. A pool of 30–60 backend connections typically serves 5–15 replicas comfortably. Tune via PgBouncer's `default_pool_size` and observe `SHOW POOLS` for wait counts.

**Diagnostics specific to this topology:**
- The `pg_stat_activity` view now shows PgBouncer's connection identity, not your replicas. Use PgBouncer's `SHOW CLIENTS` / `SHOW POOLS` for the per-replica picture.
- Compile-job throughput is `4 × R` — at `R=5` that's 20 concurrent LLM calls. Provider quota arithmetic, not Statewave arithmetic.
- A failed read-replica failover does **not** affect the API path today (it is not in the read path). It does affect analytics and DR posture.

### Topology H3 (future): Native read-replica routing

Documented here so you can plan around it. **Not implemented today.** Once `/v1/context` and other read-heavy endpoints can be routed to a replica:

- DB primary CPU drops materially for read-heavy workloads.
- Replica lag becomes a Statewave concern (today it isn't, because reads don't go there). Bounded staleness on `/v1/context` semantic search is acceptable; we will document the bound when we ship it.
- Connection-budget math will gain a "replica pool" line — plan for `replicas × pool` against **both** primary and replica.

Track progress on the [roadmap](../roadmap.md).

---

## Multi-instance diagnostics

Most of the diagnostic flow in [capacity-planning.md](capacity-planning.md) applies unchanged. The differences worth calling out:

### Per-instance vs. coordinated metrics

| Metric | Per-instance | Coordinated (one number across all replicas) |
|---|---|---|
| `pool_timeout` rate | ✅ each replica | — |
| API CPU / RAM | ✅ each replica | — |
| L1 embedding cache hit ratio | ✅ each replica | — |
| `/v1/context` p95 | ✅ each replica | — |
| Compile job backlog | — | ✅ from `/admin/jobs` |
| Webhook DLQ depth | — | ✅ from `/admin/webhooks/stats` |
| Rate-limit window state | — | ✅ shared in DB |
| L2 embedding cache hit ratio | — | ✅ from the `query_embedding_cache` table |

Common mistake: paging on a single replica's `pool_timeout` without checking the others. If one replica is hot and the rest are cold, your **load balancer** is the problem, not Statewave.

### Migrations under multi-instance deploys

`alembic upgrade head` must run **once per deploy**, not per replica. Pattern:

- A pre-deploy job / init container runs migrations and exits 0 before any new replica is admitted to the load balancer.
- Replicas come up after migrations complete; the startup schema guard (v0.7) will refuse to serve `/readyz=ok` if the schema is behind.
- Rolling deploys: keep replicas backwards-compatible across one schema version. The migration runbook is in [migrations.md](migrations.md).

Anti-pattern: each replica races to run `alembic upgrade head` at startup. This *will* work today (Alembic's version table is the lock), but it's noise in logs and slows rolling deploys. Use a pre-deploy step.

### Coordinated-shutdown gotcha

Compile jobs claimed by a replica that is `SIGTERM`ed mid-flight will be picked up by another replica after the per-job heartbeat timeout. This is by design — durability over speed. If you see jobs stuck in `running` for longer than a few minutes after a deploy, check `/admin/jobs?status=running` and the job's `claimed_at` timestamp; orphans recover automatically but slowly. Faster: trigger a manual reset (see [migrations.md](migrations.md)).

---

## Common multi-instance mistakes

In rough order of frequency:

1. **Forgetting connection-budget math.** Adding replicas without checking `max_connections`. Symptom: `too many connections for role` under burst. Fix: the formula above; switch to PgBouncer at scale.
2. **Adding a per-replica rate limit on top of the Postgres-backed one.** Doubles enforcement and confuses operators. Statewave's rate limit is already correct globally — leave it alone.
3. **Using sticky sessions.** No benefit (no per-session API state) and reduces L1 cache effectiveness. Use round-robin.
4. **Co-locating self-hosted models on API replicas.** GPU workloads belong to a separate tier with its own runbook. See [sizing.md → Tier 4](sizing.md#tier-4--enterprise--heavy-load).
5. **Provider quota not scaled with replica count.** `4 × R` concurrent LLM calls — multiply, then negotiate provider quota.
6. **Each replica running migrations at startup.** Use a pre-deploy migration step. See above.
7. **Treating a read replica as a `/v1/context` accelerator.** It is not, today. Use it for DR + analytics until native routing ships.
8. **Adding replicas before tuning the database.** A Postgres-bound system gets no faster from more API replicas. Walk the [capacity-planning checklist](capacity-planning.md) first.

---

## What we have *not* validated

To be plain, restated from [hardware-and-scaling.md](hardware-and-scaling.md#what-we-have-not-validated):

- We have not load-tested horizontal scaling under sustained high-RPS production traffic.
- We have not published per-topology throughput numbers — we do not have credible numbers to publish.
- We have not measured the exact replica-count breakpoint at which a transaction-mode pooler becomes mandatory; the "70% of `max_connections`" guideline above is operational arithmetic, not a measured threshold.

The guidance on this page derives from the system's design points — Postgres-backed coordination, the per-process LLM concurrency cap, the SQLAlchemy pool defaults, and operational experience with similar Postgres-backed services. If you have a specific scaling target you need confidence around, [open an issue](https://github.com/smaramwbc/statewave/issues) with the workload shape and we will prioritize what we benchmark.

---

## See also

- [Deployment Sizing Guide](sizing.md) — single-instance sizing, tier definitions, topology patterns
- [Capacity Planning & Tuning Checklist](capacity-planning.md) — symptom → action diagnostics
- [Hardware & Scaling](hardware-and-scaling.md) — GPU question and scaling characteristics
- [Migration & Upgrade Runbook](migrations.md) — schema migrations under multi-instance deploys
- [Deployment Troubleshooting](troubleshooting.md) — specific incident runbooks
- [Roadmap](../roadmap.md) — native read-replica routing and Helm chart
