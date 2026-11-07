-- Atomic shared-capacity reservations. These RPCs are private server capabilities.
-- No public grants, existing table permissions, or session schedule are changed.
create or replace function public.pool_event_capacity()
returns jsonb language sql security invoker set search_path = '' as $$
  with occupied as (
    select r.customer_id, bool_or(r.status = 'registered') as registered
    from public.registrations r join public.class_sessions s on s.id = r.class_session_id
    where s.external_class_id in ('nseaswim-pool-family-2027-02-15','nseaswim-pool-bls-2027-02-15')
      and (r.status = 'registered' or (r.status = 'payment_pending' and
        case when r.optional_survey ? 'holdExpiresAt' then (r.optional_survey->>'holdExpiresAt')::timestamptz > now()
             else r.updated_at > now() - interval '30 minutes' end))
    group by r.customer_id
  ) select jsonb_build_object('registered',count(*) filter (where registered),
    'checkoutHolds',count(*) filter (where not registered),'occupied',count(*),
    'remaining',greatest(0,30-count(*))) from occupied;
$$;
revoke all on function public.pool_event_capacity() from public, anon, authenticated;
grant execute on function public.pool_event_capacity() to service_role;

create or replace function public.reserve_pool_registration(p_event text,p_request_id uuid,p_fingerprint text,p_input jsonb)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare
  v_session public.class_sessions%rowtype;
  v_existing public.registrations%rowtype;
  v_previous public.registrations%rowtype;
  v_primary uuid; v_customer uuid; v_guest_customer uuid; v_order uuid; v_product uuid;
  v_ids uuid[]; v_guests jsonb; v_name text; v_first text; v_last text;
  v_count integer; v_ebooks integer; v_remaining integer; v_i integer;
  v_key text; v_prefix text; v_status text; v_survey jsonb; v_paid boolean; v_history jsonb := '[]'::jsonb;
