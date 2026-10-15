# Issue #325 dispatch receipt

- Timestamp: 2026-10-14 UTC
- Work-item state: IN_PROGRESS; existing PR #324 reused. Issue remains open.
- Local branch: codex/issue325-lifecycle-20261014
- Push destination: fix/nhcso-ux-latency-20261001 (existing PR #324)
- Substantive commit: 522a036c2e424d31d798b5708f8e1ff2f55ebe6b

## Work and findings
Read the full originating issue (no owner comments), repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos, proof standard, and owner concurrency issue #116. Acknowledged execution on #325 before editing. Preserved the active E:/GitHub/910cpr-class-landers checkout and all its dirty files. Its fetch failed with `fatal: bad object refs/remotes/origin/codex/group-training-experience`; no refs or useful work were deleted. Used a separate real sparse clone at E:/GitHub/910cpr-issue325-20261014 based on existing PR #324.

Changed Unlock label and required a deterministic seven-character class-specific acknowledgement. Cancellation/wrong code leaves the lock intact. Finalized status, backend override gates, paperwork restrictions, and Training Site warnings remain intact. Code is an acknowledgement, not an authorization credential. Existing PR #324 already supplies simple Finalize confirmation and exact backend class confirmation; updated its stale test accordingly.

## Exact intended files
- docs/corp/nhcso/index.html
- tests/nhcso_unlock_confirmation.test.cjs
- tests/test_nhcso_roster_workflow.py
- Codex_Reply_Issue325_20261014_Unlock_R1.md

## Validation
- node --test tests/nhcso_unlock_confirmation.test.cjs: 3 passed.
- python -m unittest tests.test_nhcso_roster_workflow: 8 passed after correcting stale full-number assertion.
- Inline JavaScript node --check: passed.
- Intended-file git diff --check: passed.
- Four unrelated tracked HTML changes appeared during validation: docs/ACLS.html, docs/BLS.html, docs/HEARTSAVER.html, docs/PALS.html. They are intentionally unstaged and excluded; no generator was explicitly run. No broad rebuild or cleanup.

## Remaining scope and exact gates
This is a partial UI slice, not completion of #325. Lifecycle names/symbols in My Classes and class banner and needs-something progression still require implementation. list_classes currently selects only class metadata, without roster/eCard/document evidence. Do not derive completion from dates or fetch every class separately. Next implement an authenticated bounded batch projection using existing nhcso_classes/nhcso_students/nhcso_documents truth, preserving actual finalization readiness and unknown evidence. Prove it with fixtures and browser checks before release. Post-class roster reconciliation truth must be investigated rather than guessed. History/backfill stays with #327. No account-level decision is needed for offline backend work; authenticated release proof remains unavailable in this dispatch.

Evidence state: BUILT for this narrow unlock slice only. No real end-to-end finalized correction cycle or monitoring proof obtained. Success must be checked at authenticated class -> unlock -> local save -> reload with finalized status and warning retained; failed/stale class loads must not masquerade as current lifecycle evidence. Observer health is unproven; no HEALTHY claim.

Queue scanned using open [CODEX] issues. Existing #371/#372 remains the sole deep stream. No unrelated implementation started and no assignments replaced. #372 untouched, unmerged, undeployed. No migration/function deployment, production merge or production verification. Changes validated locally only; receipt and intended files pushed to existing PR branch. Supervising process should continue #325 backend summary/progression on #324 and retain release gates, rather than treat this receipt as issue completion.
