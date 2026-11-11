-- Additive in-project transport. This migration never enables delivery, changes
-- course scope/cutoff, installs credentials, queues mail or converts old orders.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
alter table public.landerware_checkout_delivery_config
 add column if not exists provider text not null default 'cloudflare' check(provider in ('cloudflare','resend'));
alter table public.landerware_checkout_delivery_attempts
 add column if not exists provider text not null default 'cloudflare' check(provider in ('cloudflare','resend'));
-- Provider selection and queue leasing share a transaction/row lock. The old
-- bridge remains supported only for its own lane; it cannot refresh native health.
create or replace function public.landerware_claim_checkout_confirmation(p_token text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare cfg public.landerware_checkout_delivery_config%rowtype; msg public.landerware_messages%rowtype; ticket uuid;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 update public.landerware_checkout_delivery_config set last_poll_at=now() where id and provider='cloudflare' returning * into cfg;
 if not found or not cfg.enabled then return jsonb_build_object('disabled',true); end if;
 select m.* into msg from public.landerware_messages m
 join public.landerware_public_order_students st on (m.idempotency_key='public-order-paid:'||st.order_id::text||':'||st.email or m.idempotency_key='public-order-fulfillment:'||st.order_id::text)
 join public.landerware_public_orders o on o.id=st.order_id
 join public.registrations r on r.id=st.registration_id
 join public.class_sessions s on s.id=r.class_session_id
 left join public.landerware_checkout_delivery_attempts a on a.message_id=m.id
 where ((m.template_key='retail-paid-confirmation-v3' and m.recipient=st.email)
   or (m.template_key='retail-addon-fulfillment-v2' and m.recipient='brian@910cpr.com'))
   and m.created_at>=cfg.not_before and o.status='paid' and o.course_id=any(cfg.course_ids)
   and o.payment_evidence->>'payment_status'='paid'
   and st.registration_id is not null
   and r.status in ('registered','confirmed') and s.status in ('scheduled','active')
   and ((m.delivery_status='pending' and a.message_id is null)
     or (m.delivery_status='failed' and a.provider='cloudflare' and a.state='rejected' and a.attempts<5 and a.retry_at<=now()))
 order by m.created_at,m.id for update of m skip locked limit 1;
 if msg.id is null then
  select m.* into msg from public.landerware_messages m
  join public.landerware_public_orders o on m.idempotency_key='public-order-recovery:'||o.id::text
  join public.class_sessions s on s.id=o.class_session_id
  left join public.landerware_checkout_delivery_attempts a on a.message_id=m.id
  where m.template_key='retail-checkout-recovery-v2' and m.recipient=o.payer_email
   and coalesce(to_jsonb(m)->>'suppressed_at','')='' and m.created_at>=cfg.not_before
   and o.course_id=any(cfg.course_ids) and o.status in ('held','checkout_open')
   and o.hold_expires_at>now() and o.reconciliation_error is null
   and s.status in ('scheduled','active') and s.visibility='public'
   and s.registration_status='open' and s.registration_backend='landerware'
   and ((m.delivery_status='pending' and a.message_id is null)
    or (m.delivery_status='failed' and a.provider='cloudflare' and a.state='rejected' and a.attempts<5 and a.retry_at<=now()))
  order by m.created_at,m.id for update of m skip locked limit 1;
 end if;
 if msg.id is null then return jsonb_build_object('empty',true); end if;
 ticket:=gen_random_uuid();
 insert into public.landerware_checkout_delivery_attempts(message_id,lease,state)
 values(msg.id,ticket,'processing') on conflict(message_id) do update
 set lease=excluded.lease,state='processing',attempts=landerware_checkout_delivery_attempts.attempts+1,
 claimed_at=now(),retry_at=null,error_code=null;
 update public.landerware_messages set delivery_provider='cloudflare' where id=msg.id;
 return jsonb_build_object('messageId',msg.id,'lease',ticket,'recipient',msg.recipient,'subject',msg.subject,'body',msg.body_text,
   'customerTemplate',msg.template_key<>'retail-addon-fulfillment-v2','confirmation',case when msg.template_key='retail-checkout-recovery-v2' then public.landerware_checkout_recovery_data(msg.id) else public.landerware_checkout_email_data(msg.id) end);
end $$;

create or replace function public.landerware_settle_checkout_confirmation(
 p_token text,p_message_id uuid,p_lease uuid,p_outcome text,p_provider_id text,p_error text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare a public.landerware_checkout_delivery_attempts%rowtype;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 if p_outcome not in ('sent','rejected','ambiguous') or p_outcome is null then raise exception 'invalid_delivery_outcome'; end if;
 if p_outcome='sent' and nullif(trim(p_provider_id),'') is null then raise exception 'provider_receipt_required'; end if;
 select * into a from public.landerware_checkout_delivery_attempts where message_id=p_message_id for update;
 if a.message_id is null or a.provider<>'cloudflare' or a.lease is distinct from p_lease then raise exception 'invalid_delivery_lease'; end if;
 if a.state='sent' and p_outcome='sent' and a.provider_id=p_provider_id then return jsonb_build_object('replay',true); end if;
 if a.state<>'processing' then raise exception 'delivery_already_settled'; end if;
 update public.landerware_checkout_delivery_attempts set state=p_outcome,provider_id=p_provider_id,
 error_code=left(p_error,100),retry_at=case when p_outcome='rejected' then now()+interval '2 minutes'*attempts else null end
 where message_id=p_message_id;
 update public.landerware_messages set delivery_status=case when p_outcome='sent' then 'sent' else 'failed' end,
 provider_message_id=p_provider_id,sent_at=case when p_outcome='sent' then now() else null end,
 failed_at=case when p_outcome<>'sent' then now() else null end,failure_detail=left(p_error,100)
 where id=p_message_id;
 if p_outcome='sent' then update public.landerware_checkout_delivery_config set last_accepted_at=now() where id; end if;
 return jsonb_build_object('settled',true);
end $$;

create or replace function public.landerware_checkout_confirmation_health(p_token text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare cfg public.landerware_checkout_delivery_config%rowtype; stuck integer; failures integer; late integer; queued integer; recovery_queued integer; recovery_late integer;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 select * into cfg from public.landerware_checkout_delivery_config where id;
 if not cfg.enabled or cfg.provider<>'cloudflare' then return jsonb_build_object('enabled',false,'disabled',true,'healthy',false,'observerFresh',false); end if;
 select count(*) filter(where state='processing' and claimed_at<now()-interval '5 minutes'),
 count(*) filter(where state='ambiguous' or (state='rejected' and attempts>=5)) into stuck,failures
 from public.landerware_checkout_delivery_attempts;
 select count(distinct m.id),count(distinct m.id) filter(where m.created_at<now()-interval '10 minutes') into queued,late
 from public.landerware_messages m
 join public.landerware_public_order_students st on m.idempotency_key='public-order-paid:'||st.order_id::text||':'||st.email
 join public.landerware_public_orders o on o.id=st.order_id
 where m.template_key='retail-paid-confirmation-v3' and m.recipient=st.email
   and m.created_at>=cfg.not_before and o.status='paid' and o.course_id=any(cfg.course_ids)
   and o.payment_evidence->>'payment_status'='paid' and st.registration_id is not null
   and m.delivery_status in ('pending','failed');

 select count(distinct m.id),count(distinct m.id) filter(where m.created_at<now()-interval '10 minutes') into recovery_queued,recovery_late
 from public.landerware_messages m join public.landerware_public_orders o on m.idempotency_key='public-order-recovery:'||o.id::text
 where m.template_key='retail-checkout-recovery-v2' and m.recipient=o.payer_email
  and m.created_at>=cfg.not_before and o.course_id=any(cfg.course_ids) and o.status in ('held','checkout_open')
  and o.hold_expires_at>now() and o.reconciliation_error is null and coalesce(to_jsonb(m)->>'suppressed_at','')=''
  and m.delivery_status in ('pending','failed');
 queued:=queued+recovery_queued; late:=late+recovery_late;
 return jsonb_build_object('enabled',cfg.enabled,'lastPollAt',cfg.last_poll_at,'lastAcceptedAt',cfg.last_accepted_at,
 'stuck',stuck,'failures',failures,'queued',queued,'late',late,'observerFresh',coalesce(cfg.last_poll_at>now()-interval '3 minutes',false),
 'healthy',cfg.enabled and coalesce(cfg.last_poll_at>now()-interval '3 minutes',false) and stuck=0 and failures=0 and late=0);
end $$;

create or replace function public.native_checkout_claim_confirmation(p_order_id uuid default null)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare cfg public.landerware_checkout_delivery_config%rowtype; msg public.landerware_messages%rowtype; ticket uuid;
begin
 update public.landerware_checkout_delivery_config set last_poll_at=now() where id and provider='resend' returning * into cfg;
 if not found or not cfg.enabled then return jsonb_build_object('disabled',true); end if;
 select m.* into msg from public.landerware_messages m
 join public.landerware_public_order_students st on (m.idempotency_key='public-order-paid:'||st.order_id::text||':'||st.email or m.idempotency_key='public-order-fulfillment:'||st.order_id::text)
 join public.landerware_public_orders o on o.id=st.order_id
 join public.registrations r on r.id=st.registration_id
 join public.class_sessions s on s.id=r.class_session_id
 left join public.landerware_checkout_delivery_attempts a on a.message_id=m.id
 where ((m.template_key='retail-paid-confirmation-v3' and m.recipient=st.email)
   or (m.template_key='retail-addon-fulfillment-v2' and m.recipient='brian@910cpr.com'))
   and o.checkout_runtime_version='native-v1' and (p_order_id is null or o.id=p_order_id)
   and r.class_session_id=o.class_session_id
   and m.created_at>=cfg.not_before and o.status='paid' and o.course_id=any(cfg.course_ids)
   and o.payment_evidence->>'payment_status'='paid'
   and st.registration_id is not null
   and r.status in ('registered','confirmed') and s.status in ('scheduled','active')
   and ((m.delivery_status='pending' and a.message_id is null)
     or (m.delivery_status='failed' and a.provider='resend' and a.state='rejected' and a.attempts<5 and a.retry_at<=now()))
 order by m.created_at,m.id for update of m skip locked limit 1;
 if msg.id is null then
  select m.* into msg from public.landerware_messages m
  join public.landerware_public_orders o on m.idempotency_key='public-order-recovery:'||o.id::text
  join public.class_sessions s on s.id=o.class_session_id
  left join public.landerware_checkout_delivery_attempts a on a.message_id=m.id
  where m.template_key='retail-checkout-recovery-v2' and m.recipient=o.payer_email
   and coalesce(to_jsonb(m)->>'suppressed_at','')='' and m.created_at>=cfg.not_before
   and o.checkout_runtime_version='native-v1' and (p_order_id is null or o.id=p_order_id)
   and o.course_id=any(cfg.course_ids) and o.status in ('held','checkout_open')
   and o.hold_expires_at>now() and o.reconciliation_error is null
   and s.status in ('scheduled','active') and s.visibility='public'
   and s.registration_status='open' and s.registration_backend='landerware'
   and ((m.delivery_status='pending' and a.message_id is null)
    or (m.delivery_status='failed' and a.provider='resend' and a.state='rejected' and a.attempts<5 and a.retry_at<=now()))
  order by m.created_at,m.id for update of m skip locked limit 1;
 end if;
 if msg.id is null then return jsonb_build_object('empty',true); end if;
 ticket:=gen_random_uuid();
 insert into public.landerware_checkout_delivery_attempts(message_id,lease,state,provider)
 values(msg.id,ticket,'processing','resend') on conflict(message_id) do update
 set lease=excluded.lease,state='processing',attempts=landerware_checkout_delivery_attempts.attempts+1,
 claimed_at=now(),retry_at=null,error_code=null;
 update public.landerware_messages set delivery_provider='resend' where id=msg.id;
 return jsonb_build_object('messageId',msg.id,'lease',ticket,'recipient',msg.recipient,'subject',msg.subject,'body',msg.body_text,
   'customerTemplate',msg.template_key<>'retail-addon-fulfillment-v2','confirmation',case when msg.template_key='retail-checkout-recovery-v2' then public.landerware_checkout_recovery_data(msg.id) else public.landerware_checkout_email_data(msg.id) end);
end $$;

create or replace function public.native_checkout_settle_confirmation(
 p_message_id uuid,p_lease uuid,p_outcome text,p_provider_id text,p_error text
) returns jsonb language plpgsql security invoker set search_path='' as $$
declare a public.landerware_checkout_delivery_attempts%rowtype;
begin
 if p_outcome not in ('sent','rejected','ambiguous') or p_outcome is null then raise exception 'invalid_delivery_outcome'; end if;
 if p_outcome='sent' and (p_provider_id is null or p_provider_id !~ '^[A-Za-z0-9_-]{1,200}$') then raise exception 'provider_receipt_required'; end if;
 select * into a from public.landerware_checkout_delivery_attempts where message_id=p_message_id for update;
 if a.message_id is null or a.provider<>'resend' or a.lease is distinct from p_lease then raise exception 'invalid_delivery_lease'; end if;
 if a.state='sent' and p_outcome='sent' and a.provider_id=p_provider_id then return jsonb_build_object('replay',true); end if;
 if p_outcome<>'sent' and p_provider_id is not null then raise exception 'invalid_delivery_outcome'; end if;
 if p_error is not null and p_error !~ '^[a-z0-9_]{1,100}$' then raise exception 'invalid_delivery_error'; end if;
 if a.state<>'processing' then raise exception 'delivery_already_settled'; end if;
 update public.landerware_checkout_delivery_attempts set state=p_outcome,provider_id=p_provider_id,
 error_code=left(p_error,100),retry_at=case when p_outcome='rejected' then now()+interval '2 minutes'*attempts else null end
 where message_id=p_message_id;
 update public.landerware_messages set delivery_status=case when p_outcome='sent' then 'sent' else 'failed' end,
 provider_message_id=p_provider_id,sent_at=case when p_outcome='sent' then now() else null end,
 failed_at=case when p_outcome<>'sent' then now() else null end,failure_detail=left(p_error,100)
 where id=p_message_id;
 if p_outcome='sent' then update public.landerware_checkout_delivery_config set last_accepted_at=now() where id; end if;
 return jsonb_build_object('settled',true);
end $$;

create or replace function public.native_checkout_confirmation_health()
returns jsonb language plpgsql security invoker set search_path='' as $$
declare cfg public.landerware_checkout_delivery_config%rowtype; stuck integer; failures integer; late integer; queued integer; recovery_queued integer; recovery_late integer;
begin
 select * into cfg from public.landerware_checkout_delivery_config where id;
 if not cfg.enabled or cfg.provider<>'resend' then return jsonb_build_object('enabled',false,'disabled',true,'healthy',false,'observerFresh',false); end if;
 select count(*) filter(where state='processing' and claimed_at<now()-interval '5 minutes'),
 count(*) filter(where state='ambiguous' or (state='rejected' and attempts>=5)) into stuck,failures
 from public.landerware_checkout_delivery_attempts where provider='resend';
 select count(distinct m.id),count(distinct m.id) filter(where m.created_at<now()-interval '10 minutes') into queued,late
 from public.landerware_messages m
 join public.landerware_public_order_students st on (m.idempotency_key='public-order-paid:'||st.order_id::text||':'||st.email or m.idempotency_key='public-order-fulfillment:'||st.order_id::text)
 join public.landerware_public_orders o on o.id=st.order_id
 where ((m.template_key='retail-paid-confirmation-v3' and m.recipient=st.email) or (m.template_key='retail-addon-fulfillment-v2' and m.recipient='brian@910cpr.com'))
   and o.checkout_runtime_version='native-v1' and m.created_at>=cfg.not_before and o.status='paid' and o.course_id=any(cfg.course_ids)
   and o.payment_evidence->>'payment_status'='paid' and st.registration_id is not null
   and m.delivery_status in ('pending','failed');

 select count(distinct m.id),count(distinct m.id) filter(where m.created_at<now()-interval '10 minutes') into recovery_queued,recovery_late
 from public.landerware_messages m join public.landerware_public_orders o on m.idempotency_key='public-order-recovery:'||o.id::text
 where m.template_key='retail-checkout-recovery-v2' and m.recipient=o.payer_email
  and o.checkout_runtime_version='native-v1' and m.created_at>=cfg.not_before and o.course_id=any(cfg.course_ids) and o.status in ('held','checkout_open')
  and o.hold_expires_at>now() and o.reconciliation_error is null and coalesce(to_jsonb(m)->>'suppressed_at','')=''
  and m.delivery_status in ('pending','failed');
 queued:=queued+recovery_queued; late:=late+recovery_late;
 return jsonb_build_object('enabled',cfg.enabled,'provider',cfg.provider,'lastPollAt',cfg.last_poll_at,'lastAcceptedAt',cfg.last_accepted_at,
 'stuck',stuck,'failures',failures,'queued',queued,'late',late,'observerFresh',coalesce(cfg.last_poll_at>now()-interval '3 minutes',false),
 'healthy',cfg.enabled and coalesce(cfg.last_poll_at>now()-interval '3 minutes',false) and stuck=0 and failures=0 and late=0);
end $$;
-- Explicitly preserve the existing hosted service-role helper access so a clean
-- environment does not depend on installation-specific default privileges.
grant execute on function public.landerware_checkout_email_data(uuid),
 public.landerware_checkout_recovery_data(uuid) to service_role;

-- No new public authority. These invoker functions require the existing private
-- server service role and its existing table permissions.
revoke all on function public.native_checkout_claim_confirmation(uuid),
 public.native_checkout_settle_confirmation(uuid,uuid,text,text,text),
 public.native_checkout_confirmation_health() from public,anon,authenticated;
grant execute on function public.native_checkout_claim_confirmation(uuid),
 public.native_checkout_settle_confirmation(uuid,uuid,text,text,text),
 public.native_checkout_confirmation_health() to service_role;
commit;
