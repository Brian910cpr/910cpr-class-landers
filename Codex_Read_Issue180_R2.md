# Codex Reply: Issue 180, Round 2

- Timestamp: 2026-09-11T21:06:59-04:00
- Branch: `codex/issue180-durable-recovery-r2`
- Substantive commit: `e2e62e534f7afbc476b4a4087833fce8c98c363a`
- Pull request: #203 (targets the existing #181 branch)
- Work-item state: `PR_OPEN`; production proof is `BLOCKED`
- Persistent-system evidence state: `CONNECTED`

## Findings

Fact: GitHub `workflow_dispatch` cannot start this new workflow while the workflow exists only on a non-default branch. The earlier instruction to dispatch the draft-branch workflow was therefore not executable.

Fact: the first real immutable Google Drive archive and reconciliation receipt have not been produced. The process must not be described as `PROVEN`, `MONITORED`, or `HEALTHY`.

Fact: issue #168 records a separate GitHub scheduled-event delivery incident. A GitHub cron alone is not sufficient observer evidence for `MONITORED`.

## Work performed

- Removed the premature daily cron trigger, leaving the first-proof workflow manual-only.
- Documented the default-branch dispatch requirement and safe rollout order.
- Required a verified manual archive and reconciliation receipt before enabling cadence.
- Documented the need for an independent stale-run observer before a `MONITORED` claim.
- Added a regression test that fails if a schedule is enabled before the first-proof gate is deliberately changed.

## Exact files changed

- `.github/workflows/google-durable-snapshot.yml`
- `docs/operations/google-durable-recovery.md`
- `tests/test_export_google_durable_snapshot.py`
- `Codex_Reply_Issue180_R2.md` (this receipt; communication-only follow-up commit)

## Tests and checks

- `python -m unittest tests.test_export_google_durable_snapshot`: 6 tests passed.
- `python -m py_compile scripts/export_google_durable_snapshot.py`: passed.
- PyYAML safe-load of `.github/workflows/google-durable-snapshot.yml`: passed.
- `git diff --check`: passed for intended changes.

## Known unrelated changes/failures

- The isolated worktree showed modifications to `docs/Earl/index.html` and `docs/PALS.html` immediately after checkout. They were not staged, committed, or pushed.
- PR #181's Cloudflare Pages check is failing; the prior handoff identifies this as the existing incident #164, not an Issue 180 implementation failure.

## Deployment and proof status

- Local validation: passed.
- Substantive branch pushed: yes.
- Follow-up PR #203 opened: yes.
- Merged to the #181 branch: no.
- Merged to default branch: no.
- Workflow dispatched: no; it is unavailable for dispatch until merged to the default branch.
- Production Google Drive archive/receipt: none verified.
- Last successful end-to-end proof: none.

## Exact blocker and next action

Account-level action is required:

1. Configure GitHub Actions secret `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` without placing its value in Git, issues, or chat.
2. Share the Raw Snapshots and Reconciliation Reports Drive folders with that service-account email as Editor.

Repository/supervisor action after that:

1. Review and merge PR #203 into the #181 branch.
2. Merge the resulting manual-only workflow to the default branch when the credential/folder gate is confirmed.
3. Manually dispatch `Google durable snapshot`.
4. Verify the archive bytes/checksums and reconciliation receipt in Drive; record the run and Drive file evidence.
5. Only then promote the process to `PROVEN`; add daily cadence separately and resolve the independent observer dependency before claiming `MONITORED`.

No customer, schedule, price, payment, registration, production database, or Google Drive data was mutated in this round.
