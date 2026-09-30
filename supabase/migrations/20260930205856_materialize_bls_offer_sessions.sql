begin;

create or replace function public.landerware_create_public_order(
  p_idempotency_key text,
  p_external_class_id text,
  p_course_id text,
  p_payer_email text,
  p_payer_phone text,
  p_students jsonb,
  p_billing_code text default null,
  p_offer jsonb default '{}'::jsonb
) returns jsonb language plpgsql security definer set search_path = '' as $$
declare
  v_order public.landerware_public_orders;
  v_session public.class_sessions;
  v_catalog public.landerware_registration_catalog;
  v_inventory public.landerware_public_session_inventory;
  v_student jsonb; v_addon jsonb; v_addon_catalog jsonb; v_student_code text;
  v_subtotal integer:=0; v_discount integer:=0; v_student_total integer; v_student_discount integer;
  v_taken integer:=0; v_registered integer:=0; v_capacity integer; v_requested integer:=jsonb_array_length(coalesce(p_students,'[]'::jsonb));
  v_course uuid; v_location uuid; v_start timestamptz; v_end timestamptz; v_matches integer;
begin
  if nullif(trim(p_idempotency_key),'') is null or v_requested<1 or v_requested>10 then raise exception 'invalid_order'; end if;
  perform pg_advisory_xact_lock(hashtextextended('landerware-public-offer|'||trim(p_external_class_id),0));
  select * into v_order from public.landerware_public_orders where idempotency_key=trim(p_idempotency_key);
  if v_order.id is not null then return jsonb_build_object('orderId',v_order.id,'recoveryToken',v_order.recovery_token,'holdExpiresAt',v_order.hold_expires_at,'total',v_order.total,'idempotentReplay',true); end if;
  select * into v_session from public.class_sessions where external_class_id=trim(p_external_class_id) and status in ('scheduled','active') and visibility='public' and registration_status='open' order by updated_at desc limit 1 for update;
  if v_session.id is null then
    if trim(p_course_id)<>'209806' or p_offer->>'kind'<>'bls_initial_offer' then raise exception 'session_not_open'; end if;
    if p_offer->>'external_class_id' is distinct from trim(p_external_class_id) then raise exception 'offer_identity_mismatch'; end if;
    v_start:=nullif(p_offer->>'start_at','')::timestamptz; v_end:=nullif(p_offer->>'end_at','')::timestamptz;
    if v_start is null or v_end is null or v_end<=v_start then raise exception 'invalid_offer_window'; end if;
    if coalesce((p_offer->>'capacity')::integer,0)<>6 then raise exception 'invalid_offer_capacity'; end if;
    select count(*),min(id::text)::uuid into v_matches,v_course from public.courses where course_key='aha-bls-provider';
    if v_matches<>1 then raise exception 'unresolved_offer_course'; end if;
    select count(*),min(id::text)::uuid into v_matches,v_location from public.locations where location_key='910cpr-office-shipyard' and scheduling_status='active';
    if v_matches<>1 then raise exception 'unresolved_offer_location'; end if;
    insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,source_location_label)
    values('landerware_public_offer','scheduled','operational',v_course,v_start,v_end,'America/New_York',v_start,v_end,v_location,6,'landerware','public','open',trim(p_external_class_id),nullif(p_offer->>'location_label',''))
    returning * into v_session;
  end if;
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

revoke execute on function public.landerware_create_public_order(text,text,text,text,text,jsonb,text,jsonb) from public,anon,authenticated;
grant execute on function public.landerware_create_public_order(text,text,text,text,text,jsonb,text,jsonb) to service_role;

commit;