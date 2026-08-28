# NHCSO August 26, 2026 production recovery handoff

## Production result

- Original NHCSO class: `public.nhcso_classes.class_number = NHSO-20260826-1300-FCFAC7`
- Canonical durable Session: `public.class_sessions.id = 5ad39214-f084-4996-bc9d-e4e3a5cda081`
- Durable source identifier: `class_sessions.external_class_id = NHSO-20260826-1300-FCFAC7`
- Source/storage document metadata ID: `6313ecca-7751-4809-a55b-b6e7d9de31a0`
- Storage bucket: `nhcso-class-docs` (private)
- Storage object ID: `18537b13-fcb1-4ad0-b9e4-06126a529194`
- Storage path: `NHSO-20260826-1300-FCFAC7/course_completion/1787844546038-8.27_Class_Documents.pdf`
- Linked original NHCSO students: 11
- Durable registrations: 11, each linked back through `registrations.nhcso_student_id`
- Linked source documents: 1
- Durable instructors: 2
- Card-processing state: `ready_for_issue`, 11 required, 0 issued, no missing completion requirements

## Paperwork review

The unchanged 7,368,609-byte PDF was retrieved through a five-minute signed URL and inspected locally. It contains 92 scanned pages:

1. Signed New Hanover County Sheriff's Office Internal Training Class Roster for August 26, 2026, 13:00-16:00, Patrol Training Room.
2. Eleven roster entries, all with written test score `100` and practical application `Pass`.
3. Participant-specific AHA BLS skills testing checklists marked `PASS`.
4. Participant-specific BLS exam answer sheets.
5. Course evaluations.
6. Instructor attestations/signatures for Sgt. Lauren Brothers and M/Cpl. Crystal Jasper, including their instructor numbers.

The 11 roster names reconcile to the 11 active `public.nhcso_students` rows. No eCard numbers appear in the packet or database. The paperwork establishes course completion but does not establish card issuance.

## Canonical identities

- Lauren Brothers: `people.id = 573d625a-3eb8-4d07-a3f0-ac76e39f6598`, `person_key = instructor_2221028576`
- Crystal Jasper: `people.id = b6422685-d942-40ba-a6e4-09212f5fe20b`, `person_key = instructor_23125524581`
- Both have active `NHCSO_CADRE` qualifications for `aha-bls-provider`.
- Crystal is linked to the recovered Session as assistant instructor and recorded in `nhcso_classes.assistant_instructors` as an audited correction.

## Transaction and idempotency

`public.promote_nhcso_class(text)` uses a transaction-scoped advisory lock and the existing unique partial index on `class_sessions.external_class_id`. It links source rows, upserts registrations, requirements, card state, audit events, and notification outbox items. A second production invocation resulted in exactly:

- 1 Session
- 11 registrations
- 4 audit events
- 2 notification rows

## Notifications

Two durable post-commit outbox rows exist:

- Submitter confirmation to `labrothers@nhcgov.com`
- Operations notification to `brian@910cpr.com`

The dispatcher was implemented and exercised. Delivery failed because `TRANSACTIONAL_EMAIL_WORKER_URL` and `TRANSACTIONAL_EMAIL_WORKER_SECRET` are not configured in the Supabase Edge Function environment. Both failures were logged in the outbox; the committed Session remained intact. The existing Maxim email worker is workflow-specific and was not misused as a generic mail transport.

## Important source files

- `supabase/migrations/20260828030000_nhcso_durable_session_recovery.sql`
- `supabase/functions/nhcso-workspace/index.ts`
- `docs/corp/nhcso/index.html`
- `tests/test_nhcso_production_recovery.py`

## Validation

- Supabase migration applied successfully in production.
- Edge Function `nhcso-workspace` deployed as version 5.
- Live `list_instructors` returned `Crystal Jasper, Lauren Brothers` from persistent qualifications.
- Live `get_class` returned Session `5ad39214-f084-4996-bc9d-e4e3a5cda081`, 11 students, 1 document, 4 verified requirements, and `ready_for_issue` for 11 cards.
- `python -m unittest tests.test_nhcso_production_recovery`: 7 tests passed.
- `git diff --check`: passed for intended files.

## Remaining operational steps

1. Configure the general transactional email Worker URL/secret and retry the two failed outbox rows.
2. Publish the updated `/corp/nhcso/` static page so persistent cadre selection and durable card state are visible on the public site.
3. Issue 11 AHA BLS eCards through the authorized card workflow; then record eCard identifiers and move card processing from `ready_for_issue` to `issued`.

## Separate security advisory

Supabase reported that `public.maxim_billing_code_rules` has RLS disabled. This is unrelated to the NHCSO recovery and was not changed. Review before enabling RLS because enabling it without appropriate policies could break existing access.
