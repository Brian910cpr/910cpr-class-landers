-- Pool events use the existing durable Resend queue and observer, not a second sender.
-- Messages follow registration/payment lifecycle, not an abandoned checkout.
create table public.pool_event_email_profiles (
 external_class_id text primary key,
 course_label text not null,
 is_bls boolean not null,
 public_url text not null check(public_url like 'https://www.910cpr.com/%')
);
alter table public.pool_event_email_profiles enable row level security;
revoke all on public.pool_event_email_profiles from public,anon,authenticated;
grant all on public.pool_event_email_profiles to service_role;
insert into public.pool_event_email_profiles(external_class_id,course_label,is_bls,public_url) values
 ('nseaswim-pool-family-2027-02-15','Family & Friends CPR',false,'https://www.910cpr.com/pool'),
 ('nseaswim-pool-bls-2027-02-15','AHA BLS Provider',true,'https://www.910cpr.com/poolbls');

create function public.pool_event_email_copy(p_kind text,p_bls boolean,p_first_name text,p_count integer,p_start timestamptz,p_end timestamptz,p_url text)
returns jsonb language plpgsql immutable security invoker set search_path='' as $$
declare title text:=case when p_bls then 'AHA BLS Provider' else 'Family & Friends CPR' end;
 opening text; subject text; details text;
begin
 if p_kind='confirmation' then
  subject:='Registration confirmed: '||title||' at Earl Jackson Pool';
  opening:=case when p_bls then 'Your payment is complete and your AHA BLS Provider registration is confirmed.' else 'Your free Family & Friends CPR registration is confirmed.' end;
 elsif p_kind='day-before' then
  subject:='Reminder & Welcome: '||title||' tomorrow';
  opening:='A friendly reminder and welcome for tomorrow''s community CPR event at Earl Jackson Pool. We''d love to see you if you''re able to join us. Thank you for taking an interest in learning skills that could help save a life.';
 else raise exception 'invalid_pool_email_kind';
 end if;
 details:=title||E'\n'||to_char(p_start at time zone 'America/New_York','FMDay, FMMonth DD, YYYY')||E'\n'||
  to_char(p_start at time zone 'America/New_York','FMHH12:MI AM')||' to '||to_char(p_end at time zone 'America/New_York','FMHH12:MI AM')||
  E' Eastern\nEarl Jackson Pool\n750 Bess Street\nWilmington, NC 28401';
 return jsonb_build_object('subject',subject,'body',
  'Hi '||coalesce(nullif(regexp_replace(p_first_name,E'[\r\n]+',' ','g'),''),'there')||E',\n\n'||opening||E'\n\n'||details||
  E'\n\nPlaces reserved: '||p_count||case when p_count>1 then ' (including you). You are welcome to share these details with the people in your group.' else '.' end||
  E'\n\n'||case when p_bls then 'This is the AHA BLS Provider certification course. Successful course completion is required for an eCard. Please have your current BLS Provider Manual available for class. If you selected an eManual with registration, that selection is recorded with your order.' else 'This free class includes hands-on CPR practice and AED and choking-response skills. It does not issue a certification card.' end||
  E'\n\nWhat to wear: Bring a coat for getting to and from the building, with comfortable lighter layers underneath. The indoor pool area is heated and can feel warm. You will not need a swimsuit.'||
  E'\n\nMeet the partners making this community event possible. We encourage you to visit their pages to learn more about their work and how they support our community:'||
  E'\n\nNSeaSwim Foundation - community swimming and water safety\nhttps://www.nseaswim.com/'||
  E'\n\nThe Mobile Mermaid - Kasia Foltyn, community organizer\nhttps://www.facebook.com/1tallmermaid/'||
  E'\n\nNC Mobile IV Medics - community healthcare partner\nhttps://www.ncmobileivmedics.com/'||
  E'\n\n910CPR LLC - CPR, AED and BLS training\nhttps://www.910cpr.com/'||
  E'\n\nEvent details: '||p_url||
  E'\n\nQuestions or a change of plans? You are welcome to reply to this email or call 910-395-5193. We hope you can join us, and we understand if your plans change.'||
  E'\n\nThank you for being part of our community!\nBrian Ennis\n910CPR\n910-395-5193');
