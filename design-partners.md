# Design partner onboarding

A focused guide for teams adopting Statewave early — what to set up, what to evaluate, and how we work together while the runtime is still shaping its public surface.

> Statewave is open-source, Apache-2.0, and self-hosted. The design-partner relationship is **not** a commercial contract — it's a working agreement to evaluate Statewave on a real workload, file precise feedback, and shape what lands next in exchange for direct support and a voice in the roadmap.

---

## 1. Overview

Statewave is the memory runtime for AI agents. It turns a stream of raw events (`episodes`) into ranked, token-bounded, provenance-tagged `context bundles` so that a model gets the right slice of durable memory on every call — without prompt-stuffing, without query-time vector noise, and without a second database to operate.

### What a design partner gets

- A direct support channel (Slack Connect, Discord, or email — agreed at kickoff) on top of the public issue tracker.
- Priority on bug reports against the version you're running.
- Early access to features behind the next minor release; an opt-in path to try them on your data.
- Real influence on the v0.9+ roadmap — every shipped item since `v0.6` has at least one design-partner request behind it.

### What we ask in return

- A real workload (not a toy demo) running against Statewave for at least 30 days.
- Specific, reproducible feedback — episode counts, latencies, context-bundle samples, configs. Vague *"this feels slow"* is the only kind of feedback we can't act on.
- Permission to cite the relationship (logo, quote, case-study sketch) if and only if Statewave clears your internal evaluation. We will not publish anything you haven't reviewed.

This relationship runs **30 / 60 / 90 days** with checkpoint syncs at each boundary, after which it either rolls forward indefinitely or ends cleanly with no obligations either way.

---

## 2. Who Statewave is for

### Strong fit

