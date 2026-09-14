# ShiftCommander Astra R40: release prerequisite assessment

Assignment: [Brian910cpr/910cpr-class-landers#214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214), dispatch `SHIFTCOMMANDER_ASTRA_20260913_R1`.
Assessment timestamp: 2026-09-14T01:46:36-04:00, America/New_York.
Work-item state: BLOCKED for release. Persistent-system evidence: BUILT with retained local synthetic validation. Complete operational proof, monitoring and health remain unverified.

## Work performed and exact repository state

- Read the full issue body and all 83 pre-pickup comments, pinned original dispatch, original/fetched courier `AGENTS.md`, `CODEX_HANDOFF_PROTOCOL.md`, `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md`, `docs/CODEX_INSTRUCTIONS.md` and concurrency issue #116. The protocol is absent from the original dirty branch; fetched main supplies it. Read target `AGENTS.md`, project boundaries, confirmed scheduling rules, `RULES.md`, `DATA_CONTRACT.md`, consolidation-lineage migration/overlay documents, and R8/R9 release records. Historical migration claims do not establish current serving authority.
- [R40 pickup acknowledgement](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5659578824).
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r40`; branch `codex/issue-214-shiftcommander-receipt-r40`; base commit `bd7db4fe9ab105b52d94487cd248ea772f4623f0`. Root-only sparse initialization completed cleanly. No prior Reply/Read R40 collision was found in fetched history or the root.
- Target assessment was read-only in `E:\GitHub\shiftcommander_v2_codex_issue214_r9`, branch `codex/issue-214-release-gate-verification-r9`, commit `16d0ace259b485a7585decbef24c74e94bd69f5c`.
- Application remains `ba0365a250d18297a262b96ab7f15cf3fe6f1780`, branch `codex/issue-214-private-boundary-r8`, [ShiftCommander draft PR #10](https://github.com/Brian910cpr/shiftcommander_v2/pull/10). Fresh GitHub readback confirms OPEN/draft, its original three files and `statusCheckRollup=[]`. Serving PRs #5-#10 remain draft/open; migration PRs #3/#4 remain open. Target remote main remains `67a3f88f1b54fa2ffbd285df7df969cea7837616`; repository refs are not hosting-health evidence.

Reviewed the opt-in Flask authentication boundary, reconciled local/remote state, and refreshed release prerequisites and the independent backend queue. No new clearing prerequisite or reproduced independent defect was established. The [reviewed R8 hold](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5654327541) remains in force. No speculative application change, unchanged failing account-auth retry, activation, merge or deployment occurred.

## Exact blockers and next evidence required

| Blocker | Required action/evidence |
|---|---|
| Cloudflare serving metadata remains unverified after the prior Pages metadata HTTP 401. | Account operator restores minimum Pages project/deployment, Worker routing and D1 binding metadata reads, or supplies an approved sanitized export. Verify actual serving paths before staging. A bridge token and unrelated LanderWare/Sites delivery do not prove these permissions. |
| Approved operational persistent real-auth configuration is missing. | Establish the approved persistent filesystem and exact `SC_AUTH_DB_PATH`, schema v2 readiness, private real member/named supervisor accounts, signing configuration and inherited/deployed settings. Do not activate against schema v1 or restore old sessions from a stale backup. |
| Current authoritative ADR staffing inputs remain unapproved/unreconciled. | Approve current roster/certifications, unit-specific `qualOp`, explicit availability consent, staffing demand and calendar provenance. Preserve ADR Google Calendar published-staffing authority. The prior 170-shift observation ending August 10 is historical, not a current schedule read. |

After these prerequisites, continue the original release scope: scoped clients and real authentication; availability -> legal resolver -> supervisor review -> publication; member/mobile/wallboard agreement; approved-data legality, locks, overtime, swaps and DST scenarios; hosted recovery and observer proof; secure Windows startup; phone/SMS/email intake, identity, deduplication and delivery handling. Blank is not availability consent; required legal shortages remain visibly OPEN. No staffing policy or calendar authority changed.

R37's issue comment reports a bridge credential exposed in that earlier session's diagnostic output. No containment/rotation proof has been supplied. Private operator review and coordinated rotation remain outstanding. No credential value was repeated, used or changed in R40.

## Validation and reviewable evidence

Fresh local AST parsing/in-memory compilation passed for `server.py`, `engine/auth_store.py`, and `engine/live_state_store.py`; PowerShell parser validation passed for `E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1`. No bytecode was generated. Target diff from the application commit contains only existing `docs/RELEASE_VERIFICATION_ISSUE214_R9.md`; target worktree is clean.

Retained `E:\GitHub\shiftcommander_v2_codex_issue214_r9\debug\verification_r9\combined_final.log` was read, with exact result:

```text
Ran 160 tests in 189.801s
OK
FINAL: tests=160 failures=0 errors=0 skips=0
```

These are prior local synthetic tests, not a new R40 run. No changed application or new failure justified repeating the suite. No new browser, staging, CI or production proof is claimed. One initial read looked for the overlay document on the serving lineage; it was then read from its existing R2/consolidation lineage. This was a document-location error, not a test failure.

Exact review sources: [R9 verification and reproduction commands](https://github.com/Brian910cpr/shiftcommander_v2/blob/16d0ace259b485a7585decbef24c74e94bd69f5c/docs/RELEASE_VERIFICATION_ISSUE214_R9.md); [R8 release checklist](https://github.com/Brian910cpr/shiftcommander_v2/blob/ba0365a250d18297a262b96ab7f15cf3fe6f1780/docs/RELEASE_CHECKLIST_ISSUE214_R8.md); `286876e7d506bd127e14c2852f65c827815a8fa7:docs/RELEASE_EVIDENCE_ISSUE214_R2.json` (`read_only_checks`); and `5e81303e8f2cc306251ae61bd8566c3763548b83:docs/RELEASE_CHECKLIST_ISSUE214_R6.md` (schema/recovery). PR #10's exact three files are `server.py`, `tests/smoke/test_private_serving_boundary.py`, and `docs/RELEASE_CHECKLIST_ISSUE214_R8.md`. Existing candidate, tests, reports and recovery guidance remain usable.

## Runtime and preservation

Matching active-thread local `turn_context` reports `model=gpt-6-astra` at `2026-09-14T05:42:30.291Z`; session metadata reports CLI `0.153.4`. Only these sanitized fields were extracted. This is local runtime evidence, not provider-side attestation. [Official CLI documentation](https://learn.chatgpt.com/docs/developer-commands?surface=cli) was fetched; documentation/configuration alone is not runtime proof.

The existing R2 `scripts/Start-AstraReview.ps1 -RepoPath E:/GitHub/shiftcommander_v2_codex_issue214_r9 -CheckOnly` returned `can_launch=false` at `2026-09-14T01:44:42.0570909-04:00`, dispatcher lock held/inaccessible. This active worker continued; no competing worker, lock/lease/default change or timer was created. That launcher starts a review worker, not the application. No verified normal operational application URL/start command is claimed.

Both original dirty checkouts remain unchanged: courier `docs/Earl/index.html`, Python caches, `ops/handoff/codex_heartbeat.json` and `supabase/.temp/`; ShiftCommander calendar mirror, untracked availability backup/slot generator/data/tests. Four unpublished target commits remain on `codex/base44-worker-consolidation`: `3287eb4`, `9a49b9e`, `69bc1fb`, `55d6a05`; divergence remains `0 4`. No unfinished merge/rebase/cherry-pick/revert was found in either original checkout or R9. All prior worktrees/receipts were left intact. No cleanup or generator ran.

## Independent backend queue and disposition

Fresh sweep of all open CODEX issues found no newly eligible narrow backend repair. #226 explicitly has active canonical class/person/document intake implementation. #227 has an active Sites delivery workstream and requires scheduler lineage before scheduler edits. Preserve both. #215 reports private owner access delivered through PR #225; its remaining legacy Worker/finance connections, instructor identities, static-data privacy and monitoring are separate requirements. #216 needs private finance inputs and operational proof; its old shared-key requirement is superseded by #215's owner-access delivery. #219's remaining individual instructor/assignment scope overlaps the active class-record work and is not an isolated repair. #223's reconciliation is already returned; its source end-time correction and owner/API/UI proof are distinct. #140 retains the account/parity gate and HTTP 401 recurrence at scheduled run `34796567750`; preserve fail-closed publishing. No secondary issue was implemented or modified, and no completed import or active implementation was duplicated.

Expected persistent outcome: real authenticated availability survives restart and produces a legal reviewed publication consistently across all views. Success evidence must link saved revision, readback, resolver explanations, review/publication and rendered views. Last complete operational proof: not established. Expected cadence includes Wednesday 23:59 publication. Source freshness windows, independent observer, observer heartbeat and escalation delivery remain unproven. Failures include stale inputs, unavailable/schema-invalid storage, lost saves, unauthorized/illegal assignments, inconsistent views and missed publication. Follow R6/R9 credential-only recovery to a distinct store, reconcile password/audit history and prove staging; unsetting `SC_AUTH_DB_PATH` is not an assumed safe rollback. Brian must not be the routine detector.

Exact changed file: `Codex_Reply_ShiftCommanderAstra_R40.md` only. Assessment/syntax validation were local; GitHub issue/ref/receipt operations were remote. This receipt is committed/pushed separately from the unchanged application; final commit SHA and remote content verification are posted on #214 after push, avoiding a self-referential SHA. No application merge or deployment occurred.

Next ChatGPT action: review this receipt, keep #214 and its draft stack open/unmerged, obtain the three exact metadata/private-configuration/current-input prerequisites through the existing handshake, and retain private operator handling of the R37 credential incident. Then dispatch coordinated staging/client/recovery work. Account/operator action is required. This mandatory receipt is not a request for another identical implementation dispatch: meaningful continuation needs changed prerequisite evidence or a reproduced independent defect. Dispatcher policy was not changed.
