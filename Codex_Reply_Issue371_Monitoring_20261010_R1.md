# Codex Reply — Issue371 monitoring and older-record recovery, R1

Date: October 10, 2026. Review branch: codex/issue371-monitoring-20261010. Existing PR: #372, feat/customer-learning-studio-20261010, remains draft/unmerged. Source commit: d82a0b5f0 (full SHA recorded by git and final issue comment).

## Outcome and evidence levels

Changed in repo and validated locally: existing Windows loop now publishes one allowlisted GitHub health comment every minute, including during actual execution. Installed locally, running PID 33536, started 2026-10-10T21:41:00Z. Observed actual remote publications at 21:41:08Z, 21:42:08Z and 21:43:09Z. Signal: https://github.com/Brian910cpr/910cpr-class-landers/pull/372#issuecomment-6102455692 . GET /repos/Brian910cpr/910cpr-class-landers/issues/comments/6102455692 retrieves current body. A PR comment avoids changing intake issue updatedAt and causing self-dispatch. One comment is edited; no new task, service, scheduler or CRM was created.

NOT PROVEN: independent ChatGPT observation, stopped-launcher detection, scheduled alert delivery or recovery notification. Existing 910CPR Delta Watch and 910CPR Deep Stability Review remain unchanged because their account settings are inaccessible: the browser at https://chatgpt.com/tasks redirected to https://chatgpt.com/auth/login/?next=%2Fscheduled and still displays Log in or sign up. Enabled tasks reported by Brian are not proof of execution/notification. Connected tool discovery exposes no manager for arbitrary existing ChatGPT Scheduled Tasks; Codex desktop automation tools manage different automations and were not used to create substitutes. No real outage was injected before connecting an observer. Do not call the monitoring gap closed.

Owner action: sign in to ChatGPT in the preserved browser panel using the account owning those two tasks, then tell this session sign-in is complete. Never post credentials. The exact additive instructions and bounded stop/recovery acceptance test are in docs/CODEX_WAKE_SUPERVISION.md. Keep original duties/schedules. Verify task IDs, access to current GitHub comment, notifications and run evidence before stopping the verified idle loop. Delta Watch must detect a naturally stale published_at (>5 minutes) on its scheduled hourly run and deliver the alert without Brian polling. Deep Stability Review independently checks health and Delta Watch execution within 90 minutes, or explicitly reports observer health UNKNOWN if it cannot inspect execution evidence. Expected detection roughly 65 minutes plus scheduler delay. Always restore the same loop. Missing task access/notification is a separate observer failure, not a reason to claim healthy.

## Existing mechanism and safety

No existing assignments/watermarks were cleared. Only the known idle loop PID 33184 with checked start time was stopped for the publication upgrade; no active execution was killed. The worker lock was acquired during replacement and a manual implementation hold prevents overlap during this desktop session. Prior installed scripts backed up under local CodexWake backup-health timestamp directory. Existing Windows Startup entry is preserved. Release this session's manual-hold.json on yielding. Installed state/config and runtime logs remain outside Git.

ops/scripts/Start-CodexWakeLoop.ps1 uses the SAME exclusive supervisor loop; its worker subprocess runs asynchronously so that same process can publish during long jobs and idle waits. ops/scripts/Publish-CodexWakeHealth.ps1 allowlists timestamps, loop/execution state, hold state, issue IDs, last session and retry state. No raw errors, paths, prompt bodies or credentials are published. Publication errors log a generic local message and do not kill intake; remote timestamps naturally become stale. Installer copies the publisher and preserves local health-publish.json containing only the configured comment ID. CyberPC sleep/logoff remains an availability boundary.

## Issue371 progress in the existing implementation

Prior real automatic session 01a127ab-4087-7f83-93e6-9a1254bbcaaf completed at 2026-10-10T21:25:01Z with atomic interruption/resume and audited task mutation APIs; PR372 reached ccd1f76949851713a5051c1f1eda30ead3acb4cd before this increment. Existing schema, canonical case/person relationships, owner auth and APIs reused.

supabase/functions/customer-interactions/handler.ts now supports owner-only collection GETs, bounded 1–100, status filters including paused interactions, and creation-time/UUID keyset cursors preserving microseconds. It retrieves a lookahead row to expose has_more and next_cursor. Immutable creation ordering avoids duplicate timestamps losing records; invalid/duplicate/unknown parameters fail before storage. Legacy no-query combined GET remains compatible. No migrations, dependency, privilege or public browser changes. tests/customer_interaction_pagination.test.mjs traverses 125 tied paused records and checks filters, injection and owner denial. It uses injected REST fixtures, NOT a real remote PostgREST instance. Existing SQL suites separately execute actual migrations/RPCs in PGlite.

Live traversal is not a snapshot: status changes can move rows between filtered views; refresh after disposition. Isolated preview must verify lookahead permitted (>=101 Data API rows), actual query semantics, owner-session access and UI flows. No remote deployment/production schema or auth change. Existing tab-local prototype is still not durable operational capture.

Remaining CRM blocker: identify authorized isolated Supabase project and permitted preview browser origin; current owner auth permits production origins only. Do not widen production auth or use production as preview. Once identified, validate migrations/function there and connect existing UI with autosave, retries, conflicts, pending-save protection and recovery. Retention/deletion remains open. PR372 stays draft/unmerged/undeployed.

## Exact validation

Commands (run from D:/Users/ten77/Documents/910cpr-issue371-interrupt):

node --test tests/codex_wake.test.mjs
Result: tests 4, pass 4, fail 0.
node --test tests/codex_wake_health.test.mjs
Result: tests 2, pass 2, fail 0. Payload allowlist/live process/hold and publication-error isolation tested using mocked gh.

PGLITE_MODULE=file:///C:/Users/ten77/Documents/Codex/2026-10-10/codex-p0-diagnostic-repair-automatic-instruction/work/pg-proof/node_modules/@electric-sql/pglite/dist/index.js
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/admin_auth.test.mjs
Result: tests 33, suites 0, pass 33, fail 0, cancelled 0, skipped 0, todo 0.
Deno check supabase/functions/customer-interactions/index.ts: exit 0.
PowerShell Parser::ParseFile on ops/scripts/*CodexWake*.ps1: no errors.
git diff --check: exit 0.
Total: 39 tests pass. No public generator/build/deployment. No simulated alert reported as real.

Review files:
- ops/scripts/Publish-CodexWakeHealth.ps1
- ops/scripts/Start-CodexWakeLoop.ps1
- ops/scripts/Install-CodexWake.ps1
- ops/scripts/README_CODEX_WAKE.md
- docs/CODEX_WAKE_SUPERVISION.md
- docs/CUSTOMER_INTERACTION_STORAGE.md
- supabase/functions/customer-interactions/handler.ts
- tests/codex_wake_health.test.mjs
- tests/customer_interaction_pagination.test.mjs

Intentionally excluded: unrelated docs/Earl/index.html, docs/Jackson/index.html and CLI supabase/.temp/. No Codex_Read_* file created/renamed. No competing scheduler, production merge, destructive cleanup, force push or unrelated active-production changes.
