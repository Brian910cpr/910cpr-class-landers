# Codex Reply — Issue371 canonical recovery filters, October 10 R1

Branch: codex/issue371-supervisor-proof-20261010. Existing PR372 stays draft/unmerged/undeployed. This increment continues the existing Customer Interaction Studio backend; no duplicate CRM or schema added.

Changed in repo, validated locally: supabase/functions/customer-interactions/handler.ts now permits canonical UUID case_id and interaction_id filters on interactions/tasks collection GETs. They compose with existing bounded keyset pagination and status filters. Interaction lookup maps to primary id; tasks use the canonical interaction_id relation. Invalid UUIDs, duplicated parameters and unsupported receipt filters fail before storage. Owner-session auth, caller verification boundaries and no-store responses unchanged.

Important review files: supabase/functions/customer-interactions/handler.ts; tests/customer_interaction_pagination.test.mjs; docs/CUSTOMER_INTERACTION_STORAGE.md. No UI connection, migration, API privilege, origin allowance or production deployment changed. A lookup never verifies a caller or guesses customer linkage.

Validation from D:/Users/ten77/Documents/910cpr-issue371-interrupt:
PGLITE_MODULE=file:///C:/Users/ten77/Documents/Codex/2026-10-10/codex-p0-diagnostic-repair-automatic-instruction/work/pg-proof/node_modules/@electric-sql/pglite/dist/index.js
node --experimental-strip-types --test --test-reporter=dot tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/admin_auth.test.mjs
Result: 35 passing dots, exit0. Existing SQL suites execute real migrations/RPCs in local PGlite; new endpoint tests use injected REST fixtures. Deno check supabase/functions/customer-interactions/index.ts: exit0. git diff --check: exit0. Remote PostgREST/UI verification is not claimed.

Remaining gate: owner must identify authorized isolated Supabase preview project and allowed preview origin before deploying/wiring the existing UI. Retention/deletion and operational UI autosave/conflict/retry proof remain open. No production credentials requested as a substitute.

Monitoring is being separately tested in this desktop session: existing ChatGPT Delta Watch and Deep Stability Review updated, original duties/schedules verified. Delta baseline independently read fresh health. Actual idle launcher33536 stopped at2026-10-10T22:13:39Z; a one-time safety guard19520 restores the same loop by23:28:39Z. No new automation. Stopped/scheduled-alert/recovery acceptance remains PENDING in this checkpoint; final monitoring receipt must record the actual result, never infer success from configuration or this manual baseline. Task push notifications are configured; device receipt remains a separate evidence boundary.

Unrelated docs/Earl/index.html, docs/Jackson/index.html and supabase/.temp/ excluded. No Codex_Read created/renamed. Preserve all assignments. Full pushed commit recorded in final session/issue checkpoint.
