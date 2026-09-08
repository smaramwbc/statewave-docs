"""Shared proof-figure config for check-proof-figures.py.

## Why this exists

The "proof" numbers — server / SDK test counts, the support-agent eval
assertion + test counts, and the support-workflow benchmark score — are
hand-mirrored across docs, the core README, and the marketing site. They
drift: the web hero said `723` unit tests and `dev/conventions.md` said
`~939` while the actual collector reported `876`; the eval breakdown in a
CHANGELOG entry summed to `54/21` while every headline said `56/23`.

This module is the **single source of truth** for those figures (the user
chose "pin to one SSoT file", mirroring the versioning model in
`_targets.py`). `check-proof-figures.py` asserts every live mirror matches
`FIGURES`. When the test suite or benchmark genuinely changes, recompute the
figure here once — each entry carries the exact `source` command — and the
checker tells you every surface that still disagrees.

This is deliberately **separate from version consistency** (`_targets.py` /
`check-versions.py`): versions track `statewave/pyproject.toml`; proof
figures track the test/eval/benchmark reality and move on their own cadence.

## What is intentionally NOT failed by the checker

- **Launch copy** (launch posts, maintained outside this repo) — written
  ahead of the v1.0 release (shipped 2026-06-09); it says `v1.0.0` / `8/8`
  on purpose. A naive "fix" that rewrites it to the current package version
  would destroy the launch messaging. Do not add launch posts as `mechanical`.
- **Release notes / CHANGELOG** (`statewave-docs/release-notes/*.md`,
  `**/CHANGELOG.md`) — point-in-time snapshots. The figure that was true at
  v0.6.1 should stay as written; that is history, not drift.

## kind

    "mechanical"
        Group 1 of `pattern` is the live figure on that surface. It MUST
        equal FIGURES[figure_key]["value"] (string compare). Drift fails CI.

    "editorial"
        Group 1 is a figure embedded in prose that a human owns per release
        (blog posts, narrative docs). Reported with its current value for
        confirmation; never fails CI.

To track a new surface, add a row to `PROOF_TARGETS`. To change a figure
(the suite really grew), edit `FIGURES` — re-run the `source` command first
so the new number is real, not guessed.
"""

from __future__ import annotations

# --- Canonical figures (the truth). Values are strings for uniform compare.
# `source` is the exact command that recomputes the number; run it before you
# change a value. Env note: server/SDK collection uses the CI-matching stub
# providers (STATEWAVE_EMBEDDING_PROVIDER=stub STATEWAVE_COMPILER_TYPE=heuristic)
# to avoid the repo .env leaking real providers into pytest.
FIGURES: dict[str, dict[str, str]] = {
    "server_tests_total": {
        "value": "944",
        "source": "cd statewave && pytest tests --collect-only -q | tail -1",
        "note": "All server tests: 708 unit + 233 integration + 3 smoke (recomputed 2026-06-10).",
    },
    "server_tests_unit": {
        "value": "708",
        "source": (
            "cd statewave && pytest --collect-only -q "
            "--ignore=tests/integration --ignore=tests/smoke tests | tail -1"
        ),
        "note": "Server unit tests only (excludes integration + smoke).",
    },
    "py_sdk_tests": {
        "value": "80",
        "source": "cd statewave-py && pytest --collect-only -q | tail -1",
        "note": "statewave-py test functions.",
    },
    "ts_sdk_tests": {
        "value": "50",
        "source": "cd statewave-ts && npx vitest list | grep -c ' > '",
        "note": "statewave-ts test cases.",
    },
    "eval_tests": {
        "value": "23",
        "source": "cd statewave-examples && pytest eval-support-agent --collect-only -q | tail -1",
        "note": "Total support-agent eval tests (7 context + 6 handoff + 10 advanced).",
    },
    "eval_assertions": {
        "value": "56",
        "source": "grep -rcE 'assert ' statewave-examples/eval-support-agent/test_*.py | "
        "awk -F: '{s+=$2} END{print s}'",
        "note": "Total binary assertions (15 context + 15 handoff + 26 advanced).",
    },
    "eval_context_tests": {
        "value": "7",
        "source": "grep -cE '^\\s*def test_' statewave-examples/eval-support-agent/test_support_context.py",
        "note": "Context-quality eval test count.",
    },
    "eval_context_assertions": {
        "value": "15",
        "source": "grep -cE 'assert ' statewave-examples/eval-support-agent/test_support_context.py",
        "note": "Context-quality eval assertions.",
    },
    "eval_handoff_tests": {
        "value": "6",
        "source": "grep -cE '^\\s*def test_' statewave-examples/eval-support-agent/test_handoff.py",
        "note": "Handoff eval test count.",
    },
    "eval_handoff_assertions": {
        "value": "15",
        "source": "grep -cE 'assert ' statewave-examples/eval-support-agent/test_handoff.py",
        "note": "Handoff eval assertions.",
    },
    "eval_advanced_tests": {
        "value": "10",
        "source": "grep -cE '^\\s*def test_' statewave-examples/eval-support-agent/test_support_advanced.py",
        "note": "Advanced eval test count.",
    },
    "eval_advanced_assertions": {
        "value": "26",
        "source": "grep -cE 'assert ' statewave-examples/eval-support-agent/test_support_advanced.py",
        "note": "Advanced eval assertions.",
    },
    # The self-scored 8/8-vs-2/8 benchmark COMPARISON was retired from every
    # living surface (statewave-web #293 + the docs PR that changed this
    # file): scoring your own harness against a strawman is not a
    # trustworthy proof figure. The criteria COUNT remains a fact worth
    # mirroring — the harness is open, readers score it themselves.
    "support_criteria": {
        "value": "8",
        "source": "ls statewave-examples/benchmark-support-agent/criteria  # or the harness README criteria list",
        "note": "Number of support-workflow benchmark criteria (open harness).",
    },
}

