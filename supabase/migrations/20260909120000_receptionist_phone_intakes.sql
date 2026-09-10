begin;

create table if not exists public.landerware_phone_call_events (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  external_call_id text not null,
  external_call_id_kind text not null default 'provider',
  test_call boolean not null default false,
  source_received_at timestamptz not null,
  started_at timestamptz,
  ended_at timestamptz,
  duration_seconds integer check (duration_seconds is null or duration_seconds >= 0),
  caller_name text,
  caller_phone text not null,
  caller_email text,
  caller_organization text,
  person_id uuid references public.landerware_people(id),
  organization_id uuid references public.landerware_organizations(id),
  summary text not null default '',
  transcript text not null default '',
  recording_url text,
  recording_document_id uuid references public.landerware_documents(id),
  outcome text not null default 'unknown',
  transfer_status text not null default 'unknown',
  booking_status text not null default 'unknown',
  raw_payload jsonb not null,
  request_sha256 text not null,
  received_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (source, external_call_id)
);

create table if not exists public.landerware_service_requests (
  id uuid primary key default gen_random_uuid(),
  request_type text not null default 'phone_intake',
  title text not null default 'NEW PHONE INTAKE',
  status text not null default 'action_required' check (status in ('action_required','in_review','waiting','resolved','cancelled')),
  source_call_event_id uuid not null unique references public.landerware_phone_call_events(id),
  person_id uuid references public.landerware_people(id),
  organization_id uuid references public.landerware_organizations(id),
  credential_text text,
  course text,
  certifying_body text,
  initial_or_renewal text not null default 'unknown' check (initial_or_renewal in ('initial','renewal','unknown')),
  required_by_text text,
  service_type text not null default 'unknown',
  group_size integer check (group_size is null or group_size > 0),
  preferred_location text,
  preferred_windows jsonb not null default '[]'::jsonb,
  alternate_windows jsonb not null default '[]'::jsonb,
  flexibility text,
  unresolved_questions jsonb not null default '[]'::jsonb,
  escalation_flags jsonb not null default '{}'::jsonb,
  human_review_required boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists landerware_phone_call_events_person_time
  on public.landerware_phone_call_events(person_id, source_received_at desc);
create index if not exists landerware_service_requests_status_time
  on public.landerware_service_requests(status, created_at desc);

create table if not exists public.landerware_intake_nonces (
  key_id text not null,
  nonce text not null,
  received_at timestamptz not null default now(),
  primary key (key_id, nonce)
);

create or replace function public.landerware_ingest_phone_intake(p_payload jsonb, p_request_hash text, p_key_id text, p_nonce text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_call public.landerware_phone_call_events;
  v_request public.landerware_service_requests;
  v_person public.landerware_people;
  v_organization public.landerware_organizations;
  v_recording_document public.landerware_documents;
  v_phone text := regexp_replace(coalesce(p_payload#>>'{caller,phone}', ''), '[^0-9]', '', 'g');
  v_existing boolean := false;
begin
  if p_payload->>'source' <> 'marblism_rachel'
     or nullif(trim(p_payload->>'external_call_id'), '') is null
     or length(v_phone) < 10
     or nullif(trim(p_request_hash), '') is null then
    raise exception 'invalid_phone_intake';
  end if;

  begin
    insert into public.landerware_intake_nonces(key_id,nonce) values(p_key_id,p_nonce);
  exception when unique_violation then
    raise exception 'intake_nonce_replay';
  end;

  perform pg_advisory_xact_lock(hashtextextended('phone-intake|' || (p_payload->>'source') || '|' || (p_payload->>'external_call_id'), 0));
  select * into v_call from public.landerware_phone_call_events
    where source=p_payload->>'source' and external_call_id=p_payload->>'external_call_id' for update;
  if v_call.id is not null then
    select * into v_request from public.landerware_service_requests where source_call_event_id=v_call.id;
    return jsonb_build_object('callEventId',v_call.id,'serviceRequestId',v_request.id,'testCall',v_call.test_call,
      'idempotentReplay',true,'operationalWorkCreated',v_request.id is not null);
  end if;

  select * into v_person from public.landerware_people
    where archived_at is null and regexp_replace(coalesce(current_phone,''), '[^0-9]', '', 'g')=v_phone
    order by updated_at desc limit 1;
  if v_person.id is null then
    select p.* into v_person from public.landerware_person_identities i
      join public.landerware_people p on p.id=i.person_id
      where i.identity_source='phone' and regexp_replace(i.identity_key, '[^0-9]', '', 'g')=v_phone
      order by p.updated_at desc limit 1;
  end if;
  if nullif(trim(p_payload#>>'{caller,organization}'), '') is not null then
    select * into v_organization from public.landerware_organizations
      where archived_at is null and lower(trim(display_name))=lower(trim(p_payload#>>'{caller,organization}'))
      order by updated_at desc limit 1;
  end if;

  insert into public.landerware_phone_call_events(
    source,external_call_id,external_call_id_kind,test_call,source_received_at,started_at,ended_at,duration_seconds,
    caller_name,caller_phone,caller_email,caller_organization,person_id,organization_id,summary,transcript,recording_url,
    outcome,transfer_status,booking_status,raw_payload,request_sha256
  ) values (
    p_payload->>'source',p_payload->>'external_call_id',coalesce(p_payload->>'external_call_id_kind','provider'),
    coalesce((p_payload->>'test_call')::boolean,false),(p_payload->>'received_at')::timestamptz,
    nullif(p_payload#>>'{call,started_at}','')::timestamptz,nullif(p_payload#>>'{call,ended_at}','')::timestamptz,
    nullif(p_payload#>>'{call,duration_seconds}','')::integer,p_payload#>>'{caller,name}',p_payload#>>'{caller,phone}',
    p_payload#>>'{caller,email}',p_payload#>>'{caller,organization}',v_person.id,v_organization.id,
    coalesce(p_payload#>>'{call,summary}',''),coalesce(p_payload#>>'{call,transcript}',''),p_payload#>>'{call,recording_url}',
    coalesce(p_payload#>>'{call,outcome}','unknown'),coalesce(p_payload#>>'{call,transfer_status}','unknown'),
    coalesce(p_payload#>>'{call,booking_status}','unknown'),p_payload,p_request_hash
  ) returning * into v_call;

  if nullif(trim(v_call.recording_url), '') is not null then
    insert into public.landerware_documents(document_type,source,received_at,related_record_ids,retention_class,storage_provider,storage_reference,notes)
    values('call_recording_reference','marblism_rachel',v_call.source_received_at,jsonb_build_object('callEventId',v_call.id),
      'call_recording_reference','marblism',v_call.recording_url,'External recording reference; access and retention are controlled by Marblism.')
    returning * into v_recording_document;
    update public.landerware_phone_call_events set recording_document_id=v_recording_document.id where id=v_call.id;
  end if;

  if v_call.test_call then
    return jsonb_build_object('callEventId',v_call.id,'serviceRequestId',null,'testCall',true,'idempotentReplay',false,'operationalWorkCreated',false);
  end if;

  insert into public.landerware_service_requests(
    source_call_event_id,person_id,organization_id,credential_text,course,certifying_body,initial_or_renewal,
    required_by_text,service_type,group_size,preferred_location,preferred_windows,alternate_windows,flexibility,
    unresolved_questions,escalation_flags
  ) values (
    v_call.id,v_person.id,v_organization.id,p_payload#>>'{request,credential_text}',p_payload#>>'{request,course}',
    p_payload#>>'{request,certifying_body}',coalesce(p_payload#>>'{request,initial_or_renewal}','unknown'),
    p_payload#>>'{request,required_by}',coalesce(p_payload#>>'{request,service_type}','unknown'),
    nullif(p_payload#>>'{request,group_size}','')::integer,p_payload#>>'{request,preferred_location}',
    coalesce(p_payload#>'{request,preferred_windows}','[]'::jsonb),coalesce(p_payload#>'{request,alternate_windows}','[]'::jsonb),
    p_payload#>>'{request,flexibility}',coalesce(p_payload#>'{request,unresolved_questions}','[]'::jsonb),
    coalesce(p_payload->'flags','{}'::jsonb)
  ) returning * into v_request;

  insert into public.landerware_activity_events(event_type,actor_source,actor_display,person_id,organization_id,details)
  values('new_phone_intake_received','system','Marblism Rachel intake',v_person.id,v_organization.id,
    jsonb_build_object('callEventId',v_call.id,'serviceRequestId',v_request.id,'title','NEW PHONE INTAKE','requestHash',p_request_hash));

  return jsonb_build_object('callEventId',v_call.id,'serviceRequestId',v_request.id,'testCall',false,'idempotentReplay',false,'operationalWorkCreated',true);
end $$;

alter table public.landerware_phone_call_events enable row level security;
alter table public.landerware_service_requests enable row level security;
alter table public.landerware_intake_nonces enable row level security;
revoke all on public.landerware_phone_call_events, public.landerware_service_requests, public.landerware_intake_nonces from anon, authenticated;
grant select, insert, update on public.landerware_phone_call_events, public.landerware_service_requests to service_role;
grant select, insert, delete on public.landerware_intake_nonces to service_role;
revoke execute on function public.landerware_ingest_phone_intake(jsonb,text,text,text) from public, anon, authenticated;
grant execute on function public.landerware_ingest_phone_intake(jsonb,text,text,text) to service_role;

commit;