- An AI application with **returning subjects** — customers, accounts, projects, repos — where session-to-session continuity is a product feature, not a nice-to-have.
- Workflows where **provenance matters** — support escalation, compliance, audit, regulated industries — and "the model said something" needs to trace back to a source episode.
- Teams that **want to self-host** the memory layer alongside their existing Postgres, not push memory into a hosted vector DB they don't operate.
- A target of a **token-bounded prompt** today (Claude / GPT-class context limits), where ranked retrieval + provenance is a better answer than stuffing the whole history.
- Teams already on **LangChain, CrewAI, AutoGen,** or a custom Python/TS agent loop — Statewave is framework-neutral but composes naturally with all of them (see [`statewave-examples`](https://github.com/smaramwbc/statewave-examples)).

### Weak fit

- One-shot, stateless prompts where context is rebuilt from scratch each call — Statewave is overkill.
- Pure document RAG ("ask my PDFs"). Statewave is for *interaction history* over a subject, not for indexing static corpora. A docs memory pack exists for the support-agent case ([`default-support-docs-pack.md`](default-support-docs-pack.md)) but the runtime is built around episodes, not chunks.
- Teams that *require* a fully hosted memory SaaS. Statewave does not (yet) ship one.

---

## 3. 30-minute setup path

The full reference is [Getting Started](getting-started.md); below is the design-partner-paced version that gets you to a token-bounded context bundle, on a real subject, with provenance verifiable end-to-end.

### Minute 0–10 — bring the server up

```bash
git clone https://github.com/smaramwbc/statewave && cd statewave
docker compose up -d
curl http://localhost:8100/healthz   # → {"status":"ok"}
curl http://localhost:8100/readyz    # → {"status":"ready", ...}
```

This brings up Postgres (pgvector) + the API. Migrations run automatically on container start. The default deployment uses the **heuristic compiler** (regex-based, fully local — no LLM calls, nothing leaves the host).

### Minute 10–20 — install the SDK and ingest

```bash
pip install "statewave>=0.10.0"     # Python; or `npm i @statewavedev/sdk` for TS
```

```python
from statewave import StatewaveClient

with StatewaveClient("http://localhost:8100") as sw:
    sw.create_episode(
        subject_id="customer:globex",
        source="support-chat",
        type="conversation",
        payload={"messages": [
            {"role": "user", "content": "I'm on the Enterprise plan; renewal is in Q3."},
            {"role": "assistant", "content": "Saved — Enterprise plan, Q3 renewal."},
        ]},
    )
    sw.compile_memories("customer:globex")          # extract durable memories
    bundle = sw.get_context("customer:globex",
                            task="What plan is this customer on?",
                            max_tokens=300)
    print(bundle.assembled_context)                  # ranked, token-bounded
    print(bundle.provenance)                         # source episode ids
```

### Minute 20–30 — verify the things that matter

- **Idempotency.** Run `sw.compile_memories("customer:globex")` again — `memories_created` is `0`. Recompilation is a no-op.
- **Provenance.** Each memory in the bundle has `source_episode_ids` you can fetch via the timeline endpoint. Pick one fact in the bundle and trace it back to the episode.
- **Token bound.** Decrease `max_tokens` and confirm the bundle gets shorter, lower-value items drop out, and `bundle.token_estimate` stays under the budget.
- **Receipts (optional).** Set `emit_receipt=True` on `get_context` and fetch the resulting receipt via `sw.get_receipt(bundle.receipt_id)` — an immutable, content-hashed audit artifact of exactly which memories went into the bundle. See [`receipts.md`](receipts.md).

If any of these don't behave as described, **that's the first thing to file** — it's a 30-minute regression signal, not a configuration problem you should chase yourself.

---

## 4. Recommended first use cases

Pick **one** and run it on real data for 30 days. Half the value of the design-partner program is going deep on one use case; the other half is letting that one use case tell us what's missing.

| Use case | What it exercises | Reference |
|---|---|---|
| **Returning-customer support agent** | Ranked retrieval, token budget, session-aware ranking, handoff pack | [`statewave-examples/support-agent-python`](https://github.com/smaramwbc/statewave-examples/tree/main/support-agent-python) |
| **Long-running coding agent** | Multi-session subject memory, decision logs, provenance | [`statewave-examples/coding-agent-python`](https://github.com/smaramwbc/statewave-examples/tree/main/coding-agent-python) |
| **Compliance-tagged memory** | Sensitivity labels, per-tenant policy, receipts in `enforce` mode | [`sensitivity-labels.md`](sensitivity-labels.md) + [`receipts.md`](receipts.md) |
| **Framework integration** | Drop-in memory inside your existing LangChain / CrewAI / AutoGen agent | [`statewave-examples/langchain-quickstart`](https://github.com/smaramwbc/statewave-examples/tree/main/langchain-quickstart) (+ `crewai-quickstart`, `autogen-quickstart`) |
| **Memory templates** | Structured, provenance-tagged ingestion of a recurring pattern | [`docs/memory-templates.md`](https://github.com/smaramwbc/statewave/blob/main/docs/memory-templates.md) in the server repo |

Each of these has runnable code and at least one passing smoke test in `main`. None of them is "speculative" — they all reflect what Statewave does today on `main`.

---

## 5. Data and privacy expectations

Statewave is **self-hosted**. Your Postgres, your data, your network boundary.

### What stays inside your perimeter

- **Episodes and memories.** Always. They live in *your* Postgres; nothing in Statewave ships them anywhere.
- **Context bundles.** Assembled in-process on your server and returned to your caller.
- **Receipts.** Stored in *your* Postgres, ULID-addressable, tenant-scoped.

### What can leave the perimeter (operator-controlled)

This is determined entirely by your **compiler and embedding config**, not by Statewave itself:

| Component | Default | If you change it to … |
|---|---|---|
| **Compiler** | `heuristic` (regex, fully local — nothing leaves) | `llm` — episode payloads go to whichever provider `STATEWAVE_LITELLM_MODEL` selects, on compile only |
| **Embeddings** | `stub` (deterministic local) | `litellm` — query text + memory content go to the embedding provider for every assembly call |
| **Webhooks** | disabled | One global URL of *your* choosing receives event callbacks; optional event-type allowlist (`STATEWAVE_WEBHOOK_EVENTS`) restricts which |
| **OpenTelemetry tracing** | disabled | Spans flow to your OTLP collector |

The full breakdown lives in [Privacy & Data Flow](architecture/privacy-and-data-flow.md). The summary that matters for a design partner: **the default deployment is fully local — no external calls.** You opt into each external surface explicitly via env vars; we never do it for you.

### Telemetry, phone-home, "anonymous usage"

There is none. There will not be. Statewave does not ship any reporting of any kind to any host owned by us. If you find one, that's a security report (see below) — not a config option.

### Security

Vulnerabilities go to [security@statewave.ai](mailto:security@statewave.ai), not to public issues. See [SECURITY.md](SECURITY.md).

---

## 6. Support and feedback loop

| Channel | What it's for | Latency |
|---|---|---|
| **Direct private channel** (Slack Connect / shared Discord / shared email thread — agreed at kickoff) | Anything you'd rather not file publicly; production blocker; questions where you want a faster answer than a GitHub round-trip | Same business day |
| [**statewave/issues**](https://github.com/smaramwbc/statewave/issues) — the central tracker | Bugs, feature requests, anything reproducible from a public artifact. Issues across every repo route here (the per-repo Issues tabs are disabled by design). | 1–2 business days for triage |
| [**statewave/discussions**](https://github.com/smaramwbc/statewave/discussions) | Open-ended design questions, "how would you approach …", RFCs | Best effort |
| [security@statewave.ai](mailto:security@statewave.ai) | Anything security-sensitive — full stop | 24 hours |

**Cadence.** A fortnightly 30-minute sync is the default. Either side can change it (more frequent during a hot week, paused when you're heads-down). Each sync has a written summary; nothing is committed in a meeting that isn't followed up as a tracked issue.

### What makes for a useful bug report

1. Server version (`curl http://localhost:8100/v1/version` or check the running image tag).
2. SDK version (`statewave.__version__` / `import { version } from "@statewavedev/sdk"`).
3. The exact request that surfaces the bug — full `subject_id`, `task`, body. Scrub real customer data.
4. What you expected vs. what you got.
5. The receipt id (if receipts are emitted), or the assembled context.

If your bug report has those five things, we can usually have a fix-or-workaround within 24 hours.

---

## 7. Evaluation checklist

Run through this in the first two weeks. Anything that doesn't hold is a fix priority, not a configuration problem.

### Functional

- [ ] Episodes ingest at your real volume (target: ≥10 episodes/sec on the default Docker Compose stack).
- [ ] `compile_memories` produces non-empty memory output for a representative subject with > 3 episodes.
- [ ] Recompilation of the same subject is idempotent — `memories_created == 0`.
- [ ] `get_context` returns memories ranked relative to the supplied `task`; rerunning the same call returns the same bytes (deterministic per subject + task + as-of).
- [ ] `bundle.token_estimate ≤ max_tokens` for every call you make.
- [ ] Every memory in a bundle has `source_episode_ids` pointing at real, fetchable episodes.

### Performance

- [ ] `get_context` p50 latency below your application's budget on your hardware (a useful baseline: < 250 ms p50 on the default deployment with the stub embedding provider).
- [ ] `compile_memories` finishes in time appropriate for your ingest cadence (synchronous compile is fine up to ~hundreds of episodes; switch to async beyond).

### Governance (if you need it)

- [ ] Tenant isolation: a request without `X-Tenant-ID` does not return another tenant's memories (under `STATEWAVE_REQUIRE_TENANT=true`).
- [ ] Receipts: a single `get_context` call with `emit_receipt=true` produces a fetchable receipt whose `output.context_hash` matches a SHA-256 of `bundle.assembled_context`.
- [ ] Sensitivity labels: a memory tagged with a label your active policy denies is dropped from a bundle in `enforce` mode (and recorded in the receipt as `filters_applied` in `log_only` mode).

### Operational

- [ ] `docker compose down && docker compose up -d` does not lose data.
- [ ] `pg_dump` of the Statewave database produces a portable snapshot that restores cleanly to a fresh deployment (memory portability — see [`memory-portability.md`](https://github.com/smaramwbc/statewave/blob/main/docs/memory-portability.md)).
- [ ] You know how to back up and restore: [`subject` export](https://github.com/smaramwbc/statewave/blob/main/docs/memory-portability.md), Postgres snapshot, or both.

---

## 8. Sample success criteria

What "working" looks like at each checkpoint.

### Day 30

- One real workload is in production or production-like, hitting Statewave ≥ daily.
- ≥ 80% of evaluation-checklist items above are checked off.
- At least one **concrete win** documented — a recall improvement, a token-budget reduction, a handoff that the agent would have lost without durable memory.
- At least one **filed issue** (bug or feature request) that came out of your real use.

### Day 60

- The workload has been running for ≥ 4 weeks. You have latency / volume numbers you trust.
- Either: provenance / receipts / sensitivity labels are in your evaluation path (compliance angle), or you've explicitly ruled them out as out-of-scope.
- One framework integration (or your own equivalent) has been exercised end-to-end if applicable.

### Day 90

- You have a clear answer to "**should we keep this in production indefinitely?**"
- If **yes:** the relationship rolls into a regular customer cadence; we ask for permission to credit you. If **no:** an exit interview captures the why — the most important artifact in either direction.

Concrete reference numbers from the public benchmark, for shape — your workload will not look exactly like LoCoMo, but it gives a sense of what's achievable:

| At a 1 024-token budget on LoCoMo | Score (excl. adversarial) |
|---|---:|
| Statewave | 0.384 |
| Mem0 | 0.269 |
| Zep | 0.041 |
| Naïve last-N | 0.035 |
| No memory | 0.004 |

Full methodology + per-tier results: [`statewave-bench/RESULTS.md`](https://github.com/smaramwbc/statewave-bench/blob/main/RESULTS.md).

---

## 9. FAQ

**Can I bring my own LLM?**
Yes. Statewave uses [LiteLLM](https://github.com/BerriAI/litellm) under the hood, so any of its ~100+ providers works (OpenAI, Anthropic, Bedrock, self-hosted Ollama, …). Configure via `STATEWAVE_LITELLM_*` env vars. The compiler and embedding paths are independently configurable — you can run a local heuristic compiler and a hosted embedding provider, or vice versa.

**Does Statewave replace my vector DB?**
For the *memory* use case, yes. Statewave's retrieval is native to Postgres + pgvector, so you don't operate a second database. If you have a separate document-search vector DB for static corpora, keep it — Statewave is for interaction history over a subject, not for indexing static documents.

**Multi-tenant?**
Yes — set `STATEWAVE_REQUIRE_TENANT=true`. Every read and write is then scoped by the `X-Tenant-ID` header at the application query layer. Tenant A cannot read, search, or delete tenant B's data. Detailed guarantees + the pre-tenant data upgrade path are in [`api/v1-contract.md`](api/v1-contract.md#multi-tenant-isolation).

**Audit / compliance?**
The governance surface that landed in v0.8 is: **state-assembly receipts** (immutable, content-hashed, ULID-addressable record of every assembly call — [`receipts.md`](receipts.md)) and **sensitivity labels + per-tenant policy** (per-memory capability tags consulted on every assembly — [`sensitivity-labels.md`](sensitivity-labels.md)). Receipts in `enforce` mode produce a tamper-evident audit trail you can hand to a compliance team.

**Does it work with LangChain / CrewAI / AutoGen?**
Yes — quickstart examples for each are in [`statewave-examples`](https://github.com/smaramwbc/statewave-examples) (`langchain-quickstart/`, `crewai-quickstart/`, `autogen-quickstart/`). Adapter code lives inside each example; the core SDKs have **no framework deps**, so they don't chase framework version churn.

**What does it cost?**
Statewave is Apache-2.0 — the runtime, SDKs, examples, and benchmarks are free to use, modify, and self-host. Your costs are infrastructure (Postgres + a CPU-only API process; no GPU) and any LLM / embedding provider you choose. Commercial / enterprise inquiries route to [licensing@statewave.ai](mailto:licensing@statewave.ai), not to the design-partner program.

**How stable is the API?**
Statewave is pre-1.0. Minor versions (v0.6 → v0.7) may carry breaking changes; we call them out explicitly in [`statewave-docs/CHANGELOG.md`](https://github.com/smaramwbc/statewave-docs/blob/main/CHANGELOG.md) and each SDK's CHANGELOG. The HTTP wire contract is more conservative than the SDK surfaces — server upgrades are usually drop-in for existing SDK callers. The TypeScript SDK switched to a camelCase surface in v0.9.0; that was the most disruptive change so far. As a design partner, you'll see proposed breaking changes for comment before they land.

**Can I run Statewave on Kubernetes?**
Yes — there's an in-tree Helm chart at [`helm/statewave/`](https://github.com/smaramwbc/statewave/tree/main/helm/statewave), plus a deployment guide at [`deployment/kubernetes.md`](deployment/kubernetes.md). Operators bring a pgvector-capable Postgres; the chart deploys the API as a stateless Deployment with schema migrations as a pre-install / pre-upgrade Job.

**What about the connector ecosystem?**
Twelve connectors ship today — GitHub, Markdown/ADRs, MCP, Slack, Discord, Zendesk, Intercom, Freshdesk, Notion, Gmail, n8n, Zapier — covering pull, push (Tier 2 webhook receivers), and a hosted runner (`statewave-connectors run`). Full list + roadmap: [Connectors → Roadmap](connectors/roadmap.md).

---

## Next steps

1. Run through the **30-minute setup path** (§3) on your own machine.
2. Pick **one use case** from §4 to commit to for 30 days.
3. Tell us you're starting — open a discussion on [`statewave/discussions`](https://github.com/smaramwbc/statewave/discussions) tagged `design-partner`, or reach out via your direct channel. We'll schedule the kickoff sync and exchange the private contact info.
4. Work through the **evaluation checklist** (§7) in weeks 1–2; file what you find.

— *the Statewave team*
