# State-assembly receipts

A **state-assembly receipt** is a compact, immutable record of which
state entries — memories and episodes — influenced a single context
assembly. One receipt per assembly call; addressable by ULID;
queryable by id or by `(subject_id, time_range)` with a stable cursor.

Receipts make Statewave's accountability story **emittable** rather
than *reconstructable*. The underlying primitives — provenance,
lineage, validity intervals, supersession, conflict resolution — have
existed since the v0.x lines, but reading them required walking the
joins after the fact and trusting that the assembly code hadn't
changed since the call happened. A receipt collapses reconstruction
into a single artifact written at the moment of assembly.

## When to use receipts

- **Compliance audits** — regulators want byte-level proof of what an
  agent saw at decision time. The receipt's `output.context_hash`
  matches the exact bytes delivered.
- **Replay & forensics** — a customer complaint about an agent's
  answer can be traced back to the receipt, then to each memory and
  episode that fed the answer.
- **Drift detection** — comparing receipts across deployments surfaces
  silent regressions where the same query starts pulling different
  state.
- **Eval harnesses** — the `statewave-bench` runs benefit from
  emitting receipts so the eval transcript can verify ranking decisions
  against a fixture.

## How emission is decided

Per request, the server runs a single decision function over four
inputs in this order:

1. **Env kill-switch** — `STATEWAVE_RECEIPTS_DISABLED=true` blocks all
   emission. Operational hygiene only.
2. **Policy force-on** — reserved for the
   [sensitivity-label policy layer](https://github.com/smaramwbc/statewave/issues/50)
   sibling work. Returns "no opinion" today.
3. **Per-tenant config** — `tenant_configs.config.receipts` set to
   `always` | `on_request` | `never`. `always` and `never` override
   the per-request flag. Default `on_request`.
4. **Per-request flag** — `emit_receipt: true` on the assembly call.
   Default `false`.

The decision lives in one function (`server/services/receipts.py`).
Both `POST /v1/context` and `POST /v1/handoff` call into it; if a
future assembly surface is added it goes through the same gate.

## Receipt schema

Receipts use a **strict-superset** shape with a `mode` discriminator.
Every field is always present; optional ones are nullable. v1 ships
one mode (`"retrieval"`). Future modes (`as_of_replay`, `eval_run`)
can extend without a schema break.

```yaml
receipt_id:            # ULID — addressable, chainable
parent_receipt_id:     # nullable ULID — chain multi-step tasks
mode:                  # "retrieval" in v1
query_id:              # caller-supplied or null
task_id:               # caller-supplied or null
tenant_id:
subject_id:
task:
as_of:                 # timestamp the assembly resolved against
created_at:            # when the receipt itself was written

selected_entries:
  - type:              # "memory" | "episode"
    memory_id:         # (memory entries)
    kind:
    valid_from:
    valid_to:
    supersession_status:    # active | superseded | tombstoned
    source_episode_ids: []
    provenance_hash:        # sha256 over the sorted source episode ids
    fact_key:               # for conflict grouping (null until #50)
    conflict_status:        # none | merged | overridden | unresolved
    rank:                   # final position in the bundle
    score:
  - type: episode
    episode_id:
    source:
    event_type:
    occurred_at:
    rank:

policy:
  policy_bundle_hash:   # null until #50 wires the policy layer
  filters_applied: []   # empty until #50
  filters_skipped: []   # empty until #50
  mode:                 # log_only | enforce — always log_only in v1

output:
  context_hash:               # sha256 of the bytes delivered to the agent
  context_size_bytes:
  canonicalization_version:   # bump if canonicalization rules change
  token_estimate:

region:                # populated when tenant config sets a region
receipt_signature:     # reserved for v2 HMAC tamper-evidence
```

## What the failure modes look like

Receipts make six categories of failure mode detectable from the
receipt alone, with no access to assembly internals:

1. **Stale fact selected** — an entry's `valid_to` is in the past but
   it appears in `selected_entries`.
2. **Superseded memory included** — an entry has
   `supersession_status: superseded`.
3. **Tombstoned memory resurrected** — an entry has
   `supersession_status: tombstoned`.
4. **Conflicting entries merged without flag** — two entries share a
   `fact_key` but neither is marked `conflict_status: merged`.
5. **As-of fall-back** — caller asked for one `as_of`, receipt records
   a different one.
6. **Byte tampering** — recomputed sha256 over the response's
   `assembled_context` does not match `output.context_hash`.

The server's unit-test suite (`tests/test_receipts.py`) phrases each
of these as a deterministic assertion against a receipt body.

## Calling from the SDKs

**Python:**

```python
from statewave import StatewaveClient

c = StatewaveClient(tenant_id="acme", api_key="...")
bundle = c.get_context(
    subject_id="user-42",
    task="What plan is the customer on?",
    emit_receipt=True,
)
if bundle.receipt_id:
    receipt = c.get_receipt(bundle.receipt_id)
    print(receipt.output["context_hash"])
```

**TypeScript:**

```ts
import { StatewaveClient } from "@statewavedev/sdk";

const c = new StatewaveClient({ tenantId: "acme", apiKey: "..." });
const bundle = await c.getContext({
  subject_id: "user-42",
  task: "What plan is the customer on?",
  emit_receipt: true,
});
if (bundle.receipt_id) {
  const receipt = await c.getReceipt(bundle.receipt_id);
  console.log(receipt.output.context_hash);
}
```

## Storage & retention

Receipts live in a dedicated `receipts` table — not in the webhook
event stream (which has delivery-retry semantics that don't fit an
audit log) and not as inline JSON on the assembly response. Writes go
through service code only; no service-code path issues
`UPDATE` or `DELETE`. Operators wanting hard tamper-evidence at the
storage layer should grant the service DB role `INSERT`+`SELECT` only
on this table.

Retention is **tenant-controlled** via
`tenant_configs.config.receipt_retention_days`. `0` (the default)
means forever; a positive integer enables a scheduled purge worker.
v1 ships the configuration surface; the worker itself is a follow-up.

## Failure mode

If a receipt write fails (DB error, JSON serialization edge case),
the assembly call still **succeeds** and the bundle is still
returned. The response carries `receipt_id: null, receipt_emitted:
false` and a structured log records the failure. Receipts are an
audit artifact; they must not break agent serving.

## What's coming in v2

- [Sensitivity-label policy layer](https://github.com/smaramwbc/statewave/issues/50)
  — fills `policy.filters_applied` and lets receipts record what was
  filtered and why.
- HMAC signing of receipt bodies (`receipt_signature` column already
  reserved).
- Scheduled retention-purge worker reading
  `tenant_configs.config.receipt_retention_days`.
- Review-time redaction UI in the admin app.
- Receipt-driven replay (`as_of_replay` mode) for time-travel
  debugging.

## See also

- [v1 API contract — receipt endpoints](./api/v1-contract.md)
- [Issue #49 on GitHub](https://github.com/smaramwbc/statewave/issues/49)
- [Issue #50 — sensitivity labels & policy](https://github.com/smaramwbc/statewave/issues/50)
