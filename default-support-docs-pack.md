# Default support docs memory pack

Statewave ships with a **default, docs-only memory pack** so a fresh
deployment can power a useful support agent on day one — without any
ML labeling, no hand-curated Q&A list, and no source code. The pack is
built from this very repository (`statewave-docs/`) using the real
`episodes → compile → memories` pipeline. There is nothing magic about
it: it's a regular Statewave subject populated by a bootstrap script.

## What the pack is

| | |
|---|---|
| **Subject ID** | `statewave-support-docs` |
| **Source** | The 18 curated docs in this repo (see [Curated source set](#curated-source-set)) |
| **Episode source** | `statewave-docs` |
| **Episode type** | `doc_section` |
| **Pipeline** | Markdown chunked at H1/H2/H3 → ingested as episodes → compiled with the standard heuristic compiler |
| **Pack version** | `1` (carried in episode `provenance.pack_version`) |

The script lives in [`statewave/scripts/bootstrap_docs_pack.py`](https://github.com/smaramwbc/statewave/blob/main/scripts/bootstrap_docs_pack.py) and the chunker is in [`statewave/scripts/docs_loader.py`](https://github.com/smaramwbc/statewave/blob/main/scripts/docs_loader.py).

## What it is intended for

Out-of-the-box answers to questions a new user, operator, or evaluating engineer would ask:

- Product positioning ("what is Statewave?", "why over alternatives?")
- Setup and getting started
- Deployment recipes (Docker, bare metal, Fly.io, Railway)
- Compiler / privacy / scaling / ranking guidance
- Migrations, backup/restore, troubleshooting playbooks
- API contract reference

## What it is **not** intended for

- ❌ Knowledge of the user's specific deployment (instance health, env vars, live errors)
- ❌ Live GitHub issues or work in progress
- ❌ Source-code-only details that aren't published in the docs
- ❌ ADR rationales (decision history) — excluded as not directly user-facing
- ❌ Speculative roadmap items
- ❌ A general-purpose autonomous assistant

When the support agent encounters a question outside this scope, the expected behavior is to say so plainly and route the user to [`SUPPORT.md`](SUPPORT.md) or [the issue tracker](https://github.com/smaramwbc/statewave/issues). Out-of-scope answers are a feature, not a bug.

## Curated source set

| Tier | Files |
|---|---|
| Essentials | `getting-started.md`, `product.md`, `subject-design.md`, `api/v1-contract.md`, `architecture/overview.md`, `why-statewave.md` |
| Operations | `deployment/guide.md`, `deployment/troubleshooting.md`, `deployment/hardware-and-scaling.md`, `architecture/privacy-and-data-flow.md`, `SECURITY.md` |
| Advanced features | `architecture/compiler-modes.md`, `architecture/ranking.md`, `deployment/migrations.md`, `dev/backup-restore.md`, `architecture/repo-map.md` |
| Routing | `README.md`, `SUPPORT.md` |

**Excluded** (with reason):

| File | Why excluded |
|---|---|
| `adrs/*.md` | Decision-record style — historical, not user-facing |
| `CHANGELOG.md` | Reads like git history; not actionable for support |
| `roadmap.md` | Speculative; would let the agent claim unshipped behavior |
| `dev/conventions.md` | Internal developer guide |
| `dev/snapshots.md` | Gated operator feature; not part of standard user workflow |
| `.github/PULL_REQUEST_TEMPLATE.md` | Internal process |

The full allowlist lives in `MANIFEST` at the top of `scripts/docs_loader.py`. Edit there to evolve the pack.

## How it's built

The pack is built **once at release time** and shipped inside the Statewave server image. A self-hosted operator never has to run a bootstrap step against their own infrastructure to get docs-grounded answers — pulling a new image is enough.

```
statewave-docs/*.md
        │
        ▼
[build] scripts/build_support_pack.py    chunks docs, ingests + compiles
        │                                against a temporary build-time
        │                                subject, then serializes everything
        │                                back out as JSONL with each episode
        │                                keyed by content_hash so memory
        │                                provenance can be remapped on every
        │                                fresh import.
        ▼
[1] docs_loader.chunk_markdown          split each file at H1/H2/H3
        │                               (skipping fenced code blocks)
        ▼
[2] DocSection                          {doc_path, heading_path, body,
        │                                content_hash, url}
        ▼
[3] POST /v1/episodes/batch             one episode per section
        │                               source="statewave-docs"
        │                               type="doc_section"
        │                               provenance carries content_hash
        ▼
[4] POST /v1/memories/compile           extracts memories using whichever
        │                               compiler the build-time server is
        │                               configured for (see "Compiler
        │                               choice" below). Memories carry
        │                               source_episode_ids that point back
        │                               at the section content_hash.
        ▼
[5] serialise to JSONL                  server/starter_packs/
                                        statewave-support-agent/
                                        {episodes,memories,manifest}.jsonl
                                        — the bundled image artifact.
```

The runtime side is then symmetrical: importing the pack writes the same episodes + memories into the live `statewave-support-docs` subject, with `source_episode_ids` remapped from each episode's `content_hash` to its freshly-minted UUID. Memories arrive already compiled — there is no per-install LLM call.

### Compiler choice

The build script doesn't pick a compiler — the Statewave server it points at does, via the `STATEWAVE_COMPILER_TYPE` env var on whichever instance the build runs against. Either compiler works; the trade-off is extraction quality vs operational cost.

| Compiler | When it runs | What it produces |
|---|---|---|
| `heuristic` (default) | Whenever `STATEWAVE_COMPILER_TYPE` is unset | Regex-driven extraction of profile-fact / episode-summary / procedure memories. Fast, free, no LLM dependency. Good for support-chat shapes; tends to under-extract from long technical prose. |
| `llm` | Set `STATEWAVE_COMPILER_TYPE=llm` (+ `STATEWAVE_LITELLM_API_KEY` for the provider chosen by `STATEWAVE_LITELLM_MODEL`) | LLM-driven semantic extraction, ~2× memory density, captures content that doesn't match heuristic patterns. Recommended for the docs pack — it surfaces facts from `architecture/`, `deployment/`, `dev/` that the heuristic misses. |

Production (`statewave-api.fly.dev`) builds with the LLM compiler against `gpt-4o-mini` (the default for `STATEWAVE_LITELLM_MODEL`). The bundled JSONL is therefore LLM-quality memory at runtime cost zero — the LLM bill is paid once per release, not once per install.

Each section becomes one immutable episode. The compiler runs once at build time, producing summaries the support agent can retrieve via `POST /v1/context`. Provenance is preserved end-to-end: a retrieved memory points at its source episode, which carries `provenance.doc_path` and `payload.breadcrumb` (e.g. *"Architecture Overview › Compilation pipeline"*) — that's your citation.

## Auto-update on container restart

Every restart of `statewave-api` calls the version-aware reseed endpoint, which compares the bundled pack's manifest version against the version stamped on the live subject's metadata:

| State | Action |
|---|---|
| Subject empty | Seed: import every episode + memory from the bundled pack. |
| Subject populated, **versions match** | No-op. The endpoint returns `updated=false`; no rows are touched. |
| Subject populated, **versions differ** | Selective purge of pack-owned rows + reimport at the new version. Operator-added rows on the same subject (rows whose metadata doesn't carry `starter_pack_id`) are preserved. |

This means an operator pulling a newer image picks up docs updates automatically — no manual click, no GitHub Actions step, no `bootstrap_docs_pack` invocation. The image *is* the source of truth.

| Env var | Default | Effect |
|---|---|---|
| `STATEWAVE_AUTO_UPDATE_SUPPORT_PACK` | `true` | Set to `false` to disable auto-update. The drawer's manual Restore still works. |
| `STATEWAVE_BOOTSTRAP_DOCS_PACK` | (legacy) | When `true` AND `STATEWAVE_DOCS_PATH` points at a mounted docs corpus, runs `bootstrap_docs_pack.py` against `/docs` instead — useful for dev environments that want to refresh from a host-mounted docs checkout without rebuilding the image. Skipped when no mount is present. |

## Inspecting state

```
GET /admin/memory/support/state
```

Returns the bundled pack version, the version currently installed in the live subject, episode + memory counts split by ownership, and the last reseed's reason and timestamp. The admin drawer uses this to render the *installed → available* badge and the "last refreshed" line; an operator can hit it directly to confirm what's running.

```
POST /admin/memory/support/reseed
{
  "reason": "quarterly refresh",
  "force": false
}
```

Without `force`, the reseed is version-aware and no-ops when the live subject is already current. With `force=true`, it reimports unconditionally — that's what the drawer's Restore button passes when an operator manually triggers the action. Either way, the reseed is **selective**: only rows tagged with `metadata.starter_pack_id == "statewave-support-agent"` (or the legacy `metadata.pack == "statewave-support-docs"` for pre-versioning installs) are deleted before reimport. Operator-added rows on the same subject survive.

The `reason` is recorded on every imported row's metadata and surfaced as the *last refreshed* line in the admin drawer. Provide a short human-readable string when refreshing, especially in shared environments — it's the only audit breadcrumb left on the subject.

## Refreshing when docs change

### Release flow (the path that ships content to operators)

The bundled JSONL is regenerated from the current docs corpus by:

```bash
cd /path/to/statewave
python -m scripts.build_support_pack
```

The script chunks the docs, runs ingest + compile against a temporary build-time subject, fetches everything back, remaps episode IDs to stable content hashes, and writes:

- `server/starter_packs/statewave-support-agent/episodes.jsonl`
- `server/starter_packs/statewave-support-agent/memories.jsonl`
- `server/starter_packs/statewave-support-agent/manifest.json` (with a date-stamped version)

Commit the diff, push, build a new `statewave-api` image. From there, every operator pulling the new image gets the updated content on next restart via the auto-update path above.

| Flag | Purpose |
|---|---|
| `--docs-path PATH` | Point at a non-default `statewave-docs` checkout. |
| `--keep-temp` | Leave the temp build subject around for inspection (otherwise it's deleted on success). |

`STATEWAVE_URL` defaults to `http://localhost:8100`; `STATEWAVE_API_KEY` is read from the environment when the build-time server requires auth. `SUPPORT_PACK_VERSION` overrides the auto-derived version string when you want a deterministic value.

### Hot-refresh against a running production instance (legacy)

The pre-bundled-pack workflow at [`.github/workflows/refresh-support-docs.yml`](https://github.com/smaramwbc/statewave-docs/blob/main/.github/workflows/refresh-support-docs.yml) still exists. It runs `bootstrap_docs_pack.py --purge` directly against a target Statewave instance, so a docs-only push to `main` rebuilds the live subject without waiting for an image rebuild.

| | |
|---|---|
| **Lives in** | `statewave-docs/.github/workflows/refresh-support-docs.yml` |
| **Triggers** | `push` to `main` (filtered to `**/*.md` + `scripts/docs_loader.py`); `workflow_dispatch` for manual runs |
| **Mode** | Full purge-rebuild via `bootstrap_docs_pack.py --purge` |
| **Required secrets** | `STATEWAVE_URL`, `STATEWAVE_API_KEY` |
| **Concurrency** | Serialized (`cancel-in-progress: false`) |
| **Verification** | Post-run sanity check hits `GET /v1/timeline?subject_id=statewave-support-docs` and fails if the subject ends up empty |
| **On failure** | Production pack is left in whatever state it was in before the run started (purge runs first; a failure during ingest leaves an empty subject — that surfaces immediately on the support widget). Re-run via the Actions tab. |

Use this workflow when you want a docs change to land on production *between* image rebuilds. Otherwise, the release flow is enough — the next image pull carries the new content.

### Local dev refresh

If you're iterating on docs locally and want to see the change in your dev Statewave instance immediately, two options:

```bash
# Option A — refresh from a host-mounted /docs (uses the dev-only env vars)
docker exec statewave-api python -m scripts.bootstrap_docs_pack --purge

# Option B — regenerate the bundled JSONL on your host, then restart the container
python -m scripts.build_support_pack
docker compose restart api    # auto-update fires, picks up the new pack
```

Option A is faster for one-off iteration; option B exercises the same code path operators see when they upgrade an image.

### Why selective purge instead of full wipe

Operators sometimes append their own episodes to `statewave-support-docs` — internal runbooks, customer-specific FAQs, redacted incident playbooks. The auto-update path must not destroy that content. Selective purge drops only the rows whose metadata identifies them as belonging to this pack (`starter_pack_id == "statewave-support-agent"` or the legacy `pack == "statewave-support-docs"`); everything else stays put. The admin drawer's Restore action uses the same selective filter, so manual restore is non-destructive too.

The `content_hash` field is preserved on every episode for future incremental-refresh tooling — diffing per-section to update only changed sections — but the corpus is currently small enough (~210 sections, ~110 KiB of body text) that a full pack-owned purge runs in well under a second.

## Using the pack from a support agent

Application-level pseudocode:

```python
from statewave import StatewaveClient

sw = StatewaveClient("http://localhost:8100")
ctx = sw.get_context(
    subject_id="statewave-support-docs",
    task=user_question,
    max_tokens=600,
)
# ctx.assembled_context → drop into your LLM prompt
# ctx.provenance         → walk to source episodes for citations
```

A runnable example is at [`statewave-examples/support-agent-docs/`](https://github.com/smaramwbc/statewave-examples/tree/main/support-agent-docs).

## Provenance and trust

The pack is honest about what it knows:

- Every retrieved fact traces to a specific doc section (path + heading breadcrumb).
- The agent's system prompt forbids inventing API fields, config keys, or version-specific claims.
- The agent must distinguish *documented fact*, *best-effort suggestion based on docs*, and *out of scope*.

This is what makes the default pack shippable: it's not a chatbot pretending to know everything, it's a thin retrieval layer over the docs you already publish.
