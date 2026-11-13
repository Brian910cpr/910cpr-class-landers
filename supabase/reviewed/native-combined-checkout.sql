-- Reviewed local proposal. Course activation/configuration remains disabled.
begin;
create table public.native_checkout_basket_course_policy(
 public_course_id text primary key,family text not null check(family in ('BLS','ACLS','PALS')),
 physical_course_id text not null,profile_key text not null references public.landerware_registration_profiles,
 session_cents integer not null check(session_cents>0),access_addon_key text,
 enabled boolean not null default false,verified boolean not null default false,evidence text,entry_context text not null default '',
 check(not enabled or (verified and nullif(trim(evidence),'') is not null))
);
create table public.native_checkout_basket_component_policy(
 public_course_id text not null references public.native_checkout_basket_course_policy,addon_key text not null,
 product_id uuid not null references public.products,kind text not null check(kind in ('heartcode_access','paper_book','ebook')),
 unit_cents integer not null check(unit_cents>0),verified boolean not null default false,evidence text,
 primary key(public_course_id,addon_key)
);
create table public.native_checkout_baskets(
 id uuid primary key default gen_random_uuid(),request_key uuid not null unique,request_hash text not null,
 status text not null default 'held' check(status in ('held','checkout_open','paid','payment_review','cancelled','refunded','expired')),
 currency text not null default 'usd' check(currency='usd'),subtotal integer not null default 0,discount integer not null default 0,total integer not null default 0,
 lines jsonb not null default '[]',hold_expires_at timestamptz not null default now()+interval '30 minutes',
 stripe_checkout_session_id text unique,stripe_payment_intent_id text unique,checkout_url text,payment_evidence jsonb not null default '{}',
 reconciliation_error text,created_at timestamptz not null default now(),paid_at timestamptz
);
create table public.native_checkout_basket_items(
 basket_id uuid not null references public.native_checkout_baskets,position integer not null check(position between 0 and 2),
 public_course_id text not null references public.native_checkout_basket_course_policy,
 order_id uuid not null unique references public.landerware_public_orders,
 subtotal integer not null,discount integer not null,total integer not null,
 primary key(basket_id,position),check(subtotal-discount=total and total>0)
);
alter table public.native_checkout_basket_course_policy enable row level security;
alter table public.native_checkout_basket_component_policy enable row level security;
alter table public.native_checkout_baskets enable row level security;
alter table public.native_checkout_basket_items enable row level security;
revoke all on public.native_checkout_basket_course_policy,public.native_checkout_basket_component_policy,public.native_checkout_baskets,public.native_checkout_basket_items from public,anon,authenticated;
grant select,insert,update on public.native_checkout_basket_course_policy,public.native_checkout_basket_component_policy,public.native_checkout_baskets,public.native_checkout_basket_items to service_role;

create function public.native_checkout_basket_receipt(p_key uuid) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare b public.native_checkout_baskets;
begin
 select * into b from public.native_checkout_baskets where request_key=p_key;
 if b.id is null then raise exception 'reservation_not_found'; end if;
 return jsonb_build_object('kind','course_basket','basketId',b.id,'status',b.status,'amountCents',b.total,'currency',b.currency,
  'lines',b.lines,'holdExpiresAt',b.hold_expires_at,'paymentObserved',b.payment_evidence->>'payment_status'='paid',
  'reconciliationError',b.reconciliation_error,'items',(select jsonb_agg(jsonb_build_object('position',i.position,'courseNumber',i.public_course_id,
   'orderId',i.order_id,'receipt',public.native_checkout_receipt(replace(o.idempotency_key,'public-order:',''))) order by i.position)
   from public.native_checkout_basket_items i join public.landerware_public_orders o on o.id=i.order_id where i.basket_id=b.id));
end $$;

-- Reserve all courses or none. Prices/discounts are derived from actual native
-- child orders and reviewed allocation policy, never caller-supplied amounts.
create function public.native_checkout_basket_replay(p_key uuid,p_request jsonb) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare b public.native_checkout_baskets;
begin
 select * into b from public.native_checkout_baskets where request_key=p_key;
 if b.id is null then raise exception 'reservation_not_found'; end if;
 if b.request_hash is distinct from encode(sha256(convert_to(p_request::text,'UTF8')),'hex') then raise exception 'idempotency_conflict'; end if;
 return public.native_checkout_basket_receipt(p_key);
end $$;

