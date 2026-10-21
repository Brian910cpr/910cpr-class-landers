-- Reuse the existing delivery worker; future reminders are not due immediately.
alter table public.registration_reschedule_deliveries
 add column if not exists snapshot_class_session_id uuid references public.class_sessions(id),
 add column if not exists snapshot_start_at timestamptz,
 add column if not exists first_attempt_at timestamptz;
alter table public.registration_reschedule_deliveries drop constraint registration_reschedule_deliveries_status_check;
alter table public.registration_reschedule_deliveries add constraint registration_reschedule_deliveries_status_check
 check(status in ('pending','sending','sent','failed','needs_review','cancelled'));

create or replace function public.normal_course_confirmation()
returns trigger language plpgsql security invoker set search_path='' as $$
declare r public.registrations; s public.class_sessions; c public.customers; title text; venue text; instructor text;
begin
 if new.template_key<>'registration-rescheduled-v1' then return new; end if;
 select * into strict r from public.registrations where id=new.operational_registration_id;
 select * into strict s from public.class_sessions where id=r.class_session_id;
 select * into strict c from public.customers where id=r.customer_id;
 select name into title from public.courses where id=s.course_id;
 select name into venue from public.locations where id=s.location_id;
 select display_name into instructor from public.people where id=s.lead_instructor_id;
 new.subject:='Your class is confirmed — '||title;
 new.body_text:='Hi '||c.first_name||E',\n\nYour class is confirmed.\n\n'||title||E'\n'||
 to_char(s.start_at at time zone 'America/New_York','FMDay, FMMonth DD, YYYY at FMHH12:MI AM')||
 '–'||to_char(s.end_at at time zone 'America/New_York','FMHH12:MI AM')||E' Eastern\n'||
 coalesce(venue,s.source_location_label,'Location requires verification')||E'\nInstructor: '||coalesce(instructor,s.source_instructor_label,'910CPR')||
 E'\n\nYour existing registration, payments, and selected materials are recorded with this booking.\n\nWe look forward to seeing you!\n\nBrian Ennis\n910CPR\n910-395-5193';
 return new;
end $$;
create trigger normal_course_confirmation_before_insert before insert on public.landerware_messages
for each row execute function public.normal_course_confirmation();

create or replace function public.schedule_confirmation_followups()
returns trigger language plpgsql security invoker set search_path='' as $$
declare r public.registrations; s public.class_sessions; reminder uuid; owner_message uuid;
begin
 if new.template_key<>'registration-rescheduled-v1' then return new; end if;
 select * into strict r from public.registrations where id=new.operational_registration_id;
 select * into strict s from public.class_sessions where id=r.class_session_id;
 insert into public.registration_reschedule_deliveries(message_id,snapshot_class_session_id,snapshot_start_at)
 values(new.id,s.id,s.start_at) on conflict do nothing;
 -- A reminder already in the past would duplicate the immediate confirmation.
 if s.start_at-interval '48 hours'>now() then
  insert into public.landerware_messages(customer_id,operational_registration_id,template_key,channel,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key)
  values(new.customer_id,r.id,'course-two-day-confirmation-v1','email',new.recipient,new.subject,new.body_text,'resend','pending','two-day:'||new.id)
  on conflict(idempotency_key) do nothing returning id into reminder;
  if reminder is not null then
   insert into public.registration_reschedule_deliveries(message_id,next_attempt_at,snapshot_class_session_id,snapshot_start_at)
   values(reminder,s.start_at-interval '48 hours',s.id,s.start_at);
  end if;
 end if;
 -- Owner receipt is distinct from any instructor notification. Test sessions can
 -- continue suppressing instructor mail without hiding the owner outcome.
 insert into public.landerware_messages(customer_id,operational_registration_id,template_key,channel,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key)
 values(new.customer_id,r.id,'course-owner-confirmation-v1','email','brian@910cpr.com','Student booking confirmed — '||new.subject,
 'Student: '||new.recipient||E'\n\n'||new.body_text,'resend','pending','owner-confirmation:'||new.id)
 on conflict(idempotency_key) do nothing returning id into owner_message;
 if owner_message is not null then
  insert into public.registration_reschedule_deliveries(message_id,snapshot_class_session_id,snapshot_start_at)
  values(owner_message,s.id,s.start_at);
 end if;
 return new;
end $$;
create trigger schedule_confirmation_followups_after_insert after insert on public.landerware_messages
for each row execute function public.schedule_confirmation_followups();

create or replace function public.claim_reschedule_confirmations(p_registration_id uuid default null)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare claimed jsonb;
begin
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
revoke all on function public.normal_course_confirmation(),public.schedule_confirmation_followups() from public,anon,authenticated;
grant execute on function public.normal_course_confirmation(),public.schedule_confirmation_followups() to service_role;
