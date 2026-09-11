# Codex Reply — Issue #167

- Assignment: GitHub issue #167, eliminate case-colliding public-path Windows build risk
- Timestamp: 2026-09-11T11:57:25-04:00
- Branch: `codex/issue-167-case-collision-guard`
- Substantive commit: `07d3f3c165c`
- Pull request: #185 — https://github.com/Brian910cpr/910cpr-class-landers/pull/185
- Work-item state: `PR_OPEN`
- Persistent-system evidence state: `BUILT` (the revised scheduled publication path is not merged or production-proven yet)

## Findings and root cause

The Git tree contains exactly five case-insensitive collision groups:

1. `docs/ACLS.html` and `docs/acls.html`
2. `docs/BLS.html` and `docs/bls.html`
3. `docs/Earl/index.html` and `docs/earl/index.html`
4. `docs/HEARTSAVER.html` and `docs/heartsaver.html`
5. `docs/PALS.html` and `docs/pals.html`

These are intentional public aliases. The uppercase course-code pages were introduced as public selector/legacy routes, while their lowercase counterparts are canonical pages; Earl similarly has a legacy-cased public route. The blobs are not identical. GitHub Pages currently serves all five uppercase routes with HTTP 200 and lowercase canonical links. A case-insensitive Windows worktree cannot independently materialize both tracked blobs, which caused publication dirtiness even after reset/clean.

## Work performed

- Changed the canonical public-refresh job from `windows-latest` to `ubuntu-latest`, preserving both case variants in the checkout.
- Added `scripts/run_validated_public_build.py`, a cross-platform entry point with the same ordered module sequence and test-skip behavior as the existing batch runner.
- Added `scripts/check_case_insensitive_paths.py`, which inventories tracked Git paths, permits only the five documented collision groups, and fails for either a new collision or an unexplained allowlist mismatch.
- Added the collision guard to the existing source-integrity CI workflow.
- Added focused unit tests for collision detection/allowlisting and the portable build command plan.
- Preserved every existing generated route; no generator or mass rebuild was run.

## Exact files changed

- `.github/workflows/refresh-public-site.yml`
- `.github/workflows/source-integrity.yml`
- `scripts/check_case_insensitive_paths.py`
- `scripts/run_validated_public_build.py`
- `tests/test_case_insensitive_paths.py`
- `tests/test_run_validated_public_build.py`
- `Codex_Reply_Issue167.md` (this receipt, communication-only follow-up commit)

## Tests and checks

- `python -m py_compile scripts/check_case_insensitive_paths.py scripts/run_validated_public_build.py tests/test_case_insensitive_paths.py tests/test_run_validated_public_build.py` — passed.
- `python -m unittest tests.test_case_insensitive_paths tests.test_run_validated_public_build` — 4 tests passed.
- `python scripts/check_case_insensitive_paths.py` — 5 approved groups, 0 unexpected, passed.
- `git diff --check` — passed.
- Both changed workflow YAML files parsed with PyYAML — passed.
- `actionlint` was checked on PATH and common Windows install locations but was not installed; this is a validation limitation, not evidence of a workflow error.
- Live production checks on 2026-09-11: `/ACLS.html`, `/BLS.html`, `/HEARTSAVER.html`, `/PALS.html`, and `/Earl/` each returned HTTP 200 and declared the corresponding lowercase canonical URL.

## Known unrelated working-tree state

The original checkout was dirty before this task and was not altered. The separate Windows worktree itself reports `docs/Earl/index.html` and `docs/PALS.html` modified because Windows materializes one side of those case collisions; those files and test-generated `__pycache__` files were explicitly excluded from staging and commits.

## Deployment and proof status

- Validated locally: yes, at syntax, unit, inventory-guard, YAML-parse, and current-live-route levels.
- Pushed: yes, branch and substantive commit are on GitHub.
- PR: open (#185).
- Merged: no.
- Deployed: no.
- Revised end-to-end public refresh proven: no. The prior Windows run 34424816909 is the failure evidence; the Linux workflow must be merged and run successfully before promotion beyond `BUILT`.
- Current customer-facing legacy URLs: live and HTTP 200, independently verified as listed above.
- Observer health: GitHub Actions source-integrity CI will continuously reject collision drift once merged. PR checks were pending when this receipt was written.

## Remaining risks and exact next action

The portable runner duplicates the established batch module order; future build-step changes should keep both entry points aligned or eventually make the Python runner authoritative. The production workflow cannot be proven from a pull-request branch because `refresh-public-site.yml` publishes only from `main` and has write authority.

Recommended next action for ChatGPT: review and merge PR #185 after checks pass, manually dispatch `Refresh public site from Enrollware iCal` with `force_rebuild=true`, verify the run publishes cleanly from Ubuntu, then verify GitHub Pages plus the five uppercase URLs and their lowercase canonical links. Keep Cloudflare issue #164 separate.

User/account-level action required: a repository maintainer must merge PR #185 and authorize/observe the production workflow dispatch; no credentials or external account changes are otherwise required.
