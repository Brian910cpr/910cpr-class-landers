-- Run with the schema inside BEGIN / ROLLBACK. No real registrations are changed.
do $$
declare template public.class_sessions; src uuid:=gen_random_uuid(); dst uuid:=gen_random_uuid(); mirror uuid:=gen_random_uuid(); full_id uuid:=gen_random_uuid();
 customer uuid; reg uuid; mirror_reg uuid; other uuid; answer jsonb; before_count integer; source_order uuid; claim jsonb;
begin
 select * into template from public.class_sessions where record_scope='operational' and lead_instructor_id is not null and course_id is not null and location_id is not null limit 1;
 insert into public.class_sessions(id,source,status,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id)
 select v.id,'reschedule_test','scheduled',template.course_id,v.at,v.at+interval '2 hours','America/New_York',v.at,v.at+interval '2 hours',template.lead_instructor_id,template.location_id,2,'landerware','public','open',v.ext
 from (values(src,now()+interval '10 days','rs-test-source'),(dst,now()+interval '11 days','rs-test-target'),(mirror,now()+interval '10 days','rs-test-mirror'),(full_id,now()+interval '12 days','rs-test-full'))v(id,at,ext);
 insert into public.customers(first_name,last_name,email,phone) values('Synthetic','Transfer','reschedule-test@example.invalid','0000000000') returning id into customer;
 insert into public.registrations(customer_id,class_session_id,status,registration_source,material_choice,optional_survey) values(customer,src,'registered','reschedule_test','own-copy','{"test":true}') returning id into reg;
 insert into public.registrations(customer_id,class_session_id,status,registration_source) values(customer,mirror,'confirmed','reschedule_test') returning id into mirror_reg;
 insert into public.registration_orders(registration_id,status,currency,course_amount,materials_amount,total_amount) values(reg,'paid','usd',75,10,85) returning id into source_order;
 perform public.issue_registration_reschedule_link(reg,repeat('a',64),now()+interval '20 days','Synthetic test');
 -- Unpublished target, a deadline, an unavailable class, and a full class must not move the source.
 begin perform public.confirm_registration_reschedule(repeat('a',64),dst,'{}');raise exception 'TEST: unpublished target accepted';exception when others then if sqlerrm<>'session_not_available' then raise; end if;end;
 update public.registration_reschedule_links set deadline_at=now()+interval '10 days' where token_sha256=repeat('a',64);
 begin perform public.confirm_registration_reschedule(repeat('a',64),dst,array['rs-test-target']);raise exception 'TEST: deadline ignored';exception when others then if sqlerrm<>'session_not_available' then raise; end if;end;
 update public.registration_reschedule_links set deadline_at=null where token_sha256=repeat('a',64);
 insert into public.registration_reschedule_blocks(class_session_id,reason) values(dst,'Synthetic unavailable');
 begin perform public.confirm_registration_reschedule(repeat('a',64),dst,array['rs-test-target']);raise exception 'TEST: blocked target accepted';exception when others then if sqlerrm<>'session_not_available' then raise; end if;end;
 delete from public.registration_reschedule_blocks where class_session_id=dst;
 insert into public.landerware_public_session_inventory(external_class_id,capacity,externally_registered,source) values('rs-test-full',2,2,'reschedule_test');
 begin perform public.confirm_registration_reschedule(repeat('a',64),full_id,array['rs-test-full']);raise exception 'TEST: full target accepted';exception when others then if sqlerrm<>'session_not_available' then raise; end if;end;
 if (select status from public.registrations where id=reg)<>'registered' then raise exception 'TEST: failed move changed source'; end if;
 answer:=public.confirm_registration_reschedule(repeat('a',64),dst,array['rs-test-target']);
 if (select status from public.registrations where id=reg)<>'rescheduled' or (select status from public.registrations where id=mirror_reg)<>'rescheduled' then raise exception 'TEST: duplicate source seats retained'; end if;
 if (select registration_id from public.registration_orders where id=source_order)<>(answer->>'registrationId')::uuid then raise exception 'TEST: payment not transferred'; end if;
 if (select material_choice from public.registrations where id=(answer->>'registrationId')::uuid)<>'own-copy' then raise exception 'TEST: materials lost'; end if;
 if (select optional_survey from public.registrations where id=(answer->>'registrationId')::uuid)<>'{"test":true}'::jsonb then raise exception 'TEST: metadata lost'; end if;
 if (public.confirm_registration_reschedule(repeat('a',64),dst,array['rs-test-target'])->>'idempotentReplay')::boolean is not true then raise exception 'TEST: repeat confirmation not idempotent'; end if;
 if (select count(*) from public.landerware_messages where operational_registration_id=(answer->>'registrationId')::uuid and template_key='registration-rescheduled-v1')<>1 then raise exception 'TEST: duplicate confirmation'; end if;
 begin perform public.confirm_registration_reschedule(repeat('a',64),full_id,array['rs-test-full']);raise exception 'TEST: reused link changed destination';exception when others then if sqlerrm<>'link_already_used' then raise; end if;end;
 -- Independent service role caller cannot access the RPC as an anonymous API role.
 if has_function_privilege('anon','public.confirm_registration_reschedule(text,uuid,text[])','execute') then raise exception 'TEST: anonymous mutation permitted'; end if;
 if has_table_privilege('anon','public.registration_reschedule_links','select') then raise exception 'TEST: anonymous token read permitted'; end if;
 perform public.issue_registration_reschedule_link((answer->>'registrationId')::uuid,repeat('b',64),now()+interval '20 days','Synthetic second move');
 update public.registration_reschedule_links set expires_at=now()-interval '1 second' where token_sha256=repeat('b',64);
 begin perform public.registration_reschedule_context(repeat('b',64));raise exception 'TEST: expired link accepted';exception when others then if sqlerrm<>'invalid_or_expired_link' then raise; end if;end;
 raise notice 'PASS: availability, deadline, blocking, capacity, atomic preservation, mirror retirement, idempotency, expiry, and access control';
end $$;
