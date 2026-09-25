# Provenance source signing

> **Status:** draft RFC, not implemented. This page specifies an opt-in
> convention only — no Ed25519 verification, trust table, or
> `verification` field exists in Statewave core yet.

Statewave's provenance records *where a memory came from*. This page defines
an **opt-in convention** that upgrades one specific claim inside that
provenance from *asserted* to *verifiable*: "this content was authored by the
source system that supplied it". The convention lives entirely inside the
free-form `provenance` dict on episodes — no schema change, no cost for
sources that ignore it.

Tracked in issue
[#408](https://github.com/smaramwbc/statewave/issues/408).

## The problem: claimed vs verifiable authorship

Every episode carries a `source` string and a free-form `provenance` dict.
Both are written by whoever supplies the episode — the connector, the SDK
caller, the importing script. A consumer reading a compiled memory can see
`provenance.source = "acme-crm"` the same way it can see any other field:
as a **claim**, not evidence. If an operator needs to know that a memory
really originated in the CRM — that a prompt-injected agent or a compromised
connector did not invent the fact — a self-reported string cannot answer
that.

Source signing closes the gap: the source system signs the exact episode
payload it authored with a key the *operator* has whitelisted for that
connector. Statewave never trusts the signer's word about which key is
legitimate; trust flows from operator configuration, not from the writer.

## When to use source signing

- **Regulated or audit-bound deployments** — reviewers ask "prove this
  memory in the audit trail came from the CRM, not from the agent".
- **Multi-connector subjects** — several sources feed one subject;
  verification distinguishes what each one actually attested.
- **Adversarial ingestion paths** — the writer (agent, pipeline) is less
  trusted than the reader, and the operator wants the trust anchor on the
  source side.
- **Not useful** when the source and the reader are the same party, or
  when provenance only needs to be displayed, not proven.

## What gets signed: episodes, not memories

Memories are **derived** at compile time — a source system never authors
one, so a source can never sign one. The signable object is the
**episode**: the raw record the source actually handed over.

The JCS (RFC 8785) canonicalization of the signed episode covers exactly
the fields the source is in a position to attest:

```json
signed = {
  "v": 1,
  "subject_id": "...",
  "idempotency_key": "...",
  "occurred_at": "2026-09-24T12:00:00Z",
  "source": "...",
  "key_id": "src:acme-crm:2026-09",
  "alg": "Ed25519",
  "payload": { ...episode payload as supplied... }
}
signature = Ed25519.sign(source_private_key, JCS(signed))
```

- The canon is the RFC 8785 (JCS) canonicalization of the entire
  `signed` object — sorted keys, no whitespace, UTF-8. A colon-joined
  string would be delimiter-ambiguous (`repo:acme` + `widgets:doc1` is
  byte-for-byte equal to `repo:acme:widgets` + `doc1`, so a signature
  could lift from one subject onto another); object canonicalization
  removes the ambiguity because fields live in JSON structure, not in a
  concatenation.
- The signature covers `source`, `key_id`, and `alg` as well: a trusted
  key must not be able to sign a payload that is later shown under a
  different `source`, and the read path can surface the verifying
  `key_id`.
- `idempotency_key` is the source's own record id (the same key that
  makes ingest idempotent). It is what the source can guarantee across
  retries — a regenerated episode UUID cannot.
- `occurred_at` is a timezone-aware RFC 3339 UTC string and stays inside
  the signed object: binding the claimed time into the signature is the
  point, so ingest-time tampering with `occurred_at` breaks the
  signature. Naive timestamps are not signable — `occurred_at` is
  optional on ingest (it defaults to `now()`), but a signed episode
  carries its own aware value.
- Episodes without an `idempotency_key` cannot carry a meaningful source
  signature (the source would be signing an object it cannot
  re-identify); such episodes are simply never signed.

## Where the signature lives

```json
episode.provenance.signature = {
  "key_id": "src:acme-crm:2026-09",
  "alg": "Ed25519",
  "sig": "<128-char hex, over canon above>"
}
```

