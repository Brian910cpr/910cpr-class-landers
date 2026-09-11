# Issue 141 production schema contract

Captured 2026-09-11 by read-only `pg_catalog` / `information_schema` introspection against the connected production Supabase project. This artifact contains schema metadata only: no customer rows, secret values, tokens, or credentials.

This removes the schema-visibility blocker reported in `Codex_Reply_Issue141_R5.md`. PR #147 has also now been merged into `main`; use current `main` as the integration base for the next backend-only round.

## Common security state

RLS is enabled on all six tables below and `FORCE ROW LEVEL SECURITY` is false. `pg_policies` returned no explicit policies for these six tables.

## `public.class_sessions`

Columns, in ordinal order:

`id uuid NOT NULL DEFAULT gen_random_uuid()`; `source text NOT NULL`; `status text NOT NULL`; `course_id uuid NOT NULL`; `start_at timestamptz NOT NULL`; `end_at timestamptz`; `timezone text NOT NULL DEFAULT 'America/New_York'`; `consumption_start_at timestamptz`; `consumption_end_at timestamptz`; `lead_instructor_id uuid`; `location_id uuid NOT NULL`; `resource_id uuid`; `organization_id uuid`; `max_students integer NOT NULL`; `registration_backend text NOT NULL`; `visibility text NOT NULL`; `registration_status text NOT NULL`; `price numeric(10,2)`; `source_offer_id text`; `seed_id text`; `appointment_day_id text`; `matched_container_id text`; `external_class_id text`; `external_course_id text`; `course_sched_id text`; `external_location_id text`; `external_instructor_id text`; `registration_url text`; `public_notes text`; `created_at timestamptz NOT NULL DEFAULT now()`; `updated_at timestamptz NOT NULL DEFAULT now()`; `historical_student_count integer`; `source_seats integer`; `source_hours numeric`; `source_client_label text`; `source_instructor_label text`; `source_assistants_label text`; `source_location_label text`; `historical_imported_at timestamptz`; `historical_import_key text`; `advertised_duration_minutes integer`; `record_scope text NOT NULL DEFAULT 'operational'`.

Constraints:

- PK `(id)`.
- FKs: `course_id -> courses(id)`; `lead_instructor_id -> people(id)`; `location_id -> locations(id)`; `organization_id -> organizations(id)`; `resource_id -> resources(id)`.
- `end_at IS NULL OR end_at > start_at`.
- `max_students > 0`.
- `record_scope IN ('operational','historical')`.
- operational rows require non-null lead instructor, end time, and consumption window.
- consumption window must be both null or both present with end > start.
- historical rows require `historical_import_key`, `historical_imported_at`, non-public visibility, closed registration status, and a non-active/non-scheduled lifecycle state.

Indexes:

- unique PK `id`.
- unique `external_class_id` when non-null.
- unique `course_sched_id` when non-null.
- unique `historical_import_key` when non-null.
- additional unique `external_class_id` for `source='enrollware_history'`.
- schedule index `(start_at, course_id, lead_instructor_id, location_id)`.
- occupancy index `(consumption_start_at, consumption_end_at, lead_instructor_id, location_id, resource_id)`.
- `(record_scope, start_at)`.

Live non-internal triggers:

- `a_class_sessions_reconcile_historical_external_trg` BEFORE INSERT -> `class_sessions_reconcile_historical_external()`.
- `a_set_historical_session_scope` BEFORE INSERT OR UPDATE -> `set_historical_session_scope()`.
- `class_sessions_default_consumption_window_trg` BEFORE INSERT/UPDATE of time-window fields -> `class_sessions_default_consumption_window()`.
- `class_sessions_enforce_location_authority_trg` BEFORE INSERT/UPDATE of scope/location/visibility -> `enforce_session_location_authority()`.
- `seed_session_compliance_after_insert` AFTER INSERT -> `trg_seed_session_compliance()`.
- `skip_empty_enrollware_history_session` BEFORE INSERT OR UPDATE -> `skip_empty_enrollware_history_session()`.
- `trg_queue_completed_class_archive` AFTER UPDATE OF status -> `queue_completed_class_archive()`.

## `public.customers`

Columns: `id uuid NOT NULL DEFAULT gen_random_uuid()`; `first_name text NOT NULL`; `last_name text NOT NULL`; `email text`; `phone text`; `organization_id uuid`; `created_at timestamptz NOT NULL DEFAULT now()`; `updated_at timestamptz NOT NULL DEFAULT now()`.

Constraints/indexes: PK `id`; FK `organization_id -> organizations(id) ON DELETE SET NULL`; index on `lower(email)` where email is non-null.

## `public.registrations`

