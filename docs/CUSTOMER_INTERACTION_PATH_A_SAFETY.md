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

## CORS follow-up — 2026-10-12

The prior CORS mismatch is corrected in the unapplied customer-interactions handler. Exact existing www/apex origins receive matching Access-Control-Allow-Origin and Vary: Origin on preflight, success, authorization denial and storage failure. Foreign/opaque/lookalike/local/preview origins receive 403 before authorization/storage and no allow-origin header. Origin-less clients still require authorization. No origins were added, shared auth changed, or function deployed.

Validation: 42 CRM/auth tests passed, zero failed, including four new CORS tests in tests/customer_interaction_cors.test.mjs; Node syntax, Deno check and git diff --check passed. This is local handler/synthetic SQL evidence, not browser/Edge Runtime integration. Current Supabase changelog and manual CORS documentation were fetched read-only; no SDK/config migration was needed.

Production remains NO-GO: recoverable backup/restore evidence, feature-gated durable UI, and real owner-session browser/API/database reload/resume/conflict proof are outstanding. Continue those same-stream prerequisites before asking for the separate production GO.

## Prepared browser transport — 2026-10-12

`docs/admin/customer-interaction-client.mjs` prepares the existing manual interaction/task/switch envelopes and paginated reads. Default enabled=false fails before any request. It is deliberately not imported by any page and does not change admin-auth's endpoint allowlist. This is a staged integration component, not durable UI delivery or a production flag implementation.

The client takes the existing admin-auth object; credentials are handled only by that helper. Each prepared write snapshots one request UUID, serialized input, and auth generation. Explicit retries reuse that exact envelope; overlapping sends coalesce; confirmed receipts are cached and copied before returning. A 4xx becomes terminal for that prepared write; 409 requires reconciliation. Transport/5xx/invalid-receipt failures retain the envelope for explicit retry. Replacement sessions cannot replay old writes or accept late responses. Reads preserve server cursor precision and distinguish empty results from load failures. No customer notes, tokens or pending envelopes are stored in browser storage by this module. Unsaved in-memory work still does not survive browser closure; crash recovery remains a UI/server checkpoint requirement, not a claimed capability here.

`tests/customer_interaction_client.test.mjs` adds seven tests, including the actual handler with synthetic storage: a response lost after commit is retried without a second logical write, while a separate stale writer receives 409. This harness uses injected authorization/storage; it does not prove real owner login, Edge Runtime/PostgREST or database persistence. Existing SQL/disk-reopen tests separately prove the database contracts locally.

Validation: existing CRM/auth suite plus six initial client tests passed 48/48; final seven client tests passed 7/7 (49 unique tests overall). Node syntax and diff checks passed. Reproduce with `node --experimental-strip-types --test tests/customer_interaction_client.test.mjs` plus the CRM/auth command above with `tests/customer_interaction_cors.test.mjs`. No dependencies, migrations, generated pages, shared auth or deployed assets changed. Current Supabase changelog and CORS docs were read; the announced TLS cipher retirement requires modern TLS, not a client SDK or custom-session change. References: https://supabase.com/changelog.md and https://supabase.com/docs/guides/functions/cors .

Next: integrate this transport with the existing Studio behind a default-off owner feature gate; add allowlisting only with that connection, version referenced assets, replace tab-local operational state with server checkpoints, and prove save/reload/interruption/conflict/error recovery at the browser surface. Preserve unresolved drafts on errors and reconcile before replacing request IDs. Keep Production Board items read-only. Production gate remains unchanged: actual recoverable backup evidence and real owner-session UI/API/database proof are absent; separate explicit production GO still required. No owner action required for continued safe code/test integration.

## Prepared checkpoint coordination — 2026-10-12

`docs/admin/customer-interaction-checkpoint.mjs` composes the prepared transport without loading it into a page or changing the owner endpoint allowlist. Server-confirmed identity/version, not draft generation, determines saved state. Edits made while a checkpoint is pending remain dirty after its receipt; the next checkpoint uses the confirmed base version. Failed uncertain writes keep the same request envelope while later edits remain separate. Navigation/reload is guarded until all edits are confirmed. Conflicts retain the draft and require explicit reconciliation with a freshly fetched, same-identity server version before a new request can be prepared. Callers must display server changes for owner review before invoking reconcile; this module does not claim to merge text automatically. Transport failures cannot use reconcile to bypass an uncertain commit. Wrong-identity/nonadvancing receipts never confirm a save.

