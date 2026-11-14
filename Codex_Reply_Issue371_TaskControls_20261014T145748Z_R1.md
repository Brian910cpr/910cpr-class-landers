# Issue #371 — stored task disposition controls

- Timestamp: 2026-10-14T14:57:48Z (UTC).
- Branch: codex/issue371-task-controls-20261014.
- Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
- Substantive commit: 90197cebbf7ab6f59cfb0686eb7eac2e8db6d31c.
- State: IN_PROGRESS / PR_OPEN; persistent evidence BUILT, validated locally with synthetic fixtures.

## Execution and scope
Actual pickup acknowledged before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6171217430 . Read issue/body/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof rules and Path A safety report. Owner directions govern; third-party review is not authorization. Existing PR head ae3d10f7764d94bf9d710fa10dd6fe80dbc5e7d3 reused via isolated E:/GitHub/910cpr-issue371-task-controls-20261014, created from healthy D: git common repository because E:/GitHub/910cpr-class-landers lacks the current handoff protocol and has unrelated dirty work. Existing assignments, monitors and original worktrees untouched. Open issue title sweep performed; no competing deep stream started.

## Findings and changes
Existing helper was not wired to task status UI. Studio now exposes stored follow-up pending/reopen, snoozed and complete dispositions with explicit owner evidence. Task identity/linkage/source/version are preserved from fetched canonical tasks. Snooze requires a valid local-time input converted to ISO; no reminder scheduled. Completion records owner evidence, not automatic external execution.

Selected unsent status drafts block navigation and interaction editing, with explicit cancel before submission. Uncertain submissions freeze and reuse identical requests; terminal conflicts retain original envelope and draft for export and current-server review. No cancellation/rebase can discard submitted intent. Confirmation updates stored tasks; reload fetches current versions. Owner lock clears private selection/evidence/due values. Production Board stays read-only. Existing task/resume SQL fence unchanged. Assets versioned 20261014-taskcontrols1.

This extends native LanderWare task lifecycle and canonical provenance without a new catalog or Enrollware dependency. Prior mature-system rationale remains docs/CUSTOMER_INTERACTION_STORAGE.md. Manual controls are a foundation/fallback; asynchronous discovery and automatic NEXT are not claimed.

## Exact changed files / review targets
- docs/admin/customer-interaction-studio.mjs — selection, status mutation, retained exports, guards, privacy clearing.
- docs/admin/customer-learning.html — disabled-by-default owner control fields and versioned module reference.
- tests/customer_interaction_studio_browser.py — four added Chromium workflow regressions.
- docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md — full new findings/proof contract in section Stored follow-up status controls — 2026-10-14.
- Codex_Reply_Issue371_TaskControls_20261014T145748Z_R1.md — this unique root receipt.

Relevant unchanged implementation: docs/admin/customer-interaction-task.mjs; docs/admin/customer-interaction-client.mjs; supabase/functions/customer-interactions/index.ts; supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql. Concurrency runner instructions: docs/CUSTOMER_INTERACTION_CONCURRENCY.md.

## Validation / exact relevant output
Reused existing cached PGlite and Playwright/Chromium; no installation.

PGLITE_MODULE=file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js

node --experimental-strip-types --test tests/customer_interaction_task.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_client.test.mjs tests/admin_auth.test.mjs

# tests 35
# pass 35
# fail 0
# cancelled 0
# skipped 0

python tests/customer_interaction_studio_browser.py

Ran 15 tests in 14.627s
OK

New browser cases prove response-loss completion/exact retry/reload/reopen; explicit snooze validation/time conversion and unsent cancellation; conflict export and privacy clearing; completed follow-up allowing no-obligation call resume. Browser auth/API are synthetic; real local SQL is exercised by existing composed task/handler/RPC tests. These are not independent-session concurrency or real owner-session runtime proof.

node --check docs/admin/customer-interaction-studio.mjs: passed.
Python ast.parse of tests/customer_interaction_studio_browser.py: passed.
Targeted git diff --check: passed; line-ending normalization warnings only.
Initial editor encoding/newline errors corrected before final validation; first unchanged 11-browser regression suite passed, expanded final 15-browser suite passed. No outstanding known test failure. No generator.

## Persistence and deployment
Four substantive files committed locally on named branch; this receipt is a separate communication commit referencing the substantive SHA. Both branch and existing PR372 head pushed fast-forward only and receipt presence verified through GitHub contents API before exit. No force push, merge, production write, schema/function deployment, origin expansion, gate enablement, installation or reboot. PR remains draft; gate OFF. CI/branch-preview activity is not a production deployment or operational proof claim.

Unrelated original E: dirty files/untracked replies/cache/runtime artifacts preserved. Isolated Windows checkout has case-collision changes docs/Earl/index.html and docs/Jackson/index.html; explicitly excluded from staging and left dirty. No cleanup/reset/restore.

## Exact remaining gates and proof contract
Automatic saved-only NEXT remains unfinished. Independent READ COMMITTED concurrency proof remains blocked on absent authorized empty localhost PostgreSQL runtime/client and psycopg 3, per prior recorded preflight; no installation or production fallback attempted. Genuine owner-session UI/Edge/PostgREST/database recovery/conflict proof and usable backup/restore evidence remain absent. Path A supersedes Docker/WSL/Synology prerequisites; do not repeat those requests as prerequisites. Separate explicit rollout GO is mandatory before production DB/API/UI action; this dispatch explicitly prohibits merge/deploy.

Expected outcome/cadence: on-demand evidenced task disposition survives reload with uncertainty/conflict retained. Last local synthetic successful proof: 2026-10-14, browser/Node results above. No genuine operational E2E timestamp exists. Failure/staleness: missing/mismatched receipt, stale version, uncertain write or auth loss; navigation blocks. Observer: local test runners on demand only, no deployed CRM outcome observer or observer-health proof. Recovery: identical retry for uncertainty; private draft export and fresh server review for terminal conflict, never blind overwrite. Unconfirmed fields remain memory-only and can be lost on process termination. Brian is not represented as the routine monitor. No CONNECTED/PROVEN/MONITORED/HEALTHY claim.

## Next concrete same-stream action
Review exact four substantive paths and commit above. Continue existing PR372 with explicit interaction disposition and saved-only NEXT, requiring confirmed interaction/task checkpoints, no pending switch or drafts, deterministic eligible-item selection and browser failure/conflict tests. Preserve Board read-only status. Then run the documented independent-session experiment only in an authorized empty local PostgreSQL environment, establish genuine owner-session recovery and usable backup/restore evidence, and prepare the exact separate rollout go/no-go. No owner action required for safe code/test continuation. No merge or deployment authorized.
