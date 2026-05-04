# Subject Design

> **TL;DR** — A subject is the entity Statewave's memory is *about*. Pick the smallest entity whose history you'd want recalled together; everything else (multi-tenant scoping, hierarchy, archival) is layered on top.

This is the most-asked architectural question we get. There's no one right answer — the right shape depends on what your agent needs to remember together — but there are a handful of patterns that work and a few that consistently bite. This doc collects both.

If you're new to Statewave, read [What is Statewave?](product.md) first. If you've already shipped a prototype and you're reconsidering your subject scheme, jump to [Re-modelling existing subjects](#re-modelling-existing-subjects).

---

## 1. What a subject is

A **subject** is the unit Statewave organises memory around. Episodes are written to a subject; memories are compiled per-subject; context is assembled per-subject. Cross-subject retrieval is not a first-class concept — if your agent needs facts about *both* Alice and Acme, it must call `/v1/context` twice (or model them as one subject).

Concretely:

- A subject is identified by a string `subject_id`.
- Subjects are created implicitly on first episode write — there's no `POST /subjects` step.
- Every episode and memory carries the subject id; deleting a subject deletes all its data.
- Subjects do not have a separate auth model. Tenancy is enforced by `tenant_id` on episodes/memories, not by the subject id (see [Tenancy](#3-tenancy)).

The shape of your subject id is yours to decide. Statewave validates the format (alphanumeric, hyphen, underscore; reasonable length; no reserved prefixes) but otherwise treats `customer-42`, `acme/team/alice`, and `repo:smaram/statewave` the same.

---

## 2. The core question: what's the right granularity?

Pick the smallest entity whose history you'd want **recalled together**.

Concretely: imagine your agent gets a question. What would you want it to know? Whatever that *what* is — that's your subject.

Some examples:

| Use case | Subject choice | Why |
|---|---|---|
| Customer-support agent | `customer-<id>` | "What does this customer's history look like?" is the natural retrieval shape. |
| Coding assistant for one developer's codebase | `repo:<org>/<repo>` | The agent helps with one codebase at a time; per-developer would split decisions across subjects unnecessarily. |
| Sales copilot with a pipeline of accounts | `account-<id>` | Each account has its own decision-makers, deal stage, and contact preferences — distinct memory pools. |
| DevOps assistant for a service | `service-<name>` | Runbooks and incidents belong to the service, not to the human asking. |
| Research assistant for a project | `project-<id>` | A project's literature, drafts, and collaborators belong together; the human author is constant context. |
| Per-robot fleet memory | `robot-<id>` | Each robot has its own state history; aggregated fleet memory dilutes per-robot retrieval. |
| Multi-tenant SaaS user assistant | `user-<id>` (with tenant_id scoping) | Each user has their own preferences, history, and context — same shape as customer-support. |

### Heuristic: the recall test

Before you commit to a subject scheme, write down five questions you expect your agent to handle. For each one, ask: *which subject would I want Statewave to fetch context for?* If the answer is the same entity for all five, you've probably found your subject. If the answer keeps changing, your granularity is wrong.

### Heuristic: the archival test

A second test: *when this entity is gone, would I want all its memory gone with it?* If yes, that's your subject — Statewave's "delete by subject" is the GDPR-style erasure boundary. If you'd want some memory to survive (e.g. lessons learned from a churned customer), that memory belongs on a different subject (your *team* subject, your *product* subject) or as a memory marked with provenance pointing back to the deleted subject.

---

## 3. Tenancy

If your application is multi-tenant — where two different customers' data must never appear in the same context bundle — use the `tenant_id` field, not the subject id, to enforce isolation.

```python
# Good — tenant isolation enforced by Statewave on every read/write
sw.add_episode(
    subject_id="user-42",
    tenant_id="acme",     # <- scopes the episode + later compiled memories
    ...
)
ctx = sw.get_context(
    subject_id="user-42",
    tenant_id="acme",     # <- only returns facts written under tenant "acme"
    task=...,
)
```

Don't encode tenancy into the subject id (e.g. `acme__user-42`). It looks like the same thing but loses two properties:

1. **Cross-tenant subject IDs collide silently.** If both `acme` and `bigco` have a `user-42`, encoding tenancy in the subject still works — but you've made every subject id structurally tenant-coupled. The day you want to move a subject between tenants, or share one subject across tenants for a deliberate reason, your scheme fights you.
2. **Statewave's tenant guard short-circuits at the row level.** `tenant_id` is indexed; tenant-prefixed subject ids force a string-prefix scan and don't get the same isolation guarantees.

Use `tenant_id` for tenancy. Use `subject_id` for *what the memory is about*. They're different.

### Per-tenant catalogues

If you need a subject that holds tenant-wide knowledge (rather than per-user), pick a stable id like `tenant-catalogue` and write to it under the tenant's `tenant_id`. The subject id stays the same across tenants; the tenant scoping keeps each one's catalogue isolated.

---

## 4. Hierarchy and grouping

Statewave subjects are flat — there is no built-in `parent_subject_id`. Hierarchy is modelled by **convention in the subject id** plus **separate writes to the levels you care about**.

| Pattern | Example | When to use |
|---|---|---|
| Single subject | `customer-42` | The entity has one memory pool. Most cases. |
| Sibling subjects (no hierarchy) | `customer-42`, `customer-43` | Independent entities; no aggregate retrieval needed. |
| Convention-prefixed subjects | `org/acme`, `org/acme/team/eng`, `org/acme/team/eng/user/alice` | You'll sometimes query at the org level, sometimes at the team level, sometimes at the user level. Write episodes to *all* relevant levels — Statewave does not roll them up automatically. |
| Catalogue subject + entity subjects | `customer-42` for per-customer memory, `support-team-runbook` for shared procedures | Reuse cross-cutting knowledge without duplicating it onto every entity subject. |

If you want aggregated retrieval ("everything Acme") *and* fine-grained retrieval ("Alice at Acme"), you have two choices:

1. **Write to both subjects on each episode.** Higher write cost, but each subject's retrieval is self-contained and fast.
2. **Compose context client-side from two subjects.** Lower write cost, but you assemble the bundle yourself — Statewave's ranking can't see across subjects.

Choose (1) when reads outnumber writes and latency matters; choose (2) when writes dominate or hierarchy is rare.

---

## 5. Subject id naming

Stable, predictable, opaque-ish ids age best.

**Recommended:**

- Prefix by entity kind: `customer-42`, `repo:smaram/statewave`, `service-nimbus-api`. The prefix makes the scheme inspectable and lets you reserve ids for non-customer subjects (catalogues, system memory) without collision.
- Use stable surrogate keys (DB ids, UUIDs, slugs that won't be renamed). Email addresses and human names rename; stable ids don't.
- Keep ids short enough to log freely (~64 chars is a comfortable upper bound). Statewave doesn't truncate, but log lines, dashboards, and humans appreciate brevity.

**Avoid:**

- **Email addresses.** They change. When `alice@oldco.com` becomes `alice@newco.com`, you'll either lose her memory or have to migrate every row.
- **Human-readable display names.** Same renaming problem. Display names belong on metadata, not on the subject id.
- **Anything ephemeral.** A session id, a request id, a job id — these are not subjects, they're spans (see [Sessions and spans](#6-sessions-and-spans)).
- **Tenant-prefixed ids** (covered above) — use `tenant_id` instead.
- **Reserved prefixes.** Statewave reserves `demo_web_*` and a small number of internal prefixes; the import path will rewrite them automatically. Pick your own scheme outside those.

A subject id is part of your public surface (it appears in URLs, logs, and webhook payloads). Treat the rename as a migration, not an edit.

---

## 6. Sessions and spans

A common mistake: making the *session* the subject. Session-per-subject means every conversation starts from zero — you've lost the very property Statewave exists to provide.

Sessions belong inside a subject, modelled as one of:

- **An episode `metadata.session_id`** field — episodes carry session context, the subject's compiled memory persists across sessions. This is the default and almost always the right shape.
- **A separate `session-<id>` subject** *only* if sessions truly have independent memory pools (e.g. anonymous one-off chatbots where session and user are the same thing and there's no returning visitor). Rare.

If your app has both an authenticated user *and* per-conversation transcripts, the user is the subject and the conversation is metadata on the episode. Statewave's ranking already understands "this episode is from the active session" via session-aware boosting — don't reinvent that with subjects.

---

## 7. When to start a new subject vs append

**Append (same subject):** the entity's history is continuous and you want all of it recalled together. This is the default.

**New subject:** when *aggregate retrieval no longer makes sense*. Examples:

- A B2B customer churns and a year later signs up again under the same legal entity but a new contract — start `customer-42-v2` if their old context would actively mislead the agent. Otherwise reuse `customer-42`.
- A repository is forked and the fork takes its own direction — `repo:smaram/statewave-fork` is its own subject, even though git history is shared.
- A robot's hardware is replaced — the new robot might inherit the old robot's subject (if memory is about the *role* it plays in the fleet) or get its own (if memory is about the physical unit).

When in doubt, append. It's much easier to split a subject later (via clone-with-filter, see [`/admin/memory/clone`](api/v1-contract.md)) than to re-merge two subjects.

---

## 8. Common patterns by use case

### Support agents

```
customer-<id>             # one per customer/account
support-team-runbook      # cross-cutting playbooks (shared knowledge)
```

Episodes from a customer support chat go to `customer-<id>`. Reusable troubleshooting procedures go to `support-team-runbook`. Your agent calls `/v1/context` against the customer subject for context, and against the runbook subject for procedures, then composes both into the prompt.

### Coding agents

```
repo:<org>/<repo>         # one per repo
developer-<id>            # only if cross-repo developer preferences matter
```

Most of the agent's memory is about the codebase: stack choices, conventions, ADRs, in-flight refactors. Per-developer preferences (e.g. "Priya prefers concise PRs") are a small slice — only worth a separate subject if the same developer works across many repos *and* their preferences should travel.

### Sales copilots

```
account-<id>              # one per account in the pipeline
sales-team-playbook       # cross-cutting positioning (e.g. "vs Mem0: lead with determinism")
```

Each account has its own decision-maker, blockers, deal stage, and contact preferences. The playbook subject holds cross-cutting competitive memory and procedural conventions (HIPAA procurement order, AE routing rules) so they don't have to be re-recorded per account.

### DevOps assistants

```
service-<name>            # one per managed service
ops-team-conventions      # alert thresholds, deploy windows, on-call rotation
```

Service incidents, post-mortems, and runbooks live on the service subject. Team-wide policy (no Friday deploys, escalation paths) lives on the conventions subject — moving these doesn't change when you ship a new service.

### Personal AI / journaling

```
user-<id>                 # one per user
```

Single subject per user is almost always right. Don't split by topic, by year, or by device — the value is unified recall.

### Per-document or per-conversation agents

```
document-<id>             # if the document IS the unit of memory
```

Be honest with yourself here. If your "agent" is really a doc-grounded assistant where the document changes every session and there's no returning user, you may not need Statewave — a stateless RAG layer over the document is enough. Statewave is for memory *across* sessions. If the document is the persistent entity (e.g. a long-running case file), `document-<id>` works.

---

## 9. Anti-patterns

These come up often enough to call out explicitly:

| Anti-pattern | Why it bites | What to do instead |
|---|---|---|
| **Session-as-subject** | Memory dies every session. You've built a stateless agent with extra steps. | Subject = the persistent entity (user/account/project). Session goes on episode metadata. |
| **Tenant-as-prefix** | Locks tenancy into id strings; loses row-level isolation guarantees. | Use `tenant_id`. |
| **Email-as-subject-id** | Renames break recall. Migration is painful. | Stable surrogate id (DB pk, UUID, slug). |
| **Subject per (user, topic)** | "alice-billing", "alice-onboarding" — splits Alice's memory across pools. The agent loses context when the topic changes mid-conversation. | One subject per user. Topics emerge from compiled memory kinds, not from subject splits. |
| **Subject per LLM call** | Every call is its own pool; nothing accumulates. Negates the product. | Subject is the entity, not the call. |
| **Subject per agent personality** | "alice-with-friendly-bot", "alice-with-strict-bot" — splits memory by personality. The agent forgets you depending on its mood. | One subject per user; personality goes on the prompt template, not the subject. |
| **Mega-subject** (one subject for everything) | Retrieval becomes diluted; pgvector index pressure; ranking can't separate per-entity context. | Split by entity. The "recall test" in §2 is your guide. |

---

## 10. Re-modelling existing subjects

If you're already in production with a subject scheme that's wrong, you have three migration paths:

### Splitting one subject into several

You picked too-coarse subjects (e.g. `tenant-acme` holding all of Acme's user memory). To split:

1. Use `/admin/memory/clone` with a filter to copy episodes matching a predicate (e.g. `metadata.user_id == "alice"`) into the new subject `user-alice`.
2. Re-run compile on the new subject so memories regenerate from the filtered episode set.
3. Delete the rows from the source subject in a follow-up step (not the same call — verify the new subjects look right first).

This is a *clone, then cleanup* pattern, not a single atomic move. Statewave doesn't have a transactional split; the clone is non-destructive on purpose.

### Merging several subjects into one

You picked too-fine subjects (e.g. `alice-2024`, `alice-2025` instead of `alice`). To merge:

1. Pick one as the canonical destination.
2. Use `/admin/memory/clone` from each source into the destination, with `clone_scope=episodes_memories_sources` to preserve provenance.
3. Recompile the destination so the merged memory pool deduplicates idempotently.
4. Delete the source subjects.

### Renaming

You picked the wrong id format (e.g. emails) and need to migrate to stable ids. There is no in-place rename — you clone to the new id, point your application at the new id, then delete the old subject. Plan a write-side cutover so episodes don't get split across the rename.

In all three cases, capture the migration intent in episode `provenance` (`{"migration": "split-2026-Q2", "source_subject_id": "tenant-acme"}`) so the new memory pool's compiled facts trace back to the migration event.

---

## 11. Operational considerations

**Subject size limits.** There's no hard cap, but `/v1/context` latency starts climbing past a few tens of thousands of memories per subject (the pgvector probe slows). If a single subject is consistently growing into that range, that's a signal to split — usually by time window (`alice-2026q3`) for time-bounded data, or by sub-entity for hierarchical data. See [hardware and scaling](deployment/hardware-and-scaling.md).

**Subject deletion.** `DELETE /v1/subjects/<id>` removes all episodes, memories, and embeddings for that subject. It's irreversible (no soft delete) — capture a backup if you might need to recover. Per-tenant isolation means a tenant-scoped delete touches only that tenant's view of the subject; other tenants writing to the same subject id are unaffected.

**Subject discovery.** There's no `GET /subjects` listing endpoint by design — subjects are identified by your application, not enumerated by Statewave. If you need a listing, keep it in your application's database and treat Statewave's subject ids as foreign keys.

**Provenance across subjects.** Memories carry `source_episode_ids` pointing to episodes within their own subject. Cross-subject provenance is not modelled — if a memory was derived from observations across two subjects, write it to both subjects (each as its own memory) rather than trying to point one memory at another subject's episodes.

---

## 12. Worked example: choosing a scheme from scratch

Suppose you're building a customer-onboarding assistant. The agent helps newly-signed customers through their first 30 days: setup, integration, first invoice, first feature request.

**Start with the recall test.** Five expected questions:

1. "What's this customer's name and plan?" → about the customer
2. "What integration did they say they preferred?" → about the customer
3. "Is this a known onboarding blocker?" → about onboarding (cross-customer)
4. "Has anyone hit this before?" → about onboarding (cross-customer)
5. "What's the next step in their onboarding plan?" → about the customer

Three of five point at the customer; two point at cross-customer onboarding knowledge. So:

- Per-customer subject: `customer-<id>` — for questions 1, 2, 5.
- Cross-cutting subject: `onboarding-playbook` — for questions 3, 4.

Episodes from a customer's chat go to `customer-<id>`. Resolved blockers, recurring issues, and procedural steps get written to *both* `customer-<id>` (so they're recalled in that customer's context) *and* `onboarding-playbook` (so the next customer benefits). Tenancy is `tenant_id` on every write.

That's the pattern. Two subject kinds, both flat, no hierarchy, tenant-scoped, with deliberate cross-writes for shared knowledge.

---

## See also

- [What is Statewave?](product.md) — the product-level framing for subjects, episodes, memories, and bundles
- [Architecture overview](architecture/overview.md) — domain model, data lifecycle, and where subjects fit
- [Privacy and data flow](architecture/privacy-and-data-flow.md) — what leaves the box per subject
- [Hardware and scaling](deployment/hardware-and-scaling.md) — subject size, retrieval latency, when to split
- [API contract](api/v1-contract.md) — the `subject_id` field on every endpoint