Validation: 55 CRM/auth tests passed, zero failed, including six new coordinator tests in `tests/customer_interaction_checkpoint.test.mjs`; Node syntax and diff checks passed. Local injected transport/handler and synthetic SQL evidence only. No DOM/browser integration, automatic autosave, new production feature flag, crash recovery, retention observer or real owner-session end-to-end proof is delivered by this increment. No notes or credentials are written to browser storage. Modules remain unloaded/default disabled. The existing tab-local prototype and production remain unchanged.

Next concrete integration: connect the existing Studio fields to coordinator edit/save/view behind a default-off owner gate, show saving/error/conflict states, prevent selection/interrupt/NEXT transitions while dirty, fetch current server work for explicit reconciliation, wire atomic interrupt/resume, and test browser reload plus failure recovery. Complete recoverable backup evidence and real UI/API/database proof before the separate production GO. Do not merge PR372 or deploy. No owner action required for this continued local implementation.

## Default-off Studio capture integration — 2026-10-12

`docs/admin/customer-learning.html` now has an explicit `landerware-durable-crm` meta gate, committed as `disabled`. Only an explicitly enabled, exact Studio path may route the existing owner session to the exact customer-interactions endpoint through `admin-auth.js`; server authorization/CORS remain unchanged. A URL parameter or storage entry cannot activate this gate. Referenced auth/controller/client/checkpoint assets are versioned `20261012-ui1`. No production flag, service deployment, schema write or origin expansion occurred.

When enabled in a controlled test response, `docs/admin/customer-interaction-studio.mjs` replaces the prototype handlers with server capture/loading, debounced checkpoints, explicit save/retry, fresh-version selection, paginated queue loading, visible unsaved/error/conflict states, explicit same-record conflict review, and navigation guards. Fetched records seed a confirmed coordinator without redundant writes. Manual phone/email capture creates fresh canonical IDs with no person linkage; entered names/numbers never verify a customer. Raw notes, plan, draft and coaching remain scoped to that interaction's document and immutable backend history. This continues the existing canonical case/interaction/audit model rather than creating another catalog or Enrollware dependency.

Durable mode never imports or writes prototype sessionStorage drafts. The disabled mode retains them; owners can export existing drafts before a later approved migration. The controller clears fields/queue on session lock. Startup/module failures keep capture disabled with an explicit retry message instead of silently falling back to local storage. Saved state requires a matching backend receipt; pending edits still can be lost on browser/process closure. Beforeunload and internal-link guards reduce this risk but do not claim crash recovery of unconfirmed edits. Checkpoint failures preserve the immutable envelope for identical retry; conflicts preserve draft text and require review of current server text/version before a new write.

This increment intentionally does not enable atomic interrupt/resume, follow-up task disposition, customer lookup/linkage or external execution. In durable mode New call is disabled once an interaction is selected; Finish and Clear are disabled. This prevents the prototype's local-only transitions from masquerading as durable operations. Existing Production Board attention stays read-only. The whole issue remains IN_PROGRESS, not a delivered usable CRM slice.

Validation on 2026-10-12: 57 CRM/auth Node tests passed, zero failed; 5 real Chromium tests passed with synthetic intercepted API responses and a synthetic owner-session fixture; JS/module/inline-script and Python syntax checks plus `git diff --check` passed. Chromium checks cover default-disabled no-CRM requests, save/reload, actual tab close/reopen after autosave, lost-response identical retry, retained conflict draft/review, dirty navigation blocking, session-lock clearing and module-load fail-closed. Desktop 1440px rendering was visually inspected using a temporary synthetic screenshot; not committed. No production requests/customer data are used in these browser tests. They do not prove real owner authorization, deployed Edge Runtime, PostgREST, or database persistence; existing local PGlite SQL tests separately cover database behavior.

Reproduce:

```powershell
$env:PGLITE_MODULE='file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js'
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/customer_interaction_restart.test.mjs tests/customer_interaction_grants.test.mjs tests/customer_interaction_cors.test.mjs tests/customer_interaction_client.test.mjs tests/customer_interaction_checkpoint.test.mjs tests/admin_auth.test.mjs
python tests/customer_interaction_studio_browser.py
node --check docs/admin/admin-auth.js
node --check docs/admin/customer-interaction-checkpoint.mjs
node --check docs/admin/customer-interaction-studio.mjs
git diff --check
```

