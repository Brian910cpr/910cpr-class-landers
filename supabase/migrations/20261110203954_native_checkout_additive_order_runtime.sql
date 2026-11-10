-- Additive native mutation namespace. Existing legacy creator/finalizer overloads are not replaced.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
create table if not exists public.landerware_bls_bundle_policy(
 id boolean primary key default true check(id),enabled boolean not null default false,
 verified boolean not null default false,course_id text not null default '509474' check(course_id='509474'),
 skills_cents integer not null default 5500 check(skills_cents=5500),
 code_cents integer not null default 4000 check(code_cents=4000),
 total_cents integer not null default 9500 check(total_cents=9500 and total_cents=skills_cents+code_cents),
 product_key text not null default 'aha-25-3553-heartcode-bls-online' check(product_key='aha-25-3553-heartcode-bls-online'),verification_evidence text,
 check(not verified or nullif(trim(verification_evidence),'') is not null)
);
alter table public.landerware_bls_bundle_policy enable row level security;
revoke all on public.landerware_bls_bundle_policy from public,anon,authenticated;
grant all on public.landerware_bls_bundle_policy to service_role;
insert into public.landerware_bls_bundle_policy(id) values(true) on conflict(id) do nothing;
-- Reconciled atomic public-order implementation. Public inventory remains gated.
alter table public.landerware_public_order_students
 add column if not exists billing_code text,
 add column if not exists discount integer not null default 0 check(discount>=0),
 add column if not exists selected_options jsonb not null default '{}'::jsonb;


-- Existing public order/operational registration model; no new registration tables.
alter table public.landerware_public_orders
  add column if not exists request_fingerprint text,
  add column if not exists payment_evidence jsonb not null default '{}'::jsonb,
  add column if not exists reconciliation_error text;

-- Durable provider receipt protects a paid unit even if roster/outbox finalization rolls back.
alter table public.product_inventory_units add column if not exists public_order_payment_observed boolean not null default false;

-- Bind canonical units to the existing per-student order, never copy codes into
-- public responses or snapshots. Paid/manual-fulfillment reservations persist.
alter table public.product_inventory_units
 add column if not exists public_order_student_id uuid references public.landerware_public_order_students(id),
 add column if not exists public_order_hold_expires_at timestamptz;
create index if not exists product_inventory_public_order_student on public.product_inventory_units(public_order_student_id) where public_order_student_id is not null;

-- Resolve add-ons through the existing product catalog. A legacy option label,
-- migrated SKU or a positive display price is not fulfillment authorization.
-- Digital-code sales are backed by atomic canonical-unit reservations below.
-- Physical items and composite bundles remain closed pending their own contract.
create or replace function public.landerware_public_addon_state(p_addon jsonb,p_currency text)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare p public.products;
begin
 if coalesce((p_addon->>'active')::boolean,true)=false then return jsonb_build_object('available',false,'reason','inactive'); end if;
 if jsonb_typeof(p_addon->'unit_amount') is distinct from 'number' or
    (p_addon->>'unit_amount')::numeric<=0 or trunc((p_addon->>'unit_amount')::numeric)<>(p_addon->>'unit_amount')::numeric
 then return jsonb_build_object('available',false,'reason','invalid_addon_price'); end if;
 select * into p from public.products where product_key=nullif(p_addon->>'product_key','') and active;
 if p.id is null then return jsonb_build_object('available',false,'reason','product_mapping_required'); end if;
 if p_currency is distinct from 'usd' or p.customer_price is null or p.customer_price*100<>(p_addon->>'unit_amount')::numeric
 then return jsonb_build_object('available',false,'reason','product_price_mismatch'); end if;
 if p.fulfillment_mode='digital_code' then
   -- A composite bundle requires explicit component reservation; do not infer
   -- that one code fulfills every component from the display description.
   if jsonb_typeof(p_addon->'component_skus')='array' and jsonb_array_length(p_addon->'component_skus')>1
   then return jsonb_build_object('available',false,'reason','component_mapping_required'); end if;
   return jsonb_build_object('available',exists(select 1 from public.product_inventory_units u
      left join public.landerware_public_order_students os on os.id=u.public_order_student_id
      left join public.landerware_public_orders oo on oo.id=os.order_id
      where u.product_id=p.id and not u.public_order_payment_observed and u.reserved_for_registration_id is null and u.exposed_at is null and u.fulfilled_at is null
       and ((u.status='available' and u.public_order_student_id is null) or
        (u.status='reserved' and os.registration_id is null and oo.status<>'paid'
         and oo.payment_evidence->>'payment_status' is distinct from 'paid'
         and (oo.hold_expires_at<=now() or oo.status in ('expired','cancelled'))))),
      'reason','stock_required','product_id',p.id,'product_key',p.product_key,'fulfillment_mode',p.fulfillment_mode,'inventory_required',true);
 end if;
 if p.product_type is distinct from 'service' or p.fulfillment_mode is distinct from 'manual'
    or coalesce((p_addon->>'includes_online_program')::boolean,false)
 then return jsonb_build_object('available',false,'reason','inventory_reservation_required'); end if;
 return jsonb_build_object('available',true,'product_id',p.id,'product_key',p.product_key,'fulfillment_mode',p.fulfillment_mode,'inventory_required',false);
