-- Production schema metadata read only, 2026-10-19. No row data.
-- Focused local fixture: production columns/defaults/PK/unique/check constraints; foreign keys and triggers omitted.
do $$ begin
 if not exists(select 1 from pg_roles where rolname='anon') then create role anon; end if;
 if not exists(select 1 from pg_roles where rolname='authenticated') then create role authenticated; end if;
 if not exists(select 1 from pg_roles where rolname='service_role') then create role service_role; end if;
end $$;
create table public.class_sessions (id uuid default gen_random_uuid() not null,
source text not null,
status text not null,
course_id uuid not null,
start_at timestamp with time zone not null,
end_at timestamp with time zone,
timezone text default 'America/New_York'::text not null,
consumption_start_at timestamp with time zone,
consumption_end_at timestamp with time zone,
lead_instructor_id uuid,
location_id uuid not null,
resource_id uuid,
organization_id uuid,
max_students integer not null,
registration_backend text not null,
visibility text not null,
registration_status text not null,
price numeric(10,2),
source_offer_id text,
seed_id text,
appointment_day_id text,
matched_container_id text,
external_class_id text,
external_course_id text,
course_sched_id text,
external_location_id text,
external_instructor_id text,
registration_url text,
public_notes text,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null,
historical_student_count integer,
source_seats integer,
source_hours numeric,
source_client_label text,
source_instructor_label text,
source_assistants_label text,
source_location_label text,
historical_imported_at timestamp with time zone,
historical_import_key text,
advertised_duration_minutes integer,
record_scope text default 'operational'::text not null,
external_reconciliation jsonb default '{}'::jsonb not null,
external_session_evidence jsonb default '{}'::jsonb not null);
create table public.courses (id uuid default gen_random_uuid() not null,
course_key text not null,
name text not null,
course_family text,
subtype text,
certifying_body text,
delivery_mode text,
duration_minutes integer,
setup_buffer_minutes integer default 0 not null,
cleanup_buffer_minutes integer default 0 not null,
max_students_default integer,
base_price numeric(10,2),
registration_backend_default text,
visibility_default text,
enrollware_course_id text,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null);
create table public.customers (id uuid default gen_random_uuid() not null,
first_name text not null,
last_name text not null,
email text,
phone text,
organization_id uuid,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null);
create table public.instructor_qualifications (id uuid default gen_random_uuid() not null,
instructor_id uuid not null,
course_id uuid,
qualification_key text,
status text,
expires_at timestamp with time zone,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null);
create table public.landerware_messages (id uuid default gen_random_uuid() not null,
person_id uuid,
registration_id uuid,
template_key text not null,
channel text default 'email'::text not null,
recipient text,
subject text not null,
body_text text not null,
delivery_provider text default 'gmail'::text not null,
delivery_status text default 'pending'::text not null,
idempotency_key text not null,
provider_message_id text,
provider_thread_id text,
sent_at timestamp with time zone,
failed_at timestamp with time zone,
failure_detail text,
created_at timestamp with time zone default now() not null,
customer_id uuid,
operational_registration_id uuid);
create table public.landerware_public_order_students (id uuid default gen_random_uuid() not null,
order_id uuid not null,
first_name text not null,
last_name text not null,
email text not null,
phone text not null,
unit_amount integer not null,
selected_addons jsonb default '[]'::jsonb not null,
registration_id uuid,
created_at timestamp with time zone default now() not null,
billing_code text,
discount integer default 0 not null,
selected_options jsonb default '{}'::jsonb not null);
create table public.landerware_public_orders (id uuid default gen_random_uuid() not null,
recovery_token uuid default gen_random_uuid() not null,
idempotency_key text not null,
external_class_id text not null,
class_session_id uuid,
course_id text not null,
payer_email text not null,
payer_phone text,
status text default 'held'::text not null,
currency text default 'usd'::text not null,
subtotal integer default 0 not null,
discount integer default 0 not null,
total integer default 0 not null,
billing_code text,
stripe_checkout_session_id text,
stripe_payment_intent_id text,
checkout_url text,
hold_expires_at timestamp with time zone default (now() + '00:30:00'::interval) not null,
paid_at timestamp with time zone,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null);
create table public.landerware_public_session_inventory (external_class_id text not null,
capacity integer,
externally_registered integer default 0 not null,
source text default 'enrollware'::text not null,
imported_at timestamp with time zone default now() not null);
create table public.landerware_sessions (id uuid default gen_random_uuid() not null,
external_session_id text,
course_id text not null,
course_name text not null,
starts_at timestamp with time zone not null,
ends_at timestamp with time zone,
location_name text,
instructor_id uuid,
instructor_name text,
organization_id uuid,
lifecycle_state text default 'create'::text not null,
provenance text not null,
workspace_schema_version text default 'landerware.session-workspace.v1'::text not null,
requirements_manifest jsonb not null,
document_ids jsonb default '[]'::jsonb not null,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null,
class_session_id uuid);
create table public.locations (id uuid default gen_random_uuid() not null,
location_key text not null,
name text not null,
address_line1 text,
address_line2 text,
city text,
state text,
postal_code text,
public boolean default false not null,
enrollware_location_id text,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null,
scheduling_status text default 'inactive'::text not null);
create table public.participant_completions (id uuid default gen_random_uuid() not null,
customer_id uuid not null,
registration_id uuid not null,
class_session_id uuid not null,
course_id uuid not null,
completion_status text not null,
completed_at timestamp with time zone,
source_system text not null,
source_record_identity text,
evidence jsonb default '{}'::jsonb not null,
confidence numeric(5,4),
recorded_by text not null,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null);
create table public.participant_lifecycle_events (id uuid default gen_random_uuid() not null,
event_key text not null,
event_type text not null,
customer_id uuid,
registration_id uuid,
class_session_id uuid,
related_registration_id uuid,
source text not null,
actor jsonb default '{}'::jsonb not null,
occurred_at timestamp with time zone default now() not null,
details jsonb default '{}'::jsonb not null,
import_record_id uuid,
correction_of_event_id uuid,
created_at timestamp with time zone default now() not null);
create table public.people (id uuid default gen_random_uuid() not null,
person_key text,
display_name text not null,
email text,
phone text,
active boolean default true not null,
enrollware_instructor_id text,
external_reference text,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null);
create table public.registration_orders (id uuid default gen_random_uuid() not null,
registration_id uuid not null,
status text default 'payment_pending'::text not null,
currency text default 'usd'::text not null,
course_amount numeric(10,2) default 0 not null,
materials_amount numeric(10,2) default 0 not null,
total_amount numeric(10,2) default 0 not null,
stripe_checkout_session_id text,
stripe_payment_intent_id text,
paid_at timestamp with time zone,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null);
create table public.registration_requirements (id uuid default gen_random_uuid() not null,
registration_id uuid not null,
requirement_key text not null,
requirement_type text not null,
state text not null,
source text not null,
notes text,
satisfied_at timestamp with time zone,
satisfied_by text,
superseded_from_requirement_id uuid,
provenance jsonb default '{}'::jsonb not null,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null);
create table public.registration_supersessions (id uuid default gen_random_uuid() not null,
idempotency_key text not null,
source_registration_id uuid not null,
target_registration_id uuid not null,
source_session_id uuid not null,
target_session_id uuid not null,
reason text not null,
source text not null,
actor jsonb not null,
financial_policy text not null,
transferred_order_id uuid,
occurred_at timestamp with time zone default now() not null,
details jsonb default '{}'::jsonb not null);
create table public.registrations (id uuid default gen_random_uuid() not null,
customer_id uuid not null,
class_session_id uuid not null,
status text not null,
registration_source text not null,
external_registration_id text,
created_at timestamp with time zone default now() not null,
updated_at timestamp with time zone default now() not null,
material_choice text,
cancel_token_hash text,
canceled_at timestamp with time zone,
optional_survey jsonb default '{}'::jsonb not null,
nhcso_student_id uuid,
historical_import_key text,
historical_status text,
historical_score text,
historical_checked_in text,
historical_ecard_code text,
historical_codes text,
historical_comments text,
idempotency_key text,
handoff_intent_id uuid,
external_checkout_url text,
external_checkout_state text,
external_checkout_started_at timestamp with time zone,
external_reconciled_at timestamp with time zone,
external_reconciliation_evidence jsonb default '{}'::jsonb not null);
alter table public.class_sessions add constraint class_sessions_consumption_window_check CHECK ((((consumption_start_at IS NULL) AND (consumption_end_at IS NULL)) OR ((consumption_start_at IS NOT NULL) AND (consumption_end_at IS NOT NULL) AND (consumption_end_at > consumption_start_at))));
alter table public.class_sessions add constraint class_sessions_end_after_start_check CHECK (((end_at IS NULL) OR (end_at > start_at)));
alter table public.class_sessions add constraint class_sessions_historical_contract_check CHECK (((record_scope <> 'historical'::text) OR ((historical_import_key IS NOT NULL) AND (historical_imported_at IS NOT NULL) AND (visibility <> 'public'::text) AND (registration_status = 'closed'::text) AND (status <> ALL (ARRAY['scheduled'::text, 'active'::text, 'proposed_window'::text, 'draft'::text, 'tentative'::text, 'pending'::text])))));
alter table public.class_sessions add constraint class_sessions_max_students_check CHECK ((max_students > 0));
alter table public.class_sessions add constraint class_sessions_operational_fields_check CHECK (((record_scope <> 'operational'::text) OR ((lead_instructor_id IS NOT NULL) AND (end_at IS NOT NULL) AND (consumption_start_at IS NOT NULL) AND (consumption_end_at IS NOT NULL))));
alter table public.class_sessions add constraint class_sessions_pkey PRIMARY KEY (id);
alter table public.class_sessions add constraint class_sessions_record_scope_check CHECK ((record_scope = ANY (ARRAY['operational'::text, 'historical'::text])));
alter table public.courses add constraint courses_course_key_key UNIQUE (course_key);
alter table public.courses add constraint courses_enrollware_course_id_key UNIQUE (enrollware_course_id);
alter table public.courses add constraint courses_pkey PRIMARY KEY (id);
alter table public.customers add constraint customers_pkey PRIMARY KEY (id);
alter table public.instructor_qualifications add constraint instructor_qualifications_check CHECK (((course_id IS NOT NULL) OR (qualification_key IS NOT NULL)));
alter table public.instructor_qualifications add constraint instructor_qualifications_pkey PRIMARY KEY (id);
alter table public.landerware_messages add constraint landerware_messages_idempotency_key_key UNIQUE (idempotency_key);
alter table public.landerware_messages add constraint landerware_messages_pkey PRIMARY KEY (id);
alter table public.landerware_public_order_students add constraint landerware_public_order_students_discount_check CHECK ((discount >= 0));
alter table public.landerware_public_order_students add constraint landerware_public_order_students_pkey PRIMARY KEY (id);
alter table public.landerware_public_orders add constraint landerware_public_orders_idempotency_key_key UNIQUE (idempotency_key);
alter table public.landerware_public_orders add constraint landerware_public_orders_pkey PRIMARY KEY (id);
alter table public.landerware_public_orders add constraint landerware_public_orders_recovery_token_key UNIQUE (recovery_token);
alter table public.landerware_public_orders add constraint landerware_public_orders_status_check CHECK ((status = ANY (ARRAY['held'::text, 'checkout_open'::text, 'paid'::text, 'expired'::text, 'cancelled'::text, 'refunded'::text])));
alter table public.landerware_public_orders add constraint landerware_public_orders_stripe_checkout_session_id_key UNIQUE (stripe_checkout_session_id);
alter table public.landerware_public_session_inventory add constraint landerware_public_session_inventory_capacity_check CHECK (((capacity IS NULL) OR (capacity >= 0)));
alter table public.landerware_public_session_inventory add constraint landerware_public_session_inventory_externally_registered_check CHECK ((externally_registered >= 0));
alter table public.landerware_public_session_inventory add constraint landerware_public_session_inventory_pkey PRIMARY KEY (external_class_id);
alter table public.landerware_sessions add constraint landerware_sessions_external_session_id_course_id_starts_at_key UNIQUE (external_session_id, course_id, starts_at);
alter table public.landerware_sessions add constraint landerware_sessions_pkey PRIMARY KEY (id);
alter table public.locations add constraint locations_location_key_key UNIQUE (location_key);
alter table public.locations add constraint locations_pkey PRIMARY KEY (id);
alter table public.locations add constraint locations_public_requires_active_check CHECK (((NOT public) OR (scheduling_status = 'active'::text)));
alter table public.locations add constraint locations_scheduling_status_check CHECK ((scheduling_status = ANY (ARRAY['active'::text, 'inactive'::text, 'historical_only'::text])));
alter table public.participant_completions add constraint participant_completions_completion_status_check CHECK ((completion_status = ANY (ARRAY['attended'::text, 'passed'::text, 'failed'::text, 'incomplete'::text, 'unknown'::text])));
alter table public.participant_completions add constraint participant_completions_pkey PRIMARY KEY (id);
alter table public.participant_completions add constraint participant_completions_registration_id_course_id_key UNIQUE (registration_id, course_id);
alter table public.participant_lifecycle_events add constraint participant_lifecycle_events_event_key_key UNIQUE (event_key);
alter table public.participant_lifecycle_events add constraint participant_lifecycle_events_pkey PRIMARY KEY (id);
alter table public.people add constraint people_person_key_key UNIQUE (person_key);
alter table public.people add constraint people_pkey PRIMARY KEY (id);
alter table public.registration_orders add constraint registration_orders_pkey PRIMARY KEY (id);
alter table public.registration_orders add constraint registration_orders_registration_id_key UNIQUE (registration_id);
alter table public.registration_orders add constraint registration_orders_status_check CHECK ((status = ANY (ARRAY['payment_pending'::text, 'paid'::text, 'canceled'::text, 'refunded'::text, 'payment_failed'::text])));
alter table public.registration_orders add constraint registration_orders_stripe_checkout_session_id_key UNIQUE (stripe_checkout_session_id);
alter table public.registration_requirements add constraint registration_requirements_pkey PRIMARY KEY (id);
alter table public.registration_requirements add constraint registration_requirements_registration_id_requirement_key_key UNIQUE (registration_id, requirement_key);
alter table public.registration_requirements add constraint registration_requirements_state_check CHECK ((state = ANY (ARRAY['known'::text, 'unknown'::text, 'satisfied'::text, 'unsatisfied'::text, 'not_applicable'::text, 'waived'::text])));
alter table public.registration_supersessions add constraint registration_supersessions_check CHECK ((source_registration_id <> target_registration_id));
alter table public.registration_supersessions add constraint registration_supersessions_check1 CHECK ((source_session_id <> target_session_id));
alter table public.registration_supersessions add constraint registration_supersessions_financial_policy_check CHECK ((financial_policy = ANY (ARRAY['transfer'::text, 'retain'::text, 'none'::text])));
alter table public.registration_supersessions add constraint registration_supersessions_idempotency_key_key UNIQUE (idempotency_key);
alter table public.registration_supersessions add constraint registration_supersessions_pkey PRIMARY KEY (id);
alter table public.registrations add constraint registrations_customer_id_class_session_id_key UNIQUE (customer_id, class_session_id);
alter table public.registrations add constraint registrations_pkey PRIMARY KEY (id);
CREATE OR REPLACE FUNCTION public.assert_public_registration_open(p_start timestamp with time zone DEFAULT NULL::timestamp with time zone, p_end timestamp with time zone DEFAULT NULL::timestamp with time zone, p_external_id text DEFAULT NULL::text)
 RETURNS void
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare c jsonb; window_start timestamptz; window_end timestamptz; source_row record;
begin
 for c in select value from jsonb_array_elements(public.public_registration_closure_policy()->'closures') loop
  window_start:=(c->>'startsAt')::timestamptz; window_end:=(c->>'endsAt')::timestamptz;
  if p_start < window_end and coalesce(greatest(p_end,p_start+interval '1 microsecond'),p_start+interval '1 microsecond') > window_start then
   raise exception 'registration_date_closed' using errcode='P0001';
  end if;
  -- Check actual facts as well as supplied timestamps. Workspace-only sessions
  -- have starts_at/ends_at and need no invented registration_status column.
  if nullif(trim(p_external_id),'') is not null then
   for source_row in
    select coalesce(s.consumption_start_at,s.start_at) as a,coalesce(s.consumption_end_at,s.end_at) as b
    from public.class_sessions s where (s.external_class_id=p_external_id or s.id::text=p_external_id)
      and s.status in ('scheduled','active')
    union all
    select w.starts_at,w.ends_at from public.landerware_sessions w
      where w.external_session_id=p_external_id or w.id::text=p_external_id
   loop
    if source_row.a < window_end and coalesce(greatest(source_row.b,source_row.a+interval '1 microsecond'),source_row.a+interval '1 microsecond') > window_start then
     raise exception 'registration_date_closed' using errcode='P0001';
    end if;
   end loop;
  end if;
 end loop;