begin
  if p_event not in ('nseaswim-pool-family-2027-02-15','nseaswim-pool-bls-2027-02-15') or p_request_id is null then
    return jsonb_build_object('ok',false,'code','invalid_input','error','Event not found.');
  end if;
  v_paid := p_event = 'nseaswim-pool-bls-2027-02-15';
  v_count := (p_input->>'attendeeCount')::integer;
  v_ebooks := (p_input->>'ebookQty')::integer;
  v_guests := p_input->'guestNames';
  if v_count is null or v_count not between 1 and 30 or v_ebooks is null or v_ebooks not between 0 and v_count or
     (not v_paid and v_ebooks <> 0) or jsonb_typeof(v_guests) is distinct from 'array' or
     jsonb_array_length(v_guests) <> v_count-1 or nullif(trim(p_input->>'email'),'') is null or
     nullif(trim(p_input->>'firstName'),'') is null or nullif(trim(p_input->>'lastName'),'') is null then
    return jsonb_build_object('ok',false,'code','invalid_input','error','Please check all registration fields.');
  end if;
  -- All pool reservations and payment transitions serialize on one shared resource.
  perform pg_advisory_xact_lock(9102027,215);
  v_key := 'pool2027:' || p_event || ':' || p_request_id::text;
  select * into v_existing from public.registrations where idempotency_key = v_key;
  if found then
    if v_existing.optional_survey->>'requestFingerprint' is distinct from p_fingerprint then
      return jsonb_build_object('ok',false,'code','request_conflict','error','This registration attempt already has different details. Resume the original registration.');
    end if;
    return jsonb_build_object('ok',true,'registrationId',v_existing.id,'replayed',true);
  end if;
  select * into v_session from public.class_sessions where external_class_id = p_event for update;
  if not found or v_session.registration_backend <> 'landerware' or v_session.registration_status <> 'open' or
     v_session.visibility <> (case when v_paid then 'unlisted' else 'public' end) or v_session.start_at <= now() then
    return jsonb_build_object('ok',false,'code','registration_closed','error','Registration is not open.');
  end if;
  -- A second key cannot silently duplicate an attendee or charge. Expired checkout
  -- must first be verified with Stripe and canceled by expire_pool_registration.
  select r.* into v_previous from public.registrations r join public.customers c on c.id=r.customer_id
    where r.class_session_id=v_session.id and lower(c.email)=lower(p_input->>'email')
    order by r.created_at desc limit 1;
  if found and v_previous.status <> 'canceled' then
    return jsonb_build_object('ok',false,'code','duplicate_registration','error','There is already a registration for this email. Resume the original checkout or contact 910CPR before registering again.');
  end if;
  if v_previous.id is not null then
    if not exists(select 1 from public.customers where id=v_previous.customer_id and
      lower(trim(first_name))=lower(trim(p_input->>'firstName')) and lower(trim(last_name))=lower(trim(p_input->>'lastName'))) then
      return jsonb_build_object('ok',false,'code','duplicate_registration','error','This email is associated with a different attendee. Please contact 910CPR before registering again.');
    end if;
    -- The canonical customer/session constraint requires reusing the registration.
    -- Preserve prior checkout and order provenance before replacing its attempt.
    v_history := coalesce(v_previous.optional_survey->'previousAttempts','[]'::jsonb);
    v_history := v_history || jsonb_build_array(jsonb_build_object(
      'idempotencyKey',v_previous.idempotency_key,'requestFingerprint',v_previous.optional_survey->'requestFingerprint',
      'groupRegistrationIds',v_previous.optional_survey->'groupRegistrationIds','canceledAt',v_previous.canceled_at,
      'order',(select to_jsonb(o) from public.registration_orders o where registration_id=v_previous.id),
      'orderItems',(select jsonb_agg(to_jsonb(i)) from public.registration_order_items i join public.registration_orders o on o.id=i.order_id where o.registration_id=v_previous.id)));
  end if;
  v_remaining := (public.pool_event_capacity()->>'remaining')::integer;
  if v_count > v_remaining then
    return jsonb_build_object('ok',false,'code','capacity','error',format('Only %s hands-on spots remain across both pool sessions.',v_remaining),'remaining',v_remaining);
  end if;
  if v_paid and v_ebooks > 0 then
    select id into v_product from public.products where product_key='aha-bls-2025-emanual' and active=true limit 1;
    if v_product is null then raise exception 'pool_manual_unavailable'; end if;
  end if;
  v_customer := v_previous.customer_id;
  if v_customer is null then
    select id into v_customer from public.customers where lower(email)=lower(p_input->>'email')
      and lower(first_name)=lower(p_input->>'firstName') and lower(last_name)=lower(p_input->>'lastName') limit 1;
  end if;
  if v_customer is null then
    insert into public.customers(first_name,last_name,email,phone)
      values(p_input->>'firstName',p_input->>'lastName',lower(p_input->>'email'),nullif(p_input->>'phone','')) returning id into v_customer;
  end if;
  v_primary := coalesce(v_previous.id,gen_random_uuid());
  v_ids := array[v_primary];
  for v_i in 2..v_count loop v_ids := array_append(v_ids,gen_random_uuid()); end loop;
  v_prefix := case when v_paid then 'public_landerware_event:bls' else 'public_landerware_event:friends_family' end;
  v_status := case when v_paid then 'payment_pending' else 'registered' end;
  v_survey := jsonb_build_object('survey',coalesce(p_input->'survey','{}'::jsonb),
    'groupRegistrationIds',to_jsonb(v_ids),'attendeeCount',v_count,'guestNames',v_guests,'ebookQty',v_ebooks,
    'contactEmail',lower(p_input->>'email'),'contactFirstName',p_input->>'firstName','contactLastName',p_input->>'lastName',
    'requestFingerprint',p_fingerprint,'previousAttempts',v_history,'holdExpiresAt',date_trunc('second',now()+interval '35 minutes'));
  insert into public.registrations(id,customer_id,class_session_id,status,registration_source,optional_survey,idempotency_key)
    values(v_primary,v_customer,v_session.id,v_status,v_prefix||':group:'||p_request_id::text,v_survey,v_key)
    on conflict(id) do update set status=excluded.status,registration_source=excluded.registration_source,
      optional_survey=excluded.optional_survey,idempotency_key=excluded.idempotency_key,canceled_at=null,updated_at=now();
  for v_i in 1..v_count-1 loop
    v_name := trim(v_guests->>(v_i-1));
    v_first := split_part(v_name,' ',1);
    v_last := coalesce(nullif(trim(substr(v_name,length(v_first)+1)),''),'Guest');
    insert into public.customers(first_name,last_name) values(v_first,v_last) returning id into v_guest_customer;
    insert into public.registrations(id,customer_id,class_session_id,status,registration_source,optional_survey)
      values(v_ids[v_i+1],v_guest_customer,v_session.id,v_status,v_prefix||':guest:'||p_request_id::text,
        jsonb_build_object('hostRegistrationId',v_primary,'holdExpiresAt',v_survey->'holdExpiresAt'));
  end loop;
  if v_paid then
    insert into public.registration_orders(registration_id,status,currency,course_amount,materials_amount,total_amount)
      values(v_primary,'payment_pending','usd',25*v_count,18.51*v_ebooks,25*v_count+18.51*v_ebooks)
      on conflict(registration_id) do update set status='payment_pending',course_amount=excluded.course_amount,
        materials_amount=excluded.materials_amount,total_amount=excluded.total_amount,currency='usd',
        stripe_checkout_session_id=null,stripe_payment_intent_id=null,paid_at=null,updated_at=now()
      returning id into v_order;
    delete from public.registration_order_items where order_id=v_order;
    insert into public.registration_order_items(order_id,item_type,description,quantity,unit_amount,fulfillment_status)
      values(v_order,'course','AHA BLS Provider - February 15 community event',v_count,25,'not_required');
    if v_ebooks > 0 then
      insert into public.registration_order_items(order_id,item_type,product_id,description,quantity,unit_amount,fulfillment_status)
        values(v_order,'material',v_product,'2025 AHA BLS Provider eManual',v_ebooks,18.51,'awaiting_payment');
    end if;
  end if;
  return jsonb_build_object('ok',true,'registrationId',v_primary,'groupRegistrationIds',to_jsonb(v_ids));
