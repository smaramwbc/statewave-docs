# GitHub connector

Turn a GitHub repository's history into **repo memory** so an agent can answer questions like *"what's the state of issue #42?"* or *"what did we decide about caching last quarter?"* — without you stuffing raw GitHub history into the prompt.

> **Status:** Phase 1. Available in the [statewave-connectors](https://github.com/smaramwbc/statewave-connectors) repo. Planned npm package: `@statewavedev/connectors-github`.

## What it ingests

| Source event | Episode `kind` |
|---|---|
| Issue opened | `github.issue.opened` |
| Issue closed | `github.issue.closed` |
| Issue comment | `github.issue.comment` |
| Pull request opened | `github.pr.opened` |
| Pull request closed (not merged) | `github.pr.closed` |
| Pull request merged | `github.pr.merged` |
| PR comment | `github.pr.comment` |
| PR review (approve / request changes / comment) | `github.pr.review` |
| Release published | `github.release.published` |

Merged PRs get a dedicated `github.pr.merged` episode summarizing the merge — useful for "what landed in this repo last week?" recall.

## Recommended subject

```
subject = repo:<owner>/<repo>
```

This matches how teams ask about their work — agents naturally phrase questions as *"what's going on in repo X?"*. If you need to scope further (per release, per area), use `metadata.related_subjects`:

```
metadata.related_subjects = ["pr:35", "author:smaram", "release:v0.7.1"]
```

See [subject strategy](subject-strategy.md) for the full pattern.

## Episode metadata

Every GitHub episode includes:

- `repo_owner`, `repo_name`
- `issue_number` or `pr_number` where applicable
- `author` (GitHub login)
- `labels` — array of label names
- `milestone` — title of the milestone, if set
- `state` — `open` / `closed`
- `merged` — boolean (PRs only)
- `created_at`, `updated_at`, `merged_at`
- `related_subjects` — additional handles for cross-subject retrieval

## Auth

```bash
export GITHUB_TOKEN=ghp_...
```

A token is **not strictly required** for public repos — the connector falls back to unauthenticated requests. But unauthenticated requests are rate-limited far more aggressively, so set the token whenever you can.

The GitHub connector reads only `GITHUB_TOKEN`. It does not need (and never reads) credentials for any other connector.

## Quickstart

```bash
export STATEWAVE_URL=http://localhost:8100
export STATEWAVE_API_KEY=...
export GITHUB_TOKEN=ghp_...

# Preview — no ingestion happens
statewave-connectors sync github \
  --repo smaramwbc/statewave \
  --subject repo:smaramwbc/statewave \
  --dry-run

# Ingest for real
statewave-connectors sync github \
  --repo smaramwbc/statewave \
  --subject repo:smaramwbc/statewave
```

## Filtering

Slice what gets read with `--include` / `--exclude`. The available groups are `issues`, `prs`, `comments`, `reviews`, `releases`.

```bash
# Just PRs and releases
statewave-connectors sync github \
  --repo smaramwbc/statewave \
  --subject repo:smaramwbc/statewave \
  --include prs,releases \
  --dry-run
```

Combine with `--since 2026-01-01` and `--max-items 100` to bound the run.

## Resuming and idempotency

Re-running `sync` is safe. Every episode has a stable `idempotency_key` derived from the **logical identity** of the event (e.g. `["github", owner, repo, "issue", number, kind]`). Editing the body of an issue does **not** create a new episode — Statewave deduplicates.

Use `--since` to limit re-reads to recent activity, or pass `--cursor` to resume from a specific point if you've stored one.

## See also

- [Quickstart](quickstart.md) — full walkthrough
- [Subject strategy](subject-strategy.md) — `repo:` and friends
- [Concepts](concepts.md) — episodes, kinds, idempotency keys
- [Privacy & redaction](privacy-redaction.md) — `--include`, `--exclude`, secret scrubbing
- Source code: [packages/github in statewave-connectors](https://github.com/smaramwbc/statewave-connectors/tree/main/packages/github)
