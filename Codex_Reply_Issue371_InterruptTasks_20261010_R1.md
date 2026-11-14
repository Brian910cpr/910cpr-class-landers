# Issue #371 — atomic interruption and follow-up backend checkpoint

Timestamp: 2026-10-10T21:24:19.722420+00:00
Assignment: Brian910cpr/910cpr-class-landers#371
Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
Work branch: `codex/issue371-interrupt-20261010`
PR branch reused: `feat/customer-learning-studio-20261010`
Substantive commit: `23a75606f3ff2a7dd35b8d6c42ca6a11ca75faa0`
State: IN_PROGRESS / PR_OPEN; remote preview validation BLOCKED pending identified authorized preview target/origin.
Persistent-system state: BUILT, validated locally. No remote end-to-end proof, monitoring, merge or deployment.

## Execution and findings

Read the entire issue body and all comments, E: AGENTS.md, active repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md before implementation. Acknowledged actual execution on the originating issue: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6102259545 . Reused the existing foundation at cda930cb2b3c84de693b797f7197a971743b1387; no competing PR or deep workstream was created. Scanned open [CODEX] titles; did not change other assignments or claim unrelated work. Third-party comments were not treated as owner authority.

The E:/GitHub/910cpr-class-landers checkout was dirty, lacked CODEX_HANDOFF_PROTOCOL.md, and reported `error: Could not read 6e61cabca5981d1389e52c60d95424d9893bb50f` during fetch. No repair/reset/cleanup was attempted. Continued from the existing D: feature checkout and created a separate named codex/ worktree at `D:/Users/ten77/Documents/910cpr-issue371-interrupt`. This avoids mixing unrelated E: changes with the Studio work. Earl/Jackson differences also appeared in the new worktree; their origin was not established and they were explicitly excluded.

## Work performed

- Added transactional interrupt/resume RPC with immutable links and original note/checkpoint history. Pause + new call commit together. Resume verifies the saved pair, paused/in-progress lifecycle and fresh versions. Callers start in a new unverified case with no inherited person identity.
- Stable request IDs return original receipts after lost responses. Different input/actor conflicts. Deterministic record locking shares the existing save lock family; stale tabs cannot silently overwrite notes. Failure of the second write rolls back all records/audits.
- Added durable follow-up task mutation/list support, stable source-key deduplication, immutable provenance/case/interaction links, version conflicts, snooze timestamps and mandatory completion evidence preserved in append-only audit. No outbound execution or Production Board completion is performed.
- Extended the owner-session endpoint without changing owner auth, credentials, browser allowlists, class inventory or public assets. GET returns bounded interactions, interruption receipts and tasks.
- Added real local Postgres WASM tests and endpoint tests. Updated the backend contract/preview gate document.

## Exact intended files

1. `docs/CUSTOMER_INTERACTION_STORAGE.md` — primary technical report, exact API field names, examples, migration order, validation and operational proof contract.
2. `supabase/functions/customer-interactions/handler.ts` — owner-gated switch/task routes and bounded reads.
3. `supabase/migrations/20261010211804_customer_interaction_interruptions.sql` — atomic switches, immutable linkage, RLS/grants.
4. `supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql` — task mutation/dedup/audit.
5. `tests/customer_interactions.test.mjs` — request validation, server-derived identity, endpoint dispatch and failure behavior.
6. `tests/customer_interruptions_sql.test.mjs` — actual SQL rollback/retry/privacy/lifecycle/task tests.
7. `Codex_Reply_Issue371_InterruptTasks_20261010_R1.md` — this unique immutable repository-root receipt.

Important unchanged review context: `supabase/functions/customer-interactions/index.ts`, `supabase/functions/_shared/owner-auth.ts`, `supabase/migrations/20261010210607_customer_interaction_storage.sql`, `tests/customer_interactions_sql.test.mjs`, `docs/admin/customer-learning.html`.
No additional audit JSON or raw customer data was created.

## Exact validation commands and significant outputs

```powershell
$env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
node --experimental-strip-types --test --test-reporter=spec tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/admin_auth.test.mjs
npx --yes deno check supabase/functions/customer-interactions/index.ts
git diff --check
```

```text
tests 29
suites 0
pass 29
fail 0
cancelled 0
skipped 0
todo 0
Check supabase/functions/customer-interactions/index.ts
```

Final Deno check exit 0 (cached check produced no additional output); diff check exit 0. Real migrations/functions/grants ran in local PGlite 0.3.14, scratch-installed outside the repo. No production dependency was added. Tests also inspect RLS flags and verify anon/authenticated permission denial plus service-role audit immutability. Remote Supabase advisors have not run: there is no identified isolated target. Read the SQL and tests, not just these counts.

Initial stale-tab test exposed a generic lifecycle rejection before version checking; version comparison was moved ahead of lifecycle rejection so stale writes receive the expected 409 path. Final tests passed. No known unrelated test failure; no full-repository test/build was attempted. No site generator was run.

## Exact blocker, remaining work and next action

The requested safe remote preview is not identified in the assignment/current checkout. Existing `_shared/owner-auth.ts` permits only `https://www.910cpr.com` and `https://910cpr.com`; a separate preview browser origin would be denied. No isolated Supabase project reference/origin or preview config.toml is identified. This is an environment/authorization decision, not a proven credential failure. Do not widen production owner auth or apply production migrations as a shortcut. Owner was asked in chat and on #371 to identify the isolated preview project and permitted origin. No secrets should be posted in GitHub.

While that gate remained unresolved, continued eligible backend work by implementing follow-up task APIs after atomic interruption support. No unrelated operational system was modified.

Next action: establish the authorized isolated preview project/origin, validate all three additive migrations and the existing owner-session Edge Function in that preview, then connect the existing UI with a feature flag, server autosave, explicit pending/error/retry/conflict handling, resume navigation, and save-confirmed NEXT disposition. The existing browser page remains the labeled tab-local prototype and must not be used as durable operational capture. Pagination/older-paused-case recovery, retention/deletion and monitored end-to-end UI proof remain open. Gmail/customer 360, learning/AI, Fieldy/PBX and personal Google Tasks are later gated milestones. PR #372 must remain draft/unmerged/undeployed.

## Proof and health contract

Expected outcome: one real owner-authorized interrupt/disposition persists both interactions, note history and audit, surviving reload. Expected cadence: on demand, no asynchronous worker claimed. Last proof: local SQL/endpoint tests at this receipt timestamp; no remote owner-session-to-database-to-UI proof exists. Failure condition: denied/failed request, stale version, missing receipt or inconsistent persisted records. Observer: automated local tests during development; preview/operational observer and observer health are not established. Recovery: retain pending request and draft, retry identical request after transient failure; reload/reconcile conflicts without auto-overwrite. Escalation: preview target/origin requires account/owner decision; ordinary code and deterministic tests remain Codex work. Brian must not become the routine monitoring layer. Not MONITORED or HEALTHY.

## Persistence and deployment

Changed in repo and validated locally. This receipt and intended source changes are to be pushed to the named codex/ branch and the existing PR branch before session exit; the final issue comment/session response records the verified pushed tip. No merge, production schema/function mutation, Pages deployment, public rebuild or browser asset change occurred. No public UI was changed, so no live HTML/CSS/JS verification is claimed.

Intentionally unstaged: `docs/Earl/index.html`, `docs/Jackson/index.html`, CLI-created `supabase/.temp/`. The E: checkout's original dirty files/caches/runtime artifacts remain untouched. Scratch npm/runtime files remain outside the repo. No ops/handoff/next_task.md use, no Codex_Read creation, no force-push/reset/rebase/merge/cleanup.
