# Issue #371: first durable storage increment

Branch: `feat/customer-learning-studio-20261010`, existing draft PR #372. Evidence state: BUILT and validated locally; not deployed or connected to the existing UI.

## Design decision

The operating problem is preserving customer work across interrupted calls, reloads and concurrent tabs. Existing Enrollware migration records already separate people, registrations and source provenance. Their operational lesson is to retain identity and history rather than recreate a customer from a contact label. This increment uses the existing canonical `landerware_people` table, nullable until identity is verified; it creates no competing customer directory and introduces no Enrollware dependency. Customer case, interaction, follow-up task and immutable save-event objects remain distinct. Many interactions may share one case. Caller name/number is unverified document content, never an automatic person merge.

`supabase/migrations/20261010210607_customer_interaction_storage.sql` creates the tables and transactional `save_customer_interaction` RPC. All four tables enable RLS and deny anon/authenticated access. The RPC is SECURITY INVOKER, callable only by service_role. The owner endpoint validates a revocable existing owner browser session before using the server-side database credential. Corporate sessions and legacy automation keys are denied. Raw customer content is never interpreted as instructions.

Each save carries a stable request UUID, interaction/case UUID, expected version, manual source ID and document. Request retries return the original receipt; changed payload under the same ID conflicts. A stale version conflicts instead of silently overwriting a second tab. Source identity is unique and immutable. Notes and previous documents survive in append-only save events with a server-derived session fingerprint and timestamp. Database failure rolls back both records and audit. No outbound action can be executed by this API.

## Current boundary and next steps

The existing `docs/admin/customer-learning.html` still uses sessionStorage and remains explicitly labeled prototype. Do not use it for durable operational capture yet. Follow-up task schema is present but task mutation/list endpoints, automatic NEXT selection, atomic interrupt+resume across two records, retention/deletion controls, pagination and browser draft-conflict recovery are still required. Existing Production Board attention stays read-only; no duplicate tasks are generated.

Next session: continue PR #372, add task/interrupt transaction APIs and tests, then connect the existing UI with explicit pending/save/error/retry/conflict states. Add `customer-interactions` to the existing admin-auth service allowlist only as part of that UI connection. No Gmail/Fieldy/PBX ingestion, personal Tasks import, universal learning, or reminders are connected by this increment.

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
