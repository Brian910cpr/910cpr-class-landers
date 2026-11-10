begin;
-- Explicit course/product allowlist; no stock, code, recipient or sending is seeded.
create table public.native_code_delivery_policy(
 product_key text primary key,course_ids text[] not null,enabled boolean not null default false
);
insert into public.native_code_delivery_policy(product_key,course_ids) values('aha-25-3553-heartcode-bls-online',array['509474','210549']);
create table public.native_learner_code_delivery(
 id uuid primary key default gen_random_uuid(),unit_id uuid not null unique references public.product_inventory_units(id),
 student_id uuid not null references public.landerware_public_order_students(id),recipient text not null,
 state text not null check(state in ('processing','rejected','ambiguous','accepted','cancelled')),
 lease uuid not null,attempts integer not null default 1,claimed_at timestamptz not null default now(),
 prepared_at timestamptz,retry_at timestamptz,provider_id text,error_code text
);
alter table public.native_code_delivery_policy enable row level security;
alter table public.native_learner_code_delivery enable row level security;
revoke all on public.native_code_delivery_policy,public.native_learner_code_delivery from public,anon,authenticated;
grant all on public.native_code_delivery_policy,public.native_learner_code_delivery to service_role;

create function public.native_code_delivery_eligible(p_unit uuid,p_student uuid,p_recipient text) returns boolean
language sql stable security invoker set search_path='' as $$
 select exists(select 1 from public.product_inventory_units u
 join public.products p on p.id=u.product_id
 join public.native_code_delivery_policy cfg on cfg.product_key=p.product_key and cfg.enabled
 join public.landerware_public_order_students st on st.id=u.public_order_student_id
 join public.landerware_public_orders o on o.id=st.order_id
 join public.landerware_checkout_delivery_config delivery on delivery.id and delivery.enabled and o.course_id=any(delivery.course_ids) and o.created_at>=delivery.not_before
 join public.registrations r on r.id=st.registration_id
 join public.class_sessions s on s.id=r.class_session_id
 where u.id=p_unit and st.id=p_student and lower(trim(st.email))=p_recipient
 and u.reserved_for_registration_id=r.id and u.status='reserved' and u.fulfilled_at is null
 and p.fulfillment_mode='digital_code' and o.course_id=any(cfg.course_ids)
 and o.status='paid' and o.reconciliation_error is null
 and o.payment_evidence->>'payment_status'='paid'
 and o.payment_evidence->>'id'=o.stripe_checkout_session_id
 and o.payment_evidence->'metadata'->>'landerware_order_id'=o.id::text
 and o.payment_evidence->>'currency'=o.currency
 and (o.payment_evidence->>'amount_total')::bigint=o.total
 and r.status in ('registered','confirmed','active','completed') and s.status in ('scheduled','active')
 and exists(select 1 from jsonb_array_elements(st.selected_addons) a where a->>'product_id'=p.id::text and a->>'inventory_required'='true'));
$$;

