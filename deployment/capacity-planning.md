# Capacity Planning & Tuning Checklist

A compact, operator-facing checklist for **"things are slow / load is growing — what do I do now?"**

This page is the diagnostic companion to the [Deployment Sizing Guide](sizing.md). Sizing tells you what to provision; this page tells you what to check, what to tune, and when to move up a tier.

---

## How to use this page

- Read top to bottom under pressure: each section is shorter than the one before it.
- **Cheap checks before expensive changes.** Don't scale Postgres before confirming the working set fits in RAM. Don't add API replicas before checking that DB CPU isn't already saturated.
- **Identify the layer first.** Statewave / Postgres / hosted provider / self-hosted model server are independently sized and independently tuned.

---

## First minute

Three things to check before anything else:

1. **`/readyz`** — confirms the API can talk to Postgres. If this is failing, nothing else matters.
   ```bash
   curl -fsS https://your-statewave/readyz
   ```
2. **DB CPU and RAM** — your managed Postgres dashboard, or `SELECT * FROM pg_stat_activity` for an active-query view. If DB CPU is pinned, the rest of the system is downstream of that.
3. **Compile job backlog** — pending vs. running vs. failed.
   ```bash
   curl -fsS -H "X-API-Key: $KEY" https://your-statewave/admin/jobs?status=pending | jq '.total'
   ```

