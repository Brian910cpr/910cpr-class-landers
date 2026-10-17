# Issue #371 — durable follow-up confirmation checkpoint

- Timestamp: 2026-10-13T14:52:36.247312+00:00 (UTC)
- State: IN_PROGRESS; persistent-system evidence BUILT, validated locally with synthetic fixtures.
- Review branch: codex/issue371-next-20261013.
- Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
- PR head branch: feat/customer-learning-studio-20261010.
- Base: 348e19bdd0a9c5f386c062350d8ca0d2a624618b.
- Substantive commit: 189622586f3cff8cd10546f50754b67061fae202. This receipt is committed separately; pushed tip is reported on #371 and in the dispatch response.

## Actual execution and findings

Read issue #371 body/comments and repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged execution before implementation at https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6148196834 . Latest owner Path A controls; Docker/WSL/Synology staging remains paused. No arbitrary third-party authorization used. Existing PR reused, one deep stream preserved, no new PR/launcher/monitor/assignment edits. Read-only open [CODEX] queue sweep performed; no unrelated implementation undertaken because no independently verified quick win was established without disrupting the primary stream. Historical blocked #214/#297 assignments were not retried.

Root finding: save_task accepted any object as confirmation. It could cache wrong task/link/status/version/provenance/due values, unsafe for future saved-only NEXT. Targeted client checks now reject those before caching; identical request retry can retrieve a corrected receipt. Due validation preserves PostgreSQL microseconds and equivalent timezone offsets. An unloaded task disposition coordinator coalesces sends, freezes input, retains uncertain request/conflicts and exposes canLeave only after matching confirmation. All 4xx failures freeze for reconciliation; repeated successful sends still pass transport owner-session fencing. Existing canonical objects/RPC/audit preserved. No schema/auth/CORS/API shape change.

## Exact changed files / review targets

1. docs/admin/customer-interaction-client.mjs — validate task receipt before caching.
2. docs/admin/customer-interaction-task.mjs — new unloaded disposition coordinator; immutable input, retry, terminal conflict, saved-only navigation signal.
3. docs/admin/customer-interaction-studio.mjs — versioned imports only (20261013-task1).
4. docs/admin/customer-learning.html — versioned controller reference only; gate still disabled.
5. tests/customer_interaction_client.test.mjs — generic coalescing fixture now uses valid save acknowledgment.
6. tests/customer_interaction_task.test.mjs — five task tests, including actual handler + real local SQL composition.
7. docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md — appended exact findings/proof/limitations/next action in “Follow-up task confirmation boundary — 2026-10-13”. This primary safety report preserves prior live metadata and rollout gate findings.
8. Codex_Reply_Issue371_TaskBoundary_20261013T145236Z_R1.md — this immutable root receipt.

Important unchanged contracts: supabase/functions/customer-interactions/handler.ts; supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql; docs/CUSTOMER_INTERACTION_STORAGE.md. The existing immutable event input stores completion_evidence; it is not echoed in task rows. Matching receipt confirms submitted bookkeeping version, not external execution or perpetual freshness across tabs.

## Validation commands and exact results

Reused existing scratch PGlite 0.3.14; no dependency installation. All processing/tests local; documentation fetched read-only remotely.

```powershell
$env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/customer_interaction_restart.test.mjs tests/customer_interaction_grants.test.mjs tests/customer_interaction_cors.test.mjs tests/customer_interaction_client.test.mjs tests/customer_interaction_checkpoint.test.mjs tests/customer_interaction_switch.test.mjs tests/customer_interaction_task.test.mjs tests/admin_auth.test.mjs
python tests/customer_interaction_studio_browser.py
node --check docs/admin/customer-interaction-client.mjs
node --check docs/admin/customer-interaction-task.mjs
node --check docs/admin/customer-interaction-studio.mjs
git diff --check
```

Exact Node summary:
```text
# tests 68
# pass 68
# fail 0
# skipped 0
```

Exact browser summary:
```text
Ran 8 tests in 7.509s
OK
```

After final all-4xx/session-fence hardening, affected task suite rerun: tests 5 / pass 5 / fail 0. Syntax/diff passed. Initial focused run had one fixture failure because response/request nested provenance shared an object; fixed fixture structuredClone, subsequent full and affected suites green. No known unrelated test failure. Chromium verifies unchanged gated capture/switch behavior with synthetic API/auth, not task DOM integration. New task composition executes real local SQL behind actual handler/transport: create -> complete committed -> response loss -> identical retry -> two immutable audit events; stale/duplicate/missing-evidence writes fail. Existing restart/grants tests remain green.

## Persistence, deployment and unrelated work

Persisted in actual isolated repository worktree E:/GitHub/910cpr-issue371-next-20261013; intended seven files committed explicitly, receipt separately. Push intended to both review branch and existing PR branch; verify root receipt on GitHub before exiting. No merge, deploy, production DB/API write, flag exposure, origin expansion, generator or public schedule rebuild. PR372 remains draft. E:/GitHub/910cpr-class-landers dirty work/broken refs left untouched. Unrelated modified docs/Earl/index.html and docs/Jackson/index.html also appeared in isolated worktree, preserved unstaged; their producer was not established and they were not edited or committed by this dispatch. No intentionally untracked assignment artifacts; all intended new files committed. Existing other worktrees/untracked receipts/temp files untouched.

## Proof contract / remaining gates

Expected outcome/cadence: on-demand task save/disposition with matching confirmation and immutable source/completion evidence. Last local synthetic composition: 2026-10-13, tests/customer_interaction_task.test.mjs. Real owner-session UI -> Edge Runtime -> PostgREST -> persisted database -> reload/resume/conflict proof still absent. Task helper remains unloaded; no task UI or NEXT completion claimed. Failure is missing/malformed receipt, conflict/auth denial or uncertain commit; navigation stays blocked. Recovery: identical retry for uncertainty; retain/export disposition, fetch/review server task/version for terminal conflicts. Future UI must clear coordinator on session lock and require BOTH interaction and task canLeave before navigation. Local runner observes regressions; no deployed CRM outcome observer or observer-health evidence, so not MONITORED/HEALTHY. Brian must not become routine observer.

Production NO-GO remains: durable follow-up/NEXT UI integration, genuine owner-session UI/API/database proof and usable recoverable backup/restore evidence; then separate explicit owner rollout GO. These are release gates, not a blocker to safe same-stream local backend/UI work. No owner/account action needed now. Do not request approval of incomplete gates or restart obsolete installation prerequisites.

## Exact next action for ChatGPT/Codex

Review substantive commit and task tests; keep PR372 draft/unmerged/undeployed and gate disabled. Continue same stream by binding this coordinator to owner task fields/status/loading and guarded NEXT in the existing Studio. Require confirmed interaction AND task disposition; an outstanding follow-up must not be closed by the current no-follow-up resume, and Board attention remains read-only. Add task browser save/reload/uncertain retry/conflict tests, then complete real owner-session and backup/restore proof before an exact minimal rollout approval request. Do not overwrite this receipt or create Codex_Read files from Codex.
