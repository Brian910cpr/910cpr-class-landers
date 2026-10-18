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
