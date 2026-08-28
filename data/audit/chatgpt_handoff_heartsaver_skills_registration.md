# ChatGPT handoff: Heartsaver Skills unified registration

## Goal and branch

- Branch: `codex/heartsaver-skills-registration`
- Goal: one durable LanderWare Person + Registration pathway for the unlisted Heartsaver Skills page and MAXIM scheduling.

## Discovery

- Production MAXIM UI: `docs/corp/maxim.html`.
- Active MAXIM backend before this change: `supabase/functions/maxim-portal/index.ts` writing `maxim_employee_profiles` and `maxim_registration_requests`.
- Best existing durable model: migration `supabase/migrations/20260810020058_maxim_durable_records.sql`, originally developed on `codex/maxim-durable-corporate-portal` and incorporated here as commit `efb95208d3a`.
- Durable tables: `landerware_people`, `landerware_registrations`, `landerware_sessions`, `landerware_certification_requirements`, `landerware_documents`, `landerware_messages`, organizations, relationships, rosters, credentials, activity, and opaque self-service tokens.
- Earl native registration page: `docs/earl/index.html`; its backend is the separate public event registration endpoint and is not the durable identity-aware service requested here.
- Existing email convention in the durable model is a Gmail-backed `landerware_messages` queue. No queue consumer or usable Gmail/Supabase deployment credential is present in this worktree.
- Existing certificate/document mechanism is `landerware_documents` plus requirement/registration `document_ids`; this implementation reuses and completes that model with a registration-scoped opaque submission token.

## Authoritative implementation

### Registration-profile generalization (2026-08-27, production still paused)

The core is now configuration-driven. `landerware_registration_profiles` stores course identity, visibility, registration/session mode, allowed entry contexts, required fields, generic requirement definitions, addons, payer/pricing policy, corporate context, confirmation template, and completion prerequisites. `landerware_registration_requirements` creates durable per-registration requirement instances with three timing gates, upload-now/submit-later behavior, and staff satisfaction permission. `landerware_confirmation_templates` removes confirmation copy from the shared handler.

The single Edge route is now `POST /landerware-registration/register/<profile-key>`. It loads the profile, invokes `landerware_register`, processes configured upload fields, creates generic requirement-submission tokens, and renders the configured confirmation template. It contains no Heartsaver course or requirement constants. Heartsaver and MAXIM differ only by profile data and their specialized UI/input preparation.

Adding another LanderWare-only course now requires course/profile/template configuration rows. It does not require a new Edge Function or backend registration handler.

- `supabase/migrations/20260827220000_landerware_unified_registration.sql`
  - creates course `aha-heartsaver-skills-session` with no Enrollware ID and `listed=false`;
  - creates `landerware_create_or_find_person` using normalized case-insensitive email, with name+phone fallback;
  - creates `landerware_register`, the single registration operation used by public Heartsaver and MAXIM;
  - adds idempotency, optional session assignment, requirement type/status, document-submission tokens, and a private 10 MB file bucket.
- `supabase/functions/landerware-registration/index.ts`
  - public registration;
  - optional immediate certificate upload;
  - secure later upload to the same person/registration/requirement;
  - token expiry, missing/type/size validation, checksum duplicate handling;
  - confirmation queued through existing `landerware_messages` Gmail convention.
- `supabase/functions/maxim-portal/index.ts`
  - Add Student durable-person creation now uses `landerware_create_or_find_person`;
  - Schedule for Them and self-service `/go/` registration ultimately use `landerware_register`;
  - legacy MAXIM tables remain as a backwards-compatible projection and retain foreign-key links to durable records.
- `docs/register/heartsaver-skills/index.html`: unlisted/noindex direct-link registration UI.
- `docs/certificate-submit/index.html`: opaque-token certificate-later UI.
- `docs/admin/dashboard.html`: adds the course to LanderWare session creation choices.
- `tests/test_heartsaver_skills_registration.py`: focused contract tests.

## Validation results

Commands:

```text
node --check supabase/functions/landerware-registration/index.ts
node --check supabase/functions/maxim-portal/index.ts
python -m unittest tests.test_heartsaver_skills_registration
git diff --check
```

Result: 7 focused tests passed; both Edge functions parsed; both public inline scripts parsed; diff check passed.

Broader command:

```text
python -m unittest tests.test_heartsaver_skills_registration tests.test_maxim_corporate_portal
```

Result: 49 passed, 2 failed. Both failures concern pre-existing generated selector pages (`docs/bls.html` projection helper and `docs/corp/maxim-schedule.html` date-bound marker), not the registration files changed here.

## Exact duplicate/identity proof encoded in implementation

1. Public Heartsaver calls `rpc/landerware_register`.
2. `landerware_register` calls `landerware_create_or_find_person` under a transaction advisory lock.
3. Normalized email is matched case-insensitively; the earliest existing active person wins.
4. A subsequent course registration inserts another `landerware_registrations` row referencing that same person.
5. MAXIM Add Student calls the same person RPC, and MAXIM scheduling calls the same registration RPC with the durable person ID.
6. No migration deletes or rewrites historical registrations or MAXIM records.

## Certificate-later proof encoded in implementation

The raw token is never stored. Its SHA-256 record contains exact `person_id`, `registration_id`, and `requirement_id`. Upload creates `landerware_documents.related_record_ids` with those same three IDs, appends the document ID to the existing requirement and registration, and sets the original requirement to `satisfied`.

## Blockers / open verification

- No Supabase CLI, Docker, `SUPABASE_URL`, or service-role credential is available locally. The migration and Edge function could not be applied/deployed or exercised against the production database.
- The repository contains no working Gmail queue consumer. Confirmation rows are durably queued with `delivery_provider=gmail`, but actual delivery cannot be claimed until that existing operational gap is connected.
- The isolated worktree acquired an unrelated unstaged `docs/Earl/index.html` modification during checkout. It was intentionally preserved and excluded from this task's staging/commit.
- Required production journey test (Jane across Heartsaver, certificate-later, second course, and MAXIM) must run after migration/function deployment using a test email, then verify one `landerware_people` row and three related registrations.

## Deployment order

1. Apply `20260810020058_maxim_durable_records.sql` if production does not already have it.
2. Apply `20260827220000_landerware_unified_registration.sql`.
3. Deploy `landerware-registration` and the updated `maxim-portal` Edge functions.
4. Connect/verify the existing Gmail queue sender.
5. Deploy the public/static pages from the branch through the normal production host.
6. Run the Jane identity/certificate journey and verify live HTML, API calls, database rows, and received email.