end $$;

-- Only an unpaid, unexposed, unfulfilled, unregistered checkout hold can be
-- reclaimed. Never reclaim another workflow's reservation or a paid booking.
create or replace function public.landerware_release_expired_public_inventory(p_product_id uuid)
returns void language sql security invoker set search_path='' as $$
 update public.product_inventory_units u set status='available',public_order_student_id=null,
  public_order_hold_expires_at=null,reserved_at=null,updated_at=now()
 from public.landerware_public_order_students st,public.landerware_public_orders o
 where u.product_id=p_product_id and not u.public_order_payment_observed and u.public_order_student_id=st.id and st.order_id=o.id
  and st.registration_id is null and o.status<>'paid' and o.payment_evidence->>'payment_status' is distinct from 'paid'
  and (o.hold_expires_at<=now() or o.status in ('expired','cancelled'))
  and u.status='reserved' and u.reserved_for_registration_id is null
  and u.exposed_at is null and u.fulfilled_at is null;
$$;

create or replace function public.landerware_reserve_public_addons(p_student_id uuid)
returns void language plpgsql security invoker set search_path='' as $$
declare st public.landerware_public_order_students; o public.landerware_public_orders; a jsonb; unit_id uuid;
begin
 select * into st from public.landerware_public_order_students where id=p_student_id;
 -- Canonical creation already owns this order. Also serialize an accidental
 -- direct service call before testing whether a unit has already been reserved.
 select * into o from public.landerware_public_orders where id=st.order_id for update;
 select * into st from public.landerware_public_order_students where id=p_student_id for update;
 if st.id is null or o.id is null then raise exception 'order_not_found'; end if;
 if o.status not in ('held','checkout_open') or o.hold_expires_at<=now() then raise exception 'hold_expired'; end if;
 if exists(select value->>'product_id' from jsonb_array_elements(st.selected_addons) where value->>'inventory_required'='true' group by value->>'product_id' having count(*)>1) then raise exception 'duplicate_product_addon'; end if;
 for a in select value from jsonb_array_elements(st.selected_addons) where value->>'inventory_required'='true' order by value->>'product_id',value->>'key' loop
  select id into unit_id from public.product_inventory_units where public_order_student_id=st.id and product_id=(a->>'product_id')::uuid and status='reserved';
  if unit_id is not null then continue; end if;
  perform public.landerware_release_expired_public_inventory((a->>'product_id')::uuid);
  select id into unit_id from public.product_inventory_units where product_id=(a->>'product_id')::uuid
   and status='available' and not public_order_payment_observed and public_order_student_id is null and reserved_for_registration_id is null
   and exposed_at is null and fulfilled_at is null order by id for update skip locked limit 1;
  if unit_id is null then raise exception 'addon_inventory_exhausted'; end if;
  update public.product_inventory_units set status='reserved',public_order_student_id=st.id,
   public_order_hold_expires_at=o.hold_expires_at,reserved_at=now(),updated_at=now() where id=unit_id;
 end loop;
end $$;

create or replace function public.landerware_public_seat_state(p_session_id uuid)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare s public.class_sessions; v_registered integer; v_holds integer; v_external integer:=0; v_native integer;
  proof jsonb; observed timestamptz; v_capacity integer;