end;
$function$;

CREATE OR REPLACE FUNCTION public.move_registration(p_idempotency_key text, p_source_registration_id uuid, p_target_session_id uuid, p_reason text, p_source text, p_actor jsonb DEFAULT '{}'::jsonb, p_financial_policy text DEFAULT 'transfer'::text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO 'public', 'pg_temp'
AS $function$
declare
  v_source public.registrations%rowtype;
  v_target_id uuid;
  v_move public.registration_supersessions%rowtype;
  v_order_id uuid;
  v_has_completion boolean;
  v_target_course uuid;
  v_source_course uuid;
begin
  if nullif(trim(p_idempotency_key),'') is null or nullif(trim(p_reason),'') is null then
    raise exception 'idempotency_key and reason are required';
  end if;
  if p_financial_policy not in ('transfer','retain','none') then raise exception 'invalid financial policy'; end if;
  perform pg_advisory_xact_lock(hashtextextended('move:'||p_idempotency_key,0));

  select * into v_move from public.registration_supersessions where idempotency_key=p_idempotency_key;
  if found then
    return jsonb_build_object('ok',true,'idempotent_replay',true,'source_registration_id',v_move.source_registration_id,
      'target_registration_id',v_move.target_registration_id,'supersession_id',v_move.id,
      'transferred_order_id',v_move.transferred_order_id);
  end if;

  select * into v_source from public.registrations where id=p_source_registration_id for update;
  if not found then raise exception 'source registration not found'; end if;
  if v_source.class_session_id=p_target_session_id then raise exception 'target session must differ from source session'; end if;
  select course_id into v_source_course from public.class_sessions where id=v_source.class_session_id;
  select course_id into v_target_course from public.class_sessions where id=p_target_session_id;
  if v_target_course is null then raise exception 'target session not found'; end if;
  if v_source_course<>v_target_course then raise exception 'target session course differs from source course'; end if;

  select exists(select 1 from public.participant_completions where registration_id=v_source.id) into v_has_completion;

  insert into public.registrations(customer_id,class_session_id,status,registration_source)
  values(v_source.customer_id,p_target_session_id,
    case when v_source.status='completed' then 'registered' else v_source.status end,p_source)
  on conflict(customer_id,class_session_id) do update set updated_at=now()
  returning id into v_target_id;

  select id into v_order_id from public.registration_orders where registration_id=v_source.id for update;
  if p_financial_policy='transfer' and v_order_id is not null then
    if exists(select 1 from public.registration_orders where registration_id=v_target_id) then
      raise exception 'target registration already has an order';
    end if;
    update public.registration_orders set registration_id=v_target_id,updated_at=now() where id=v_order_id;
  elsif p_financial_policy<>'transfer' then
    v_order_id:=null;
  end if;

  insert into public.registration_requirements(
    registration_id,requirement_key,requirement_type,state,source,notes,satisfied_at,satisfied_by,
    superseded_from_requirement_id,provenance
  )
  select v_target_id,requirement_key,requirement_type,state,p_source,notes,satisfied_at,satisfied_by,id,
    provenance||jsonb_build_object('moved_from_registration_id',v_source.id)
  from public.registration_requirements where registration_id=v_source.id
  on conflict(registration_id,requirement_key) do nothing;

  if not v_has_completion then
    update public.registrations set status='rescheduled',updated_at=now() where id=v_source.id;
  end if;

  insert into public.registration_supersessions(
    idempotency_key,source_registration_id,target_registration_id,source_session_id,target_session_id,
    reason,source,actor,financial_policy,transferred_order_id,details
  ) values(
    p_idempotency_key,v_source.id,v_target_id,v_source.class_session_id,p_target_session_id,
    p_reason,p_source,p_actor,p_financial_policy,
    case when p_financial_policy='transfer' then v_order_id end,
    jsonb_build_object('source_status_preserved',v_has_completion,'source_course_id',v_source_course)
  ) returning * into v_move;

  insert into public.participant_lifecycle_events(
    event_key,event_type,customer_id,registration_id,class_session_id,related_registration_id,source,actor,details
  ) values(
    'move:'||p_idempotency_key,'moved',v_source.customer_id,v_source.id,v_source.class_session_id,v_target_id,
    p_source,p_actor,jsonb_build_object('target_session_id',p_target_session_id,'reason',p_reason,
      'financial_policy',p_financial_policy,'transferred_order_id',v_move.transferred_order_id,
      'completed_source_preserved',v_has_completion)
  );

  return jsonb_build_object('ok',true,'idempotent_replay',false,'source_registration_id',v_source.id,
    'target_registration_id',v_target_id,'supersession_id',v_move.id,
    'transferred_order_id',v_move.transferred_order_id,'completed_source_preserved',v_has_completion);
end;
$function$;

CREATE OR REPLACE FUNCTION public.public_registration_closure_policy()
 RETURNS jsonb
 LANGUAGE sql
 IMMUTABLE
 SET search_path TO ''
AS $function$
select '{"schemaVersion":"public-registration-closures.v1","closures":[{"id":"owner-oct21-20261015","startsAt":"2026-10-21T04:00:00Z","endsAt":"2026-10-22T04:00:00Z","timezone":"America/New_York","reason":"Registration is closed for October 21.","scope":"all_new_registrations","preserveExisting":true}]}'::jsonb;
$function$;
