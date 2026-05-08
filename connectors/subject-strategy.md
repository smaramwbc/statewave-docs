# Subject strategy for connectors

Picking the right subject is the single most important decision when wiring up a connector. Subjects determine what episodes get compiled together and what your agent can recall in a single query.

> **Going deeper:** This page is the connector-specific cheat sheet. For the full architectural treatment — tenancy, granularity trade-offs, hierarchy, archival — read [Subject Design](../subject-design.md).

## Three rules

1. **Subjects are stable, low-cardinality identifiers.** Not free text. Not per-event ids.
2. **One episode has one primary subject.** Use `metadata.related_subjects` to cross-link.
3. **Pick the subject your agent will *ask about*.** "What's going on with Acme?" → `customer:acme`. "What did we decide about licensing?" → `repo:smaramwbc/statewave` with `decision:licensing` related.

## Patterns by use case

### Repo memory

```
subject = repo:smaramwbc/statewave
```

For: GitHub issues, PRs, comments, releases, ADRs, architecture docs that govern the repo, internal decision pages tied to the repo.

```
# GitHub PR
subject = repo:smaramwbc/statewave
metadata.related_subjects = ["pr:35", "author:smaram"]
```

### Customer memory

```
subject = customer:northwind-logistics
```

For: Zendesk tickets, Intercom conversations, Freshdesk replies, support-channel Slack threads.

```
# Zendesk ticket
subject = customer:acme
metadata.related_subjects = ["ticket:12345", "product:admin"]
```

### Community memory

```
subject = community:statewave
```

For: Discord channels and forums, public Slack communities, public GitHub discussions.

```
# Discord question
subject = community:statewave
metadata.related_subjects = ["user:discord-id", "topic:mcp"]
```

### Contact / relationship memory

```
subject = contact:person@example.com
```

For: Gmail threads, calendar invites, CRM-like signal.

```
# Gmail thread
subject = contact:person@example.com
metadata.related_subjects = ["company:acme"]
```

### Decision memory

```
subject = repo:smaramwbc/statewave        # if the decision governs a repo
subject = workspace:<your-workspace>      # if the decision is org-wide
metadata.related_subjects = ["decision:licensing"]
```

For: ADRs, RFCs, architecture notes, Notion decision docs.

### Workflow memory

```
subject = workflow:billing-reminders
```

For: n8n executions, Zapier zap runs, internal job queues.

```
# n8n execution
subject = workflow:billing-reminders
metadata.related_subjects = ["customer:acme"]
```

## Quick reference

| Source | Default subject | Common related subjects |
|---|---|---|
| GitHub repo | `repo:<owner>/<name>` | `pr:<n>`, `author:<login>` |
| Markdown / ADRs | `repo:<owner>/<name>` | `decision:<topic>` |
| Slack support channel | `customer:<account>` | `team:<workspace>` |
| Discord forum | `community:<server>` | `topic:<channel>`, `user:<id>` |
| Zendesk ticket | `customer:<account>` | `ticket:<id>`, `product:<area>` |
| Intercom conversation | `customer:<account>` *or* `contact:<email>` | `conversation:<id>` |
| Notion decision doc | `repo:<owner>/<name>` | `decision:<topic>` |
| Gmail thread | `contact:<email>` | `company:<domain>` |
| n8n / Zapier run | `workflow:<id>` | `customer:<account>` |

## Anti-patterns

- **Per-message subjects.** `subject = message:abc123` defeats memory compilation; one memory per message and no recall by topic.
- **Time-based subjects.** `subject = 2026-Q1` makes recall painful and undermines drift-resistance.
- **Mixed cardinality.** Don't mix `customer:acme` and `customer:acme/north-america/team-7` for the same agent. Pick one granularity and stay there.

## See also

- [Subject Design](../subject-design.md) — the deep architectural treatment
- [Concepts](concepts.md) — how subject fits with kind, episode, idempotency
- [Privacy & redaction](privacy-redaction.md) — scoping what each connector reads
