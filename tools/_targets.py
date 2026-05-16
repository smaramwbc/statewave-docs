"""Shared version-target config for bump-version.py and check-versions.py.

## Versioning model (see smaramwbc/statewave#106)

Packages are **versioned independently per semver, per repo**. There is no
single workspace-wide version that every package must match — the Python SDK
(`statewave` on PyPI), the TypeScript SDK (`@statewavedev/sdk` on npm), and the
server release on their own cadences.

The cross-repo **compatibility axis is the `/v1` API contract**, not a package
number. Any SDK that speaks `/v1` works against any server that serves `/v1`;
that guarantee lives in prose in `api/v1-contract.md`, not in matching version
strings.

`TRUTH_FILE` (statewave/pyproject.toml) is therefore the **server /
reference-implementation version** — it governs only the server repo's own
self-referential surfaces (its README status line) and the conceptual-doc
banners that describe "the system as implemented at server vX.Y". It does
**not** assert anything about SDK package numbers.

## kind

    "mechanical"
        Capture group 1 is the current version; it tracks TRUTH exactly.
        Use only for surfaces that legitimately reference the server /
        reference-impl version. Bumper writes
        replacement_template.format(ver=new_version) into the matched span.

    "mechanical_minor"
        Like "mechanical" but the surface tracks only major.minor of TRUTH
        (conceptual-doc banners that shouldn't churn every patch). Capture
        group 1 is the current major.minor; replacement uses {ver_minor}.

    "mechanical_resub"
        Pattern uses multiple capture groups. replacement contains \\g<N>
        backrefs to preserve surrounding text and {ver} for the new version;
        the version is capture group 2. Use for spans where the version is
        sandwiched between text that must be preserved.

    "editorial"
        Capture group 1 is the current version, but the surrounding prose
        changes per release (status/feature blurbs). Flagged for manual
        review; never fails CI; never auto-written. replacement is None.

    "independent"
        Surface names a package that versions on its own cadence (an SDK
        row, a per-SDK status line). Capture group 1 is that package's
        version. By design it does NOT have to equal TRUTH — it is
        reported for human confirmation, never fails CI, and is never
        auto-written by the bumper. Update it by hand when that package
        releases. replacement is None. This kind exists so the
        independence is explicit and a future maintainer doesn't
        "reconcile" it back into a lockstep check.
"""

TRUTH_FILE = "statewave/pyproject.toml"
TRUTH_PATTERN = r'^version\s*=\s*"(\d+\.\d+\.\d+)"'

TARGETS = [
    # --- Server / reference-impl self-references (legitimately track TRUTH) ---
    (
        "core_active_dev",
        "statewave/README.md",
        r'Statewave is in active development \(v(\d+\.\d+\.\d+)\)',
        'Statewave is in active development (v{ver})',
        "mechanical",
    ),
    (
        "core_status_blurb",
        "statewave/README.md",
        r'(> \*\*v)(\d+\.\d+\.\d+)(\*\* — actively developed)',
        r'\g<1>{ver}\g<3>',
        "mechanical_resub",
    ),
    (
        "docs_test_counts_label",
        "statewave-docs/architecture/repo-map.md",
        r'## Test counts \(as of v(\d+\.\d+\.\d+)\)',
        '## Test counts (as of v{ver})',
        "mechanical",
    ),
    # --- Conceptual-doc banners: "the system as implemented at server vX.Y" ---
    # major.minor only, so conceptual docs don't churn every patch release.
    (
        "docs_banner_overview",
        "statewave-docs/architecture/overview.md",
        r'^Version: \*\*(\d+\.\d+)\.x\*\*',
        'Version: **{ver_minor}.x**',
        "mechanical_minor",
    ),
    (
        "docs_banner_repo_map",
        "statewave-docs/architecture/repo-map.md",
        r'^Version: \*\*(\d+\.\d+)\.x\*\*',
        'Version: **{ver_minor}.x**',
        "mechanical_minor",
    ),
    (
        "docs_banner_v1_contract",
        "statewave-docs/api/v1-contract.md",
        r'^Version: \*\*(\d+\.\d+)\.x\*\*',
        'Version: **{ver_minor}.x**',
        "mechanical_minor",
    ),
    (
        "docs_banner_conventions",
        "statewave-docs/dev/conventions.md",
        r'^Version: \*\*(\d+\.\d+)\.x\*\*',
        'Version: **{ver_minor}.x**',
        "mechanical_minor",
    ),
    # --- Editorial: version-stamped prose that needs a human per release ---
    (
        "docs_readme_feature_blurb",
        "statewave-docs/README.md",
        r'\*\*v(\d+\.\d+\.\d+)\*\* —',
        None,
        "editorial",
    ),
    # --- Independently-versioned package surfaces (NOT tied to TRUTH) ---
    # Each package versions on its own cadence; these are reported for
    # confirmation, never failed, never auto-written. Hand-update on release.
    (
        "docs_product_status",
        "statewave-docs/product.md",
        r'in active early development \(v(\d+\.\d+\.\d+)\)',
        None,
        "independent",
    ),
    (
        "docs_sdk_row_python",
        "statewave-docs/architecture/repo-map.md",
        r'`statewave` \(Python SDK\)[^|]+\|[^|]+\|\s*(\d+\.\d+\.\d+)\s*\|\s*Apache-2\.0',
        None,
        "independent",
    ),
    (
        "docs_sdk_row_ts",
        "statewave-docs/architecture/repo-map.md",
        r'`@statewavedev/sdk` \(TypeScript SDK\)[^|]+\|[^|]+\|\s*(\d+\.\d+\.\d+)\s*\|\s*Apache-2\.0',
        None,
        "independent",
    ),
]
