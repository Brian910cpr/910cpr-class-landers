-- Only load into an empty, disposable localhost database. Contains synthetic records only.
create schema if not exists reschedule_test_fixture;
create table if not exists reschedule_test_fixture.local_only(marker text primary key);
insert into reschedule_test_fixture.local_only values('synthetic localhost fixture') on conflict do nothing;
insert into public.people(person_key,display_name) values('brian','Brian Ennis');
insert into public.locations(location_key,name,scheduling_status) values('910cpr-office-shipyard','Synthetic Shipyard','active');
insert into public.courses(course_key,name,enrollware_course_id,duration_minutes,max_students_default)
 values('aha-bls-provider','Synthetic BLS Initial','209806',120,12),
 ('aha-bls-provider-renewal','Synthetic BLS Renewal','359474',120,12),
 ('aha-heartsaver-fa-cpr-aed','Synthetic Heartsaver FA CPR AED','209809',120,12);

create or replace function reschedule_test_fixture.registration(label text,course_number text,source_day integer default 10)
returns jsonb language plpgsql as $$
declare customer uuid; session uuid; registration uuid; token text:=md5(label)||md5(label); course uuid; instructor uuid; venue uuid;
begin
 select id into course from public.courses where enrollware_course_id=course_number;
 select id into instructor from public.people where person_key='brian';
 select id into venue from public.locations where location_key='910cpr-office-shipyard';
 insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,consumption_start_at,consumption_end_at,
  lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id)
 values('reschedule_test','scheduled','operational',course,date_trunc('day',now())+source_day*interval '1 day',
  date_trunc('day',now())+source_day*interval '1 day'+interval '2 hours',date_trunc('day',now())+source_day*interval '1 day',
  date_trunc('day',now())+source_day*interval '1 day'+interval '150 minutes',instructor,venue,6,'landerware','unlisted','open','test-source:'||label)
 returning id into session;
 insert into public.customers(first_name,last_name,email) values('Synthetic',label,label||'@example.invalid') returning id into customer;
 insert into public.registrations(customer_id,class_session_id,status,registration_source,material_choice,optional_survey)
 values(customer,session,'registered','reschedule_test','own-copy','{"synthetic":true}') returning id into registration;
 perform public.issue_registration_reschedule_link(registration,token,now()+interval '60 days','Synthetic test');
 return jsonb_build_object('registration',registration,'session',session,'customer',customer,'token',token);
end $$;

create or replace function reschedule_test_fixture.offer(label text,course_number text,target_day integer default 30,minute_offset integer default 0)
returns jsonb language sql as $$
 select jsonb_build_object('kind','dynamic','selectionId','dynamic:test:'||label,'courseNumber',course_number,
  'startsAt',s,'endsAt',s+interval '2 hours','consumptionEndsAt',s+interval '150 minutes',
  'localStart',to_char(s at time zone 'America/New_York','YYYY-MM-DD"T"HH24:MI'),
  'generatedAt',now(),'validUntil',now()+interval '10 minutes','availabilityBlockId','synthetic-window',
  'instructor','Brian Ennis','resource',':: Wilmington; Shipyard Blvd - B','location',':: Wilmington; Shipyard Blvd',
  'appointmentDayId','260794','sourceSessionIds','[]'::jsonb,'registrationUrl','https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260794')
 from (select date_trunc('day',now())+target_day*interval '1 day'+minute_offset*interval '1 minute' s) x;
$$;
