# Codex reply: ShiftCommander Astra R7

Assignment: [Brian910cpr/910cpr-class-landers#214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214), dispatch `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing R6 as R7.
Timestamp: 2026-09-13T11:10:00-04:00 (America/New_York).
State: **PR_OPEN checkpoint; overall release BLOCKED**.
Persistent-system evidence: **BUILT**, with local synthetic request/process evidence. No operational PROVEN, MONITORED or HEALTHY claim.

## Exact implementation handoff

- Target repository: `Brian910cpr/shiftcommander_v2`.
- Worktree: `E:\GitHub\shiftcommander_v2_codex_issue214_r7`.
- Branch: `codex/issue-214-password-gate-r7`.
- Commit: [`b0f4978f24ff309918ad0eb64389fa95d948b1b0`](https://github.com/Brian910cpr/shiftcommander_v2/commit/b0f4978f24ff309918ad0eb64389fa95d948b1b0), pushed.
- Draft PR: [ShiftCommander #9](https://github.com/Brian910cpr/shiftcommander_v2/pull/9), OPEN and draft on GitHub readback, head SHA verified. Base is R6 `codex/issue-214-auth-audit-r6` at `5e81303e8f2cc306251ae61bd8566c3763548b83`, draft PR #8.
- Primary report: [`docs/RELEASE_CHECKLIST_ISSUE214_R7.md`](https://github.com/Brian910cpr/shiftcommander_v2/blob/b0f4978f24ff309918ad0eb64389fa95d948b1b0/docs/RELEASE_CHECKLIST_ISSUE214_R7.md). Read this full report for exact validation commands, field meanings, scope limits, recovery references and all release requirements.
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r7`.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r7`, based on `8808884a23e4da2ce055b4da6a9002a6ea17c39c`. Its only intended committed file is this root receipt. The final courier commit is reported on #214 and in the dispatch UI after push/readback.

The full issue/comments, linked dispatch, both repositories' AGENTS, `CODEX_HANDOFF_PROTOCOL.md`, proof standard, target project boundaries/confirmed staffing rules/RULES/DATA_CONTRACT and migration/overlay contracts were read before implementation. Local `CODEX_HANDOFF_PROTOCOL.md` was absent in the original stale courier branch; the protocol was read from fetched `origin/main`, which is also the new courier worktree's base. Issue #116's single active worker constraint remains honored.

## Finding and work performed

R6 stored `must_change_password` but never enforced it. Two tests first reproduced a temporary account reading `/api/member/availability` with HTTP 200 and login omitting restriction metadata. R7 fixes that in the opt-in durable Flask candidate:

- Current durable credential flags gate normal API requests and page access by authenticated cookie/bearer sessions, including roster-backed supervisors. Normal APIs return HTTP 403 with `code: "password_change_required"`; page reads redirect to `/change-password`.
- Login, session inspection/exchange, own password change and logout remain available. Responses expose `must_change_password` and `auth_scope: "password_change"` or `"full"`. Restricted token exchange omits the full member profile; restricted login does not put its bearer credential in a redirect URL.
- Durable `/login.html` uses the existing real member-ID/password form rather than the static test-login form. A same-origin `/change-password` form works through the existing canonical API or its alias, preserving exact input text, origin checks and readable validation errors. Passwords are not echoed into HTML.
- Reusing the exact temporary password cannot clear the flag. Successful change clears the flag, atomically audits/revokes sessions using R6 storage, clears the cookie and requires reauthentication. Input/audit-write failures keep the restriction and do not claim success.
- Fresh-login response scope follows the newly verified credential, including requests with stale or another account's token header. This last edge case was caught during final review and covered by an additional regression.
- Auth/recovery responses add no-store/no-referrer headers. No changed external CSS/JavaScript asset is referenced; the new rendered form has inline styling.

No candidate activation, production bypass removal, schema migration, account provisioning, credential filesystem choice, staffing policy change or production authority change occurred. This is an independently testable backend candidate while release gates remain blocked.

## Changed files to review

Exactly three target files are committed in PR #9:

1. [`server.py`](https://github.com/Brian910cpr/shiftcommander_v2/blob/b0f4978f24ff309918ad0eb64389fa95d948b1b0/server.py): `restrict_temporary_password_session`, `password_change_required`, `password_session_fields`, `member_login_success_payload`, auth routes, real member-login routing and password-change HTML/form behavior.
2. [`tests/smoke/test_temporary_password_gate.py`](https://github.com/Brian910cpr/shiftcommander_v2/blob/b0f4978f24ff309918ad0eb64389fa95d948b1b0/tests/smoke/test_temporary_password_gate.py): 17 new cases using the existing isolated harness and synthetic SQLite/HTTP fixtures.
3. [`docs/RELEASE_CHECKLIST_ISSUE214_R7.md`](https://github.com/Brian910cpr/shiftcommander_v2/blob/b0f4978f24ff309918ad0eb64389fa95d948b1b0/docs/RELEASE_CHECKLIST_ISSUE214_R7.md): report, contracts, reproduction commands and complete release checklist.

Supporting unchanged files: `engine/auth_store.py`, `tests/smoke/test_durable_auth.py`, `tests/smoke/test_serving_auth_safeguards.py`, `tests/smoke/auth_process_fixture.py` and `docs/RELEASE_CHECKLIST_ISSUE214_R6.md`.

Courier change: only `Codex_Reply_ShiftCommanderAstra_R7.md`. Filename collision checks across fetched/local Git history found no prior Reply/Read R7. No `Codex_Read_*` marker was created. No retired `ops/handoff/next_task.md` channel was used.

## Validation and exact outcomes

All implementation/testing was local; GitHub issue/PR/push/readback and official model-document retrieval were remote. No public repair is claimed.

| Check | Result |
|---|---|
| First two regressions against R6 | 2 expected failures confirmed the defect. |
| Initial gate suite | 15 passed in 25.906 seconds. |
| Combined gate/durable-auth/audit/serving-auth/beta-session/persistence/resolver suite | `Ran 143 tests in 154.417s` / `OK`; zero failures/errors/skips. |
| Final gate suite after two-line fresh-login scope correction and new regression | `python -B -m unittest discover -s tests/smoke -p test_temporary_password_gate.py -v`: `Ran 17 tests in 33.170s` / `OK`; zero failures/errors/skips. |
| Final syntax | AST parse and in-memory compile passed for both changed Python files. |
| Scope | Target working tree clean after commit; explicit three-file stage and base-to-head whitespace checks passed. GitHub PR file list matches those three files. |
| GitHub checks | Check-run API returned `total_count: 0` for target commit; local evidence is not CI proof. |
| Browser visual validation | BLOCKED: browser selection returned `No browser is available`; inventory was `{"apps":[],"browsers":[]}`. |

The combined run had 16 gate + 54 durable-auth + 15 audit-store + 23 serving-auth + 8 beta-session + 12 live-state-store + 15 resolver cases. The final targeted suite added one case. Thus evidence covers 17 final gate cases and 127 broader regressions, **not a single final-tree 144-case run**. The report includes the exact command to run the current combined 144-case suite. No unresolved local test failure remains.

New process evidence: temporary login -> actual OS-process stop/restart -> restriction still enforced -> password change -> another process restart -> old token rejected -> fresh full-scope login/readback. Existing durable-auth process/backup/recovery coverage also passed. These are synthetic local Windows proofs, not hosted recovery or a real staffing publication cycle.

Rendered HTML/form checks validated actions, password field types, no echoed credentials, origin rejection, errors, HTTP 303 and fresh login. No screenshot, mobile layout or real-browser-cookie claim is made. A separate synthetic UI fixture started at `http://127.0.0.1:50706/login.html`; after discovering no browser surface, its identified process and parent were stopped and the listener was confirmed absent. The first guarded stop command refused a path-separator mismatch; inspection corrected the exact match before stopping only those fixture processes. No operational process was touched. No normal application URL is left running.

Ignored local evidence remains under `E:\GitHub\shiftcommander_v2_codex_issue214_r7\debug\auth_r7\`: `password_gate.log`, `combined_final.log`, `combined_runtime.log`, `password_gate_final.log`. They are intentionally not committed. Tests prohibit external calendar/source fetches and keep mutable state synthetic/temporary. No schedule or sitewide generator ran; no operational mirror changed.

## Exact blockers, limitations and deployment state

1. **Provider metadata access:** the prior Cloudflare Pages metadata read returned HTTP 401; minimum Pages/Worker/binding read access remains unverified. R7 did not retry the unchanged failing auth path. Restore that access and verify actual routing/bindings before any coordinated cutover. R2's exact sanitized evidence is [`docs/RELEASE_EVIDENCE_ISSUE214_R2.json`](https://github.com/Brian910cpr/shiftcommander_v2/blob/286876e7d506bd127e14c2852f65c827815a8fa7/docs/RELEASE_EVIDENCE_ISSUE214_R2.json), especially `read_only_checks[].pages_error_status` and `render_services`.
2. **Credential/storage authority:** no approved persistent `SC_AUTH_DB_PATH`, privately provisioned real accounts, strong signing material or verified deployed/inherited configuration is established. Candidate activation requires R6 schema version 2 and approved provisioning/recovery. Missing credential flags retain the existing false default; provisioning must review them explicitly. No real database was upgraded or selected.
3. **Current ADR authority:** approved availability consent, staffing demand, roster/certification, unit-specific qualOp and current ADR Calendar snapshot remain unreconciled. Last successful prior public schedule evidence ended August 10, 2026. Do not substitute historical/seed data or infer consent from Blank; preserve ADR Calendar published-staffing authority.
4. **Remaining auth/client work:** this gate restricts authenticated durable Flask sessions; it is not a complete anonymous/static-read protection repair. Existing publicly exposed endpoints/bypasses remain broader serving-lane work. Standalone frontend/Worker consumers must enforce `auth_scope`, respond to the 403 and use their configured backend for recovery. A returned `role` alone is insufficient. Full-session token transport, client reauthentication and named supervisor accountability remain open.
5. **Whole-system proof:** no real staged availability -> lawful resolver -> supervisor review -> publication cycle or member/supervisor/mobile/wallboard agreement has been established. Hosted backup restoration, audit continuity, health observer and observer heartbeat are unproven. Phone/SMS/email identity, source retention, deduplication, ambiguity review and retry/failure handling remain in scope after core proof.
6. **Browser proof:** no browser/app surface is connected to the available UI tool. Server-rendered HTML tests do not resolve actual browser/mobile behavior. No account prompt is needed merely to preserve this candidate; visual proof must precede activation.

Fresh GitHub readback shows main still at `67a3f88f1b54fa2ffbd285df7df969cea7837616`. That is repository state, not fresh provider deployment health. R2's Render main/D1 bridge observations and R3's timeout/403 remain historical evidence, not current success. No account-auth retries, deployment, main merge, production write or member communications occurred. PR #9 and parent #5/#6/#7/#8 remain draft/unmerged; #214 remains open. R1/R2 work is preserved separately.

## Preservation, model and single-worker evidence

- Original `E:\GitHub\shiftcommander_v2` remains dirty on `codex/base44-worker-consolidation`, ahead four unpublished commits: `3287eb4`, `9a49b9e`, `69bc1fb`, `55d6a05`. Calendar mirror, availability backup, slot schedule data/source/test files remain untouched. Prior target worktrees/PRs remain intact.
- Original `E:\GitHub\910cpr-class-landers` remains on `codex/durable-session-participant-linking` with the same unrelated HTML/cache/heartbeat/Supabase-temp changes. This new courier worktree has its checkout-time `docs/Earl/index.html` difference left unstaged/uncommitted; it is excluded from the receipt commit. No resets/restores/rebases/merges/cleanup occurred.
- Active-thread local `turn_context`: `model=gpt-6-astra`, timestamp `2026-09-13T14:53:43.782Z`; installed `codex-cli 0.153.4`. Only sanitized fields are returned. This is local runtime evidence, not provider-side attestation or a configuration-only claim.
- Existing R2 `scripts/Start-AstraReview.ps1 -RepoPath E:\GitHub\shiftcommander_v2_codex_issue214_r6 -CheckOnly` at `2026-09-13T10:55:03.1992899-04:00` returned `can_launch=false`, dispatcher lock held/inaccessible. No second worker or launcher, lock/lease change, timer or unrelated model-default edit occurred. The same project launcher can target R7 after legitimate release of the lock/lease.
- Pickup: [#214 acknowledgement](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5654025375) at `2026-09-13T14:55:43Z`. Only #214 had an open title beginning exactly `[CODEX]` in the queue sweep; no independent eligible backend dispatch was identified. This increment advanced safe backend work despite external release blockers.

## Proof contract and next action

Expected real outcome: member availability persists through restart and feeds legally staffed, reviewed publication consistently across views. Last successful complete real-world proof: **unverified**. Latest synthetic local proof: September 13 runs above. Test cadence is on candidate changes, not a production observer.

Failure/staleness signals: unavailable auth storage fails closed; audited password changes roll back when audit/storage writes fail; restricted normal requests return the documented 403. These do not prove schedule freshness or hosted recovery. No verified operational observer or observer-health heartbeat exists; Brian must not become the missing monitoring layer.

**Recommended ChatGPT action:** review PR #9 and the complete R7 report against R6, especially recovery endpoint scope, supervisor identity handling, current durable flag revalidation and standalone-client limitations. Keep the stack draft and #214 open. Restore minimum provider metadata access, approve the persistent credential path/private provisioning and current ADR inputs, then perform staged browser/client/anonymous-access, legal publication and hosted recovery verification. Do not activate the candidate to discover those answers. R6's current-state schema upgrade is not stale-backup recovery.

Owner/account action is still needed for the precise provider/storage/credential/current-input authority gates. No new broad permission request is needed for reviewing this pushed candidate. This receipt is a checkpoint, not a release or a ChatGPT acknowledgement; only ChatGPT may create its `Codex_Read_*` state.
