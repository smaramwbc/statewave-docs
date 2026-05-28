# Working in the Statewave workspace — agent guardrails

Read this before changing anything. It applies to autonomous agents (e.g. the
GitHub Copilot coding agent) and to anyone making docs/quality edits. It exists
because the easy "obvious" fix is sometimes exactly the wrong move here — the
rules below encode mistakes we don't want to repeat.

> **Canonical home:** this file lives in `statewave-docs/` and is the template
> for the other repos. Copy it to the root of any repo an agent will touch
> (`statewave/`, `statewave-web/`, `statewave-py/`, `statewave-ts/`, …) — GitHub
> Copilot reads `AGENTS.md` (or `.github/copilot-instructions.md`) from the root
> of the repo it is working in, so a single central copy is not enough.

## Hard rules — do not violate

1. **Never overclaim maturity.** Do not write "GA", "production-ready",
   "enterprise-ready", "hardened", or "battle-tested". The canonical maturity
   phrase is **"first stable public developer release."** Any benchmark or
   performance claim must be source-backed and caveated — never imply
   third-party validation we don't have.

2. **Public repos address users, not owners.** Every `statewave-*` repo is
   public **except `statewave-launch`** (private; holds ops/launch material).
   In public docs: no owner-facing TODOs, no "before launch" notes, no pricing
   placeholders, no internal commentary. Write for the reader/customer.

3. **Neutral brand voice on public-facing copy.** No personal/founder names in
   templates, posts, or outreach. Sign off as **"Statewave team"** or not at
   all. For visitor-first surfaces (homepage, core READMEs, package
   descriptions, social bios) the brand is the identity.

4. **Proof figures are mirrored — never hand-edit one surface.** Test counts,
   eval assertion/test counts, and the support-workflow benchmark score appear
   in many files. They have a single source of truth in
   [`tools/_proof_figures.py`](tools/_proof_figures.py). After any change that
   touches one of these numbers, run:

   ```bash
   python statewave-docs/tools/check-proof-figures.py
   ```

   If a number genuinely changed, re-run that figure's `source` command
   (`--sources` prints them), update `FIGURES` once, then fix every surface the
   checker flags. Do not "fix" a single doc to match your memory of the number.

5. **Versions are independent per package — do not "reconcile" them.** The core
   server, the Python SDK (`statewave` on PyPI), and the TypeScript SDK
   (`@statewavedev/sdk`) version on **separate cadences**. A core `0.9.x` next
   to an SDK `0.10.x` is **correct, not drift** — the compatibility axis is the
   `/v1` API contract, not a shared number. Verify with
   `python statewave-docs/tools/check-versions.py`. Never align version numbers
   across packages or rewrite `pip install statewave` pins to force a match.

6. **Launch copy is intentionally ahead — do not "correct" it.**
   `statewave-launch/posts/*.md` is pre-written for the unreleased **v1.0** and
   deliberately says `v1.0.0`, `pip install statewave==1.0.0`, `8/8`, etc. while
   shipped packages are still `0.x`. Rewriting it down to the current version
   destroys the launch messaging. Leave launch posts and dated release-notes /
   CHANGELOG entries as written — those are history, not drift.

7. **Respect the v1.0 launch freeze.** Until the launch is explicitly
   authorized: no new tags, releases, or version bumps, and no changes to
   backend / SDK / connector code. Docs, markdown, lint, and consistency fixes
   are in scope. If a task needs a frozen surface, stop and flag it.

## Conventions that keep CI green

- **Markdown lint is `markdownlint-cli2`** (matches CI), not `markdownlint-cli`.
  For the MD028 "no blank line inside blockquote" rule, merge adjacent
  blockquotes with a `>` on the empty line, or separate them with `---`. HTML
  comments do **not** satisfy MD028.
- **Link check (lychee) is brittle on some hosts.** Don't add
  `npmjs.com/package/<pkg>/v/<ver>` URLs or links to the private
  `statewave-launch` repo — they 4xx in CI. Keep the textual reference instead
  (e.g. `statewave==0.10.2 (PyPI)`), no hyperlink.
- **Run the consistency checks before opening a PR** that touches numbers or
  versions: `check-proof-figures.py` and `check-versions.py` both exit non-zero
  on drift and are meant to be CI gates.

## Git hygiene

- **No self-attribution.** Strip `Co-Authored-By`, "Generated with …", and any
  agent self-attribution from commit messages **and** PR descriptions.
- **Neutral commit identity** — `smaramwbc <145447586+smaramwbc@users.noreply.github.com>`.
- **Rebase merges only** — squash/merge-commit are disabled repo-wide; use
  `gh pr merge --rebase --delete-branch`.
- **Quote-safety:** backticks inside `git commit -m "…"` / `gh pr ... --body "…"`
  get command-substituted by the shell and silently eat the token. Write the
  message to a file and use `git commit -F` / `--body-file`.

## When unsure

Prefer asking over guessing. A wrong "fix" to public launch copy, a maturity
overclaim, or a forced version reconciliation is more expensive to undo than a
question is to ask.