end;
$$;
revoke all on function public.reserve_pool_registration(text,uuid,text,jsonb) from public, anon, authenticated;
grant execute on function public.reserve_pool_registration(text,uuid,text,jsonb) to service_role;

create or replace function public.bind_pool_checkout(p_registration_id uuid,p_request_id uuid,p_checkout_session_id text)
returns void language plpgsql security invoker set search_path = '' as $$
declare v_key text; v_checkout text;
begin
  perform pg_advisory_xact_lock(9102027,215);
  select idempotency_key into v_key from public.registrations where id=p_registration_id;
  if v_key is distinct from 'pool2027:nseaswim-pool-bls-2027-02-15:'||p_request_id::text or
     p_checkout_session_id is null or p_checkout_session_id not like 'cs_%' then raise exception 'pool_checkout_attempt_mismatch'; end if;
  select stripe_checkout_session_id into v_checkout from public.registration_orders where registration_id=p_registration_id for update;
  if not found or (v_checkout is not null and v_checkout<>p_checkout_session_id) then raise exception 'pool_checkout_binding_mismatch'; end if;
  update public.registration_orders set stripe_checkout_session_id=p_checkout_session_id,updated_at=now() where registration_id=p_registration_id;
end;
$$;
revoke all on function public.bind_pool_checkout(uuid,uuid,text) from public, anon, authenticated;
grant execute on function public.bind_pool_checkout(uuid,uuid,text) to service_role;

create or replace function public.confirm_pool_registration_payment(p_registration_id uuid,p_checkout_session_id text,p_amount_total bigint,p_currency text,p_payment_intent_id text)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare
  v_reg public.registrations%rowtype; v_order public.registration_orders%rowtype;
  v_ids uuid[]; v_occupied integer; v_extra integer;
