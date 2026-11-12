-- Default-off native learner-code transport. No stock, recipients, secrets or proof seeded.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
alter table public.native_learner_code_delivery add column provider text not null default 'cloudflare' check(provider in ('cloudflare','resend'));
create table public.native_learner_code_runtime(
 id boolean primary key default true check(id), enabled boolean not null default false,
 provider text not null default 'resend' check(provider='resend'),
 configured boolean not null default false, proven boolean not null default false,
 proof_reference text, proof_at timestamptz,
 last_poll_at timestamptz,last_completed_at timestamptz,last_fault_at timestamptz,
 fault boolean not null default false,next_lane text not null default 'learner_code' check(next_lane in ('confirmation','learner_code')),
 check(not proven or (proof_at is not null and nullif(trim(proof_reference),'') is not null))
);
insert into public.native_learner_code_runtime(id) values(true);
-- Explicit invoker prerequisites: never rely on installation default privileges.
-- Public orders/students SELECT/UPDATE are granted by20260909220000; repeat the
-- minimal privileges for clean, reproducible installation and row locking.
grant usage on schema public to service_role;
grant select on public.landerware_checkout_delivery_config,public.product_inventory_units,
 public.products,public.registrations,public.class_sessions,
 public.landerware_public_orders,public.landerware_public_order_students to service_role;
grant update(id) on public.landerware_checkout_delivery_config,public.registrations,
 public.landerware_public_orders,public.landerware_public_order_students to service_role;
grant update(exposed_at,updated_at) on public.product_inventory_units to service_role;

