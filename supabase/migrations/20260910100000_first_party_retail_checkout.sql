begin;

create table if not exists public.landerware_retail_orders (
  id uuid primary key default gen_random_uuid(),
  registration_id uuid not null unique references public.landerware_registrations(id),
  person_id uuid not null references public.landerware_people(id),
  session_id uuid not null references public.landerware_sessions(id),
  external_class_id text not null,
  course_id text not null,
  course_name text not null,
  class_amount_cents integer not null check (class_amount_cents >= 0),
  selected_options jsonb not null default '{}'::jsonb,
  options_amount_cents integer not null default 0 check (options_amount_cents >= 0),
  total_amount_cents integer not null check (total_amount_cents >= 0),
  currency text not null default 'usd',
  status text not null default 'held' check (status in ('held','checkout_open','paid','expired','cancelled','refunded')),
  hold_expires_at timestamptz not null,
  stripe_checkout_session_id text unique,
  stripe_payment_intent_id text,
  checkout_url text,
  paid_at timestamptz,
  idempotency_key text not null unique,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create index if not exists landerware_retail_orders_session_state on public.landerware_retail_orders(session_id,status,hold_expires_at);
alter table public.landerware_retail_orders enable row level security;
revoke all on public.landerware_retail_orders from public,anon,authenticated;
grant select,insert,update on public.landerware_retail_orders to service_role;

insert into public.landerware_courses(id,display_name,provider,delivery_mode,public_slug,listed,enrollware_course_id,active)
values
 ('retail-209806','AHA BLS Provider – In-Person','American Heart Association','classroom','aha-bls-provider',true,'209806',true),
 ('retail-359474','AHA BLS Provider – In-Person Renewal','American Heart Association','classroom','bls-renewal',true,'359474',true),
 ('retail-210549','AHA BLS Provider – HeartCode + Skills Session','American Heart Association','blended','heartcode-bls',true,'210549',true)
on conflict(id) do update set display_name=excluded.display_name,listed=true,enrollware_course_id=excluded.enrollware_course_id,active=true,updated_at=now();

insert into public.landerware_registration_profiles(profile_key,course_id,display_name,listed,registration_mode,session_policy,allowed_entry_contexts,required_fields,requirements,addons,payer_policy,pricing_behavior,corporate_context,confirmation_template_key,completion_prerequisites)
values
 ('retail-209806','retail-209806','AHA BLS Provider – In-Person',true,'public_direct','required',array['public_anonymous'],'["first_name","last_name","email","phone"]','[]','[]','{"mode":"customer_pays"}','{"mode":"enrollware_catalog_snapshot","amount_cents":7500,"currency":"usd","source":"raw/course_archive_v4.json"}','{"capacity":6,"source":"Enrollware catalog 1:6 hands-on ratio"}','standard-registration-confirmation-v1','[]'),
 ('retail-359474','retail-359474','AHA BLS Provider – In-Person Renewal',true,'public_direct','required',array['public_anonymous'],'["first_name","last_name","email","phone"]','[]','[]','{"mode":"customer_pays"}','{"mode":"enrollware_catalog_snapshot","amount_cents":7500,"currency":"usd","source":"raw/course_archive_v4.json"}','{"capacity":6,"source":"Enrollware catalog 1:6 hands-on ratio"}','standard-registration-confirmation-v1','[]'),
 ('retail-210549','retail-210549','AHA BLS Provider – HeartCode + Skills Session',true,'public_direct','required',array['public_anonymous'],'["first_name","last_name","email","phone"]','[]','[]','{"mode":"customer_pays"}','{"mode":"enrollware_catalog_snapshot","amount_cents":5500,"currency":"usd","source":"raw/course_archive_v4.json"}','{"capacity":6,"source":"BLS hands-on station ratio"}','standard-registration-confirmation-v1','[]')
on conflict(profile_key) do update set display_name=excluded.display_name,listed=true,pricing_behavior=excluded.pricing_behavior,updated_at=now();

create or replace function public.begin_retail_checkout(p_external_class_id text,p_course_id text,p_course_name text,p_starts_at timestamptz,p_ends_at timestamptz,p_location_name text,p_first_name text,p_last_name text,p_email text,p_phone text,p_selected_options jsonb,p_idempotency_key text,p_capacity integer default null)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_profile public.landerware_registration_profiles; v_person jsonb; v_person_id uuid; v_session public.landerware_sessions; v_roster public.landerware_rosters; v_reg public.landerware_registrations; v_order public.landerware_retail_orders; v_base int; v_options int:=0; v_option_key text; v_option_value jsonb; v_allowed jsonb; v_count int;
begin
 perform pg_advisory_xact_lock(hashtextextended('retail-seat|'||p_external_class_id,0));
 update public.landerware_retail_orders set status='expired',updated_at=now() where status in('held','checkout_open') and hold_expires_at<=now();
 update public.landerware_registrations r set status='expired',updated_at=now() from public.landerware_retail_orders o where o.registration_id=r.id and o.status='expired' and r.status='held';
 select * into v_order from public.landerware_retail_orders where idempotency_key='retail:'||p_idempotency_key;
 if v_order.id is not null then return jsonb_build_object('orderId',v_order.id,'registrationId',v_order.registration_id,'holdExpiresAt',v_order.hold_expires_at,'totalAmountCents',v_order.total_amount_cents,'status',v_order.status,'checkoutUrl',v_order.checkout_url,'idempotentReplay',true); end if;
 select * into v_profile from public.landerware_registration_profiles where profile_key='retail-'||p_course_id and active and listed;
 if v_profile.profile_key is null then raise exception 'retail_profile_not_found'; end if;
 v_base:=coalesce((v_profile.pricing_behavior->>'amount_cents')::int,-1); if v_base<0 then raise exception 'retail_price_unavailable'; end if;
 for v_option_key,v_option_value in select key,value from jsonb_each(coalesce(p_selected_options,'{}')) loop
   select value into v_allowed from jsonb_array_elements(v_profile.addons) where value->>'key'=v_option_key limit 1;
   if v_allowed is null or v_option_value <> 'true'::jsonb then raise exception 'invalid_retail_option'; end if;
   v_options:=v_options+coalesce((v_allowed->>'amount_cents')::int,0);
 end loop;
 insert into public.landerware_sessions(external_session_id,course_id,course_name,starts_at,ends_at,location_name,provenance,requirements_manifest)
 values(p_external_class_id,v_profile.course_id,p_course_name,p_starts_at,p_ends_at,p_location_name,'public_retail','{}')
 on conflict(external_session_id,course_id,starts_at) do update set ends_at=excluded.ends_at,location_name=excluded.location_name,updated_at=now() returning * into v_session;
 select count(*) into v_count from public.landerware_retail_orders where session_id=v_session.id and (status='paid' or (status in('held','checkout_open') and hold_expires_at>now()));
 if v_count>=coalesce(p_capacity,(v_profile.corporate_context->>'capacity')::int) then raise exception 'session_full'; end if;
 v_person:=public.landerware_create_or_find_person(p_first_name,p_last_name,p_email,p_phone); v_person_id:=(v_person->>'personId')::uuid;
 insert into public.landerware_rosters(session_id) values(v_session.id) on conflict(session_id) do update set updated_at=now() returning * into v_roster;
 insert into public.landerware_registrations(person_id,session_id,roster_id,status,source,idempotency_key,course_id,registration_profile_key,registration_profile_snapshot,entry_context,session_selection_status,selected_options,payer_mode,pricing_state,payment_state,billing_state)
 values(v_person_id,v_session.id,v_roster.id,'held','public_retail','retail:'||p_idempotency_key,v_profile.course_id,v_profile.profile_key,to_jsonb(v_profile),'public_anonymous','held',coalesce(p_selected_options,'{}'),'customer_pays',v_profile.pricing_behavior,'pending','not_required') returning * into v_reg;
 insert into public.landerware_retail_orders(registration_id,person_id,session_id,external_class_id,course_id,course_name,class_amount_cents,selected_options,options_amount_cents,total_amount_cents,hold_expires_at,idempotency_key)
 values(v_reg.id,v_person_id,v_session.id,p_external_class_id,p_course_id,p_course_name,v_base,coalesce(p_selected_options,'{}'),v_options,v_base+v_options,now()+interval '31 minutes','retail:'||p_idempotency_key) returning * into v_order;
 return jsonb_build_object('orderId',v_order.id,'registrationId',v_reg.id,'personId',v_person_id,'holdExpiresAt',v_order.hold_expires_at,'totalAmountCents',v_order.total_amount_cents,'status',v_order.status,'idempotentReplay',false);
end $$;
revoke execute on function public.begin_retail_checkout(text,text,text,timestamptz,timestamptz,text,text,text,text,text,jsonb,text,integer) from public,anon,authenticated;
grant execute on function public.begin_retail_checkout(text,text,text,timestamptz,timestamptz,text,text,text,text,text,jsonb,text,integer) to service_role;

create or replace function public.confirm_retail_payment(p_order_id uuid,p_checkout_session_id text,p_payment_intent_id text,p_evidence jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare v_order public.landerware_retail_orders;
begin select * into v_order from public.landerware_retail_orders where id=p_order_id for update; if v_order.id is null then raise exception 'order_not_found'; end if; if v_order.status='paid' then return jsonb_build_object('ok',true,'orderId',v_order.id,'registrationId',v_order.registration_id,'idempotentReplay',true); end if;
 update public.landerware_retail_orders set status='paid',stripe_checkout_session_id=coalesce(stripe_checkout_session_id,p_checkout_session_id),stripe_payment_intent_id=p_payment_intent_id,paid_at=coalesce(paid_at,now()),updated_at=now() where id=v_order.id;
 update public.landerware_registrations set status='active',session_selection_status='selected',payment_state='paid',updated_at=now() where id=v_order.registration_id;
 insert into public.landerware_roster_memberships(roster_id,session_id,person_id,registration_id,display_name,email,source)
 select r.roster_id,r.session_id,r.person_id,r.id,trim(p.current_first_name||' '||p.current_last_name),p.current_email,'stripe_checkout' from public.landerware_registrations r join public.landerware_people p on p.id=r.person_id where r.id=v_order.registration_id and not exists(select 1 from public.landerware_roster_memberships m where m.registration_id=r.id);
 insert into public.landerware_activity_events(event_type,actor_source,person_id,registration_id,session_id,details) values('retail_payment_confirmed','system',v_order.person_id,v_order.registration_id,v_order.session_id,p_evidence);
 insert into public.landerware_messages(person_id,registration_id,template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key)
 select v_order.person_id,v_order.registration_id,'standard-registration-confirmation-v1',p.current_email,'Your 910CPR registration is confirmed','Hi '||p.current_first_name||E',\n\nYour payment was received and your seat is confirmed for '||v_order.course_name||E'.\n\n910CPR\n910-395-5193','gmail','pending','retail-paid-confirmation:'||v_order.id from public.landerware_people p where p.id=v_order.person_id on conflict(idempotency_key) do nothing;
 return jsonb_build_object('ok',true,'orderId',v_order.id,'registrationId',v_order.registration_id);
end $$;
revoke execute on function public.confirm_retail_payment(uuid,text,text,jsonb) from public,anon,authenticated; grant execute on function public.confirm_retail_payment(uuid,text,text,jsonb) to service_role;

commit;
