-- Disposable LOCAL database only. Every mutation in this file rolls back.
begin;
\ir helpers/reschedule-synthetic.sql
do $$
declare v_source jsonb; offer jsonb; options jsonb; answer jsonb; cid text; n integer; before_sessions integer;
 original_order uuid; duplicate uuid; duplicate_session uuid; mirrored public.class_sessions; mirror_customer uuid; public_order uuid;
begin
 foreach cid in array array['209806','359474','209809'] loop
  v_source:=reschedule_test_fixture.registration('dynamic-'||cid,cid);
  offer:=reschedule_test_fixture.offer(cid,cid,30+array_position(array['209806','359474','209809'],cid));
  select count(*) into before_sessions from public.class_sessions;
  options:=public.registration_reschedule_dynamic_targets(v_source->>'token',jsonb_build_array(offer));
  if jsonb_array_length(options)<>1 then raise exception 'TEST: missing dynamic choice %',cid; end if;
  if (options->0->>'capacity')::integer<>case when cid='209806' then 6 else 12 end then raise exception 'TEST: wrong course-specific capacity %',cid; end if;
  if (select count(*) from public.class_sessions)<>before_sessions then raise exception 'TEST: browsing materialized a class'; end if;
  insert into public.registration_orders(registration_id,status,total_amount,course_amount,materials_amount)
   values((v_source->>'registration')::uuid,'paid',85,75,10) returning id into original_order;
  insert into public.registration_requirements(registration_id,requirement_key,requirement_type,state,source,provenance)
   values((v_source->>'registration')::uuid,'manual','material','satisfied','synthetic','{"original":true}');
  insert into public.landerware_public_orders(idempotency_key,external_class_id,class_session_id,course_id,payer_email,status,total)
   values('test-order-'||cid,'test-source:dynamic-'||cid,(v_source->>'session')::uuid,cid,'payer@example.invalid','paid',8500) returning id into public_order;
  insert into public.landerware_public_order_students(order_id,first_name,last_name,email,phone,unit_amount,registration_id,selected_options)
   values(public_order,'Synthetic','Student','test@example.invalid','000',8500,(v_source->>'registration')::uuid,'{"manualChoice":"own-copy"}');
  -- Imported mirror must be retired; no second financial record may be silently lost.
  select * into mirrored from public.class_sessions where id=(v_source->>'session')::uuid;
  insert into public.class_sessions(source,status,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status)
   values('reschedule_test','scheduled',mirrored.course_id,mirrored.start_at,mirrored.end_at,mirrored.consumption_start_at,mirrored.consumption_end_at,mirrored.lead_instructor_id,mirrored.location_id,6,'landerware','unlisted','open') returning id into duplicate_session;
  insert into public.registrations(customer_id,class_session_id,status,registration_source)
   values((v_source->>'customer')::uuid,duplicate_session,'confirmed','reschedule_test') returning id into duplicate;
  answer:=public.confirm_registration_reschedule_dynamic(v_source->>'token',offer);
  if (select count(*) from public.class_sessions)<>before_sessions+2 then raise exception 'TEST: wrong materialization count'; end if;
  if exists(select 1 from public.registrations where id in ((v_source->>'registration')::uuid,duplicate) and status<>'rescheduled') then raise exception 'TEST: source/mirror seat retained'; end if;
  if (select registration_id from public.registration_orders where id=original_order)<>(answer->>'registrationId')::uuid then raise exception 'TEST: financial reference lost'; end if;
  if (select total_amount from public.registration_orders where id=original_order)<>85 then raise exception 'TEST: financial amount changed'; end if;
  if not exists(select 1 from public.landerware_public_order_students where order_id=public_order and registration_id=(answer->>'registrationId')::uuid and selected_options='{"manualChoice":"own-copy"}') then raise exception 'TEST: payer/material references lost'; end if;
  if not exists(select 1 from public.registration_requirements where registration_id=(answer->>'registrationId')::uuid and provenance->>'original'='true' and superseded_from_requirement_id is not null) then raise exception 'TEST: provenance lost'; end if;
  if not exists(select 1 from public.registrations where id=(answer->>'registrationId')::uuid and material_choice='own-copy' and optional_survey='{"synthetic":true}') then raise exception 'TEST: materials/metadata lost'; end if;
  if not (public.confirm_registration_reschedule_dynamic(v_source->>'token',offer)->>'idempotentReplay')::boolean then raise exception 'TEST: replay not idempotent'; end if;
  if (select count(*) from public.registration_supersessions where source_registration_id=(v_source->>'registration')::uuid)<>1 then raise exception 'TEST: duplicate move'; end if;
  if (select count(*) from public.landerware_messages where operational_registration_id=(answer->>'registrationId')::uuid)<>1 then raise exception 'TEST: duplicate mail'; end if;
 end loop;
 -- A late failure from duplicate-finance checking must roll back a newly materialized target.
 v_source:=reschedule_test_fixture.registration('failure','209806',14);offer:=reschedule_test_fixture.offer('failure','209806',40);
 select * into mirrored from public.class_sessions where id=(v_source->>'session')::uuid;
 insert into public.class_sessions(source,status,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status)
  values('reschedule_test','scheduled',mirrored.course_id,mirrored.start_at,mirrored.end_at,mirrored.consumption_start_at,mirrored.consumption_end_at,mirrored.lead_instructor_id,mirrored.location_id,6,'landerware','unlisted','open') returning id into duplicate_session;
 insert into public.registrations(customer_id,class_session_id,status,registration_source) values((v_source->>'customer')::uuid,duplicate_session,'registered','reschedule_test') returning id into duplicate;
 insert into public.registration_orders(registration_id,status,total_amount) values(duplicate,'paid',50);
 select count(*) into before_sessions from public.class_sessions;
 begin
  perform public.confirm_registration_reschedule_dynamic(v_source->>'token',offer);
  raise exception 'TEST: conflicting finance accepted';
 exception when others then if sqlerrm<>'duplicate_financial_record_requires_review' then raise; end if; end;
 if (select count(*) from public.class_sessions)<>before_sessions then raise exception 'TEST: failed transfer left new class'; end if;
 if (select status from public.registrations where id=(v_source->>'registration')::uuid)<>'registered' then raise exception 'TEST: failed transfer changed source'; end if;
 if exists(select 1 from public.registration_reschedule_links where token_sha256=v_source->>'token' and used_at is not null) then raise exception 'TEST: failed transfer consumed link'; end if;
 -- Fail closed for a changed instructor/room and expired exact offer.
 if public.registration_reschedule_dynamic_option((v_source->>'registration')::uuid,offer||'{"instructor":"other"}',null) is not null
  or public.registration_reschedule_dynamic_option((v_source->>'registration')::uuid,offer||'{"resource":"Room C"}',null) is not null
  or public.registration_reschedule_dynamic_option((v_source->>'registration')::uuid,offer||jsonb_build_object('validUntil',now()-interval '1 second'),null) is not null then raise exception 'TEST: invalid offer accepted'; end if;
 if has_function_privilege('anon','public.confirm_registration_reschedule_dynamic(text,jsonb)','execute') then raise exception 'TEST: anonymous materialization permitted'; end if;
 insert into public.instructor_qualifications(instructor_id,course_id,status)
  select p.id,c.id,'revoked' from public.people p cross join public.courses c where p.person_key='brian' and c.enrollware_course_id='209806';
 if public.registration_reschedule_dynamic_option((v_source->>'registration')::uuid,offer,null) is not null then raise exception 'TEST: revoked instructor accepted'; end if;
 delete from public.instructor_qualifications;
 update public.locations set scheduling_status='inactive' where location_key='910cpr-office-shipyard';
 if public.registration_reschedule_dynamic_option((v_source->>'registration')::uuid,offer,null) is not null then raise exception 'TEST: inactive venue accepted'; end if;
 update public.locations set scheduling_status='active' where location_key='910cpr-office-shipyard';
 raise notice 'PASS: three courses, browse read-only, atomic materialization/transfer, finance/provenance/materials, mirror retirement, rollback, replay and access';
