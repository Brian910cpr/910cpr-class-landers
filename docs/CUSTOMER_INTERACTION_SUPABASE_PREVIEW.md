# Issue371 isolated Supabase preview decision — 2026-10-19

State: target discovery complete; provisioning BLOCKED on explicit billing-organization selection and a live cost quote/approval. Existing draft PR372 remains the single implementation. Production rollout stays NO-GO. Brian's October19 request authorizes investigation and continuation in an isolated cloud preview; older local-only Path A records remain historical and their operational proof gates still apply.

## Connected account inventory (read-only)

- LanderWare: wktwgcnwdvbebcobgyey, ACTIVE_HEALTHY, us-east-1, organization kukukymsnhicxzwsvxgo. Known production; excluded from writes/deployments.
- ShiftCommander: cskcgwjvgsgawxwncjrf, ACTIVE_HEALTHY, us-east-1, same organization. Another application; no evidence it is disposable or authorized for CRM; excluded from writes/deployments.
- list_branches returned [] for each project. No existing isolated preview was discovered. No customer rows, sessions, keys or secrets were requested. These are inventory/API status observations, not application-health proof.

Recommended candidate: NEW dedicated project named landerware-issue371-preview in us-east-1, once organization and cost are approved. It has no project reference yet. Do not relabel an existing application as preview. A new blank project avoids copying unrelated deployed functions/settings/webhooks. Supabase branches are isolated and data-less by default, but copy deployed functions/settings and enable database webhooks; they require a separate side-effect review before use. Source: https://supabase.com/docs/guides/deployment/branching . Never merge a preview branch into production in this assignment.

## Exact approvals and cost boundary

1. Organization selection REQUIRED by the connected Supabase get_cost/create_project tools, even though this account currently shows only kukukymsnhicxzwsvxgo. Asked Brian to select it or another organization. This is not a skill-imposed extra approval; it is an explicit tool requirement. Selecting it authorizes the quote, not charges.
2. After selection, get_cost(type=project, organization_id=selected ID). Report the returned exact amount/currency/recurrence; do not invent a price or assume existing compute credits apply. Nonzero quote needs explicit agreement. Follow the tool's server cost-confirmation flow; call confirm_cost only after explicit agreement if a confirmation ID is required. No quote has been obtained and no billing operation has occurred at this checkpoint.
3. Brian's current request authorizes isolated preview implementation, synthetic records, preview-only deployment and tests. No second general permission is needed for those reversible steps after target/cost are settled. An owner interactive sign-in may be needed for the genuine owner-session browser test; generate a separate short-lived preview credential, never copy a production session or post tokens.
4. Proposed browser origin: https://feat-customer-learning-studi.910cpr-class-landers.pages.dev . Confirm its deployment/access before binding; use only this exact origin in preview-specific code/config. No wildcard or shared production origin expansion. If owner chooses a different preview origin, use that explicit value instead.
5. Production migration, authentication change, rollout/merge and any production backup work remain separately gated. Existing independent-session concurrency, owner-session recovery and usable backup/restore gates do not disappear because a preview exists. No Docker/WSL/NAS prerequisite is revived.

## Narrow deployment manifest after provisioning

First get_project(new reference); require ACTIVE_HEALTHY and reference unequal to BOTH existing application refs. Inventory the new target's public tables/migrations/functions and auth configuration. Stop on unexpected objects; preserve existing target contents instead of resetting. Record the confirmed reference in the audit before any write. Use explicit project_id for every connector mutation; never use a locally linked default project (supabase/.temp is unrelated and untouched).

Schema prerequisites and files to review/apply only to confirmed isolated project:
- Canonical people relationship: CRM references public.landerware_people(id uuid). Determine and reuse the repository's canonical migration dependency closure; do not apply every production migration blindly. A minimal id-only test fixture is acceptable for synthetic SQL proof ONLY and must be labelled incomplete; it is not proof of real identity integration or a replacement person catalog.
- supabase/migrations/20260914015555_owner_access_sessions.sql defines the existing grant/browser-session objects. Review actual preview default ACLs; enforce RLS/private privileges and validate expiry/revocation rather than importing live owners.
- supabase/migrations/20261010210607_customer_interaction_storage.sql
- supabase/migrations/20261010211804_customer_interaction_interruptions.sql
- supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql
- Record migration identities/hashes; do not replay history already present.

Edge bundle: supabase/functions/customer-interactions/index.ts, handler.ts, ../_shared/owner-auth.ts and ../_shared/owner-session.ts, plus any declared runtime config. The current runtime uses custom revocable x-landerware-owner-session, not Supabase Auth JWT, and must retain that authorization. Review gateway JWT compatibility explicitly; a gateway rejection is not a reason to weaken owner authorization. No HOT_SYNC fallback or corporate identity may authorize CRM. The preview must use its own server-side credentials/SUPABASE_URL; never export or copy production credentials. Read-only API inventory does not prove deployment permission until attempted on an approved target.

## Discovered browser/auth routing blockers

Provisioning alone will NOT enable safe browser testing:
- docs/admin/customer-interaction-client.mjs hardcodes the production customer-interactions endpoint.
- docs/admin/admin-auth.js hardcodes production owner-access, service allowlisting, refresh/logout and session storage identity.
- supabase/functions/_shared/owner-auth.ts accepts only production origins; handler.ts also has an explicit production-origin CORS allowlist.
- Existing tests/customer_interaction_cors.test.mjs deliberately rejects preview/local origins.

Do not turn on the existing Studio feature meta flag while any of those paths still points at production. Continue in PR372 with preview-scoped dependency/configuration and a distinct preview session namespace, exact endpoint/ref/origin checks and refusal tests proving that no production requests or credentials cross environments. Keep default production behavior and release gate unchanged. This is an identified implementation step, not an already-deployed repair. No routing/auth source changed in this discovery increment.

## Required proof and next execution

Once target/cost are authorized: provision the one preview, bind its exact reference, prepare only prerequisite schema and these CRM migrations, run security advisors, create synthetic short-lived owner fixtures, deploy preview-only endpoint, then implement/test the isolated browser route before enabling synthetic preview capture. Verify owner denial/expiry/revocation; durable save/reload/interrupt/resume; stale conflict and uncertain identical retry; follow-up obligations and immutable receipts through Edge/PostgREST and fresh browser session. Independently prove READ COMMITTED blocking with the existing runner when an authorized supported environment is available; do not broaden its loopback-only guard to a remote DSN as a shortcut. Existing data-retention and backup/restore requirements remain release gates. Report exact remote evidence without calling local mocks operational proof.

Current evidence: connected account read-only inventory only. No preview created, schema applied, function deployed, UI enabled, secret fetched, application data copied, production changed, paid resource created or preview E2E proof claimed. No new CRM, scheduler or monitor.

GitHub operational blocker: gh issue view371 reports repository issues disabled; do not re-enable repository settings. Post the checkpoint on existing PR372 and retain root Codex_Reply handoff instead. Unrelated docs/Earl/index.html, docs/Jackson/index.html and supabase/.temp remain preserved/excluded.
