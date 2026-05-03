# Community Guide

Statewave is built in the open. This guide explains how the community works — where to ask questions, where to propose changes, and how we balance an open project with a sustainable commercial path.

## Where to post what

| Channel | What it's for |
|---|---|
| **[GitHub Discussions](https://github.com/smaramwbc/statewave/discussions)** | Questions, ideas, RFCs, integrations, use cases, roadmap input, "show and tell" |
| **[GitHub Issues](https://github.com/smaramwbc/statewave/issues)** | Confirmed, reproducible bugs and concrete implementation tasks |
| **Pull Requests** | Code, docs, and config changes (see [CONTRIBUTING.md](https://github.com/smaramwbc/statewave/blob/main/CONTRIBUTING.md)) |
| **[security@statewave.ai](mailto:security@statewave.ai)** | Security vulnerabilities — never post these publicly. See [SECURITY.md](https://github.com/smaramwbc/statewave/blob/main/SECURITY.md) |
| **[licensing@statewave.ai](mailto:licensing@statewave.ai)** | Commercial licensing, private terms, enterprise procurement |

Rule of thumb: **if you can describe a clean reproduction or a concrete change, open an Issue or PR. Otherwise, start in Discussions.**

## Discussion categories

The repo uses these Discussions categories:

- **Announcements** — releases, roadmap milestones, licensing updates (maintainer-posted)
- **General** — open questions, broad conversation
- **Q&A** — setup help, usage questions, troubleshooting, deployment help
- **Show and Tell** — agents, integrations, memory workflows, evals, benchmarks
- **Ideas & Feature Requests** — product/SDK/API ideas, integrations, admin UI improvements
- **RFCs** — design proposals for memory model, API shape, import/export, agent integrations, storage backends, security, architecture
- **Integrations** — LangChain, LlamaIndex, CrewAI, AutoGen, OpenAI Agents SDK, MCP, vector stores, Postgres/pgvector, LiteLLM, local models, deployment patterns
- **Roadmap** — prioritization input on what's next
- **Research** — long-term memory, temporal memory, agent state, retrieval, evals, memory quality, context engineering
- **Support** — practical help. Security vulnerabilities go to [security@statewave.ai](mailto:security@statewave.ai), not here

If a category isn't visible yet, the operator may not have created it — see [discussions-setup.md](./discussions-setup.md).

## How to write a good question

A good question gets answered fast because it gives someone enough to act on. Include:

- **What you're trying to do** — the actual goal, not just the symptom
- **What you tried** — code or commands, not paraphrased
- **What happened vs. what you expected**
- **Environment** — Statewave version, install method, Python/Node version, database, model/provider, deployment style (local / self-hosted / cloud)
- **Relevant logs** — trimmed to the failure, with secrets redacted

The [Q&A template](./discussion-templates.md#qa) walks through this.

## How to write a good RFC

RFCs are for design proposals significant enough to deserve community review before implementation. Use the [RFC template](./discussion-templates.md#rfc). A strong RFC:

- States the **problem** before the **solution**
- Describes the **proposed design** in enough detail that someone else could critique it
- Lists **alternatives considered** and why they were rejected
- Names **risks and tradeoffs** honestly
- Ends with **open questions** the author wants feedback on

If you're not sure whether something needs an RFC, post in **General** first and ask.

## How to share a use case

We learn the most from real, specific use cases. Post in **Show and Tell** with:

- What you built
- What Statewave remembers (subjects, episode kinds, retrieval shape)
- Stack — agent framework, LLM provider, deployment
- Demo or screenshots
- What worked, what didn't, what was missing

This is also the best signal we have for prioritizing the roadmap.

## Tone and behavior

- Be kind. Assume good faith. Critique ideas, not people.
- Search before posting — your question may already be answered.
- Stay on topic. Keep promotional content to **Show and Tell** and only when it's genuinely Statewave-related.
- Disagreement is welcome; personal attacks, harassment, and discrimination are not.

### Good discussions include

- A concrete use case
- Stack and environment
- What was tried
- Expected vs. actual behavior
- Why it matters

### Avoid

- Vague "does this work?" posts without context
- Security reports in public — email [security@statewave.ai](mailto:security@statewave.ai) instead
- Spam and unrelated self-promotion
- Personal attacks
- Generic AI hype with no Statewave-specific substance

Maintainers may move, edit, lock, or delete posts that don't fit these guidelines.

## Open source and commercial sustainability

Statewave is positioned as a long-lived piece of infrastructure. To keep it that way, the project balances two tracks:

- **Model-agnostic, durable memory and state outside the model** — inspectable, portable, self-hostable, vendor-neutral, built for real agents and production systems.
- **AGPLv3 for open-source / community use**, with a separate **Statewave Commercial License** for proprietary, SaaS, embedded, hosted, or enterprise use. See [LICENSING.md](https://github.com/smaramwbc/statewave/blob/main/LICENSING.md).

What this means in practice for community participation:

- Architecture, API design, integrations, and roadmap are discussed openly. Public RFCs and Discussions are the right venue.
- Bug reports, fixes, features, docs improvements — all welcome under the dual-license contribution model described in [CONTRIBUTING.md](https://github.com/smaramwbc/statewave/blob/main/CONTRIBUTING.md).
- **Commercial terms, custom contracts, indemnity, SLAs** are handled privately at [licensing@statewave.ai](mailto:licensing@statewave.ai), not in public Discussions.
- General licensing *questions* (which license fits my use case? what does AGPL §13 mean here?) are fine to discuss publicly. Specific commercial *terms* are not.

This guide is community guidance, not legal advice. For licensing questions specific to your situation, consult qualified counsel.
