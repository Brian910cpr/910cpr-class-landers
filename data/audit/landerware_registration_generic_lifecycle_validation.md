# Unified LanderWare registration lifecycle validation

Status: **validated locally; not deployed; production remains paused**

Validation date: 2026-08-27/28 EDT

Branch: `codex/heartsaver-skills-registration`

Execution mode: local PGlite integration database plus static/source tests. No production Supabase migration, Edge Function deployment, email, billing, or credential-provider call was made.

## Traceable third-course proof

This scenario is neither Heartsaver nor MAXIM. It uses a normal instructor-led group profile added as data:

- profile key: `nhcso-foundations-instructor-led-v1`
- course ID: `landerware-foundations`
- person ID: `052b7337-15e2-4205-844a-c52bbbec7c8b`
- registration ID: `c1fa113c-fc96-4de5-a6c7-7bcdc00411d4`
- session ID: `f70eb302-2d9d-4fae-a129-d44f69cf803e`
- payer mode: `invoice_later`
- idempotency key: `validation-nhcso-001`
- entry context: `staff_admin`
- source/external identity: `nhcso_roster / employee-FT-2048`

Durable requirement instances:

- signed form: `18bba557-7f52-40b0-9651-49186a1cce73`; upload required before registration; not staff-satisfiable; satisfied by document `1530c9bc-1e27-4a44-9672-832d59f68168`
- employer document: `e0d3c1a5-3829-4da4-b950-0fab38f1c549`; submit later; required before attendance/completion; staff-satisfiable; satisfied by `staff:validation`

Lifecycle linkage:

- completion ID: `af81cf9f-5fec-4156-91a1-4110f12524af`
- credential ID: `f7eebe25-2135-44a9-9c9e-8b13d848c89a`
- eCard code: `VALIDATION-CARD-2048`
- completion and credential each retain the same person, registration, course, and session IDs above
- document retains person, registration, and registration-requirement linkage

Activity history, in order:

1. `registration_created` — profile `nhcso-foundations-instructor-led-v1`
2. `requirement_document_received` — document `1530c9bc-1e27-4a44-9672-832d59f68168`
3. `requirement_satisfied` — requirement `e0d3c1a5-3829-4da4-b950-0fab38f1c549`, actor `staff:validation`
4. `registration_completed` — completion `af81cf9f-5fec-4156-91a1-4110f12524af`
5. `credential_issued` — credential `f7eebe25-2135-44a9-9c9e-8b13d848c89a`, eCard `VALIDATION-CARD-2048`

The same registration was retrieved independently by person ID, registration ID, session ID, case-insensitive email, name/phone, and external identity. Replaying the submission returned registration `c1fa113c-fc96-4de5-a6c7-7bcdc00411d4`; the registration count remained one.

## Lifecycle assertions

1. Person resolution uses `landerware_create_or_find_person`; `landerware_register` remains the sole registration operation.
2. The generic route is `POST /landerware-registration/register/<profile-key>`; the handler has one profile-key route and no course dispatch table.
3. Registration is durable and independent of its originating page.
4. `session_policy` enforces required, optional, or none. The Foundations proof used required and produced the session above. The HTTP handler now forwards generic external session inputs.
5. Requirements are instantiated from profile JSON into `landerware_registration_requirements` without type-specific branches.
6. Empty requirements, required-now upload, submit-later, and staff satisfaction are represented generically. Completion rejects unsatisfied `required_before_completion` instances.
7. Payer modes are profile data. The proof used `invoice_later`; the shared operation supports customer, corporate/client, invoice later, prepaid, free, and special-price states.
8. A required-session registration is tied to the durable roster/session workflow.
9. `landerware_record_completion` records completion against the original registration.
10. `landerware_issue_credential` derives person/course/session from that registration and requires completion first.
11. Documents retain person, registration, and requirement-instance IDs.
12. Shared activity events cover creation, requirement changes, completion, and credential issuance.
13. Confirmation content is loaded from the profile's template key. MAXIM's durable confirmation was changed to use that same template configuration. The local proof generated confirmation and reminder variants from `group-course-confirmation-v1`; production delivery scheduling remains a separate operational concern.
14. Registration idempotency and handler side-effect replay were tested/guarded. Confirmation messages and deferred-upload tokens are not recreated on replay.
15. Discovery succeeded for all requested identifiers. Name/phone lookup is appropriate only when sufficient identifying data is present.

## Hidden-special-case audit

Core generic Edge Function:

- no Heartsaver, MAXIM, Earl, NHCSO, or course-ID branching
- no requirement-type conditional
- upload field, size, MIME types, required-now behavior, submit-later behavior, and token lifetime come from requirement configuration (the 30-day value is only a generic fallback)
- confirmation template comes from the registration profile
- session inputs and source/external identity are generic request fields

Configuration/data:

- Heartsaver and MAXIM course IDs remain only in migration seed/profile data, except for MAXIM's upstream scheduling/catalog presentation mappings
- Heartsaver-specific requirement wording and 180-day token policy are profile data
- Foundations/NHCSO course, requirements, payer policy, and templates are profile data

Legitimate specialized entry-context/UI behavior:

- the Heartsaver page contains Heartsaver copy and selects its profile key
- MAXIM retains corporate authorization, scheduling-task validation, location display, simulated client notices, and catalog display mappings
- Earl remains a separate event-branded page and legacy event endpoint; it was not made canonical and its unrelated unstaged `docs/Earl/index.html` change was not edited or staged by this work

Finding corrected during this pass:

- MAXIM's durable confirmation had hard-coded subject/body text. It now resolves the profile's `confirmation_template_key` and renders the shared template.
- The generic handler previously omitted required-session parameters and could recreate token/message side effects on replay. Both were corrected.

## Validation commands and results

- `python -m unittest tests.test_heartsaver_skills_registration` — 11/11 passed
- combined focused registration/MAXIM suite — 53/55 passed; the two failures are pre-existing rendered-page projection/expiry assertions in `docs/bls.html` and `docs/corp/maxim-schedule.html`, neither changed in this pass
- PostgreSQL syntax parse of `20260827220000_landerware_unified_registration.sql` with `pglast` — passed
- local PGlite lifecycle execution — passed and produced the identifiers above
- `git diff --check -- supabase tests` — passed

## Production gate

This is a local proof, not a live Supabase proof. Production must remain paused until the migration and Edge Functions are applied to a non-production Supabase environment and the real HTTP endpoint is exercised with the Foundations profile, including Storage upload and PostgREST/RPC behavior. The repository has no local Supabase CLI/Deno/Postgres runtime or non-production credentials available in this environment, so that final environment-level check was not performed.
