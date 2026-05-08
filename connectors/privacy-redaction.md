# Privacy & redaction

Statewave Connectors are designed around one rule: **never ingest data without explicit user command**. This page explains the safety primitives every official connector inherits, and the boundaries you should expect.

## Defaults

- **Connectors do nothing unless explicitly run.** There is no auto-discovery, no background poll, no "ingest everything you can find" mode.
- **Dry-run is the default in examples and docs.** Every example shows `--dry-run` first.
- **`STATEWAVE_URL` must be set before any ingestion can happen.** The CLI refuses to ingest if it's missing.
- **Per-connector credentials.** The GitHub connector never reads Slack tokens, and vice versa. You install only the connectors you need; you supply only the credentials those connectors require.
- **No telemetry. No phone-home.** Source state (cursors) lives where you put it.

## Dry-run

`--dry-run` runs the read path and the mapper, prints the resulting episodes, and **does not** call the Statewave ingest API.

```bash
statewave-connectors sync github --repo acme/widgets --subject repo:acme/widgets --dry-run
statewave-connectors sync markdown --path ./docs --subject repo:acme/widgets --dry-run
```

Dry-run is the right way to discover surprises *before* they're stored.

## Include / exclude filters

Use `--include` and `--exclude` to slice what a connector reads. Filters are applied **at read time**, so an excluded source is never even mapped, let alone ingested.

```bash
# Only issues, no PRs, no releases
statewave-connectors sync github \
  --repo acme/widgets \
  --include issues

# Skip a folder
statewave-connectors sync markdown \
  --path ./docs \
  --exclude internal-only
```

## `--since` and `--max-items`

Cap the temporal and quantitative reach of any sync:

```bash
statewave-connectors sync github \
  --repo acme/widgets \
  --since 2026-01-01 \
  --max-items 100 \
  --dry-run
```

Useful when you're testing a new connector against a busy repo, or when you only want a recent slice of history.

## Built-in best-effort redaction

Each redaction rule is opt-in per sync:

- `--redact-email` — strips `name@domain` patterns
- `--redact-phone` — strips long digit runs that look like phone numbers
- `--redact-secrets` — best-effort for common token shapes: GitHub tokens, OpenAI/Anthropic keys, AWS access keys, Slack tokens, JWTs, PEM private-key blocks

Connector libraries also accept programmatic `redaction.rules: [{ name, pattern, replacement }]` for custom regex.

> **Best-effort detection is not perfect detection.** Treat redaction as defense-in-depth, not as a substitute for keeping secrets out of shared systems in the first place. Public docs that mention secrets should be sanitized at the source, not relied on to be scrubbed in transit.

## Connector-specific credentials

The principle is one-way:

- If you only use Markdown, you never need a GitHub token.
- If you only use GitHub, you never need Slack credentials.
- The convenience meta-package `@statewavedev/connectors` exists for ergonomics — it does **not** load credentials, it just re-exports types and factories.

A breakage in one connector cannot leak into another's credential surface.

## No need to install or configure unused connectors

Connectors are independent npm packages. Each one declares its own dependencies. Installing `@statewavedev/connectors-github` does not pull in Slack, Notion, or Gmail dependencies. There is no transitive bloat path through "the connectors package".

## Local-first behaviour

- The Markdown connector is fully local — no network calls beyond the optional Statewave ingest.
- The GitHub connector talks only to `api.github.com` (configurable for GHES).
- Source state (resume cursors) is stored locally — in memory, in a file you specify, or wherever your custom store puts it.

## See also

- [Privacy & data flow](../architecture/privacy-and-data-flow.md) — the broader Statewave privacy model
- [Quickstart](quickstart.md) — dry-run-first walkthrough
- [Concepts](concepts.md) — episodes are immutable; ingestion is explicit
