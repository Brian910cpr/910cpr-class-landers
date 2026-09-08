begin;

alter table public.registrations
  add column if not exists idempotency_key text,
  add column if not exists handoff_intent_id uuid,
  add column if not exists external_checkout_url text,
  add column if not exists external_checkout_state text,
  add column if not exists external_checkout_started_at timestamptz,
  add column if not exists external_reconciled_at timestamptz,
  add column if not exists external_reconciliation_evidence jsonb not null default '{}'::jsonb;

create unique index if not exists registrations_idempotency_key_unique
  on public.registrations(idempotency_key)
  where idempotency_key is not null;

create unique index if not exists registrations_handoff_intent_unique
  on public.registrations(handoff_intent_id)
  where handoff_intent_id is not null;

create or replace function public.start_public_registration_intent(
  p_external_class_id text,
  p_first_name text,
  p_last_name text,
  p_email text,
  p_phone text,
  p_idempotency_key text
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_session public.class_sessions;
  v_customer public.customers;
  v_registration public.registrations;
  v_email text := lower(trim(coalesce(p_email, '')));
  v_phone text := regexp_replace(coalesce(p_phone, ''), '[^0-9]', '', 'g');
begin
  if nullif(trim(p_external_class_id), '') is null
     or nullif(trim(p_first_name), '') is null
     or nullif(trim(p_last_name), '') is null
     or v_email = ''
     or length(v_phone) < 10
     or nullif(trim(p_idempotency_key), '') is null then
    raise exception 'required_registration_field_missing';
  end if;

  select * into v_registration
  from public.registrations
  where idempotency_key = 'public-registration:' || trim(p_idempotency_key)
  limit 1;

  if v_registration.id is not null then
    return jsonb_build_object(
      'registrationId', v_registration.id,
      'customerId', v_registration.customer_id,
      'sessionId', v_registration.class_session_id,
      'intentId', v_registration.handoff_intent_id,
      'checkoutUrl', v_registration.external_checkout_url,
      'status', v_registration.status,
      'idempotentReplay', true
    );
  end if;

  select * into v_session
  from public.class_sessions
  where external_class_id = trim(p_external_class_id)
    and record_scope = 'operational'
    and status in ('scheduled', 'active')
    and visibility = 'public'
    and registration_status = 'open'
  order by updated_at desc
  limit 1;

  if v_session.id is null then raise exception 'session_not_open'; end if;
  if coalesce(v_session.registration_url, '') !~ ('^https://coastalcprtraining[.]enrollware[.]com/enroll[?]id=' || trim(p_external_class_id) || '(&.*)?$') then
    raise exception 'invalid_checkout_url';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('public-registration|' || v_email, 0));

  select * into v_customer
  from public.customers
  where lower(trim(coalesce(email, ''))) = v_email
  order by updated_at desc
  limit 1
  for update;

  if v_customer.id is null then
    select * into v_customer
    from public.customers
    where regexp_replace(coalesce(phone, ''), '[^0-9]', '', 'g') = v_phone
      and lower(trim(first_name)) = lower(trim(p_first_name))
      and lower(trim(last_name)) = lower(trim(p_last_name))
    order by updated_at desc
    limit 1
    for update;
  end if;

  if v_customer.id is null then
    insert into public.customers(first_name, last_name, email, phone)
    values (trim(p_first_name), trim(p_last_name), v_email, trim(p_phone))
    returning * into v_customer;
  else
    update public.customers
    set first_name = trim(p_first_name),
        last_name = trim(p_last_name),
        email = v_email,
        phone = trim(p_phone),
        updated_at = now()
    where id = v_customer.id
    returning * into v_customer;
  end if;

  select * into v_registration
  from public.registrations
  where customer_id = v_customer.id and class_session_id = v_session.id
  for update;

  if v_registration.id is null then
    insert into public.registrations(
      customer_id, class_session_id, status, registration_source,
      idempotency_key, handoff_intent_id, external_checkout_url,
      external_checkout_state, external_checkout_started_at
    ) values (
      v_customer.id, v_session.id, 'awaiting_external_checkout', 'landerware_front_door',
      'public-registration:' || trim(p_idempotency_key), gen_random_uuid(),
      v_session.registration_url, 'awaiting_completion', now()
    ) returning * into v_registration;
  end if;

  return jsonb_build_object(
    'registrationId', v_registration.id,
    'customerId', v_registration.customer_id,
    'sessionId', v_registration.class_session_id,
    'intentId', v_registration.handoff_intent_id,
    'checkoutUrl', coalesce(v_registration.external_checkout_url, v_session.registration_url),
    'status', v_registration.status,
    'idempotentReplay', false
  );
end $$;

revoke execute on function public.start_public_registration_intent(text,text,text,text,text,text) from public, anon, authenticated;
grant execute on function public.start_public_registration_intent(text,text,text,text,text,text) to service_role;

commit;
