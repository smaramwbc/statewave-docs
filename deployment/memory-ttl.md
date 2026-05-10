# Memory TTL

Per-kind expiry windows for memories. When you configure a TTL for a memory `kind`, every newly-compiled memory of that kind gets a `valid_to` stamped at `valid_from + ttl_days`. Once `valid_to` has passed, the memory:

- **stops appearing in `/v1/context`** immediately (the retrieval filter is `(valid_to IS NULL OR valid_to > now())`);
- **transitions to `status = 'tombstoned'`** on the next hourly cleanup pass;
- **stays in the database** — soft-delete only, so the source remains resolvable for audits and for the receipts surface tracked in [issue #49](https://github.com/smaramwbc/statewave/issues/49).

> **Scope:** v0.7 ships **per-kind global** TTL only. Per-subject, per-tenant, and per-policy expiry rules belong to the policy layer being designed in [issue #50](https://github.com/smaramwbc/statewave/issues/50). Once that layer lands, the per-kind windows here become its default-fallback rule — no migration owed.

---

## Config

One env var, JSON-encoded:

```bash
STATEWAVE_KIND_TTL_DAYS='{"episode_summary":30,"profile_fact":365}'
```

Rules:

| Input | Effect |
|---|---|
| Empty / unset (default) | No expiry for any kind. Backwards-compatible. |
| Kind not listed | No expiry for that kind. |
| Positive integer | Memory of that kind expires `N` days after `valid_from`. |
| Zero or negative | Validator rejects at startup. **To disable expiry for a kind, leave it out of the dict** — explicit zero is treated as a misconfiguration. |
| Non-integer value | Validator rejects at startup. |
| Invalid JSON | Validator rejects at startup with the JSON parse position. |

The validator runs at process start, not at first memory insert — misconfiguration surfaces loudly in your boot logs instead of silently nine hours into a workload.

### Configuring via the Helm chart

The chart's `extraEnv` field passes any `STATEWAVE_*` env var through:

```yaml
extraEnv:
  - name: STATEWAVE_KIND_TTL_DAYS
    value: '{"episode_summary":30,"profile_fact":365}'
```

### Configuring via Docker Compose

Add to the `api.environment:` block in `docker-compose.yml`, or set in your host `.env`:

```yaml
api:
  environment:
    STATEWAVE_KIND_TTL_DAYS: '{"episode_summary":30,"profile_fact":365}'
```

### Configuring via Fly / Railway

Set as a secret / env var the same way you set `STATEWAVE_API_KEY`. Quoting matters — your platform's env-var input usually accepts the JSON literal as-is.

---

## What kinds exist?

The default kinds shipped by the project compilers:

| Kind | Source | Typical TTL choice |
|---|---|---|
| `profile_fact` | Profile-shaped statements ("name is X", "works at Y") | Long or none — these are durable user facts |
| `episode_summary` | Compressed conversation / event summaries | Medium (30–180d) — the freshness window your agent actually uses |
| `procedure` | Repeatable how-to extracted from interactions | Long or none — operationally useful indefinitely |
| `artifact_ref` | Pointers to external artifacts (URLs, IDs) | Short (7–30d) — references decay quickly |

These are recommendations, not contracts. Pick TTLs that match how stale you're willing to let each kind get before it stops influencing retrieval. Start permissive (longer TTLs) and tighten if you see noise in `/v1/context`.

---

## Backfill behaviour

**Existing memories are not retroactively stamped.** When you set a TTL for a kind for the first time (or change it), only **newly-written memories of that kind** get the new `valid_to`. Memories already in the database keep their existing `valid_to` (NULL or the value set at insert).

If you want to apply a fresh TTL to existing memories, that's a one-shot operator action. The general shape:

```sql
-- Forward-fill TTL for a kind that did not have one configured before.
UPDATE memories
SET valid_to = valid_from + INTERVAL '30 days'
WHERE kind = 'episode_summary'
  AND valid_to IS NULL
  AND status = 'active';
```

Test against a non-production database first. The cleanup loop will tombstone any rows whose new `valid_to` is now in the past on the next hourly pass.

---

## How retrieval enforces TTL

The load-bearing constraint is **the retrieval filter**, not the cleanup loop. Three repository functions in `server/db/repositories.py` apply `(valid_to IS NULL OR valid_to > now())`:

- `search_memories` — used by `/v1/context` for kind-filtered fetches
- `search_memories_by_embedding` — used by `/v1/context` semantic search
- `list_active_memories_by_subject` — used by conflict resolution

This means: **the moment `valid_to` passes**, the memory is invisible to retrieval. Operators do not have to wait for the hourly cleanup pass; cleanup is a backstop that brings the row's `status` field in line so downstream consumers (admin dashboard, the receipts surface in #49) see consistent state.

> **Why both?** The retrieval filter handles correctness — no expired memory ever influences `/v1/context`. The cleanup pass handles operability — the `status` column reflects reality, not just the `valid_to` timestamp, so admin dashboards and audit receipts read clean values.

---

## Cleanup loop behaviour

The hourly `_cleanup_loop` in `server/app.py` already runs ephemeral-subject cleanup, compile-job retention, and rate-limit-window cleanup. With TTL configured, it gains a fourth pass:

```sql
UPDATE memories
SET status = 'tombstoned'
WHERE status = 'active'
  AND valid_to IS NOT NULL
  AND valid_to < now();
```

Single atomic statement, replica-safe. The pass is skipped entirely when `STATEWAVE_KIND_TTL_DAYS` is unset/empty — no overhead for deployments that don't use TTL.

The cleanup loop activates if **any** of these are configured: snapshots, compile-job retention, distributed rate limiting, or memory TTL.

---

## What TTL does NOT do (yet)

- **Hard-delete.** Tombstoned rows persist. Storage reclamation is a separate operator knob; v0.8+ may add `STATEWAVE_TOMBSTONE_PURGE_DAYS` to delete tombstoned rows older than a grace window. Until then, large deployments with aggressive TTLs should plan for steady storage growth.
- **Per-subject TTLs.** "Memories under subject `customer:acme` expire after 7 days; everywhere else after 90." This is the policy layer's job ([#50](https://github.com/smaramwbc/statewave/issues/50)) — TTL deliberately stays coarse so the simple primitive composes cleanly when policies arrive.
- **Per-tenant TTLs.** Same as per-subject — policy layer.
- **Sliding-window expiry.** TTL is computed from `valid_from` (= the source episode's timestamp), not from "last access". A memory that's heavily used and a memory that's never read both expire at the same time. If you need usage-based retention, that's a separate roadmap item.
- **Per-memory TTL overrides on insert.** The compiler stamps `valid_to` based on the kind's configured TTL. SDKs cannot set a custom TTL per memory.
- **Restore-time stamping.** Snapshots, backups, and memory packs preserve the original `valid_to` from the source data. Re-stamping at restore time would change semantics — restore is not the same as ingest.

---

## Compatibility notes

### `MemoryStatus` enum

The Python `MemoryStatus` enum changed from `active | superseded | deleted` to `active | superseded | tombstoned` in this release. Two things to know:

- The previous `deleted` value was aspirational — no code path ever wrote it (verified via grep across the v0.6.0 codebase).
- Alembic migration `0016_memory_status_tombstoned` defensively transitions any stray `'deleted'` rows to `'tombstoned'`. The downgrade reverses the rename.

The Python and TypeScript SDKs do not currently expose `MemoryStatus` as a public symbol, so no breaking change for SDK consumers.

### Coexistence with conflict resolution

Conflict resolution writes to `valid_to` when one memory supersedes another (it sets the older memory's `valid_to` to the new one's `valid_from`). TTL writes to `valid_to` to encode "expires after N days". Both uses share the same column with the same semantic — "no longer authoritative as of T" — and the cleanup pass intentionally skips memories with `status = 'superseded'` so superseded rows are never re-stamped as `tombstoned`.

---

## See also

- [Deployment Sizing Guide](sizing.md) — TTL choices interact with retention sizing
- [Capacity Planning & Tuning Checklist](capacity-planning.md)
- [Migration & Upgrade Runbook](migrations.md) — schema migration handling for the `0016` rename
- [Issue #49 — state-assembly receipts](https://github.com/smaramwbc/statewave/issues/49)
- [Issue #50 — sensitivity labels and per-memory policy bindings](https://github.com/smaramwbc/statewave/issues/50)
- [Roadmap](../roadmap.md)