Browser tests use the already installed Python Playwright/Chromium; no production dependency was added. Supabase changelog and current manual CORS documentation were reviewed read-only; no SDK/API convention change is introduced. Changelog: https://supabase.com/changelog.md ; manual CORS: https://supabase.com/docs/guides/functions/cors .

Evidence classification: BUILT, locally validated gated UI. Last useful browser proof: 2026-10-12 synthetic tab reopen restored confirmed notes; real owner/UI/API/database proof remains absent. Expected outcome/cadence: capture and recover confirmed interactions on demand. Failure: missing/mismatched receipt, version conflict, inaccessible records or unconfirmed edits. Local test runner observes regressions; no deployed CRM outcome observer or observer-health proof exists, so MONITORED/HEALTHY is not claimed. Recovery: identical retry, explicit review/reconciliation, reload confirmed work; export unconfirmed notes before closure. Brian must not be the routine monitoring layer when this becomes operational.

Next same-stream change: wire atomic interruption/resume and durable follow-up task/NEXT disposition into this controller with browser tests and actual handler/SQL integration, then establish real owner-session end-to-end and recoverable backup/restore evidence. Production remains NO-GO until these gates pass and a separate exact rollout receives explicit owner approval. Do not merge draft PR372, expose the gate, migrate production or deploy a function in this state. No owner action is currently required for safe local continuation.


## Gated atomic interruption/resume — 2026-10-13

The existing default-disabled Studio now connects the existing atomic switch RPC. A saved email/manual interaction can be paused and a fresh unlinked phone interaction opened in one transaction. Editing and navigation freeze until both records are confirmed. Resume fetches the current paused record and explicitly closes the active call with **no follow-up** before restoring previous work. This does not send a reply or assert external execution. Production Board attention stays read-only. Canonical cases/interactions/audit remain authoritative; no new Enrollware dependency or alternative customer directory is introduced.

`docs/admin/customer-interaction-switch.mjs` retains the immutable pair/request for identical retry, coalesces sends, and makes 4xx/conflicts terminal rather than silently preparing another transaction. The transport validates request ID, operation, both IDs/case IDs/statuses/versions, source and person linkage, and document contents before caching a switch receipt. PostgreSQL JSON key ordering is normalized for comparison. Uncertain or conflicting switches retain both drafts for explicit export; they cannot degrade into independent single-record saves. Switch conflicts currently require exporting both drafts, then reloading and reviewing current server work; automatic two-record reconciliation is deliberately absent.

Selecting an in-progress call after reload searches immutable interruption links through all pages, preserving cursor precision and rejecting repeated cursors. It fetches fresh interaction versions before resumption; stale concurrent writes are rejected by the existing RPC. Caller identity is still unverified, and new calls have null person linkage. This first integration permits one interruption level and requires confirmed edits before interrupt/resume. Nested calls, direct interruption during an unresolved save, follow-up task disposition and NEXT remain incomplete. Unconfirmed in-memory edits still do not survive browser closure; only confirmed checkpoints recover.

Changed public module references use `20261013-interrupt1`. The committed gate remains disabled. No migration, function/auth/CORS change, installation, generated-page rebuild, production write, merge or deployment was performed.

Validation: 63 CRM/auth Node tests passed, zero failures; eight real Chromium tests passed with synthetic intercepted API/auth fixtures. New tests cover atomic interrupt/reload/resume, lost interrupt and resume responses with identical retries, stale conflict retention/export, malformed switch receipts, older interruption-page recovery and cursor-loop failure. `tests/customer_interruptions_sql.test.mjs` now composes the browser coordinator, transport, actual handler and real local Postgres RPC: a response lost after commit yields one immutable switch event, retry retrieves it, reload/resume preserves notes, and a stale writer fails. After final receipt-validation hardening, 11 affected Node tests and all eight browser tests passed again. Node syntax and `git diff --check` passed.

Reproduce with the preceding full test command plus `tests/customer_interaction_switch.test.mjs`; run `python tests/customer_interaction_studio_browser.py`. Existing scratch PGlite 0.3.14 is reused; no dependencies were installed. Supabase changelog and current manual CORS docs reviewed read-only; no SDK convention changes apply to this existing custom transport.

