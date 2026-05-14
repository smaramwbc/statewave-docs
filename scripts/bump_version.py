#!/usr/bin/env python
"""Bump or verify Statewave ecosystem version refs in this docs repo.

This repo is a coordinator: it documents shipped versions of three siblings
that own their own version metadata.

  - server (`statewave/pyproject.toml`)
  - Python SDK (`statewave-py/pyproject.toml`)
  - TypeScript SDK (`statewave-ts/package.json`)

Markdown can't read those at render time, so this script keeps the docs in
sync. Default mode discovers versions from sibling repos under the same
parent directory; pass `--server` / `--py` / `--ts` to override (useful for
CI when siblings live elsewhere or are pinned to a specific sha).

Usage:
    python scripts/bump_version.py                          # apply: read siblings, write docs
    python scripts/bump_version.py --check                  # verify only
    python scripts/bump_version.py --server 0.8.0 --py 0.7  # apply with overrides

Exit codes:
    0 — applied successfully (or all targets already match in --check)
    1 — drift detected (--check), missing siblings, or invalid args
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIBLINGS = ROOT.parent

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
PYPROJECT_VERSION_RE = re.compile(r'^version = "(?P<version>[^"]+)"', re.MULTILINE)


@dataclass
class Target:
    """One anchored substitution. The pattern matches verbatim except for the
    `version` named group; the template rebuilds the full matched text."""

    path: Path
    pattern: str
    template: str


SERVER_TARGETS: list[Target] = [
    Target(
        path=ROOT / "product.md",
        pattern=r"Statewave is in active early development \(v(?P<version>[^)]+)\)\. We document",
        template="Statewave is in active early development (v{version}). We document",
    ),
    Target(
        path=ROOT / "README.md",
        pattern=r"\*\*v(?P<version>\S+)\*\* — Full support-agent intelligence stack",
        template="**v{version}** — Full support-agent intelligence stack",
    ),
    Target(
        path=ROOT / "api" / "v1-contract.md",
        pattern=r"^Version: \*\*(?P<version>[^*]+)\*\*$",
        template="Version: **{version}**",
    ),
    Target(
        path=ROOT / "architecture" / "repo-map.md",
        pattern=r"^Version: \*\*(?P<version>[^*]+)\*\*$",
        template="Version: **{version}**",
    ),
    Target(
        path=ROOT / "architecture" / "repo-map.md",
        pattern=r"\| `statewave` \| Core server — API, domain model, DB, services, deployment \| (?P<version>\S+) \| Apache-2\.0 \|",
        template="| `statewave` | Core server — API, domain model, DB, services, deployment | {version} | Apache-2.0 |",
    ),
    Target(
        path=ROOT / "architecture" / "repo-map.md",
        pattern=r"## Test counts \(as of v(?P<version>[^)]+)\)",
        template="## Test counts (as of v{version})",
    ),
]

PY_TARGETS: list[Target] = [
    Target(
        path=ROOT / "architecture" / "repo-map.md",
        pattern=r"\| `statewave` \(Python SDK\) \| Sync \+ async clients, typed exceptions, auth, batch \| (?P<version>\S+) \| Apache-2\.0 \|",
        template="| `statewave` (Python SDK) | Sync + async clients, typed exceptions, auth, batch | {version} | Apache-2.0 |",
    ),
]

TS_TARGETS: list[Target] = [
    Target(
        path=ROOT / "architecture" / "repo-map.md",
        pattern=r"\| `@statewavedev/sdk` \(TypeScript SDK\) \| Typed errors, auth, batch, ESM \| (?P<version>\S+) \| Apache-2\.0 \|",
        template="| `@statewavedev/sdk` (TypeScript SDK) | Typed errors, auth, batch, ESM | {version} | Apache-2.0 |",
    ),
]

# Bundles: (key, source-repo-dir-name, manifest-file, targets).
# The source-repo dir names match the GitHub repo names — those are
# unchanged. The published package names live inside the manifests.
BUNDLES = [
    ("server", "statewave", "pyproject.toml", SERVER_TARGETS),
    ("py", "statewave-py", "pyproject.toml", PY_TARGETS),
    ("ts", "statewave-ts", "package.json", TS_TARGETS),
]


def _read_pyproject(path: Path) -> str | None:
    if not path.exists():
        return None
    match = PYPROJECT_VERSION_RE.search(path.read_text(encoding="utf-8"))
    return match["version"] if match else None


def _read_package_json(path: Path) -> str | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("version")


def discover(kind: str) -> str | None:
    if kind == "server":
        return _read_pyproject(SIBLINGS / "statewave" / "pyproject.toml")
    if kind == "py":
        return _read_pyproject(SIBLINGS / "statewave-py" / "pyproject.toml")
    if kind == "ts":
        return _read_package_json(SIBLINGS / "statewave-ts" / "package.json")
    raise ValueError(f"unknown kind {kind!r}")


def resolve_versions(args: argparse.Namespace) -> dict[str, str]:
    """Override flags win; otherwise read siblings. Returns {} on error."""
    overrides = {"server": args.server, "py": args.py, "ts": args.ts}
    resolved: dict[str, str] = {}
    errors = False
    for kind, sibling, source, _ in BUNDLES:
        version = overrides[kind] or discover(kind)
        if version is None:
            print(
                f"error: cannot resolve {kind} version — "
                f"{SIBLINGS / sibling / source} not found and no --{kind} override given",
                file=sys.stderr,
            )
            errors = True
            continue
        if not SEMVER_RE.match(version):
            print(
                f"error: {kind} version {version!r} is not a valid version (expected X.Y.Z)",
                file=sys.stderr,
            )
            errors = True
            continue
        resolved[kind] = version
    return {} if errors else resolved


def _match(target: Target, text: str) -> re.Match[str] | None:
    return re.compile(target.pattern, re.MULTILINE).search(text)


def apply_target(target: Target, new: str) -> bool:
    text = target.path.read_text(encoding="utf-8")
    match = _match(target, text)
    if not match:
        raise RuntimeError(
            f"pattern not found in {target.path.relative_to(ROOT)}: {target.pattern!r}"
        )
    if match["version"] == new:
        return False
    updated = re.compile(target.pattern, re.MULTILINE).sub(
        target.template.format(version=new), text, count=1
    )
    target.path.write_text(updated, encoding="utf-8")
    return True


def is_stale(target: Target, expected: str) -> tuple[bool, str]:
    """Returns (stale, reason). Pattern-missing counts as drift."""
    text = target.path.read_text(encoding="utf-8")
    match = _match(target, text)
    if not match:
        return True, "anchor pattern not found (file edited without updating the script?)"
    if match["version"] != expected:
        return True, f"found {match['version']!r}, expected {expected!r}"
    return False, ""


def cmd_check(versions: dict[str, str]) -> int:
    drifted: list[tuple[str, Target, str]] = []
    for kind, _, _, targets in BUNDLES:
        for t in targets:
            stale, reason = is_stale(t, versions[kind])
            if stale:
                drifted.append((kind, t, reason))
    if not drifted:
        print(
            f"all version references in sync — "
            f"server={versions['server']}, py={versions['py']}, ts={versions['ts']}"
        )
        return 0
    print("version drift detected:", file=sys.stderr)
    for kind, t, reason in drifted:
        print(f"  - [{kind}] {t.path.relative_to(ROOT)} — {reason}", file=sys.stderr)
    print("\nfix: python scripts/bump_version.py", file=sys.stderr)
    return 1


def cmd_apply(versions: dict[str, str]) -> int:
    changed = 0
    for kind, _, _, targets in BUNDLES:
        new = versions[kind]
        for t in targets:
            if apply_target(t, new):
                print(f"  [{kind}={new}] updated {t.path.relative_to(ROOT)}")
                changed += 1
    if changed == 0:
        print(
            f"already in sync — "
            f"server={versions['server']}, py={versions['py']}, ts={versions['ts']}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify only, do not edit")
    parser.add_argument("--server", help="override server version (default: read ../statewave/pyproject.toml)")
    parser.add_argument("--py", help="override Python SDK version (default: read ../statewave-py/pyproject.toml)")
    parser.add_argument("--ts", help="override TypeScript SDK version (default: read ../statewave-ts/package.json)")
    args = parser.parse_args()

    versions = resolve_versions(args)
    if not versions:
        return 1

    return cmd_check(versions) if args.check else cmd_apply(versions)


if __name__ == "__main__":
    raise SystemExit(main())
