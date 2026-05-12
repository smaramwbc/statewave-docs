#!/usr/bin/env python3
"""Propagate a new Statewave workspace version everywhere it lives.

Reads the truth from statewave/pyproject.toml and updates every mechanical
version reference across sibling repos. Editorial surfaces (status blurbs,
feature blurbs, CHANGELOGs) are flagged for manual review but not touched.

Usage:
    python tools/bump-version.py 0.7.3              # dry-run (default)
    python tools/bump-version.py 0.7.3 --apply      # write changes

Before running with --apply: bump statewave/pyproject.toml to the new
version yourself (it's the truth source the workspace tracks).

Paths are resolved from __file__, so this works from any cwd.
"""

from __future__ import annotations

import argparse
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


def bump(new_version: str, apply: bool) -> int:
    truth = read_truth()
    print(f"truth source: {TRUTH_FILE} (currently v{truth} → target v{new_version})")
    if truth != new_version:
        print(
            f"  note: truth is v{truth}; bump {TRUTH_FILE} to v{new_version} "
            "before publishing the workspace."
        )
    print()

    editorial = []
    changed = 0
    issues = 0

    for key, rel, pattern, replacement, kind in TARGETS:
        path = WORKSPACE / rel
        if not path.exists():
            print(f"  ⚠ {key}: file not found at {rel}")
            issues += 1
            continue

        content = path.read_text()
        m = re.search(pattern, content, re.MULTILINE)
        if not m:
            print(f"  ⚠ {key}: pattern did not match in {rel}")
            issues += 1
            continue

        if kind == "editorial":
            editorial.append((key, rel, m.group(1)))
            continue

        if kind == "mechanical":
            current = m.group(1)
            new_content = re.sub(
                pattern,
                replacement.format(ver=new_version),
                content,
                count=1,
                flags=re.MULTILINE,
            )
        elif kind == "mechanical_resub":
            # capture group 2 holds the version for this kind
            current = m.group(2)
            new_content = re.sub(
                pattern,
                replacement.replace("{ver}", new_version),
                content,
                count=1,
            )
        else:
            print(f"  ⚠ {key}: unknown kind {kind!r}")
            issues += 1
            continue

        if current == new_version and new_content == content:
            print(f"  · {key}: already v{new_version}")
            continue

        if apply:
            path.write_text(new_content)
            print(f"  ✓ {key}: v{current} → v{new_version}  [{rel}]")
        else:
            print(f"  would write {key}: v{current} → v{new_version}  [{rel}]")
        changed += 1

    print()
    if editorial:
        print("editorial surfaces — rewrite the surrounding prose manually:")
        for key, rel, cur in editorial:
            print(f"  • {key} (currently v{cur})  [{rel}]")
        print()
        print(
            "also remember the CHANGELOGs: statewave-py/CHANGELOG.md and "
            "statewave-ts/CHANGELOG.md need a human-authored entry."
        )
        print()

    if not apply and changed:
        print(f"dry run — {changed} change(s) would be applied. Re-run with --apply.")
    elif apply and changed:
        print(f"applied {changed} change(s). Don't forget the editorial surfaces above.")
    elif not changed:
        print("nothing to do — every mechanical surface is already at the target version.")

    return 1 if issues else 0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("version", help="new version, e.g. 0.7.3")
    p.add_argument(
        "--apply",
        action="store_true",
        help="write changes (default: dry-run)",
    )
    args = p.parse_args()
    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        sys.exit("error: version must be in form X.Y.Z")
    sys.exit(bump(args.version, args.apply))


if __name__ == "__main__":
    main()
