# Sensitivity labels & per-memory policy bindings

Statewave's policy layer lets an operator decide, per memory and per
caller, whether a memory is allowed to influence an assembled context.
The decision lives in a **policy bundle** — a versioned, content-hashed
YAML (or JSON) document — that the server consults on every assembly
call. Decisions are always recorded into the
[state-assembly receipt](./receipts.md)'s `policy.filters_applied`
block; whether they're *enforced* (memory dropped or redacted) is
governed by a tenant-level config flag.

Tracked in issue
[#50](https://github.com/smaramwbc/statewave/issues/50). Builds on the
receipt infrastructure from
[#49](https://github.com/smaramwbc/statewave/issues/49).

## Core concepts

- **Sensitivity labels** — per-memory capability tags like `pii`,
  `financial`, `secret`. Operator-supplied via the admin app or
  `PATCH /v1/memories/{id}/labels`. Stored as `TEXT[]` with a GIN
  index so the policy evaluator's overlap check is cheap on the hot
  path.
- **Policy bundle** — a YAML document with a list of rules. Each rule
  has an `id`, a `when:` predicate block, and an `action: deny |
  redact`. Bundles are content-hashed at load time, immutable, and
  stored in `policy_bundles`.
- **Active bundle** — at most one per (tenant or global) scope. The
  resolver checks tenant-specific first, then falls back to global.
- **Policy mode** — `tenant_configs.config.policy_mode` is either
  `log_only` (default) or `enforce`. log_only records decisions
  without filtering; enforce drops denied memories and redacts the
  ones flagged `redact`.

## Receipt vs policy responsibilities

The receipt records *what happened*. The policy decides *what should
happen*. They split as follows:

| Concern | Layer | Field |
|---|---|---|
| Which memories were selected? | receipt | `selected_entries` |
| What labels did they carry? | memory | `memories.sensitivity_labels` (queryable; not yet inlined on `selected_entries`) |
| What labels were suggested but not yet promoted? | memory | `memories.suggested_labels` (v0.9 — advisory only, policy ignores) |
| Which rules fired? | policy → receipt | `policy.filters_applied` |
| Which rules ran but didn't fire? | policy → receipt | `policy.filters_skipped` |
| What policy was in effect? | policy → receipt | `policy.policy_bundle_hash` |
| Was the response actually filtered? | tenant config | `policy.mode` (`log_only` vs `enforce`) |
| Who was asking? | request | receipt's `caller_id` + `caller_type` |

## Bundle format

```yaml
version: 1
metadata:
  description: "Production policy v3"
  authored_by: "security-team@example.com"
rules:
  - id: deny-pii-for-marketing-tools
    description: "PII memories cannot be read by marketing tools"
    when:
      memory_has_any_label: [pii, sensitive_personal]
      caller_type: marketing_tool
    action: deny

  - id: redact-secrets-for-non-admin
    when:
      memory_has_any_label: [secret, api_key]
      caller_type_not_in: [admin, security]
    action: redact
```

### Predicates (v1)

| Predicate | Type | Semantics |
|---|---|---|
| `memory_has_any_label` | `list[str]` | Memory's labels overlap the list (disjunctive) |
| `memory_has_all_labels` | `list[str]` | Every listed label is on the memory (conjunctive) |
| `caller_type` | `str` | Exact match on the request's `caller_type` |
| `caller_type_in` | `list[str]` | List membership |
| `caller_type_not_in` | `list[str]` | Negated list membership |
| `caller_id` | `str` | Exact match on the request's `caller_id` |

All predicates within a single `when:` are **AND**-ed. A rule with no
predicates is a load-time validation error.

### Actions (v1)

- `deny` — under `enforce` mode the memory is excluded from
  `selected_entries`. The receipt records the deny.
- `redact` — under `enforce` mode the memory's `content` is replaced
  with `[REDACTED by policy]` before delivery. The memory still
  appears in `selected_entries` so the receipt records the redaction.

Regex predicates and explicit `allow` overrides are deferred to v2 —
the schema reserves the space so they can be added without a version
bump.

### First match wins

Rules are evaluated in declaration order. The first matching rule's
action is applied; no later rule fires. A memory matching no rule
falls through to default-allow.

## Caller identity

`caller_id` and `caller_type` are optional fields on `POST
/v1/context` and `POST /v1/handoff`. They default to `null` (the
caller is anonymous). Tenants that want policy enforcement to be
non-bypassable flip
`tenant_configs.config.require_caller_identity: true`; thereafter,
calls without both fields return `401`.

The fields are recorded on the receipt body so a reviewer can answer
"who triggered this assembly?" without joining against an external
log.

## Log-only vs enforce

v1 of the policy layer ships in **log_only mode by default**. This
is the load-bearing safe-rollout property: when a tenant flips on
the policy layer, every assembly call still returns the same data it
returned the day before, but the receipt now records *what would
happen* under enforce. After a few days of audit-log review,
operators flip `policy_mode: enforce` and the same receipts start
recording real filter decisions.

Without log-only, the day a tenant enabled policy they'd risk a
silent data-availability regression on every under-tagged memory.
With it, that risk is observable for as long as the operator wants
before flipping the switch.

## Endpoints

### Memory labels

```
PATCH /v1/memories/{memory_id}/labels
```

Body:
```json
{ "sensitivity_labels": ["pii", "financial"] }
```

Server normalises (deduplicate, lowercase, trim whitespace) and caps
at 32 entries. Empty list clears all labels (memory becomes untagged
→ default-allow under any policy).

The admin app reaches the same code path via
`PATCH /admin/memories/{memory_id}/labels?tenant_id=...` — the proxy
allowlist stays scoped to `/admin/*` by design.

### Policy bundles (admin)

```
POST   /admin/policy/bundles
GET    /admin/policy/bundles
GET    /admin/policy/bundles/{bundle_hash}
POST   /admin/policy/activate
POST   /admin/policy/reload
GET    /admin/policy/active
```

`POST /admin/policy/bundles` validates the YAML at upload time;
malformed bundles return `400` with the parser message. `POST
/admin/policy/activate` flips a bundle to active for its scope and
busts the in-process cache. `POST /admin/policy/reload` busts the
cache without changing activation — used after direct DB fix-ups
during incident response.

The bundle YAML is content-hashed; submitting the same logical rules
twice returns the same hash. This is what makes "what did policy
`abc123` say on date Y?" answerable forever — the receipt's
`policy.policy_bundle_hash` is a stable, addressable pointer.

## Acceptance criteria (#50)

The integration test suite verifies four load-bearing failure modes:

1. **Sensitive memory delivered to disallowed caller** — under
   `enforce`, a memory labelled `pii` does not appear in the
   assembled context when the caller is `marketing_tool` AND the
   receipt records the deny.
2. **Filtered memory influences ranking** — denied memories are
   removed before scoring, not after, so they cannot leak through
   ranking signals.
3. **Policy version bump invalidates audit replay** — two assembly
   calls under different bundles record different
   `policy_bundle_hash` values; old receipts pin the old hash.
4. **require_caller_identity enforced** — when the tenant config
   flag is on, unidentified callers return 401.

## SDKs

**Python:**
```python
from statewave import StatewaveClient

c = StatewaveClient(tenant_id="acme", api_key="...")
c.set_memory_labels("mem-id-123", ["pii", "financial"])
bundle = c.get_context(
    subject_id="user-42",
    task="...",
    caller_id="agent-7",
    caller_type="support_agent",
    emit_receipt=True,
)
```

**TypeScript:**
```ts
import { StatewaveClient } from "@statewavedev/sdk";

const c = new StatewaveClient({ tenantId: "acme", apiKey: "..." });
await c.setMemoryLabels({
  memoryId: "mem-id-123",
  sensitivityLabels: ["pii", "financial"],
});
const bundle = await c.getContext({
  subjectId: "user-42",
  task: "...",
  callerId: "agent-7",
  callerType: "support_agent",
  emitReceipt: true,
});
```

## Shipped after v0.8

- **Heuristic auto-labeling** ([#158](https://github.com/smaramwbc/statewave/issues/158)) — v0.9 added an opt-in pipeline that stamps advisory `suggested_labels` on memories at compile time (PII email/phone, financial card with Luhn, secret tokens). The policy evaluator **does not read** this column; promotion into authoritative `sensitivity_labels` is an explicit operator action via the admin app. See [`docs/auto-labeling.md`](https://github.com/smaramwbc/statewave/blob/main/docs/auto-labeling.md). The "v1 is operator-supplied only" stance still applies to the authoritative column.
- **Operator review + promote workflow** ([#160](https://github.com/smaramwbc/statewave/issues/160)) — v0.9 added `POST /admin/memories/{id}/promote-labels` (review-only; ad-hoc writes refused) plus a `/suggested-labels` page in the admin app. Promotions are audit-trailed on `memory.metadata.label_promotions`.

## Still out of scope

- **Visual policy editor in the admin app** — v0.9 surfaces YAML upload + bundle list + activate; authoring stays in YAML in git. Deferred beyond v1.0 (see [roadmap](roadmap.md)) — originally planned for v0.9, kept out to keep the v0.9 release focused on the audit + replay + residency story.
- Cross-tenant policy sharing.
- Regex predicates (`caller_id_pattern`, `memory_content_pattern`).
- Explicit `allow` rules — uses default-allow + `deny`/`redact`.
- Per-rule audit metadata (last-fired timestamp, hit counts).
- Human-approval workflows for memory-promotion gating.

## See also

- [State-assembly receipts](./receipts.md) — the audit artifact the
  policy layer populates.
- [v1 API contract — labels + policy endpoints](./api/v1-contract.md)
- [Issue #50 on GitHub](https://github.com/smaramwbc/statewave/issues/50)
- [Issue #49 — receipts](https://github.com/smaramwbc/statewave/issues/49)
