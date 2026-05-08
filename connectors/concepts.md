# Connector Concepts

A connector turns events from a source system — GitHub, Slack, a folder of Markdown — into a sequence of normalized **episodes** that Statewave compiles into durable memory. This page walks through the seven concepts that show up in every connector.

## Source event

The raw shape a source system gives you. A GitHub issue payload. A Slack message. A Markdown file on disk. Source events are **never** the unit Statewave reasons about; they're just the input.

A connector's job is to map source events into the normalized [episode](#episode) shape, deterministically, with a stable identity.

## Episode

The single normalized shape every connector produces. It is intentionally small and source-agnostic.

```ts
interface StatewaveEpisode {
  subject: string;
  kind: string;
  text: string;
  occurred_at: string;
  source: {
    type: string;
    id: string;
    url?: string;
  };
  metadata?: Record<string, unknown>;
  idempotency_key: string;
}
```

Every field below is a slice of this shape.

## Subject

The memory subject this episode is *about*. Subjects are how Statewave groups episodes into compiled memories — agents query memory by subject. Use stable, low-cardinality identifiers:

```
repo:smaramwbc/statewave
customer:northwind-logistics
community:statewave
contact:person@example.com
decision:licensing
workflow:billing-reminders
```

Subject choice is the most important decision you make per connector. See [subject-strategy.md](subject-strategy.md) for full guidance, and the deeper [Subject Design](../subject-design.md) doc for the architectural treatment.

## Kind

A dotted, source-prefixed event kind. Examples:

- `github.issue.opened`
- `github.pr.merged`
- `docs.adr`
- `slack.message.posted`
- `zendesk.ticket.solved`

Kinds are descriptive — Statewave doesn't require any particular value. They exist so retrieval and analytics can filter (`kinds: ["github.pr.merged"]`).

## Source pointer

A pointer back to the original record:

- `source.type` — typed identifier of the source record (e.g. `github.issue`, `markdown`, `zendesk.ticket`)
- `source.id` — stable id within that source (e.g. `acme/widgets#42`)
- `source.url` — optional canonical URL

The source pointer never *replaces* the original record. If your agent needs the full body, click through the URL. The episode is what gets compiled and recalled.

## Metadata

A free-form bag of typed signal attached to the episode: author, labels, milestone, state, related subjects, etc. Connectors should be conservative — anything that isn't useful for retrieval or downstream consumers belongs on the source, not in the episode.

A common pattern: `metadata.related_subjects: string[]` so a single episode can be surfaced under multiple subjects (`pr:35`, `author:linus`) when querying.

## Idempotency key

A stable key derived from the **logical identity** of the event, not its current body. Re-running a sync against the same source produces the same key, so Statewave deduplicates rather than double-storing.

Good idempotency keys look like:

```
github + acme + widgets + issue + 42 + github.issue.opened
markdown + repo:acme/widgets + docs/adr/0001.md + <content-hash>
```

Editing the body of a GitHub issue produces the same key (logical identity unchanged). Editing the file content of an ADR produces a new key (because the content hash is part of the key) — so you keep the prior version in the timeline.

## Compile memories

Once episodes have been ingested, Statewave compiles them into durable memories per subject. Compilation can run automatically (when episodes accumulate) or be triggered explicitly via the API or the MCP `statewave_compile_subject` tool.

Memories are the unit your agents recall. Episodes are the *evidence*; memories are the *understanding*.

## Retrieve context

When an agent has a question, it asks Statewave for **context** — a compact, ranked, token-bounded selection of memories for the relevant subject(s). Context is what goes into the agent's prompt, instead of raw chat history or a full RAG dump.

Connectors are how that context gets fed in the first place. The MCP server (or the SDKs) is how it gets out.

## See also

- [Quickstart](quickstart.md) — run a connector end-to-end
- [Subject strategy](subject-strategy.md) — pick the right subject for your use case
- [Subject Design](../subject-design.md) — the deep architectural treatment
- [API v1 Contract](../api/v1-contract.md) — the underlying ingest and context APIs
- [Architecture Overview](../architecture/overview.md) — record → compile → context → govern