create function public.native_checkout_basket_choices(p_primary_course text) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare primary_family text;
begin
 select family into primary_family from public.native_checkout_basket_course_policy where public_course_id=p_primary_course and enabled and verified;
 if primary_family not in ('ACLS','PALS') or primary_family is null then return '[]'; end if;
 return (select coalesce(jsonb_agg(jsonb_build_object('courseNumber',p.public_course_id,'family',p.family,'title',c.name,'context',p.entry_context,'inventoryKind',f.form_schema->>'inventory_kind',
  'sessions',(select coalesce(jsonb_agg(jsonb_build_object('session',x.external_class_id,'startsAt',x.start_at,'endsAt',x.end_at,'location',x.source_location_label) order by x.start_at),'[]') from
   (select s.* from public.class_sessions s where f.form_schema->>'inventory_kind'='scheduled_session_v1' and s.course_id=c.id and s.status in ('scheduled','active') and s.registration_backend='landerware' and s.registration_status='open' and s.record_scope='operational' and s.visibility='public' and s.start_at>now()+interval '24 hours' and s.start_at<now()+interval '90 days' and s.consumption_start_at is not null and s.consumption_end_at is not null and s.external_class_id is not null order by s.start_at limit 100) x))), '[]')
  from public.native_checkout_basket_course_policy p join public.courses c on c.enrollware_course_id=p.physical_course_id and c.registration_profile_key=p.profile_key
  join public.landerware_registration_profiles f on f.profile_key=p.profile_key and f.course_id=c.course_key and f.active and f.registration_mode='native_public_checkout'
  where p.enabled and p.verified and p.family<>primary_family);
end $$;

create function public.reserve_native_checkout_basket(p_key uuid,p_items jsonb,p_request jsonb default null) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare b public.native_checkout_baskets; item jsonb; policy public.native_checkout_basket_course_policy;
 o public.landerware_public_orders; s public.class_sessions; prior public.class_sessions; a jsonb; st public.landerware_public_order_students;
 result jsonb; child_key text; fingerprint text; n integer:=0; base integer; reduction integer; components integer; families text[]:=array[]::text[];
 v_lines jsonb:='[]'; line jsonb; component public.native_checkout_basket_component_policy; access_count integer; expected integer; payer text; participant_hash text;
