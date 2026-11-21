# Issue #270 Universal Scheduling Gateway, R1

## Status

- Capability level: **BUILT** on branch `codex/universal-scheduling-gateway`.
- Connected to production Supabase: **No**.
- Deployed: **No**.
- Live verified: **No**.
- Durable production card: GitHub Issue #270.

This is the first vertical slice of the universal email-to-LanderWare scheduling gateway. It does not close Issue #270 and must not be described as production-ready until the migration and Edge Function are deployed in a controlled environment, real tokens are exercised, and the required adversarial review is complete.

## What was built

- A universal opaque-token model for initial scheduling, direct registration, rescheduling, no-show recovery, 22-month renewal, 23-month renewal, and instructor invitations.
- SHA-256 token storage, expiration, revocation, scoped actions, completion limits, and no PII or payment claim in the URL.
- A server endpoint that rechecks the canonical registration/payment state and the current public schedule on every open and selection.
- Course compatibility through data-driven `compatible_course_ids` and delivery-mode restrictions rather than a course-specific route.
- Canonical Session, Roster, Registration, Person, Organization, message, and activity-event integration.
- Append-only rescheduling: the old registration is superseded, its roster membership is marked rescheduled, and a new registration points back to it.
- Idempotent selection and durable scheduling-action receipts.
- Prepaid, organization-billed, no-charge, inherited, and self-pay behavior. Self-pay continues into the existing native checkout; covered registrations are not sent to payment again.
- A responsive `/schedule/` customer page with one course context, current compatible dates, a payment explanation, and one clear action.
- Static-host recovery for emailed `/schedule/<opaque-token>` URLs through `docs/404.html`, keeping the raw token out of generated files and analytics.
- Protected admin token issuance through `X-Hot-Sync-Admin-Key`; referenced Person, Registration, Organization, Profile, and Course records are re-read before issuance.

## Files

- `supabase/migrations/20260922220000_universal_scheduling_gateway.sql`
- `supabase/functions/scheduling-gateway/index.ts`
- `supabase/functions/scheduling-gateway/deployment.json`
- `docs/schedule/index.html`
- `docs/404.html`
- `tests/test_universal_scheduling_gateway.py`

## Validation

Passing targeted suite:

```text
python -m unittest -q \
  tests.test_universal_scheduling_gateway \
  tests.test_public_registration \
  tests.test_heartsaver_skills_registration \
  tests.test_course_lander_sales_page \
  tests.test_build_courses_preserves_individual_landers

Ran 34 tests: OK
```

Additional checks:

- `node --check supabase/functions/scheduling-gateway/index.ts`: passed.
- Extracted inline JavaScript from `docs/schedule/index.html` and ran `node --check`: passed.
- `git diff --check`: passed.

No local PostgreSQL/Supabase runtime was available, so the migration and RPC have not yet been executed against a database. That is a deployment-blocking validation item, not a hidden success claim.

## Lander spot-check

The public lander maintenance pipeline is active. On 2026-09-22, the latest GitHub runs for Pages deployment, public-site refresh, admin-availability refresh, expired-page retirement, source integrity, and Cloudflare preflight all showed success. The current schedule artifact was generated at `2026-09-22T16:11:14-04:00` with 36 future public sessions. The repository contains 147 class HTML pages.

Live spot-checks succeeded for:

- `/bls.html`
- `/acls.html`
- `/pals.html`
- `/heartsaver.html`
- `/arc.html`
- `/hsi.html`
- `/classes/14034158.html` (BLS Renewal)
- `/classes/14083302.html` (ACLS HeartCode)

The family landers render current course selectors, calendar/start-time areas, and registration areas. The class landers render the expected course, date, time, location, and registration link.

Observed maintenance debt outside this branch:

- The two sampled class pages ended with a stray visible `None`.
- The ACLS sample's “Latest ACLS class dates” section repeated some dates/times for distinct co-class sessions without explaining the distinction.
- A broader local legacy test group has existing failures caused by outdated expectations, missing generated historical pages, and a missing local `beautifulsoup4` dependency. These were not introduced by this branch. The current production workflows named above are green.

## Next controlled proof

1. Review and apply the migration in a non-production Supabase environment.
2. Deploy `scheduling-gateway` with JWT verification disabled only because the public routes use opaque tokens; confirm the admin issuance boundary remains `X-Hot-Sync-Admin-Key`.
3. Issue synthetic tokens for each lifecycle and payment policy.
4. Verify open, expired, revoked, completed, replay, incompatible-course, stale-session, and reschedule cases against real canonical records.
5. Prove Change the Game PT/Heartsaver blended, a 22-month renewal, a 23-month renewal, and a no-show reschedule.
6. Run the separate adversarial review required by Issue #270 before any acceptance claim.

