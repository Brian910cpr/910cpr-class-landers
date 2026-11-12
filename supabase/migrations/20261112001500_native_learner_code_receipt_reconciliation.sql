-- Optional service-only known-receipt verification. No provider calls, sends,
-- activation, proof, credentials, inventory release or entitlement changes.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
-- Product row lock for final receipt identity requires UPDATE on one column.
grant update(id) on public.products to service_role;
create table public.native_learner_code_receipt_evidence(
 delivery_id uuid primary key references public.native_learner_code_delivery(id),
 lease uuid not null,provider text not null check(provider='resend'),
 provider_id text not null unique,provider_created_at timestamptz not null,
 last_status text not null check(last_status in ('sent','delivered','delivery_delayed','bounced','failed','complained','suppressed','opened','clicked')),
 first_verified_at timestamptz not null default clock_timestamp(),last_verified_at timestamptz not null default clock_timestamp(),
 delivered_observed_at timestamptz,adverse_status text check(adverse_status in ('bounced','failed','complained','suppressed'))
);
alter table public.native_learner_code_receipt_evidence enable row level security;
revoke all on public.native_learner_code_receipt_evidence from public,anon,authenticated;
grant select,insert,update on public.native_learner_code_receipt_evidence to service_role;

-- This is a private canonical-identity check, intentionally independent of
-- business eligibility, runtime enablement and payment/refund/session status.
create function public.native_learner_code_receipt_identity(p_delivery_id uuid,p_lease uuid) returns boolean
language sql stable security invoker set search_path='' as $$
 select exists(select 1 from public.native_learner_code_delivery d
 join public.product_inventory_units u on u.id=d.unit_id
 join public.products p on p.id=u.product_id
 join public.landerware_public_order_students st on st.id=d.student_id and st.id=u.public_order_student_id
 join public.landerware_public_orders o on o.id=st.order_id
 join public.registrations r on r.id=st.registration_id and r.id=u.reserved_for_registration_id
 where d.id=p_delivery_id and d.lease=p_lease and d.provider='resend'
 and d.prepared_at is not null and u.exposed_at is not null
 and d.provider_id ~ '^[A-Za-z0-9_-]{1,128}$'
 and d.state in ('processing','ambiguous','accepted','cancelled')
 and lower(trim(st.email))=d.recipient and o.checkout_runtime_version='native-v1'
 and r.class_session_id=o.class_session_id
 and p.fulfillment_mode='digital_code' and nullif(trim(u.secret_value),'') is not null
 and exists(select 1 from jsonb_array_elements(st.selected_addons) a where a->>'product_id'=p.id::text and a->>'inventory_required'='true')
 and not exists(select 1 from public.native_learner_code_delivery other
  where other.provider='resend' and other.provider_id=d.provider_id and other.id<>d.id));
$$;
create function public.native_learner_code_receipt_context(p_delivery_id uuid,p_lease uuid) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare d public.native_learner_code_delivery;
begin
 select * into d from public.native_learner_code_delivery where id=p_delivery_id;
 if d.id is null or d.lease is distinct from p_lease or d.provider<>'resend' or d.provider_id is null then
  return jsonb_build_object('blocked',true,'reason','receipt_unavailable'); end if;
 if not public.native_learner_code_receipt_identity(p_delivery_id,p_lease) then
  return jsonb_build_object('blocked',true,'reason','assignment_mismatch'); end if;
 return (select jsonb_build_object('deliveryId',d.id,'lease',d.lease,'provider','resend','providerId',d.provider_id,
 'recipient',d.recipient,'product',p.product_key,'code',u.secret_value,'preparedAt',d.prepared_at)
 from public.product_inventory_units u join public.products p on p.id=u.product_id where u.id=d.unit_id);
end $$;

