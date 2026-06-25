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
- **Eval harnesses** — benchmark runs benefit from
  emitting receipts so the eval transcript can verify ranking decisions
  against a fixture.

## How emission is decided

Per request, the server runs a single decision function over four
inputs in this order:

1. **Env kill-switch** — `STATEWAVE_RECEIPTS_DISABLED=true` blocks all
   emission. Operational hygiene only.
2. **Policy force-on** — reserved for the
   [sensitivity-label policy layer](./sensitivity-labels.md). v1 of
   the policy layer returns "no opinion" on the emission gate; it
   *does* fill `policy.filters_applied` and `policy.policy_bundle_hash`
   on the body of receipts that are emitted for other reasons.
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
Every field is always present; optional ones are nullable. v0.8 added
`"retrieval"` (covers both `/v1/context` and `/v1/handoff` emissions);
v0.9 added `"as_of_replay"` (emitted by [`POST /v1/receipts/{id}/replay`](https://github.com/smaramwbc/statewave/blob/main/docs/replay.md)). Future modes (`eval_run`) can extend
without a schema break.

```yaml
receipt_id:            # ULID — addressable, chainable
parent_receipt_id:     # nullable ULID — set on as_of_replay receipts pointing at the parent
mode:                  # "retrieval" | "as_of_replay"
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

region:                            # set from STATEWAVE_REGION in multi-region mode (v0.9)
receipt_signature:                  # HMAC-SHA256 over the canonical body (v0.9, nullable for unsigned)
receipt_signature_key_id:           # operator key id used to sign (v0.9, nullable for unsigned)
receipt_signature_algorithm:        # e.g. "hmac-sha256-canonical-v1" (v0.9, nullable for unsigned)
policy_snapshot:                    # embedded policy YAML + hash + captured_at (v0.9, nullable for pre-v0.9 receipts)
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
  subjectId: "user-42",
  task: "What plan is the customer on?",
  emitReceipt: true,
});
if (bundle.receiptId) {
  const receipt = await c.getReceipt(bundle.receiptId);
  console.log(receipt.output.contextHash);
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

## What v0.9 added

- **HMAC signing** ([#157](https://github.com/smaramwbc/statewave/issues/157)) — body signed with `hmac-sha256-canonical-v1` under tenant-scoped operator-provided keys. `GET /v1/receipts/{id}/verify` returns `{valid: true | false | null, key_id, algorithm, reason}` with constant-time compare. Pre-v0.9 receipts verify cleanly as `no_signature`.
- **Scheduled retention worker** ([#156](https://github.com/smaramwbc/statewave/issues/156)) — hourly tombstones receipts past `tenant_configs.config.receipt_retention_days`. Soft-delete; rows persist for forensic lookup.
- **Receipt-driven replay** ([#159](https://github.com/smaramwbc/statewave/issues/159)) — `policy_snapshot` embeds the active bundle's YAML on every receipt; `POST /v1/receipts/{id}/replay` re-runs the retrieval against current memories with the original policy and returns a structural diff envelope. Reference: [`docs/replay.md`](https://github.com/smaramwbc/statewave/blob/main/docs/replay.md).
- **Auto-labeling** ([#158](https://github.com/smaramwbc/statewave/issues/158)) — heuristic detectors stamp advisory `suggested_labels` (kept separate from authoritative `sensitivity_labels`). Operator review + explicit promotion via the admin app ([#160](https://github.com/smaramwbc/statewave/issues/160)).
- **Residency** ([#161](https://github.com/smaramwbc/statewave/issues/161)) — `STATEWAVE_REGION` + `tenant_configs.config.region` enforced at the application layer; receipts stamp the local region for end-to-end audit.

## Still out of scope

- Review-time redaction UI in the admin app.
- Cross-tenant / cross-region federated audit search (see [`docs/residency.md`](https://github.com/smaramwbc/statewave/blob/main/docs/residency.md) for the explicit-not-implicit stance).
- KMS / Vault-backed signing (v0.9 reads keys from env / secret-manager mount; the architecture is compatible with swapping the key resolver behind the same `receipt_signing_keys` settings field).
- Asymmetric signatures (the `algorithm` field reserves space for `ed25519-canonical-v1` etc.; v0.9 ships HMAC only).
- Byte-for-byte historical replay (memory snapshots). v0.9 ships *current code + original policy*; the data model leaves room for memory snapshots without a schema break.

## See also

- [v1 API contract — receipt endpoints](./api/v1-contract.md)
- [Issue #49 on GitHub](https://github.com/smaramwbc/statewave/issues/49)
- [Issue #50 — sensitivity labels & policy](https://github.com/smaramwbc/statewave/issues/50)
