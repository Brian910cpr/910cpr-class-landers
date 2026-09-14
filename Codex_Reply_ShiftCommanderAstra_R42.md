# ShiftCommander Astra R42: release prerequisite assessment

- Assignment: [910cpr-class-landers #214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214), dispatch `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing R41.
- Timestamp: 2026-09-14T02:34:30-04:00 (America/New_York).
- Work-item state: **BLOCKED** for release. Assessment persisted locally; this receipt is the only intended change being committed and pushed. No application merge, deployment or activation.
- Persistent-system evidence: **BUILT**, with retained local synthetic evidence. Full operational CONNECTED/PROVEN/MONITORED/HEALTHY is not established.
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r42`.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r42`; base commit `387be9c0c16a6d6b8184fed30b59a17a5eec5bbf`. The post-push #214 comment records the receipt commit and remote content verification; its own SHA is not embedded recursively.
- Application commit: `ba0365a250d18297a262b96ab7f15cf3fe6f1780`, branch `codex/issue-214-private-boundary-r8`, [OPEN draft PR #10](https://github.com/Brian910cpr/shiftcommander_v2/pull/10).
- Read-only target assessment: `E:\GitHub\shiftcommander_v2_codex_issue214_r9`, `codex/issue-214-release-gate-verification-r9` at `16d0ace259b485a7585decbef24c74e94bd69f5c`.

## Findings and work performed

Read the complete issue body and all 87 pre-pickup comments, pinned original dispatch, original and current courier AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, docs/CODEX_INSTRUCTIONS.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md, #116, and target AGENTS/project boundaries/confirmed scheduling rules/RULES/DATA_CONTRACT. Read R8/R9 release evidence and historical migration/overlay documents. The original courier branch lacks CODEX_HANDOFF_PROTOCOL.md; its GitHub/current-main version was used before changes.

Fresh GitHub readback confirms the unchanged PR #10 head, OPEN/draft state, the original three-file scope (`server.py`, `tests/smoke/test_private_serving_boundary.py`, `docs/RELEASE_CHECKLIST_ISSUE214_R8.md`) and empty `statusCheckRollup`. Target remote main remains `67a3f88f1b54fa2ffbd285df7df969cea7837616`. These are repository observations, not current hosting-health proof. The R9 tree differs from R8 only by `docs/RELEASE_VERIFICATION_ISSUE214_R9.md`.

No new clearing prerequisite evidence or reproduced independent defect was established. The reviewed hold on speculative implementation, merge and deployment remains applicable. Account-auth requests previously rejected by the provider were not repeated. No operational inputs, credentials, bindings, database, calendar authority, application code or public assets were changed. No generator ran.

## Exact blockers and required next actions

| Gate | Evidence, boundary and next action |
|---|---|
| Serving metadata access | R2's authenticated Cloudflare Pages metadata request returned HTTP 401. No subsequent approved evidence establishes minimum Pages project/deployment, Worker route and D1-binding reads. Restore those minimum permissions or supply an approved sanitized export, then verify actual serving paths before staged cutover. A bridge credential or another project's successful deployment does not establish this permission. |
| Persistent authentication authority | Approve the persistent filesystem and exact `SC_AUTH_DB_PATH`, schema version 2 readiness, privately provisioned real member/named supervisor accounts, signing configuration and inherited hosting settings. No approved current configuration was supplied through this dispatch. Do not activate on schema v1, restore revoked sessions from a stale backup, or unset the path as an assumed safe rollback. |
| Current ADR staffing authority | Approve current roster/certifications, per-unit `qualOp` and driver eligibility, explicit availability consent, demand and calendar provenance. Prior successful public schedule evidence contained 170 shifts ending August 10, 2026; this is historical, not a fresh schedule read. Preserve ADR Google Calendar's published-staffing authority and Blank = do not automatically schedule. |
| Earlier credential exposure | R37 reported a bridge credential in its local tool output. Private operator containment/coordinated rotation and rejection proof for the old credential remain unverified. R42 did not retrieve, repeat, use or change that credential. Do not put a credential value in this issue or mailbox. |
| Staged release and recovery | After the preceding gates, coordinate scoped client/alternate-host auth, real availability -> legal resolver -> supervisor review -> publication, member/mobile/wallboard agreement, hosted backup/recovery and observer proof. Retain open-shift/release/swap, partial/overnight/DST, ALS/driver shortage, locks, OT/fairness and duplicate/unauthorized-submission scenarios. Secure Windows application startup and phone/SMS/email intake remain in scope. |

Account/operator and staffing-owner action is required for the specified access, private configuration and current-input gates. Existing candidate, checklists, regression suites and recovery guidance remain usable. No broad new implementation or production cutover is justified by this unchanged dispatch.

## Runtime, validation and preservation

Matching active-thread local `session_meta`/`turn_context` fields report CLI `0.153.4`, model `gpt-6-astra`, timestamp `2026-09-14T06:27:38.764Z`. Only these allowlisted fields were returned. This is local runtime evidence, not provider attestation or proof inferred from a prompt/configuration edit.

Existing project launcher: `E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1 -RepoPath E:\GitHub\shiftcommander_v2_codex_issue214_r9 -CheckOnly`. At `2026-09-14T02:31:10.4639127-04:00`, it returned `can_launch=false`, `runtime_model_verified=false`, and `The dispatcher worker lock is held or inaccessible. Continue the active worker; do not launch a duplicate.` That launcher field describes its check-only invocation, separate from this active thread's runtime evidence. No second launch, lock/lease/default or timer change occurred. The launcher already selects `-m gpt-6-astra` for this project; it is not an application start command. [Official CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli) was fetched during assessment.

Fresh local validation passed: AST parse and in-memory compile for `server.py`, `engine/auth_store.py`, `engine/live_state_store.py` (3 files; no bytecode), plus PowerShell parser validation for `scripts/Start-AstraReview.ps1` in the R2 worktree (1 file). No unfinished merge/cherry-pick/revert/rebase/bisect markers were found in either original checkout or the target assessment worktree.

Retained R9 log readback at `E:\GitHub\shiftcommander_v2_codex_issue214_r9\debug\verification_r9\combined_final.log`:

```text
Ran 160 tests in 189.801s
OK
FINAL: tests=160 failures=0 errors=0 skips=0
```

Those behavioral tests were **not rerun in R42**. They cover local synthetic auth, restart/recovery, audit, persistence and resolver cases; they are not browser/staging/CI/production proof. No application change or new test failure justified repeating the unchanged suite. Receipt field, Markdown, whitespace and explicit staged/base-to-head scope checks passed before commit. Remote tip and complete content/blob readback follow push and are recorded on #214.

Setup exception: the new sparse worktree initially contained only `.git` with 60 tracked root files absent, producing unstaged deletion reports. Work stopped for inspection; staged diff was empty and all non-sparse index entries were root-only. `read-tree -mu HEAD` did not populate them. `checkout-index --all`, without force, populated the reviewed root-only index into that empty new directory; status then became clean. No original files were deleted or overwritten. Only this receipt is staged. This is checkout initialization, not a generator or application repair.

Both original dirty checkouts remain preserved. Courier changes remain `docs/Earl/index.html`, two tracked Python caches, untracked heartbeat/Python caches and `supabase/.temp/`. ShiftCommander retains its modified calendar mirror and untracked slot schedule, availability backup, generator/script/test work. Four unpublished commits remain `3287eb4`, `9a49b9e`, `69bc1fb`, `55d6a05`. Existing worktrees, including the unfinished R37 receipt, were not cleaned or reused for writes. Temporary issue/acknowledgement snapshots are outside the repository; no new runtime artifact is intended for Git.

## Independent backend queue assessment

Swept all open issue titles and read current bodies/latest evidence for #140, #215, #216, #219, #223, #226 and #227. No newly eligible independent narrow backend repair was established; no secondary implementation or duplicate import was started.

- #140 remains P0/account-blocked: scheduled runs `34791610996` and `34796567750` report HTTP 401 despite present masked HOT_SYNC_ADMIN_KEY. Restore validator/Actions parity before rerunning both publishers and #205. Preserve fail-closed publication.
- #215's private owner access is already delivered through merged PR #225. Preserve it. Financial/legacy Hot Sync/inbox connections, individual instructor authorization, legacy static-data privacy and monitoring remain separate work; its success does not clear ShiftCommander gates.
- #216's monitor exists; current private balances/bills and full browser/observer proof remain. Do not invent cash prompts or duplicate its dashboard.
- #219's owner document controls are deployed. Individual instructor identity/assignment scope and authenticated instructor click-through remain; do not distribute owner access to instructors.
- #223's 19-class/13-registration reconciliation already has source/roster evidence. Preserve its identities; source class 51431 still has an explicitly provisional end requiring authoritative correction. Later #215 owner access does not by itself prove this class workflow.
- #226 explicitly has active implementation on `codex/class-record-details-intake`; preserve that work.
- #227's latest stabilization review accepts the Sites slice as a deployed preview, treats its September 11 public schedule as stale/non-authoritative while #140 blocks publication, and defers customer feature/SEO expansion until backend freshness/auth/reconciliation is stable. Preserve owner-session authority and avoid duplicate scheduling truth.

## Proof contract and review handoff

Expected outcome: a real authenticated availability save survives restart, produces legal reviewed publication, and renders the same revision across all operational views. No complete real-world successful cycle or last-success timestamp is established. Local tests run on change; they are not a service heartbeat. The confirmed Wednesday 23:59 publication boundary/freshness window needs approved-input proof. Failure conditions include unreadable/auth-invalid storage, stale sources, lost saves, illegal assignments, inconsistent views or missed publication. The whole-workflow observer, its heartbeat and escalation delivery remain unproven; Brian must not become the routine detector.

Primary exact evidence: [R9 verification report](https://github.com/Brian910cpr/shiftcommander_v2/blob/16d0ace259b485a7585decbef24c74e94bd69f5c/docs/RELEASE_VERIFICATION_ISSUE214_R9.md), [R8 release checklist](https://github.com/Brian910cpr/shiftcommander_v2/blob/ba0365a250d18297a262b96ab7f15cf3fe6f1780/docs/RELEASE_CHECKLIST_ISSUE214_R8.md). Historical JSON reference: `286876e7d506bd127e14c2852f65c827815a8fa7:docs/RELEASE_EVIDENCE_ISSUE214_R2.json`, `read_only_checks` (provider/auth/schedule observations); historical interpretation is retained in the reviewed reports. Recovery boundaries: `434d7b0650602a81263afb28ec39e464462f0331:docs/RELEASE_CHECKLIST_ISSUE214_R4.md` and `5e81303e8f2cc306251ae61bd8566c3763548b83:docs/RELEASE_CHECKLIST_ISSUE214_R6.md`. Key review sources remain `server.py`, `engine/auth_store.py`, `engine/live_state_store.py`, and the eight test paths enumerated in R9. No new source/config/test file changed in R42.

Exact changed file: repository-root `Codex_Reply_ShiftCommanderAstra_R42.md` only. Processing was local except GitHub metadata/issue/push/readback and official documentation retrieval. Deployment status: no application merge/deploy, no activation, no production write, no staffing-authority cutover or member communications. No operational local URL or verified application start command is claimed.

Next ChatGPT action: review this receipt and retained candidate evidence, keep #214 and the draft stack open/unmerged, obtain the precise prerequisite evidence above and coordinate staging only when eligible. This mandatory receipt does not request another identical implementation round. Resume useful implementation on changed prerequisite evidence or a reproducible independent defect; continue other independently eligible backend work without duplicating active deliveries.
