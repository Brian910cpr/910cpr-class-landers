begin;

alter table public.landerware_registrations
  add column if not exists handoff_intent_id uuid,
  add column if not exists external_system text,
  add column if not exists external_registration_id text,
  add column if not exists external_checkout_url text,
  add column if not exists external_checkout_state text,
  add column if not exists external_checkout_started_at timestamptz,
  add column if not exists external_reconciled_at timestamptz,
  add column if not exists external_reconciliation_evidence jsonb not null default '{}'::jsonb;

create unique index if not exists landerware_registration_handoff_intent
  on public.landerware_registrations(handoff_intent_id)
  where handoff_intent_id is not null;

create unique index if not exists landerware_registration_external_identity
  on public.landerware_registrations(external_system, external_registration_id)
  where external_system is not null and external_registration_id is not null;

create unique index if not exists landerware_front_door_one_intent_per_person_session
  on public.landerware_registrations(person_id, session_id)
  where source = 'landerware_front_door'
    and status in ('awaiting_external_checkout', 'confirmed');

create or replace function public.landerware_start_external_registration(
  p_first_name text,
  p_last_name text,
  p_email text,
  p_phone text,
  p_external_session_id text,
  p_course_id text,
  p_course_name text,
  p_starts_at timestamptz,
  p_ends_at timestamptz,
  p_location_name text,
  p_external_checkout_url text,
  p_idempotency_key text
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_person_result jsonb;
  v_person_id uuid;
  v_session public.landerware_sessions;
  v_roster public.landerware_rosters;
  v_registration public.landerware_registrations;
begin
  if nullif(trim(p_first_name), '') is null or nullif(trim(p_last_name), '') is null
     or nullif(trim(p_email), '') is null or nullif(trim(p_phone), '') is null then
    raise exception 'required_identity_field_missing';
  end if;
  if nullif(trim(p_external_session_id), '') is null or p_starts_at is null then
    raise exception 'session_required';
  end if;
  if p_external_checkout_url !~ '^https://coastalcprtraining[.]enrollware[.]com/enroll[?]id=[0-9]+$' then
    raise exception 'invalid_external_checkout_url';
  end if;
  if nullif(trim(p_idempotency_key), '') is null then
    raise exception 'idempotency_key_required';
  end if;

  select * into v_registration
  from public.landerware_registrations
  where idempotency_key = 'front-door:' || p_idempotency_key
  limit 1;
  if v_registration.id is not null then
    return jsonb_build_object(
      'personId', v_registration.person_id,
      'registrationId', v_registration.id,
      'sessionId', v_registration.session_id,
      'intentId', v_registration.handoff_intent_id,
      'checkoutUrl', v_registration.external_checkout_url,
      'status', v_registration.status,
      'idempotentReplay', true
    );
  end if;

  v_person_result := public.landerware_create_or_find_person(
    p_first_name, p_last_name, lower(trim(p_email)), p_phone,
    null, null, null
  );
  v_person_id := (v_person_result->>'personId')::uuid;
  perform pg_advisory_xact_lock(hashtextextended(
    'front-door|' || v_person_id::text || '|' || p_external_session_id, 0
  ));

  insert into public.landerware_sessions(
    external_session_id, course_id, course_name, starts_at, ends_at,
    location_name, lifecycle_state, provenance, requirements_manifest
  ) values (
    p_external_session_id, p_course_id, p_course_name, p_starts_at, p_ends_at,
    p_location_name, 'published', 'enrollware_public_schedule', '{}'::jsonb
  )
  on conflict (external_session_id, course_id, starts_at) do update
    set course_name = excluded.course_name,
        ends_at = excluded.ends_at,
        location_name = excluded.location_name,
        updated_at = now()
  returning * into v_session;

  insert into public.landerware_rosters(session_id)
  values (v_session.id)
  on conflict (session_id) do update set updated_at = now()
  returning * into v_roster;

  select * into v_registration
  from public.landerware_registrations
  where person_id = v_person_id and session_id = v_session.id
    and source = 'landerware_front_door'
    and status in ('awaiting_external_checkout', 'confirmed')
  order by created_at desc limit 1 for update;

  if v_registration.id is null then
    insert into public.landerware_registrations(
      person_id, session_id, roster_id, status, source, idempotency_key,
      course_id, entry_context, session_selection_status, payer_mode,
      payment_state, billing_state, handoff_intent_id, external_system,
      external_checkout_url, external_checkout_state, external_checkout_started_at
    ) values (
      v_person_id, v_session.id, v_roster.id, 'awaiting_external_checkout',
      'landerware_front_door', 'front-door:' || p_idempotency_key,
      p_course_id, 'public_anonymous', 'selected', 'customer_pays',
      'pending', 'not_required', gen_random_uuid(), 'enrollware',
      p_external_checkout_url, 'awaiting_completion', now()
    ) returning * into v_registration;

    insert into public.landerware_activity_events(
      event_type, actor_source, person_id, registration_id, session_id, details
    ) values (
      'external_checkout_started', 'system', v_person_id, v_registration.id,
      v_session.id, jsonb_build_object(
        'registration_source', 'landerware_front_door',
        'external_system', 'enrollware',
        'external_session_id', p_external_session_id,
        'handoff_intent_id', v_registration.handoff_intent_id
      )
    );
  end if;

  return jsonb_build_object(
    'personId', v_person_id,
    'customerCreated', (v_person_result->>'created')::boolean,
    'registrationId', v_registration.id,
    'sessionId', v_session.id,
    'intentId', v_registration.handoff_intent_id,
    'checkoutUrl', v_registration.external_checkout_url,
    'status', v_registration.status,
    'idempotentReplay', false
  );
end $$;

create or replace function public.landerware_reconcile_external_registration(
  p_external_system text,
  p_external_registration_id text,
  p_external_session_id text,
  p_first_name text,
  p_last_name text,
  p_email text,
  p_phone text default null,
  p_registered_at timestamptz default now(),
  p_source_record jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_registration public.landerware_registrations;
  v_match_count integer;
  v_normalized_phone text := regexp_replace(coalesce(p_phone, ''), '[^0-9]', '', 'g');
begin
  if nullif(trim(p_external_registration_id), '') is null
     or nullif(trim(p_external_session_id), '') is null then
    raise exception 'external_registration_identity_required';
  end if;
  select * into v_registration
  from public.landerware_registrations
  where external_system = p_external_system
    and external_registration_id = p_external_registration_id
  limit 1;
  if v_registration.id is not null then
    return jsonb_build_object('matched', true, 'registrationId', v_registration.id,
      'personId', v_registration.person_id, 'sessionId', v_registration.session_id,
      'intentId', v_registration.handoff_intent_id, 'status', v_registration.status,
      'idempotentReplay', true);
  end if;

  select count(*) into v_match_count
  from public.landerware_registrations r
  join public.landerware_sessions s on s.id = r.session_id
  join public.landerware_people p on p.id = r.person_id
  where r.source = 'landerware_front_door'
    and r.status = 'awaiting_external_checkout'
    and s.external_session_id = p_external_session_id
    and lower(trim(coalesce(p.current_email, ''))) = lower(trim(coalesce(p_email, '')))
    and lower(trim(p.current_first_name)) = lower(trim(p_first_name))
    and lower(trim(p.current_last_name)) = lower(trim(p_last_name))
    and (v_normalized_phone = '' or regexp_replace(coalesce(p.current_phone, ''), '[^0-9]', '', 'g') = v_normalized_phone)
    and r.external_checkout_started_at between p_registered_at - interval '7 days' and p_registered_at + interval '1 day';

  if v_match_count = 0 then raise exception 'registration_intent_not_found'; end if;
  if v_match_count > 1 then raise exception 'registration_intent_ambiguous'; end if;

  select r.* into v_registration
  from public.landerware_registrations r
  join public.landerware_sessions s on s.id = r.session_id
  join public.landerware_people p on p.id = r.person_id
  where r.source = 'landerware_front_door'
    and r.status = 'awaiting_external_checkout'
    and s.external_session_id = p_external_session_id
    and lower(trim(coalesce(p.current_email, ''))) = lower(trim(coalesce(p_email, '')))
    and lower(trim(p.current_first_name)) = lower(trim(p_first_name))
    and lower(trim(p.current_last_name)) = lower(trim(p_last_name))
    and (v_normalized_phone = '' or regexp_replace(coalesce(p.current_phone, ''), '[^0-9]', '', 'g') = v_normalized_phone)
    and r.external_checkout_started_at between p_registered_at - interval '7 days' and p_registered_at + interval '1 day'
  for update of r;

  update public.landerware_registrations
  set status = 'confirmed',
      external_system = p_external_system,
      external_registration_id = p_external_registration_id,
      external_checkout_state = 'completed',
      external_reconciled_at = now(),
      external_reconciliation_evidence = jsonb_build_object(
        'external_session_id', p_external_session_id,
        'email_match', true,
        'name_match', true,
        'phone_checked', v_normalized_phone <> '',
        'registered_at', p_registered_at,
        'source_record', p_source_record
      ),
      updated_at = now()
  where id = v_registration.id
  returning * into v_registration;

  insert into public.landerware_activity_events(
    event_type, actor_source, person_id, registration_id, session_id, details
  ) values (
    'external_registration_reconciled', 'enrollware_import', v_registration.person_id,
    v_registration.id, v_registration.session_id,
    jsonb_build_object('externalRegistrationId', p_external_registration_id,
      'handoffIntentId', v_registration.handoff_intent_id,
      'sourceRecord', p_source_record)
  );

  return jsonb_build_object('matched', true, 'registrationId', v_registration.id,
    'personId', v_registration.person_id, 'sessionId', v_registration.session_id,
    'intentId', v_registration.handoff_intent_id, 'status', v_registration.status);
end $$;

revoke execute on function public.landerware_start_external_registration(text,text,text,text,text,text,text,timestamptz,timestamptz,text,text,text) from public, anon, authenticated;
grant execute on function public.landerware_start_external_registration(text,text,text,text,text,text,text,timestamptz,timestamptz,text,text,text) to service_role;
revoke execute on function public.landerware_reconcile_external_registration(text,text,text,text,text,text,text,timestamptz,jsonb) from public, anon, authenticated;
grant execute on function public.landerware_reconcile_external_registration(text,text,text,text,text,text,text,timestamptz,jsonb) to service_role;

commit;