If all three are healthy, the problem is most likely **outside Statewave** — your hosted LLM/embedding provider or your own model server. Skip to [Where the bottleneck is *not* Statewave](#where-the-bottleneck-is-not-statewave).

---

## Symptom → likely cause → first action

| Symptom | Likely cause | First action |
|---------|--------------|-------------|
| `/v1/context` p95 climbing | DB working set no longer hot in RAM, **or** repeat-task embedding cache is cold | Check pgvector index size vs. DB RAM; confirm same task strings are hitting the in-process query-embedding cache (warm machines first) |
| `/v1/context` cold-start latency only | Embedding-provider RTT for first-time task strings | Hosted: nothing to tune locally — provider is the floor. Consider self-hosted embeddings if egress/latency is a problem. |
| Compile backlog grows during the day | LLM compiler is the limiter — provider quota or the in-process 4-in-flight cap | Negotiate provider quota; **add a Statewave API replica** to multiply effective LLM concurrency |
| Compile jobs failing intermittently | Provider 429s or transient errors | Check provider rate-limit dashboard; lower episode batch cadence; the heuristic compiler is the always-available fallback |
| `pool_timeout` errors in API logs | Connection pool exhausted: too few SQLAlchemy connections, **or** DB `max_connections` too low for replicas | Raise SQLAlchemy `pool_size`/`max_overflow`; confirm `replicas × (pool_size + max_overflow) < db.max_connections` (with margin) |
| `distributed_rate_limit_db_error` warnings | Postgres connection slots saturated by per-request rate-limit checks | See [Troubleshooting STATEWAVE-TS-001](troubleshooting.md); switch to in-memory rate limit if running a single instance |
| Sustained DB CPU > 70% | Working set doesn't fit in RAM, vacuum is lagging, or HNSW search is paging | Tune autovacuum + `work_mem`; raise DB RAM before raising cores |
| Webhook DLQ growing | Receiver erroring or rate-limited; or subscriber too slow | Check the receiver's error rate and 5xx; scale subscribers; webhook event filters are on the v0.8 [roadmap](../roadmap.md) |
| API instances healthy but UX feels degraded | Latency floor is the embedding provider or your agent's own LLM | Trace one end-to-end request; verify `/v1/context` is not the long pole |
| `/readyz` reports queue degraded after upgrade | Orphaned in-flight compile jobs from old replica | Wait 30 min for self-recovery, or follow the reset path in [migrations.md](migrations.md) |

---

## What to check (with commands)

Use these probes in the order listed. Each is cheap.

### 1. Statewave API liveness and readiness
```bash
curl -fsS https://your-statewave/healthz   # liveness — process up?
curl -fsS https://your-statewave/readyz    # readiness — DB reachable, queue healthy?
```

### 2. Compile pipeline state
```bash
# Backlog (pending vs running vs failed)
curl -fsS -H "X-API-Key: $KEY" https://your-statewave/admin/jobs | jq '.[].status' | sort | uniq -c

# Recent failures
curl -fsS -H "X-API-Key: $KEY" 'https://your-statewave/admin/jobs?status=failed' | jq
```
Backlog growing = compiler can't keep up. Failures repeating = provider problem (or config), not capacity.

### 3. Webhook delivery
```bash
curl -fsS -H "X-API-Key: $KEY" https://your-statewave/admin/webhooks/stats | jq
```
DLQ depth should be small and stable. Rising DLQ = receiver-side issue.

### 4. Postgres health
```sql
-- Active queries and waits
SELECT pid, usename, state, wait_event_type, wait_event, query_start, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- Index sizes (HNSW on memories.embedding is the one to watch)
SELECT relname, pg_size_pretty(pg_relation_size(oid)) AS size
FROM pg_class
WHERE relkind = 'i'
ORDER BY pg_relation_size(oid) DESC
LIMIT 10;

-- Vacuum lag
SELECT relname, n_dead_tup, last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 10;

-- Connection usage
SELECT count(*) AS total,
       count(*) FILTER (WHERE state = 'active') AS active,
       count(*) FILTER (WHERE state = 'idle')   AS idle
FROM pg_stat_activity;
```
If the HNSW index size approaches your DB's RAM, semantic search starts paging — this is the most common Tier-3-and-up bottleneck.

### 5. External providers
- Hosted LLM/embeddings: check the provider's rate-limit and latency dashboards. 429s and elevated p99 there will surface as compile failures and `/v1/context` cold-start slowness here.
- Self-hosted model server: its own runbook applies (KV cache, batch size, queue depth). **It is not part of the Statewave API tier.**

---

## Tune before you scale

Order matters. Each step is cheaper than the next.

1. **Confirm your tier fit.** Re-read [sizing.md](sizing.md#tiers) — workload shape, not company size. Many "performance" complaints are tier mismatch, not tuning.
2. **Verify pgvector HNSW fits in DB RAM.** Index size from the SQL above ≪ Postgres RAM. If not, **raise DB RAM before adding cores or replicas.**
3. **Tune autovacuum and `work_mem`** before scaling DB. Default Postgres settings rarely match Statewave's read/write mix at Tier 3+.
4. **Verify embedding cache is warming.** First-time task strings pay one provider RTT; repeats are local. If your traffic is mostly fresh strings every time, that's a workload property — only a self-hosted endpoint changes it.
5. **Right-size the SQLAlchemy pool.** Current default is `pool_size=5, max_overflow=10` (per Statewave process). With `R` replicas, total possible connections = `R × 15`. Make sure DB `max_connections` covers that with headroom for migrations and admin tooling. Use a transaction-mode pooler (PgBouncer / managed equivalent) at Tier 4.
6. **Reduce compile cadence before scaling capacity.** If you're calling `/v1/memories/compile` on every request, you're doing more work than the product needs — compilation is idempotent and batches naturally. Schedule it.
7. **Move from bundled to managed Postgres** before splitting application topology. Postgres-on-the-app-VM is a Tier 1 pattern only.
8. **Add an API replica only after the above are done.** Replicas multiply effective LLM concurrency (per-process cap of 4 in-flight calls) and absorb burstier traffic, but do nothing for a Postgres-bound system.
9. **Add observability before adding topology.** OpenTelemetry tracing (optional `[otel]` extra), DB metrics, and provider dashboards make every later decision faster. Don't split topology without them.
10. **Isolate self-hosted model workloads.** If you've chosen self-hosted LLM/embeddings, give them their own machine and runbook. **Never co-locate the model server with the Statewave API tier.**

---

## When to move up a tier

Move up when **two or more** of the per-tier signals from [sizing.md](sizing.md) fire together. Single-signal upgrades usually mean the symptom-table action above is enough.

| Currently on | Move up when… | Move to |
|--------------|--------------|---------|
| **Tier 1 (Local / Dev)** | Putting it in front of real users; needing observability or persistence guarantees | [Tier 2](sizing.md#tier-2--small-production) |
| **Tier 2 (Small Production)** | Sustained DB CPU > 60%; subject count past a few thousand; HNSW index approaching DB RAM; multiple teams/tenants on a single instance | [Tier 3](sizing.md#tier-3--growing-production) |
| **Tier 3 (Growing Production)** | DB CPU > 70% after tuning; HNSW recall degrading; compile backlog persistent; multiple noisy-neighbor tenants | [Tier 4](sizing.md#tier-4--enterprise--heavy-load) |
| **Tier 4 (Enterprise)** | Single primary can't keep up after tuning, replica, and pooler; provider rate limits are the floor; compliance demands self-hosted models | Shard by tenant; add a self-hosted model sidecar; see the v0.7 horizontal-scaling guide on the [roadmap](../roadmap.md) |

---

## Where the bottleneck is *not* Statewave

Stop investigating Statewave when:

- **Postgres CPU/IO is healthy and `/readyz` is green, but `/v1/context` is slow.** It's almost always the embedding provider on cold task strings. Verify with a trace. The fix is on the provider side, or by switching to a self-hosted embedding endpoint — not by scaling Statewave.
- **Compile failures correlate with provider 429 dashboards.** That is the provider's quota, not the Statewave compiler. Negotiate quota; the heuristic compiler keeps running as the fallback.
- **A self-hosted model server is your LLM/embedding backend and it's slow or queueing.** Statewave's view of it is "any LiteLLM provider" — diagnose the model server with its own tools (vLLM/TGI/Ollama metrics), not via Statewave.
- **Your agent's own LLM is the long pole.** Statewave returns the assembled context bundle; what your agent does with it is governed by your agent. Trace end-to-end, not Statewave-only.

These are not failures of Statewave to scale — they are the layer being saturated showing through. Treat each layer as an independent product.

---

## See also

- [Deployment Sizing Guide](sizing.md) — tier-by-tier hardware profiles
- [Hardware & Scaling](hardware-and-scaling.md) — GPU question and scaling characteristics
- [Deployment Troubleshooting](troubleshooting.md) — specific incident runbooks
- [Migration & Upgrade Runbook](migrations.md) — operational hygiene during upgrades
- [Compiler Modes](../architecture/compiler-modes.md) — heuristic vs LLM cost shape
- [Privacy & Data Flow](../architecture/privacy-and-data-flow.md) — what each layer sends where
