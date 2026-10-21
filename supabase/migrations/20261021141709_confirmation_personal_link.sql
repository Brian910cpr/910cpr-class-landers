create or replace function public.normal_course_confirmation()
returns trigger language plpgsql security invoker set search_path='' as $$
declare r public.registrations; s public.class_sessions; c public.customers; title text; venue text; instructor text; token text;
begin
 if new.template_key<>'registration-rescheduled-v1' then return new; end if;
 if exists(select 1 from public.landerware_messages where idempotency_key=new.idempotency_key) then return new; end if;
 select * into strict r from public.registrations where id=new.operational_registration_id;
 select * into strict s from public.class_sessions where id=r.class_session_id;
 select * into strict c from public.customers where id=r.customer_id;
 select name into title from public.courses where id=s.course_id;
 select name into venue from public.locations where id=s.location_id;
 select display_name into instructor from public.people where id=s.lead_instructor_id;
 token:='lw_r_'||encode(extensions.gen_random_bytes(32),'hex');
 perform public.issue_registration_reschedule_link(r.id,encode(extensions.digest(token,'sha256'),'hex'),greatest(now()+interval '60 days',s.start_at+interval '30 days'),'Student requested schedule selection');
 new.subject:='Your class is confirmed — '||title;
 new.body_text:='Hi '||c.first_name||E',\n\nYour class is confirmed.\n\n'||title||E'\n'||
 to_char(s.start_at at time zone 'America/New_York','FMDay, FMMonth DD, YYYY at FMHH12:MI AM')||
 '–'||to_char(s.end_at at time zone 'America/New_York','FMHH12:MI AM')||E' Eastern\n'||
 coalesce(venue,s.source_location_label,'Location requires verification')||E'\nInstructor: '||coalesce(instructor,s.source_instructor_label,'910CPR')||
 E'\n\nYour existing registration, payments, and selected materials are recorded with this booking.\n\nChoose a new class time: https://www.910cpr.com/reschedule/#'||token||E'\n\nWe look forward to seeing you!\n\nBrian Ennis\n910CPR\n910-395-5193';
 return new;
end $$;
