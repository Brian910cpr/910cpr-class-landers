begin;

alter table public.landerware_public_order_students
  add column if not exists billing_code text,
  add column if not exists discount integer not null default 0 check (discount >= 0),
  add column if not exists selected_options jsonb not null default '{}'::jsonb;

create or replace function public.landerware_create_public_order(
  p_idempotency_key text,p_external_class_id text,p_course_id text,p_payer_email text,
  p_payer_phone text,p_students jsonb,p_billing_code text default null
) returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_order public.landerware_public_orders; v_session public.class_sessions;
  v_catalog public.landerware_registration_catalog; v_inventory public.landerware_public_session_inventory;
  v_student jsonb; v_addon jsonb; v_addon_catalog jsonb; v_student_code text;
  v_subtotal integer:=0; v_discount integer:=0; v_student_total integer; v_student_discount integer;
  v_taken integer:=0; v_registered integer:=0; v_capacity integer;
  v_requested integer:=jsonb_array_length(coalesce(p_students,'[]'::jsonb));
begin
  if nullif(trim(p_idempotency_key),'') is null or v_requested<1 or v_requested>10 then raise exception 'invalid_order'; end if;
  select * into v_order from public.landerware_public_orders where idempotency_key=trim(p_idempotency_key);
  if v_order.id is not null then return jsonb_build_object('orderId',v_order.id,'recoveryToken',v_order.recovery_token,'holdExpiresAt',v_order.hold_expires_at,'total',v_order.total,'idempotentReplay',true); end if;
  select * into v_session from public.class_sessions where external_class_id=trim(p_external_class_id) and status in ('scheduled','active') and visibility='public' and registration_status='open' order by updated_at desc limit 1 for update;
  if v_session.id is null then raise exception 'session_not_open'; end if;
  select * into v_catalog from public.landerware_registration_catalog where course_id=trim(p_course_id) and active=true;
  if v_catalog.course_id is null then raise exception 'price_catalog_missing'; end if;
  select * into v_inventory from public.landerware_public_session_inventory where external_class_id=trim(p_external_class_id) for update;
  select count(*) into v_registered from public.registrations where class_session_id=v_session.id and status='active';
  select count(*) into v_taken from public.landerware_public_order_students s join public.landerware_public_orders o on o.id=s.order_id where o.external_class_id=trim(p_external_class_id) and o.status in ('held','checkout_open') and o.hold_expires_at>now();
  v_capacity:=coalesce(v_inventory.capacity,v_session.max_students);
  if v_capacity is not null and greatest(v_registered,coalesce(v_inventory.externally_registered,0))+v_taken+v_requested>v_capacity then raise exception 'insufficient_seats'; end if;
  insert into public.landerware_public_orders(idempotency_key,external_class_id,class_session_id,course_id,payer_email,payer_phone,billing_code)
    values(trim(p_idempotency_key),trim(p_external_class_id),v_session.id,trim(p_course_id),lower(trim(p_payer_email)),trim(p_payer_phone),nullif(trim(p_billing_code),'')) returning * into v_order;
  for v_student in select * from jsonb_array_elements(p_students) loop
    if nullif(trim(v_student->>'firstName'),'') is null or nullif(trim(v_student->>'lastName'),'') is null or nullif(trim(v_student->>'email'),'') is null or nullif(trim(v_student->>'phone'),'') is null then raise exception 'required_registration_field_missing'; end if;
    v_student_total:=v_catalog.unit_amount;
    for v_addon in select * from jsonb_array_elements(coalesce(v_student->'addons','[]'::jsonb)) loop
      select value into v_addon_catalog from jsonb_array_elements(v_catalog.addons) where value->>'key'=v_addon->>'key' and coalesce((value->>'active')::boolean,true) limit 1;
      if v_addon_catalog is null then raise exception 'invalid_addon'; end if;
      v_student_total:=v_student_total+coalesce((v_addon_catalog->>'unit_amount')::integer,0)*greatest(coalesce((v_addon->>'quantity')::integer,1),1);
    end loop;
    v_student_code:=coalesce(nullif(trim(v_student->>'billingCode'),''),nullif(trim(p_billing_code),'')); v_student_discount:=0;
    if v_student_code is not null then
      select case when value->>'type'='percent' then round(v_student_total*coalesce((value->>'amount')::numeric,0)/100)::integer when value->>'type'='amount' then least(v_student_total,coalesce((value->>'amount')::integer,0)) else 0 end into v_student_discount from jsonb_array_elements(v_catalog.billing_codes) where lower(value->>'code')=lower(v_student_code) and coalesce((value->>'active')::boolean,true) limit 1;
      if v_student_discount is null then raise exception 'invalid_billing_code'; end if;
    end if;
    insert into public.landerware_public_order_students(order_id,first_name,last_name,email,phone,unit_amount,selected_addons,billing_code,discount,selected_options)
      values(v_order.id,trim(v_student->>'firstName'),trim(v_student->>'lastName'),lower(trim(v_student->>'email')),trim(v_student->>'phone'),v_student_total,coalesce(v_student->'addons','[]'::jsonb),v_student_code,v_student_discount,jsonb_build_object('manualChoice',coalesce(v_student->>'manualChoice','own-copy'),'firstAidChoice',coalesce(v_student->>'firstAidChoice','none')));
    v_subtotal:=v_subtotal+v_student_total; v_discount:=v_discount+v_student_discount;
  end loop;
  update public.landerware_public_orders set subtotal=v_subtotal,discount=v_discount,total=greatest(v_subtotal-v_discount,0),updated_at=now() where id=v_order.id returning * into v_order;
  return jsonb_build_object('orderId',v_order.id,'recoveryToken',v_order.recovery_token,'holdExpiresAt',v_order.hold_expires_at,'subtotal',v_order.subtotal,'discount',v_order.discount,'total',v_order.total,'idempotentReplay',false);
end $$;

create or replace view public.landerware_corporate_invoice_lines as
select o.id as order_id,o.created_at,o.external_class_id,o.course_id,
  s.first_name,s.last_name,s.email,s.billing_code,s.unit_amount as company_amount_cents,
  s.selected_addons,s.selected_options
from public.landerware_public_orders o
join public.landerware_public_order_students s on s.order_id=o.id
where nullif(trim(s.billing_code),'') is not null
  and o.status in ('held','checkout_open','paid');

commit;
