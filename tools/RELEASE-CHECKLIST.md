# Server release checklist

The single most important rule:

> **Version bump + version mirrors + checklist pass must happen before the tag is pushed.**
> Once a tag is pushed it is immutable. Forgetting a mirror means the release workflow fails on a tag we cannot move.

This is a checklist, not tooling. It exists because we made the mistake described under [What went wrong on v0.9.2](#what-went-wrong-on-v092) — let's not repeat it.

Scope: this applies to the **server / reference-impl version** only (`statewave/pyproject.toml`). The Python SDK (`statewave-py`), the TypeScript SDK (`statewave-ts`), and the Helm chart version their own packages on their own cadences — see [`_targets.py`](_targets.py) for the model.

## The checklist

### Step 1 — Bump truth

Edit `statewave/pyproject.toml`:

```toml
version = "X.Y.Z"   # the new server version
```

**Do not stage / commit yet.** This and the next step go in **one commit together**.

### Step 2 — Propagate to mirrors

From the workspace root (sibling clones of `statewave/`, `statewave-docs/`, `statewave-py/`, `statewave-ts/`):

```bash
# Dry-run first — shows you exactly what would change
python statewave-docs/tools/bump-version.py X.Y.Z

# When happy, apply
python statewave-docs/tools/bump-version.py X.Y.Z --apply
```

The tool rewrites the **mechanical** surfaces — README banners, status blurbs, doc map labels, conceptual-doc banners — to match truth. It does **not** touch editorial prose, SDK rows, or anything it considers independently versioned. See [`_targets.py`](_targets.py) for the catalogue.

### Step 3 — Verify locally

From the same workspace root:

```bash
python statewave-docs/tools/check-versions.py
```

Must exit `0`. If it doesn't:

- `mechanical surface(s) drift from truth` → re-run `bump-version.py --apply`; you probably skipped the apply.
- `editorial surface(s)` flag → manual prose review only; **never fails CI**, but worth a pass on each release.
- `independently-versioned surface(s)` → never fails; only update if the named package itself is releasing.

### Step 4 — Commit as a single atomic change

```bash
git -C statewave add pyproject.toml README.md
git -C statewave-docs add architecture/repo-map.md  # or whichever surfaces changed
# … and any other workspace mirrors

# One commit per repo, message clearly labelling this as the version bump
git commit -m "chore: bump version to X.Y.Z (and propagate mirrors)"
```

**The pyproject bump and the mirror bumps belong in the same commit.** This is the rule that v0.9.2 broke and that this checklist exists to enforce.

### Step 5 — Open the PR(s) and wait for CI

PR per repo touched. Standard CI must be green before proceeding. **Do not tag while a PR is still open** — if a reviewer asks for changes, the version bump needs to ride those changes, and tagging early ties you to the wrong commit.

### Step 6 — Merge

```bash
gh pr merge <number> --rebase --delete-branch
```

Per [statewave merge convention](https://github.com/smaramwbc/statewave): rebase only, no squash.

Pull the merged state locally:

```bash
git checkout main && git pull --ff-only
```

### Step 7 — Tag the merge commit

```bash
git tag -a vX.Y.Z <merge-sha> -m "vX.Y.Z — <one-line summary>

<release notes here, will also be used by gh release>"

git push origin vX.Y.Z
```

The tag points at the merge commit — the commit that has truth + mirrors aligned.

### Step 8 — Confirm the release workflow passes

The `Release` workflow at [`.github/workflows/release.yml`](https://github.com/smaramwbc/statewave/blob/main/.github/workflows/release.yml) fires on tag-push. Its first job (`Verify server/contract version self-consistency`) runs `check-versions.py` against the **tagged** commit. If steps 1–7 were followed, this MUST pass.

If it fails:

1. **Do not** force-move the tag — [published tags are immutable](https://github.com/smaramwbc/statewave-docs/blob/main/CHANGELOG.md#v091--v09-governance-release-correction-2026-05-26).
2. Cut the next patch (vX.Y.(Z+1)) at current main with the additional mirrors fixed. The bad tag stays in history with a "Superseded by …" banner on its GitHub release.

### Step 9 — Verify the GitHub release looks right

The workflow's second job creates a GitHub release auto-populated from the tag message. Either:
- Let it be (auto-notes are usually fine for patch releases), or
- Manually edit if the release deserves a curated narrative (see e.g. [v0.9.1](https://github.com/smaramwbc/statewave/releases/tag/v0.9.1) for a long-form note).

---

## What went wrong on v0.9.2

A direct lessons-learned, written so the next maintainer doesn't have to read the chat history.

**The mistake.** v0.9.2 bumped `statewave/pyproject.toml` from `0.9.0` to `0.9.2` in a focused PR that touched **only** pyproject. The tag was then pushed at that commit. The Release workflow's `Verify` step caught two stale README mirror surfaces (`core_active_dev`, `core_status_blurb`) and one in `statewave-docs/architecture/repo-map.md` (`docs_test_counts_label`), and failed.

The drift was real — `pip show statewave` would have reported `0.9.2` while the README said `v0.9.0`. The check-versions tool did exactly what it was supposed to do.

**Why the mirrors were missed.** The PR scope was read narrowly as "bump pyproject metadata" without the broader "and propagate mirrors" step. The `bump-version.py` tool exists precisely for that propagation — but it was not run because the workflow-enforced rule wasn't visible at PR-authoring time.

**Why we did not force-move the tag.** Published tags are immutable. Anyone who already pinned to `vX.Y.Z` would see the SHA shift silently — a quiet supply-chain risk. The Statewave-workspace rule is: when a tag is wrong, cut an additive patch. We have a precedent for this: v0.9.0 was a stub tag at pre-v0.9 code, and v0.9.1 superseded it without touching v0.9.0 itself.

**How we recovered.** Two follow-up PRs in `statewave` and `statewave-docs` ran `bump-version.py 0.9.2 --apply` and committed the mirror fixes. The failed workflow run was deleted so future on-lookers don't think the v0.9.2 release is unstable. Current main has truth + mirrors aligned, so the next tag (when it lands) will pass `Verify` on the first try.

**The structural fix.** This checklist. The rule lives at the source — the `tools/` directory next to the bump and check scripts — and is referenced from both tools' docstrings. The next maintainer cutting a release sees the pointer before they push a tag.

---

## See also

- [`bump-version.py`](bump-version.py) — the propagation script.
- [`check-versions.py`](check-versions.py) — the verifier the Release workflow runs.
- [`_targets.py`](_targets.py) — the catalogue of mirror surfaces and the model docstring explaining mechanical vs editorial vs independent.
- [statewave Release workflow](https://github.com/smaramwbc/statewave/blob/main/.github/workflows/release.yml) — the CI that enforces this on every tag push.
