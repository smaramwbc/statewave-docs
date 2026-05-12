# Workspace tooling

Cross-repo housekeeping scripts for the Statewave workspace. They live in
`statewave-docs/tools/` but operate on sibling repos
(`statewave/`, `statewave-py/`, `statewave-ts/`, `statewave-docs/`)
via paths resolved from `__file__`, so they work from any cwd.

## `bump-version.py`

Propagates a new version number from `statewave/pyproject.toml`
(the workspace's truth source) to every known **mechanical** version
reference across the workspace.

Bump `statewave/pyproject.toml` to the new version first, then run:

```bash
# Dry-run (default) — shows what would change
python statewave-docs/tools/bump-version.py 0.7.3

# Apply
python statewave-docs/tools/bump-version.py 0.7.3 --apply
```

### What it touches

| Surface | Where |
|---|---|
| Python SDK `version` field | `statewave-py/pyproject.toml` |
| Python SDK `__version__` | `statewave-py/statewave/__init__.py` |
| TypeScript SDK `version` field | `statewave-ts/package.json` |
| Core README "active development" sentence | `statewave/README.md` |
| Docs "active early development" status | `statewave-docs/product.md` |
| Test-counts label | `statewave-docs/architecture/repo-map.md` |
| SDK table rows (Python + TS) | `statewave-docs/architecture/repo-map.md` |

### What it does NOT touch (you handle manually)

- The `Status:` blurb in `statewave/README.md` — the prose around the
  version changes per release (which features shipped). The script flags
  it for review.
- The feature blurb in `statewave-docs/README.md` — same reason.
- CHANGELOGs in `statewave-py/` and `statewave-ts/` — entries need a
  human-authored body.
- `statewave/pyproject.toml` — this is the **truth source**; bump it
  before running the script.
- The `statewave-connectors` repo — connectors have their own
  independent version stream (each connector package versions
  separately, plus the wave / RELEASE_NOTES.md timeline). Don't try to
  tie connectors to the server version.
- Marketing copy on `statewave-web` and the dev.to / Medium launch
  posts — those are external surfaces that are out of scope here.

## `check-versions.py`

Verifies every mechanical surface matches the truth.

```bash
python statewave-docs/tools/check-versions.py
```

- Exits `0` if all mechanical surfaces match.
- Exits `1` if any mechanical surface has drifted, or if a configured
  target's pattern no longer matches (means `_targets.py` is stale).
- Editorial surfaces are reported with current version but never fail
  the check.

Wire as a release-blocker on the `statewave/` release-tag workflow:

```yaml
- name: Verify workspace version consistency
  run: python statewave-docs/tools/check-versions.py
```

## Adding new targets

Both scripts share `_targets.py`. To track a new file/string, add an
entry to `TARGETS`:

```python
(
    "unique_key",
    "relative/path/from/workspace/root.md",
    r'pattern with (capture group 1) holding the version',
    'replacement template with {ver}',  # or None for editorial
    "mechanical",  # or "mechanical_resub" or "editorial"
),
```

`kind` semantics:

- **`"mechanical"`** — pattern's group 1 is the version; replacement is
  `template.format(ver=new_version)`.
- **`"mechanical_resub"`** — pattern has multiple capture groups
  (typically for table rows or other contexts where the version is
  sandwiched between text that must be preserved). Replacement uses
  `\g<N>` backrefs and `{ver}` for the new version. The version is
  captured in group 2 by convention.
- **`"editorial"`** — pattern's group 1 is the current version, but the
  surrounding prose changes per release. The bumper flags the surface
  for manual review; the checker reports it but doesn't fail.

After adding a target, sanity-check with:

```bash
python statewave-docs/tools/check-versions.py
```

— it should still pass (no drift introduced) and the new target should
appear in the editorial section if `kind="editorial"`.
