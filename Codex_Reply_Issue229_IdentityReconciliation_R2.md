# Issue #229 — identity reconciliation R2

- Assignment: `Brian910cpr/910cpr-class-landers#229`, September 14 11:26:30Z owner dispatch; sequential independent backend continuation after blocked #214 R55.
- Timestamp: `2026-09-14T08:21:32-04:00`, America/New_York.
- State: **PR_OPEN**; bounded identity audit **validated locally**. Full archive/editorial delivery **IN_PROGRESS**, publication gated.
- Branch: `codex/issue-229-identity-reconciliation-r2`.
- Worktree: `E:\GitHub\910cpr-class-landers_codex_issue229_identity_r2`.
- Substantive commit: `a51bf3236e205d7e5651716586751f26f07f5bc3`.
- [Draft PR #231](https://github.com/Brian910cpr/910cpr-class-landers/pull/231), stacked on source-recovery PR #230 at `844218802483e75c177916ea7165577e8a01ce58`. No merge.
- [Full report](https://github.com/Brian910cpr/910cpr-class-landers/blob/a51bf3236e205d7e5651716586751f26f07f5bc3/data/audit/issue229_identity_reconciliation_r2.md) and [aggregate JSON](https://github.com/Brian910cpr/910cpr-class-landers/blob/a51bf3236e205d7e5651716586751f26f07f5bc3/data/audit/issue229_identity_reconciliation_r2.json).

## Work and findings

Read the full #229 issue/comments, current AGENTS.md, source-recovery report/code/tests, #228 and the relevant #140/#227 gates. Reused the existing audit rather than creating a second catalog or reinstalling an old public generator.

Added `--identity-only` to `scripts/audit_historical_source_recovery.py`. It reconciles historical/current Registration Link identities, compares exact source facts, exposes invalid/ambiguous identities, inventories safe status labels, and inspects enrollment anchors in seven orphan historical pages. Reports contain aggregate counts and path/content digests, not source records or private labels. Publication authorization stays null.

Exact facts from pinned inputs:

- 26,165 historical rows; 19,708 current archive rows; 19,655 unique shared registration pairs; 6,510 historical registration IDs absent from current; 53 current-only IDs.
- Historical exclusive dispositions: 19,438 shared pairs with valid timing and differing source fields; 217 shared pairs with invalid timing; 6,510 absent identities. These sum to 26,165. No ambiguous identity appeared in these actual snapshots; tests cover ambiguity.
- Shared-pair differences: 21 starts, 14 ends, **22 distinct changed-time pairs**, 382 locations, and 19,655 exact course-label strings. Label differences are not proof every course changed and do not establish Course Master equivalence. There are 19,034 valid pairs differing only in exact course label.
- All current source rows say `session_status=active`; that does not establish historical completion/cancellation. Do not infer that every elapsed row was taught or is still bookable.
- Each of seven orphan HTML pages contains one registration identity, and all seven identities are absent from both sources. They remain unresolved; no invented source row, public alias or historical 200 shell was created.

The full report supplies exact input commits/blobs. JSON review fields: `sources[]`, `exclusive_historical_dispositions`, `overlapping_changed_fields_in_unique_pairs`, `overlapping_unique_pair_flags`, `unique_pair_difference_sets`, `current_source_status_labels`, `orphan_dispositions`, `orphans_by_path_sha256`, and `publication_authorized_count`.

## Exact changed files

1. `scripts/audit_historical_source_recovery.py` — additive identity-only mode; original six-source mode retained.
2. `tests/test_audit_historical_source_recovery.py` — eleven new cases plus the existing eight cases.
3. `data/audit/issue229_identity_reconciliation_r2.json` — aggregate immutable-source evidence.
4. `data/audit/issue229_identity_reconciliation_r2.md` — complete report, commands, limits and next action.
5. `Codex_Reply_Issue229_IdentityReconciliation_R2.md` — this unique root receipt, committed separately after the substantive SHA above.

## Validation

All data processing and checks were local; only GitHub issue/PR/push actions were remote. Existing Git JSON/HTML blobs were read; no live operational data, calendar, database or spreadsheet was fetched/modified.

```powershell
python -B scripts/audit_historical_source_recovery.py --identity-only --current-ref abc7e9b1dd2d03039437721f80fe294190060c8a --as-of 2026-09-14T00:00:00-04:00 --output data/audit/issue229_identity_reconciliation_r2.json
python -B -m unittest discover -s tests -p test_audit_historical_source_recovery.py -v
```

```text
Ran 19 tests in 0.004s
OK
SYNTAX: 2 Python files passed
JSON: totals, pair partitions, orphan keys and null publication gate passed
```

The exact audit command/output scope was reported before each run: one JSON under `data/audit/`, zero public outputs. After a diagnostic extension, the second run updated only that same file. No unexpected generator scope. AST/in-memory compile produced no bytecode; staged/file-scope and whitespace checks passed. The report discloses two corrected exploratory command errors (literal rg globs and JSON list/object assumption); actual audit runs and final tests passed. No unrelated suite/build was run; no CI, staging or production proof is inferred from local checks.

## Delivery, preservation and blockers

Substantive commit pushed and draft PR created. This receipt is pushed next; final issue/UI return supplies its tip and complete-file readback verification. No application merge, production deployment, public HTML generation, sitemap generation, GSC submission, authority change, credential retry or communication to members/customers. Full-corpus restoration remains the target; no numerical cap is introduced. R1's candidate count is not a final publication count; newly generated/deployed public pages in R2: **0**.

Original dirty courier/ShiftCommander checkouts and four unpublished target commits remain untouched. PR #230 and prior receipts are preserved. New worktree setup was inspected while `.git`-only/empty-index and then initialized from its pinned base; no prior files were removed. Only the five intended paths are committed. Diagnostic caches are outside the repository; no new runtime junk or private source exports are intentionally left untracked here. No Codex_Read marker or retired mutable mailbox was used.

Persistent archive evidence state: **BUILT** audit tooling only. No real full-corpus generation -> validation -> publication -> refresh/indexing cycle has been proven by this increment. Last operational end-to-end success, automatic refresh cadence, whole-workflow observer/heartbeat and indexing health remain unverified. Invalid identities/facts, leaked private content, expired booking claims, stale current options and sitemap/link drift are release failure conditions; monitoring cannot rely on Brian remembering to inspect them.

Next ChatGPT/implementation action: review PR #231's exact four-file increment against PR #230; adjudicate the 22 changed-time pairs, 382 location changes, invalid intervals and seven orphan identities against private authoritative evidence, then reconcile course/status mapping and construct the allowlisted historical projection in the existing retained-page generator. R1 Client/public-location/privacy gates remain. Do not infer completion or cancellation from `active`/elapsed/enrollment. Public current options must reuse #228; #140 requires exact credential parity and both-publisher occupancy/freshness proof. Report the exact full eligible sitewide generation scope for approval before running it. Owner/account action is required where private provenance or #140 credentials must be resolved; no credential values belong in GitHub. Keep #229 open for the full archive, editorial modules, validators, sitemaps, production and indexing proof.

ShiftCommander #214 remains independently **BLOCKED** at approved persistent real auth, current ADR staffing inputs and private R37/R47 incident disposition. Its required [R55 receipt](https://github.com/Brian910cpr/910cpr-class-landers/blob/0240381dc7acc9f2d45f27f3f5eecfb4cf21c6a6/Codex_Reply_ShiftCommanderAstra_R55.md) was already pushed and all 12,334 committed bytes verified before this continuation. This audit clears none of those release gates; no competing worker or lock/default change occurred.
