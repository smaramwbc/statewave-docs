#!/usr/bin/env python3
"""Verify the server / reference-impl version references stay self-consistent.

Packages version independently per repo; the cross-repo compatibility axis is
the `/v1` API contract, not a shared number (see smaramwbc/statewave#106 and
the model description in _targets.py). This check therefore validates only:

  - mechanical surfaces — the server repo's own self-references and the
    conceptual-doc banners that describe "the system at server vX.Y". These
    track TRUTH (statewave/pyproject.toml = server version) and MUST match.
  - editorial surfaces — version-stamped prose; reported, never failed.
  - independent surfaces — SDK rows / per-SDK status lines that version on
    their own cadence. Reported for human confirmation, never failed. NOT
    expected to equal TRUTH — that independence is intentional.

Exits:
    0 — all mechanical surfaces match truth
    1 — at least one mechanical surface drifted, or a configured target's
        pattern no longer matches (means TARGETS in _targets.py is stale)

Wire into CI as a release-blocker on the statewave/ release-tag workflow:

    - name: Verify server/contract version self-consistency
      run: python statewave-docs/tools/check-versions.py

When this script fails on a tag push, the canonical recovery is documented
in tools/RELEASE-CHECKLIST.md (see "What went wrong on v0.9.2" — published
tags are immutable; cut an additive patch with the missing mirrors instead
of force-moving the tag).
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
    independent = []
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
        current = m.group(2) if kind == "mechanical_resub" else m.group(1)
        if kind == "editorial":
            editorial.append((key, rel, current))
        elif kind == "independent":
            independent.append((key, rel, current))
        else:
            expected = truth_minor if kind == "mechanical_minor" else truth
            if current != expected:
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

    if independent:
        print(
            f"ℹ {len(independent)} independently-versioned surface(s) — "
            "each tracks its own package, not truth (this is expected):"
        )
        for key, rel, cur in independent:
            print(f"  · {key}: v{cur}  [{rel}]")
        print(
            "  these never fail the check; hand-update them when that "
            "package releases."
        )
        print()

    if fail:
        sys.exit(1)

    print(f"✓ all mechanical surfaces match truth (server v{truth})")


if __name__ == "__main__":
    main()
