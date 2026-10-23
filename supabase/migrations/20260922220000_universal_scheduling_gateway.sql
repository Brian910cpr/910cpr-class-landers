begin;

create table if not exists public.landerware_scheduling_tokens (
  id uuid primary key default gen_random_uuid(),
  token_sha256 text not null unique check (token_sha256 ~ '^[a-f0-9]{64}$'),
  purpose text not null check (purpose in (
    'initial_scheduling', 'direct_registration', 'reschedule', 'no_show_recovery',
    'renewal_22_month', 'renewal_23_month', 'instructor_invitation'
  )),
  person_id uuid references public.landerware_people(id),
  organization_id uuid references public.landerware_organizations(id),
  registration_id uuid references public.landerware_registrations(id),
  registration_profile_key text references public.landerware_registration_profiles(profile_key),
  course_id text not null,
  course_display_name text not null,
  compatible_course_ids text[] not null,
  allowed_delivery_modes text[] not null default '{}'::text[],
  allowed_actions text[] not null default array['select_session']::text[],
  payment_policy text not null check (payment_policy in (
    'inherit', 'prepaid', 'organization_billed', 'no_charge', 'self_pay'
  )),
  organization_display_name text,
  public_explanation text,
  entry_context text not null default 'secure_known_person',
  expires_at timestamptz not null,
  revoked_at timestamptz,
  completed_at timestamptz,
  max_completed_actions integer not null default 1 check (max_completed_actions between 1 and 20),
  completed_action_count integer not null default 0 check (completed_action_count >= 0),
  last_opened_at timestamptz,
  created_by text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (cardinality(compatible_course_ids) > 0),
  check (course_id = any(compatible_course_ids)),
  check (person_id is not null or payment_policy = 'self_pay')
);

create index if not exists landerware_scheduling_tokens_person_created_idx
  on public.landerware_scheduling_tokens(person_id, created_at desc)
  where person_id is not null;

create index if not exists landerware_scheduling_tokens_registration_idx
  on public.landerware_scheduling_tokens(registration_id)
  where registration_id is not null;

create index if not exists landerware_scheduling_tokens_active_expiry_idx
  on public.landerware_scheduling_tokens(expires_at)
  where revoked_at is null and completed_at is null;