Columns: `id uuid NOT NULL DEFAULT gen_random_uuid()`; `customer_id uuid NOT NULL`; `class_session_id uuid NOT NULL`; `status text NOT NULL`; `registration_source text NOT NULL`; `external_registration_id text`; `created_at timestamptz NOT NULL DEFAULT now()`; `updated_at timestamptz NOT NULL DEFAULT now()`; `material_choice text`; `cancel_token_hash text`; `canceled_at timestamptz`; `optional_survey jsonb NOT NULL DEFAULT '{}'`; `nhcso_student_id uuid`; `historical_import_key text`; `historical_status text`; `historical_score text`; `historical_checked_in text`; `historical_ecard_code text`; `historical_codes text`; `historical_comments text`; `idempotency_key text`; `handoff_intent_id uuid`; `external_checkout_url text`; `external_checkout_state text`; `external_checkout_started_at timestamptz`; `external_reconciled_at timestamptz`; `external_reconciliation_evidence jsonb NOT NULL DEFAULT '{}'`.

Constraints/indexes:

- PK `id`.
- FK `customer_id -> customers(id)`.
- FK `class_session_id -> class_sessions(id) ON DELETE CASCADE`.
- FK `nhcso_student_id -> nhcso_students(id)`.
- unique `(customer_id, class_session_id)`.
- unique partial indexes for non-null `external_registration_id`, `historical_import_key`, `idempotency_key`, `handoff_intent_id`, and `nhcso_student_id`.
- index `(class_session_id)` and `(class_session_id,status)`.

No non-internal triggers were returned for this table.

## Connected operational tables

### `public.class_session_requirements`

Columns: `class_session_id uuid NOT NULL`; `requirement_key text NOT NULL`; `status text NOT NULL`; `evidence_document_id uuid`; `verified_at timestamptz`; `verified_by text`; `notes text`; `updated_at timestamptz NOT NULL DEFAULT now()`.

PK `(class_session_id,requirement_key)`; FK session -> `class_sessions(id) ON DELETE CASCADE`; FK evidence -> `nhcso_documents(id)`; status check allows `missing|received|verified|waived`.

### `public.session_card_processing`

Columns: `class_session_id uuid NOT NULL`; `status text NOT NULL`; `cards_required integer NOT NULL DEFAULT 0`; `cards_issued integer NOT NULL DEFAULT 0`; `missing_requirements jsonb NOT NULL DEFAULT '[]'`; `reviewed_at timestamptz`; `updated_at timestamptz NOT NULL DEFAULT now()`.

PK/FK `class_session_id -> class_sessions(id) ON DELETE CASCADE`; status `not_ready|ready_for_issue|issuing|issued|blocked`; card counts nonnegative and issued <= required.

### `public.class_session_audit`

Columns: `id uuid NOT NULL DEFAULT gen_random_uuid()`; `class_session_id uuid NOT NULL`; `event_key text NOT NULL`; `event_type text NOT NULL`; `actor_person_id uuid`; `actor_label text`; `occurred_at timestamptz NOT NULL`; `details jsonb NOT NULL DEFAULT '{}'`; `created_at timestamptz NOT NULL DEFAULT now()`.

PK `id`; unique `(class_session_id,event_key)`; FK session -> `class_sessions(id) ON DELETE CASCADE`; FK actor -> `people(id)`.

## Relevant live function contract observed

The production database currently contains, among others:

- `import_historical_class_batch(p_rows jsonb) returns jsonb` SECURITY DEFINER.
- `import_historical_registration_batch(p_rows jsonb) returns jsonb` SECURITY DEFINER.
- `promote_historical_registration_batch(p_rows jsonb, p_source_sha256 text, p_dry_run boolean default true) returns jsonb` SECURITY DEFINER.
- `class_sessions_reconcile_historical_external() returns trigger`.
- `set_historical_session_scope() returns trigger`.
- `class_sessions_default_consumption_window() returns trigger`.
- `enforce_session_location_authority() returns trigger`.
- `skip_empty_enrollware_history_session() returns trigger`.
- `populate_session_compliance_requirements(p_session_id uuid) returns integer` SECURITY DEFINER.
- `trg_seed_session_compliance() returns trigger` SECURITY DEFINER.
- `move_registration(...) returns jsonb`.
- `start_public_registration_intent(...) returns jsonb` SECURITY DEFINER.
- existing `landerware_record_corporate_registration(...) returns jsonb` SECURITY DEFINER for the newer durable LanderWare model.

The historical import function bodies introduced by PR #147 are now present in `main` as migrations and match the live production function family observed during introspection.

## Next safe implementation boundary

Backend-only. Do not enable outbound sends or the paused historical browser. Design the attendance/scheduling state slice against this live contract, add migration/database tests, preserve positive-fact attendance semantics and provenance gates, and keep all messaging disabled until those tests prove the fail-closed behavior.
