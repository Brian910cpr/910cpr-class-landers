begin;

create table if not exists public.public_registration_intents (
  id uuid primary key default gen_random_uuid(),
  idempotency_key text not null unique,
  external_class_id text not null,
  course_name text not null,
  starts_at timestamptz not null,
  ends_at timestamptz,
  location_name text,
  checkout_url text not null,
  first_name text not null,
  last_name text not null,
  email text not null,
  phone text not null,
  status text not null default 'awaiting_external_checkout',
  registration_id uuid references public.registrations(id) on delete set null,
  reconciliation_evidence jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists public_registration_intents_class_created
  on public.public_registration_intents(external_class_id, created_at desc);

alter table public.public_registration_intents enable row level security;
revoke all on public.public_registration_intents from anon, authenticated;
grant select, insert, update on public.public_registration_intents to service_role;

create or replace function public.queue_public_registration_intent(
  p_external_class_id text,
  p_course_name text,
  p_starts_at timestamptz,
  p_ends_at timestamptz,
  p_location_name text,
  p_checkout_url text,
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
  v_intent public.public_registration_intents;
  v_email text := lower(trim(coalesce(p_email, '')));
  v_phone text := regexp_replace(coalesce(p_phone, ''), '[^0-9]', '', 'g');
begin
  if nullif(trim(p_external_class_id), '') is null
     or nullif(trim(p_course_name), '') is null
     or p_starts_at is null
     or nullif(trim(p_first_name), '') is null
     or nullif(trim(p_last_name), '') is null
     or v_email = '' or length(v_phone) < 10
     or nullif(trim(p_idempotency_key), '') is null then
    raise exception 'required_registration_field_missing';
  end if;
  if coalesce(p_checkout_url, '') !~ ('^https://coastalcprtraining[.]enrollware[.]com/enroll[?]id=' || trim(p_external_class_id) || '(&.*)?$') then
    raise exception 'invalid_checkout_url';
  end if;

  insert into public.public_registration_intents(
    idempotency_key, external_class_id, course_name, starts_at, ends_at,
    location_name, checkout_url, first_name, last_name, email, phone
  ) values (
    'public-registration:' || trim(p_idempotency_key), trim(p_external_class_id),
    trim(p_course_name), p_starts_at, p_ends_at, nullif(trim(p_location_name), ''),
    p_checkout_url, trim(p_first_name), trim(p_last_name), v_email, trim(p_phone)
  ) on conflict (idempotency_key) do update
    set updated_at = now()
  returning * into v_intent;

  return jsonb_build_object(
    'intentId', v_intent.id,
    'externalClassId', v_intent.external_class_id,
    'checkoutUrl', v_intent.checkout_url,
    'status', v_intent.status,
    'idempotentReplay', v_intent.created_at <> v_intent.updated_at
  );
end $$;

revoke execute on function public.queue_public_registration_intent(text,text,timestamptz,timestamptz,text,text,text,text,text,text,text) from public, anon, authenticated;
grant execute on function public.queue_public_registration_intent(text,text,timestamptz,timestamptz,text,text,text,text,text,text,text) to service_role;

commit;
