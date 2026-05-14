#!/usr/bin/env python3
"""Verify every known version reference in the workspace matches the truth.

Truth is statewave/pyproject.toml. Mechanical surfaces (SDK pyprojects,
package.json, doc status lines, table rows) must match. Editorial surfaces
(status blurbs, feature blurbs) are reported but never fail the check —
they need a human to confirm the prose still makes sense.

Exits:
    0 — all mechanical surfaces match truth
    1 — at least one drifted, or a configured target's pattern no longer
        matches (means TARGETS in _targets.py is stale)

Wire into CI as a release-blocker on the statewave/ release-tag workflow:

    - name: Verify workspace version consistency
      run: python statewave-docs/tools/check-versions.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _targets import TARGETS, TRUTH_FILE, TRUTH_PATTERN  # noqa: E402

WORKSPACE = Path(__file__).resolve().parent.parent.parent


def read_truth() -> str:
    path = WORKSPACE / TRUTH_FILE
    m = re.search(TRUTH_PATTERN, path.read_text(), re.MULTILINE)
    if not m:
        sys.exit(f"error: could not find version in {path}")
    return m.group(1)


def main() -> None:
    truth = read_truth()
    truth_minor = ".".join(truth.split(".")[:2])
    print(f"truth: v{truth}  ({TRUTH_FILE})")
    print()

    drift = []
    editorial = []
    missing = []

    for key, rel, pattern, _, kind in TARGETS:
        path = WORKSPACE / rel
        if not path.exists():
            missing.append((key, rel, "file not found"))
            continue
        m = re.search(pattern, path.read_text(), re.MULTILINE)
        if not m:
            missing.append((key, rel, "pattern not found"))
            continue
        current = m.group(1) if kind != "mechanical_resub" else m.group(2)
        expected = truth_minor if kind == "mechanical_minor" else truth
        if kind == "editorial":
            editorial.append((key, rel, current))
        elif current != expected:
            drift.append((key, rel, current, expected))

    fail = False

    if missing:
        print(f"⚠ {len(missing)} target(s) missing — config or repo state has drifted:")
        for key, rel, why in missing:
            print(f"  {key}: {why}  [{rel}]")
        print(
            "  fix: update tools/_targets.py to reflect the new file paths or "
            "patterns, or restore the missing surface."
        )
        print()
        fail = True

    if drift:
        print(f"✗ {len(drift)} mechanical surface(s) drift from truth (v{truth}):")
        for key, rel, cur, exp in drift:
            print(f"  {key}: v{cur} ≠ v{exp}  [{rel}]")
        print()
        print(f"  fix: python tools/bump-version.py {truth} --apply")
        print()
        fail = True

    if editorial:
        print(f"ℹ {len(editorial)} editorial surface(s) — confirm wording is current:")
        for key, rel, cur in editorial:
            mark = "·" if cur == truth else "?"
            print(f"  {mark} {key}: v{cur}  [{rel}]")
        print()

    if fail:
        sys.exit(1)

    print(f"✓ all mechanical surfaces match truth (v{truth})")


if __name__ == "__main__":
    main()
