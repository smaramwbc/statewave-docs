# Discussions: Operator Setup Checklist

Operator-facing setup guide for the GitHub Discussions experience on the [statewave](https://github.com/smaramwbc/statewave) repository. This is a one-time setup followed by light recurring maintenance.

The community-facing guide is in [discussions.md](./discussions.md).

## One-time setup

### 1. Enable Discussions

Settings → General → Features → tick **Discussions**.

GitHub will create a default set of categories. The next step is to align them with the recommended layout below.

### 2. Create / align categories

Settings → Discussions → Categories. The recommended layout:

| Category | Format | Purpose |
|---|---|---|
| Announcements | Announcement | Releases, roadmap milestones, licensing updates (maintainers only) |
| General | Open-ended | Open questions, broad conversation |
| Q&A | Question / Answer | Setup help, usage questions, troubleshooting, deployment help |
| Show and Tell | Open-ended | Agents, integrations, memory workflows, evals, benchmarks built with Statewave |
| Ideas & Feature Requests | Open-ended (or Poll for prioritization) | Product / SDK / API ideas, integrations, admin UI improvements |
| RFCs | Open-ended | Design proposals for memory model, API shape, import/export, integrations, storage backends, security, architecture |
| Integrations | Open-ended | LangChain, LlamaIndex, CrewAI, AutoGen, OpenAI Agents SDK, MCP, vector stores, Postgres/pgvector, LiteLLM, local models, deployment patterns |
| Roadmap | Open-ended | Prioritization input — what should ship next |
| Research | Open-ended | Long-term memory, temporal memory, agent state, retrieval, evals, memory quality, context engineering |
| Support | Question / Answer | Practical help. Note: redirect security reports to [security@statewave.ai](mailto:security@statewave.ai) |

GitHub doesn't yet expose category creation via the public API, so create these manually in the UI.

The default categories that ship on enable typically include Announcements, General, Ideas, Polls, Q&A, Show and tell. Consider:

- **Keep:** Announcements, General, Q&A, Show and tell, Polls (Polls can be repurposed inside Roadmap / Ideas threads).
- **Rename:** Ideas → "Ideas & Feature Requests" (clearer intent).
- **Add:** RFCs, Integrations, Roadmap, Research, Support.

### 3. Pin the starter discussions

Draft posts ready to copy live in [pinned-discussions/](./pinned-discussions/):

| File | Suggested category | Pin? |
|---|---|---|
| [welcome.md](./pinned-discussions/welcome.md) | Announcements | ✅ pin |
| [what-are-you-building.md](./pinned-discussions/what-are-you-building.md) | Show and Tell | ✅ pin |
| [roadmap-priorities.md](./pinned-discussions/roadmap-priorities.md) | Roadmap | ✅ pin |
| [show-us-your-memory-problem.md](./pinned-discussions/show-us-your-memory-problem.md) | Research (or General) | ✅ pin |
| [rfc-memory-import-export.md](./pinned-discussions/rfc-memory-import-export.md) | RFCs | optional pin |
| [rfc-agent-integrations.md](./pinned-discussions/rfc-agent-integrations.md) | RFCs | optional pin |

Posting workflow:
1. Open the file, copy the title and body.
2. New discussion → pick the category → paste.
3. After posting, pin from the discussion page (top-right menu).
4. GitHub allows up to **4 pinned discussions** at the repository level. Pick the 4 that best serve your current goals; rotate as priorities shift.

### 4. Link Discussions from the README

The core repo README should have a "Community" section pointing to:
- GitHub Discussions
- This community guide ([discussions.md](./discussions.md))
- Issues vs Discussions vs SECURITY guidance

This is in place after [statewave/README.md](https://github.com/smaramwbc/statewave/blob/main/README.md) is updated alongside this checklist.

### 5. (Optional) Add `.github/DISCUSSION_TEMPLATE/` form templates

GitHub supports per-category form templates at `.github/DISCUSSION_TEMPLATE/<slug>.yml`, similar to issue forms. The markdown bodies in [discussion-templates.md](./discussion-templates.md) can be ported into YAML form templates if you want stricter structure. Treat this as an optional follow-up — the markdown templates are useful even without it.

## Recurring maintenance

Light-touch monthly review keeps Discussions feeling alive without becoming a second job.

- **Roadmap & RFC threads** — read accumulated comments, post a synthesis update, mark resolved questions.
- **Triage**:
  - Confirmed reproducible bugs → convert to an Issue (use GitHub's *Convert to issue* action) and link back.
  - Wishlist items → leave in Ideas & Feature Requests, or convert if scoped enough.
  - Off-topic / spam → moderate or delete.
- **Stale threads** — discussions with no activity for >90 days and no clear question can be closed with a short note inviting the original poster to reopen.
- **Security check** — scan for any vulnerability-shaped posts. If anything looks like a real vulnerability, lock the thread, delete the sensitive details, and email the poster to redirect them to [security@statewave.ai](mailto:security@statewave.ai).

## Things to keep out of public Discussions

- Security vulnerabilities (route to [SECURITY.md](https://github.com/smaramwbc/statewave/blob/main/SECURITY.md))
- Customer / account specifics that belong in private support
- Specific commercial terms, contract negotiations, pricing for a particular customer (route to [licensing@statewave.ai](mailto:licensing@statewave.ai))
- Legal advice — point to qualified counsel and the published [LICENSING.md](https://github.com/smaramwbc/statewave/blob/main/LICENSING.md)
