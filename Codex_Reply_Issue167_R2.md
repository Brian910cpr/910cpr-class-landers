# Codex Reply — Issue #167, verification round 2

- Assignment: GitHub issue #167, eliminate case-colliding public-path Windows build risk
- Timestamp: 2026-09-11T12:22:07-04:00
- Branch: `codex/issue-167-verification-r2`
- Substantive repair commit: `07d3f3c165c9bb61b5019c03649c9f97fbc5b8d9`
- Merge commit: `ea10db1ce219ef26c575eb493367d916df162aec`
- Production publication commit: `256f8895c3e0b852859ec713c238db34056445cf`
- Pull request: #185 — https://github.com/Brian910cpr/910cpr-class-landers/pull/185
- Work-item state: `VERIFIED`
- Persistent-system evidence state: `HEALTHY`

## Root cause and durable strategy

The Git tree intentionally contains five case-insensitive collision groups for legacy public URLs. A Windows worktree cannot independently materialize both tracked blobs, which caused the prior publication checkout to remain dirty. The durable repair preserves all aliases, moves the canonical public-refresh job to an Ubuntu case-sensitive worktree, adds a cross-platform Python build entry point, and adds source-integrity CI that fails for any collision outside the five explicit legacy groups.

The approved inventory remains:

1. `docs/ACLS.html` and `docs/acls.html`
2. `docs/BLS.html` and `docs/bls.html`
3. `docs/Earl/index.html` and `docs/earl/index.html`
4. `docs/HEARTSAVER.html` and `docs/heartsaver.html`
5. `docs/PALS.html` and `docs/pals.html`

## Work performed

- Re-reviewed the issue, repository `AGENTS.md`, and `CODEX_HANDOFF_PROTOCOL.md` before acting.
- Re-ran the focused syntax, unit, collision-inventory, diff, and workflow-YAML checks.
- Re-verified all five uppercase legacy production routes before merge.
- Merged PR #185 after its required checks passed.
- Observed the merge-triggered canonical refresh run through the full build, reconciliation, link audit, inventory validation, publication commit, and push from Ubuntu.
- Observed the resulting GitHub Pages build and deployment to success.
- Re-verified all five uppercase legacy routes after deployment.
- Preserved unrelated dirty files in the original checkout and used separate named worktrees.

## Exact files changed by the substantive repair

- `.github/workflows/refresh-public-site.yml`
- `.github/workflows/source-integrity.yml`
- `scripts/check_case_insensitive_paths.py`
- `scripts/run_validated_public_build.py`
- `tests/test_case_insensitive_paths.py`
- `tests/test_run_validated_public_build.py`
- `Codex_Reply_Issue167.md`

This verification round changes only `Codex_Reply_Issue167_R2.md` on its branch.

## Tests and checks

- `python -m py_compile scripts/check_case_insensitive_paths.py scripts/run_validated_public_build.py tests/test_case_insensitive_paths.py tests/test_run_validated_public_build.py` — passed.
- `python -m unittest tests.test_case_insensitive_paths tests.test_run_validated_public_build` — 4 tests passed.
- `python scripts/check_case_insensitive_paths.py` — exactly 5 approved groups and 0 unexpected groups; passed.
- `git diff --check origin/main...HEAD` on the repair branch — passed.
- Both changed workflow YAML files parsed with PyYAML — passed.
- PR #185 source-integrity, Cloudflare preflight, and Cloudflare Pages checks — passed before merge.

## Production proof

- Canonical refresh: GitHub Actions run 34620928988 — success on Ubuntu in 5m7s: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/34620928988
- The run completed the full validated build, admin occupancy reconciliation, strict link audit, refreshed-inventory validation, approved-output commit, and push to `main`.
- Publication result: commit `256f8895c3e0b852859ec713c238db34056445cf` on `main`.
- Validated inventory in the run: 23 public sessions and 28 admin sessions. Selector totals included BLS 4,101 offers, Heartsaver 7,822, ACLS 9, and PALS 7.
- GitHub Pages: run 34621420567 — build and deploy succeeded: https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/34621420567
- Post-deploy route checks all returned HTTP 200 and the expected canonical: `/ACLS.html` -> `/acls.html`, `/BLS.html` -> `/bls.html`, `/HEARTSAVER.html` -> `/heartsaver.html`, `/PALS.html` -> `/pals.html`, `/Earl/` -> `/earl/`.

## Persistent-system proof contract

- Expected outcome: scheduled or forced public refreshes build in a case-sensitive checkout, validate, publish only approved output, and preserve legacy case-distinct URLs.
- Success evidence: refresh run 34620928988, publication commit `256f8895c3e`, Pages run 34621420567, and live HTTP/canonical checks above.
- Expected cadence: workflow schedule at minutes 13 and 43 each hour, plus eligible pushes and manual dispatch.
- Last successful end-to-end proof: 2026-09-11 between 16:15Z and 16:22Z, evidenced by the two successful workflow runs and live route checks.
- Failure/staleness condition: a failed refresh/Pages run, a source-integrity CI failure, a new or missing allowlisted collision, or a legacy URL/canonical mismatch.
- Observer: GitHub Actions scheduled refresh, source-integrity checks on pushes/PRs, and GitHub Pages deployment status.
- Observer health: the merged workflow, source-integrity checks, refresh run, and Pages deployment all reported success in this round.
- Recovery path: inspect the failing Actions step and artifacts; for collision drift, run `python scripts/check_case_insensitive_paths.py`; for publication failure, preserve the failed run and rebuild from current `main` rather than replaying stale output.
- Escalation boundary: credentials, GitHub service incidents, or business decisions about retiring a legacy URL require repository-owner action; repository-side deterministic failures can be handled in a follow-up Codex issue.

## Known unrelated conditions and remaining risk

- Windows worktrees still report one side of some intentional aliases as modified because NTFS is case-insensitive. Those files were not staged or committed in either round.
- GitHub Actions emitted a Node.js 20 deprecation warning for current action versions forced onto Node 24. It did not affect this run and is unrelated to issue #167.
- Cloudflare issue #164 remains separate as required by the issue.

## Recommended next action

ChatGPT should acknowledge this receipt by renaming it to `Codex_Read_Issue167_R2.md`, then close issue #167 with links to PR #185, refresh run 34620928988, Pages run 34621420567, and publication commit `256f8895c3e`.

User/account-level action required: none for the repair itself. Closing the GitHub issue is the remaining supervisory action.
