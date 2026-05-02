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
| **Source** | The 17 curated docs in this repo (see [Curated source set](#curated-source-set)) |
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
| Essentials | `getting-started.md`, `product.md`, `api/v1-contract.md`, `architecture/overview.md`, `why-statewave.md` |
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

```
statewave-docs/*.md
        │
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
                                        compiler the server is configured
                                        for (see "Compiler choice" below)
```

### Compiler choice

The bootstrap script doesn't pick a compiler — the Statewave server does, via the `STATEWAVE_COMPILER_TYPE` env var on whichever instance the script targets. Either compiler works; the trade-off is extraction quality vs operational cost.

| Compiler | When it runs | What it produces |
|---|---|---|
| `heuristic` (default) | Whenever `STATEWAVE_COMPILER_TYPE` is unset | Regex-driven extraction of profile-fact / episode-summary / procedure memories. Fast, free, no LLM dependency. Good for support-chat shapes; tends to under-extract from long technical prose. |
| `llm` | Set `STATEWAVE_COMPILER_TYPE=llm` (+ `STATEWAVE_LITELLM_API_KEY` for the provider chosen by `STATEWAVE_LITELLM_MODEL`) | LLM-driven semantic extraction, ~2× memory density, captures content that doesn't match heuristic patterns. Recommended for the docs pack — it surfaces facts from `architecture/`, `deployment/`, `dev/` that the heuristic misses. |

Production (`statewave-api.fly.dev`) runs the LLM compiler with model `gpt-4o-mini` (the default for `STATEWAVE_LITELLM_MODEL`). After flipping `STATEWAVE_COMPILER_TYPE`, re-run the refresh workflow once to recompile against the new compiler.

Each section becomes one immutable episode. The compiler runs once, producing summaries the support agent can retrieve via `POST /v1/context`. Provenance is preserved end-to-end: a retrieved memory points at its source episode, which carries `provenance.doc_path` and `payload.breadcrumb` (e.g. *"Architecture Overview › Compilation pipeline"*) — that's your citation.

## Bootstrapping the pack

From the `statewave/` repo, with the server running:

```bash
python -m scripts.bootstrap_docs_pack
```

By default the script reads docs from a sibling `../statewave-docs/` directory. Override with:

```bash
python -m scripts.bootstrap_docs_pack --docs-path /path/to/statewave-docs
# or
STATEWAVE_DOCS_PATH=/path/to/docs python -m scripts.bootstrap_docs_pack
```

Useful flags:

| Flag | Purpose |
|---|---|
| `--dry-run` | Parse and chunk only — no HTTP calls. Prints a section preview. |
| `--purge` | Delete existing episodes for the subject and rebuild from scratch. |
| `--docs-path PATH` | Point at a non-default `statewave-docs` checkout. |

The script will refuse to run if the subject already has episodes, unless you pass `--purge`. Each episode carries a `content_hash` in `provenance` so future incremental-refresh tooling can diff section-by-section without re-ingesting unchanged content.

## Refreshing when docs change

### Automated (production)

A GitHub Actions workflow at [`.github/workflows/refresh-support-docs.yml`](https://github.com/smaramwbc/statewave-docs/blob/main/.github/workflows/refresh-support-docs.yml) (in this repo) rebuilds the production pack on every push to `main` that touches a markdown file or the chunker. It also exposes a manual `workflow_dispatch` trigger for ad-hoc refreshes.

| | |
|---|---|
| **Lives in** | `statewave-docs/.github/workflows/refresh-support-docs.yml` |
| **Triggers** | `push` to `main` (filtered to `**/*.md` + `scripts/docs_loader.py`); `workflow_dispatch` for manual runs |
| **Mode** | Full purge-rebuild via `bootstrap_docs_pack.py --purge` |
| **Required secrets** | `STATEWAVE_URL`, `STATEWAVE_API_KEY` — set in this repo's *Settings → Secrets and variables → Actions* |
| **Concurrency** | Serialized (`cancel-in-progress: false`) — a queued push waits for the running purge instead of cancelling it mid-stream |
| **Verification** | Post-run sanity check hits `GET /v1/timeline?subject_id=statewave-support-docs` and fails the workflow if the subject ends up with 0 episodes. Belt-and-suspenders against a "bootstrap exits 0 but pack is empty" regression — the failure mode that previously produced hallucinated answers in the marketing widget. |
| **On failure** | Workflow shows a red ❌ on the commit; production pack is left in whatever state it was in before the run started (purge runs *first*, so a failure during ingest leaves an empty subject — that surfaces immediately on the support widget). Re-run via the Actions tab once the underlying issue is fixed. |

Set up:

1. In this repo's *Settings → Secrets and variables → Actions*, add `STATEWAVE_URL` (e.g. `https://statewave-api.fly.dev`) and `STATEWAVE_API_KEY` (a key with write access to the subject).
2. Push any docs change to `main`, or click *Run workflow* on the *Refresh support-docs memory pack* action. Watch the run in the Actions tab.
3. The first run also serves as the initial bootstrap if production never had the pack.

### Manual

The same script runs locally for development or one-off refreshes:

```bash
cd /path/to/statewave
STATEWAVE_URL=https://statewave-api.fly.dev \
STATEWAVE_API_KEY=... \
python -m scripts.bootstrap_docs_pack --docs-path /path/to/statewave-docs --purge
```

Useful for testing chunker changes against the full corpus before pushing.

### Why full rebuild and not incremental

The pack is small (~180 sections, ~80 KiB of body text); a full rebuild takes seconds. The complexity cost of incremental refresh — diffing per-section `content_hash`, superseding only changed memories, handling deleted sections — is not worth paying for a corpus this size. The `content_hash` field is already in episode `provenance` so the upgrade path is open whenever the corpus is large enough to justify it.

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
