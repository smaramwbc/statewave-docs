# Markdown / docs connector

Turn a folder of Markdown files — including ADRs, RFCs, and architecture notes — into **decision and project memory** so an agent can answer *"what did we decide about authentication?"* by recalling the actual decision documents instead of regenerating an opinion.

> **Status:** Phase 1. Available in the [statewave-connectors](https://github.com/smaramwbc/statewave-connectors) repo. Planned npm package: `@statewavedev/connectors-markdown`.

## What it ingests

The connector recursively scans a folder for `.md` and `.mdx` files. It skips `node_modules`, `.git`, `dist`, `build`, `coverage`, `.next`, `.turbo`, and `.cache` automatically.

Each file becomes one episode. The connector detects **decision-style** documents from path/filename and tags them with a more specific kind:

| Path / filename pattern | Episode `kind` |
|---|---|
| Anything under `adrs/` or filename like `ADR-0042-licensing.md` | `docs.adr` |
| Anything under `rfcs/` or `RFC-0007-protocol.md` | `docs.rfc` |
| Filenames containing `decision`, paths under `architecture/` | `docs.decision` |
| Everything else | `docs.page` |

The H1 of each document is used as the title. YAML frontmatter (when present) is parsed and placed under `metadata.frontmatter`; a `title:` in frontmatter overrides the derived title.

## Recommended subject

```
subject = repo:<owner>/<repo>
```

Use the same `repo:owner/name` you use for the GitHub connector, so an agent asking *"what's been decided about repo X?"* picks up the decision docs and the GitHub history under the same subject.

For org-wide decision docs that don't belong to a single repo, use `workspace:<your-workspace>`.

## Episode metadata

Each Markdown episode includes:

- `path` — the file's path relative to the scan root
- `hash` — short content hash (used in idempotency)
- `size` — file size in bytes
- `title` — derived or frontmatter-supplied
- `frontmatter` — parsed YAML, when present

## Idempotency

Each episode's `idempotency_key` is derived from the file's **path** and **content hash**. Practical consequences:

- Re-running a sync without changes is a no-op.
- Editing a doc produces a **new** episode (the prior version remains in the timeline). You get a real "what changed when" history, not a destructive overwrite.
- Renaming a file produces a new episode under the new path. If you want to merge histories, retire the old subject pointer and re-sync.

## Quickstart

```bash
export STATEWAVE_URL=http://localhost:8000
export STATEWAVE_API_KEY=...

# Preview
statewave-connectors sync markdown \
  --path ./docs \
  --subject repo:smaramwbc/statewave \
  --dry-run

# Ingest
statewave-connectors sync markdown \
  --path ./docs \
  --subject repo:smaramwbc/statewave
```

## Filtering

The connector accepts `--include` / `--exclude` to slice on path substrings:

```bash
# Skip an internal-only folder
statewave-connectors sync markdown \
  --path ./docs \
  --subject repo:smaramwbc/statewave \
  --exclude internal-only \
  --dry-run

# Only the ADRs
statewave-connectors sync markdown \
  --path ./docs \
  --subject repo:smaramwbc/statewave \
  --include adrs/ \
  --dry-run
```

## Local-first

The Markdown connector makes **no** network calls except the optional Statewave ingest. There are no credentials to configure, no third-party services to depend on. If you only ever use this connector, you also never need any token from any other connector.

## See also

- [Quickstart](quickstart.md) — full walkthrough
- [Subject strategy](subject-strategy.md) — repo memory and decision memory
- [Concepts](concepts.md) — kinds, idempotency, metadata
- [Privacy & redaction](privacy-redaction.md) — local-first, dry-run-first
- Source code: [packages/markdown in statewave-connectors](https://github.com/smaramwbc/statewave-connectors/tree/main/packages/markdown)
