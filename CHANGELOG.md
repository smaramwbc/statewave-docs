# Changelog

All notable changes to the Statewave workspace.

## v0.8.1 — Adoption (2026-05-25)

Closes the Adoption half of the v0.8 milestone, on top of the Governance & Audit foundation shipped in v0.8.0. Each item shipped as its own focused PR; the full breakdown lives in [`roadmap.md`](roadmap.md#v08--governance--adoption-) under "Adoption — shipped".

### Added — SDK convenience methods for support endpoints ([statewave-py#15](https://github.com/smaramwbc/statewave-py/pull/15), [statewave-ts#16](https://github.com/smaramwbc/statewave-ts/pull/16))

- `get_health` / `getHealth`, `get_sla` / `getSLA`, `create_handoff` / `createHandoff`, `create_resolution` / `createResolution`, `list_resolutions` / `listResolutions` on **both** the Python `StatewaveClient` (sync + async) and the TypeScript `StatewaveClient`.
- Same auth, tenant-scoping, retry/backoff, and structured error handling as the rest of each client — these methods route through the existing shared request path.
- Wrap support-agent endpoints the server has exposed since v0.6, so callers no longer need raw HTTP alongside the SDK.
- Released as `statewave` **0.10.0** on PyPI and `@statewavedev/sdk` **0.10.0** on npm (version-aligned across SDKs).

### Added — webhook event-type filter ([statewave#150](https://github.com/smaramwbc/statewave/pull/150) · docs [statewave-docs#39](https://github.com/smaramwbc/statewave-docs/pull/39))

- `STATEWAVE_WEBHOOK_EVENTS` (comma-separated) — an event-type allowlist applied at the global webhook URL. Filtered-out events are dropped before they reach the delivery queue (zero storage, zero delivery attempts).
- Unknown event types fail the server at startup, so a typo can't silently drop every webhook. Validation against the canonical event vocabulary in `server/core/webhook_events.py`.
- Fully backward-compatible: empty / unset filter delivers every event. No DB migration.

### Added — memory templates for common patterns ([statewave#152](https://github.com/smaramwbc/statewave/pull/152) · docs [statewave-docs#41](https://github.com/smaramwbc/statewave-docs/pull/41))

- Declarative, versioned scaffolds for recurring information patterns. Five bundled templates ship today: `customer-support-handoff`, `user-preference`, `project-decision`, `incident-summary`, `account-onboarding` (server `server/templates/*.yaml`).
- Read-only API exposes every template's full field schema for inspection: `GET /v1/memory-templates`, `GET /v1/memory-templates/{template_id}`.
- `POST /v1/memory-templates/{template_id}/apply` validates caller-supplied field values against the template, deterministically renders the content, and ingests an ordinary episode with `template_id` / `template_version` recorded in both `payload` and `metadata.template` for provenance.
- Pure data — no code runs inside a template; rendering is plain string substitution. Adding a template is dropping a YAML file in `server/templates/`. The compiler is unchanged. Reference: [`docs/memory-templates.md`](https://github.com/smaramwbc/statewave/blob/main/docs/memory-templates.md).

### Added — framework integration examples ([statewave-examples#12](https://github.com/smaramwbc/statewave-examples/pull/12))

- Three runnable quickstarts under [`statewave-examples`](https://github.com/smaramwbc/statewave-examples): `langchain-quickstart/`, `crewai-quickstart/`, `autogen-quickstart/`. Each ships an `adapter.py`, a runnable demo, a mock-based smoke test (no LLM, no Statewave server needed), and a README.
- **Dependency strategy:** zero framework deps in the core Statewave SDKs. Adapter code lives inside each example; framework versions pinned only in the example READMEs. SDK releases don't chase framework version churn.
- Adapter shapes: `StatewaveMemory(BaseMemory)` for LangChain; pure-function helpers (`build_task_description` + `record_crew_output`, `build_system_message` + `update_system_message` + `record_turn`) for CrewAI and AutoGen — both dependency-free of their own framework so smoke tests run without those installs.

### Added — head-to-head benchmark vs Mem0 / Zep ([statewave-bench#14](https://github.com/smaramwbc/statewave-bench/pull/14))

- First **complete equal-budget sweep** across the public [LoCoMo](https://github.com/snap-research/LoCoMo) dataset: 4 token tiers (512 / 1024 / 2048 / 4096) × 5 systems (statewave, mem0, zep, naive, no_memory) × 10 conversations × 1,986 questions/system, single consistent run.
- Publication-safety harness — `swb report` refuses headline rankings without 100% scored coverage, the same question set across systems, no `judge_failed` rows, measured input tokens reported beside every score, and a standing vendor-correction invitation.
- Headline (excl. adversarial mean per-question score): statewave **0.393 / 0.384 / 0.404 / 0.416** across the four budgets; mem0 0.154 / 0.269 / 0.283 / 0.273; zep 0.035 / 0.041 / 0.048 / 0.046. Full per-tier results in [`RESULTS.md`](https://github.com/smaramwbc/statewave-bench/blob/main/RESULTS.md) on `statewave-bench` `main`.

### Added — design partner onboarding package ([statewave-docs#42](https://github.com/smaramwbc/statewave-docs/pull/42))

- New [`design-partners.md`](design-partners.md): a single-page guide covering overview + 30/60/90-day relationship shape, who Statewave is for (strong + weak fit), a 30-minute setup path, recommended first use cases, data/privacy expectations, support and feedback loop, evaluation checklist (functional, performance, governance, operational), success criteria with benchmark reference numbers, and a 9-entry FAQ. Linked from `README.md` and `SUPPORT.md`.

### Roadmap consistency ([statewave-connectors#66](https://github.com/smaramwbc/statewave-connectors/pull/66) · [statewave-docs#38](https://github.com/smaramwbc/statewave-docs/pull/38) · [statewave-docs#43](https://github.com/smaramwbc/statewave-docs/pull/43))

- Connectors-repo roadmap brought into agreement with the canonical `statewave-docs` roadmap: Tier 3 operator/cloud productization wave (v0.12.0–v0.17.0) recorded in the "State of the world" callout; the stale "Built-in OIDC verification for Gmail Pub/Sub" entry (shipped in `connectors` v0.15.0) removed from the Queued list in both copies.
- `roadmap.md` ticks every Adoption checkbox with PR citations, flips the `← CURRENT` marker from v0.8 to v0.9, and renames `Adoption — in progress` to `Adoption — shipped`.

## v0.8.0 — Governance & Audit (2026-05-14)

This release adds the governance layer that turns Statewave from "structured memory with provenance" into "structured memory with emitted, queryable, policy-governed accountability." Three components:

### Added — state-assembly receipts ([#49](https://github.com/smaramwbc/statewave/issues/49))

- Every `/v1/context` and `/v1/handoff` call can emit an **immutable, ULID-addressable receipt** of which memories + episodes influenced the assembled bundle, plus a SHA-256 hash of the bytes delivered to the agent. Receipts are tenant-scoped, append-only, and queryable via `GET /v1/receipts/{id}` and `GET /v1/receipts?subject_id=&since=&until=&cursor=`.
- Strict-superset schema with a `mode` discriminator (`retrieval` in v0.8; `as_of_replay` and `eval_run` reserved for v0.9) so future modes extend without breaking parsers.
- Per-entry fields cover the supersession status (`active | superseded | tombstoned`), source episodes, provenance hash, rank, and a `fact_key` / `conflict_status` slot for the conflict-resolution layer to fill in.
- Reserved schema slots for v0.9 work: `parent_receipt_id` (wired in v0.8 for chaining), `region` (for data residency), `receipt_signature` (for HMAC tamper-evidence).
- Emission control is a single decision function consulting (env kill-switch → per-policy force-on → per-tenant config `receipts: always | on_request | never` → per-request `emit_receipt: bool`). Fail-open: a receipt write error logs a structured warning and the assembly bundle still returns.
- Six negative-test acceptance criteria from the design doc — stale fact selected, superseded memory ranked, tombstoned memory resurrected, unresolved conflict, as-of drift, byte tampering — each phrased as a deterministic assertion against the receipt body.
- Read API surface ships in both SDKs: `client.get_receipt(id)`, `client.list_receipts(subject_id, ...)`. Receipts also exposed via the admin app's `/receipts` page (read-only, cross-tenant) and the `/admin/receipts` cross-tenant operator endpoints.
- Full reference in [`receipts.md`](receipts.md).

### Added — sensitivity labels & per-memory policy bindings ([#50](https://github.com/smaramwbc/statewave/issues/50))

- Per-memory **capability tags** stored as `memories.sensitivity_labels: TEXT[]` with a GIN index for cheap overlap queries on the hot path. Operator-supplied via `PATCH /v1/memories/{id}/labels`; server normalises (deduplicate + lowercase + trim) and caps at 32 entries per memory.
- **Declarative policy bundles** in YAML or JSON, content-hashed and immutable in the new `policy_bundles` table. Six predicates (`memory_has_any_label`, `memory_has_all_labels`, `caller_type`, `caller_type_in`, `caller_type_not_in`, `caller_id`) AND-ed inside `when:`; first-match-wins across rules; default-allow on no match. Two actions: `deny` (drop memory) and `redact` (replace content with `[REDACTED by policy]`).
- **Caller identity** in requests: `caller_id` and `caller_type` on `/v1/context` and `/v1/handoff` feed the evaluator. Tenant config `require_caller_identity: true` 401s anonymous calls — the lever compliance customers flip to make policy enforcement non-bypassable.
- **Per-tenant policy_mode: log_only | enforce**. Ships in `log_only` by default — receipts record what *would* be denied without filtering the response, so operators can audit a policy for a few days before flipping to `enforce`. Without this lever the day a tenant enabled policy would silently lose memories for any under-tagged subject.
- Receipts fill `policy.filters_applied` (one entry per memory where a rule fired) and `policy.filters_skipped` (one entry per rule that ran but matched nothing — bounded by `len(bundle.rules)`, not memory count).
- Admin endpoints: `POST /admin/policy/bundles` (upload + optional activate), `GET /admin/policy/bundles` (list, optional tenant filter), `GET /admin/policy/bundles/{hash}?tenant_id=` (detail with disambiguation), `POST /admin/policy/activate` (flip active in a scope), `POST /admin/policy/reload` (bust in-process cache for direct DB fix-ups), `GET /admin/policy/active?tenant_id=` (returns `200 + null` for unconfigured scopes).
- Admin app `/policy` page: list, upload YAML, activate, detail viewer with parsed rules + when blocks + actions.
- Full reference in [`sensitivity-labels.md`](sensitivity-labels.md).

### Added — per-tenant configuration

- `GET / PATCH /admin/tenants/{tenant_id}/config` covers the receipt emission policy, retention window (worker is v0.9), policy mode, and caller-identity gate. PATCH is partial-merge (only touches supplied keys, preserves the rest) so future per-tenant knobs land without each endpoint knowing the full key set.
- Validation at the API boundary: enum values, integer bounds, and the documented key set are all checked by Pydantic before they reach the JSONB. A typo like `policy_mode: "enforced"` returns 422 instead of silently leaving enforcement off — the failure mode the JSONB shape made too easy to introduce.
- Optimistic concurrency via `expected_version`: lost-update races between parallel admin edits surface as 409 with a clear message, not silent overwrites. `expected_version=0` is the create semantic for a tenant with no row yet.
- Admin app: tenant-config form on the `/policy` page (rendered when a tenant scope is selected), with an enforce-mode warning and 409-auto-reload on concurrent edits.

### Added — cross-tenant policy bundle independence ([#79](https://github.com/smaramwbc/statewave/issues/79))

- `policy_bundles` now keyed on a synthetic UUID `id` PK plus a composite unique index `(tenant_id, bundle_hash) NULLS NOT DISTINCT` (PG15+). Two tenants installing the identical YAML produce two independently-resolvable rows.
- `GET /admin/policy/bundles/{hash}` accepts `?tenant_id=` for disambiguation; `POST /admin/policy/activate` request body includes `tenant_id` so the flip targets exactly `(tenant, hash)`.
- Pre-fix, the second tenant's upload silently re-bound the first's row and broke their policy resolution. Caught in the enforce-mode prod smoke; the temporary workaround was to add a tenant-identifying comment to the YAML.

### Fixed

- **Multi-replica policy bundle cache staleness** ([#77](https://github.com/smaramwbc/statewave/issues/77)) — dropped the in-process cache on `policy_bundles`. The 60-second TTL caused replicas that hadn't handled the admin upload to keep serving the pre-upload `None` value until their TTL expired, which under `enforce` would silently pass sensitive memories through for up to a minute after a tenant activated a policy. DB lookup is sub-millisecond with the existing index; correctness > caching savings. Caught in production smoke testing.
- **`/admin/policy/active` 404 → 200 + null** when no bundle is active for the scope. "No bundle uploaded yet" is the default state on fresh install, not an error. 404 polluted every operator's browser console on first page load.
- **Stacked-PR rebase hygiene** in the merged history — the closed-by-cascade PRs (server #73, py #8, ts #10) have explanatory comments pointing at their replacement PRs.

### Architectural notes

- The receipt body shape was chosen as a strict superset rather than a tagged union so v0.9's `as_of_replay` and `eval_run` modes can extend without forcing every receipt consumer to update its parser. The `mode` discriminator carries the actual variant.
- `policy_bundles` uses a synthetic UUID PK rather than a sentinel-tenant approach (`tenant_id NOT NULL DEFAULT ''`) so wire shapes don't shift — global bundles still appear as `tenant_id: null` on the wire post-#79.
- The policy evaluator is intentionally pure (no DB, no IO inside `evaluate_memory`) so it can be tested directly with synthetic rules and memories. Bundle resolution is the only DB-touching part.

### Migrated

- `alembic` head moved from `0016_memory_status_tombstoned` to `0019_per_tenant_bundles`. Three new migrations:
  - `0017_receipts_and_policy` — `receipts`, `tenant_configs`, `policy_bundles` tables.
  - `0018_sensitivity_labels` — `memories.sensitivity_labels TEXT[]` + GIN index.
  - `0019_per_tenant_bundles` — composite uniqueness on `policy_bundles` (synthetic UUID PK + `(tenant_id, bundle_hash) NULLS NOT DISTINCT`).

### Companion releases

- `statewave` server v0.8.0 — full surface above.
- `statewave-py` 0.8.0 (PyPI) — `Receipt`, `ReceiptList`, `set_memory_labels`, `get_receipt`, `list_receipts`, `caller_id` / `caller_type` on `get_context()`.
- `statewave-ts` 0.8.0 (npm `@statewavedev/sdk`) — same surface, first-class types.
- `statewave-admin` — Receipts viewer, Policy page (upload + activate + bundle detail), Tenant config form, sensitivity-labels editor on `MemoryDetailModal`.

## v0.7.2 (2026-05-10)

### Added
- **Per-kind memory TTL** — operators configure global expiry windows per memory kind (`profile_fact`, `episode_summary`, `procedure`, `artifact_ref`) via `STATEWAVE_KIND_TTL_DAYS` (JSON). Compilers stamp `valid_to = valid_from + ttl_days` at insert; `/v1/context` retrieval filters expired rows immediately; an hourly cleanup loop tombstones expired rows. Soft-delete only — rows are preserved for audit and future receipt lookup. ([#59](https://github.com/smaramwbc/statewave/issues/59), full operator guide: [`deployment/memory-ttl.md`](deployment/memory-ttl.md))
- **MemoryStatus enum aligned to `active | superseded | tombstoned`** — the previously unused `deleted` value renamed to `tombstoned` (alembic 0016) so the status surface composes cleanly with the receipts work in [#49](https://github.com/smaramwbc/statewave/issues/49).
- **Helm chart** at [`helm/statewave`](https://github.com/smaramwbc/statewave/tree/main/helm/statewave) — API-only chart with pre-install hook ordering, externalSecret support, optional HPA + Ingress + PDB, and migration Job. ([#58](https://github.com/smaramwbc/statewave/issues/58))
- **Cross-machine query embedding cache (L2)** — Postgres-backed `query_embedding_cache` table (alembic 0014) shared across all backend instances. Wraps the in-process LRU as L2: warm calls are sub-second regardless of which instance handles them. 24h TTL, composite (text, model) key.
- **In-process LRU + TTL query embedding cache (L1)** — eliminates repeat provider calls on identical task text in `/v1/context`.
- **CODE_OF_CONDUCT.md** — adopt-by-reference Contributor Covenant 2.1.

### Changed
- **All LLM and embedding calls go through a single LiteLLM adapter** (`server/services/llm.py`). One env-var contract (`STATEWAVE_LITELLM_*`), 100+ provider compatibility, consistent retry + timeout + structured logging.
- **Cross-workspace positioning unified** — `Open-source memory runtime for AI agents` is now the canonical tagline across homepage, READMEs, package descriptions, GitHub bios, and Docker Hub.
- **Docker Hub repo description sync** now succeeds via the OAT-scoped `DOCKERHUB_TOKEN`.

### Docs
- New: deployment sizing guide, capacity-planning checklist.

## v0.6.1 — Support-Agent Superiority (2026-04-29)

### Added
- **Session-aware context assembly** — active session boosted, resolved sessions deprioritized
- **Resolution tracking** — `POST /v1/resolutions`, `GET /v1/resolutions` for open/resolved/unresolved state per session
- **Handoff context packs** — `POST /v1/handoff` generates compact escalation briefs with customer summary, active issue, attempted steps, resolution history, health, and SLA context
- **Customer health scoring** — `GET /v1/subjects/{id}/health` returns deterministic 0–100 score with explainable factors (unresolved issues, repeats, escalations, idle open issues, SLA breaches, slow response)
- **Repeat-issue detection** — surfaces prior resolutions when episode patterns recur
- **Support-specific ranked retrieval** — session awareness, resolution status, and health signals feed into context ranking
- **Health-aware handoff** — risk level, score, and top factors appear in handoff briefs
- **Proactive health alerts** — `subject.health_degraded` and `subject.health_improved` webhooks on state transitions
- **SLA tracking** — `GET /v1/subjects/{id}/sla` computes first-response time, resolution time, and breach flags per session with configurable thresholds
- **SLA integration** — breach signals feed into health scoring; SLA summary appears in handoff packs when relevant

### Proof layer
- 3 eval suites: context quality (7 tests, 14 assertions), handoff (7 tests, 16 assertions), advanced (7 tests, 24 assertions)
- 2 benchmarks: context recall + workflow comparison (Statewave 9/9 vs Naive 2/9)
- 232 unit tests passing

### Changed
- Health scoring now includes SLA breach penalty and slow first-response penalty
- Handoff packs now include conditional SLA section (absent when clean)
- Context ranking formula updated with session and resolution awareness

## v0.5.0 — Reliability & Trust (2026-04-29)

### Added
- **True multi-tenant isolation** — tenant_id persisted on all tables, all queries scoped by tenant
- **Distributed rate limiting** — Postgres-backed fixed-window, survives restarts, multi-worker
- **Backup/restore tooling** — subject-level export/import via admin API with SHA-256 checksum
- **Tenant audit endpoint** — `GET /admin/tenant-audit` for NULL-tenant row discovery
- **Admin export/import** — `GET /admin/export/{subject_id}`, `POST /admin/import`
- Operator upgrade guidance for pre-tenant data backfill

### Changed
- Rate limiting now defaults to `distributed` strategy (Postgres-backed)
- Tenant middleware no longer experimental — real data isolation enforced
- Background cleanup loop now also handles rate limit window pruning

### Migrations
- `0008_add_tenant_id_columns` — tenant_id + indexes on episodes, memories, webhook_events, subject_snapshots
- `0009_add_rate_limit_table` — rate_limit_hits table for distributed rate limiting

## v0.4.3 — Public Release Polish (2026-04-25)

### Improved
- README rewrite across all repos — accurate product framing, docs navigation, current limitations
- Consistent tagline and cross-repo linking
- SDK READMEs updated with batch and subject listing examples
- CI workflows: added tests to TS CI, fixed lint errors
- Release workflows: tag-push trigger, CI gate, no accidental releases
- PUBLISHING.md rewritten for automated release process
- Cleaned up all failed GitHub Actions runs

## v0.4.0 — Operator & Adoption Readiness (2026-04-24)

### Added (server)
- **Batch episode ingestion** — `POST /v1/episodes/batch` accepts up to 100 episodes per request
- **OpenTelemetry tracing** — optional tracing spans on compile, search, and context assembly. Install with `pip install statewave[otel]`
- **Comprehensive `.env.example`** — documents all `STATEWAVE_*` configuration variables with comments

### Added (SDKs)
- **Python SDK 0.4.0** — `create_episodes_batch()` method, `BatchCreateResult` model, `py.typed` marker, PyPI-ready metadata (classifiers, URLs, keywords)
- **TypeScript SDK 0.4.0** — `createEpisodesBatch()` method, `BatchCreateResult` type, npm-ready metadata (exports, files, engines, repository)
- **Publish checklists** — `PUBLISHING.md` in both SDK repos

### Added (docs)
- **Deployment guide** — Docker Compose, bare metal, single container, Fly.io, Railway instructions with production checklist
- **SDK changelogs** — `CHANGELOG.md` in both SDK repos

### Deferred
- **TTL/auto-expiry** — deferred to v0.5. `valid_to` on memories provides manual expiry semantics. Automatic sweep requires a background scheduler not yet justified.

## v0.3.5 — Stabilization (2026-04-24)

### Fixed (server)
- **Middleware execution order** — corrected Starlette reverse-ordering so auth runs before rate limiting and request ID is set outermost
- **Compile + conflict resolution transaction** — both now execute in a single commit, preventing data inconsistency on partial failure
- **LLM compiler event loop blocking** — `LLMCompiler` now uses `ThreadPoolExecutor` so synchronous OpenAI calls don't block async request handling
- **Episode route uses repository layer** — previously bypassed `repo.insert_episode()` and used raw session directly
- **Request validation** — added `min_length`/`max_length` on string fields, bounded `max_tokens` (1–128,000) and `limit` (1–100)

### Changed (SDKs)
- **Python SDK 0.3.5** — added `api_key` and `tenant_id` constructor params, `semantic` param on `search_memories()`
- **TypeScript SDK 0.3.5** — added `ClientOptions` with `apiKey`/`tenantId`, `semantic` param on `searchMemories()`

### Changed (examples)
- All examples now accept `STATEWAVE_API_KEY` and `STATEWAVE_URL` environment variables
- Coding agent example added to examples README

### Changed (docs)
- API contract doc fully rewritten to match v0.3.5 server behavior (auth, semantic, webhooks, validation, config reference)
- Architecture overview updated with v0.3 component diagram, scoring model, middleware stack
- Repo map updated with current versions, test counts, and server structure
- Development conventions refreshed with current SDK features and test counts
- ADR-004 written documenting all v0.3 architectural decisions
- Multi-tenant demoted to "experimental" with clear documentation that data isolation is not implemented

---

## v0.3.0 — Advanced Features (2026-04-24)

### Added (server)
- LLM-backed memory compiler (`LLMCompiler` using OpenAI chat completions)
- Embedding generation during compilation (OpenAI + stub providers)
- Semantic search via pgvector cosine similarity with `semantic=true` query param
- Temporal reasoning in context assembly (+3 bonus for valid, -4 penalty for expired memories)
- Memory conflict resolution (Jaccard similarity, auto-supersede older overlapping memories)
- Webhook event hooks (`episode.created`, `memories.compiled`, `subject.deleted`)
- API key authentication middleware (`X-API-Key` header)
- Rate limiting middleware (per-IP sliding window)
- Multi-tenant header extraction middleware (`X-Tenant-ID`, experimental)
- Coding agent example (`coding-agent-python/`)

---

## v0.2.0 — Production Hardening (2026-04-24)

### Added (server)
- Idempotent memory compilation (only uncompiled episodes processed)
- Pluggable `BaseCompiler` protocol with `HeuristicCompiler`
- Token-bounded context assembly with configurable budget
- Ranked retrieval (kind priority × recency × task-keyword relevance)
- Structured error responses with consistent JSON shape
- Request ID middleware (`X-Request-ID` header)
- CORS configuration
- Health endpoints (`/healthz`, `/readyz`)
- Structured logging via structlog (JSON in production, console in dev)

### Added (SDKs)
- Python SDK 0.2.0 — typed exceptions (`StatewaveAPIError`, `StatewaveConnectionError`, `StatewaveTimeoutError`), async client
- TypeScript SDK 0.2.0 — typed errors, full type exports

### Added (examples)
- Support agent example (2-session demo with ranked context)

---

## v0.1.0 — Local MVP (2026-04-24)

### Added
- Core domain model (Episode, Memory, ContextBundle)
- FastAPI server with 6 endpoints
- Heuristic memory compiler (regex/pattern extraction)
- Context assembly with token estimation
- PostgreSQL + pgvector schema with Alembic migrations
- Docker Compose local deployment
- Python SDK 0.1.0
- TypeScript SDK 0.1.0
- Minimal quickstart example
- CI/CD pipeline (GitHub Actions)