-- Owner handler resolves its exact delivery UUID to the current private lease.
-- No caller-supplied lease or receipt is accepted by that handler.
create function public.native_learner_code_receipt_target(p_delivery_id uuid) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare d public.native_learner_code_delivery;
begin
 select * into d from public.native_learner_code_delivery where id=p_delivery_id;
 if d.id is null or not public.native_learner_code_receipt_identity(d.id,d.lease) then
  return jsonb_build_object('blocked',true); end if;
 return jsonb_build_object('deliveryId',d.id,'lease',d.lease);
end $$;
revoke all on function public.native_learner_code_receipt_target(uuid) from public,anon,authenticated;
grant execute on function public.native_learner_code_receipt_target(uuid) to service_role;

-- Only the authenticated server verifier may call this RPC after a successful
-- fixed-endpoint provider GET and exact identity/body verification. An HTTP
-- caller must never supply these evidence fields. DB rechecks identity and code
-- digest after the network round trip. It does not authenticate Resend itself.
create function public.native_reconcile_learner_code_receipt(
 p_delivery_id uuid,p_lease uuid,p_provider_id text,p_recipient text,p_product_key text,
 p_code_sha256 text,p_provider_created_at timestamptz,p_status text
) returns jsonb language plpgsql security invoker set search_path='' as $$
declare d public.native_learner_code_delivery;u public.product_inventory_units;st public.landerware_public_order_students;e public.native_learner_code_receipt_evidence;
begin
 if p_status is null or p_status not in ('sent','delivered','delivery_delayed','bounced','failed','complained','suppressed','opened','clicked')
 or p_code_sha256 is null or p_code_sha256 !~ '^[0-9a-f]{64}$' then raise exception 'invalid_receipt_evidence'; end if;
 select * into d from public.native_learner_code_delivery where id=p_delivery_id for update;
 if d.id is null or d.lease is distinct from p_lease or d.provider<>'resend'
 or d.provider_id is null or d.provider_id is distinct from p_provider_id then raise exception 'receipt_binding_mismatch'; end if;
 -- Locks serialize assignment changes with the final identity verification.
 perform 1 from public.landerware_public_orders o join public.landerware_public_order_students s on s.order_id=o.id where s.id=d.student_id for update of o,s;
 select * into st from public.landerware_public_order_students where id=d.student_id;
 perform 1 from public.registrations where id=st.registration_id for update;
 select * into u from public.product_inventory_units where id=d.unit_id for update;
 perform 1 from public.products where id=u.product_id for share;
 if not public.native_learner_code_receipt_identity(p_delivery_id,p_lease)
 or d.recipient is distinct from p_recipient
 or (select product_key from public.products where id=u.product_id) is distinct from p_product_key
 or encode(sha256(convert_to(u.secret_value,'UTF8')),'hex') is distinct from p_code_sha256
 or p_provider_created_at is null or not isfinite(p_provider_created_at)
 or p_provider_created_at<d.prepared_at or p_provider_created_at>clock_timestamp()+interval '5 minutes'
 then raise exception 'receipt_identity_mismatch'; end if;
 select * into e from public.native_learner_code_receipt_evidence where delivery_id=d.id for update;
 if e.delivery_id is not null and (e.lease is distinct from p_lease or e.provider_id is distinct from p_provider_id or e.provider_created_at is distinct from p_provider_created_at)
 then raise exception 'receipt_evidence_conflict'; end if;
 insert into public.native_learner_code_receipt_evidence(delivery_id,lease,provider,provider_id,provider_created_at,last_status,delivered_observed_at,adverse_status)
 values(d.id,p_lease,'resend',p_provider_id,p_provider_created_at,p_status,
 case when p_status='delivered' then clock_timestamp() else null end,
 case when p_status in ('bounced','failed','complained','suppressed') then p_status else null end)
 on conflict(delivery_id) do update set last_status=excluded.last_status,last_verified_at=clock_timestamp(),
 delivered_observed_at=coalesce(public.native_learner_code_receipt_evidence.delivered_observed_at,excluded.delivered_observed_at),
 adverse_status=coalesce(public.native_learner_code_receipt_evidence.adverse_status,excluded.adverse_status)
 returning * into e;
 -- Preserve the business status (including cancellation/refund). This is only
 -- transport receipt reconciliation; no code exposure, assignment or fulfillment
 -- field is changed, and no global proof is created.
 if p_status in ('sent','delivered','delivery_delayed','opened','clicked') then
  update public.native_learner_code_delivery set state='accepted',error_code=null,retry_at=null where id=d.id;
 end if;
 return jsonb_build_object('verified',true,'status',p_status,
 'actualDeliveryConfirmed',e.delivered_observed_at is not null and e.adverse_status is null);
