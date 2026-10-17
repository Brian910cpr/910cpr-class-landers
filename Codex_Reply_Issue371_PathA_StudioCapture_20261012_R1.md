# Issue 371 — Path A gated Studio capture checkpoint

- Timestamp: 2026-10-12T18:26:14-04:00 (America/New_York).
- Assignment: Brian910cpr/910cpr-class-landers#371; existing draft PR https://github.com/Brian910cpr/910cpr-class-landers/pull/372.
- Review branch: `codex/issue371-ui-20261012`; existing PR branch: `feat/customer-learning-studio-20261010`.
- Base: `b57cd799618a565886ded2f55864f184b4355716`.
- Substantive commit: `1f58ebeed5cf8a9cb673704062ce656dd873366d`. Receipt is a separate subsequent commit; pushed tip must be reported on the issue/final response and verified on GitHub.
- Work-item state: IN_PROGRESS / PR_OPEN. Persistent evidence: BUILT, locally validated default-off UI. Not production-complete, PROVEN, MONITORED or HEALTHY.

## Execution and findings

Actual dispatch acknowledged before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6133672744 . Read issue/body/comments and repository AGENTS, handoff, design ethos and proof standard. Followed latest owner Path A; Docker/WSL/Synology staging remains superseded for this milestone. Prior production metadata/CORS/client/checkpoint evidence reused; no repeated live schema scan or production write. Supabase skill/changelog and manual CORS docs reviewed. Launcher signal observed current_task=371, execution_process_alive=true, manual_hold=false, session 01a13221-e12e-78e1-bc17-ae3027d78e2e; assignments/monitors untouched. Queue titles scanned; no new competing deep stream or arbitrary third-party authorization used.

Prior modules were disconnected from the Studio. Added actual UI binding for capture, server queue/current-version loading, debounced save, explicit identical retries, conflict review and guarded navigation. Server-fetched records initialize a confirmed checkpoint without a redundant write. Customer name/contact are unverified document text; no person linkage inferred. Immutable history remains owned by existing backend objects, moving toward native LanderWare independence without new Enrollware dependency.

The committed meta gate is DISABLED. No query parameter/local storage flag can enable it. The auth helper accepts the exact CRM endpoint only from the exact Studio pathname with explicit enabled gate; server owner authorization and CORS remain unchanged. Asset URLs use version 20261012-ui1. Durable mode does not read/write/import prototype sessionStorage drafts; disabled mode preserves the prototype. Startup failure stays disabled instead of falling back to tab-only capture. Session lock clears private fields and queue.

Atomic interrupt/resume and stored follow-up task/NEXT disposition remain UNWIRED. Their prototype controls are disabled in durable mode, including New call while a record is active, rather than suggesting an independent save is atomic interruption. Production Board attention stays read-only. No customer lookup, email send, Gmail/Fieldy/Tasks integration, payment/refund/reschedule, policy promotion, scheduling logic, public inventory or production infrastructure changed.

## Exact changed files / review order

1. `docs/admin/customer-interaction-studio.mjs` — new gated DOM/controller integration; review save, loading, conflict and lock/navigation paths.
2. `docs/admin/customer-learning.html` — disabled meta gate, startup failure handling, versioned module/auth URLs and save controls; prototype skip only under explicit enabled gate.
3. `docs/admin/admin-auth.js` — narrow conditional exact CRM URL credential routing; all existing service rules retained.
4. `docs/admin/customer-interaction-checkpoint.mjs` — explicit confirmed initialization for fetched records; existing draft behavior unchanged by default.
5. `tests/customer_interaction_studio_browser.py` — five real Chromium tests using synthetic intercepted API and synthetic owner session.
6. `tests/admin_auth.test.mjs` — exact path/gate credential routing regression.
7. `tests/customer_interaction_checkpoint.test.mjs` — confirmed fetch initialization requires no write.
8. `docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md` — full safety report and new default-off Studio integration section, exact commands, evidence boundaries and next gates. Earlier live catalog references remain `data/audit/issue371_patha_metadata_20261012.json`; no new live metadata was collected.
9. `Codex_Reply_Issue371_PathA_StudioCapture_20261012_R1.md` — this receipt.