alter table public.native_learner_code_runtime enable row level security;
revoke all on public.native_learner_code_runtime from public,anon,authenticated;
grant select,update on public.native_learner_code_runtime to service_role;
-- Legacy token endpoints remain isolated to legacy provider attempts. New service
-- functions below are independent invoker bodies, never token-bypassing wrappers.
create or replace function public.landerware_claim_learner_code(p_token text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u public.product_inventory_units; st public.landerware_public_order_students; d public.native_learner_code_delivery; ticket uuid;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 perform 1 from public.landerware_checkout_delivery_config where id for share;
 perform 1 from public.native_code_delivery_policy for share;
 if not exists(select 1 from public.landerware_checkout_delivery_config where id and enabled and provider='cloudflare') then return jsonb_build_object('disabled',true); end if;
 select unit.* into u from public.product_inventory_units unit
 join public.landerware_public_order_students student on student.id=unit.public_order_student_id
 left join public.native_learner_code_delivery job on job.unit_id=unit.id
 where public.native_code_delivery_eligible(unit.id,student.id,lower(trim(student.email)))
 and ((job.id is null and unit.exposed_at is null) or (job.provider='cloudflare' and job.state='rejected' and job.attempts<5 and job.retry_at<=now()))
 order by unit.id for update of unit skip locked limit 1;
 -- Serialize provider switch against claims.
 if u.id is null then return jsonb_build_object('empty',true); end if;
 select * into st from public.landerware_public_order_students where id=u.public_order_student_id;
 ticket:=gen_random_uuid();
 insert into public.native_learner_code_delivery(unit_id,student_id,recipient,state,lease)
 values(u.id,st.id,lower(trim(st.email)),'processing',ticket)
 on conflict(unit_id) do update set state='processing',lease=ticket,attempts=public.native_learner_code_delivery.attempts+1,
 prepared_at=null,claimed_at=now(),retry_at=null,error_code=null
 -- A concurrent statement may have observed a missing job before another
 -- claimer committed. Never replace a live lease using that stale join.
 where public.native_learner_code_delivery.provider='cloudflare' and public.native_learner_code_delivery.state='rejected'
   and public.native_learner_code_delivery.attempts<5
   and public.native_learner_code_delivery.retry_at<=now()
   and public.native_learner_code_delivery.student_id=excluded.student_id
   and public.native_learner_code_delivery.recipient=excluded.recipient
 returning * into d;
 if d.id is null then return jsonb_build_object('empty',true); end if;
 return jsonb_build_object('deliveryId',d.id,'lease',ticket);
end $$;
create or replace function public.landerware_prepare_learner_code(p_token text,p_delivery_id uuid,p_lease uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare d public.native_learner_code_delivery; u public.product_inventory_units; st public.landerware_public_order_students;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 perform 1 from public.landerware_checkout_delivery_config where id for share;
 perform 1 from public.native_code_delivery_policy for share;
 select * into d from public.native_learner_code_delivery where id=p_delivery_id for update;
 if d.id is null or d.provider<>'cloudflare' or d.lease is distinct from p_lease or d.state<>'processing' or d.prepared_at is not null then raise exception 'invalid_delivery_lease'; end if;
 -- Order/student locks serialize against payment finalization and cancellation.
 perform 1 from public.landerware_public_orders o join public.landerware_public_order_students s on s.order_id=o.id where s.id=d.student_id for update of o,s;
 select * into st from public.landerware_public_order_students where id=d.student_id;
 perform 1 from public.registrations where id=st.registration_id for update;
 select * into u from public.product_inventory_units where id=d.unit_id for update;
 if not exists(select 1 from public.landerware_checkout_delivery_config where id and enabled and provider='cloudflare')
 or not public.native_code_delivery_eligible(d.unit_id,d.student_id,d.recipient) or nullif(trim(u.secret_value),'') is null then
  update public.native_learner_code_delivery set state='cancelled',error_code='delivery_no_longer_eligible' where id=d.id;
  return jsonb_build_object('blocked',true);
 end if;
 update public.native_learner_code_delivery set prepared_at=now() where id=d.id;
 -- Exposure protects this assigned unit even if the worker/provider result is lost.
 update public.product_inventory_units set exposed_at=coalesce(exposed_at,now()),updated_at=now() where id=u.id;
 return jsonb_build_object('recipient',d.recipient,'product',(select product_key from public.products where id=u.product_id),'code',u.secret_value);
end $$;
create or replace function public.landerware_settle_learner_code(p_token text,p_delivery_id uuid,p_lease uuid,p_outcome text,p_provider_id text,p_error text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare d public.native_learner_code_delivery;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 if p_outcome not in ('accepted','rejected','ambiguous') or p_outcome is null then raise exception 'invalid_delivery_outcome'; end if;
 if p_outcome='accepted' and nullif(trim(p_provider_id),'') is null then raise exception 'provider_receipt_required'; end if;
 select * into d from public.native_learner_code_delivery where id=p_delivery_id for update;
 if d.id is null or d.provider<>'cloudflare' or d.lease is distinct from p_lease then raise exception 'invalid_delivery_lease'; end if;
 if d.state='accepted' and p_outcome='accepted' and d.provider_id=p_provider_id then return jsonb_build_object('replay',true); end if;
 if d.state<>'processing' or d.prepared_at is null then raise exception 'delivery_already_settled'; end if;
 update public.native_learner_code_delivery set
 state=case when public.native_code_delivery_eligible(d.unit_id,d.student_id,d.recipient) then p_outcome else 'cancelled' end,
 provider_id=p_provider_id,error_code=left(p_error,100),
 retry_at=case when p_outcome='rejected' then now()+interval '2 minutes'*attempts else null end where id=d.id;
 return jsonb_build_object('settled',true,'actualDeliveryConfirmed',false);
end $$;

create function public.native_learner_code_eligible(p_unit uuid,p_student uuid,p_recipient text) returns boolean
language sql stable security invoker set search_path='' as $$
 select public.native_code_delivery_eligible(p_unit,p_student,p_recipient) and exists(
 select 1 from public.product_inventory_units u
 join public.landerware_public_order_students st on st.id=u.public_order_student_id
 join public.landerware_public_orders o on o.id=st.order_id
 join public.registrations r on r.id=st.registration_id
 join public.class_sessions s on s.id=r.class_session_id
 where u.id=p_unit and st.id=p_student and o.checkout_runtime_version='native-v1'
 and r.class_session_id=o.class_session_id and s.registration_backend='landerware'
 and u.public_order_payment_observed);
$$;
create function public.native_claim_learner_code(p_order_id uuid default null) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare u public.product_inventory_units; st public.landerware_public_order_students; d public.native_learner_code_delivery; ticket uuid;
begin
 perform 1 from public.landerware_checkout_delivery_config where id for share;
 perform 1 from public.native_code_delivery_policy for share;
 perform 1 from public.native_learner_code_runtime where id for share;

 if not exists(select 1 from public.landerware_checkout_delivery_config where id and enabled and provider='resend') or not exists(select 1 from public.native_learner_code_runtime where id and enabled) then return jsonb_build_object('disabled',true); end if;
 select unit.* into u from public.product_inventory_units unit
 join public.landerware_public_order_students student on student.id=unit.public_order_student_id
 left join public.native_learner_code_delivery job on job.unit_id=unit.id
 where public.native_learner_code_eligible(unit.id,student.id,lower(trim(student.email)))
 and (p_order_id is null or student.order_id=p_order_id)
 and ((job.id is null and unit.exposed_at is null) or (job.provider='resend' and job.state='rejected' and job.attempts<5 and job.retry_at<=now()))
 order by unit.id for update of unit skip locked limit 1;
 if u.id is null then return jsonb_build_object('empty',true); end if;
 select * into st from public.landerware_public_order_students where id=u.public_order_student_id;
 ticket:=gen_random_uuid();
 insert into public.native_learner_code_delivery(unit_id,student_id,recipient,state,lease,provider)
 values(u.id,st.id,lower(trim(st.email)),'processing',ticket,'resend')
 on conflict(unit_id) do update set state='processing',lease=ticket,attempts=public.native_learner_code_delivery.attempts+1,
 prepared_at=null,claimed_at=now(),retry_at=null,error_code=null
 -- A concurrent statement may have observed a missing job before another
 -- claimer committed. Never replace a live lease using that stale join.
 where public.native_learner_code_delivery.provider='resend' and public.native_learner_code_delivery.state='rejected'
   and public.native_learner_code_delivery.attempts<5
   and public.native_learner_code_delivery.retry_at<=now()
   and public.native_learner_code_delivery.student_id=excluded.student_id
   and public.native_learner_code_delivery.recipient=excluded.recipient
 returning * into d;
 if d.id is null then return jsonb_build_object('empty',true); end if;
 return jsonb_build_object('deliveryId',d.id,'lease',ticket);
end $$;
create function public.native_prepare_learner_code(p_delivery_id uuid,p_lease uuid) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare d public.native_learner_code_delivery; u public.product_inventory_units; st public.landerware_public_order_students;
begin
 perform 1 from public.landerware_checkout_delivery_config where id for share;
 perform 1 from public.native_code_delivery_policy for share;
 perform 1 from public.native_learner_code_runtime where id for share;

 select * into d from public.native_learner_code_delivery where id=p_delivery_id for update;
 if d.id is null or d.provider<>'resend' or d.lease is distinct from p_lease or d.state<>'processing' or d.prepared_at is not null then raise exception 'invalid_delivery_lease'; end if;
 -- Order/student locks serialize against payment finalization and cancellation.
 perform 1 from public.landerware_public_orders o join public.landerware_public_order_students s on s.order_id=o.id where s.id=d.student_id for update of o,s;
 select * into st from public.landerware_public_order_students where id=d.student_id;
 perform 1 from public.registrations where id=st.registration_id for update;
 select * into u from public.product_inventory_units where id=d.unit_id for update;
 if not exists(select 1 from public.landerware_checkout_delivery_config where id and enabled and provider='resend')
 or not exists(select 1 from public.native_learner_code_runtime where id and enabled)
 or not public.native_learner_code_eligible(d.unit_id,d.student_id,d.recipient) or nullif(trim(u.secret_value),'') is null then
  update public.native_learner_code_delivery set state='cancelled',error_code='delivery_no_longer_eligible' where id=d.id;
  return jsonb_build_object('blocked',true);
 end if;
 update public.native_learner_code_delivery set prepared_at=now() where id=d.id;
 -- Exposure protects this assigned unit even if the worker/provider result is lost.
 update public.product_inventory_units set exposed_at=coalesce(exposed_at,now()),updated_at=now() where id=u.id;
 return jsonb_build_object('recipient',d.recipient,'product',(select product_key from public.products where id=u.product_id),'code',u.secret_value);
end $$;
create function public.native_settle_learner_code(p_delivery_id uuid,p_lease uuid,p_outcome text,p_provider_id text,p_error text) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare d public.native_learner_code_delivery;
begin

 if p_outcome not in ('accepted','rejected','ambiguous') or p_outcome is null then raise exception 'invalid_delivery_outcome'; end if;
 if p_outcome='accepted' and (p_provider_id is null or p_provider_id !~ '^[A-Za-z0-9_-]{1,128}$') then raise exception 'provider_receipt_required'; end if;
 if p_outcome<>'accepted' and p_provider_id is not null then raise exception 'invalid_delivery_outcome'; end if;
 if p_error is not null and p_error !~ '^[a-z0-9_]{1,100}$' then raise exception 'invalid_delivery_error'; end if;
 select * into d from public.native_learner_code_delivery where id=p_delivery_id for update;
 if d.id is null or d.provider<>'resend' or d.lease is distinct from p_lease then raise exception 'invalid_delivery_lease'; end if;
 if d.state=p_outcome and d.provider_id is not distinct from p_provider_id and d.error_code is not distinct from p_error then return jsonb_build_object('replay',true); end if;
 if d.state<>'processing' or d.prepared_at is null then raise exception 'delivery_already_settled'; end if;
 update public.native_learner_code_delivery set
 state=p_outcome,
 provider_id=p_provider_id,error_code=left(p_error,100),
 retry_at=case when p_outcome='rejected' then now()+interval '2 minutes'*attempts else null end where id=d.id;
 return jsonb_build_object('settled',true,'actualDeliveryConfirmed',false);
end $$;

-- Cadence can run while admission is closed. This does not grant or create proof.
create function public.native_learner_code_runtime_tick(p_phase text,p_configured boolean,p_fault boolean) returns jsonb
language plpgsql security invoker set search_path='' as $$
begin
 if p_phase is null or p_phase not in ('poll','completed') or p_configured is null or p_fault is null then raise exception 'invalid_runtime_tick'; end if;
 update public.native_learner_code_runtime set configured=p_configured,
 last_poll_at=case when p_phase='poll' then clock_timestamp() else last_poll_at end,
 last_completed_at=case when p_phase='completed' and p_configured and not p_fault then clock_timestamp() else last_completed_at end,
 last_fault_at=case when p_fault then clock_timestamp() else last_fault_at end,
 fault=case when p_fault or not p_configured then true when p_phase='completed' then false else fault end where id;
 return jsonb_build_object('recorded',true);
end $$;
create function public.native_mail_next_lane() returns jsonb
language plpgsql security invoker set search_path='' as $$
declare lane text;
begin
 select next_lane into lane from public.native_learner_code_runtime where id and enabled for update;
 if not found then return jsonb_build_object('lane','confirmation'); end if;
 update public.native_learner_code_runtime set next_lane=case lane when 'confirmation' then 'learner_code' else 'confirmation' end where id;
 return jsonb_build_object('lane',lane);
end $$;
create function public.native_learner_code_health() returns jsonb
language plpgsql volatile security invoker set search_path='' as $$
declare cfg public.native_learner_code_runtime; pending integer; faults integer; accepted integer; oldest timestamptz; checked_at timestamptz:=clock_timestamp();
begin
 select * into cfg from public.native_learner_code_runtime where id;
 select count(*),min(o.paid_at) into pending,oldest from public.product_inventory_units u
 join public.landerware_public_order_students st on st.id=u.public_order_student_id
 join public.landerware_public_orders o on o.id=st.order_id
 left join public.native_learner_code_delivery d on d.unit_id=u.id
 where public.native_learner_code_eligible(u.id,st.id,lower(trim(st.email))) and (d.id is null or d.state='cancelled' or (d.provider<>'resend' and d.state<>'accepted'));
 select count(*) filter(where state in ('ambiguous','processing','rejected')),
 count(*) filter(where state='accepted') into faults,accepted from public.native_learner_code_delivery where provider='resend';
 return jsonb_build_object('enabled',coalesce(cfg.enabled,false),'provider','resend','configured',coalesce(cfg.configured,false),'proven',coalesce(cfg.proven,false),
 'unclaimedEligible',pending,'oldestUnclaimedAt',oldest,'unresolvedFaults',faults+case when cfg.fault then 1 else 0 end,'accepted',accepted,
 'healthy',coalesce(cfg.enabled and cfg.configured and cfg.proven and not cfg.fault and cfg.last_poll_at>checked_at-interval '3 minutes' and cfg.last_poll_at<=checked_at and cfg.last_completed_at>checked_at-interval '3 minutes' and cfg.last_completed_at<=checked_at and faults=0 and pending=0,false),
 'deliveryUnconfirmed',accepted,'actualDeliveryConfirmed',false,'lastPollAt',cfg.last_poll_at,'lastCompletedAt',cfg.last_completed_at,
 'pollFresh',coalesce(cfg.last_poll_at>checked_at-interval '3 minutes' and cfg.last_poll_at<=checked_at,false),'completionFresh',coalesce(cfg.last_completed_at>checked_at-interval '3 minutes' and cfg.last_completed_at<=checked_at,false));
end $$;
create function public.native_learner_code_runtime_readiness() returns jsonb
language plpgsql volatile security invoker set search_path='' as $$
declare h jsonb; ready boolean; observer jsonb; checked_at timestamptz:=clock_timestamp();
begin
 h:=public.native_learner_code_health();
 if to_regprocedure('public.native_checkout_scheduler_status()') is not null then
  execute 'select public.native_checkout_scheduler_status()' into observer;
 end if;
 -- Evaluate the final cadence boundary after reading all health observations.
 checked_at:=clock_timestamp();
 h:=h||jsonb_build_object('pollFresh',coalesce((h->>'lastPollAt')::timestamptz>checked_at-interval '3 minutes' and (h->>'lastPollAt')::timestamptz<=checked_at,false),
  'completionFresh',coalesce((h->>'lastCompletedAt')::timestamptz>checked_at-interval '3 minutes' and (h->>'lastCompletedAt')::timestamptz<=checked_at,false));
 h:=h||jsonb_build_object('observerFresh',coalesce((observer->>'lastObservedAt')::timestamptz>checked_at-interval '3 minutes' and (observer->>'lastObservedAt')::timestamptz<=checked_at and (observer->>'lastCompletedAt')::timestamptz>checked_at-interval '3 minutes' and (observer->>'lastCompletedAt')::timestamptz<=checked_at and observer->'enabled'='true'::jsonb and observer->'latched'='false'::jsonb,false));
 ready:=coalesce((h->>'enabled')::boolean and (h->>'configured')::boolean and (h->>'proven')::boolean
 and (h->>'pollFresh')::boolean and (h->>'observerFresh')::boolean and (h->>'completionFresh')::boolean and (h->>'unresolvedFaults')::integer=0 and (h->>'unclaimedEligible')::integer=0,false)
 and exists(select 1 from public.landerware_checkout_delivery_config where id and enabled and provider='resend');
 return h||jsonb_build_object('ready',ready);
end $$;
-- Provider isolation also applies to historical receipt projection. Legacy event
-- ingestion cannot prove a Resend receipt, even if message IDs happen to collide.
create or replace view public.native_code_delivery_history with(security_invoker=true) as
select d.id,d.unit_id,d.student_id,d.recipient,d.state,d.lease,d.attempts,d.claimed_at,d.prepared_at,d.retry_at,d.provider_id,d.error_code,
 e.status as provider_delivery_status,e.event_at as provider_event_at,coalesce(e.status='delivered',false) as actual_delivery_confirmed
from public.native_learner_code_delivery d
left join lateral(select ev.status,ev.event_at from public.landerware_email_delivery_events ev
 where d.provider='cloudflare' and ev.provider_message_id=trim(both '<>' from d.provider_id) and ev.recipient=lower(trim(d.recipient))
 order by (ev.status='complained') desc,(ev.status<>'deferred') desc,ev.event_at desc,ev.event_id desc limit 1) e on true;
revoke all on function public.native_learner_code_eligible(uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.native_learner_code_eligible(uuid,uuid,text) to service_role;
revoke all on function public.native_claim_learner_code(uuid) from public,anon,authenticated;
grant execute on function public.native_claim_learner_code(uuid) to service_role;
revoke all on function public.native_prepare_learner_code(uuid,uuid) from public,anon,authenticated;
grant execute on function public.native_prepare_learner_code(uuid,uuid) to service_role;
revoke all on function public.native_settle_learner_code(uuid,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.native_settle_learner_code(uuid,uuid,text,text,text) to service_role;
revoke all on function public.native_learner_code_runtime_tick(text,boolean,boolean) from public,anon,authenticated;
grant execute on function public.native_learner_code_runtime_tick(text,boolean,boolean) to service_role;
revoke all on function public.native_mail_next_lane() from public,anon,authenticated;
grant execute on function public.native_mail_next_lane() to service_role;
revoke all on function public.native_learner_code_health() from public,anon,authenticated;
grant execute on function public.native_learner_code_health() to service_role;
revoke all on function public.native_learner_code_runtime_readiness() from public,anon,authenticated;
grant execute on function public.native_learner_code_runtime_readiness() to service_role;
DO $scheduler$ begin
 if to_regprocedure('public.native_checkout_scheduler_finish(uuid,jsonb)') is not null then
 execute $definition$create or replace function public.native_checkout_scheduler_finish(p_run_id uuid,p_result jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare r landerware_native_scheduler.runs%rowtype; k text; n integer; total integer:=0;
begin
 if p_result is null or jsonb_typeof(p_result)<>'object' or
  (select count(*) from jsonb_object_keys(p_result))<>(case when p_result?'blocked' then 7 else 6 end) or
  not(p_result ?& array['outcome','code','claimed','accepted','rejected','ambiguous']) or
  coalesce(p_result->>'outcome','') not in('completed','disabled','uncertain','fault') or
  (p_result->>'code' is not null and p_result->>'code' !~ '^[a-z0-9_]{1,100}$') then raise exception 'invalid_scheduler_result'; end if;
 foreach k in array (array['claimed','accepted','rejected','ambiguous']||case when p_result?'blocked' then array['blocked'] else array[]::text[] end) loop
  if jsonb_typeof(p_result->k)<>'number' or p_result->>k !~ '^[0-9]{1,2}$' then raise exception 'invalid_scheduler_result'; end if;
  n:=(p_result->>k)::int;if n>10 then raise exception 'invalid_scheduler_result';end if;
  if k<>'claimed' then total:=total+n;end if;
 end loop;
 if total>(p_result->>'claimed')::int or
  (p_result->>'outcome'='completed' and (total<>(p_result->>'claimed')::int or (p_result->>'ambiguous')::int<>0 or p_result->>'code' is not null)) or
  (p_result->>'outcome'='disabled' and ((p_result->>'claimed')::int<>0 or p_result->>'code' is not null)) then raise exception 'invalid_scheduler_result';end if;
 perform 1 from landerware_native_scheduler.config where id for update;
 select * into r from landerware_native_scheduler.runs where id=p_run_id for update;
 if r.finished_at is not null and r.result=p_result then return jsonb_build_object('replay',true);end if;
 if r.id is null or r.state<>'running' or r.finished_at is not null then raise exception 'invalid_scheduler_run';end if;
 update landerware_native_scheduler.runs set state=p_result->>'outcome',result=p_result,finished_at=now() where id=r.id;
 if p_result->>'outcome' in('uncertain','fault') then
  update landerware_native_scheduler.config set latched=true,reason=coalesce(p_result->>'code','callback_unknown') where id;
 end if;
 return jsonb_build_object('settled',true);
end $$;$definition$;
 end if;
end $scheduler$;



commit;
