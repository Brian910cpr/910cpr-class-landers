-- Only install into a disposable LOCAL database. Explicit fixture values, never production defaults.
create schema skills_test;
insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price)
 values('fixture-skills','Fixture Skills','509474',45,15,2,55),('fixture-qualification','Fixture Qualification','fixture-qualification',45,15,1,55);
insert into people(person_key,display_name) values('skills-test','Fixture Instructor');
insert into locations(location_key,name,scheduling_status) values('910cpr-office-shipyard',':: Wilmington; Shipyard Blvd','active');
insert into instructor_qualifications(instructor_id,course_id,status)
 select p.id,c.id,'active' from people p cross join courses c where p.person_key='skills-test' and c.course_key='fixture-qualification';
insert into skills_session_context_config(context_key,course_id,qualification_course_id,enabled,capacity_policy_verified,policy_evidence)
 select 'cpr-aed',c.id,q.id,true,true,'EXPLICIT DISPOSABLE TEST FIXTURE ONLY' from courses c cross join courses q
 where c.course_key='fixture-skills' and q.course_key='fixture-qualification';
create function skills_test.offer(p_identity text,p_day integer,p_minutes integer default 0) returns jsonb language sql as $$
 with x as (select ((current_date+p_day)::timestamp+interval '10 hours'+make_interval(mins=>p_minutes)) at time zone 'America/New_York' a)
 select jsonb_build_object('kind','dynamic','offerType','dynamic_appointment','courseNumber','509474','context','cpr-aed','selectionId','skills:'||p_identity,
  'startsAt',a,'endsAt',a+interval '45 minutes','consumptionEndsAt',a+interval '60 minutes',
  'localStart',to_char(a at time zone 'America/New_York','YYYY-MM-DD"T"HH24:MI'),'instructor','Fixture Instructor',
  'resource',':: Wilmington; Shipyard Blvd - B','location',':: Wilmington; Shipyard Blvd','availabilityBlockId','fixture',
  'sourceSessionIds','[]'::jsonb,'generatedAt',now(),'validUntil',now()+interval '10 minutes') from x;
$$;
create function skills_test.student(p_n integer) returns jsonb language sql as $$
 select jsonb_build_object('firstName','Fixture','lastName','Student','email','fixture-'||p_n||'@example.invalid','onlineCompleted',true);
$$;
