# Issue 215 — October 12 isolated backend checkpoint

Timestamp: 2026-10-12T10:04:50-04:00
Branch: codex/issue215-review-20261012
Work-item state: IN_PROGRESS; issue not complete.
Substantive commit: 9d09148de94e602fd6c1d977d1092b87bcf59483
Reviewed main: c6861d9d718c01f7c4d83c887fa4fca2da65b859

## Execution and authority
Read full issue body and all owner comments, current AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Acknowledged execution before changes at https://github.com/Brian910cpr/910cpr-class-landers/issues/215#issuecomment-6125857455 . The later private remembered-session directive supersedes the withdrawn open-access directive. #140 is currently CLOSED; historical credential-parity failure is not asserted as a current blocker. No third-party comments used as authorization.

## Findings and work
Added tests/finance_auth_boundary.test.mjs: three deterministic local tests pin the existing Finance authorization boundary, missing configuration denial, corporate/remembered-session denial, legacy-key acceptance and restricted CORS. Tests never call Stripe or read/write financial data. No application/authentication changes.

Exact relevant source:
- docs/admin/admin-auth.js: remembered landerwareOwnerSession / X-LanderWare-Owner-Session; schedule.910cpr.com legacy calls still require sessionStorage.hotSyncAdminKey and return 503 locally when absent. A legacy denial preserves the remembered session.
- docs/admin/financial.html: API_BASE https://schedule.910cpr.com/admin/finance; still includes an owner-key form calling helper.set, which does not install a different credential.
- worker/finance-worker.js: HOT_SYNC_ADMIN_KEY authority and X-Hot-Sync-Admin-Key only; CORS excludes the remembered-session header.
- worker/admin-api.js: legacy Hot Sync/inbox authorization remains key-only.
- worker/finance-api.js: separately requires Stripe configuration before route selection.
- docs/data/admin_people.json, admin_payables.json, admin_schedule.json, admin_availability.json, admin_location_catalog.json, admin_locations_search.json, admin_locations.json, admin_client_catalog.json and docs/data/admin/scheduling_landscape.json remain tracked static files. Existence is confirmed; sensitive contents were not printed. This checkpoint does not prove removal of public exposure.

## Validation
Local command: node --test tests/finance_auth_boundary.test.mjs tests/admin_auth.test.mjs tests/owner_access.test.mjs tests/owner_access_ui.test.mjs tests/admin_api.test.mjs
Result: 40 tests, 40 pass, 0 fail.
node --check docs/admin/admin-auth.js and node --check tests/finance_auth_boundary.test.mjs passed.
Initial new route test failed 503 versus expected 404 because the local fixture lacked Stripe configuration. Added unused local fixture; no network was involved. Removed trailing blank line detected by diff check. No production/browser proof or CI result claimed.

## Preservation and exact limitations
Original E:\GitHub\910cpr-class-landers untouched: unrelated dirty files and assignments preserved. Fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and corrupt origin/codex/group-training-experience reference. No repair, cleanup or reset attempted. Separate shallow checkout E:\GitHub\910cpr-issue215-20261012 bypasses this local Git blocker. Windows case collisions leave docs/Earl/index.html and docs/Jackson/index.html dirty in that checkout; neither staged nor changed intentionally.

Only test file and this receipt are intended changes. No generated output or broad builder. Existing PRs reviewed; #218 is the historical helper PR and #372 is the separate active Studio stream. Neither changed, merged nor deployed. No new competing deep implementation stream or PR created. Queue swept; existing backend/fleet/payment assignments retained, not opportunistically rewritten.

## Remaining work and next action
Issue 215 is not complete. This is a local backend boundary checkpoint, not an implementation of the remaining connection. Coordinate an owner-session validator and CORS migration across Finance and legacy Hot Sync/inbox before sending owner sessions there. Preserve separate automation/corporate lanes and fail closed. Then prove remembered access through those actual pages, lock/back-forward cleanup and real protected reads; do not test payment writes merely to prove authentication. Separately migrate private static data, define individual roles and production observation. No authenticated owner browser session was available or used in this run; production accepted-session proof remains unperformed. Account action has not been established as necessary; do not ask Brian to copy secrets based on this checkpoint.

Persistent evidence: existing session implementation BUILT and locally regression-validated this run; historical September 14 live API proof is recorded in #215 but is not current health evidence. Current last successful end-to-end proof, monitoring cadence, observer health and escalation automation were not established. No HEALTHY/MONITORED claim. Recovery begins with coordinated source migration and authorized session verification, not removal of authentication. Brian must not become the routine monitoring layer.

Publication: test and receipt committed/pushed on this named branch; no merge, deployment, or public repair completion claimed. Final pushed SHA and GitHub receipt readback are reported in issue/chat after push. No ops/handoff/next_task.md used.
