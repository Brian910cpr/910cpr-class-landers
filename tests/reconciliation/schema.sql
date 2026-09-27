create role anon; create role authenticated; create role service_role;
create table public.class_sessions (
id uuid not null default gen_random_uuid(),
source text not null ,
status text not null ,
course_id uuid not null ,
start_at timestamp with time zone not null ,
end_at timestamp with time zone  ,
timezone text not null default 'America/New_York'::text,
consumption_start_at timestamp with time zone  ,
consumption_end_at timestamp with time zone  ,
lead_instructor_id uuid  ,
location_id uuid not null ,
resource_id uuid  ,
organization_id uuid  ,
max_students integer not null ,
registration_backend text not null ,
visibility text not null ,
registration_status text not null ,
price numeric(10,2)  ,
source_offer_id text  ,
seed_id text  ,
appointment_day_id text  ,
matched_container_id text  ,
external_class_id text  ,
external_course_id text  ,
course_sched_id text  ,
external_location_id text  ,
external_instructor_id text  ,
registration_url text  ,
public_notes text  ,
created_at timestamp with time zone not null default now(),
updated_at timestamp with time zone not null default now(),
historical_student_count integer  ,
source_seats integer  ,
source_hours numeric  ,
source_client_label text  ,
source_instructor_label text  ,
source_assistants_label text  ,
source_location_label text  ,
historical_imported_at timestamp with time zone  ,
historical_import_key text  ,
advertised_duration_minutes integer  ,
record_scope text not null default 'operational'::text
);
CREATE UNIQUE INDEX class_sessions_pkey ON public.class_sessions USING btree (id);
CREATE UNIQUE INDEX class_sessions_external_class_unique ON public.class_sessions USING btree (external_class_id) WHERE (external_class_id IS NOT NULL);
CREATE UNIQUE INDEX class_sessions_course_sched_unique ON public.class_sessions USING btree (course_sched_id) WHERE (course_sched_id IS NOT NULL);
CREATE INDEX class_sessions_schedule_idx ON public.class_sessions USING btree (start_at, course_id, lead_instructor_id, location_id);
CREATE INDEX class_sessions_occupancy_idx ON public.class_sessions USING btree (consumption_start_at, consumption_end_at, lead_instructor_id, location_id, resource_id);
CREATE UNIQUE INDEX class_sessions_enrollware_history_external_class_uidx ON public.class_sessions USING btree (external_class_id) WHERE ((source = 'enrollware_history'::text) AND (external_class_id IS NOT NULL));
CREATE UNIQUE INDEX class_sessions_historical_import_key_uidx ON public.class_sessions USING btree (historical_import_key) WHERE (historical_import_key IS NOT NULL);
CREATE INDEX class_sessions_record_scope_start_idx ON public.class_sessions USING btree (record_scope, start_at);
create table public.courses (
id uuid not null default gen_random_uuid(),
course_key text not null ,
name text not null ,
course_family text  ,
subtype text  ,
certifying_body text  ,
delivery_mode text  ,
duration_minutes integer  ,
setup_buffer_minutes integer not null default 0,
cleanup_buffer_minutes integer not null default 0,
max_students_default integer  ,
base_price numeric(10,2)  ,
registration_backend_default text  ,
visibility_default text  ,
enrollware_course_id text  ,
created_at timestamp with time zone not null default now(),
updated_at timestamp with time zone not null default now()
);
CREATE UNIQUE INDEX courses_pkey ON public.courses USING btree (id);
CREATE UNIQUE INDEX courses_course_key_key ON public.courses USING btree (course_key);
CREATE UNIQUE INDEX courses_enrollware_course_id_key ON public.courses USING btree (enrollware_course_id);
create table public.customers (
id uuid not null default gen_random_uuid(),
first_name text not null ,
last_name text not null ,
email text  ,
phone text  ,
organization_id uuid  ,
created_at timestamp with time zone not null default now(),
updated_at timestamp with time zone not null default now()
);
CREATE UNIQUE INDEX customers_pkey ON public.customers USING btree (id);
CREATE INDEX customers_email_idx ON public.customers USING btree (lower(email)) WHERE (email IS NOT NULL);
create table public.ingest_facts (
id uuid not null default gen_random_uuid(),
ingest_job_id uuid not null ,
fact_type text not null ,
source_locator jsonb not null default '{}'::jsonb,
proposed_value jsonb not null ,
matched_entity_type text  ,
matched_entity_id uuid  ,
confidence numeric(5,4)  ,
resolution text not null default 'proposed'::text,
resolution_reason text  ,
resolved_at timestamp with time zone  ,
created_at timestamp with time zone not null default now(),
deterministic_key text  ,
committed_at timestamp with time zone
);
CREATE UNIQUE INDEX ingest_facts_pkey ON public.ingest_facts USING btree (id);
CREATE INDEX ingest_facts_job_idx ON public.ingest_facts USING btree (ingest_job_id);
CREATE INDEX ingest_facts_resolution_idx ON public.ingest_facts USING btree (resolution);
CREATE UNIQUE INDEX ingest_facts_job_deterministic_uidx ON public.ingest_facts USING btree (ingest_job_id, deterministic_key) WHERE (deterministic_key IS NOT NULL);
create table public.ingest_jobs (
id uuid not null default gen_random_uuid(),
source_kind text not null ,
source_name text not null ,
source_ref text  ,
sha256 text  ,
mime_type text  ,
status text not null default 'queued'::text,
parser_status text not null default 'pending'::text,
ai_status text not null default 'not_needed'::text,
review_status text not null default 'none'::text,
document_type text  ,
metadata jsonb not null default '{}'::jsonb,
error text  ,
created_at timestamp with time zone not null default now(),
updated_at timestamp with time zone not null default now(),
completed_at timestamp with time zone  ,
priority integer not null default 100,
attempt_count integer not null default 0,
started_at timestamp with time zone  ,
locked_at timestamp with time zone  ,
lock_owner text  ,
next_attempt_at timestamp with time zone
);
CREATE UNIQUE INDEX ingest_jobs_pkey ON public.ingest_jobs USING btree (id);
CREATE UNIQUE INDEX ingest_jobs_sha256_uidx ON public.ingest_jobs USING btree (sha256) WHERE (sha256 IS NOT NULL);
CREATE INDEX ingest_jobs_worker_idx ON public.ingest_jobs USING btree (status, next_attempt_at, priority, created_at);
create table public.ingest_review_queue (
id uuid not null default gen_random_uuid(),
ingest_job_id uuid not null ,
ingest_fact_id uuid  ,
review_type text not null ,
question text not null ,
candidates jsonb not null default '[]'::jsonb,
status text not null default 'open'::text,
decision jsonb  ,
created_at timestamp with time zone not null default now(),
decided_at timestamp with time zone
);
CREATE UNIQUE INDEX ingest_review_queue_pkey ON public.ingest_review_queue USING btree (id);
CREATE INDEX ingest_review_queue_status_idx ON public.ingest_review_queue USING btree (status, created_at);
CREATE UNIQUE INDEX ingest_review_queue_historical_fact_uidx ON public.ingest_review_queue USING btree (ingest_job_id, ingest_fact_id, review_type) WHERE (ingest_fact_id IS NOT NULL);
create table public.locations (
id uuid not null default gen_random_uuid(),
location_key text not null ,
name text not null ,
address_line1 text  ,
address_line2 text  ,
city text  ,
state text  ,
postal_code text  ,
public boolean not null default false,
enrollware_location_id text  ,
created_at timestamp with time zone not null default now(),
updated_at timestamp with time zone not null default now(),
scheduling_status text not null default 'inactive'::text
);
CREATE UNIQUE INDEX locations_pkey ON public.locations USING btree (id);
CREATE UNIQUE INDEX locations_location_key_key ON public.locations USING btree (location_key);
CREATE INDEX locations_scheduling_status_idx ON public.locations USING btree (scheduling_status, name);
create table public.people (
id uuid not null default gen_random_uuid(),
person_key text  ,
display_name text not null ,
email text  ,
phone text  ,
active boolean not null default true,
enrollware_instructor_id text  ,
external_reference text  ,
created_at timestamp with time zone not null default now(),
updated_at timestamp with time zone not null default now()
);
CREATE UNIQUE INDEX people_pkey ON public.people USING btree (id);
CREATE UNIQUE INDEX people_person_key_key ON public.people USING btree (person_key);
create table public.registrations (
id uuid not null default gen_random_uuid(),
customer_id uuid not null ,
class_session_id uuid not null ,
status text not null ,
registration_source text not null ,
external_registration_id text  ,
created_at timestamp with time zone not null default now(),
updated_at timestamp with time zone not null default now(),
material_choice text  ,
cancel_token_hash text  ,
canceled_at timestamp with time zone  ,
optional_survey jsonb not null default '{}'::jsonb,
nhcso_student_id uuid  ,
historical_import_key text  ,
historical_status text  ,
historical_score text  ,
historical_checked_in text  ,
historical_ecard_code text  ,
historical_codes text  ,
historical_comments text  ,
idempotency_key text  ,
handoff_intent_id uuid  ,
external_checkout_url text  ,
external_checkout_state text  ,
external_checkout_started_at timestamp with time zone  ,
external_reconciled_at timestamp with time zone  ,
external_reconciliation_evidence jsonb not null default '{}'::jsonb
);
CREATE UNIQUE INDEX registrations_pkey ON public.registrations USING btree (id);
CREATE UNIQUE INDEX registrations_customer_id_class_session_id_key ON public.registrations USING btree (customer_id, class_session_id);
CREATE UNIQUE INDEX registrations_external_registration_unique ON public.registrations USING btree (external_registration_id) WHERE (external_registration_id IS NOT NULL);
CREATE INDEX registrations_class_session_idx ON public.registrations USING btree (class_session_id);
CREATE INDEX registrations_session_status_idx ON public.registrations USING btree (class_session_id, status);
CREATE UNIQUE INDEX registrations_nhcso_student_unique ON public.registrations USING btree (nhcso_student_id) WHERE (nhcso_student_id IS NOT NULL);
CREATE UNIQUE INDEX registrations_historical_import_key_uidx ON public.registrations USING btree (historical_import_key) WHERE (historical_import_key IS NOT NULL);
CREATE UNIQUE INDEX registrations_idempotency_key_unique ON public.registrations USING btree (idempotency_key) WHERE (idempotency_key IS NOT NULL);
CREATE UNIQUE INDEX registrations_handoff_intent_unique ON public.registrations USING btree (handoff_intent_id) WHERE (handoff_intent_id IS NOT NULL);
