# Ranking & Retrieval

This page explains how Statewave decides which memories make it into a context bundle, and what's configurable today vs. what isn't.

---

## How ranking works

Every candidate memory is scored deterministically by summing a small number of signals. Items are then sorted by composite score and packed into the requested token budget, section by section (facts → procedures → history → episodes).

### Core signals (always applied)

| Signal | Range | What it captures |
|--------|-------|------------------|
| **Kind priority** | 3–10 | `profile_fact`=10, `procedure`=8, `episode_summary`=5, `raw_episode`=3 |
| **Recency** | 0–5 | Linear scale across the candidate set; most recent gets the max |
| **Task relevance** | 0–5 (text) or 0–8 (semantic) | Word-overlap fraction with the task, or cosine similarity if embeddings exist |
| **Temporal validity** | -4 to +3 | Currently valid (`valid_to` null or future) = +3, expired = -4 |

### Support-agent signals (applied when relevant context exists)

These adjust scores when the candidate is an episode or session-linked memory. They reflect the v0.6 support-agent intelligence layer:

| Signal | Effect | When |
|--------|--------|------|
| Active-session boost | +6.0 | Episode belongs to the current open session |
| Resolved-session penalty | -5.0 | Episode belongs to a session marked resolved |
| Open-issue boost | +4.0 | Session has an open or unresolved issue tied to the task |
| Action-step boost | +2.0 | Episode is an agent / assistant / tool turn (not idle chatter) |
| Urgency boost | +2.0 | Content matches urgency keywords (escalation, breach, urgent, …) |
| Idle-chatter penalty | -2.0 | Very short content with no signal |
| Repeat-issue boost | +4.0 | Pattern matches a prior issue; +6.0 if that prior issue was resolved |

The support signals are additive — they nudge ranking, they don't replace the core formula.

---

## Properties

- **Deterministic.** Same subject + task + budget + corpus → same ordering. No non-determinism from vector-only retrieval.
- **Inspectable.** The context bundle returned by `/v1/context` includes which items were selected and their provenance.
- **Token-bounded.** The assembler packs by score until the budget is exhausted, reserving 10 tokens of header per section. It does not arbitrarily truncate items mid-content.
- **Graceful fallback.** If embeddings are unavailable, semantic similarity drops out and word-overlap relevance is used.

---

## Is scoring customizable?

**Not today.** The weights and thresholds above are constants in `server/services/context.py`. There is no per-tenant or per-call override.

**Why these defaults:**
- Kind priority reflects how often each kind is *the answer* in support / coding / sales workloads we tested.
- Support boosts and penalties came from concrete failure cases — closed sessions polluting recommendations, idle chatter outranking action steps, missed repeat issues.
- The numeric scales are chosen so that one strong signal can't single-handedly dominate (no signal exceeds the kind-priority ceiling).

**Should it be customizable?** Possibly. If you have a workload where these defaults are wrong, please open an issue with examples. We don't ship configurability speculatively — we'd rather see a real misranking before adding tuning surface.

If you need bespoke ranking today, you can:
- Filter the candidate set with `kind` or `subject_id` before requesting context (the assembler ranks what you give it).
- Subclass `ContextAssembler` and override `_score_*` helpers in your own deployment.

---

## See also

- [Architecture Overview](overview.md) — high-level scoring table
- [Compiler Modes](compiler-modes.md)
- [API v1 — context endpoint](../api/v1-contract.md)
