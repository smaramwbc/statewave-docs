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

### What it touches (auto-written)

These are the surfaces that legitimately track the server / reference-impl
version, so the bumper writes them. SDK packages version **independently**
(per `statewave#106`) and are NOT in this set.

| Surface | Where | Kind |
|---|---|---|
| Core README "active development" sentence | `statewave/README.md` | `mechanical` |
| Core README "actively developed" status blurb | `statewave/README.md` | `mechanical_resub` |
| Test-counts label | `statewave-docs/architecture/repo-map.md` | `mechanical` |
| Conceptual-doc banner (`Version: **X.Y.x**`) | `architecture/overview.md`, `architecture/repo-map.md`, `api/v1-contract.md`, `dev/conventions.md` | `mechanical_minor` |

### Reported but never auto-written (you handle manually)

| Surface | Where | Kind |
|---|---|---|
| Docs README feature blurb | `statewave-docs/README.md` | `editorial` |
| `product.md` "first stable public developer release (vX.Y.Z)" status | `statewave-docs/product.md` | `independent` |
| SDK table rows (Python + TS) | `statewave-docs/architecture/repo-map.md` | `independent` |

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
- **`"mechanical_minor"`** — like `mechanical` but the surface tracks only
  `major.minor` of the truth (conceptual-doc banners that shouldn't churn
  every patch). Group 1 is the current `major.minor`; replacement uses
  `{ver_minor}`.
- **`"mechanical_resub"`** — pattern has multiple capture groups
  (typically for table rows or other contexts where the version is
  sandwiched between text that must be preserved). Replacement uses
  `\g<N>` backrefs and `{ver}` for the new version. The version is
  captured in group 2 by convention.
- **`"editorial"`** — pattern's group 1 is the current version, but the
  surrounding prose changes per release. The bumper flags the surface
  for manual review; the checker reports it but doesn't fail.
- **`"independent"`** — pattern's group 1 names a package that versions on
  its own cadence (an SDK row, a per-SDK status line). It does NOT have to
  equal the truth: reported for confirmation, never failed, never
  auto-written. Hand-update on that package's release.

After adding a target, sanity-check with:

```bash
python statewave-docs/tools/check-versions.py
```

— it should still pass (no drift introduced) and the new target should
appear in the editorial section if `kind="editorial"`.

## Version-history bodies (`HISTORY_BODIES`)

Some conceptual docs carry a "Version history" body alongside their
banner — e.g. `architecture/overview.md`. The banner check would happily
pass with the banner at v0.9.x while the body's newest entry stopped at
v0.8, which is exactly what happened on the v0.9 release.

`HISTORY_BODIES` in `_targets.py` is a separate list of
`(key, path, heading_template)` entries. At check time the template is
formatted with the truth's `{ver_minor}` and the file must contain that
heading somewhere. The bumper never auto-writes these — release-note prose
is human-authored — but `bump-version.py` flags the gap and
`check-versions.py` fails the release-tag workflow until the heading is
added. Add a new doc here whenever you create a new
banner-plus-version-history surface.