end $$;

create function public.queue_pool_event_emails(p_registration_id uuid)
returns integer language plpgsql security invoker set search_path='' as $$
declare r public.registrations; s public.class_sessions; c public.customers; p public.pool_event_email_profiles;
 kind text; due timestamptz; payload jsonb; message_id uuid; n integer:=0; places integer; now_at timestamptz:=now();
begin
 select * into r from public.registrations where id=p_registration_id;
 if not found or r.status not in ('registered','confirmed','active') or coalesce(r.registration_source,'') not like 'public_landerware_event:%:group:%' then return 0; end if;
 if jsonb_typeof(r.optional_survey->'groupRegistrationIds') is distinct from 'array' then return 0; end if;
 places:=jsonb_array_length(r.optional_survey->'groupRegistrationIds');
 if places<1 or places>30 or not ((r.optional_survey->'groupRegistrationIds') ? r.id::text) then return 0; end if;
 select * into s from public.class_sessions where id=r.class_session_id;
 select * into p from public.pool_event_email_profiles where external_class_id=s.external_class_id;
 if not found or s.status not in ('scheduled','active') or s.start_at<=now_at+interval '1 minute' then return 0; end if;
 if p.is_bls and not exists(select 1 from public.registration_orders o where o.registration_id=r.id and o.status='paid') then return 0; end if;
 select * into c from public.customers where id=r.customer_id;
 if c.email is null or c.email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$' then return 0; end if;
 foreach kind in array array['confirmation','day-before'] loop
  due:=case kind when 'confirmation' then now_at+interval '1 minute' else s.start_at-interval '24 hours' end;
  -- A late registration receives confirmation without an overdue reminder.
  if due<now_at+interval '1 minute' or due>=s.start_at then continue; end if;
  payload:=public.pool_event_email_copy(kind,p.is_bls,c.first_name,places,s.start_at,s.end_at,p.public_url);
  message_id:=null;
  insert into public.landerware_messages(customer_id,operational_registration_id,template_key,channel,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key)
  values(c.id,r.id,'pool-'||kind||'-v1','email',lower(c.email),payload->>'subject',payload->>'body','resend','pending','pool:'||kind||':'||r.id::text)
  on conflict(idempotency_key) do nothing returning id into message_id;
  if message_id is not null then
   insert into public.registration_reschedule_deliveries(message_id,next_attempt_at,snapshot_class_session_id,snapshot_start_at)
   values(message_id,due,s.id,s.start_at);
   n:=n+1;
  end if;
 end loop;
 return n;
end $$;

create function public.queue_pool_event_emails_after_registration()
returns trigger language plpgsql security invoker set search_path='' as $$
begin
 perform public.queue_pool_event_emails(new.id);
 return new;
end $$;
create trigger pool_event_emails_after_registration
 after insert or update of status,optional_survey,class_session_id on public.registrations
 for each row execute function public.queue_pool_event_emails_after_registration();

