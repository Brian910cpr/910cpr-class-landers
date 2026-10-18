alter table public.landerware_messages
 add column if not exists scheduled_for timestamptz,
 add column if not exists suppressed_at timestamptz,
 add column if not exists suppression_reason text;

-- Owner-approved rule: one email 24 hours before class, skipped for late registration.
-- Scope is verified native paid orders after the configured production cutover.
create or replace function public.landerware_prepare_checkout_reminders(p_token text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare cfg public.landerware_checkout_delivery_config%rowtype; added integer; suppressed integer;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 select * into cfg from public.landerware_checkout_delivery_config where id;
 if not cfg.enabled then return jsonb_build_object('disabled',true); end if;
 -- Do not leave obsolete recovery requests appearing ready to send forever.
 update public.landerware_messages m set suppressed_at=now(),suppression_reason='Checkout paid, closed, or hold expired'
 from public.landerware_public_orders o
 where m.template_key='retail-checkout-recovery-v2' and m.idempotency_key='public-order-recovery:'||o.id::text
   and m.created_at>=cfg.not_before and m.suppressed_at is null and m.delivery_status in ('pending','failed')
   and (o.status not in ('held','checkout_open') or o.hold_expires_at<=now())
   and not exists(select 1 from public.landerware_checkout_delivery_attempts a where a.message_id=m.id and a.state in ('processing','sent','ambiguous'));
 update public.landerware_messages m set suppressed_at=now(),suppression_reason='Registration canceled, class changed, or class started'
 from public.registrations r join public.class_sessions s on s.id=r.class_session_id
 where m.operational_registration_id=r.id and m.template_key='retail-class-reminder-24h-v1'
   and m.delivery_status in ('pending','failed') and m.suppressed_at is null
   and (r.status not in ('registered','confirmed') or s.status not in ('scheduled','active')
     or s.start_at<=now() or m.scheduled_for is distinct from s.start_at-interval '24 hours')
   and not exists(select 1 from public.landerware_checkout_delivery_attempts a where a.message_id=m.id and a.state in ('processing','sent','ambiguous'));
 get diagnostics suppressed=row_count;
 insert into public.landerware_messages(template_key,channel,recipient,subject,body_text,
   delivery_provider,delivery_status,idempotency_key,customer_id,operational_registration_id,scheduled_for)
 select 'retail-class-reminder-24h-v1','email',st.email,'Class reminder — '||c.name,
   'Reminder for your upcoming class: '||c.name||E'.\n'||to_char(s.start_at at time zone 'America/New_York','FMMonth DD, YYYY HH12:MI AM')||E' America/New_York\n'||coalesce(l.name,'Location not recorded')||E'\n'||concat_ws(', ',nullif(l.address_line1,''),nullif(l.address_line2,''),nullif(l.city,''),nullif(l.state,''),nullif(l.postal_code,''))||E'\nQuestions or changes? Call 910-395-5193.',
   'cloudflare','pending','class-reminder-24h:'||r.id||':'||extract(epoch from s.start_at)::text,
   r.customer_id,r.id,s.start_at-interval '24 hours'
 from public.landerware_public_orders o
 join public.landerware_public_order_students st on st.order_id=o.id
 join public.registrations r on r.id=st.registration_id
 join public.class_sessions s on s.id=r.class_session_id
 join public.courses c on c.id=s.course_id
 left join public.locations l on l.id=s.location_id
 where o.status='paid' and o.paid_at>=cfg.not_before and o.course_id=any(cfg.course_ids)
   and o.payment_evidence->>'payment_status'='paid'
   and r.status in ('registered','confirmed') and s.status in ('scheduled','active')
   and r.registration_source='landerware_native_checkout' and s.registration_backend='landerware'
   and r.created_at<=s.start_at-interval '24 hours' and s.start_at>now()
 on conflict(idempotency_key) do nothing;
 get diagnostics added=row_count;
 return jsonb_build_object('scheduled',added,'suppressed',suppressed);
end $$;
revoke all on function public.landerware_prepare_checkout_reminders(text) from public;
grant execute on function public.landerware_prepare_checkout_reminders(text) to anon,service_role;

create or replace function public.landerware_claim_checkout_confirmation(p_token text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare cfg public.landerware_checkout_delivery_config%rowtype; msg public.landerware_messages%rowtype; ticket uuid;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 update public.landerware_checkout_delivery_config set last_poll_at=now() where id returning * into cfg;
 if not cfg.enabled then return jsonb_build_object('disabled',true); end if;
 select m.* into msg from public.landerware_messages m
 join public.landerware_public_order_students st on (m.idempotency_key='public-order-paid:'||st.order_id::text||':'||st.email or m.idempotency_key='public-order-fulfillment:'||st.order_id::text or (m.template_key='retail-class-reminder-24h-v1' and m.operational_registration_id=st.registration_id))
 join public.landerware_public_orders o on o.id=st.order_id
 join public.registrations r on r.id=st.registration_id join public.class_sessions s on s.id=r.class_session_id left join public.landerware_checkout_delivery_attempts a on a.message_id=m.id
 where ((m.template_key in ('retail-paid-confirmation-v3','retail-class-reminder-24h-v1') and m.recipient=st.email) or (m.template_key='retail-addon-fulfillment-v2' and m.recipient='brian@910cpr.com')) and m.suppressed_at is null and (m.scheduled_for is null or m.scheduled_for<=now()) and (m.template_key in ('retail-paid-confirmation-v3','retail-addon-fulfillment-v2') or (r.status in ('registered','confirmed') and s.status in ('scheduled','active') and s.start_at>now() and m.scheduled_for=s.start_at-interval '24 hours' and r.created_at<=m.scheduled_for))
   and m.created_at>=cfg.not_before and o.status='paid' and o.course_id=any(cfg.course_ids)
   and o.payment_evidence->>'payment_status'='paid'
   and st.registration_id is not null
   and r.status in ('registered','confirmed') and s.status in ('scheduled','active')
   and ((m.delivery_status='pending' and a.message_id is null)
     or (m.delivery_status='failed' and a.state='rejected' and a.attempts<5 and a.retry_at<=now()))
 order by m.created_at,m.id for update of m skip locked limit 1;
 if msg.id is null then ticket:=public.landerware_find_checkout_recovery(cfg.not_before,cfg.course_ids); select * into msg from public.landerware_messages where id=ticket; end if;
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

create or replace function public.landerware_checkout_confirmation_health(p_token text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare cfg public.landerware_checkout_delivery_config%rowtype; stuck integer; failures integer; late integer; queued integer; recovery_queued integer; recovery_late integer;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 select * into cfg from public.landerware_checkout_delivery_config where id;
 if not cfg.enabled then return jsonb_build_object('enabled',false,'disabled',true,'healthy',false,'observerFresh',false); end if;
 select count(*) filter(where state='processing' and claimed_at<now()-interval '5 minutes'),
 count(*) filter(where state='ambiguous' or (state='rejected' and attempts>=5)) into stuck,failures
 from public.landerware_checkout_delivery_attempts;
 select count(distinct m.id),count(distinct m.id) filter(where coalesce(m.scheduled_for,m.created_at)<now()-interval '10 minutes') into queued,late
 from public.landerware_messages m
 join public.landerware_public_order_students st on (m.idempotency_key='public-order-paid:'||st.order_id::text||':'||st.email or m.idempotency_key='public-order-fulfillment:'||st.order_id::text or (m.template_key='retail-class-reminder-24h-v1' and m.operational_registration_id=st.registration_id))
 join public.landerware_public_orders o on o.id=st.order_id
 where ((m.template_key in ('retail-paid-confirmation-v3','retail-class-reminder-24h-v1') and m.recipient=st.email) or (m.template_key='retail-addon-fulfillment-v2' and m.recipient='brian@910cpr.com')) and m.suppressed_at is null and (m.scheduled_for is null or m.scheduled_for<=now())
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