Evidence: BUILT, locally validated; browser fixtures and local SQL composition do not prove real owner authorization, deployed Edge Runtime/PostgREST, production persistence or recoverable production backup. Expected outcome is on-demand saved email -> interrupted call -> reload -> saved no-follow-up resume with immutable links. Last local synthetic proof: 2026-10-13, tests above. Failure signals are missing/mismatched receipts, stale versions, incomplete link recovery or unconfirmed notes. Local runners observe regressions; no deployed CRM outcome observer or observer-health proof exists. Recovery is identical retry, or retained-pair export and server review after conflict. No MONITORED/HEALTHY claim. Brian must not become the routine monitoring layer.

Next: integrate durable follow-up task creation/status and save-confirmed NEXT, then complete real owner-session UI/API/database and backup/restore evidence. Production remains NO-GO; a separate explicit rollout GO is required after gates pass. No owner action required for safe same-stream code/test continuation. Keep PR372 draft/unmerged/undeployed.


## Follow-up task confirmation boundary — 2026-10-13

Safe backend preparation for the same draft PR372; evidence BUILT/local synthetic validation only. The existing save_task transport previously accepted any object as a successful task receipt. An unrelated task, partial object or wrong disposition could therefore masquerade as confirmation when a future NEXT controller used it. The client now validates task ID, case/interaction linkage, source key, title/status, exact next version, canonical provenance and due instant (including PostgreSQL microseconds and timezone equivalence) before caching. A malformed response retains the identical prepared request so a corrected replay can recover. No SQL, RPC, auth, CORS or production permission change was needed.

`docs/admin/customer-interaction-task.mjs` supplies an unloaded immutable disposition coordinator. It coalesces simultaneous sends, freezes input, preserves exact retries after uncertain failures, retains conflicts without a replacement request, and exposes canLeave only after confirmation. All 4xx failures block for reconciliation, including oversized requests. Repeated confirmed sends still consult the existing transport session fence; a replacement owner session cannot retrieve a cached private result through this helper. A future UI must also require the interaction checkpoint's canLeave, clear this helper on owner lock, and fetch fresh task versions before editing. canLeave confirms this submitted bookkeeping version, not that the row can never subsequently change in another tab. Completion evidence is retained by the existing immutable SQL event, not echoed in the task row; the client does not fabricate proof of external execution.

The canonical task/case/interaction design and mature identity/provenance rationale remain those in `docs/CUSTOMER_INTERACTION_STORAGE.md`. This increment adds no competing task authority, Enrollware dependency, manual-checklist requirement, background inference or reminder promise. Production Board attention stays read-only. The helper is not imported by the Studio; follow-up disposition and save-confirmed NEXT are still unwired. The gate remains disabled. Changed controller/client references use `20261013-task1` so a later approved rollout cannot mix the previous client with new HTML. No generator was run.

Validation: 68 CRM/auth Node tests passed, zero failed, including five new task tests in `tests/customer_interaction_task.test.mjs`; eight existing Chromium tests passed. After final all-4xx/session-fence hardening, the five affected task tests passed again. Node syntax and diff checks passed. The new test composes coordinator -> transport -> actual handler -> real local PGlite RPC, proving committed completion survives lost response with exactly two task audit events (create/complete), identical retry returns its receipt, stale/duplicate writes fail, and missing completion evidence cannot write. Browser/API authorization fixtures remain synthetic; there is no real owner-session/Edge/PostgREST/database proof. One initial test fixture incorrectly shared nested response/request provenance and was corrected with structuredClone; final checks are green. Existing scratch PGlite 0.3.14 and Python Playwright/Chromium were reused; no dependencies installed.

