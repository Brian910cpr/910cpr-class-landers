# Owner access without manual secret setup — issue 215

- Timestamp: 2026-09-14T02:17:52.996Z
- Branch: codex/owner-passwordless
- Substantive commit: 844b7b9469f83b89d19fe5eee74cf84ef626b810
- State at receipt: IN_PROGRESS (backend proven; frontend publication and link delivery pending).
- Issue: https://github.com/Brian910cpr/910cpr-class-landers/issues/215

## Owner instruction and selected implementation

Brian authorized whichever private sign-in can be installed using existing connected access, without requiring him to place secrets in multiple services. Selected a private, revocable capability link, delivered to his verified connected business inbox, that creates a separate remembered browser session. This is not anonymous access and not Google OAuth.

Google sign-in is disabled in current Supabase Auth settings. Native email sign-in is enabled but has no existing users and depends on SMTP/redirect configuration that this session cannot manage. Existing Cloudflare administration is unavailable; Supabase env and integration/vault metadata contain no usable HOT_SYNC authority key. No new provider account, SMTP configuration, DNS change, or user-copied secret is required for the installed link.

The access link uses 256 random bits, stored only as a SHA-256 hash in the database. The owner grant expires after 365 days and can be revoked. Browser sessions are independently revocable, expire after 30 days, and refresh during use when fewer than seven days remain, bounded by the grant expiry. The access credential is in the URL fragment, removed immediately with history.replaceState; no credentials are committed, printed, or included in this receipt. The new entry page has no external scripts or analytics and sends credentials only to the first-party Supabase access API.

## Work performed

- Added owner_access_grants and owner_browser_sessions, both RLS enabled and with all anon/authenticated privileges revoked. Only service_role can read/write them. Created migration through the Supabase CLI before applying its SQL.
- Added owner-access exchange, session validation, refresh, and sign-out endpoints. Invalid, expired, and revoked access fails closed.
- Added private-session authorization alongside the existing HOT_SYNC automation path in the shared backend helper.
- Deployed owner-access v1, instructor-workbench v9, canonical-session-workspace v5, class-registry v6, owner-dashboard v6, production-board v8.
- Preserved original deployed function bodies except shared-auth wiring and CORS support for the new session header.
- Replaced the browser auth helper with remembered sessions. It restricts credential destinations, isolates legacy Cloudflare failures, aborts stale responses, and clears state across tabs/on sign-out.
- Added the private entry page, removed visible password gates from eight owner pages, and added Sign out to the shared navigation.
- Preserved the previous noindex/crawler exclusions.
- Operations can load canonical participant truth even when its legacy Hot Sync panel is unavailable.

Exact substantive files:
- .github/workflows/verify-owner-access.yml
- docs/admin/access.html
- docs/admin/admin-auth.js
- docs/admin/admin-nav.js
- docs/admin/admin-port.html
- docs/admin/all-classes.html
- docs/admin/class-registry.html
- docs/admin/dashboard-ops.js
- docs/admin/dashboard.html
- docs/admin/financial.html
- docs/admin/instructor-workbench.html
- docs/admin/now.html
- docs/admin/now.js
- docs/admin/owner-access.js
- docs/admin/production.html
- docs/admin/production.js
- docs/assets/instructor-workbench.js
- supabase/functions/_shared/owner-auth.ts
- supabase/functions/_shared/owner-session.ts
- supabase/functions/canonical-session-workspace/index.ts
- supabase/functions/class-registry/index.ts
- supabase/functions/instructor-workbench/index.ts
- supabase/functions/owner-access/handler.ts
- supabase/functions/owner-access/index.ts
- supabase/functions/owner-dashboard/index.ts
- supabase/functions/production-board/index.ts
- supabase/migrations/20260914015555_owner_access_sessions.sql
- tests/admin_auth.test.mjs
- tests/instructor_documents.test.cjs
- tests/owner_access.test.mjs
- tests/owner_access_ui.test.mjs

## Verification already completed

- 20 auth/backend/entry-page tests passed.
- 18 instructor document and UI tests passed after the harness was updated to load the new shared dependency.
- Deno check passed for owner-access; changed browser JS syntax and git diff --check passed.
- Live private-link exchange returned 200 and a browser session.
- With that session: Class History returned 400 real sessions; canonical workspace returned 11 sessions for the tested date range; Class Registry returned 31 sessions; NOW returned eight upcoming sessions, 32 board records and seven prompts; Production Board returned 49 cards.
- The same five services returned 401 anonymously.
- Six local page integrations against real production APIs rendered records without script errors: Class History, Class Registry, ALL Classes, Admin Port, NOW, Production Board. This is a DOM integration check, not a claim that Brian has personally signed in.
- A real retained PDF attached to the Aug 27 class was opened through the authenticated view endpoint and returned 200 with a PDF signature.
- The two mistaken attachments remain absent from the Aug 28 class. No additional business documents were deleted.
- SQL privilege verification confirms both new tables have RLS, no anon/authenticated SELECT, and service-role access.
- Supabase security advisor returned informational RLS-with-no-policy notices for the two intentionally service-only tables. No public policy should be added to suppress those notices. Guidance: https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy
- Temporary verification grant/session must be revoked after final verification. Owner link must be delivered only after Pages publication is verified.

## Remaining limitations

- The Financial Worker and legacy Hot Sync/inbox write paths are not connected to this new owner session. Existing valid legacy keys may still work in their original tab, but their failure no longer clears the main owner session. Admin Port itself already uses the canonical Supabase workspace and passed.
- Legacy public admin JSON feeds, embedded prototype data, and the public GitHub repository remain a separate privacy gap. This change does not represent them as private. The new grant/session records and owner API data are protected.
- This creates owner access, not individual instructor accounts or instructor-scoped permissions.
- The reusable private access link authorizes its holder. Keep its delivery private; revoke the grant to revoke all sessions derived from it.
- If the grant is lost/revoked/expired, an authorized operator must issue a replacement. The self-service email recovery service is not yet installed.
- Frontend publication, production bytes, and private inbox delivery are still pending at this immutable receipt checkpoint. Final evidence will be recorded on issue 215.

## Persistent proof contract and next action

Evidence level: PROVEN private session -> real owner API records and private PDF; BUILT frontend pending production publication. Not MONITORED or HEALTHY.

Expected useful outcome: Brian opens his private link, enters Class History, navigates owner pages without copying a password, and can view/manage class documents; anonymous visitors cannot query the protected records.

Success evidence: this receipt's live status/count checks, six DOM integrations, private PDF proof; next verify production Pages assets and link delivery. Brian's own browser sign-in is not yet observed.

Cadence: session checks on each owner API call; renewal during active use; regression CI on owner-auth changes. A continuously observed end-to-end synthetic login monitor is not yet installed or proven.

Failure condition: invalid/expired/revoked sessions expose data; first-party session cannot load records; stale responses repopulate signed-out views; old Cloudflare errors sign the owner out. Observer: regression CI and issue 215; runtime observer health unproven.

Recovery: retain closed backend authorization; diagnose owner-access exchange/session calls separately from page business data. Revoke only the affected grant/session when necessary; issue a new private link through the existing connected account. Do not ask Brian to copy HOT_SYNC secrets.

Next: publish this reviewed branch, verify live assets and preflights, send the private entry link to the verified connected Brian business inbox, revoke the temporary test grant, and record exact PR/deployment/delivery evidence on issue 215. No user configuration is required for this installed path.