begin
 if p_key is null or jsonb_typeof(p_items) is distinct from 'array' or jsonb_array_length(p_items) not between 2 and 3 then raise exception 'invalid_course_combination'; end if;
 fingerprint:=encode(sha256(convert_to(coalesce(p_request,p_items)::text,'UTF8')),'hex');
 perform pg_advisory_xact_lock(hashtextextended('native-basket|'||p_key::text,0));
 select * into b from public.native_checkout_baskets where request_key=p_key for update;
 if b.id is not null then
  if b.request_hash is distinct from fingerprint then raise exception 'idempotency_conflict'; end if;
  return public.native_checkout_basket_receipt(p_key);
 end if;
 -- Existing claims already take this table lock for dynamic materialization.
 -- One ordering also prevents cross-course basket/ordinary-claim seat races.
 lock table public.class_sessions in share row exclusive mode;
 perform 1 from public.class_sessions cs where cs.external_class_id in (select value->>'externalId' from jsonb_array_elements(p_items)) order by cs.id for update;
 lock table public.native_checkout_basket_course_policy,public.native_checkout_basket_component_policy in share mode;
 insert into public.native_checkout_baskets(request_key,request_hash) values(p_key,fingerprint) returning * into b;
 for item in select value from jsonb_array_elements(p_items) loop
  select * into policy from public.native_checkout_basket_course_policy where public_course_id=item->>'courseNumber' and enabled and verified;
  if policy.public_course_id is null or policy.family=any(families) or policy.profile_key is distinct from item->>'profileKey' then raise exception 'unverified_course_allocation'; end if;
  families:=array_append(families,policy.family);
  if n=0 and policy.family not in ('ACLS','PALS') then raise exception 'invalid_primary_course'; end if;
  -- An addition is for the same participants, not an unrelated order joined to
  -- obtain a discount. Different per-course options remain allowed.
  if participant_hash is null then participant_hash:=md5((select jsonb_agg(jsonb_build_array(value->>'firstName',value->>'lastName',lower(trim(value->>'email'))) order by lower(trim(value->>'email'))) from jsonb_array_elements(item->'students'))::text);
  elsif participant_hash is distinct from md5((select jsonb_agg(jsonb_build_array(value->>'firstName',value->>'lastName',lower(trim(value->>'email'))) order by lower(trim(value->>'email'))) from jsonb_array_elements(item->'students'))::text) then raise exception 'basket_participants_mismatch'; end if;
  child_key:=md5(p_key::text||':'||n::text);child_key:=substr(child_key,1,8)||'-'||substr(child_key,9,4)||'-4'||substr(child_key,14,3)||'-8'||substr(child_key,18,3)||'-'||substr(child_key,21,12);
  if exists(select 1 from public.landerware_public_orders where idempotency_key='public-order:'||child_key) then raise exception 'basket_child_identity_conflict'; end if;
  if policy.family in ('ACLS','PALS') then
   result:=public.reserve_native_advanced_checkout_order(child_key,policy.profile_key,(item->>'profileVersion')::integer,coalesce(item->>'context',''),item->>'externalId',coalesce(item->'offer','{}'),item->'students',item->'inputs',(item->>'expectedTotal')::integer);
  else
   result:=public.reserve_native_checkout_order(child_key,policy.profile_key,(item->>'profileVersion')::integer,coalesce(item->>'context',''),item->>'externalId',coalesce(item->'offer','{}'),item->'students',item->'inputs',(item->>'expectedTotal')::integer);
  end if;
  select * into strict o from public.landerware_public_orders where id=(result->>'orderId')::uuid;
  if o.course_id is distinct from policy.physical_course_id or o.currency<>'usd' or o.discount<>0 or o.billing_code is not null then raise exception 'ambiguous_price_allocation'; end if;
  if payer is null then payer:=o.payer_email; elsif payer is distinct from o.payer_email then raise exception 'basket_payer_mismatch'; end if;
  select * into strict s from public.class_sessions where id=o.class_session_id;
  if s.consumption_start_at is null or s.consumption_end_at is null then raise exception 'unverified_session_interval'; end if;
  if exists(select 1 from public.native_checkout_basket_items bi join public.landerware_public_orders bo on bo.id=bi.order_id join public.class_sessions bs on bs.id=bo.class_session_id where bi.basket_id=b.id and (bs.id=s.id or (bs.consumption_start_at<s.consumption_end_at and bs.consumption_end_at>s.consumption_start_at))) then raise exception 'course_schedule_overlap'; end if;
  base:=0;components:=0;
  for st in select * from public.landerware_public_order_students where order_id=o.id loop
   access_count:=0;
   for a in select value from jsonb_array_elements(st.selected_addons) loop
    if a->>'key'=policy.access_addon_key then access_count:=access_count+1; end if;
    -- Only explicitly priced product components are pass-through charges.
    -- Service/first-aid add-ons need their own session: reject ambiguous bundles.
    select * into component from public.native_checkout_basket_component_policy where public_course_id=policy.public_course_id and addon_key=a->>'key' and verified and nullif(trim(evidence),'') is not null;
    if component.product_id is null or component.product_id::text is distinct from a->>'product_id' or component.unit_cents is distinct from (a->>'unit_amount')::integer or (a->>'quantity')::integer is distinct from 1
     or ((component.kind='heartcode_access') is distinct from coalesce(a->>'key'=policy.access_addon_key,false)) then raise exception 'unverified_component_allocation'; end if;
    line:=jsonb_build_object('courseNumber',policy.public_course_id,'kind',component.kind,'sku',a->>'product_key','quantity',1,'subtotalCents',(a->>'unit_amount')::integer,'discountCents',0,'totalCents',(a->>'unit_amount')::integer);
    v_lines:=v_lines||jsonb_build_array(line);components:=components+(a->>'unit_amount')::integer;
   end loop;
   if (policy.access_addon_key is null and access_count<>0) or (policy.access_addon_key is not null and access_count<>1) or st.discount<>0 then raise exception 'ambiguous_price_allocation'; end if;
   if st.unit_amount is distinct from policy.session_cents+(select coalesce(sum((value->>'unit_amount')::integer),0) from jsonb_array_elements(st.selected_addons)) then raise exception 'ambiguous_price_allocation'; end if;
   base:=base+policy.session_cents;
  end loop;
  if o.subtotal is distinct from base+components or o.total is distinct from base+components then raise exception 'ambiguous_price_allocation'; end if;
  reduction:=case when n=0 then 0 else floor((base::numeric*1000+5000)/10000)::integer end;
  v_lines:=v_lines||jsonb_build_array(jsonb_build_object('courseNumber',policy.public_course_id,'kind','session','primary',n=0,'quantity',(select count(*) from public.landerware_public_order_students where order_id=o.id),'subtotalCents',base,'discountCents',reduction,'totalCents',base-reduction));
  update public.landerware_public_orders set discount=reduction,total=subtotal-reduction where id=o.id;
  insert into public.native_checkout_basket_items values(b.id,n,policy.public_course_id,o.id,o.subtotal,reduction,o.subtotal-reduction);
  update public.native_checkout_baskets set subtotal=subtotal+o.subtotal,discount=discount+reduction,total=total+o.subtotal-reduction,hold_expires_at=least(hold_expires_at,o.hold_expires_at) where id=b.id;
  n:=n+1;
 end loop;
 update public.native_checkout_baskets set lines=v_lines where id=b.id;
 return public.native_checkout_basket_receipt(p_key);
