# RFC: Statewave Memory Import / Export Format

> Suggested category: **RFCs**. Pin while feedback window is open; unpin once a decision lands.
>
> **Status:** draft RFC, not implemented. Subject-level export/import shipped in v0.5; this RFC proposes a portable, vendor-neutral, encryption-first **archive format** that builds on it.

---

## Title

RFC: Statewave Memory Import / Export Format

## Body

### Summary

Statewave already supports subject-level export/import (v0.5). This RFC proposes a portable, well-specified archive format — provisionally **`.swmem`** — for moving memory between Statewave instances, environments, providers, and (eventually) tools. The goal is to make memory **a first-class portable artifact**: something you can clone, ship, snapshot, and audit, without locking it to a single deployment.

### Motivation

Memory portability matters for several real workflows:

- **Disaster recovery** — restore a subject's memory state on a fresh instance with byte-for-byte fidelity.
- **Environment promotion** — move a subject from staging to production after validation.
- **Cloning** — duplicate a subject (or a whole pack) for testing, A/B comparison, or onboarding new tenants.
- **Vendor / instance migration** — leave a managed Statewave for self-hosted (or vice versa) without re-deriving memory from scratch.
- **Starter packs** — distribute curated memory packs (e.g. the docs-grounded support pack) as standalone artifacts.
- **Auditability** — hand a regulator, customer, or counterparty a sealed, verifiable copy of "what we knew, when".

This is also a **trust signal**. A memory layer you can't extract is not portable infrastructure; it's lock-in.

### Scope

In scope:
- Format spec for a single archive (`.swmem`)
- Cleartext and encrypted variants
- Subject-scoped, multi-subject, and pack archives
- Episodes, compiled memories, embeddings (optional), provenance edges, schema metadata
- Versioned format with forward/backward-compatibility rules

Out of scope (for this RFC):
- Online sync / replication protocols
- Cross-tool interop with non-Statewave memory systems (worth a separate RFC if there's interest)
- Live "follow" subscriptions

### Proposed design (sketch)

A `.swmem` archive is a tar (or zip) with a documented internal layout:

```
manifest.json          # format version, scope, encryption header, integrity hashes
schema/                # alembic migration head, kind catalogs, embedding model id
subjects/
  <subject_id>/
    episodes.jsonl
    memories.jsonl
    provenance.jsonl
    embeddings.bin       # optional; omitted if non-portable across providers
attachments/             # optional binary blobs referenced by episodes
```

**Encrypted-by-default** for archives that leave the originating environment:
- Symmetric content encryption (e.g. AES-GCM-256) over the inner payload
- Key derivation from a **client-side passphrase** via a strong KDF (e.g. argon2id) — passphrase never leaves the client
- Optional asymmetric envelope (recipient public key) for hand-off scenarios
- Integrity covers the manifest + payload; tampering breaks decryption

**Vendor-neutral by design:**
- No provider-specific identifiers in the on-disk format beyond a recorded `embedding_model_id` for traceability
- Embeddings are **optional** — when omitted on import, the receiving instance recomputes with its configured provider
- Compiler-mode metadata is recorded but doesn't constrain the importer

**Starter packs** are a first-class subtype: a `.swmem` that ships with no per-customer subject identifiers, intended to be imported into many environments. The docs-grounded support pack would become the reference example.

### Alternatives considered

- **JSON dump only** — what we have today at the API level. Easy, but no integrity guarantees, no encryption story, no pack semantics, no formal versioning.
- **SQL dump** — too tightly coupled to Postgres and to Statewave's current schema; defeats the portability goal.
- **Reuse an existing format (Parquet, Arrow, OCI artifacts)** — interesting for the data files, possibly worth adopting *inside* the archive. The outer envelope (manifest + encryption + scope) still needs to be Statewave-specific.

### Risks / tradeoffs

- **Encryption complexity** — done wrong, this is worse than no encryption. Defaults must be strong, options must be small.
- **Embedding portability** — embeddings only travel cleanly between matching models. Recording `embedding_model_id` and recomputing on mismatch is a correctness floor; the alternative (re-embedding on every import) makes large packs slow.
- **Format churn** — once people ship archives in the wild, the format is hard to change. v1 must be conservative.
- **Schema drift** — the importer needs to handle archives produced by older or newer Statewave schemas. Migration on import vs. fail-closed is a design decision.

### Open questions

1. **Container format** — tar+zstd, zip, OCI artifact? Tradeoff: tooling familiarity vs. content-addressed reuse.
2. **Size limits** — should the spec cap individual archives, or is that purely operational? Streaming import for very large packs?
3. **Default encryption posture** — encrypted by default with `--no-encryption` opt-out for local use, or cleartext default with explicit `--encrypt`?
4. **Passphrase ergonomics** — how is the passphrase delivered when the archive is shared (separate channel, key wrapping, integration with a KMS)?
5. **Conflict behavior on import** — overwrite, merge, fail, namespace-prefix? Per-subject, or per-record?
6. **Provenance on imported memory** — preserve the original episode IDs, or rewrite them into the importer's namespace? How is "imported from" recorded?
7. **Signing** — is a separate signature (detached, or in the manifest) needed beyond integrity hashing? Use case: distributing a starter pack with verified authorship.
8. **Embedding handling** — always strip on export by default, or include with a recorded model id and let the importer decide?
9. **Pack authoring tooling** — what's the minimum CLI / API surface to make pack creation feasible without hand-editing JSONL?
10. **Compatibility window** — how many format versions back must an importer accept?

### Feedback requested

Most useful comments would address:

- Real workflows you'd use this for — clone, migrate, audit, distribute, snapshot
- Threat model for the encryption story — who is the adversary and what's the failure mode that scares you
- Whether `.swmem` should aim to interoperate with any existing tools, and if so, which
- Hard requirements from regulated environments (HIPAA, GDPR, SOC 2) that should be in v1

> This RFC is a design discussion, not an implementation commitment. Nothing here ships until the design is sound and there's a concrete use case to ship it for.
