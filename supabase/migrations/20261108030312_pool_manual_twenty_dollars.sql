-- New quotes use $20 and collect each attendee's email. Existing orders and
-- attempt history remain unchanged; guest email collection grants no send consent.
CREATE OR REPLACE FUNCTION public.reserve_pool_registration(p_event text, p_request_id uuid, p_fingerprint text, p_input jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare
  v_session public.class_sessions%rowtype;
  v_existing public.registrations%rowtype;
  v_previous public.registrations%rowtype;
  v_primary uuid; v_customer uuid; v_guest_customer uuid; v_order uuid; v_product uuid;
  v_ids uuid[]; v_guests jsonb; v_emails jsonb; v_email text; v_name text; v_first text; v_last text;
  v_count integer; v_ebooks integer; v_remaining integer; v_i integer;
  v_key text; v_prefix text; v_status text; v_survey jsonb; v_paid boolean; v_history jsonb := '[]'::jsonb;
begin
  -- Fail closed during the brief endpoint/migration rollover: the old handler
  -- neither saves guest emails nor uses durable order pricing for new checkouts.
  if p_input->>'contractVersion' is distinct from '2' then
    return jsonb_build_object('ok',false,'code','invalid_input','error','Registration has been updated. Please reload the page and try again.');
  end if;
  if p_event not in ('nseaswim-pool-family-2027-02-15','nseaswim-pool-bls-2027-02-15') or p_request_id is null then
    return jsonb_build_object('ok',false,'code','invalid_input','error','Event not found.');
  end if;
  v_paid := p_event = 'nseaswim-pool-bls-2027-02-15';
  v_count := (p_input->>'attendeeCount')::integer;
  v_ebooks := (p_input->>'ebookQty')::integer;
  v_guests := p_input->'guestNames';
  v_emails := coalesce(p_input->'guestEmails','[]'::jsonb);
  if v_count is null or v_count not between 1 and 30 or v_ebooks is null or v_ebooks not between 0 and v_count or
     (not v_paid and v_ebooks <> 0) or jsonb_typeof(v_guests) is distinct from 'array' or
     jsonb_array_length(v_guests) <> v_count-1 or nullif(trim(p_input->>'email'),'') is null or
     nullif(trim(p_input->>'firstName'),'') is null or nullif(trim(p_input->>'lastName'),'') is null then
    return jsonb_build_object('ok',false,'code','invalid_input','error','Please check all registration fields.');
  end if;
  if jsonb_typeof(v_emails) is distinct from 'array' or jsonb_array_length(v_emails) <> v_count-1 then
    return jsonb_build_object('ok',false,'code','invalid_input','error','Please provide an email address for every additional attendee.');
  end if;
  if exists(select 1 from jsonb_array_elements_text(v_emails) as e(email) where email is null or length(email)>160 or email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$') then
    return jsonb_build_object('ok',false,'code','invalid_input','error','Please enter a valid email address for every additional attendee.');
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
  -- Reuse only an exact guest identity; never change an existing profile.
  for v_i in 1..v_count-1 loop
    v_name := trim(v_guests->>(v_i-1));
    v_first := split_part(v_name,' ',1);
    v_last := coalesce(nullif(trim(substr(v_name,length(v_first)+1)),''),'Guest');
    v_email := lower(trim(v_emails->>(v_i-1)));
    if exists(select 1 from public.customers c join public.registrations r on r.customer_id=c.id
      where lower(c.email)=v_email and lower(c.first_name)=lower(v_first) and lower(c.last_name)=lower(v_last) and r.class_session_id=v_session.id and r.status<>'canceled') then
      return jsonb_build_object('ok',false,'code','invalid_input','error','An additional attendee is already registered for this event. Please list each attendee only once.');
    end if;
  end loop;
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
    'groupRegistrationIds',to_jsonb(v_ids),'attendeeCount',v_count,'guestNames',v_guests,'guestEmails',v_emails,'ebookQty',v_ebooks,
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
    v_email := lower(trim(v_emails->>(v_i-1)));
    select c.id into v_guest_customer from public.customers c where lower(c.email)=v_email and lower(c.first_name)=lower(v_first) and lower(c.last_name)=lower(v_last)
      and not exists(select 1 from public.registrations r where r.customer_id=c.id and r.class_session_id=v_session.id) limit 1;
    if v_guest_customer is null then
      insert into public.customers(first_name,last_name,email) values(v_first,v_last,v_email) returning id into v_guest_customer;
    end if;
    insert into public.registrations(id,customer_id,class_session_id,status,registration_source,optional_survey)
      values(v_ids[v_i+1],v_guest_customer,v_session.id,v_status,v_prefix||':guest:'||p_request_id::text,
        jsonb_build_object('hostRegistrationId',v_primary,'holdExpiresAt',v_survey->'holdExpiresAt'));
  end loop;
  if v_paid then
    insert into public.registration_orders(registration_id,status,currency,course_amount,materials_amount,total_amount)
      values(v_primary,'payment_pending','usd',25*v_count,20*v_ebooks,25*v_count+20*v_ebooks)
      on conflict(registration_id) do update set status='payment_pending',course_amount=excluded.course_amount,
        materials_amount=excluded.materials_amount,total_amount=excluded.total_amount,currency='usd',
        stripe_checkout_session_id=null,stripe_payment_intent_id=null,paid_at=null,updated_at=now()
      returning id into v_order;
    delete from public.registration_order_items where order_id=v_order;
    insert into public.registration_order_items(order_id,item_type,description,quantity,unit_amount,fulfillment_status)
      values(v_order,'course','AHA BLS Provider - February 15 community event',v_count,25,'not_required');
    if v_ebooks > 0 then
      insert into public.registration_order_items(order_id,item_type,product_id,description,quantity,unit_amount,fulfillment_status)
        values(v_order,'material',v_product,'2025 AHA BLS Provider eManual',v_ebooks,20,'awaiting_payment');
    end if;
  end if;
  return jsonb_build_object('ok',true,'registrationId',v_primary,'groupRegistrationIds',to_jsonb(v_ids));
end;
$function$;

update public.class_sessions set public_notes=replace(public_notes,'eBook optional $18.51','eBook optional $20') where external_class_id='nseaswim-pool-bls-2027-02-15' and public_notes like '%eBook optional $18.51%';

