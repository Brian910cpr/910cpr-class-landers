# LanderWare public registration front door handoff

## Outcome

Implemented a review branch for `/register/?session=<ENROLLWARE_CLASS_ID>` that records identity and a durable pending registration intent before redirecting to the exact Enrollware class checkout. Production deployment is intentionally blocked until Supabase authentication is available.

## Primary audit findings

- Canonical customer table in this repository: `public.landerware_people` (the requested `public.customers` name is not present in current migrations).
- Canonical session table: `public.landerware_sessions` (the requested `public.class_sessions` name is not present).
- Canonical registration table: `public.landerware_registrations`.
- Existing customer deduplication is reused through `public.landerware_create_or_find_person`, primarily matching normalized email, then normalized phone plus exact first/last name.
- New intent state: `status='awaiting_external_checkout'`, `source='landerware_front_door'`, `external_checkout_state='awaiting_completion'`.
- Pending intents are excluded from confirmed participant semantics; reconciliation updates the existing row to `status='confirmed'`.
- Durable identifiers: registration UUID plus `handoff_intent_id` UUID; both are returned by the service.
- Enrollware handoff is allowlisted to `https://coastalcprtraining.enrollware.com/enroll?id=<CLASS_ID>` and the ID must match the selected public schedule session.

## Enrollware prefill investigation

Tested current class `13963993` on 2026-09-03 with URL-encoded probe parameters `firstName`, `lastName`, `email`, and `phone`. After advancing to Enrollware's Student Information form, all four fields remained empty. The live input names are WebForms names (`ctl00$maincontent$fnameTextBox`, `lnameTextBox`, `emailTextBox`, and `primaryPhone`), but passing public query parameters is not a supported contract and was not used. No Enrollware registration was submitted.

Supported identity prefill fields: none found.

Unsupported tested fields: first name, last name, email, mobile phone.

## Important files

- `docs/register/index.html`
- `supabase/functions/landerware-registration/index.ts`
- `supabase/migrations/20260903190143_landerware_public_registration_front_door.sql`
- `scripts/import_enrollware_registration_events.py`
- `scripts/build_landers.py`
- `scripts/build_index_and_sitemap.py`
- `scripts/build_slug_hubs.py`
- `tests/test_public_registration_front_door.py`
- `tests/test_import_enrollware_registration_events.py`

## Validation

Command: `python -m unittest tests.test_public_registration_front_door tests.test_import_enrollware_registration_events`

Result: 9 tests passed.

Command: `git diff --check`

Result: passed (line-ending warnings only).

Browser checks:

- LanderWare page rendered the correct course, date, time, location, and four required fields at `http://127.0.0.1:8765/register/?session=13963993`.
- Enrollware handoff displayed the same class, Monday 9/28/2026 at 2:00 PM, Wilmington Shipyard location, and $225.00 base price.

## Deployment blocker

`supabase projects list` returned: `Access token not provided. Supply an access token by running supabase login or setting the SUPABASE_ACCESS_TOKEN environment variable.`

GitHub authentication is available, but no Supabase access-token secret exists in the repository. Do not merge the public route before deploying the migration and `landerware-registration` Edge Function.

## Required continuation

1. Authenticate the Supabase CLI for project `wktwgcnwdvbebcobgyey`.
2. Review and apply `supabase/migrations/20260903190143_landerware_public_registration_front_door.sql`.
3. Deploy `supabase/functions/landerware-registration`.
4. Exercise one test intent, query the returned person/registration/session IDs, and invoke the reconciliation RPC with a synthetic external registration ID to prove the same row becomes confirmed.
5. Merge the branch, wait for GitHub Pages, verify live `/register/?session=13963993`, and capture final live screenshots.

## Open assumptions

- `public.landerware_people`, `public.landerware_sessions`, and `public.landerware_registrations` remain the canonical equivalents of customer/session/registration.
- The static public schedule remains the authoritative public-sellability contract used to validate requested session IDs.
- Appointment offers remain direct-to-Enrollware until they resolve to a durable session ID.
