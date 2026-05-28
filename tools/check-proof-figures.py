#!/usr/bin/env python3
"""Verify proof figures (test counts, eval assertions, benchmark score) stay
consistent across docs, the core README, and the marketing site.

These numbers are hand-mirrored and drift (the web hero said 723 unit tests
while the collector reported 876; an eval breakdown summed to 54/21 while every
headline said 56/23). This script pins them to a single source of truth
(`_proof_figures.py`, FIGURES) and fails when any *mechanical* mirror disagrees.

This is the proof-figure analogue of check-versions.py. Versions track
statewave/pyproject.toml; proof figures track the test/eval/benchmark reality.
The two are intentionally separate.

Usage:
    python statewave-docs/tools/check-proof-figures.py            # check
    python statewave-docs/tools/check-proof-figures.py --sources  # also print
                                                                  # recompute cmds

Exits:
    0 — every mechanical mirror matches the SSoT
    1 — a mechanical mirror drifted, or a target's pattern no longer matches
        (means PROOF_TARGETS in _proof_figures.py is stale vs the file)

Wire into CI as a docs-quality gate (e.g. statewave-docs PRs, or the release
workflow):

    - name: Verify proof-figure consistency
      run: python statewave-docs/tools/check-proof-figures.py

When a figure legitimately changes (the suite grew, the benchmark moved):
re-run the `source` command for that figure (see --sources), update its value
in FIGURES once, then run this script and fix every surface it flags.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _proof_figures import FIGURES, PROOF_TARGETS  # noqa: E402

WORKSPACE = Path(__file__).resolve().parent.parent.parent


def main() -> None:
    show_sources = "--sources" in sys.argv[1:]

    print("Proof figures — single source of truth (_proof_figures.py):")
    for key, meta in FIGURES.items():
        line = f"  {key} = {meta['value']}"
        if meta.get("note"):
            line += f"   — {meta['note']}"
        print(line)
        if show_sources:
            print(f"      recompute: {meta['source']}")
    print()

    drift: list[tuple[str, str, str, str]] = []
    editorial: list[tuple[str, str, str, str]] = []
    missing: list[tuple[str, str, str]] = []

    for key, rel, pattern, figure_key, kind in PROOF_TARGETS:
        if figure_key not in FIGURES:
            missing.append((key, rel, f"unknown figure key '{figure_key}'"))
            continue
        path = WORKSPACE / rel
        if not path.exists():
            missing.append((key, rel, "file not found"))
            continue
        m = re.search(pattern, path.read_text(), re.MULTILINE)
        if not m:
            missing.append((key, rel, "pattern not found"))
            continue
        current = m.group(1)
        expected = FIGURES[figure_key]["value"]
        if kind == "editorial":
            editorial.append((key, rel, current, expected))
        elif current != expected:
            drift.append((key, rel, current, expected))

    fail = False

    if missing:
        print(f"⚠ {len(missing)} target(s) missing — config or file state has drifted:")
        for key, rel, why in missing:
            print(f"  {key}: {why}  [{rel}]")
        print(
            "  fix: update PROOF_TARGETS in tools/_proof_figures.py to match the "
            "file's current wording, or restore the missing surface."
        )
        print()
        fail = True

    if drift:
        print(f"✗ {len(drift)} mechanical surface(s) drift from the SSoT:")
        for key, rel, cur, exp in drift:
            print(f"  {key}: {cur} ≠ {exp}  [{rel}]")
        print()
        print(
            "  fix: if the SSoT value is right, update the surface to match it. "
            "If the suite/benchmark actually changed, re-run the figure's "
            "`source` command (--sources), update FIGURES once, then re-run."
        )
        print()
        fail = True

    if editorial:
        print(f"ℹ {len(editorial)} editorial surface(s) — confirm the prose is current:")
        for key, rel, cur, exp in editorial:
            mark = "·" if cur == exp else "?"
            print(f"  {mark} {key}: {cur} (ssot {exp})  [{rel}]")
        print()

    if fail:
        sys.exit(1)

    print("✓ all mechanical proof-figure mirrors match the single source of truth")


if __name__ == "__main__":
    main()
