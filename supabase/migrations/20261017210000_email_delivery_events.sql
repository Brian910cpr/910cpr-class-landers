-- Delivery evidence is separate from the outbox's provider-acceptance receipt.
create table if not exists public.landerware_email_delivery_events (
 event_id text primary key check(length(event_id) between 1 and 256),
 provider_message_id text not null check(length(provider_message_id) between 1 and 256),
 recipient text not null check(length(recipient) between 1 and 320),
 status text not null check(status in ('delivered','deferred','bounced','failed','rejected','complained')),
 event_at timestamptz not null,
 detail text,
 created_at timestamptz not null default now()
);
create index if not exists landerware_email_delivery_lookup
 on public.landerware_email_delivery_events(provider_message_id,recipient,event_at desc);
alter table public.landerware_email_delivery_events enable row level security;
revoke all on public.landerware_email_delivery_events from public,anon,authenticated;

create or replace function public.landerware_record_email_delivery_event(p_token text,p_event jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare state text; event_time timestamptz;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 if p_event#>>'{source,domain}' is distinct from 'notify.910cpr.com'
   or p_event#>>'{source,type}' is distinct from 'email.sending'
   or p_event#>>'{metadata,accountId}' is distinct from '9acb24ab8037cc5abe5518f7758455fd'
   or p_event#>>'{source,zoneId}' is distinct from 'dafc32f545bccb5fae2ff6f94cec92df'
   then raise exception 'invalid_email_event_source'; end if;
 state:=p_event#>>'{payload,delivery,status}';
 if state not in ('delivered','deferred','bounced','failed','rejected','complained')
   or state is null or p_event->>'type' is distinct from 'cf.email.sending.message.'||state
   then raise exception 'invalid_email_event_type'; end if;
 event_time:=(p_event#>>'{metadata,eventTimestamp}')::timestamptz;
 if event_time is null or event_time>now()+interval '5 minutes' then raise exception 'invalid_email_event_time'; end if;
 insert into public.landerware_email_delivery_events(event_id,provider_message_id,recipient,status,event_at,detail)
 values(p_event#>>'{payload,eventId}',trim(both '<>' from p_event#>>'{payload,messageId}'),
   lower(p_event#>>'{payload,recipient}'),state,event_time,
   left(coalesce(p_event#>>'{payload,bounce,reason}',p_event#>>'{payload,failure,reason}',p_event#>>'{payload,rejection,detail}',p_event#>>'{payload,delivery,smtpResponse}'),1000))
 on conflict(event_id) do nothing;
 return jsonb_build_object('recorded',true);
end $$;
revoke all on function public.landerware_record_email_delivery_event(text,jsonb) from public;
grant execute on function public.landerware_record_email_delivery_event(text,jsonb) to anon,service_role;

-- Joining on provider receipt also handles events arriving before outbox settlement.
create or replace view public.landerware_message_history with(security_invoker=true) as
select m.*,e.status as provider_delivery_status,e.event_at as provider_event_at,case when e.status<>'delivered' then e.detail else null end as provider_failure_detail,
 case when m.suppressed_at is not null then 'suppressed'
   when e.status is not null then e.status
   when m.delivery_status='pending' and m.scheduled_for>now() then 'scheduled'
   else m.delivery_status end as effective_status
from public.landerware_messages m
left join lateral (
 select ev.status,ev.event_at,ev.detail from public.landerware_email_delivery_events ev
 where ev.provider_message_id=trim(both '<>' from m.provider_message_id)
   and ev.recipient=lower(m.recipient) and m.delivery_provider='cloudflare'
 order by (ev.status='complained') desc,(ev.status<>'deferred') desc,ev.event_at desc,ev.event_id desc limit 1
) e on true;
revoke all on public.landerware_message_history from public,anon,authenticated;
grant select on public.landerware_message_history to service_role;


-- Supersede acceptance-only health after the provider evidence view exists.
create or replace function public.landerware_checkout_confirmation_health(p_token text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare cfg public.landerware_checkout_delivery_config%rowtype; stuck integer; failures integer; late integer; queued integer; recovery_queued integer; recovery_late integer; delivery_failures integer; delivery_unconfirmed integer;
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

 -- Acceptance is not delivery. Use the same recipient-bound provider evidence
 -- as owner message history; never resend an accepted message to repair health.
 select count(*) filter(where m.provider_delivery_status in ('bounced','failed','rejected','complained')),
   count(*) filter(where (m.provider_delivery_status is null or m.provider_delivery_status='deferred')
     and coalesce(m.sent_at,a.claimed_at)<now()-interval '10 minutes')
 into delivery_failures,delivery_unconfirmed
 from public.landerware_message_history m
 join public.landerware_checkout_delivery_attempts a on a.message_id=m.id and a.state='sent'
 where m.delivery_provider='cloudflare' and m.created_at>=cfg.not_before and m.suppressed_at is null
   and exists(select 1 from public.landerware_public_orders o
     join public.landerware_public_order_students st on st.order_id=o.id
     where o.course_id=any(cfg.course_ids) and (
       m.idempotency_key='public-order-paid:'||o.id::text||':'||st.email
       or m.idempotency_key='public-order-recovery:'||o.id::text
       or m.idempotency_key='public-order-fulfillment:'||o.id::text
       or (m.template_key='retail-class-reminder-24h-v1' and m.operational_registration_id=st.registration_id)));
 return jsonb_build_object('enabled',cfg.enabled,'lastPollAt',cfg.last_poll_at,'lastAcceptedAt',cfg.last_accepted_at,
 'deliveryFailures',delivery_failures,'deliveryUnconfirmed',delivery_unconfirmed,'stuck',stuck,'failures',failures,'queued',queued,'late',late,'observerFresh',coalesce(cfg.last_poll_at>now()-interval '3 minutes',false),
 'healthy',cfg.enabled and coalesce(cfg.last_poll_at>now()-interval '3 minutes',false) and stuck=0 and failures=0 and late=0 and delivery_failures=0 and delivery_unconfirmed=0);
end $$;