- `key_id` — opaque to Statewave; meaningful only to the operator's trust
  table. Convention, not scheme: rotating a key changes `key_id`, not the
  field shape.
- `alg` — v1 accepts only `Ed25519`. The field exists so a future
  algorithm change is not a schema break.
- The signature covers the payload bytes, not the whole episode row: the
  server-generated `id` and `created_at` must not be part of what the
  source attests, since the source cannot know them at sign time.

## Key distribution, rotation, and verification

**Trust table.** The operator configures, per connector, which `key_id`s
are trusted and their public keys. Statewave never sees private keys.

**Rotation.** Add the new `key_id` to the trust table, keep the old one
valid for a configurable grace window, then prune. No revocation list in
v1 — a rotated-out key simply stops verifying after the grace window.

**Verification timing.** Verification runs **at read time** against the
current trust table, never at ingest and never persisted. Two
consequences, both deliberate:

- late-arriving key configurations still work (verify first, configure
  moments later);
- key changes apply **retroactively** — an episode that verified yesterday
  becomes `unverified` today if its key leaves the trust table. That is
  the honest behavior; caching the status would lie about what the
  operator currently trusts.

**Read path.** Read responses gain an optional `verification` field per
episode and per memory: `verified | unverified | unsigned`.

- `verified` — a signature present, algorithm accepted, `key_id` in the
  trust table, signature valid over the JCS canonicalization recomputed
  from stored bytes.
- `unverified` — a signature present but failing any of the above
  (mismatched bytes, unknown-algorithm, pruned key).
- `unsigned` — no signature was ever supplied (the field is absent).
  A separate bucket: deployments that have not adopted signing report
  `unsigned` (neutral), NOT `unverified` (which means a signature
  failed).

## Propagation to derived memories

A memory is not signed by the source, and it doesn't need to be: it
inherits verification through its `source_episode_ids`, which every
memory already carries.

The propagation rule, stated once and applied mechanically:

> A memory reports `verified` if and only if **every** episode listed in
> its `source_episode_ids` verifies. Any `unverified` episode in the set
> makes the memory `unverified`; absent `source_episode_ids` (orphaned or
> hand-authored memories) makes the memory `unsigned`.

The three statuses stay exactly as defined above; this rule only decides
how a memory derives its own status from the episodes it was compiled
from.

## Temporal anchoring (out of scope here, by design)

Source signing proves **authorship** — "this source attested this payload
with this key". It does not and cannot prove **when** the attestation was
made: a source in control of its clock can sign today and claim
yesterday, and the signature verifies perfectly. That backdating gap is
real, and it is *not* solved inside this convention — it is a different
problem with a different trust model (an independent third party, not the
authoring source).

The design leaves room for it deliberately: a future, separate page can
define a generic temporal-anchor slot — an external attestation *over the
signature*, shaped by the standard (RFC 3161 timestamp tokens,
transparency-log entries) rather than by any particular implementation's
receipt format. Anything that fits the generic slot can plug in; v1 of
this page defines no such artifact class. Until then, treat
`occurred_at` as *claimed* time, verifiable as authorship but not as
independent time.

## Still out of scope

- Reference implementation of signing or verification (per the
  vendor-neutral docs policy; the convention is implementable from this
  page alone).
- KMS / Vault integration for source-side key custody (orthogonal — keys
  live with the source).
- Multi-signature episodes (several sources attesting one payload).
- Algorithm agility beyond the `alg` field (v1 is Ed25519-only).
- Temporal anchoring (see the section above — separate spec after v1).

## See also

- [State-assembly receipts](./receipts.md) — server-side integrity for
  assembly calls (HMAC by the operator, not by sources)
- [Connectors](./connectors/index.md) — the ingestion paths whose
  `provenance` this convention extends
- [Issue #408 on GitHub](https://github.com/smaramwbc/statewave/issues/408)
