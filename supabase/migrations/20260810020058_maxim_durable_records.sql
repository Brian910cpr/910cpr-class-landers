begin;

create table if not exists public.landerware_organizations (
  id uuid primary key default gen_random_uuid(),
  display_name text not null,
  organization_type text not null default 'corporate_account',
  billing_reference text,
  archived_at timestamptz,
  document_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create unique index if not exists landerware_organization_identity
  on public.landerware_organizations(display_name, coalesce(billing_reference, ''));

create table if not exists public.landerware_people (
  id uuid primary key default gen_random_uuid(), current_first_name text not null,
  current_last_name text not null, current_email text, current_phone text,
  prior_names jsonb not null default '[]'::jsonb,
  prior_contacts jsonb not null default '[]'::jsonb,
  searchable_text text not null default '',
  archived_at timestamptz, document_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table if not exists public.landerware_person_organizations (
  person_id uuid not null references public.landerware_people(id),
  organization_id uuid not null references public.landerware_organizations(id),
  employer_identifier text, active boolean not null default true,
  started_at timestamptz not null default now(), ended_at timestamptz,
  primary key (person_id, organization_id, started_at)
);

create table if not exists public.landerware_certification_requirements (
  id uuid primary key default gen_random_uuid(), person_id uuid not null references public.landerware_people(id),
  organization_id uuid references public.landerware_organizations(id),
  course_id text not null, course_name text not null, expiration_date date,
  source_policy text, source_policy_version text, employer_controlled boolean not null default true,
  status text not null default 'active', document_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table if not exists public.landerware_sessions (
  id uuid primary key default gen_random_uuid(), external_session_id text,
  course_id text not null, course_name text not null, starts_at timestamptz not null,
  ends_at timestamptz, location_name text, instructor_id uuid, instructor_name text,
  organization_id uuid references public.landerware_organizations(id),
  lifecycle_state text not null default 'create', provenance text not null,
  workspace_schema_version text not null default 'landerware.session-workspace.v1',
  requirements_manifest jsonb not null, document_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  unique (external_session_id, course_id, starts_at)
);

create table if not exists public.landerware_rosters (
  id uuid primary key default gen_random_uuid(), session_id uuid not null unique references public.landerware_sessions(id),
  blank_walk_in_rows integer not null default 5 check (blank_walk_in_rows >= 3),
  document_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table if not exists public.landerware_registrations (
  id uuid primary key default gen_random_uuid(), person_id uuid not null references public.landerware_people(id),
  requirement_id uuid not null references public.landerware_certification_requirements(id),
  session_id uuid not null references public.landerware_sessions(id),
  roster_id uuid not null references public.landerware_rosters(id),
  organization_id uuid references public.landerware_organizations(id),
  status text not null default 'active', source text not null,
  supersedes_registration_id uuid references public.landerware_registrations(id),
  superseded_by_registration_id uuid references public.landerware_registrations(id),
  fee_disclosure_version text, fee_disclosure_presented_at timestamptz,
  fee_disclosure_channel text, fee_disclosure_accepted_at timestamptz,
  document_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create unique index if not exists landerware_one_active_registration_requirement
  on public.landerware_registrations(person_id, requirement_id) where status = 'active';

create table if not exists public.landerware_disclosure_versions (
  version text primary key, disclosure_type text not null, canonical_text text not null,
  source_title text not null, source_url text not null, verified_at timestamptz not null,
  active boolean not null default true, created_at timestamptz not null default now()
);
insert into public.landerware_disclosure_versions(version,disclosure_type,canonical_text,source_title,source_url,verified_at)
values('aha-course-fees-2026-pam-v1','course_fee',
  'Course fees are set and charged by 910CPR / Coastal CPR Training and are not charged by the American Heart Association.',
  'AHA Program Administration Manual: International Version, 2026',
  'https://www.heart.org/-/media/04191BA05B574F49941485ADAF2AF631.ashx','2026-08-10T00:00:00-04:00')
on conflict(version) do nothing;

create table if not exists public.landerware_roster_memberships (
  id uuid primary key default gen_random_uuid(), roster_id uuid not null references public.landerware_rosters(id),
  session_id uuid not null references public.landerware_sessions(id), person_id uuid references public.landerware_people(id),
  registration_id uuid references public.landerware_registrations(id),
  display_name text not null, email text, attendance_status text not null default 'registered',
  source text not null, document_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);

create table if not exists public.landerware_activity_events (
  id uuid primary key default gen_random_uuid(), event_type text not null,
  actor_source text not null check (actor_source in ('maxim_staff','brian_admin','employee_self_service','instructor','system','enrollware_import')),
  actor_display text, person_id uuid references public.landerware_people(id),
  organization_id uuid references public.landerware_organizations(id),
  requirement_id uuid references public.landerware_certification_requirements(id),
  registration_id uuid references public.landerware_registrations(id),
  session_id uuid references public.landerware_sessions(id), details jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now()
);

create table if not exists public.landerware_messages (
  id uuid primary key default gen_random_uuid(), person_id uuid references public.landerware_people(id),
  registration_id uuid references public.landerware_registrations(id), template_key text not null,
  channel text not null default 'email', recipient text, subject text not null, body_text text not null,
  delivery_provider text not null default 'gmail', delivery_status text not null default 'pending',
  idempotency_key text not null unique, provider_message_id text, provider_thread_id text,
  sent_at timestamptz, failed_at timestamptz, failure_detail text, created_at timestamptz not null default now()
);

create table if not exists public.landerware_documents (
  id uuid primary key default gen_random_uuid(), document_type text not null, source text not null,
  document_date date, received_at timestamptz, related_record_ids jsonb not null default '{}'::jsonb,
  retention_class text not null default 'durable_indefinite', original_filename text,
  checksum_sha256 text, storage_provider text, storage_reference text, notes text,
  activity_history jsonb not null default '[]'::jsonb, created_at timestamptz not null default now()
);

create table if not exists public.landerware_credentials (
  id uuid primary key default gen_random_uuid(), person_id uuid not null references public.landerware_people(id),
  registration_id uuid references public.landerware_registrations(id), course_id text,
  ecard_code text, issued_at timestamptz, expires_on date, document_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.landerware_self_service_tokens (
  id uuid primary key default gen_random_uuid(), token_sha256 text not null unique,
  person_id uuid not null references public.landerware_people(id),
  organization_id uuid not null references public.landerware_organizations(id),
  requirement_id uuid not null references public.landerware_certification_requirements(id),
  expires_at timestamptz not null, revoked_at timestamptz, last_opened_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.maxim_employee_profiles add column if not exists landerware_person_id uuid references public.landerware_people(id);
alter table public.maxim_employee_profiles add column if not exists landerware_organization_id uuid references public.landerware_organizations(id);
alter table public.maxim_employee_profiles add column if not exists landerware_requirement_id uuid references public.landerware_certification_requirements(id);
alter table public.maxim_employee_profiles add column if not exists link_prepared_at timestamptz;
alter table public.maxim_registration_requests add column if not exists landerware_registration_id uuid references public.landerware_registrations(id);
alter table public.maxim_registration_requests add column if not exists landerware_session_id uuid references public.landerware_sessions(id);

create or replace function public.landerware_record_corporate_registration(
  p_person_id uuid, p_requirement_id uuid, p_organization_id uuid,
  p_external_session_id text, p_course_id text, p_course_name text,
  p_starts_at timestamptz, p_location_name text, p_provenance text,
  p_requirements_manifest jsonb, p_display_name text, p_email text,
  p_actor_source text, p_fee_disclosure_version text, p_fee_disclosure_channel text
) returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare v_session public.landerware_sessions; v_roster public.landerware_rosters;
  v_prior public.landerware_registrations; v_registration public.landerware_registrations;
begin
  perform pg_advisory_xact_lock(hashtextextended(p_person_id::text || '|' || p_requirement_id::text, 0));
  insert into public.landerware_sessions(external_session_id, course_id, course_name, starts_at,
    location_name, organization_id, provenance, requirements_manifest)
  values(p_external_session_id, p_course_id, p_course_name, p_starts_at,
    p_location_name, p_organization_id, p_provenance, p_requirements_manifest)
  on conflict(external_session_id, course_id, starts_at) do update set updated_at = now()
  returning * into v_session;
  insert into public.landerware_rosters(session_id) values(v_session.id)
  on conflict(session_id) do update set updated_at = now() returning * into v_roster;
  select * into v_prior from public.landerware_registrations
    where person_id=p_person_id and requirement_id=p_requirement_id and status='active'
    order by created_at desc limit 1 for update;
  if v_prior.id is not null then update public.landerware_registrations set status='replacing',updated_at=now() where id=v_prior.id; end if;
  insert into public.landerware_registrations(person_id,requirement_id,session_id,roster_id,
    organization_id,status,source,supersedes_registration_id,fee_disclosure_version,
    fee_disclosure_presented_at,fee_disclosure_channel,fee_disclosure_accepted_at)
  values(p_person_id,p_requirement_id,v_session.id,v_roster.id,p_organization_id,'active',p_actor_source,
    v_prior.id,p_fee_disclosure_version,now(),p_fee_disclosure_channel,now()) returning * into v_registration;
  insert into public.landerware_roster_memberships(roster_id,session_id,person_id,registration_id,
    display_name,email,source) values(v_roster.id,v_session.id,p_person_id,v_registration.id,p_display_name,p_email,p_actor_source);
  if v_prior.id is not null then
    update public.landerware_registrations set status='superseded',superseded_by_registration_id=v_registration.id,updated_at=now() where id=v_prior.id;
  end if;
  insert into public.landerware_activity_events(event_type,actor_source,actor_display,person_id,
    organization_id,requirement_id,registration_id,session_id,details)
  values(case when v_prior.id is null then 'scheduled' else 'rescheduled' end,p_actor_source,
    case when p_actor_source='employee_self_service' then 'Action performed through employee scheduling link' else p_actor_source end,
    p_person_id,p_organization_id,p_requirement_id,v_registration.id,v_session.id,
    jsonb_build_object('supersedesRegistrationId',v_prior.id));
  return jsonb_build_object('registrationId',v_registration.id,'sessionId',v_session.id,
    'rosterId',v_roster.id,'supersedesRegistrationId',v_prior.id);
end $$;

revoke all on function public.landerware_record_corporate_registration(uuid,uuid,uuid,text,text,text,timestamptz,text,text,jsonb,text,text,text,text,text) from public,anon,authenticated;
grant execute on function public.landerware_record_corporate_registration(uuid,uuid,uuid,text,text,text,timestamptz,text,text,jsonb,text,text,text,text,text) to service_role;

create index if not exists landerware_people_search on public.landerware_people using gin (to_tsvector('simple', searchable_text));
create index if not exists landerware_sessions_search on public.landerware_sessions(course_name, starts_at);
create index if not exists landerware_activity_person_time on public.landerware_activity_events(person_id, occurred_at desc);
create index if not exists landerware_documents_related on public.landerware_documents using gin (related_record_ids);

do $$ declare table_name text; begin
  foreach table_name in array array[
    'landerware_organizations','landerware_people','landerware_person_organizations',
    'landerware_certification_requirements','landerware_sessions','landerware_rosters',
    'landerware_registrations','landerware_roster_memberships','landerware_activity_events',
    'landerware_messages','landerware_documents','landerware_credentials','landerware_self_service_tokens','landerware_disclosure_versions'
  ] loop execute format('alter table public.%I enable row level security', table_name); end loop;
end $$;

revoke all on public.landerware_organizations, public.landerware_people,
  public.landerware_person_organizations, public.landerware_certification_requirements,
  public.landerware_sessions, public.landerware_rosters, public.landerware_registrations,
  public.landerware_roster_memberships, public.landerware_activity_events,
  public.landerware_messages, public.landerware_documents, public.landerware_credentials,
  public.landerware_self_service_tokens, public.landerware_disclosure_versions from anon, authenticated;

commit;
