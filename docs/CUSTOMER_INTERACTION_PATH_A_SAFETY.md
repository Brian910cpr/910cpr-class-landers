# Issue 371 Path A safety audit — 2026-10-12

State: IN_PROGRESS / PR_OPEN. CRM evidence level: BUILT, locally validated. Production rollout: NO-GO pending remaining gates. Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372 . No production write, function deployment, UI exposure, merge, installation or reboot occurred.

## Live read-only evidence

`data/audit/issue371_patha_metadata_20261012.json` contains the exact catalog query and sanitized results observed at 2026-10-12 13:42:03.729321+00. Project `wktwgcnwdvbebcobgyey` is the existing LanderWare project; server version 17.6. No customer rows, owner tokens, grants containing identities, or secrets were read.

- Six proposed tables and three RPC names are absent in the live public catalog. `customer-interactions` is absent from the deployed function list. This is a point-in-time no-collision check, to repeat immediately before any approved rollout.
- `landerware_people.id` exists as UUID; the proposed nullable case foreign key matches. No legacy person, registration, class or scheduling table is modified. A separate `customers` identity system also exists; no automatic cross-directory merge is authorized or added.
- `owner_access_grants` and `owner_browser_sessions` exist with RLS enabled, no public policies, and service-role access. Existing deployed `owner-access` v5 uses `verify_jwt=false` and the revocable custom browser-session scheme. Its retrieved `_shared/owner-session.ts` matches the reviewed source in behavior: SHA-256 token lookup, session and grant expiry/revocation checked on each request. No real owner-session integration request was made.
- Default table ACLs for both postgres and supabase_admin in public grant ALL to anon, authenticated and service_role. Default functions grant EXECUTE. This matters even when a later GRANT names a smaller set: GRANT is additive.

## Security defect reproduced and corrected locally

The original migrations revoked anon/authenticated/PUBLIC, then granted SELECT/INSERT to service_role on audit tables. Under actual live defaults this retained UPDATE, DELETE and TRUNCATE on immutable history. Existing local fixtures did not model those defaults.

`tests/customer_interaction_grants.test.mjs` reproduces production-like table/function defaults. Before the correction it failed with:

```text
service_role UPDATE customer_interaction_events
true !== false
# tests 1
# pass 0
# fail 1
```

All three UNAPPLIED CRM migrations now revoke service_role alongside PUBLIC/anon/authenticated before their explicit grants. This also strips unnecessary DELETE/TRUNCATE/REFERENCES/TRIGGER from mutable CRM tables. Final rights: SELECT/INSERT/UPDATE on operational tables, SELECT/INSERT on three audit tables, EXECUTE only to service_role on three SECURITY INVOKER RPCs with empty search_path. No global default privilege changes or shared auth changes. Audit remains protected against application service-role mutation, not against a database owner/admin, who inherently controls the database.

Exact edited migrations:
- `supabase/migrations/20261010210607_customer_interaction_storage.sql`
- `supabase/migrations/20261010211804_customer_interaction_interruptions.sql`
- `supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql`

Editing these pending migrations is justified by live absence of the objects. If another environment has already applied them, do not replay/rewrite its history; prepare a separate corrective migration for that environment.

## Reviewed safeguards and remaining gaps

`supabase/functions/customer-interactions/index.ts` requires the custom owner-session header before invoking shared authorization; a legacy automation key or corporate-only session cannot enter the CRM. The service credential remains server-side. Handler assigns actor from the session hash; client author fields do not authorize. All responses are no-store. Customer content is JSON data, never an executable instruction. Only manual capture is accepted; no email/send/refund/reschedule/payment/eCard operations exist.

RPCs keep stable request receipts, actor/input checks and expected versions; interrupt/resume atomically writes both interactions and histories. Task provenance/source identity is immutable, duplicate source keys conflict and completion requires evidence. SQL failures roll back record and audit together. Session-fingerprint idempotency means a renewed/new browser token cannot replay a prior token's request: UI must reconcile stored state instead of generating a fresh write automatically after session replacement.

CORS currently returns www.910cpr.com for every response while shared authorization permits both www and apex. Apex browser use would fail CORS; choose the existing canonical www owner surface or implement/test origin reflection restricted to the SAME two existing origins. Do not widen origins. No owner credential should be sent to an unapproved preview URL. `docs/admin/admin-auth.js` does not yet allow customer-interactions. Existing `docs/admin/customer-learning.html` remains tab-local/sessionStorage; dashboard link alone is not durable UI integration. UI feature gate, autosave/retry/conflict retention and save-confirmed NEXT remain implementation work. Production Board attention must stay read-only.

## Minimal intended rollout, NOT executed