# --- Mirror surfaces. (key, relative_path, pattern, figure_key, kind)
# Group 1 of `pattern` is the live token; it is compared string-equal to
# FIGURES[figure_key]["value"].
PROOF_TARGETS: list[tuple[str, str, str, str, str]] = [
    # --- dev/conventions.md: per-component test counts ---
    (
        "conventions_server",
        "statewave-docs/dev/conventions.md",
        r"Server: ~(\d+) tests",
        "server_tests_total",
        "mechanical",
    ),
    (
        "conventions_py",
        "statewave-docs/dev/conventions.md",
        r"Python SDK: (\d+) tests",
        "py_sdk_tests",
        "mechanical",
    ),
    (
        "conventions_ts",
        "statewave-docs/dev/conventions.md",
        r"TypeScript SDK: (\d+) tests",
        "ts_sdk_tests",
        "mechanical",
    ),
    # --- architecture/repo-map.md ---
    (
        "repomap_eval_assertions",
        "statewave-docs/architecture/repo-map.md",
        r"eval suites \((\d+) assertions\)",
        "eval_assertions",
        "mechanical",
    ),
    (
        "repomap_context_tests",
        "statewave-docs/architecture/repo-map.md",
        r"Context quality eval \((\d+) tests",
        "eval_context_tests",
        "mechanical",
    ),
    (
        "repomap_context_assertions",
        "statewave-docs/architecture/repo-map.md",
        r"Context quality eval \(\d+ tests, (\d+) assertions",
        "eval_context_assertions",
        "mechanical",
    ),
    # --- architecture/overview.md ---
    (
        "overview_eval_assertions",
        "statewave-docs/architecture/overview.md",
        r"eval suites \((\d+) assertions\)",
        "eval_assertions",
        "mechanical",
    ),
    (
        "overview_bench_criteria",
        "statewave-docs/architecture/overview.md",
        r"support-workflow benchmark \((\d+) criteria",
        "support_criteria",
        "mechanical",
    ),
    # --- roadmap.md ---
    (
        "roadmap_eval_assertions",
        "statewave-docs/roadmap.md",
        r"eval suites \((\d+) assertions\)",
        "eval_assertions",
        "mechanical",
    ),
    (
        "roadmap_bench_criteria",
        "statewave-docs/roadmap.md",
        r"support-workflow benchmark \((\d+) criteria",
        "support_criteria",
        "mechanical",
    ),
    # --- why-statewave.md: per-suite breakdown + benchmark table row ---
    (
        "why_context_tests",
        "statewave-docs/why-statewave.md",
        r"runs (\d+) tests with \d+ binary assertions",
        "eval_context_tests",
        "mechanical",
    ),
    (
        "why_context_assertions",
        "statewave-docs/why-statewave.md",
        r"runs \d+ tests with (\d+) binary assertions",
        "eval_context_assertions",
        "mechanical",
    ),
    (
        "why_handoff_tests",
        "statewave-docs/why-statewave.md",
        r"test_handoff\.py\) \((\d+) tests",
        "eval_handoff_tests",
        "mechanical",
    ),
    (
        "why_handoff_assertions",
        "statewave-docs/why-statewave.md",
        r"test_handoff\.py\) \(\d+ tests, (\d+) assertions",
        "eval_handoff_assertions",
        "mechanical",
    ),
    (
        "why_advanced_tests",
        "statewave-docs/why-statewave.md",
        r"test_support_advanced\.py\) \((\d+) tests",
        "eval_advanced_tests",
        "mechanical",
    ),
    (
        "why_advanced_assertions",
        "statewave-docs/why-statewave.md",
        r"test_support_advanced\.py\) \(\d+ tests, (\d+) assertions",
        "eval_advanced_assertions",
        "mechanical",
    ),
    (
        "why_bench_criteria",
        "statewave-docs/why-statewave.md",
        r"Support-workflow benchmark: (\d+) criteria \(active-issue",
        "support_criteria",
        "mechanical",
    ),
    # --- statewave/README.md (core) ---
    (
        "core_readme_eval_assertions",
        "statewave/README.md",
        r"eval suite \((\d+) assertions across",
        "eval_assertions",
        "mechanical",
    ),
    (
        "core_readme_eval_tests",
        "statewave/README.md",
        r"eval suite \(\d+ assertions across (\d+) tests",
        "eval_tests",
        "mechanical",
    ),
    # --- statewave-web: proof-stats.ts SSoT for the marketing site ---
    # statewave-web #271/#293 centralized the site's literals into
    # PROOF_FIGURES and retired the self-scored benchmark tiles, so the
    # mirrors grep the named constants instead of tile literals.
    (
        "proofstats_unit",
        "statewave-web/src/lib/proof-stats.ts",
        r"unitTests: '(\d+)'",
        "server_tests_unit",
        "mechanical",
    ),
    (
        "proofstats_assertions",
        "statewave-web/src/lib/proof-stats.ts",
        r"evalAssertions: '(\d+)'",
        "eval_assertions",
        "mechanical",
    ),
    (
        "proofstats_criteria",
        "statewave-web/src/lib/proof-stats.ts",
        r"supportCriteria: '(\d+)'",
        "support_criteria",
        "mechanical",
    ),
    # HomePage score prose and the blog's self-scored comparison were removed
    # with the retirement (web #271/#293); the homepage now quotes
    # PROOF_FIGURES constants directly in JSX, so proof-stats.ts is the one
    # greppable web surface and no separate HomePage/blog mirrors remain.
]