create function public.landerware_claim_learner_code(p_token text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u public.product_inventory_units; st public.landerware_public_order_students; d public.native_learner_code_delivery; ticket uuid;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 if not exists(select 1 from public.landerware_checkout_delivery_config where id and enabled) then return jsonb_build_object('disabled',true); end if;
 select unit.* into u from public.product_inventory_units unit
 join public.landerware_public_order_students student on student.id=unit.public_order_student_id
 left join public.native_learner_code_delivery job on job.unit_id=unit.id
 where public.native_code_delivery_eligible(unit.id,student.id,lower(trim(student.email)))
 and ((job.id is null and unit.exposed_at is null) or (job.state='rejected' and job.attempts<5 and job.retry_at<=now()))
 order by unit.id for update of unit skip locked limit 1;
 if u.id is null then return jsonb_build_object('empty',true); end if;
 select * into st from public.landerware_public_order_students where id=u.public_order_student_id;
 ticket:=gen_random_uuid();
 insert into public.native_learner_code_delivery(unit_id,student_id,recipient,state,lease)
 values(u.id,st.id,lower(trim(st.email)),'processing',ticket)
 on conflict(unit_id) do update set state='processing',lease=ticket,attempts=public.native_learner_code_delivery.attempts+1,
 prepared_at=null,claimed_at=now(),retry_at=null,error_code=null
 returning * into d;
 return jsonb_build_object('deliveryId',d.id,'lease',ticket);
end $$;

create function public.landerware_prepare_learner_code(p_token text,p_delivery_id uuid,p_lease uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare d public.native_learner_code_delivery; u public.product_inventory_units; st public.landerware_public_order_students;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 select * into d from public.native_learner_code_delivery where id=p_delivery_id for update;
 if d.id is null or d.lease<>p_lease or d.state<>'processing' or d.prepared_at is not null then raise exception 'invalid_delivery_lease'; end if;
 -- Order/student locks serialize against payment finalization and cancellation.
 perform 1 from public.landerware_public_orders o join public.landerware_public_order_students s on s.order_id=o.id where s.id=d.student_id for update of o,s;
 select * into st from public.landerware_public_order_students where id=d.student_id;
 perform 1 from public.registrations where id=st.registration_id for update;
 select * into u from public.product_inventory_units where id=d.unit_id for update;
 if not exists(select 1 from public.landerware_checkout_delivery_config where id and enabled)
 or not public.native_code_delivery_eligible(d.unit_id,d.student_id,d.recipient) or nullif(trim(u.secret_value),'') is null then
  update public.native_learner_code_delivery set state='cancelled',error_code='delivery_no_longer_eligible' where id=d.id;
  return jsonb_build_object('blocked',true);
 end if;
 update public.native_learner_code_delivery set prepared_at=now() where id=d.id;
 -- Exposure protects this assigned unit even if the worker/provider result is lost.
 update public.product_inventory_units set exposed_at=coalesce(exposed_at,now()),updated_at=now() where id=u.id;
 return jsonb_build_object('recipient',d.recipient,'product',(select product_key from public.products where id=u.product_id),'code',u.secret_value);
end $$;

create function public.landerware_settle_learner_code(p_token text,p_delivery_id uuid,p_lease uuid,p_outcome text,p_provider_id text,p_error text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare d public.native_learner_code_delivery;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 if p_outcome not in ('accepted','rejected','ambiguous') or p_outcome is null then raise exception 'invalid_delivery_outcome'; end if;
 if p_outcome='accepted' and nullif(trim(p_provider_id),'') is null then raise exception 'provider_receipt_required'; end if;
 select * into d from public.native_learner_code_delivery where id=p_delivery_id for update;
 if d.id is null or d.lease<>p_lease then raise exception 'invalid_delivery_lease'; end if;
 if d.state='accepted' and p_outcome='accepted' and d.provider_id=p_provider_id then return jsonb_build_object('replay',true); end if;
 if d.state<>'processing' or d.prepared_at is null then raise exception 'delivery_already_settled'; end if;
 update public.native_learner_code_delivery set
 state=case when public.native_code_delivery_eligible(d.unit_id,d.student_id,d.recipient) then p_outcome else 'cancelled' end,
 provider_id=p_provider_id,error_code=left(p_error,100),
 retry_at=case when p_outcome='rejected' then now()+interval '2 minutes'*attempts else null end where id=d.id;
 return jsonb_build_object('settled',true,'actualDeliveryConfirmed',false);
end $$;
create function public.landerware_learner_code_health(p_token text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare processing integer; uncertain integer; rejected integer; accepted integer;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 select count(*) filter(where state='processing'),count(*) filter(where state='ambiguous' or (state='processing' and claimed_at<now()-interval '5 minutes')),
 count(*) filter(where state='rejected'),count(*) filter(where state='accepted') into processing,uncertain,rejected,accepted from public.native_learner_code_delivery;
 return jsonb_build_object('processing',processing,'reviewRequired',uncertain,'rejected',rejected,'accepted',accepted,'actualDeliveryConfirmed',false);
end $$;
-- Replace obsolete manual-only owner wording; retain the durable operational
-- notification without suggesting a second release of an automatically sent code.
DO $rewrite$ declare definition text; begin
 select pg_get_functiondef('public.landerware_finalize_public_order(uuid,text,jsonb)'::regprocedure) into definition;
 definition:=replace(definition,'Manual fulfillment required; do not auto-release codes or materials.','Configured paid-course access codes are delivered automatically when enabled. Review nonautomatic items and delivery exceptions; do not duplicate an assigned code release.');
 execute definition;
end $rewrite$;
revoke all on function public.landerware_learner_code_health(text),public.native_code_delivery_eligible(uuid,uuid,text),public.landerware_claim_learner_code(text),public.landerware_prepare_learner_code(text,uuid,uuid),public.landerware_settle_learner_code(text,uuid,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.native_code_delivery_eligible(uuid,uuid,text) to service_role;
grant execute on function public.landerware_learner_code_health(text),public.landerware_claim_learner_code(text),public.landerware_prepare_learner_code(text,uuid,uuid),public.landerware_settle_learner_code(text,uuid,uuid,text,text,text) to service_role,anon;
commit;
