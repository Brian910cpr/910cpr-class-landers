# Issue #371: first durable storage increment

Branch: `feat/customer-learning-studio-20261010`, existing draft PR #372. Evidence state: BUILT and validated locally; not deployed or connected to the existing UI.

## Design decision

The operating problem is preserving customer work across interrupted calls, reloads and concurrent tabs. Existing Enrollware migration records already separate people, registrations and source provenance. Their operational lesson is to retain identity and history rather than recreate a customer from a contact label. This increment uses the existing canonical `landerware_people` table, nullable until identity is verified; it creates no competing customer directory and introduces no Enrollware dependency. Customer case, interaction, follow-up task and immutable save-event objects remain distinct. Many interactions may share one case. Caller name/number is unverified document content, never an automatic person merge.

`supabase/migrations/20261010210607_customer_interaction_storage.sql` creates the tables and transactional `save_customer_interaction` RPC. All four tables enable RLS and deny anon/authenticated access. The RPC is SECURITY INVOKER, callable only by service_role. The owner endpoint validates a revocable existing owner browser session before using the server-side database credential. Corporate sessions and legacy automation keys are denied. Raw customer content is never interpreted as instructions.

Each save carries a stable request UUID, interaction/case UUID, expected version, manual source ID and document. Request retries return the original receipt; changed payload under the same ID conflicts. A stale version conflicts instead of silently overwriting a second tab. Source identity is unique and immutable. Notes and previous documents survive in append-only save events with a server-derived session fingerprint and timestamp. Database failure rolls back both records and audit. No outbound action can be executed by this API.

## Current boundary and next steps

The existing `docs/admin/customer-learning.html` still uses sessionStorage and remains explicitly labeled prototype. Do not use it for durable operational capture yet. Task mutation/list and atomic interruption/resume backend contracts are implemented below. Automatic NEXT selection, retention/deletion controls, pagination and browser draft-conflict recovery are still required. Existing Production Board attention stays read-only; no duplicate tasks are generated.

Next session: continue PR #372, validate the transaction APIs in an authorized isolated preview, then connect the existing UI with explicit pending/save/error/retry/conflict states. Add `customer-interactions` to the existing admin-auth service allowlist only as part of that UI connection. No Gmail/Fieldy/PBX ingestion, personal Tasks import, universal learning, or reminders are connected by this increment.

Validate the additive migration and Edge Function in an authorized isolated preview before applying either to production. A preview browser origin must be explicitly authorized without widening production owner access. Deploy the Edge Function with the existing custom owner-session authorization arrangement (platform JWT verification settings must match existing owner endpoints); do not change secrets or shared auth. No production schema or function mutation was performed by this assignment. Supabase read-only schema discovery succeeded; no Supabase login is currently blocking work.

## Reproduce local tests

Install `@electric-sql/pglite@0.3.14` in a scratch directory, not as a production dependency. Set `PGLITE_MODULE` to the file URL of its `dist/index.js`, then run:

```powershell
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs
node --test tests/codex_wake.test.mjs
node --experimental-strip-types --test tests/admin_auth.test.mjs
deno check supabase/functions/customer-interactions/index.ts
```

10 new storage tests, 4 launcher tests and 10 existing owner-auth tests passed. SQL executed against local Postgres WASM, including real constraints, grants, function execution, retries and transaction rollback. This is local behavioral proof, not remote preview or deployed proof.

## Atomic interruption and follow-up backend increment (October 10, 2026)

Local evidence only: BUILT. No migration/function deployment or UI connection. Existing PR #372 remains draft. The original sessionStorage UI must not be used as durable operational capture.

The owner-session endpoint accepts these additional POST envelopes (all request IDs and record IDs are UUIDs):

```json
{
  "request_id": "stable UUID retained for retries",
  "operation": "interrupt",
  "input": {
    "previous": {"id": "existing interaction UUID", "case_id": "existing case UUID", "expected_version": 1, "kind": "email", "status": "paused", "source": "manual", "source_id": "original immutable source ID", "document": {"callNotes": "full checkpoint", "selection": "reply"}},
    "active": {"id": "new call UUID", "case_id": "new unverified case UUID", "expected_version": 0, "kind": "phone", "status": "in_progress", "source": "manual", "source_id": "new source ID", "document": {"callNotes": "raw caller notes"}}
  }
}
```

