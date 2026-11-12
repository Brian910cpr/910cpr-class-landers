-- Provider envelope/validation reused from the existing checkout-owner event contract.
-- Expected source IDs are non-secret policy, not verification of current hosted bindings.
begin;
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
grant select on public.landerware_email_delivery_events to service_role;

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
revoke all on function public.landerware_record_email_delivery_event(text,jsonb) from public,anon,authenticated;
grant execute on function public.landerware_record_email_delivery_event(text,jsonb) to anon,service_role;

-- Read-only projection: never modify inventory, order/registration state or resend.
create or replace view public.native_code_delivery_history with(security_invoker=true) as
select d.*,e.status as provider_delivery_status,e.event_at as provider_event_at,
 coalesce(e.status='delivered',false) as actual_delivery_confirmed
from public.native_learner_code_delivery d
left join lateral (
 select ev.status,ev.event_at from public.landerware_email_delivery_events ev
 where ev.provider_message_id=trim(both '<>' from d.provider_id) and ev.recipient=lower(trim(d.recipient))
 order by (ev.status='complained') desc,(ev.status<>'deferred') desc,ev.event_at desc,ev.event_id desc limit 1
) e on true;
revoke all on public.native_code_delivery_history from public,anon,authenticated;
grant select on public.native_code_delivery_history to service_role;

create or replace function public.landerware_learner_code_health(p_token text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare processing integer; uncertain integer; rejected integer; accepted integer; confirmed integer; unconfirmed integer; failures integer;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 select count(*) filter(where state='processing'),count(*) filter(where state='ambiguous' or (state='processing' and claimed_at<now()-interval '5 minutes')),
 count(*) filter(where state='rejected'),count(*) filter(where state='accepted'),
 count(*) filter(where actual_delivery_confirmed),
 count(*) filter(where state='accepted' and (provider_delivery_status is null or provider_delivery_status='deferred')),
 count(*) filter(where provider_delivery_status in ('bounced','failed','rejected','complained'))
 into processing,uncertain,rejected,accepted,confirmed,unconfirmed,failures from public.native_code_delivery_history;
 return jsonb_build_object('processing',processing,'reviewRequired',uncertain,'rejected',rejected,'accepted',accepted,
 'deliveryConfirmed',confirmed,'deliveryUnconfirmed',unconfirmed,'deliveryFailures',failures,'actualDeliveryConfirmed',false);
end $$;
revoke all on function public.landerware_learner_code_health(text) from public,anon,authenticated;
grant execute on function public.landerware_learner_code_health(text) to service_role,anon;
commit;
