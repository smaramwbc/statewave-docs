"""Shared version-target config for bump-version.py and check-versions.py.

Each entry in TARGETS:

    (key, relative_path_from_workspace, regex_pattern,
     replacement_template_or_None, kind)

kind:
    "mechanical"
        Pattern's capture group 1 is the current version. Bumper writes
        replacement_template.format(ver=new_version) into the matched span.

    "mechanical_resub"
        Pattern uses multiple capture groups. Replacement_template contains
        \\g<N> backrefs to preserve surrounding text, and {ver} for the new
        version. Bumper does re.sub(pattern, template_with_ver_subbed, ...).
        Use this for table rows where the version is sandwiched between
        per-row text that must be preserved.

    "editorial"
        Pattern's capture group 1 is the current version, but the surrounding
        prose changes per release (status blurbs, feature blurbs). Bumper
        flags these for manual review; replacement_template is None.

Truth source for the workspace version is statewave/pyproject.toml.
"""

TRUTH_FILE = "statewave/pyproject.toml"
TRUTH_PATTERN = r'^version\s*=\s*"(\d+\.\d+\.\d+)"'

TARGETS = [
    (
        "py_pyproject",
        "statewave-py/pyproject.toml",
        r'^version\s*=\s*"(\d+\.\d+\.\d+)"',
        'version = "{ver}"',
        "mechanical",
    ),
    (
        "py_init_version",
        "statewave-py/statewave/__init__.py",
        r'__version__\s*=\s*"(\d+\.\d+\.\d+)"',
        '__version__ = "{ver}"',
        "mechanical",
    ),
    (
        "ts_package_json",
        "statewave-ts/package.json",
        r'"version":\s*"(\d+\.\d+\.\d+)"',
        '"version": "{ver}"',
        "mechanical",
    ),
    (
        "docs_product_status",
        "statewave-docs/product.md",
        r'in active early development \(v(\d+\.\d+\.\d+)\)',
        'in active early development (v{ver})',
        "mechanical",
    ),
    (
        "docs_test_counts_label",
        "statewave-docs/architecture/repo-map.md",
        r'## Test counts \(as of v(\d+\.\d+\.\d+)\)',
        '## Test counts (as of v{ver})',
        "mechanical",
    ),
    (
        "docs_sdk_row_python",
        "statewave-docs/architecture/repo-map.md",
        r'(`statewave` \(Python SDK\)[^|]+\|[^|]+\|\s*)(\d+\.\d+\.\d+)(\s*\|\s*Apache-2\.0)',
        r'\g<1>{ver}\g<3>',
        "mechanical_resub",
    ),
    (
        "docs_sdk_row_ts",
        "statewave-docs/architecture/repo-map.md",
        r'(`@statewavedev/sdk` \(TypeScript SDK\)[^|]+\|[^|]+\|\s*)(\d+\.\d+\.\d+)(\s*\|\s*Apache-2\.0)',
        r'\g<1>{ver}\g<3>',
        "mechanical_resub",
    ),
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
        r'> \*\*Status:\*\* v(\d+\.\d+\.\d+) —',
        None,
        "editorial",
    ),
    (
        "docs_readme_feature_blurb",
        "statewave-docs/README.md",
        r'\*\*v(\d+\.\d+\.\d+)\*\* —',
        None,
        "editorial",
    ),
]
