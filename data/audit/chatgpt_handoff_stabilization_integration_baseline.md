# 910CPR stabilization and integration baseline

Date: 2026-08-31  
Production project: `wktwgcnwdvbebcobgyey`  
Baseline: `origin/main@6575c4e7f30fd811786340a5a113ed3769c77db3`  
Integration branch/worktree: `codex/stabilization-integration` at `E:\GitHub\910cpr-class-landers-stabilization`

## Status labels

- **Deployed:** `public-event-registration` version 8 and the RLS migration described below.
- **Changed in repo:** production function sources, Heartsaver safe-route change, RLS migration, regression test, and this handoff.
- **Not deployed:** the static Heartsaver redirect and the environment-only Stripe webhook source.
- **Preserved:** the dirty primary checkout was not edited, reset, cleaned, rebased, or used as the implementation baseline. Its unique work remains intact.
- **Known unrelated worktree difference:** `docs/Earl/index.html` appeared modified immediately after worktree creation and is intentionally excluded from this branch's commit.

## 1. Urgent production fixes

### Special-event endpoint — completed and deployed

Root cause: the deployed function relied on inferred PostgREST relationships for `class_sessions -> courses/locations/people`. The production relationships are now selected by their explicit foreign-key names:

- `class_sessions_course_id_fkey`
- `class_sessions_location_id_fkey`
- `class_sessions_lead_instructor_id_fkey`

The function also no longer attempts to write the absent `registration_surveys` table; it stores the JSON in the existing `registrations.optional_survey` column.

Production verification after version 8 deployment: GET for the Earl event returned HTTP 200 with the real course, location, instructor, and remaining seats.

Consumers found: `docs/Earl/index.html`. No other repository consumer was found.

### MAXIM billing-code rules RLS — completed and deployed

Intended access is trusted server-side access from MAXIM Edge Functions using the service role. No browser needs direct table access. Migration `secure_maxim_billing_code_rules`:

- enables RLS;
- revokes all table privileges from `anon` and `authenticated`;
- preserves `service_role` access.

Production grants now list only `postgres` and `service_role`.

### Heartsaver route — source correction complete; publication remains

Root cause: the static page submits to undeployed `landerware-registration`, whose required `landerware_*` schema is also absent from production. Deploying that function would create or depend on a competing participant model and was rejected.

The narrow correction routes `/register/heartsaver-skills/` to the existing live `/heartsaver.html` session chooser. This prevents false confirmation and preserves Enrollware as the current intake channel until canonical participant intake exists. The static change is not live until the normal site publication workflow promotes it.

Other consumer: `docs/certificate-submit/index.html` calls the same undeployed function's requirement endpoint. It is currently an orphaned follow-up route and must remain out of active registration flows; it should later be reconnected to canonical registration requirements.

### Stripe signing secret — source corrected; production rotation/configuration remains

The deployed function contains a hard-coded signing secret. The recovered source has been sanitized and now reads only `STRIPE_WEBHOOK_SECRET` from Edge Function secrets and fails closed if it is absent. The secret value is not present in the repository, tests, or this report.

Because the secret was embedded in deployed source, it must be treated as exposed and rotated in Stripe. The current tool surface cannot create/rotate a Stripe webhook endpoint secret or set a Supabase project secret. Therefore the environment-only function has deliberately **not** been deployed: doing so before configuration would reject legitimate webhooks.

Required operator sequence:

1. Rotate the endpoint signing secret in Stripe.
2. Set the new value as Supabase Edge Function secret `STRIPE_WEBHOOK_SECRET`.
3. Deploy the repository version of `stripe-registration-webhook`.
4. Send a signed Stripe test event and verify the order and registration transition.
5. Retire the old endpoint secret.

## 2. PR #109 reconciliation

PR #109 head is `27b50e8ea181f38319391b4e28560405598b8803`.

Already represented in production:

- NHCSO durable recovery database objects and promotion into canonical `class_sessions` / `registrations`;
- deployed `nhcso-workspace`;
- deployed production-board attention behavior.

Not in `main`:

- the PR migration source, Edge Function source, tests, admin attention summary, dashboard wiring, and NHCSO page changes.

The production migration timestamp differs from the PR filename, so the PR migration must not be replayed blindly. Safest integration: import the exact deployed migration/function definitions as an idempotent production-baseline commit, then separately review the static UI and notification/outbox behavior. Do not merge the whole PR as a unit.

## 3. PR #114 reconciliation

PR #114 head is `7f9788de55ac54cb529a43ed9f4043648efc000a`.

The corrected implementation uses canonical `class_sessions`, `registrations.class_session_id`, `courses`, `locations`, and instructor `people`; includes display names; includes only committed operational statuses; and does not treat capacity as participant count. It is not deployed or merged.

It remains required for durable session projection and workspace read behavior. It must be rebased/reconciled after the PR #109 production-baseline commit because both touch the admin dashboard and production data flow. Deploy `session-workspace` only after its schema-contract and durable-only projection tests pass against the captured production schema. Do not bring forward any earlier `landerware_sessions` or `landerware_registrations` assumptions.

## 4. Canonical lifecycle authority

The production authority is:

`customers.id -> registrations.customer_id -> registrations.class_session_id -> class_sessions.id`

A registration row is the current roster membership. There is no need for a second roster-membership table for ordinary participation.

Supporting production objects:

- Sessions: `class_sessions`, `courses`, `locations`, `class_session_instructors`
- Participant identity: `customers`
- Staff/instructor identity: `people`
- Employer: `organizations`, with `customers.organization_id` and `class_sessions.organization_id`
- Registration/roster: `registrations`, unique on `(customer_id, class_session_id)`
- Payment: `registration_orders`, one-to-one with `registrations`
- Materials: `registration_order_items -> products`, optionally `product_inventory_units`
- Session requirements/documents: `class_session_requirements`, `class_session_documents`
- Card operations: `session_card_processing`
- Session audit: `class_session_audit`

Gaps that cannot yet be represented cleanly:

- registration-level requirement/evidence records;
- participant-level completion and issued credential/card records;
- durable reschedule/supersession linkage between registrations;
- general participant lifecycle events;
- stable external identity aliases beyond the existing external registration fields;
- explicit uncertainty/provenance records for historical imports.

`session_card_processing` is an aggregate session workflow record, not participant completion history.

## 5. Shared commands

### `register_participant`

One transactional, security-definer database command should accept:

- normalized customer identity or an existing `customer_id`;
- `class_session_id`;
- course/credential context validated from the session;
- source/persona and idempotency key;
- payment state;
- material/product selections;
- notes and registration-level requirements;
- source provenance/external identifiers.

It should atomically:

1. resolve/create one canonical customer;
2. resolve/create one canonical registration;
3. preserve the unique active relationship and idempotency;
4. create/update the registration order and items when applicable;
5. create requirement records;
6. append an immutable activity/audit event;
7. return customer, registration, session, roster, payment/material, and event identifiers.

Retail, Admin, Corporate, Instructor walk-in, and Enrollware ingestion must call this same command with different authorization and entry context.

### `move_registration`

One transactional command should:

- lock and validate the source registration;
- reject a duplicate active target registration;
- create or reactivate the target registration;
- link source and target by supersession/reschedule records;
- transfer or explicitly retain financial and material associations under a documented rule;
- never rewrite historical completion/card facts;
- append audit/activity events for both sessions;
- return both registration identities.

A walk-in is `register_participant(source='instructor_walk_in')`, not a separate roster model. Enrollware is `register_participant(source='enrollware', external_identity=...)`.

## 6. Reusable `landerware_*` machinery mapping

| Reusable concept | Canonical destination |
|---|---|
| create/find person and identity aliases | `customers` plus a new customer-identity-alias table |
| atomic `landerware_register` orchestration | new `register_participant` RPC over canonical tables |
| sessions | `class_sessions`; do not create `landerware_sessions` |
| registrations/roster memberships | `registrations`; do not create parallel registration/roster rows |
| organization membership | existing `customers.organization_id` initially; add dated many-to-many only if required |
| registration requirements and submission tokens | new registration-scoped requirement/evidence tables linked to `registrations` and existing document machinery |
| activity events | immutable canonical participant/registration event table; session events may also project to `class_session_audit` |
| completions and credentials | new participant registration completion/credential tables linked to `registrations` and `customers` |
| documents | extend canonical session document approach with registration/customer ownership |
| confirmation profiles/templates | reusable configuration, but it must invoke canonical commands |

## 7. Duplicate representations to retire later

After canonical replacements and data reconciliation exist, retire or archive:

- undeployed `landerware_people`, `landerware_sessions`, `landerware_registrations`, `landerware_rosters`, and `landerware_roster_memberships` schema proposals;
- persona-specific registration writes that bypass `registrations`;
- MAXIM request state as a lifecycle authority (retain it as intake/workflow provenance);
- NHCSO-specific participant/session copies after continuous canonical synchronization is proven;
- any projection treating Enrollware rows as the durable participant relationship.

Do not delete existing data during this stabilization work.

## 8. Historical import prerequisites

Before importing:

- immutable source record ID, file/document provenance, extraction version, and import batch;
- normalized matching strategy with exact-match keys and an ambiguity queue;
- dry-run output showing create/match/skip/conflict counts and reasons;
- idempotency constraints and restart checkpoints;
- explicit rules for reschedules, duplicates, cancellations, completion, cards, employer links, products, and unknown payment allocations;
- uncertainty fields that never turn missing evidence into facts;
- precedence rules preventing historical rows from overwriting newer authoritative customer/session data;
- document attachment keys resolving to customer + registration + session;
- reconciliation reports and rollback-by-batch capability.

## 9. Readiness and exact next instruction

The integration branch is the safe baseline, but source control still does not fully explain production because PR #109's deployed artifacts remain outside `main`, the Stripe secret has not been rotated/configured, and the canonical shared commands plus import identity/provenance structures do not exist.

Exact next implementation instruction:

> On `codex/stabilization-integration`, first capture PR #109's exact deployed database and Edge Function definitions in an idempotent production-baseline commit without replaying its already-applied data migration. Then implement one reviewed migration that adds canonical customer identity aliases, registration supersession, registration requirements/evidence, participant lifecycle events, and participant completion/credential records, together with transactional `register_participant` and `move_registration` RPCs over `customers -> registrations -> class_sessions`. Add dry-run contract tests for idempotency, ambiguous identity, duplicate active registration, reschedule history, payment/material preservation, and Enrollware replay. Do not build persona UIs or run the historical import.

## Genuine historical-import blockers

- No canonical idempotent registration command or stable external customer identity-alias contract.
- No durable reschedule/supersession model, so imported moves can duplicate active participation or erase history.
- No participant-level completion/credential model, so historical cards cannot be attached without misassociation.
- No source-provenance/ambiguity/import-batch contract, so historical identity matches could silently corrupt current records.

**HISTORY IMPORT NOT READY**