end $$;

create function public.native_checkout_basket_contains_order(p_order_id uuid) returns boolean
language sql stable security invoker set search_path='' as $$select exists(select 1 from public.native_checkout_basket_items where order_id=p_order_id)$$;
create function public.native_checkout_basket_payment_valid(p_order_id uuid,p_intent text,p_evidence jsonb) returns boolean
language sql stable security invoker set search_path='' as $$
 select exists(select 1 from public.native_checkout_basket_items i join public.native_checkout_baskets b on b.id=i.basket_id join public.landerware_public_orders o on o.id=i.order_id
 where i.order_id=p_order_id and b.status in ('held','checkout_open','payment_review','paid') and b.payment_evidence->>'payment_status'='paid' and b.payment_evidence->>'id'=p_evidence->>'id' and b.payment_evidence->>'currency'=p_evidence->>'currency' and b.payment_evidence->>'amount_total'=p_evidence->>'amount_total' and jsonb_typeof(p_evidence->'livemode')='boolean' and b.payment_evidence->>'livemode'=p_evidence->>'livemode'
 and b.stripe_checkout_session_id=p_evidence->>'id' and b.stripe_payment_intent_id=p_intent and p_intent like 'pi_%'
 and p_evidence->>'mode'='payment' and p_evidence->>'payment_status'='paid' and (p_evidence->>'amount_total')::integer=b.total
 and p_evidence->>'currency'=b.currency and p_evidence->'metadata'->>'landerware_basket_id'=b.id::text and o.total=i.total and o.subtotal=i.subtotal and o.discount=i.discount
 and o.checkout_runtime_version='native-v1');
$$;

-- Reuse the installed finalizer's complete canonical roster/inventory/outbox
-- logic. Only its payment admission changes to the verified aggregate ledger.
-- Fail atomically if the established guard is absent or appears twice.
do $clone$ declare definition text; guard text; count_guard integer;
begin
 definition:=replace(pg_get_functiondef('public.native_checkout_finalize_order(uuid,text,jsonb)'::regprocedure),E'\r\n',E'\n');
 guard:=$guard$ if p_evidence->>'payment_status' is distinct from 'paid' or p_evidence->>'mode' is distinct from 'payment'
   or p_evidence->>'id' is distinct from o.stripe_checkout_session_id or o.stripe_checkout_session_id is null
   or p_evidence->'metadata'->>'landerware_order_id' is distinct from o.id::text
   or (p_evidence->>'amount_total')::integer is distinct from o.total or p_evidence->>'currency' is distinct from o.currency
   or nullif(p_stripe_payment_intent_id,'') is null or p_stripe_payment_intent_id not like 'pi_%'
   or (o.stripe_payment_intent_id is not null and o.stripe_payment_intent_id is distinct from p_stripe_payment_intent_id) then raise exception 'payment_evidence_mismatch'; end if;$guard$;
 count_guard:=(length(definition)-length(replace(definition,guard,'')))/length(guard);
 if count_guard<>1 then raise exception 'basket_finalizer_source_drift'; end if;
 definition:=replace(definition,'public.native_checkout_finalize_order(', 'public.native_checkout_finalize_basket_child(');
 definition:=replace(definition,guard,$new$ if not public.native_checkout_basket_payment_valid(o.id,p_stripe_payment_intent_id,p_evidence) then raise exception 'payment_evidence_mismatch'; end if;$new$);
 execute definition;
end $clone$;