create table if not exists public.landerware_scheduling_actions (
  id uuid primary key default gen_random_uuid(),
  token_id uuid not null references public.landerware_scheduling_tokens(id),
  person_id uuid references public.landerware_people(id),
  organization_id uuid references public.landerware_organizations(id),
  prior_registration_id uuid references public.landerware_registrations(id),
  resulting_registration_id uuid references public.landerware_registrations(id),
  prior_session_id uuid references public.landerware_sessions(id),
  selected_session_id uuid references public.landerware_sessions(id),
  action_type text not null,
  status text not null check (status in ('applied', 'checkout_required', 'idempotent_replay')),
  external_session_id text not null,
  idempotency_key text not null unique,
  session_snapshot jsonb not null,
  payment_snapshot jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists landerware_scheduling_actions_token_created_idx
  on public.landerware_scheduling_actions(token_id, created_at desc);

create or replace function public.landerware_apply_scheduling_selection(
  p_token_id uuid,
  p_idempotency_key text,
  p_external_session_id text,
  p_course_id text,
  p_course_name text,
  p_starts_at timestamptz,
  p_ends_at timestamptz,
  p_location_name text,
  p_delivery_mode text
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_token public.landerware_scheduling_tokens;
  v_action public.landerware_scheduling_actions;
  v_person public.landerware_people;
  v_session public.landerware_sessions;
  v_roster public.landerware_rosters;
  v_prior public.landerware_registrations;
  v_result public.landerware_registrations;
  v_registered jsonb;
  v_payment jsonb;
begin
  if nullif(trim(p_idempotency_key), '') is null
     or nullif(trim(p_external_session_id), '') is null
     or nullif(trim(p_course_id), '') is null
     or p_starts_at is null then
    raise exception 'invalid_scheduling_selection';
  end if;

  select * into v_action
  from public.landerware_scheduling_actions
  where idempotency_key = trim(p_idempotency_key)
  limit 1;

  if v_action.id is not null then
    return jsonb_build_object(
      'actionId', v_action.id,
      'status', v_action.status,
      'registrationId', v_action.resulting_registration_id,
      'sessionId', v_action.selected_session_id,
      'idempotentReplay', true
    );
  end if;

  select * into v_token
  from public.landerware_scheduling_tokens
  where id = p_token_id
  for update;

  if v_token.id is null then raise exception 'scheduling_token_not_found'; end if;
  if v_token.revoked_at is not null then raise exception 'scheduling_token_revoked'; end if;
  if v_token.expires_at <= now() then raise exception 'scheduling_token_expired'; end if;
  if v_token.completed_action_count >= v_token.max_completed_actions then
    raise exception 'scheduling_token_completed';
  end if;
  if not ('select_session' = any(v_token.allowed_actions)) then
    raise exception 'scheduling_action_not_allowed';
  end if;
  if not (trim(p_course_id) = any(v_token.compatible_course_ids)) then
    raise exception 'incompatible_course';
  end if;
  if cardinality(v_token.allowed_delivery_modes) > 0
     and not (coalesce(trim(p_delivery_mode), '') = any(v_token.allowed_delivery_modes)) then
    raise exception 'incompatible_delivery_mode';
  end if;

  v_payment := jsonb_build_object(
    'policy', v_token.payment_policy,
    'organizationId', v_token.organization_id,
    'resolvedAt', now()
  );

  if v_token.payment_policy = 'self_pay' then
    insert into public.landerware_scheduling_actions(
      token_id, person_id, organization_id, prior_registration_id,
      action_type, status, external_session_id, idempotency_key,
      session_snapshot, payment_snapshot
    ) values (
      v_token.id, v_token.person_id, v_token.organization_id, v_token.registration_id,
      v_token.purpose, 'checkout_required', trim(p_external_session_id), trim(p_idempotency_key),
      jsonb_build_object('courseId', trim(p_course_id), 'courseName', trim(p_course_name),
        'startsAt', p_starts_at, 'endsAt', p_ends_at, 'location', p_location_name,
        'deliveryMode', p_delivery_mode),
      v_payment
    ) returning * into v_action;

    update public.landerware_scheduling_tokens
    set last_opened_at = now(), updated_at = now()
    where id = v_token.id;

    return jsonb_build_object(
      'actionId', v_action.id,
      'status', v_action.status,
      'externalSessionId', trim(p_external_session_id),
      'idempotentReplay', false
    );
  end if;

  insert into public.landerware_sessions(
    external_session_id, course_id, course_name, starts_at, ends_at,
    location_name, organization_id, provenance, requirements_manifest
  ) values (
    trim(p_external_session_id), trim(p_course_id), trim(p_course_name), p_starts_at,
    p_ends_at, nullif(trim(p_location_name), ''), v_token.organization_id,
    'scheduling_gateway:' || v_token.purpose,
    jsonb_build_object('deliveryMode', nullif(trim(p_delivery_mode), ''))
  ) on conflict(external_session_id, course_id, starts_at) do update
    set ends_at = excluded.ends_at,
        location_name = excluded.location_name,
        updated_at = now()
  returning * into v_session;

  insert into public.landerware_rosters(session_id)
  values(v_session.id)
  on conflict(session_id) do update set updated_at = now()
  returning * into v_roster;

  if v_token.registration_id is not null then
    select * into v_prior
    from public.landerware_registrations
    where id = v_token.registration_id
    for update;

    if v_prior.id is null or v_prior.person_id <> v_token.person_id then
      raise exception 'scheduling_registration_mismatch';
    end if;

    if v_prior.session_id = v_session.id and v_prior.status = 'active' then
      v_result := v_prior;
    else
      update public.landerware_registrations
      set status = 'superseded', updated_at = now()
      where id = v_prior.id;

      update public.landerware_roster_memberships
      set attendance_status = 'rescheduled', updated_at = now()
      where registration_id = v_prior.id
        and attendance_status = 'registered';

      insert into public.landerware_registrations(
        person_id, requirement_id, session_id, roster_id, organization_id,
        status, source, supersedes_registration_id, fee_disclosure_version,
        fee_disclosure_presented_at, fee_disclosure_channel, fee_disclosure_accepted_at,
        idempotency_key, course_id, registration_profile_key,
        registration_profile_snapshot, entry_context, session_selection_status,
        selected_options, payer_mode, pricing_state, payment_state, billing_state
      ) values (
        v_prior.person_id, v_prior.requirement_id, v_session.id, v_roster.id,
        coalesce(v_token.organization_id, v_prior.organization_id), 'active',
        'scheduling_gateway', v_prior.id, v_prior.fee_disclosure_version,
        v_prior.fee_disclosure_presented_at, v_prior.fee_disclosure_channel,
        v_prior.fee_disclosure_accepted_at,
        'scheduling-token:' || v_token.id || ':' || trim(p_idempotency_key),
        trim(p_course_id), v_prior.registration_profile_key,
        v_prior.registration_profile_snapshot, v_token.entry_context, 'selected',
        v_prior.selected_options,
        case v_token.payment_policy
          when 'prepaid' then 'prepaid'
          when 'organization_billed' then 'corporate_client_pays'
          when 'no_charge' then 'free'
          else v_prior.payer_mode
        end,
        v_prior.pricing_state,
        case when v_token.payment_policy in ('prepaid','organization_billed','no_charge')
          then 'not_required' else v_prior.payment_state end,
        case when v_token.payment_policy = 'organization_billed'
          then 'pending' else v_prior.billing_state end
      ) returning * into v_result;

      update public.landerware_registrations
      set superseded_by_registration_id = v_result.id, updated_at = now()
      where id = v_prior.id;
    end if;
  else
    if v_token.person_id is null or v_token.registration_profile_key is null then
      raise exception 'known_person_profile_required';
    end if;

    select * into v_person
    from public.landerware_people
    where id = v_token.person_id
    for update;

    if v_person.id is null then raise exception 'scheduling_person_not_found'; end if;

    v_registered := public.landerware_register(
      v_token.registration_profile_key,
      v_token.entry_context,
      jsonb_build_object(
        'first_name', v_person.current_first_name,
        'last_name', v_person.current_last_name,
        'email', v_person.current_email,
        'phone', v_person.current_phone
      ),
      'scheduling-token:' || v_token.id || ':' || trim(p_idempotency_key),
      '{}'::jsonb,
      v_token.organization_id,
      v_token.person_id,
      null,
      null,
      trim(p_external_session_id),
      p_starts_at,
      nullif(trim(p_location_name), ''),
      'scheduling_gateway:' || v_token.purpose,
      jsonb_build_object('deliveryMode', nullif(trim(p_delivery_mode), ''))
    );

    select * into v_result
    from public.landerware_registrations
    where id = (v_registered->>'registrationId')::uuid
    for update;

    update public.landerware_registrations
    set payer_mode = case v_token.payment_policy
          when 'prepaid' then 'prepaid'
          when 'organization_billed' then 'corporate_client_pays'
          when 'no_charge' then 'free'
          else payer_mode
        end,
        payment_state = case when v_token.payment_policy in ('prepaid','organization_billed','no_charge')
          then 'not_required' else payment_state end,
        billing_state = case when v_token.payment_policy = 'organization_billed'
          then 'pending' else billing_state end,
        updated_at = now()
    where id = v_result.id
    returning * into v_result;
  end if;

  insert into public.landerware_roster_memberships(
    roster_id, session_id, person_id, registration_id, display_name, email, source
  ) select
    v_roster.id, v_session.id, v_result.person_id, v_result.id,
    trim(p.current_first_name || ' ' || p.current_last_name), p.current_email,
    'scheduling_gateway'
  from public.landerware_people p
  where p.id = v_result.person_id
    and not exists (
      select 1 from public.landerware_roster_memberships m
      where m.registration_id = v_result.id and m.session_id = v_session.id
    );

  insert into public.landerware_scheduling_actions(
    token_id, person_id, organization_id, prior_registration_id,
    resulting_registration_id, prior_session_id, selected_session_id,
    action_type, status, external_session_id, idempotency_key,
    session_snapshot, payment_snapshot
  ) values (
    v_token.id, v_result.person_id, v_token.organization_id, v_prior.id,
    v_result.id, v_prior.session_id, v_session.id,
    v_token.purpose, 'applied', trim(p_external_session_id), trim(p_idempotency_key),
    jsonb_build_object('courseId', trim(p_course_id), 'courseName', trim(p_course_name),
      'startsAt', p_starts_at, 'endsAt', p_ends_at, 'location', p_location_name,
      'deliveryMode', p_delivery_mode),
    v_payment
  ) returning * into v_action;

  update public.landerware_scheduling_tokens
  set completed_action_count = completed_action_count + 1,
      completed_at = case when completed_action_count + 1 >= max_completed_actions then now() else null end,
      last_opened_at = now(), updated_at = now(), registration_id = v_result.id
  where id = v_token.id;

  insert into public.landerware_activity_events(
    event_type, actor_source, person_id, organization_id, registration_id, session_id, details
  ) values (
    case when v_prior.id is null then 'scheduling_gateway_registered' else 'registration_rescheduled' end,
    'system', v_result.person_id, v_token.organization_id, v_result.id, v_session.id,
    jsonb_build_object('schedulingTokenId', v_token.id, 'actionId', v_action.id,
      'purpose', v_token.purpose, 'priorRegistrationId', v_prior.id,
      'priorSessionId', v_prior.session_id, 'paymentPolicy', v_token.payment_policy)
  );

  if v_prior.id is not null then
    insert into public.landerware_messages(
      person_id, registration_id, template_key, channel, recipient, subject,
      body_text, delivery_provider, delivery_status, idempotency_key
    ) select
      v_result.person_id, v_result.id, 'scheduling-gateway-rescheduled-v1', 'email',
      p.current_email, 'Your 910CPR class has been rescheduled',
      'Your class is now scheduled for ' || trim(p_course_name) || E'.\n\n' ||
        to_char(p_starts_at at time zone 'America/New_York', 'FMDay, FMMonth DD, YYYY at FMHH12:MI AM') ||
        case when nullif(trim(p_location_name), '') is not null then E'\n' || trim(p_location_name) else '' end ||
        E'\n\n910CPR\n910-395-5193',
      'gmail', 'pending', 'scheduling-gateway-confirmation:' || v_action.id
    from public.landerware_people p
    where p.id = v_result.person_id
      and nullif(trim(coalesce(p.current_email, '')), '') is not null
    on conflict(idempotency_key) do nothing;
  end if;

  return jsonb_build_object(
    'actionId', v_action.id,
    'status', v_action.status,
    'registrationId', v_result.id,
    'sessionId', v_session.id,
    'idempotentReplay', false
  );
end $$;

alter table public.landerware_scheduling_tokens enable row level security;
alter table public.landerware_scheduling_actions enable row level security;

revoke all on public.landerware_scheduling_tokens, public.landerware_scheduling_actions
  from public, anon, authenticated;
grant select, insert, update on public.landerware_scheduling_tokens,
  public.landerware_scheduling_actions to service_role;

revoke execute on function public.landerware_apply_scheduling_selection(
  uuid, text, text, text, text, timestamptz, timestamptz, text, text
) from public, anon, authenticated;
grant execute on function public.landerware_apply_scheduling_selection(
  uuid, text, text, text, text, timestamptz, timestamptz, text, text
) to service_role;

commit;
