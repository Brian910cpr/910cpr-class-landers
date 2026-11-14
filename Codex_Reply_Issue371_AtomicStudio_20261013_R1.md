# Issue 371 — gated atomic Studio interruption/resume

- Timestamp: 2026-10-13 America/New_York (UTC-04:00).
- Assignment: https://github.com/Brian910cpr/910cpr-class-landers/issues/371
- Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
- Work branch: codex/issue371-interrupt-ui-20261013; existing PR branch: feat/customer-learning-studio-20261010.
- Base: 468c76909a10d2e8ab62a32979dce2eef9b384bb.
- Substantive commit: 16bfb2d191e0f151de67d477390f1816b539078e.
- State: IN_PROGRESS / PR_OPEN. Evidence: BUILT, validated locally with synthetic browser/auth and real local Postgres SQL. Not real owner-session production proof.

## Execution and findings

Read issue body/full comments and repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md and intake workflow. Acknowledged actual execution on #371 before implementation. Preserved unrelated dirty work and all assignment/monitor state; isolated worktree E:\GitHub\910cpr-issue371-interrupt-ui-20261013 from healthy repository. E:\GitHub\910cpr-class-landers has missing handoff file on its stale checkout and previously recorded broken refs; it was not repaired/reset/cleaned. Queue title sweep found existing P0 assignments; no competing stream launched. Canonical live launcher signal observed current_task=371, execution_process_alive=true, manual_hold=false during this dispatch.

Prior gated UI had no atomic interrupt/resume connection. This increment connects the existing two-record transaction rather than approximating it with independent saves. A saved email/manual interaction may be interrupted by a fresh unlinked phone call. Resume reloads the paused record and explicitly closes the call with no follow-up. Unknown caller identity stays unverified. Source/audit semantics and native LanderWare ownership remain unchanged; no Enrollware dependency added.

Uncertain switches freeze editing/navigation and retain both drafts and the exact prepared request for retry. Malformed receipts cannot poison the cache: operation/request, pair identity, version, status, provenance/person and document checks precede acceptance. Reload recovers immutable interruption links through pagination. Conflicts retain both drafts for export, followed by reload and explicit server review; no automatic two-record merge. One interruption level only; all edits must be confirmed before switching. Follow-up/NEXT remains disabled/incomplete. Production Board attention remains read-only.

## Exact changed files / review order

1. docs/admin/customer-interaction-studio.mjs — gated atomic UI states, fresh-version resume, retained pair export, navigation/privacy guards.
2. docs/admin/customer-interaction-switch.mjs — immutable switch/retry coordinator and paginated link recovery.
3. docs/admin/customer-interaction-client.mjs — switch receipt validation before caching.
4. docs/admin/customer-learning.html — disabled rollout gate preserved; explicit no-follow-up resume control; controller URL versioned 20261013-interrupt1. Controller dependency URLs use matching version.
5. tests/customer_interaction_switch.test.mjs — four switch/recovery regression tests, including malformed pair/versions/identity/status/documents and cursor loops.
6. tests/customer_interruptions_sql.test.mjs — coordinator -> transport -> actual handler -> real local RPC composition, lost-response retry, resume and stale conflict.
7. tests/customer_interaction_studio_browser.py — eight Chromium tests total; three new atomic/recovery/conflict tests.
8. docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md — appended exact scope, limitations, evidence and next gates. Primary safety report; latest section is “Gated atomic interruption/resume — 2026-10-13”. Earlier live read-only metadata remains data/audit/issue371_patha_metadata_20261012.json; no new metadata audit was generated.
9. Codex_Reply_Issue371_AtomicStudio_20261013_R1.md — this receipt.

Relevant unchanged contracts: supabase/functions/customer-interactions/handler.ts and supabase/migrations/20261010211804_customer_interaction_interruptions.sql. No schema, auth allowlist or CORS change.

## Validation and exact commands

Reused existing scratch PGlite 0.3.14; no install. All processing/tests local except read-only GitHub/docs and authorized GitHub comments/push.

```powershell
$env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/customer_interaction_restart.test.mjs tests/customer_interaction_grants.test.mjs tests/customer_interaction_cors.test.mjs tests/customer_interaction_client.test.mjs tests/customer_interaction_checkpoint.test.mjs tests/customer_interaction_switch.test.mjs tests/admin_auth.test.mjs
python tests/customer_interaction_studio_browser.py
node --check docs/admin/customer-interaction-client.mjs
node --check docs/admin/customer-interaction-switch.mjs
node --check docs/admin/customer-interaction-studio.mjs
git diff --check
```

Full Node output summary: tests 63; suites 0; pass 63; fail 0; cancelled 0; skipped 0; todo 0. Chromium: Ran 8 tests; OK. Syntax/diff exit 0. After final document/person receipt hardening, reran the affected switch+SQL tests: tests 11; pass 11; fail 0, and all eight Chromium tests: OK; syntax/diff passed again. Initial existing browser assertion that New call stays disabled was updated to assert the intentionally enabled saved-email behavior; final checks have no failures.

The composed SQL test uses injected synthetic authorization, not real owner login or deployed Edge Runtime/PostgREST. Chromium uses intercepted synthetic endpoints/auth, not a production database. No private customer data or secrets used/committed. No generator ran. Supabase skill applied; changelog/manual CORS docs read, no SDK/API change required.

## Persistence, deployment, unrelated files

Changed in repo and persisted locally. Substantive commit plus receipt are to be pushed to the named review branch and existing PR branch without force. Receipt existence will be verified through GitHub contents API before final response. No duplicate PR, merge, production schema/API write, Edge Function deployment, gate exposure, installation or public rebuild was performed. Draft PR372 must remain draft/unmerged/undeployed; this increment does not authorize rollout.

Unrelated E: dirty files and earlier receipts/runtime artifacts remain untouched. This isolated Windows worktree exposes pre-existing case-collision differences at docs/Earl/index.html and docs/Jackson/index.html; excluded from staging/commits. No cleanup/restoration was attempted. No intentionally untracked task artifacts remain; other worktrees/assignments/monitors were not changed.

## Proof contract and remaining gates

Expected useful outcome/cadence: on-demand saved email -> atomic call interruption -> browser reload -> explicit no-follow-up resume with notes/immutable links intact. Last successful local synthetic proof: 2026-10-13 tests above. Real owner-session UI/API/database proof remains absent. Failure/staleness signals: missing/mismatched switch receipt, stale version, incomplete recovery links, unresolved notes. Local test runners detect regressions; no deployed CRM outcome observer or observer-health evidence exists. No MONITORED/HEALTHY claim. Recovery: identical request retry; conflict pair export and reload/current-server review. Owner must not become routine monitoring layer.

Exact production blockers: durable follow-up/NEXT not wired; recoverable backup/restore evidence absent; genuine owner-session UI/API/database reload/resume/conflict proof absent; separate explicit rollout GO not granted. Docker/WSL2/Synology are not prerequisites under Path A and no installation was attempted. Unconfirmed edits remain memory-only; browser closure cannot guarantee their recovery. Nested calls and in-page pair-conflict reconciliation remain limitations.

Next action for ChatGPT/Codex: review these exact source/test paths and latest safety section, keep PR372 draft/gate disabled, continue the same stream with durable follow-up task creation/status and save-confirmed NEXT. Then establish real owner-session integration and recoverable backup/restore evidence before requesting the separate minimal production GO. Do not infer authorization from arbitrary third-party comments. No Brian/account action is currently required for safe code/test continuation; production requires separate owner authorization after gates pass.