Reproduce: use the preceding full Node command plus `tests/customer_interaction_task.test.mjs`, and `python tests/customer_interaction_studio_browser.py`. Supabase changelog and Data API security documentation were reviewed read-only (https://supabase.com/changelog.md and https://supabase.com/docs/guides/api/securing-your-api.md); the November TLS cipher retirement entry introduces no RPC/envelope change here (https://supabase.com/changelog/cbc-tls-ciphers-deprecated). No live metadata/data query or production write was required for this browser-contract increment.

Proof contract: expected outcome is on-demand task disposition with immutable evidence, matching save confirmation and safe retry. Last successful local composition proof: 2026-10-13, task test above. Real operational end-to-end proof remains absent. Missing/malformed receipt, conflict, failed auth or uncertain commit is failure; caller must keep navigation blocked. Local test runner observes regressions, but no deployed outcome observer or observer-health proof exists. Recovery is identical retry for uncertainty; retain/export and fetch/review current server state for terminal conflicts. Do not discard or silently rebase a conflicting disposition. No MONITORED/HEALTHY claim, and Brian must not become the routine observer.

Next same-stream action: connect this coordinator to owner task fields/status/loading and guarded NEXT in the existing default-off Studio. Require confirmed interaction AND task disposition before advancing; do not resolve a call with outstanding follow-up as no-follow-up, and do not mark Production Board records complete. Then establish real owner-session UI/API/database recovery and usable backup/restore proof. Those remain production NO-GO gates before a separate explicit rollout GO; no migration/deploy/exposure/merge is authorized by this checkpoint. No owner action needed for safe code/test continuation. Keep PR372 draft/unmerged/undeployed.


## Default-off promised follow-up capture — 2026-10-13

The existing Studio now imports the existing immutable task-write coordinator. Explicit owner-entered title and original evidence save a pending canonical task linked to the confirmed interaction/case. Save is disabled until the interaction checkpoint is confirmed. Unsaved task fields and unconfirmed task writes block case selection, interruption/resume, internal navigation and beforeunload. An uncertain write freezes editing and offers identical-request retry; a terminal conflict retains the task envelope and draft for export/server review. Owner lock clears task fields, rows and pending state. No browser storage, customer matching, external execution, Google Tasks, task inference or notifications were added. This manual control is a foundation/fallback, not the primary extra-brain experience promised by #371.

Stored tasks are fetched by immutable interaction ID across all pages when opening an interaction. Repeated cursors, unexpected linkage/status and read failures fail closed instead of declaring no obligations. Resume fetches fresh tasks for both interactions; pending/proposed/snoozed obligations yield follow_up_due for the call, rather than resolved. Resuming restores the previous interaction's task display. Task completion/snooze editing, automatic saved-only NEXT and background recognition remain unwired. Production Board items remain read-only. Existing canonical task provenance/history and incumbent rationale in docs/CUSTOMER_INTERACTION_STORAGE.md apply; this adds no Enrollware dependency and moves capture toward native persistence.

Important unresolved concurrency boundary: the fresh task lookup and existing atomic two-interaction resume RPC are separate transactions. Another tab can create/change a task between the lookup and resume. This UI snapshot does not establish a transactional no-follow-up invariant. Before release, add a server-side task/disposition consistency fence in the resume transaction and prove concurrent task creation/status changes cannot produce a misleading resolved call. Task writes themselves retain the existing optimistic conflict/idempotency protections. No claim of a complete task workflow or production readiness.

Changed module references use 20261013-followup1; the owner meta gate remains disabled. No migration, endpoint, auth, CORS, generated inventory, build chain or production configuration changed. Existing Earl/Jackson dirty pages discovered in the isolated checkout were preserved and excluded from staging.

Validation: 11 real Chromium tests with synthetic owner/API fixtures, including promised callback -> lost response -> identical retry -> reload with paginated task reads -> resume retaining follow_up_due, conflict export/privacy clearing, and fail-closed task lookup. Full CRM/auth Node suite and syntax/diff results are recorded in the root receipt. Browser fixtures are synthetic; existing real local SQL task tests prove RPC bookkeeping only. No genuine owner-session/Edge/PostgREST/production database or backup/restore proof occurred. Current Supabase changelog/security docs and TLS deprecation page were fetched read-only; no API convention change relevant to this custom transport.

Proof contract: BUILT/local validation only; expected on-demand outcome is saved owner obligation survives reload and remains pending after call resume. Last local synthetic proof: 2026-10-13, tests/customer_interaction_studio_browser.py. Missing/malformed receipt, uncertain write, conflict or incomplete reads block navigation/disposition. Local runners observe regressions; no deployed CRM outcome observer or observer-health proof exists. Recovery: identical retry after uncertainty; export retained draft/envelope and reload/review server after conflict. Unconfirmed typed fields remain memory-only and can be lost if the process dies. Brian must not become the routine monitoring layer. Production remains NO-GO pending transactional task/resume fencing, task status/NEXT integration, real owner-session UI/API/database recovery proof, recoverable backup/restore evidence and separate explicit rollout GO. No owner action required for safe local continuation; keep PR372 draft/unmerged/undeployed.