begin
  select * into s from public.class_sessions where id=p_session_id;
  if s.id is null then raise exception 'session_not_open'; end if;
  -- Honor a stricter existing published inventory limit as well as the canonical
  -- physical class limit. Never increase an established seat limit at checkout.
  select least(s.max_students,coalesce((select i.capacity from public.landerware_public_session_inventory i where i.external_class_id=s.external_class_id),s.max_students)) into v_capacity;
  if v_capacity is null or v_capacity<1 then raise exception 'unverified_capacity'; end if;
  select count(*) into v_registered from public.registrations where class_session_id=s.id and status in ('registered','confirmed','completed','active');
  -- Only genuinely native sessions are independent of external roster evidence.
  if s.registration_backend='enrollware' or s.external_class_id ~ '^\d+$'
    or exists(select 1 from public.registrations r where r.class_session_id=s.id
      and r.status in ('registered','confirmed','completed','active')
      and (r.external_registration_id is not null or r.registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation'))) then
    proof:=coalesce(s.external_reconciliation,'{}'::jsonb);
    observed:=nullif(proof->>'source_observed_at','')::timestamptz;
    if coalesce((proof->>'complete')::boolean,false) is not true or observed is null or observed<now()-interval '1 hour' or observed>now()+interval '5 minutes'
      or jsonb_typeof(proof->'active_external_registration_ids') is distinct from 'array' then raise exception 'external_reconciliation_required'; end if;
    v_external:=jsonb_array_length(proof->'active_external_registration_ids');
    if v_external is distinct from (proof->>'active_registration_count')::integer
      or v_external<>(select count(distinct value) from jsonb_array_elements_text(proof->'active_external_registration_ids')) then raise exception 'external_reconciliation_required'; end if;
    -- Every external seat must be reconciled to the operational roster exactly once.
    if v_external<>(select count(*) from public.registrations r where r.class_session_id=s.id and r.status in ('registered','confirmed','completed','active') and proof->'active_external_registration_ids' ? r.external_registration_id)
      or exists(select 1 from public.registrations r where r.class_session_id=s.id and r.status in ('registered','confirmed','completed','active')
        and (r.external_registration_id is not null or r.registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation'))
        and not coalesce(proof->'active_external_registration_ids' ? r.external_registration_id,false)) then raise exception 'external_reconciliation_required'; end if;
  end if;
  v_native:=v_registered-v_external;
  select count(*) into v_holds from public.landerware_public_order_students st join public.landerware_public_orders o on o.id=st.order_id
    where o.class_session_id=s.id and o.status in ('held','checkout_open') and (o.hold_expires_at>now() or (o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true'));
  return jsonb_build_object('capacity',v_capacity,'registered',v_registered,'externallyRegistered',v_external,'nativeRegistered',v_native,'holds',v_holds,'remaining',greatest(v_capacity-v_registered-v_holds,0));
end $$;

create or replace function public.native_checkout_create_order(
 p_idempotency_key text,p_external_class_id text,p_course_id text,p_payer_email text,p_payer_phone text,p_students jsonb,p_billing_code text default null,p_offer jsonb default '{}'::jsonb
) returns jsonb language plpgsql security invoker set search_path='' as $$
declare o public.landerware_public_orders; s public.class_sessions; c public.landerware_registration_catalog;
 st jsonb; a jsonb; ac jsonb; bc jsonb; v_code text; v_amount integer; v_discount integer; v_subtotal integer:=0; v_discounts integer:=0;
 v_requested integer; v_fingerprint text; seats jsonb; v_course text; v_addons jsonb; v_student_id uuid;
begin
 -- Preserve the installed owner-closure contract before any hold or order write.
 perform public.assert_public_registration_open(null,null,p_external_class_id);
 if nullif(trim(p_idempotency_key),'') is null or jsonb_typeof(p_students) is distinct from 'array' then raise exception 'invalid_order'; end if;
 v_requested:=jsonb_array_length(p_students);
 if v_requested<1 or v_requested>10 or nullif(trim(p_payer_email),'') is null then raise exception 'invalid_order'; end if;
 if (select count(distinct lower(trim(value->>'email'))) from jsonb_array_elements(p_students))<>v_requested then raise exception 'duplicate_student'; end if;
 v_fingerprint:=md5(jsonb_build_object('session',p_external_class_id,'course',p_course_id,'payer',lower(trim(p_payer_email)),'phone',p_payer_phone,'students',p_students,'code',p_billing_code)::text);
 perform pg_advisory_xact_lock(hashtextextended('public-order-key|'||trim(p_idempotency_key),0));
 select * into o from public.landerware_public_orders where idempotency_key=trim(p_idempotency_key) for update;
 if o.id is not null then
   if o.request_fingerprint is distinct from v_fingerprint then raise exception 'idempotency_conflict'; end if;
   return jsonb_build_object('orderId',o.id,'status',o.status,'holdExpiresAt',o.hold_expires_at,'total',o.total,'idempotentReplay',true);
 end if;
 select * into s from public.class_sessions where external_class_id=trim(p_external_class_id) and record_scope='operational' order by updated_at desc limit 1 for update;
 if s.id is null or s.status not in ('scheduled','active') or s.visibility<>'public' or s.registration_status<>'open' or s.start_at<=now() or s.lead_instructor_id is null or s.end_at is null or s.end_at<=s.start_at then raise exception 'session_not_open'; end if;
 -- No implicit materialization or conversion of an Enrollware class at checkout.
 select enrollware_course_id into v_course from public.courses where id=s.course_id;
 if v_course is distinct from trim(p_course_id) then raise exception 'course_session_mismatch'; end if;
 if coalesce(p_offer->>'profile_fields_validated','false')<>'true' and exists(select 1 from public.courses x where x.id=s.course_id and nullif(to_jsonb(x)->>'registration_profile_key','') is not null) then raise exception 'generic_checkout_required'; end if;
 select * into c from public.landerware_registration_catalog where course_id=trim(p_course_id) and active;
 if c.course_id is null then raise exception 'price_catalog_missing'; end if;
 if c.unit_amount is null or c.unit_amount<=0 then raise exception 'price_catalog_missing'; end if;
 seats:=public.landerware_public_seat_state(s.id);
 if (seats->>'remaining')::integer<v_requested then raise exception 'insufficient_seats'; end if;
 for st in select value from jsonb_array_elements(p_students) loop
   if nullif(trim(st->>'firstName'),'') is null or nullif(trim(st->>'lastName'),'') is null or coalesce(st->>'email','') !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' or (nullif(trim(st->>'phone'),'') is null and coalesce(p_offer->>'profile_fields_validated','false')<>'true') then raise exception 'required_registration_field_missing'; end if;
   if st->>'manualChoice'='physical' or st->>'firstAidManualChoice'='physical' then raise exception 'physical_manual_unavailable'; end if;
   if jsonb_typeof(coalesce(st->'addons','[]'::jsonb)) is distinct from 'array' then raise exception 'invalid_addon'; end if;
   if exists(select 1 from jsonb_array_elements(coalesce(st->'addons','[]'::jsonb)) choice(value)
       where jsonb_typeof(choice.value) is distinct from 'object' or nullif(trim(choice.value->>'key'),'') is null) then raise exception 'invalid_addon'; end if;
   if (select count(distinct choice.value->>'key') from jsonb_array_elements(coalesce(st->'addons','[]'::jsonb)) choice(value))
       <>jsonb_array_length(coalesce(st->'addons','[]'::jsonb)) then raise exception 'duplicate_addon'; end if;
   -- Source registration options are per-student choices, never bulk quantities.
   if exists(select 1 from jsonb_array_elements(coalesce(st->'addons','[]'::jsonb)) choice(value)
       where choice.value ? 'quantity' and (jsonb_typeof(choice.value->'quantity') is distinct from 'number'
         or choice.value->'quantity'<>'1'::jsonb)) then raise exception 'invalid_addon_quantity'; end if;
   if c.course_id in ('209806','359474') then
     if coalesce(st->>'manualChoice','own-copy') not in ('own-copy','ebook')
       or (coalesce(st->>'manualChoice','own-copy')='ebook') is distinct from
          exists(select 1 from jsonb_array_elements(coalesce(st->'addons','[]')) option_choice(value) where option_choice.value->>'key'='aha_bls_provider_manual_ebook')
       then raise exception 'invalid_course_option'; end if;
   end if;
   if c.course_id='210549' then
     if coalesce(st->>'learningPath','') not in ('skills-only','online-and-skills')
       or (st->>'learningPath'='online-and-skills') is distinct from
          exists(select 1 from jsonb_array_elements(coalesce(st->'addons','[]')) option_choice(value) where option_choice.value->>'key'='aha_heartcode_bls_online')
       then raise exception 'invalid_course_option'; end if;
     if st->'onlineCompletionAcknowledged' is distinct from 'true'::jsonb then raise exception 'online_completion_ack_required'; end if;
   end if;
   if c.course_id='509474' then
     if c.unit_amount<>5500 or not exists(select 1 from public.skills_session_context_config cfg where cfg.context_key=st->>'skillsContext' and cfg.course_id=s.course_id and cfg.enabled and cfg.capacity_policy_verified) then raise exception 'invalid_course_option'; end if;
     if st->>'learningPath'='skills-only' then
       if st->'onlineCompleted' is distinct from 'true'::jsonb or exists(select 1 from jsonb_array_elements(coalesce(st->'addons','[]')) x where x->>'key'='aha_heartcode_bls_online') then raise exception 'online_completion_ack_required'; end if;
     elsif st->>'learningPath'='online-and-skills' then
       if st->>'skillsContext' is distinct from 'bls-skills' or st->'onlineCompletionAcknowledged' is distinct from 'true'::jsonb
        or not exists(select 1 from public.landerware_bls_bundle_policy where enabled and verified)
        or not exists(select 1 from jsonb_array_elements(coalesce(st->'addons','[]')) x where x->>'key'='aha_heartcode_bls_online') then raise exception 'invalid_course_option'; end if;
     else raise exception 'invalid_course_option'; end if;
   end if;
   if c.course_id in ('209806','359474','210549') then
     if coalesce(st->>'firstAidChoice','none') not in ('none','in-person','online')
       or (coalesce(st->>'firstAidChoice','none')='in-person') is distinct from
          exists(select 1 from jsonb_array_elements(coalesce(st->'addons','[]')) option_choice(value) where option_choice.value->>'key'='aha_heartsaver_first_aid_in_person')
       or (coalesce(st->>'firstAidChoice','none')='online') is distinct from
          exists(select 1 from jsonb_array_elements(coalesce(st->'addons','[]')) option_choice(value) where option_choice.value->>'key'='aha_heartsaver_first_aid_online')
       then raise exception 'invalid_course_option'; end if;
     if coalesce(st->>'firstAidChoice','none')='in-person' and coalesce(st->>'firstAidManualChoice','own-copy') not in ('own-copy','ebook') then raise exception 'invalid_course_option'; end if;
     if (coalesce(st->>'firstAidChoice','none')='in-person' and coalesce(st->>'firstAidManualChoice','own-copy')='ebook') is distinct from
        exists(select 1 from jsonb_array_elements(coalesce(st->'addons','[]')) option_choice(value) where option_choice.value->>'key'='aha_heartsaver_first_aid_manual_ebook')
       then raise exception 'invalid_course_option'; end if;
   end if;
   if exists(select 1 from public.registrations r join public.customers p on p.id=r.customer_id where r.class_session_id=s.id and lower(trim(p.email))=lower(trim(st->>'email')) and r.status in ('registered','confirmed','completed','active')) then raise exception 'already_registered'; end if;
   if exists(select 1 from public.landerware_public_order_students os join public.landerware_public_orders oo on oo.id=os.order_id where oo.class_session_id=s.id and oo.status in ('held','checkout_open') and (oo.hold_expires_at>now() or (oo.payment_evidence->>'payment_status'='paid' and oo.payment_evidence->>'seat_hold_protected'='true')) and os.email=lower(trim(st->>'email'))) then raise exception 'student_already_held'; end if;
 end loop;
 insert into public.landerware_public_orders(idempotency_key,request_fingerprint,external_class_id,class_session_id,course_id,payer_email,payer_phone,billing_code,currency,hold_expires_at)
 values(trim(p_idempotency_key),v_fingerprint,trim(p_external_class_id),s.id,c.course_id,lower(trim(p_payer_email)),trim(p_payer_phone),nullif(trim(p_billing_code),''),c.currency,now()+interval '30 minutes') returning * into o;
 for st in select value from jsonb_array_elements(p_students) loop
   v_amount:=c.unit_amount; v_discount:=0; v_addons:='[]'::jsonb;
   for a in select value from jsonb_array_elements(coalesce(st->'addons','[]')) loop
     select value into ac from jsonb_array_elements(c.addons) where value->>'key'=a->>'key' and coalesce((value->>'active')::boolean,true);
     if ac is null or coalesce((a->>'quantity')::integer,1) not between 1 and 10 then raise exception 'invalid_addon'; end if;
     if jsonb_typeof(ac->'unit_amount') is distinct from 'number' then raise exception 'invalid_addon_price'; end if;
     if (ac->>'unit_amount')::numeric<=0 or trunc((ac->>'unit_amount')::numeric)<>(ac->>'unit_amount')::numeric then raise exception 'invalid_addon_price'; end if;
     -- Lock the canonical product for this transaction so a concurrent catalog
     -- edit cannot change the mapping/price between validation and snapshot.
     perform 1 from public.products where product_key=ac->>'product_key' for share;
     perform public.landerware_release_expired_public_inventory(id) from public.products where product_key=ac->>'product_key';
     if not coalesce((public.landerware_public_addon_state(ac,c.currency)->>'available')::boolean,false) then raise exception 'addon_fulfillment_unavailable'; end if;
     v_amount:=v_amount+(ac->>'unit_amount')::integer*coalesce((a->>'quantity')::integer,1);
     v_addons:=v_addons||jsonb_build_array(jsonb_strip_nulls(jsonb_build_object(
       'key',ac->>'key','quantity',1,'unit_amount',(ac->>'unit_amount')::integer,
       'display_name',coalesce(ac->>'display_name',ac->>'key'),'product_key',ac->>'product_key',
       'product_id',public.landerware_public_addon_state(ac,c.currency)->>'product_id',
       'inventory_required',public.landerware_public_addon_state(ac,c.currency)->'inventory_required',
       'manufacturer_sku',ac->>'manufacturer_sku',
       'component_skus',ac->'component_skus',
       'includes_online_program',ac->'includes_online_program','includes_student_ebook',ac->'includes_student_ebook',
       'includes_skills_testing',ac->'includes_skills_testing',
       'fulfillment_mode',public.landerware_public_addon_state(ac,c.currency)->>'fulfillment_mode')));
   end loop;
   v_code:=coalesce(nullif(trim(st->>'billingCode'),''),nullif(trim(p_billing_code),''));
   if v_code is not null then
     select value into bc from jsonb_array_elements(c.billing_codes) where lower(value->>'code')=lower(v_code) and coalesce((value->>'active')::boolean,true);
     -- Approved invoice authorization needs a separate payer procedure; never label it paid.
     if bc is null or coalesce(bc->>'payer_mode','')='corporate_invoice' or coalesce(bc->>'type','') not in ('percent','amount') then raise exception 'billing_approval_required'; end if;
     v_discount:=case when bc->>'type'='percent' then round(v_amount*(bc->>'amount')::numeric/100)::integer else (bc->>'amount')::integer end;
     if v_discount<0 or v_discount>v_amount then raise exception 'invalid_billing_code'; end if;
   end if;
   insert into public.landerware_public_order_students(order_id,first_name,last_name,email,phone,unit_amount,selected_addons,billing_code,discount,selected_options)
   values(o.id,trim(st->>'firstName'),trim(st->>'lastName'),lower(trim(st->>'email')),coalesce(trim(st->>'phone'),''),v_amount,v_addons,v_code,v_discount,jsonb_build_object('manualChoice',coalesce(st->>'manualChoice','own-copy'),'firstAidChoice',coalesce(st->>'firstAidChoice','none'),'learningPath',st->>'learningPath','firstAidManualChoice',st->>'firstAidManualChoice','onlineCompletionAcknowledged',st->'onlineCompletionAcknowledged','skillsContext',st->>'skillsContext','selectorSelectionId',st->>'selectorSelectionId')) returning id into v_student_id;
   perform public.landerware_reserve_public_addons(v_student_id);
   v_subtotal:=v_subtotal+v_amount; v_discounts:=v_discounts+v_discount;
 end loop;
 if v_subtotal-v_discounts<=0 then raise exception 'billing_approval_required'; end if;
 update public.landerware_public_orders set subtotal=v_subtotal,discount=v_discounts,total=v_subtotal-v_discounts,updated_at=now() where id=o.id;
 return jsonb_build_object('orderId',o.id,'status','held','holdExpiresAt',o.hold_expires_at,'total',v_subtotal-v_discounts,'idempotentReplay',false);
end $$;

-- Retire the old overload as a bypass, preserving its calling contract.


-- Called in its own transaction by verified webhook/API recovery BEFORE the
-- atomic finalizer. A transient roster/outbox failure must not erase payment.
create or replace function public.native_checkout_record_payment(p_order_id uuid,p_stripe_payment_intent_id text,p_evidence jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare o public.landerware_public_orders; s public.class_sessions; protect boolean;
begin
 select * into o from public.landerware_public_orders where id=p_order_id;
 if o.id is null then raise exception 'order_not_found'; end if;
 select * into s from public.class_sessions where id=o.class_session_id for update;
 select * into o from public.landerware_public_orders where id=p_order_id for update;
 if p_evidence->>'payment_status' is distinct from 'paid' or p_evidence->>'mode' is distinct from 'payment'
  or p_evidence->>'id' is distinct from o.stripe_checkout_session_id or o.stripe_checkout_session_id is null
  or p_evidence->'metadata'->>'landerware_order_id' is distinct from o.id::text
  or (p_evidence->>'amount_total')::integer is distinct from o.total or p_evidence->>'currency' is distinct from o.currency
  or nullif(p_stripe_payment_intent_id,'') is null or p_stripe_payment_intent_id not like 'pi_%'
  or (o.stripe_payment_intent_id is not null and o.stripe_payment_intent_id is distinct from p_stripe_payment_intent_id)
 then raise exception 'payment_evidence_mismatch'; end if;
 if o.status='refunded' then return jsonb_build_object('recorded',false,'status','refunded','idempotentReplay',true); end if;
 if o.payment_evidence->>'payment_status'='paid' then return jsonb_build_object('recorded',true,'idempotentReplay',true); end if;
 protect:=o.status in ('held','checkout_open') and o.hold_expires_at>now() and s.status in ('scheduled','active') and s.registration_status='open' and s.start_at>now();
 update public.product_inventory_units u set public_order_payment_observed=true,updated_at=now()
 from public.landerware_public_order_students st where st.order_id=o.id and u.public_order_student_id=st.id and u.status='reserved';
 update public.landerware_public_orders set payment_evidence=p_evidence||jsonb_build_object('seat_hold_protected',coalesce(protect,false)),
 stripe_payment_intent_id=p_stripe_payment_intent_id,updated_at=now() where id=o.id;
 return jsonb_build_object('recorded',true,'idempotentReplay',false);
end $$;

create or replace function public.native_checkout_finalize_order(p_order_id uuid,p_stripe_payment_intent_id text,p_evidence jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare o public.landerware_public_orders; s public.class_sessions; st public.landerware_public_order_students; person public.customers;
 reg public.registrations; seats jsonb; v_needed integer; v_own_hold integer:=0; v_result jsonb; v_name text; v_location text; v_error text;
begin
 -- Same session row lock as seat allocation. Avoid order/session lock inversion.
 select * into o from public.landerware_public_orders where id=p_order_id;
 if o.id is null then raise exception 'order_not_found'; end if;
 select * into s from public.class_sessions where id=o.class_session_id for update;
 select * into o from public.landerware_public_orders where id=p_order_id for update;
 if p_evidence->>'payment_status' is distinct from 'paid' or p_evidence->>'mode' is distinct from 'payment'
   or p_evidence->>'id' is distinct from o.stripe_checkout_session_id or o.stripe_checkout_session_id is null
   or p_evidence->'metadata'->>'landerware_order_id' is distinct from o.id::text
   or (p_evidence->>'amount_total')::integer is distinct from o.total or p_evidence->>'currency' is distinct from o.currency
   or nullif(p_stripe_payment_intent_id,'') is null or p_stripe_payment_intent_id not like 'pi_%'
   or (o.stripe_payment_intent_id is not null and o.stripe_payment_intent_id is distinct from p_stripe_payment_intent_id) then raise exception 'payment_evidence_mismatch'; end if;
 if o.status='refunded' then return jsonb_build_object('orderId',o.id,'status','refunded','idempotentReplay',true); end if;
 if o.status='paid' then return jsonb_build_object('orderId',o.id,'status','paid','idempotentReplay',true); end if;
 if o.status='cancelled' then v_error:='order_cancelled'; end if;
 select count(*) into v_needed from public.landerware_public_order_students where order_id=o.id;
 if s.id is null or s.status not in ('scheduled','active') or s.registration_status<>'open' or s.start_at<=now() then v_error:='session_not_open';
 else
   begin seats:=public.landerware_public_seat_state(s.id); exception when others then v_error:='external_reconciliation_required'; end;
 end if;
 if o.status in ('held','checkout_open') and (o.hold_expires_at>now() or (o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true')) then v_own_hold:=v_needed; end if;
 if v_error is null and (seats->>'remaining')::integer+v_own_hold<v_needed then v_error:='paid_seat_unavailable'; end if;
 -- Late paid events may recover expired holds only after a fresh seat check.
 if v_error is null and exists(select 1 from public.landerware_public_order_students os join public.customers p on lower(trim(p.email))=os.email join public.registrations r on r.customer_id=p.id and r.class_session_id=s.id where os.order_id=o.id and r.status in ('registered','confirmed','completed','active')) then v_error:='duplicate_paid_registration'; end if;
 if v_error is null and exists(select 1 from public.landerware_public_order_students os join public.customers p on lower(trim(p.email))=os.email where os.order_id=o.id and (lower(trim(p.first_name))<>lower(os.first_name) or lower(trim(p.last_name))<>lower(os.last_name))) then v_error:='identity_review_required'; end if;
 if v_error is null then
   perform 1 from public.product_inventory_units u join public.landerware_public_order_students os on os.id=u.public_order_student_id where os.order_id=o.id order by u.id for update of u;
   if exists(select 1 from public.landerware_public_order_students os cross join lateral jsonb_array_elements(os.selected_addons) a
     where os.order_id=o.id and a->>'inventory_required'='true' and not exists(
      select 1 from public.product_inventory_units u where u.public_order_student_id=os.id
       and u.product_id=(a->>'product_id')::uuid and u.status='reserved'
       and u.reserved_for_registration_id is null and u.exposed_at is null and u.fulfilled_at is null))
   then v_error:='paid_inventory_unavailable'; end if;
 end if;
 if v_error is not null then
   update public.landerware_public_orders set status=case when status in ('held','checkout_open') then 'expired' else status end,payment_evidence=p_evidence,reconciliation_error=v_error,updated_at=now() where id=o.id;
   return jsonb_build_object('orderId',o.id,'status','payment_review','reason',v_error);
 end if;
 select name into v_name from public.courses where id=s.course_id;
 select concat_ws(E'\n',name,nullif(concat_ws(', ',nullif(address_line1,''),nullif(address_line2,''),nullif(city,''),nullif(state,''),nullif(postal_code,'')),'')) into v_location from public.locations where id=s.location_id;
 -- Deterministic identity lock ordering also protects concurrent different classes.
 for st in select * from public.landerware_public_order_students where order_id=o.id order by email loop
   perform pg_advisory_xact_lock(hashtextextended('public-person|'||st.email,0));
   select * into person from public.customers where lower(trim(email))=st.email order by updated_at desc,id limit 1 for update;
   if person.id is null then
     insert into public.customers(first_name,last_name,email,phone) values(st.first_name,st.last_name,st.email,st.phone) returning * into person;
   elsif lower(trim(person.first_name))<>lower(st.first_name) or lower(trim(person.last_name))<>lower(st.last_name) then
     raise exception 'identity_review_required';
   end if;
   insert into public.registrations(customer_id,class_session_id,status,registration_source,optional_survey)
   values(person.id,s.id,'registered','landerware_native_checkout',jsonb_build_object('publicOrderId',o.id,'stripePaymentIntentId',p_stripe_payment_intent_id,'learningPath',st.selected_options->>'learningPath','skillsContext',st.selected_options->>'skillsContext','certificateDocumentId',st.selected_options->>'certificateDocumentId')) returning * into reg;
   update public.landerware_public_order_students set registration_id=reg.id where id=st.id;
   if to_regclass('public.native_checkout_upload_intents') is not null then
     update public.registrations set native_checkout_profile_snapshot=o.registration_profile_snapshot||jsonb_build_object('inputs',jsonb_build_array(coalesce(o.registration_profile_snapshot->'inputs'->coalesce((st.selected_options->>'clientIndex')::integer,0),'{}'::jsonb))) where id=reg.id;
     perform public.native_checkout_record_received(reg.id,i.id) from public.native_checkout_upload_intents i where i.public_order_student_id=st.id and i.state='received';
   end if;
   update public.product_inventory_units set reserved_for_registration_id=reg.id,public_order_hold_expires_at=null,updated_at=now() where public_order_student_id=st.id and status='reserved';
   -- Message registration_id references the older canonical model: use durable order key,
   -- not an invalid cross-model FK. Operational registration provenance is in body/key.
   insert into public.landerware_messages(template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key)
   values('retail-paid-confirmation-v3',st.email,'Registration confirmed — '||v_name,
     'Hi '||st.first_name||E',\n\nYou are registered for '||v_name||E'.\n'||to_char(s.start_at at time zone 'America/New_York','FMDay, FMMonth FMDD, YYYY')||E'\n'||to_char(s.start_at at time zone 'America/New_York','FMHH12:MI AM')||' Eastern'||E'\n'||coalesce(v_location,'Contact 910CPR to confirm your class location.')||E'\n\nPayment received. Your Stripe payment receipt is separate.\n'||
     case when o.course_id in ('209806','359474') then
       case when exists(select 1 from jsonb_array_elements(st.selected_addons) a where a->>'key'='aha_bls_provider_manual_ebook') then E'Your purchased BLS eManual will be provided separately by 910CPR.\n' else E'Have your current 2025 AHA BLS Student Manual available for class.\n' end
       else '' end||E'\nQuestions, changes or cancellation? Reply to this email or call 910-395-5193. Please include your name and class date.\n\n910CPR',
     'cloudflare','pending','public-order-paid:'||o.id||':'||st.email) on conflict(idempotency_key) do nothing;
 end loop;
 if exists(select 1 from public.landerware_public_order_students where order_id=o.id and selected_addons<>'[]'::jsonb) then
   insert into public.landerware_messages(template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key)
   values('retail-addon-fulfillment-v2','brian@910cpr.com','Paid add-ons require fulfillment — '||v_name,
     'Order '||o.id||E' is paid. Manual fulfillment required; do not auto-release codes or materials.\n'||
     (select string_agg(os.first_name||' '||os.last_name||': '||coalesce(a->>'display_name',a->>'key')||
       coalesce(' [SKU '||nullif(a->>'manufacturer_sku','')||']','')||
       case when a->>'includes_student_ebook'='true' then ' (student eBook included)' else '' end||
       case when jsonb_typeof(a->'component_skus')='array' then ' [component SKUs: '||(select string_agg(v.value,', ') from jsonb_array_elements_text(a->'component_skus') v(value))||']' else '' end,E'\n' order by os.email,a->>'key')
      from public.landerware_public_order_students os cross join lateral jsonb_array_elements(os.selected_addons) a where os.order_id=o.id),
     'cloudflare','pending','public-order-fulfillment:'||o.id) on conflict(idempotency_key) do nothing;
 end if;
 update public.landerware_public_orders set status='paid',paid_at=now(),stripe_payment_intent_id=p_stripe_payment_intent_id,payment_evidence=p_evidence,reconciliation_error=null,updated_at=now() where id=o.id;
 return jsonb_build_object('orderId',o.id,'status','paid','registrations',v_needed,'idempotentReplay',false);
end $$;

-- Old finalizer cannot turn an arbitrary service call/zero invoice into a payment.



revoke all on function public.landerware_public_addon_state(jsonb,text) from public,anon,authenticated;
grant execute on function public.landerware_public_addon_state(jsonb,text) to service_role;
revoke all on function public.landerware_release_expired_public_inventory(uuid) from public,anon,authenticated;
grant execute on function public.landerware_release_expired_public_inventory(uuid) to service_role;
revoke all on function public.landerware_reserve_public_addons(uuid) from public,anon,authenticated;
grant execute on function public.landerware_reserve_public_addons(uuid) to service_role;
revoke all on function public.landerware_public_seat_state(uuid) from public,anon,authenticated;
grant execute on function public.landerware_public_seat_state(uuid) to service_role;
revoke all on function public.native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb) from public,anon,authenticated;
grant execute on function public.native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb) to service_role;
revoke all on function public.native_checkout_record_payment(uuid,text,jsonb) from public,anon,authenticated;
grant execute on function public.native_checkout_record_payment(uuid,text,jsonb) to service_role;
revoke all on function public.native_checkout_finalize_order(uuid,text,jsonb) from public,anon,authenticated;
grant execute on function public.native_checkout_finalize_order(uuid,text,jsonb) to service_role;
commit;
