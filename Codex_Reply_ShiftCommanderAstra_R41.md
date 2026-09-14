# ShiftCommander Astra R41: prerequisite assessment

Assignment: [Brian910cpr/910cpr-class-landers#214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214), dispatch `SHIFTCOMMANDER_ASTRA_20260913_R1`.
Timestamp: 2026-09-14T02:09:07-04:00, America/New_York.
Work-item state: BLOCKED for release. Persistent-system evidence: BUILT with retained local synthetic validation; complete operational proof, monitoring and health remain unverified.

## Work performed and repository state

Read the complete issue body and all 85 pre-pickup comments, pinned original dispatch, original/current courier `AGENTS.md`, `CODEX_HANDOFF_PROTOCOL.md`, `LANDERWARE_PROOF_AND_HEALTH_STANDARD.md`, `docs/CODEX_INSTRUCTIONS.md`, and concurrency issue #116. The original dirty courier branch lacks the protocol; fetched main supplied it. Read target `AGENTS.md`, `docs/PROJECT_BOUNDARIES.md`, `docs/CONFIRMED_SCHEDULING_RULES.md`, `RULES.md`, `DATA_CONTRACT.md`, R8/R9 release records, and R2-lineage `docs/MIGRATION_PROGRESS_LOG.md` / `docs/SHIFT_OVERLAY_CONTRACT.md`. Historical migration status is not current hosting evidence.

- [R41 pickup acknowledgement](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5659744650).
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r41`; branch `codex/issue-214-shiftcommander-receipt-r41`; base commit `387be9c0c16a6d6b8184fed30b59a17a5eec5bbf`. Root-only sparse checkout initialized cleanly; no prior Reply/Read R41 collision was found in fetched history or the new root.
- Read-only target assessment: `E:\GitHub\shiftcommander_v2_codex_issue214_r9`, branch `codex/issue-214-release-gate-verification-r9`, commit `16d0ace259b485a7585decbef24c74e94bd69f5c`.
- Unchanged application: `ba0365a250d18297a262b96ab7f15cf3fe6f1780`, branch `codex/issue-214-private-boundary-r8`, [ShiftCommander PR #10](https://github.com/Brian910cpr/shiftcommander_v2/pull/10). Fresh GitHub readback: OPEN, draft, exactly three original files, `statusCheckRollup=[]`. Remote main remains `67a3f88f1b54fa2ffbd285df7df969cea7837616`; refs do not establish hosting health.

The [R40 acknowledgement](https://github.com/Brian910cpr/910cpr-class-landers/blob/54075ee8ace2bb2c0e8e768a087ce19c35a52f3d/Codex_Read_ShiftCommanderAstra_R40.md) retains the no-merge/no-release gate and says no identical implementation round is justified without changed prerequisites or an independently reproduced defect. This assessment found neither. Execution stopped at those prerequisites; no speculative application change, failed-auth retry, activation, merge or deployment occurred.

## Exact blockers and next evidence

| Blocker | Required next action |
|---|---|
| Cloudflare serving metadata is unverified after the prior Pages metadata HTTP 401. | Account operator restores minimum Pages project/deployment, Worker routing and D1-binding metadata reads, or supplies an approved sanitized export. Verify actual serving paths before staging. A bridge credential and unrelated Sites/LanderWare delivery do not prove those permissions. No new access was supplied in the issue; the failing request was not repeated. |
| Approved persistent operational authentication is missing. | Establish approved persistent filesystem and exact `SC_AUTH_DB_PATH`, schema v2 readiness, private real member/named supervisor accounts, signing configuration and deployed/inherited settings. Do not activate schema v1 or restore revoked sessions from a stale backup. |
| Current authoritative ADR staffing inputs remain unapproved/unreconciled. | Approve current roster/certifications, unit-specific `qualOp`, explicit availability consent, demand and calendar provenance. Preserve ADR Google Calendar published-staffing authority. Prior evidence of 170 shifts ending August 10 is historical, not a current schedule read. |

R37's issue comment reports a bridge credential exposed in its earlier diagnostic output. R40's acknowledgement confirms containment/rotation remains unverified. Account operator must handle revocation/rotation privately wherever the credential is accepted and verify the old credential no longer works. No credential value was retrieved, repeated, used or changed in this assessment.

After prerequisite evidence arrives, coordinate real scoped clients and authentication; availability -> legal resolver -> supervisor review -> publication; member/mobile/wallboard agreement; approved-data legality, locks, overtime, swaps, duplicates and DST scenarios; hosted recovery/observer proof; secure Windows startup; and phone/SMS/email identity, intake, deduplication and delivery handling. Blank is not consent; required unfilled legal seats remain visibly OPEN. Full original release scope remains outstanding.

## Validation and usable evidence

Fresh local AST parsing/in-memory compilation passed for `server.py`, `engine/auth_store.py`, and `engine/live_state_store.py`. PowerShell parser validation passed for `E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1`. No bytecode was written. The target is clean; `git diff --name-only ba0365a250d18297a262b96ab7f15cf3fe6f1780 HEAD` returns only the existing `docs/RELEASE_VERIFICATION_ISSUE214_R9.md`.

Retained local log `E:\GitHub\shiftcommander_v2_codex_issue214_r9\debug\verification_r9\combined_final.log` was read:

```text
Ran 160 tests in 189.801s
OK
FINAL: tests=160 failures=0 errors=0 skips=0
```

These are prior R9 local synthetic tests, not a new R41 run. The unchanged suite was not rerun. No new browser, CI, staging or production proof is claimed. Receipt validation covers required fields, Markdown fences, whitespace and explicit one-file staged/base-to-head scope. The initial read from the old courier checkout could not find the protocol; it was read from fetched main. Large diagnostic reads were split to read the issue fully; neither was an application-test failure.

Review sources remain usable: [R9 verification/reproduction report](https://github.com/Brian910cpr/shiftcommander_v2/blob/16d0ace259b485a7585decbef24c74e94bd69f5c/docs/RELEASE_VERIFICATION_ISSUE214_R9.md), [R8 checklist](https://github.com/Brian910cpr/shiftcommander_v2/blob/ba0365a250d18297a262b96ab7f15cf3fe6f1780/docs/RELEASE_CHECKLIST_ISSUE214_R8.md), `286876e7d506bd127e14c2852f65c827815a8fa7:docs/RELEASE_EVIDENCE_ISSUE214_R2.json` (`read_only_checks`), and `5e81303e8f2cc306251ae61bd8566c3763548b83:docs/RELEASE_CHECKLIST_ISSUE214_R6.md` (schema/recovery). PR #10's exact review files are `server.py`, `tests/smoke/test_private_serving_boundary.py`, and `docs/RELEASE_CHECKLIST_ISSUE214_R8.md`.

## Runtime, preservation and independent backend queue

Matching active-thread local `turn_context` reports `model=gpt-6-astra` at `2026-09-14T06:04:37.581Z`; session metadata and `codex --version` report CLI `0.153.4`. Only sanitized model/version fields were returned. This is local runtime evidence, not provider attestation. [Official model documentation](https://learn.chatgpt.com/docs/models) was fetched; documentation/configuration is not runtime proof.

Existing R2 `scripts/Start-AstraReview.ps1 -RepoPath E:/GitHub/shiftcommander_v2_codex_issue214_r9 -CheckOnly` returned `can_launch=false` at `2026-09-14T02:07:35.1971847-04:00`, dispatcher lock held/inaccessible. This worker continued without another launch or lock/lease/default/timer changes. This launcher starts a review worker, not the application. A verified normal operational URL and secure application startup remain blocked on approved configuration.

Both original dirty checkouts retain their initial status: courier `docs/Earl/index.html`, Python caches, `ops/handoff/codex_heartbeat.json`, and `supabase/.temp/`; ShiftCommander calendar mirror plus untracked availability backup/slot generator/data/tests. Four unpublished target commits remain (`3287eb4`, `9a49b9e`, `69bc1fb`, `55d6a05`), divergence `0 4`. No unfinished merge/rebase/cherry-pick/revert markers were found in either original checkout or R9. All prior worktrees and receipt history were preserved. No generator or cleanup ran.

Fresh open-CODEX sweep and current dependency readback found no newly eligible narrow backend repair:

- #227 has new [stabilization guidance](https://github.com/Brian910cpr/910cpr-class-landers/issues/227#issuecomment-5659631006): its first Sites slice is accepted only as a deployed preview; September 11 schedule data is stale/non-authoritative while #140 blocks publication. Backend freshness/auth/reconciliation take priority; customer SEO/features are deferred. Preserve owner-session authority and existing work.
- #226 explicitly has active canonical class/person/document intake implementation. Remaining #219 instructor identity/assignment scope overlaps that work; owner-only controls must not be given to instructors via owner credentials.
- #215 reports private owner access delivered through PR #225. Preserve that delivery. Legacy Worker/finance connections, instructor identities, static-data privacy and monitoring remain separate requirements; its success does not clear ShiftCommander gates.
- #216 still needs current private finance inputs and complete operational proof; its historical shared-key requirement is superseded by #215's private owner access.
- #223's 19-class/13-registration reconciliation is already returned. Its authoritative source end-time correction and owner/API/UI proof remain distinct; no duplicate import was performed.
- #140 retains the credential-parity/account gate; latest read recurrence names scheduled run `34796567750` and HTTP 401. Preserve fail-closed publishing; no credential workaround or unchanged failing retry.

These were eligibility reads, not secondary implementations. No secondary issue was modified or completed work duplicated.

## Proof contract and disposition

Expected outcome: real authenticated availability survives restart and produces legal reviewed publication consistently across all views. Success evidence must connect the same saved revision, persistence readback, resolver explanation, review/publication and rendered views. Last complete operational proof: not established. Expected cadence includes Wednesday 23:59 publication; freshness windows, independent observer, observer heartbeat and escalation delivery remain unproven. Failures include stale inputs, unreadable/schema-invalid storage, lost saves, unauthorized/illegal assignments, inconsistent views and missed publication. Recovery follows R6/R9 credential-only recovery into a distinct store, password/audit reconciliation and staging proof; unsetting `SC_AUTH_DB_PATH` is not an assumed safe rollback. Brian must not be the routine detector.

Exact changed file: `Codex_Reply_ShiftCommanderAstra_R41.md` only. Assessment and syntax validation were local; GitHub issue/ref/receipt operations were remote. This receipt is delivered on the named courier branch; its final commit SHA and remote byte verification are posted on #214 after push to avoid a self-referential SHA. No application merge, deployment, production write, calendar-authority change or member communication occurred.

Next ChatGPT action: review this receipt; retain #214 and the draft stack open/unmerged; obtain the three exact provider/private-configuration/current-input prerequisites through the existing handshake and coordinate private handling of R37's credential incident. Account/operator action is required. Then dispatch scoped staging/client/recovery work. This mandatory blocked receipt does not request another identical implementation round; useful continuation requires changed prerequisite evidence or a reproduced independent defect. Dispatcher policy was not changed.
