# Admin access privacy correction — issue 215

- Timestamp: 2026-09-14T01:42:40.618Z
- Branch: codex/admin-privacy-controls
- Substantive commit: 7d6cddc2e9d0648e47b7b51362628f9951fb8264
- Work-item state: IN_PROGRESS (indexing changes ready for PR; owner sign-in and complete privacy remain BLOCKED).
- Related issue: https://github.com/Brian910cpr/910cpr-class-landers/issues/215

## Corrected owner instruction

The latest owner message explicitly requires private company pages and records, with practical access that does not repeatedly lock the owner out. This supersedes the immediately preceding request to remove passwords entirely. Do not publish the withdrawn public-access implementation or treat the old removal comment as current authorization.

## Containment completed

The five Supabase owner APIs briefly ran without their original shared-key validation while following the preceding explicit direction. That was reversed after the owner clarified the privacy requirement. No frontend page or Cloudflare Worker changes from the password-removal implementation were published; its local changes and new helper/tests were withdrawn.

Original function artifacts were restored:
- instructor-workbench v8
- canonical-session-workspace v4
- class-registry v5
- owner-dashboard v5
- production-board v7

Their verify_jwt:false setting is intentional because the original custom owner authorization is restored. The new owner-operations gateway was disabled at v2, with verify_jwt:true and an unconditional 401 handler; it no longer forwards anything.

Fresh anonymous GETs after restoration returned 401 for all six services, including the disabled gateway. This proves anonymous denial for those tested routes; it does not prove a successful owner sign-in or absence of third-party access during the brief public window. No participant, payment, attachment, or class records were changed in this turn.

## Search findings and patch

Ten of 20 docs/admin HTML pages lacked a robots meta tag. Admin Port lacked noarchive. Added the missing directives and made all 20 consistently noindex,nofollow,noarchive. No admin or admin-data URL was present in the current 64-entry sitemap.

robots.txt now excludes /data/admin_ from cooperative crawling. Google/Bing can still fetch admin HTML to see noindex. OAI-SearchBot and GPTBot are explicitly excluded from /admin/ and /data/admin_, while public course pages remain allowed. This is crawler guidance, not access control or proof of deindexing. Existing search results can persist until reprocessing.

Exact substantive files:
- docs/admin/admin-port.html
- docs/admin/financial.html
- docs/admin/instructor-class-intake-prototype.html
- docs/admin/nhcso-training-history-v5.html
- docs/admin/nhcso-training-workspace-prototype.html
- docs/admin/nhcso-training-workspace-v3-prototype.html
- docs/admin/nhcso-training-workspace-v4-prototype.html
- docs/admin/nhcso-training-workspace-v6.html
- docs/admin/payments.html
- docs/admin/refresh-availability.html
- docs/admin/schedule-reader.html
- docs/robots.txt

## Verification

- Parsed all 20 admin HTML heads: exactly one robots tag with noindex, nofollow, noarchive.
- Parsed the sitemap: zero admin/admin-data URLs among 64 entries.
- Checked Googlebot, Bingbot, OAI-SearchBot, and GPTBot crawler paths: public BLS allowed, admin data disallowed; Google/Bing can read admin noindex, OpenAI crawlers excluded from admin pages.
- Compared HTML to base with robots metadata/whitespace removed: no other HTML, JS, authentication, or business changes.
- git diff --check passed.
- No generators or full-stack rebuilds ran.
- Local validation only at receipt creation; production Pages publication and live-byte verification must still be recorded on issue 215.

## Material remaining exposure and access blocker

Older static admin JSON feeds already exist in docs/data and are independent of the restored API checks. A direct anonymous production GET of the people feed returned 200, with 79 records containing contact fields. No contact values were emitted in this receipt or chat. Other legacy feeds include schedule, availability, clients, and locations; older NHCSO prototypes also embed historical class information. The indexing patch does NOT make these resources private.

Do not assert that all LanderWare data or all admin pages are private. Protecting only an HTML page or adding a JavaScript login cannot protect an independently public JSON/PDF URL. The underlying feeds, files, and direct API origins must be protected too; preserving authoritatively generated public class inventory is required.

The existing shared-key owner login still has no successful end-to-end proof. Cloudflare's actual HOT_SYNC_ADMIN_KEY authority is separate from identically named GitHub secrets; the key is absent from Supabase's runtime. The connected tools provide no authenticated Cloudflare administration session (Wrangler whoami unauthenticated; provider plugin discovery found no Cloudflare plugin). Do not ask the owner to reveal the key in chat.

Recommended next implementation: identity allowlist with Google or email one-time-code login and a remembered server session, plus protection/migration of all underlying private resources and bypass-proof direct origins. Cloudflare Access supports email policies and sessions up to one month. Account-level configuration is required for that option and is not available in this tool session. Do not remove the restored API authorization before the replacement has passed real owner access AND anonymous denial checks.

## Evidence and recovery contract

- Indexing controls: BUILT at receipt creation; pending production verification. Deindexing itself has not been observed.
- Restored API denial: PROVEN only for the six anonymous GETs at this checkpoint.
- Owner access / comprehensive privacy: BLOCKED, not PROVEN or HEALTHY.
- Expected outcome: owner opens and manages records through remembered access; anonymous requests cannot obtain private records/files or mutate them.
- Required next proof: owner sign-in -> navigation across owner pages -> authorized document view/removal; anonymous direct page/API/feed/file requests denied.
- Failure: owner cannot sign in, any private direct URL returns data anonymously, or a publisher recreates a public private-data feed.
- Observer: issue 215 remains open; no continuously verified privacy or owner-login monitor was installed in this change. Observer health is unproven.
- Recovery: retain restored authorization; obtain account configuration capability, protect/migrate legacy resources, verify one useful complete owner workflow, then expand.
- User/account action: Cloudflare account connection/configuration is needed for the proposed Access approach; do not request the shared secret again.