end $$;
do $$
declare first_source jsonb; second_source jsonb; offer jsonb; answer jsonb; target uuid; public_order uuid; original_count integer;
begin
 first_source:=reschedule_test_fixture.registration('capacity-a','209806',16);
 second_source:=reschedule_test_fixture.registration('capacity-b','209806',17);
 offer:=reschedule_test_fixture.offer('capacity','209806',45);
 answer:=public.confirm_registration_reschedule_dynamic(first_source->>'token',offer);target:=(answer->>'sessionId')::uuid;
 update public.class_sessions set max_students=1 where id=target;
 if jsonb_array_length(public.registration_reschedule_dynamic_targets(second_source->>'token',jsonb_build_array(offer)))<>0 then raise exception 'TEST: full target listed'; end if;
 begin perform public.confirm_registration_reschedule_dynamic(second_source->>'token',offer);raise exception 'TEST: full target accepted';
 exception when others then if sqlerrm<>'session_not_available' then raise; end if;end;
 update public.class_sessions set max_students=2 where id=target;
 insert into public.landerware_public_orders(idempotency_key,external_class_id,class_session_id,course_id,payer_email,status)
  select 'held-seat',external_class_id,id,'209806','held@example.invalid','held' from public.class_sessions where id=target returning id into public_order;
 insert into public.landerware_public_order_students(order_id,first_name,last_name,email,phone,unit_amount)
  values(public_order,'Synthetic','Held','held@example.invalid','000',0);
 if public.registration_reschedule_dynamic_option((second_source->>'registration')::uuid,offer,null) is not null then raise exception 'TEST: active checkout hold ignored'; end if;
 update public.landerware_public_orders set hold_expires_at=now()-interval '1 second' where id=public_order;
 if public.registration_reschedule_dynamic_option((second_source->>'registration')::uuid,offer,null) is null then raise exception 'TEST: expired hold blocks target'; end if;
 insert into public.landerware_public_session_inventory(external_class_id,capacity,externally_registered,source)
  select external_class_id,2,2,'synthetic' from public.class_sessions where id=target;
 if public.registration_reschedule_dynamic_option((second_source->>'registration')::uuid,offer,null) is not null then raise exception 'TEST: external capacity ignored'; end if;
 delete from public.landerware_public_session_inventory where external_class_id=(select external_class_id from public.class_sessions where id=target);
 select count(*) into original_count from public.class_sessions;
 answer:=public.confirm_registration_reschedule_dynamic(second_source->>'token',offer);
 if (answer->>'sessionId')::uuid<>target or (select count(*) from public.class_sessions)<>original_count then raise exception 'TEST: exact target not reused'; end if;
 -- A stale overlapping alternative must lose even when its external identity differs.
 second_source:=reschedule_test_fixture.registration('overlap','359474',19);
 offer:=reschedule_test_fixture.offer('overlap','359474',45,30);
 if public.registration_reschedule_dynamic_option((second_source->>'registration')::uuid,offer,null) is not null then raise exception 'TEST: cross-course overlap accepted'; end if;
 if exists(select 1 from public.registrations where id=(first_source->>'registration')::uuid and status<>'rescheduled') then raise exception 'TEST: successful source not retired'; end if;
 raise notice 'PASS: target reuse, capacity, checkout holds, expired holds, external occupancy and overlapping alternatives';
