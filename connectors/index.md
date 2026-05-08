# Connectors

Statewave Connectors feed real-world events into Statewave so agents can remember projects, customers, communities, docs, tickets, emails, and workflows — not just live chat transcripts.

A connector is a small, focused package that reads from one source, normalizes its events into the Statewave [episode schema](concepts.md), and lets the CLI or your own code ingest them. Statewave compiles those episodes into durable memories per subject, and serves compact context to your agents on demand.

> **Status:** Phase 1 packages (Core, CLI, MCP server, GitHub, Markdown) ship with the [statewave-connectors](https://github.com/smaramwbc/statewave-connectors) repository. Other connectors are planned — see the [roadmap](roadmap.md).

## What's available

### MCP server

Connect Statewave memory to any MCP-compatible client — coding assistants, agent loops, custom tools. Vendor-neutral by design. → [MCP server](mcp.md)

### GitHub

Turn issues, pull requests, reviews, releases, and discussions into **repo memory**. → [GitHub connector](github.md)

### Markdown / docs

Turn local docs, ADRs, RFCs, and decision notes into **project memory** — the team's actual reasoning, not a re-derivation of it. → [Markdown connector](markdown.md)

### Slack / Discord — *planned*

Turn community and team conversations into **support and community memory** for shared channels and forums.

### Zendesk / Intercom / Freshdesk — *planned*

Turn support tickets and conversations into **customer memory**, scoped per account.

### Notion / Gmail — *planned*

Turn workspace decision docs and inbox threads into **decision and relationship memory**.

### n8n / Zapier — *planned*

Feed workflow events into Statewave so agents have **workflow memory** without you writing custom integration code.

## Modular by design

Connectors are developed as a monorepo but published as **separate, independent packages**. You install only what you need.

```bash
# Planned package names — published in a follow-up release of statewave-connectors
npm install @statewavedev/connectors-github
npm install @statewavedev/connectors-markdown
npm install @statewavedev/mcp-server
```

A convenience meta-package `@statewavedev/connectors` re-exports the official connectors for the rare case where you want them all at once. **It is not required for normal usage** and not the recommended install path.

You never need to install Slack, Gmail, Zendesk, or Notion to use the GitHub connector. Each connector pulls only the credentials and dependencies it actually uses.

## Where to start

- New here? **[Quickstart →](quickstart.md)**
- Want the model? **[Concepts: episode, subject, kind →](concepts.md)**
- Picking subjects? **[Subject strategy →](subject-strategy.md)**
- Worried about data? **[Privacy & redaction →](privacy-redaction.md)**
- Building a new connector? See [contributing in the connectors repo](https://github.com/smaramwbc/statewave-connectors/blob/main/docs/contribution-guide.md).

## See also

- [Subject Design](../subject-design.md) — the deep architectural treatment of subjects in Statewave
- [API v1 Contract](../api/v1-contract.md) — the underlying ingest and context APIs that connectors call
- [Architecture Overview](../architecture/overview.md) — how episodes become memory becomes context