begin
  perform pg_advisory_xact_lock(9102027,215);
  select r.* into v_reg from public.registrations r join public.class_sessions s on s.id=r.class_session_id
    where r.id=p_registration_id and s.external_class_id='nseaswim-pool-bls-2027-02-15' for update of r;
  if not found then raise exception 'pool_registration_not_found'; end if;
  select * into v_order from public.registration_orders where registration_id=p_registration_id for update;
  if not found or v_order.stripe_checkout_session_id is distinct from p_checkout_session_id or p_checkout_session_id is null or
     p_currency is distinct from 'usd' or v_order.currency <> 'usd' or
     p_amount_total is distinct from round(v_order.total_amount*100)::bigint then raise exception 'pool_payment_mismatch'; end if;
  if v_order.status='paid' and v_reg.status='registered' then return jsonb_build_object('ok',true,'alreadyConfirmed',true); end if;
  if v_order.status not in ('payment_pending','payment_failed') then raise exception 'pool_order_not_payable'; end if;
  select array_agg(value::uuid) into v_ids from jsonb_array_elements_text(v_reg.optional_survey->'groupRegistrationIds');
  if v_ids is null or not p_registration_id=any(v_ids) or cardinality(v_ids)<>(v_reg.optional_survey->>'attendeeCount')::integer or
    (select count(*) from public.registrations where id=any(v_ids) and class_session_id=v_reg.class_session_id and status in ('payment_pending','registered'))<>cardinality(v_ids) then
    raise exception 'pool_group_mismatch';
  end if;
  -- A late provider callback must never silently oversell an expired reservation.
  v_occupied := (public.pool_event_capacity()->>'occupied')::integer;
  select count(*) into v_extra from public.registrations r where r.id=any(v_ids) and r.status<>'registered'
    and (r.optional_survey->>'holdExpiresAt')::timestamptz <= now();
  if v_occupied+v_extra > 30 then raise exception 'pool_paid_capacity_review_required'; end if;
  update public.registration_orders set status='paid',stripe_payment_intent_id=p_payment_intent_id,paid_at=now(),updated_at=now() where id=v_order.id;
  update public.registrations set status='registered',updated_at=now() where id=any(v_ids);
  update public.registrations set optional_survey=optional_survey||jsonb_build_object('stripePaidAmount',p_amount_total,'stripeCheckoutSessionId',p_checkout_session_id,'stripePaidAt',now()) where id=p_registration_id;
  update public.registration_order_items set fulfillment_status='awaiting_attention',updated_at=now() where order_id=v_order.id and fulfillment_status='awaiting_payment';
  return jsonb_build_object('ok',true,'registrationId',p_registration_id,'groupRegistrationIds',to_jsonb(v_ids),'orderId',v_order.id);
end;
$$;
revoke all on function public.confirm_pool_registration_payment(uuid,text,bigint,text,text) from public, anon, authenticated;
grant execute on function public.confirm_pool_registration_payment(uuid,text,bigint,text,text) to service_role;

create or replace function public.expire_pool_registration(p_registration_id uuid,p_checkout_session_id text)
returns void language plpgsql security invoker set search_path = '' as $$
declare v_reg public.registrations%rowtype; v_order public.registration_orders%rowtype; v_ids uuid[];
begin
  perform pg_advisory_xact_lock(9102027,215);
  select r.* into v_reg from public.registrations r join public.class_sessions s on s.id=r.class_session_id
    where r.id=p_registration_id and s.external_class_id='nseaswim-pool-bls-2027-02-15' for update of r;
  if not found then raise exception 'pool_registration_not_found'; end if;
  select * into v_order from public.registration_orders where registration_id=p_registration_id for update;
  if not found or v_order.stripe_checkout_session_id is distinct from p_checkout_session_id then raise exception 'pool_checkout_mismatch'; end if;
  if p_checkout_session_id is null and (v_reg.optional_survey->>'holdExpiresAt')::timestamptz > now() then raise exception 'pool_hold_not_expired'; end if;
  if v_order.status='paid' then raise exception 'pool_order_already_paid'; end if;
  select array_agg(value::uuid) into v_ids from jsonb_array_elements_text(v_reg.optional_survey->'groupRegistrationIds');
  update public.registrations set status='canceled',canceled_at=now(),updated_at=now() where id=any(v_ids) and status='payment_pending';
  update public.registration_orders set status='canceled',updated_at=now() where id=v_order.id;
  update public.registration_order_items set fulfillment_status='canceled',updated_at=now() where order_id=v_order.id and fulfillment_status='awaiting_payment';
end;
$$;
revoke all on function public.expire_pool_registration(uuid,text) from public, anon, authenticated;
grant execute on function public.expire_pool_registration(uuid,text) to service_role;

update public.class_sessions set public_notes=replace(public_notes,'eBook optional $20','eBook optional $18.51')
where external_class_id='nseaswim-pool-bls-2027-02-15' and public_notes like '%eBook optional $20%';