## Validation and exact material outputs

Local execution only; no dependencies installed and no generator/full build run.

```text
Node CRM/auth suite:
1..57
# tests 57
# pass 57
# fail 0
# cancelled 0
# skipped 0

python tests/customer_interaction_studio_browser.py (final run):
.....
Ran 5 tests in 5.204s
OK

node --check docs/admin/admin-auth.js: exit 0
node --check docs/admin/customer-interaction-checkpoint.mjs: exit 0
node --check docs/admin/customer-interaction-studio.mjs: exit 0
All nonempty inline HTML scripts extracted to temporary .mjs files and node --check: exit 0
Python ast.parse browser test: passed
git diff --check: exit 0
```

Reproduce full Node command in `docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md` new section. PGLITE_MODULE uses existing cached 0.3.14 dependency at `C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js`. Browser test uses existing Python Playwright/Chromium, localhost static server and synthetic API interception; no genuine credentials/customer data or live Supabase requests. Browser coverage: default off/no CRM requests; save/reload; autosave then actual tab close/reopen; lost-response same-envelope retry; conflict draft retained and reviewed; navigation blocked while dirty; auth-lock privacy; module-load fail-closed. Desktop 1440px screenshot visually inspected, temporary only at `C:/Users/ten77/AppData/Local/Temp/issue371-studio-ui.png`, not committed. Existing tests separately prove local synthetic SQL transactions/restart; browser mocks do not prove actual Edge Runtime/PostgREST/owner-session/database integration.

## Preservation / deployment

Original E: checkout dirty work left untouched. Separate named worktree: `E:/GitHub/910cpr-issue371-ui-20261012`. Windows checkout case-collision modifications `docs/Earl/index.html` and `docs/Jackson/index.html` appeared in this new worktree and remain unstaged/uncommitted; not repaired or included. Browser test execution can create untracked `tests/__pycache__`; excluded. Existing original E: dirty pages/data/cache/temp/receipts remain preserved. Only the nine explicit intended files are committed. No cleanup, reset, restore, force-push, merge, deployment, production DB/API write, origin expansion, NAS write or installation. PR372 stays draft. No ops/handoff/next_task.md use or Codex_Read creation.

## Remaining gates / proof contract / next action

Production NO-GO is unchanged: actual recoverable backup/restore evidence and real owner-session UI → Edge Function → database save/reload/resume/conflict proof remain absent. The useful CRM slice is still incomplete until atomic interruption/resume and durable follow-up/NEXT are wired and verified. This is not an auth/credential failure discovered in this run and no owner action is needed for safe local continuation. Do not ask for approval of an incomplete safety gate. After gates pass, prepare exact minimal rollout and seek the separate explicit production GO before migration/function deployment/UI exposure/merge.

Expected outcome: owner captures and recovers confirmed notes/case work. Cadence: on demand. Last useful browser proof: 2026-10-12 local synthetic autosave/tab reopen, in the test above; last real owner/UI/API/database proof: none. Failure conditions: missing/mismatched receipt, conflict, inaccessible stored work or retained unsaved edits. Local test runner detects these regressions, but no deployed CRM outcome observer or observer-health proof exists. Browser unconfirmed edits still can be lost on crash/closure; beforeunload/internal-link guards reduce risk without claiming guaranteed crash recovery. Recovery: preserve draft/request, identical retry after uncertain response, explicit current-version review/reconciliation, reload confirmed work/export unsaved notes before closure. Routine monitoring must not depend on Brian; unresolved until operational integration.

Exact next same-stream action: review the four source files above, wire the existing atomic interrupt/resume RPC envelopes plus durable follow-up task/NEXT disposition into this controller, extend Chromium tests and compose real handler/SQL integration proof. Establish recoverable backup evidence and genuine owner-session runtime proof before the separate production go/no-go. Preserve all existing assignments and draft PR372. No duplicate PR/launcher or Docker prerequisite request.