end $$;
-- A synthetic closure inside this rollback transaction exercises both the list and confirmation boundary.
create or replace function public.public_registration_closure_policy() returns jsonb language sql stable as $$
 select jsonb_build_object('closures',jsonb_build_array(jsonb_build_object('startsAt',date_trunc('day',now())+interval '46 days',
  'endsAt',date_trunc('day',now())+interval '47 days')));
$$;
do $$
declare v_source jsonb; offer jsonb; before_count integer;
begin
 v_source:=reschedule_test_fixture.registration('closure','209809',18);offer:=reschedule_test_fixture.offer('closure','209809',46);
 select count(*) into before_count from public.class_sessions;
 if public.registration_reschedule_dynamic_option((v_source->>'registration')::uuid,offer,null) is not null then raise exception 'TEST: closure listed'; end if;
 begin perform public.confirm_registration_reschedule_dynamic(v_source->>'token',offer);raise exception 'TEST: closure confirmed';
 exception when others then if sqlerrm<>'session_not_available' then raise; end if;end;
 if (select count(*) from public.class_sessions)<>before_count or (select status from public.registrations where id=(v_source->>'registration')::uuid)<>'registered' then raise exception 'TEST: closure changed source/target'; end if;
 raise notice 'PASS: closure fails closed without changing source or creating target';
end $$;
rollback;
