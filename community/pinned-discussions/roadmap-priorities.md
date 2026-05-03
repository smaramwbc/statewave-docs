# Statewave Roadmap: what should we prioritize?

> Suggested category: **Roadmap**. Pin after posting.

---

## Title

Statewave Roadmap: what should we prioritize?

## Body

The current roadmap is published in [statewave-docs/roadmap.md](https://github.com/smaramwbc/statewave-docs/blob/main/roadmap.md). v0.7 is in flight (operator + cloud experience), and v0.8 (adoption & ecosystem) is next.

This thread is for **prioritization input** — which of the candidate areas below would unblock the most value for *your* use case, and what's missing from the list.

### How to participate

- 👍 react on the buckets that matter most to you
- Comment with your **specific use case** and which bucket would help (vague +1s are less useful than "this would unblock X for us")
- Propose missing buckets — if your priority isn't on the list, add it
- If you'd champion one (RFC, prototype, design partner), say so

### Candidate priorities

Pick whatever resonates — you don't need to weigh in on all of them.

#### SDK ergonomics
- Convenience methods for support endpoints (health, SLA, handoff, resolutions)
- Streaming context responses
- Better typed error surfaces
- Per-language idiomatic helpers

#### Hosted / cloud Statewave
- Managed multi-tenant Statewave so teams don't have to operate Postgres + pgvector themselves
- Pricing and tier shape input welcome

#### Admin UI
- Beyond the current read-only dashboard — what would you want to *do* from a UI?
- Examples: subject browsing, memory inspection, retrieval debugging, manual corrections, replay

#### Memory debugging
- "Why did this memory rank where it did?" — explainable retrieval
- Eval harnesses you can point at your own corpus
- Diff tools for memory state across compilations

#### Clone / import / export
- Subject-level export already exists. What's needed beyond that?
- Cross-instance migration, cross-environment cloning, time-travel snapshots
- See the related [Memory Import/Export RFC](./rfc-memory-import-export.md)

#### Starter packs
- Ready-made memory packs for common domains (support docs, product specs, account history)
- The docs-grounded support pack already exists — what's the next pack you'd want?

#### Framework integrations
- LangChain, LlamaIndex, CrewAI, AutoGen, OpenAI Agents SDK, MCP — see the [Agent Framework Integrations RFC](./rfc-agent-integrations.md)
- Tell us your stack and what "good integration" would look like in it

#### Deployment templates
- Helm chart + Kubernetes guide
- Terraform modules
- Reference deployments for AWS / GCP / Azure / Fly / Railway

#### Evals & benchmarks
- More benchmark scenarios beyond support agents — coding agents, workspace agents, voice
- Standardized memory-quality evals you can plug into CI

#### Multi-tenant
- Currently app-layer query scoping. What would push you toward needing Postgres RLS or hard isolation?
- Per-tenant rate limiting, per-tenant billing surfaces

#### Observability
- OpenTelemetry tracing exists. What metrics, logs, dashboards would actually move on-call work?
- Prometheus exporters, Grafana templates

#### Compliance & security
- SOC 2, HIPAA, GDPR readiness — which is blocking adoption for you?
- Audit logs, retention policies, data-residency controls, key management

#### Enterprise features
- SSO / SCIM, RBAC, custom contracts, indemnity, SLA tiers
- Procurement-friendly packaging

### What we'll do with this

Periodically (roughly every release cycle) we'll synthesize this thread into a roadmap update post in **Announcements**, with the rationale for what moved up or down. Concrete use cases beat abstract feature votes — the more specific your context, the more weight it carries.

---

> Heads-up: comments on this thread are public. Specific commercial / contractual asks should go to [licensing@statewave.ai](mailto:licensing@statewave.ai) instead.