1. Finish feature-gated integration in the existing Studio; smallest UI files are `docs/admin/customer-learning.html`, `docs/admin/admin-auth.js` and, only if needed for gate/navigation, `docs/admin/dashboard.html`. Version changed assets. Keep flag OFF by default. No public lander generators.
2. Repeat metadata/collision/security review at the final commit, inspect external dependencies on the six names, and prove synthetic owner-session UI/API/database reload, interruption/resume, failed-save/retry and cross-tab conflicts. Local PGlite is SQL evidence only; it does not prove Edge Runtime/PostgREST/browser integration.
3. Verify an actual recoverable production backup/export and its timestamp/storage/access without exporting customer data to GitHub. Backup existence, restore capability, RPO/RTO and permitted secure export location have NOT been established by current tools/evidence. A plan alone does not clear this gate.
4. After explicit separate owner GO for the reviewed commit: apply ONLY the three listed CRM SQL files in order, recording applied versions. Do not run a broad `db push` including unrelated pending migrations. Verify final catalog grants/RLS/RPC definitions before enabling the endpoint.
5. Deploy ONLY customer-interactions with the reviewed custom-session authorization (`verify_jwt=false`, consistent with owner-access), existing secret bindings untouched. First test absent/expired/revoked/foreign/corporate access denial and synthetic namespaced CRM data; never use genuine customer data as fixtures. Synthetic IDs/source keys must be recorded in a private test manifest, with no person linkage or outbound actions.
6. Only under separately approved UI exposure/merge scope, enable owner-only flag at the canonical www domain and verify referenced HTML/JS plus save/reload/resume at the browser surface. Keep PR372 draft until integration/security evidence and express merge authorization.

Exact proposed approval boundary after steps 1–3 pass: “GO for the reviewed commit: apply only the three named additive CRM migrations and deploy only customer-interactions to LanderWare wktwgcnwdvbebcobgyey, for synthetic owner-session proof; leave UI flag OFF, PR372 draft/unmerged, and all other infrastructure unchanged.” A later UI/merge GO must be separately explicit. **This is a future approval request template, not a request to approve an incomplete safety gate now.** Current recommendation: NO-GO; continue code/tests without production writes.

## Backup / reversal / recovery

Before rollout, record schema/function versions, migration hashes and restorable backup evidence. Each migration is transactional; failure of one rolls back that migration, not previously committed migrations. Stop on any unexpected object or ACL. The three files add six tables, three functions and indexes; only the new task table is altered by file three. Existing canonical people are referenced, never edited.

After endpoint/UI trouble, first disable the new feature flag and withdraw ONLY customer-interactions; preserve CRM records/audit. Do not rollback by dropping tables after operational writes. Before any destructive removal require a verified private export, dependency review and explicit authorization. Never use CASCADE or restore the entire production database for an isolated CRM defect. If empty pre-use objects must be removed, prepare separately reviewed reverse-order exact-object SQL; no removal SQL was executed or authorized here. Synthetic cleanup must be narrowly scoped and preserve meaningful audit; unrestricted service-role deletion is intentionally unavailable.

## Validation

Scratch PGlite 0.3.14 reused, no production dependency added:

```powershell
$env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/customer_interaction_restart.test.mjs tests/customer_interaction_grants.test.mjs tests/admin_auth.test.mjs
node --check tests/customer_interaction_grants.test.mjs
npx --yes deno check supabase/functions/customer-interactions/index.ts
git diff --check
```

Results: 38 tests, 38 pass, zero fail; JS syntax, Deno type-check and diff check passed. Includes production-default ACL regression, SQL transactions, restart persistence, retries, stale tabs, unknown caller isolation, follow-up completion/provenance, pagination and owner-auth privacy. No production integration or backup restore proof.

Current Supabase changelog and API security docs fetched read-only; the API security guide explicitly describes automatic default grants and separate grant/RLS layers. References: https://supabase.com/changelog.md and https://supabase.com/docs/guides/api/securing-your-api.md . No SDK/API change was introduced.

## Operational proof boundary / next action

Expected useful outcome: owner captures a call or email, server receipt survives browser closure, interrupt/resume preserves notes and real follow-up status. Cadence: on demand. Last successful proof: local synthetic SQL suite 2026-10-12; real owner UI/API/database proof remains absent. Failure: missing receipt, error, version conflict, inaccessible stored work or retained pending draft. Recovery: preserve request/draft, identical retry on transient failure, reload/reconcile on conflict; never silently overwrite. CRM outcome observer and observer health are not yet implemented; do not claim MONITORED/HEALTHY or require Brian to check routinely. Existing Codex Wake signal showed task371 running at 13:42:02Z; launcher/assignments/observers untouched.

Next safe work: feature-gated durable UI wiring and runtime integration harness; complete actual backup/recovery evidence before requesting GO. No Docker/WSL/Synology prerequisite request for this milestone. Owner-level action will be needed for the separate production GO only after remaining gates clear, and for backup access if no authorized read-only route can establish recovery evidence. No secrets should be posted.
