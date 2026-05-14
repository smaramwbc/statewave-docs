#!/usr/bin/env python3
"""Orchestrate a Statewave workspace release.

One command, three responsibilities — none of them remote without `--apply`:

  1. Bump the truth source (statewave/pyproject.toml) to the target version.
  2. Run bump-version.py to propagate the version into every mechanical
     surface across the workspace (SDK pyprojects, package.json, docs
     status lines, repo-map table rows, statewave-web homepage chip, …).
  3. Run check-versions.py to confirm everything aligned.

Then it *prints* — but does not run — the exact `git tag -a … && git push
origin v…` commands you should issue in each publishable repo (server,
Python SDK, TypeScript SDK). Tagging triggers GitHub Releases, PyPI / npm
publishes, and a versioned Docker image build, so it stays a deliberate
human step.

Usage:
    python tools/release.py 0.8.1              # dry-run (default)
    python tools/release.py 0.8.1 --apply      # write the bumps

Run from anywhere — paths are resolved from __file__.

Why no --tag flag: branch protection, working-tree cleanliness, and
upstream sync are easier to verify manually per-repo than to gate
correctly in a script. The printed commands are copy-paste ready.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _targets import TRUTH_FILE, TRUTH_PATTERN  # noqa: E402

import importlib.util  # noqa: E402

TOOLS = Path(__file__).resolve().parent
WORKSPACE = TOOLS.parent.parent
TRUTH_PATH = WORKSPACE / TRUTH_FILE

PUBLISHABLE_REPOS = [
    ("statewave", "server release + Docker image"),
    ("statewave-py", "PyPI publish"),
    ("statewave-ts", "npm publish"),
]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _read_truth() -> str:
    m = re.search(TRUTH_PATTERN, TRUTH_PATH.read_text(), re.MULTILINE)
    if not m:
        sys.exit(f"error: could not find version in {TRUTH_PATH}")
    return m.group(1)


def _write_truth(new_version: str) -> bool:
    """Rewrite TRUTH_PATH. Returns True if the file changed."""
    content = TRUTH_PATH.read_text()
    new_content = re.sub(
        TRUTH_PATTERN,
        f'version = "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if new_content == content:
        return False
    TRUTH_PATH.write_text(new_content)
    return True


def _git_clean(repo: Path) -> bool:
    out = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    return out.returncode == 0 and not out.stdout.strip()


def _preflight() -> int:
    """Refuse to run if any affected repo has uncommitted work."""
    dirty = []
    for repo_name, _ in PUBLISHABLE_REPOS:
        repo = WORKSPACE / repo_name
        if repo.exists() and not _git_clean(repo):
            dirty.append(repo_name)
    for repo_name in ("statewave-docs", "statewave-web"):
        repo = WORKSPACE / repo_name
        if repo.exists() and not _git_clean(repo):
            dirty.append(repo_name)
    if dirty:
        print("✗ refusing to run — uncommitted changes in:")
        for r in dirty:
            print(f"    {r}")
        print()
        print("commit or stash before bumping, so the diff is reviewable.")
        return 1
    return 0


def _print_tag_commands(new_version: str) -> None:
    tag = f"v{new_version}"
    print()
    print(f"── next: tag + push each publishable repo (triggers remote workflows) ──")
    print()
    for repo_name, what in PUBLISHABLE_REPOS:
        print(f"  # {repo_name} — {what}")
        print(f"  cd {WORKSPACE}/{repo_name}")
        print(
            f"  git tag -a {tag} -m 'Release {tag}' && "
            f"git push origin {tag}"
        )
        print()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("version", help="target version, e.g. 0.8.1")
    p.add_argument(
        "--apply",
        action="store_true",
        help="write changes (default: dry-run preview)",
    )
    p.add_argument(
        "--skip-preflight",
        action="store_true",
        help="skip the 'all repos clean' check (use only if you know what you're doing)",
    )
    args = p.parse_args()

    if not re.fullmatch(r"\d+\.\d+\.\d+", args.version):
        sys.exit("error: version must be in form X.Y.Z")

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"╭─ Statewave workspace release — target v{args.version} ({mode})")
    print()

    if args.apply and not args.skip_preflight:
        rc = _preflight()
        if rc:
            return rc

    current_truth = _read_truth()
    if current_truth == args.version:
        print(f"truth source already at v{args.version} — skipping bump of {TRUTH_FILE}")
    else:
        if args.apply:
            _write_truth(args.version)
            print(f"  ✓ truth: v{current_truth} → v{args.version}  [{TRUTH_FILE}]")
        else:
            print(f"  would bump truth: v{current_truth} → v{args.version}  [{TRUTH_FILE}]")
    print()

    print("── propagating to mechanical surfaces ──")
    print()
    bumper = _load("bump_version", "bump-version.py")
    bump_rc = bumper.bump(args.version, apply=args.apply)
    if bump_rc != 0:
        print()
        print("✗ bump-version.py reported issues — fix targets in _targets.py and re-run.")
        return bump_rc

    if args.apply:
        print()
        print("── verifying with check-versions.py ──")
        print()
        checker = _load("check_versions", "check-versions.py")
        try:
            checker.main()
        except SystemExit as e:
            if e.code:
                return int(e.code) or 1

        _print_tag_commands(args.version)
    else:
        print()
        print(f"dry run — re-run with --apply to actually write changes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
