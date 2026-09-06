# Group training funnel amendment audit

Date: 2026-09-06

Branch: `codex/group-training-funnel`

PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/149

Issue: https://github.com/Brian910cpr/910cpr-class-landers/issues/148

## Implemented

- Rebuilt the hub as a progressive visual planner: organization, recommendation, program, exact course, logistics, authoritative preferred-time lookup, then contact.
- The selected course is the availability key. The server re-fetches the production selector artifact and requires date, time, course ID, block ID, page key, course family/name, and non-seated offer type to agree.
- Added enum validation, a 32 KiB body limit, honeypot, salted-IP hourly limiting, safe public errors, and non-PII analytics.
- Replaced multi-call persistence with one transaction. Advisory locks close idempotency and normalized-organization races; organization, coordinator, request, optional requested-confirmation session, and activity evidence cannot be partially created.
- Converts customer selections with `America/New_York`; DST assertions cover January and July.
- Kept seven useful industry guides and five market guides; removed five thin industry pages and their sitemap entries.
- Used authentic repository asset `docs/images/PrestonsReady.webp`. Full review: `data/audit/group_training_image_inventory.md`.
- Removed deployment-generated scheduling churn in commit `f378badf043`.
- Moved unreferenced 27,865,379-byte `docs/images/files (11).zip` to `private/archive/legacy-images-files-11.zip`. This preserves it while removing the likely Cloudflare Pages failure: the documented per-asset maximum is 25 MiB.

## Local evidence

- `node --test tests/group_training_funnel.test.cjs`: pass. Coverage includes mappings, program switching, ACLS/PALS, exact candidate matching, seated/stale/wrong-course rejection, validation, safe errors, body size, and analytics privacy.
- `python -m unittest tests.test_group_training_public`: pass.
- Broader targeted Python run: 21/22 pass. `test_public_class_landers_match_direct_bookable_public_schedule` fails on 127 existing public schedule IDs absent from the checked-in class-index artifact; this is outside the group-funnel files.
- Chrome captures for desktop light/dark, mobile first/program, recommendation, two industries, and two locations are under `data/audit/group-training-screenshots/`.
- Source inspection confirms GTM is retained and data-layer events exclude contact fields.

## Preview status and authenticated blockers

- Cloudflare Pages passed for PR head `445ca112de0eef2407d484d1f7f2287f562c2cbd` after the oversized archive was moved. Direct dashboard/API access remains unavailable because the local token is rejected and the dashboard is signed out.
- No preview Supabase credentials are available. Migration/Function remote integration is not claimed.
- GTM Preview and GA4 DebugView require live container/property access; only source-level event checks are complete.
- `GROUP_REQUEST_RATE_SALT` must be configured in preview.

## Deliberate limits and pre-merge gate

- A preferred time is a request, not a reservation; no `group_session_reserved` event exists.
- No Turnstile widget was added because the repository has no site key/configuration. Controls are honeypot, validation, body limit, salted-IP rate limiting, and idempotency.
- No production merge or deployment was performed.
- Before merge: require preview Supabase duplicate/concurrent/stale/wrong-course/oversize/rate-limit tests; GTM Preview and GA4 DebugView; keyboard and true 200% zoom checks.