`interrupt` requires an existing eligible previous interaction and a new phone interaction/new case with no person linkage. Caller ID is not verification. Pausing and opening the call are one transaction, including immutable note events. If either write fails, neither is committed. UUID locks are acquired in consistent order and share the single-record save lock family. Retries with the same request ID/input/session return the original switch receipt. Changed request data or actor conflicts. The server overwrites the input operation with the validated envelope operation.

For `operation: "resume"`, use the same previous/active IDs and current expected versions, set previous status to `in_progress`, set active status to `resolved`, `follow_up_due`, `awaiting_data` or `awaiting_approval`, and include `input.interrupt_request_id` referencing the successful interrupt request. The previous record must still be paused and the active phone must still be in progress. A wrong pair, stale version or repeat disposition cannot silently overwrite work. A unique index prevents two resume events for one interruption. This is disposition bookkeeping, not evidence that an external action was executed.

GET now returns `{interactions, interruptions, tasks, limit: 100}`. Immutable interruption receipts retain the link and checkpoint through reload. All three lists are bounded; pagination and an older-paused-case recovery query remain necessary before large-scale operational use. Existing Production Board attention is untouched and is never marked complete by this API.

For task mutation use `operation: "save_task"`, `request_id`, and `input` containing `id`, `case_id`, `interaction_id`, `expected_version`, `source_key`, `title`, `status`, `provenance: {evidence: "original source evidence"}`, optional `due_at`, and `completion_evidence` when completing. Status is `proposed`, `pending`, `snoozed` or `complete`. Snoozing requires a due timestamp. A stable source_key deduplicates obligations; unrelated obligations need different keys. The interaction must belong to the submitted case. Case/interaction/source/provenance become immutable after creation. Completion requires an explicit owner statement or cited authoritative evidence, retained in the immutable event input; it never changes an external Production Board record. No reminders or background recognition are connected.

New migrations, in order:
- `supabase/migrations/20261010211804_customer_interaction_interruptions.sql`
- `supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql`

Both RPCs use SECURITY INVOKER and an empty search_path, with execute granted only to service_role. New audit tables enable RLS, deny anon/authenticated access and permit only select/insert to service_role. No secrets or raw customer data enter browser assets or global model policy. The design continues native case/interaction/task separation without adding an Enrollware dependency.

### Validation and preview gate

Scratch dependency location for this run: `C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js`, version 0.3.14. No production dependency was added.

```powershell
$env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/admin_auth.test.mjs
npx --yes deno check supabase/functions/customer-interactions/index.ts
git diff --check
```

29 tests pass, zero failures; type-check passes. SQL tests execute the real migrations/RPCs/grants in local Postgres WASM. Coverage includes atomic save/reload/resume, failure of the second write with full rollback, stale tabs, lost responses, changed retry actor/payload, unknown caller isolation, wrong resume pair, follow-up source deduplication, provenance immutability and completion evidence. Local SQL catalog checks and permission-denial tests are the security check for this undeployed increment; remote advisors have not run because no isolated target is identified.

Preview remains gated on an identified authorized isolated Supabase project and permitted browser origin. Existing `_shared/owner-auth.ts` accepts only production 910CPR origins; this increment does not widen them. No preview target/config.toml exists in this worktree. The owner has been asked which preview target/origin is authorized. Production credentials are not a substitute for that decision. Next: validate migrations/function and real owner-session requests in that preview, then wire the existing UI with autosave/retry/conflict recovery and feature gating; do not merge/deploy PR #372.

Operational proof contract: expected outcome is one owner-authorized interrupt/disposition with both records/audit retained across reload. Cadence is on demand; no background worker is claimed. Last proof is local SQL testing on October 10; no remote end-to-end proof exists. Failure is a denied/failed transaction, conflict, missing receipt or mismatched persisted versions. Automated preview observer/observer health are not yet established, so this is not MONITORED/HEALTHY. Recovery is retain the pending request/draft, retry the identical request after transient failure, or reload/reconcile on conflict; never auto-overwrite. Preview/environment authorization requires owner/account decision; ordinary code/test repairs remain Codex work. Brian must not become the routine monitoring layer when the UI is connected.
