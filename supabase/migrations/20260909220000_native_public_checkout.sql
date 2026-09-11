begin;

create table if not exists public.landerware_registration_catalog (
  course_id text primary key,
  source text not null default 'enrollware',
  course_name text not null,
  unit_amount integer not null check (unit_amount >= 0),
  currency text not null default 'usd',
  addons jsonb not null default '[]'::jsonb,
  billing_codes jsonb not null default '[]'::jsonb,
  source_snapshot jsonb not null default '{}'::jsonb,
  imported_at timestamptz not null default now(),
  active boolean not null default true
);

create table if not exists public.landerware_public_session_inventory (
  external_class_id text primary key,
  capacity integer check (capacity is null or capacity >= 0),
  externally_registered integer not null default 0 check (externally_registered >= 0),
  source text not null default 'enrollware',
  imported_at timestamptz not null default now()
);

create table if not exists public.landerware_public_orders (
  id uuid primary key default gen_random_uuid(),
  recovery_token uuid not null default gen_random_uuid() unique,
  idempotency_key text not null unique,
  external_class_id text not null,
  class_session_id uuid references public.class_sessions(id) on delete set null,
  course_id text not null,
  payer_email text not null,
  payer_phone text,
  status text not null default 'held' check (status in ('held','checkout_open','paid','expired','cancelled','refunded')),
  currency text not null default 'usd',
  subtotal integer not null default 0,
  discount integer not null default 0,
  total integer not null default 0,
  billing_code text,
  stripe_checkout_session_id text unique,
  stripe_payment_intent_id text,
  checkout_url text,
  hold_expires_at timestamptz not null default (now() + interval '30 minutes'),
  paid_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.landerware_public_order_students (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.landerware_public_orders(id) on delete cascade,
  first_name text not null,
  last_name text not null,
  email text not null,
  phone text not null,
  unit_amount integer not null,
  selected_addons jsonb not null default '[]'::jsonb,
  registration_id uuid references public.registrations(id) on delete set null,
  created_at timestamptz not null default now()
);

create index if not exists landerware_public_orders_active_hold
  on public.landerware_public_orders(external_class_id, hold_expires_at)
  where status in ('held','checkout_open');

insert into public.landerware_registration_catalog(course_id,source,course_name,unit_amount,currency,addons,billing_codes,source_snapshot)
values
  ('209806','enrollware','AHA BLS Provider – In-Person',7500,'usd','[]','[]','{"source_file":"raw/course_archive_v4.json","snapshot_price":75}'),
  ('359474','enrollware','AHA BLS Provider – In-Person Renewal',7500,'usd','[]','[]','{"source_file":"raw/course_archive_v4.json","snapshot_price":75}'),
  ('210549','enrollware','AHA BLS Provider – HeartCode + Skills Session',5500,'usd','[]','[]','{"source_file":"raw/course_archive_v4.json","snapshot_price":55}')
on conflict (course_id) do update set
  source=excluded.source,course_name=excluded.course_name,unit_amount=excluded.unit_amount,
  currency=excluded.currency,addons=excluded.addons,billing_codes=excluded.billing_codes,
  source_snapshot=excluded.source_snapshot,imported_at=now(),active=true;

alter table public.landerware_registration_catalog enable row level security;
alter table public.landerware_public_session_inventory enable row level security;
alter table public.landerware_public_orders enable row level security;
alter table public.landerware_public_order_students enable row level security;
revoke all on public.landerware_registration_catalog, public.landerware_public_session_inventory, public.landerware_public_orders, public.landerware_public_order_students from anon, authenticated;
grant select, insert, update on public.landerware_registration_catalog, public.landerware_public_session_inventory, public.landerware_public_orders, public.landerware_public_order_students to service_role;

create or replace function public.landerware_create_public_order(
  p_idempotency_key text,
  p_external_class_id text,
  p_course_id text,
  p_payer_email text,
  p_payer_phone text,
  p_students jsonb,
  p_billing_code text default null
) returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_order public.landerware_public_orders;
  v_session public.class_sessions;
  v_catalog public.landerware_registration_catalog;
  v_inventory public.landerware_public_session_inventory;
  v_student jsonb;
  v_addon jsonb;
  v_addon_catalog jsonb;
  v_subtotal integer := 0;
  v_student_total integer;
  v_discount integer := 0;
  v_taken integer := 0;
  v_registered integer := 0;
  v_capacity integer;
  v_requested integer := jsonb_array_length(coalesce(p_students, '[]'::jsonb));
begin
  if nullif(trim(p_idempotency_key),'') is null or v_requested < 1 or v_requested > 10 then raise exception 'invalid_order'; end if;
  select * into v_order from public.landerware_public_orders where idempotency_key=trim(p_idempotency_key);
  if v_order.id is not null then return jsonb_build_object('orderId',v_order.id,'recoveryToken',v_order.recovery_token,'holdExpiresAt',v_order.hold_expires_at,'total',v_order.total,'idempotentReplay',true); end if;
  select * into v_session from public.class_sessions where external_class_id=trim(p_external_class_id) and status in ('scheduled','active') and visibility='public' and registration_status='open' order by updated_at desc limit 1 for update;
  if v_session.id is null then raise exception 'session_not_open'; end if;
  select * into v_catalog from public.landerware_registration_catalog where course_id=trim(p_course_id) and active=true;
  if v_catalog.course_id is null then raise exception 'price_catalog_missing'; end if;
  select * into v_inventory from public.landerware_public_session_inventory where external_class_id=trim(p_external_class_id) for update;
  select count(*) into v_registered from public.registrations where class_session_id=v_session.id and status='active';
  select count(*) into v_taken from public.landerware_public_order_students s join public.landerware_public_orders o on o.id=s.order_id where o.external_class_id=trim(p_external_class_id) and o.status in ('held','checkout_open') and o.hold_expires_at>now();
  v_capacity := coalesce(v_inventory.capacity,v_session.max_students);
  if v_capacity is not null and greatest(v_registered,coalesce(v_inventory.externally_registered,0)) + v_taken + v_requested > v_capacity then raise exception 'insufficient_seats'; end if;
  insert into public.landerware_public_orders(idempotency_key,external_class_id,class_session_id,course_id,payer_email,payer_phone,billing_code)
    values(trim(p_idempotency_key),trim(p_external_class_id),v_session.id,trim(p_course_id),lower(trim(p_payer_email)),trim(p_payer_phone),nullif(trim(p_billing_code),'')) returning * into v_order;
  for v_student in select * from jsonb_array_elements(p_students) loop
    if nullif(trim(v_student->>'firstName'),'') is null or nullif(trim(v_student->>'lastName'),'') is null or nullif(trim(v_student->>'email'),'') is null or nullif(trim(v_student->>'phone'),'') is null then raise exception 'required_registration_field_missing'; end if;
    v_student_total := v_catalog.unit_amount;
    for v_addon in select * from jsonb_array_elements(coalesce(v_student->'addons','[]'::jsonb)) loop
      select value into v_addon_catalog from jsonb_array_elements(v_catalog.addons) where value->>'key'=v_addon->>'key' and coalesce((value->>'active')::boolean,true) limit 1;
      if v_addon_catalog is null then raise exception 'invalid_addon'; end if;
      v_student_total := v_student_total + coalesce((v_addon_catalog->>'unit_amount')::integer,0) * greatest(coalesce((v_addon->>'quantity')::integer,1),1);
    end loop;
    insert into public.landerware_public_order_students(order_id,first_name,last_name,email,phone,unit_amount,selected_addons) values(v_order.id,trim(v_student->>'firstName'),trim(v_student->>'lastName'),lower(trim(v_student->>'email')),trim(v_student->>'phone'),v_student_total,coalesce(v_student->'addons','[]'::jsonb));
    v_subtotal := v_subtotal + v_student_total;
  end loop;
  if nullif(trim(p_billing_code),'') is not null then
    select case when value->>'type'='percent' then round(v_subtotal*coalesce((value->>'amount')::numeric,0)/100)::integer when value->>'type'='amount' then least(v_subtotal,coalesce((value->>'amount')::integer,0)) else 0 end into v_discount from jsonb_array_elements(v_catalog.billing_codes) where lower(value->>'code')=lower(trim(p_billing_code)) and coalesce((value->>'active')::boolean,true) limit 1;
    if v_discount is null then raise exception 'invalid_billing_code'; end if;
  end if;
  update public.landerware_public_orders set subtotal=v_subtotal,discount=v_discount,total=greatest(v_subtotal-v_discount,0),updated_at=now() where id=v_order.id returning * into v_order;
  return jsonb_build_object('orderId',v_order.id,'recoveryToken',v_order.recovery_token,'holdExpiresAt',v_order.hold_expires_at,'subtotal',v_order.subtotal,'discount',v_order.discount,'total',v_order.total,'idempotentReplay',false);
end $$;

revoke execute on function public.landerware_create_public_order(text,text,text,text,text,jsonb,text) from public,anon,authenticated;
grant execute on function public.landerware_create_public_order(text,text,text,text,text,jsonb,text) to service_role;

create or replace function public.landerware_finalize_public_order(
  p_order_id uuid,
  p_stripe_payment_intent_id text
) returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_order public.landerware_public_orders;
  v_student public.landerware_public_order_students;
  v_customer public.customers;
  v_registration public.registrations;
  v_count integer := 0;
begin
  select * into v_order from public.landerware_public_orders where id=p_order_id for update;
  if v_order.id is null then raise exception 'order_not_found'; end if;
  if v_order.status='paid' then return jsonb_build_object('orderId',v_order.id,'status','paid','registrations',jsonb_array_length((select coalesce(jsonb_agg(registration_id),'[]'::jsonb) from public.landerware_public_order_students where order_id=v_order.id and registration_id is not null)),'idempotentReplay',true); end if;
  if v_order.status not in ('held','checkout_open') then raise exception 'order_not_payable'; end if;
  for v_student in select * from public.landerware_public_order_students where order_id=v_order.id order by created_at loop
    select * into v_customer from public.customers where lower(trim(coalesce(email,'')))=lower(v_student.email) order by updated_at desc limit 1 for update;
    if v_customer.id is null then insert into public.customers(first_name,last_name,email,phone) values(v_student.first_name,v_student.last_name,v_student.email,v_student.phone) returning * into v_customer;
    else update public.customers set first_name=v_student.first_name,last_name=v_student.last_name,phone=v_student.phone,updated_at=now() where id=v_customer.id returning * into v_customer; end if;
    select * into v_registration from public.registrations where customer_id=v_customer.id and class_session_id=v_order.class_session_id limit 1 for update;
    if v_registration.id is null then insert into public.registrations(customer_id,class_session_id,status,registration_source) values(v_customer.id,v_order.class_session_id,'active','landerware_native_checkout') returning * into v_registration; end if;
    update public.landerware_public_order_students set registration_id=v_registration.id where id=v_student.id;
    v_count := v_count + 1;
  end loop;
  update public.landerware_public_orders set status='paid',stripe_payment_intent_id=nullif(trim(p_stripe_payment_intent_id),''),paid_at=now(),updated_at=now() where id=v_order.id returning * into v_order;
  return jsonb_build_object('orderId',v_order.id,'status','paid','registrations',v_count,'idempotentReplay',false);
end $$;

revoke execute on function public.landerware_finalize_public_order(uuid,text) from public,anon,authenticated;
grant execute on function public.landerware_finalize_public_order(uuid,text) to service_role;

commit;