-- Reuse the existing row-locking/idempotent delivery mechanism. Extra pool guards
-- prevent stale or refunded messages and a late tomorrow reminder being sent.
create function public.cancel_invalid_pool_event_emails()
returns void language plpgsql security invoker set search_path='' as $$
begin
 update public.registration_reschedule_deliveries d set status='cancelled',last_error='pool_email_no_longer_eligible'
 from public.landerware_messages m
 where d.message_id=m.id and m.template_key in ('pool-confirmation-v1','pool-day-before-v1')
  and d.status in ('pending','failed','sending','needs_review') and not exists(
   select 1 from public.registrations r join public.class_sessions s on s.id=r.class_session_id
    join public.pool_event_email_profiles p on p.external_class_id=s.external_class_id
   where r.id=m.operational_registration_id and r.status in ('active','registered','confirmed')
    and s.status in ('active','scheduled') and s.id=d.snapshot_class_session_id and s.start_at=d.snapshot_start_at and s.start_at>now()
    and (not p.is_bls or exists(select 1 from public.registration_orders o where o.registration_id=r.id and o.status='paid'))
    and (m.template_key<>'pool-day-before-v1' or (now() at time zone 'America/New_York')::date < (s.start_at at time zone 'America/New_York')::date)
  );
 update public.landerware_messages m set delivery_status='cancelled'
 from public.registration_reschedule_deliveries d where d.message_id=m.id and d.status='cancelled' and m.delivery_status='pending';
end $$;
revoke all on function public.pool_event_email_copy(text,boolean,text,integer,timestamptz,timestamptz,text),public.queue_pool_event_emails(uuid),public.queue_pool_event_emails_after_registration(),public.cancel_invalid_pool_event_emails() from public,anon,authenticated;
grant execute on function public.pool_event_email_copy(text,boolean,text,integer,timestamptz,timestamptz,text),public.queue_pool_event_emails(uuid),public.queue_pool_event_emails_after_registration(),public.cancel_invalid_pool_event_emails() to service_role;
create or replace function public.claim_reschedule_confirmations(p_registration_id uuid default null)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare claimed jsonb;
begin
 perform public.cancel_invalid_pool_event_emails();
 insert into public.registration_reschedule_deliveries(message_id)
 select m.id from public.landerware_messages m where m.template_key in ('registration-rescheduled-v1','reschedule-help-v1') and m.delivery_status='pending'
 on conflict do nothing;
 -- Previously sent deliveries have no first-attempt field; their old timestamp
 -- remains the conservative bound. Future unsent reminders must not age out.
 update public.registration_reschedule_deliveries set status='needs_review',last_error='delivery_attempt_window_expired'
 where status in ('failed','sending') and coalesce(first_attempt_at,created_at)<now()-interval '23 hours';
 update public.registration_reschedule_deliveries d set status='cancelled',last_error='booking_superseded_or_cancelled'
 from public.landerware_messages m
 where d.message_id=m.id and d.snapshot_class_session_id is not null and d.status in ('pending','failed','sending','needs_review')
 and not exists(select 1 from public.registrations r join public.class_sessions s on s.id=r.class_session_id
  where r.id=m.operational_registration_id and r.status in ('active','registered','confirmed')
   and s.status in ('scheduled','active') and s.id=d.snapshot_class_session_id and s.start_at=d.snapshot_start_at and s.start_at>now());
 update public.landerware_messages m set delivery_status='cancelled'
 from public.registration_reschedule_deliveries d where m.id=d.message_id and d.status='cancelled' and m.delivery_status='pending';
 with candidates as (
  select d.message_id from public.registration_reschedule_deliveries d join public.landerware_messages m on m.id=d.message_id
  where (p_registration_id is null or m.operational_registration_id=p_registration_id) and m.delivery_status<>'sent'
   and ((d.status in ('pending','failed') and d.next_attempt_at<=now()) or (d.status='sending' and d.locked_at<now()-interval '5 minutes'))
  order by d.next_attempt_at,d.created_at limit 10 for update of d skip locked
 ), updated as (
  update public.registration_reschedule_deliveries d set status='sending',attempts=attempts+1,locked_at=now(),first_attempt_at=coalesce(first_attempt_at,now())
  from candidates c where d.message_id=c.message_id returning d.message_id
 ) select coalesce(jsonb_agg(jsonb_build_object('id',m.id,'recipient',m.recipient,'subject',m.subject,'body',m.body_text)),'[]'::jsonb)
 into claimed from updated u join public.landerware_messages m on m.id=u.message_id;
 return claimed;
end $$;