create function public.native_checkout_basket_record_payment(p_basket_id uuid,p_intent text,p_evidence jsonb) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare b public.native_checkout_baskets; o public.landerware_public_orders; protect boolean;
begin
 -- Match every seat allocator's session-before-order lock ordering.
 perform 1 from public.class_sessions cs join public.landerware_public_orders co on co.class_session_id=cs.id join public.native_checkout_basket_items ci on ci.order_id=co.id where ci.basket_id=p_basket_id order by cs.id for update of cs;
 select * into b from public.native_checkout_baskets where id=p_basket_id for update;
 if jsonb_typeof(p_evidence->'livemode') is distinct from 'boolean' or b.id is null or b.stripe_checkout_session_id is null or p_evidence->>'id' is distinct from b.stripe_checkout_session_id or p_evidence->>'mode' is distinct from 'payment' or p_evidence->>'payment_status' is distinct from 'paid' or p_evidence->'metadata'->>'landerware_basket_id' is distinct from b.id::text or (p_evidence->>'amount_total')::integer is distinct from b.total or p_evidence->>'currency' is distinct from b.currency or p_intent is null or p_intent not like 'pi_%' or (b.stripe_payment_intent_id is not null and b.stripe_payment_intent_id<>p_intent) then raise exception 'payment_evidence_mismatch'; end if;
 if b.status in ('cancelled','refunded') then return jsonb_build_object('status',b.status); end if;
 if b.payment_evidence->>'payment_status'='paid' then return jsonb_build_object('recorded',true,'replay',true); end if;
 update public.native_checkout_baskets set payment_evidence=p_evidence,stripe_payment_intent_id=p_intent where id=b.id;
 for o in select oo.* from public.landerware_public_orders oo join public.native_checkout_basket_items i on i.order_id=oo.id where i.basket_id=b.id order by oo.id for update of oo loop
  protect:=o.status in ('held','checkout_open') and o.hold_expires_at>now() and exists(select 1 from public.class_sessions s where s.id=o.class_session_id and s.status in ('scheduled','active') and s.registration_status='open' and s.start_at>now());
  update public.landerware_public_orders set payment_evidence=p_evidence||jsonb_build_object('seat_hold_protected',protect),stripe_payment_intent_id=p_intent where id=o.id;
  update public.product_inventory_units u set public_order_payment_observed=true from public.landerware_public_order_students st where st.order_id=o.id and u.public_order_student_id=st.id and u.status='reserved';
 end loop;
 return jsonb_build_object('recorded',true);
end $$;

create function public.native_checkout_basket_finalize(p_basket_id uuid,p_intent text,p_evidence jsonb) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare b public.native_checkout_baskets; i public.native_checkout_basket_items; result jsonb;
begin
 perform 1 from public.class_sessions cs join public.landerware_public_orders co on co.class_session_id=cs.id join public.native_checkout_basket_items ci on ci.order_id=co.id where ci.basket_id=p_basket_id order by cs.id for update of cs;
 select * into b from public.native_checkout_baskets where id=p_basket_id for update;
 if b.id is null then raise exception 'reservation_not_found'; end if;
 if b.status in ('cancelled','refunded') then return jsonb_build_object('status',b.status); end if;
 if b.status='paid' then return public.native_checkout_basket_receipt(b.request_key); end if;
 begin
  for i in select * from public.native_checkout_basket_items where basket_id=b.id order by position loop
   if not public.native_checkout_basket_payment_valid(i.order_id,p_intent,p_evidence) then raise exception 'payment_evidence_mismatch'; end if;
   result:=public.native_checkout_finalize_basket_child(i.order_id,p_intent,p_evidence);
   if result->>'status' is distinct from 'paid' then raise exception 'basket_child_finalization_pending'; end if;
  end loop;
  update public.native_checkout_baskets set status='paid',paid_at=now(),reconciliation_error=null where id=b.id;
 exception when others then
  update public.native_checkout_baskets set status='payment_review',reconciliation_error='basket_finalization_pending' where id=b.id;
 end;
 return public.native_checkout_basket_receipt(b.request_key);
end $$;

revoke all on function public.native_checkout_basket_contains_order(uuid),public.native_checkout_basket_choices(text),public.native_checkout_basket_replay(uuid,jsonb),public.native_checkout_basket_receipt(uuid),public.reserve_native_checkout_basket(uuid,jsonb,jsonb),public.native_checkout_basket_payment_valid(uuid,text,jsonb),public.native_checkout_finalize_basket_child(uuid,text,jsonb),public.native_checkout_basket_record_payment(uuid,text,jsonb),public.native_checkout_basket_finalize(uuid,text,jsonb) from public,anon,authenticated;
grant execute on function public.native_checkout_basket_contains_order(uuid),public.native_checkout_basket_choices(text),public.native_checkout_basket_replay(uuid,jsonb),public.native_checkout_basket_receipt(uuid),public.reserve_native_checkout_basket(uuid,jsonb,jsonb),public.native_checkout_basket_payment_valid(uuid,text,jsonb),public.native_checkout_finalize_basket_child(uuid,text,jsonb),public.native_checkout_basket_record_payment(uuid,text,jsonb),public.native_checkout_basket_finalize(uuid,text,jsonb) to service_role;
commit;
