-- Disabled until the sender domain, bridge secret and owner-only delivery proof exist.
create table if not exists public.landerware_checkout_delivery_config (
 id boolean primary key default true check(id),
 enabled boolean not null default false,
 token_sha256 text,
 not_before timestamptz not null default now(),
 course_ids text[] not null default array['209806','359474','210549'],
 last_poll_at timestamptz,
 last_accepted_at timestamptz
);
insert into public.landerware_checkout_delivery_config(id) values(true) on conflict do nothing;
create table if not exists public.landerware_checkout_delivery_attempts (
 message_id uuid primary key references public.landerware_messages(id),
 lease uuid not null,
 state text not null check(state in ('processing','sent','rejected','ambiguous')),
 attempts integer not null default 1,
 claimed_at timestamptz not null default now(),
 retry_at timestamptz,
 provider_id text,
 error_code text
);
alter table public.landerware_checkout_delivery_config enable row level security;
alter table public.landerware_checkout_delivery_attempts enable row level security;
revoke all on public.landerware_checkout_delivery_config,public.landerware_checkout_delivery_attempts from public,anon,authenticated;

create or replace function public.landerware_check_checkout_delivery_token(p_token text)
returns void language plpgsql security definer set search_path='' as $$
begin
 if length(coalesce(p_token,''))<32 or not exists(
   select 1 from public.landerware_checkout_delivery_config
   where id and token_sha256=encode(sha256(convert_to(p_token,'UTF8')),'hex')
 ) then raise exception 'delivery_unauthorized'; end if;
end $$;
revoke all on function public.landerware_check_checkout_delivery_token(text) from public,anon,authenticated;

-- Whitelist customer-facing class facts; operational IDs stay in private queue keys.
create or replace function public.landerware_checkout_email_data(p_message_id uuid)
returns jsonb language sql stable set search_path='' as $$
 select jsonb_build_object('kind',case when m.template_key='retail-class-reminder-24h-v1' then 'reminder' else 'confirmation' end,
   'firstName',st.first_name,'course',c.name,'courseId',o.course_id,
   'startsAt',s.start_at,'endsAt',s.end_at,'venue',l.name,
   'address',concat_ws(', ',nullif(l.address_line1,''),nullif(l.address_line2,''),nullif(l.city,''),nullif(l.state,''),nullif(l.postal_code,'')),
   'selectedOptions',st.selected_addons,'selections',st.selected_options)
 from public.landerware_messages m
 join public.landerware_public_order_students st on
   (m.idempotency_key='public-order-paid:'||st.order_id::text||':'||st.email
    or (m.template_key='retail-class-reminder-24h-v1' and to_jsonb(m)->>'operational_registration_id'=st.registration_id::text))
 join public.landerware_public_orders o on o.id=st.order_id
 join public.registrations r on r.id=st.registration_id
 join public.class_sessions s on s.id=r.class_session_id
 join public.courses c on c.id=s.course_id left join public.locations l on l.id=s.location_id
 where m.id=p_message_id and o.status='paid' and o.payment_evidence->>'payment_status'='paid'
   and r.status in ('registered','confirmed') and s.status in ('scheduled','active')
 limit 1;
$$;
revoke all on function public.landerware_checkout_email_data(uuid) from public,anon,authenticated;

create or replace function public.landerware_find_checkout_recovery(p_not_before timestamptz,p_course_ids text[])
returns uuid language sql volatile set search_path='' as $$
 select m.id from public.landerware_messages m
 join public.landerware_public_orders o on m.idempotency_key='public-order-recovery:'||o.id::text
 join public.class_sessions s on s.id=o.class_session_id
 left join public.landerware_checkout_delivery_attempts a on a.message_id=m.id
 where m.template_key='retail-checkout-recovery-v2' and m.recipient=o.payer_email
   and coalesce(to_jsonb(m)->>'suppressed_at','')=''
   and m.created_at>=p_not_before and o.course_id=any(p_course_ids)
   and o.status in ('held','checkout_open') and o.hold_expires_at>now() and o.reconciliation_error is null
   and s.status in ('scheduled','active') and s.visibility='public' and s.registration_status='open' and s.registration_backend='landerware'
   and ((m.delivery_status='pending' and a.message_id is null)
    or (m.delivery_status='failed' and a.state='rejected' and a.attempts<5 and a.retry_at<=now()))
 order by m.created_at,m.id for update of m skip locked limit 1;
$$;
revoke all on function public.landerware_find_checkout_recovery(timestamptz,text[]) from public,anon,authenticated;

create or replace function public.landerware_checkout_recovery_data(p_message_id uuid)
returns jsonb language sql stable set search_path='' as $$
 select jsonb_build_object('kind','recovery','course',c.name,'courseId',o.course_id,
  'startsAt',s.start_at,'endsAt',s.end_at,'venue',l.name,
  'address',concat_ws(', ',nullif(l.address_line1,''),nullif(l.address_line2,''),nullif(l.city,''),nullif(l.state,''),nullif(l.postal_code,'')),
  'recoveryUrl','https://www.910cpr.com/register/?recover='||o.recovery_token::text,'holdExpiresAt',o.hold_expires_at)
 from public.landerware_messages m join public.landerware_public_orders o on m.idempotency_key='public-order-recovery:'||o.id::text
 join public.class_sessions s on s.id=o.class_session_id join public.courses c on c.id=s.course_id
 left join public.locations l on l.id=s.location_id
 where m.id=p_message_id and m.template_key='retail-checkout-recovery-v2' and m.recipient=o.payer_email
  and o.status in ('held','checkout_open') and o.hold_expires_at>now() and o.reconciliation_error is null;
$$;
revoke all on function public.landerware_checkout_recovery_data(uuid) from public,anon,authenticated;

create or replace function public.landerware_claim_checkout_confirmation(p_token text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare cfg public.landerware_checkout_delivery_config%rowtype; msg public.landerware_messages%rowtype; ticket uuid;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 update public.landerware_checkout_delivery_config set last_poll_at=now() where id returning * into cfg;
 if not cfg.enabled then return jsonb_build_object('disabled',true); end if;
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

create or replace function public.landerware_settle_checkout_confirmation(
 p_token text,p_message_id uuid,p_lease uuid,p_outcome text,p_provider_id text,p_error text
) returns jsonb language plpgsql security definer set search_path='' as $$
declare a public.landerware_checkout_delivery_attempts%rowtype;
begin
 perform public.landerware_check_checkout_delivery_token(p_token);
 if p_outcome not in ('sent','rejected','ambiguous') or p_outcome is null then raise exception 'invalid_delivery_outcome'; end if;
 if p_outcome='sent' and nullif(trim(p_provider_id),'') is null then raise exception 'provider_receipt_required'; end if;
 select * into a from public.landerware_checkout_delivery_attempts where message_id=p_message_id for update;
 if a.message_id is null or a.lease<>p_lease then raise exception 'invalid_delivery_lease'; end if;
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
 if not cfg.enabled then return jsonb_build_object('enabled',false,'disabled',true,'healthy',false,'observerFresh',false); end if;
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

revoke all on function public.landerware_claim_checkout_confirmation(text),
 public.landerware_settle_checkout_confirmation(text,uuid,uuid,text,text,text),
 public.landerware_checkout_confirmation_health(text) from public;
grant execute on function public.landerware_claim_checkout_confirmation(text),
 public.landerware_settle_checkout_confirmation(text,uuid,uuid,text,text,text),
 public.landerware_checkout_confirmation_health(text) to anon,service_role;