end $$;
revoke all on function public.native_learner_code_receipt_identity(uuid,uuid) from public,anon,authenticated;
grant execute on function public.native_learner_code_receipt_identity(uuid,uuid) to service_role;
revoke all on function public.native_learner_code_receipt_context(uuid,uuid) from public,anon,authenticated;
grant execute on function public.native_learner_code_receipt_context(uuid,uuid) to service_role;
revoke all on function public.native_reconcile_learner_code_receipt(uuid,uuid,text,text,text,text,timestamptz,text) from public,anon,authenticated;
grant execute on function public.native_reconcile_learner_code_receipt(uuid,uuid,text,text,text,text,timestamptz,text) to service_role;
create or replace function public.native_learner_code_health() returns jsonb
language plpgsql volatile security invoker set search_path='' as $$
declare cfg public.native_learner_code_runtime; pending integer; faults integer; accepted integer; oldest timestamptz; checked_at timestamptz:=clock_timestamp(); confirmed integer; adverse integer;
begin
 select * into cfg from public.native_learner_code_runtime where id;
 select count(*),min(o.paid_at) into pending,oldest from public.product_inventory_units u
 join public.landerware_public_order_students st on st.id=u.public_order_student_id
 join public.landerware_public_orders o on o.id=st.order_id
 left join public.native_learner_code_delivery d on d.unit_id=u.id
 where public.native_learner_code_eligible(u.id,st.id,lower(trim(st.email))) and (d.id is null or d.state='cancelled' or (d.provider<>'resend' and d.state<>'accepted'));
 select count(*) filter(where state in ('ambiguous','processing','rejected')),
 count(*) filter(where state='accepted') into faults,accepted from public.native_learner_code_delivery where provider='resend';
 select count(*) filter(where e.delivered_observed_at is not null and e.adverse_status is null),count(*) filter(where e.adverse_status is not null) into confirmed,adverse
 from public.native_learner_code_receipt_evidence e join public.native_learner_code_delivery d on d.id=e.delivery_id and d.provider=e.provider and d.provider_id=e.provider_id and d.lease=e.lease;
 faults:=faults+adverse;
 return jsonb_build_object('enabled',coalesce(cfg.enabled,false),'provider','resend','configured',coalesce(cfg.configured,false),'proven',coalesce(cfg.proven,false),
 'unclaimedEligible',pending,'oldestUnclaimedAt',oldest,'unresolvedFaults',faults+case when cfg.fault then 1 else 0 end,'accepted',accepted,
 'healthy',coalesce(cfg.enabled and cfg.configured and cfg.proven and not cfg.fault and cfg.last_poll_at>checked_at-interval '3 minutes' and cfg.last_poll_at<=checked_at and cfg.last_completed_at>checked_at-interval '3 minutes' and cfg.last_completed_at<=checked_at and faults=0 and pending=0,false),
 'deliveryConfirmed',confirmed,'deliveryFailures',adverse,'deliveryUnconfirmed',greatest(accepted-confirmed,0),'actualDeliveryConfirmed',false,'lastPollAt',cfg.last_poll_at,'lastCompletedAt',cfg.last_completed_at,
 'pollFresh',coalesce(cfg.last_poll_at>checked_at-interval '3 minutes' and cfg.last_poll_at<=checked_at,false),'completionFresh',coalesce(cfg.last_completed_at>checked_at-interval '3 minutes' and cfg.last_completed_at<=checked_at,false));
end $$;
commit;
