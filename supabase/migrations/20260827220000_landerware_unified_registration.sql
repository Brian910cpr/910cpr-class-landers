begin;

create table if not exists public.landerware_courses (
  id text primary key,
  display_name text not null,
  provider text not null,
  delivery_mode text not null,
  public_slug text unique,
  listed boolean not null default false,
  enrollware_course_id text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.landerware_courses
  (id, display_name, provider, delivery_mode, public_slug, listed, enrollware_course_id)
values
  ('aha-heartsaver-skills-session', 'AHA Heartsaver Skills Session',
   'American Heart Association', 'skills_session', 'heartsaver-skills', false, null)
on conflict (id) do update set
  display_name = excluded.display_name,
  public_slug = excluded.public_slug,
  listed = excluded.listed,
  enrollware_course_id = excluded.enrollware_course_id,
  updated_at = now();

alter table public.landerware_certification_requirements
  add column if not exists requirement_type text,
  add column if not exists satisfied_at timestamptz;

alter table public.landerware_registrations
  alter column requirement_id drop not null,
  alter column session_id drop not null,
  alter column roster_id drop not null,
  add column if not exists idempotency_key text,
  add column if not exists course_id text,
  add column if not exists session_selection_status text not null default 'selected';

create unique index if not exists landerware_registration_idempotency
  on public.landerware_registrations(idempotency_key)
  where idempotency_key is not null;

create table if not exists public.landerware_document_submission_tokens (
  id uuid primary key default gen_random_uuid(),
  token_sha256 text not null unique,
  person_id uuid not null references public.landerware_people(id),
  registration_id uuid not null references public.landerware_registrations(id),
  requirement_id uuid not null references public.landerware_certification_requirements(id),
  expires_at timestamptz not null,
  revoked_at timestamptz,
  last_opened_at timestamptz,
  submission_count integer not null default 0,
  created_at timestamptz not null default now()
);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('landerware-requirement-documents', 'landerware-requirement-documents', false,
  10485760, array['application/pdf','image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = false, file_size_limit = 10485760,
  allowed_mime_types = excluded.allowed_mime_types;

create or replace function public.landerware_create_or_find_person(
  p_first_name text, p_last_name text, p_email text, p_phone text default null,
  p_existing_person_id uuid default null
) returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare
  v_person public.landerware_people;
  v_email text := lower(trim(coalesce(p_email, '')));
  v_phone text := regexp_replace(coalesce(p_phone, ''), '[^0-9]', '', 'g');
  v_created boolean := false;
begin
  if trim(coalesce(p_first_name,'')) = '' or trim(coalesce(p_last_name,'')) = '' or v_email = '' then
    raise exception 'first name, last name, and email are required';
  end if;
  perform pg_advisory_xact_lock(hashtextextended('landerware-person|' || v_email, 0));
  if p_existing_person_id is not null then
    select * into v_person from public.landerware_people where id=p_existing_person_id for update;
  else
    select * into v_person from public.landerware_people
      where archived_at is null and lower(trim(coalesce(current_email,'')))=v_email
      order by created_at asc limit 1 for update;
    if v_person.id is null and v_phone <> '' then
      select * into v_person from public.landerware_people
        where archived_at is null
          and regexp_replace(coalesce(current_phone,''), '[^0-9]', '', 'g')=v_phone
          and lower(trim(current_first_name))=lower(trim(p_first_name))
          and lower(trim(current_last_name))=lower(trim(p_last_name))
        order by created_at asc limit 1 for update;
    end if;
  end if;
  if v_person.id is null then
    insert into public.landerware_people
      (current_first_name,current_last_name,current_email,current_phone,searchable_text)
    values(trim(p_first_name),trim(p_last_name),v_email,nullif(trim(coalesce(p_phone,'')),''),
      lower(trim(p_first_name)||' '||trim(p_last_name)||' '||v_email||' '||coalesce(p_phone,'')))
    returning * into v_person;
    v_created := true;
  else
    update public.landerware_people set current_first_name=trim(p_first_name),
      current_last_name=trim(p_last_name),current_email=v_email,
      current_phone=coalesce(nullif(trim(coalesce(p_phone,'')),''),current_phone),
      searchable_text=lower(trim(p_first_name)||' '||trim(p_last_name)||' '||v_email||' '||coalesce(p_phone,'')),
      updated_at=now() where id=v_person.id returning * into v_person;
  end if;
  return jsonb_build_object('personId',v_person.id,'created',v_created);
end $$;

create or replace function public.landerware_register(
  p_first_name text,
  p_last_name text,
  p_email text,
  p_phone text,
  p_course_id text,
  p_course_name text,
  p_source text,
  p_idempotency_key text,
  p_requirement_type text default null,
  p_organization_id uuid default null,
  p_existing_person_id uuid default null,
  p_existing_requirement_id uuid default null,
  p_external_session_id text default null,
  p_starts_at timestamptz default null,
  p_location_name text default null,
  p_provenance text default null,
  p_requirements_manifest jsonb default '{}'::jsonb,
  p_fee_disclosure_version text default null,
  p_fee_disclosure_channel text default null
) returns jsonb language plpgsql security definer set search_path = public, pg_temp as $$
declare
  v_person public.landerware_people;
  v_person_result jsonb;
  v_requirement public.landerware_certification_requirements;
  v_session public.landerware_sessions;
  v_roster public.landerware_rosters;
  v_registration public.landerware_registrations;
  v_email text := lower(trim(coalesce(p_email, '')));
begin
  if trim(coalesce(p_first_name,'')) = '' or trim(coalesce(p_last_name,'')) = '' or v_email = '' then
    raise exception 'first name, last name, and email are required';
  end if;
  if p_idempotency_key is not null then
    select * into v_registration from public.landerware_registrations
      where idempotency_key = p_idempotency_key limit 1;
    if v_registration.id is not null then
      return jsonb_build_object('personId',v_registration.person_id,
        'registrationId',v_registration.id,'requirementId',v_registration.requirement_id,
        'sessionId',v_registration.session_id,'created',false,'idempotentReplay',true);
    end if;
  end if;

  v_person_result := public.landerware_create_or_find_person(
    p_first_name,p_last_name,p_email,p_phone,p_existing_person_id);
  select * into v_person from public.landerware_people
    where id=(v_person_result->>'personId')::uuid;

  if p_existing_requirement_id is not null then
    select * into v_requirement from public.landerware_certification_requirements
      where id=p_existing_requirement_id and person_id=v_person.id for update;
  else
    insert into public.landerware_certification_requirements
      (person_id,organization_id,course_id,course_name,requirement_type,employer_controlled,status)
    values (v_person.id,p_organization_id,p_course_id,p_course_name,p_requirement_type,
      p_organization_id is not null,'active') returning * into v_requirement;
  end if;

  if p_external_session_id is not null and p_starts_at is not null then
    insert into public.landerware_sessions(external_session_id,course_id,course_name,starts_at,
      location_name,organization_id,provenance,requirements_manifest)
    values(p_external_session_id,p_course_id,p_course_name,p_starts_at,p_location_name,
      p_organization_id,coalesce(p_provenance,p_source),p_requirements_manifest)
    on conflict(external_session_id,course_id,starts_at) do update set updated_at=now()
    returning * into v_session;
    insert into public.landerware_rosters(session_id) values(v_session.id)
      on conflict(session_id) do update set updated_at=now() returning * into v_roster;
  end if;

  insert into public.landerware_registrations
    (person_id,requirement_id,session_id,roster_id,organization_id,status,source,
     idempotency_key,course_id,session_selection_status,fee_disclosure_version,
     fee_disclosure_presented_at,fee_disclosure_channel,fee_disclosure_accepted_at)
  values(v_person.id,v_requirement.id,v_session.id,v_roster.id,p_organization_id,'active',p_source,
    p_idempotency_key,p_course_id,case when v_session.id is null then 'pending' else 'selected' end,
    p_fee_disclosure_version,case when p_fee_disclosure_version is null then null else now() end,
    p_fee_disclosure_channel,case when p_fee_disclosure_version is null then null else now() end)
  returning * into v_registration;

  if v_roster.id is not null then
    insert into public.landerware_roster_memberships
      (roster_id,session_id,person_id,registration_id,display_name,email,source)
    values(v_roster.id,v_session.id,v_person.id,v_registration.id,
      trim(p_first_name)||' '||trim(p_last_name),v_email,p_source);
  end if;

  insert into public.landerware_activity_events
    (event_type,actor_source,person_id,organization_id,requirement_id,registration_id,session_id,details)
  values('registration_created',case when p_source in ('maxim_staff','employee_self_service','brian_admin','instructor','system','enrollware_import') then p_source else 'system' end,
    v_person.id,p_organization_id,v_requirement.id,v_registration.id,v_session.id,
    jsonb_build_object('source',p_source,'courseId',p_course_id,'sessionSelectionStatus',case when v_session.id is null then 'pending' else 'selected' end));

  return jsonb_build_object('personId',v_person.id,'registrationId',v_registration.id,
    'requirementId',v_requirement.id,'sessionId',v_session.id,'created',true,'idempotentReplay',false);
end $$;

revoke all on function public.landerware_register(text,text,text,text,text,text,text,text,text,uuid,uuid,uuid,text,timestamptz,text,text,jsonb,text,text) from public,anon,authenticated;
grant execute on function public.landerware_register(text,text,text,text,text,text,text,text,text,uuid,uuid,uuid,text,timestamptz,text,text,jsonb,text,text) to service_role;
revoke all on function public.landerware_create_or_find_person(text,text,text,text,uuid) from public,anon,authenticated;
grant execute on function public.landerware_create_or_find_person(text,text,text,text,uuid) to service_role;

alter table public.landerware_courses enable row level security;
alter table public.landerware_document_submission_tokens enable row level security;
revoke all on public.landerware_courses, public.landerware_document_submission_tokens from anon, authenticated;

commit;
