-- Run only inside an outer transaction that is rolled back.
do $test$
declare
  v_course uuid;
  v_instructor uuid;
  v_location uuid;
  v_org uuid;
  v_s1 uuid := gen_random_uuid();
  v_s2 uuid := gen_random_uuid();
  v_s3 uuid := gen_random_uuid();
  v_a jsonb;
  v_b jsonb;
  v_move jsonb;
  v_customer uuid;
  v_registration uuid;
  v_order uuid;
  v_item uuid;
  v_completion uuid;
  v_credential uuid;
  v_ambiguous jsonb;
  v_corp jsonb;
  v_walkin jsonb;
  v_batch uuid;
begin
  select id into v_course from public.courses order by created_at limit 1;
  if v_course is null then raise exception 'fixture requires one canonical course'; end if;
  select id into v_instructor from public.people order by created_at limit 1;
  select id into v_location from public.locations order by created_at limit 1;
  if v_instructor is null or v_location is null then
    raise exception 'fixture requires one canonical instructor and location';
  end if;
  insert into public.organizations(organization_key,name)
    values('lifecycle-test-'||v_s1,'Lifecycle Test Organization') returning id into v_org;
  insert into public.class_sessions(
    id,source,status,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,
    lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status
  ) values
    (v_s1,'lifecycle_test','scheduled',v_course,now()+interval '10 days',now()+interval '10 days 3 hours','America/New_York',now()+interval '10 days',now()+interval '10 days 3 hours',v_instructor,v_location,12,'landerware','private','open'),
    (v_s2,'lifecycle_test','scheduled',v_course,now()+interval '20 days',now()+interval '20 days 3 hours','America/New_York',now()+interval '20 days',now()+interval '20 days 3 hours',v_instructor,v_location,12,'landerware','private','open'),
    (v_s3,'lifecycle_test','scheduled',v_course,now()+interval '30 days',now()+interval '30 days 3 hours','America/New_York',now()+interval '30 days',now()+interval '30 days 3 hours',v_instructor,v_location,12,'landerware','private','open');

  v_a := public.register_participant(
    'test-enrollware-1','enrollware',v_s1,
    '{"first_name":"Lifecycle","last_name":"Replay","email":"lifecycle-replay@example.invalid","registration_status":"confirmed"}',
    '{"label":"test"}',null,
    '{"source_system":"enrollware","source_identity":"person-1","registration_identity":"registration-1","confidence":1}',
    '[{"key":"online_prerequisite","type":"course_prerequisite","state":"satisfied"}]',
    '{"status":"paid","currency":"usd","course_amount":100,"materials_amount":20,"total_amount":120,
      "items":[{"source_item_key":"manual-1","item_type":"material","description":"Current manual","quantity":1,"unit_amount":20,"total_amount":20,"fulfillment_status":"fulfilled"}]}',
    'first import',null
  );
  v_b := public.register_participant(
    'test-enrollware-1','enrollware',v_s1,
    '{"first_name":"Changed","last_name":"Ignored","email":"lifecycle-replay@example.invalid","registration_status":"canceled"}',
    '{"label":"test"}',null,
    '{"source_system":"enrollware","source_identity":"person-1","registration_identity":"registration-1","confidence":1}',
    '[]',null,'replay',null
  );
  if not (v_b->>'idempotent_replay')::boolean then raise exception 'registration replay was not idempotent'; end if;
  if v_a->>'customer_id' <> v_b->>'customer_id' or v_a->>'registration_id' <> v_b->>'registration_id' then
    raise exception 'replay changed canonical identity';
  end if;
  v_customer := (v_a->>'customer_id')::uuid;
  v_registration := (v_a->>'registration_id')::uuid;
  if (select status from public.registrations where id=v_registration) <> 'confirmed' then
    raise exception 'replay overwrote locally authoritative registration status';
  end if;
  if (select state from public.registration_requirements where registration_id=v_registration and requirement_key='online_prerequisite') <> 'satisfied' then
    raise exception 'participant requirement was not preserved';
  end if;
  select id into v_order from public.registration_orders where registration_id=v_registration;
  select id into v_item from public.registration_order_items where order_id=v_order and source_item_key='manual-1';
  if v_order is null or v_item is null then raise exception 'payment/material association missing'; end if;

  v_move := public.move_registration('test-move-1',v_registration,v_s2,'customer requested','admin','{"label":"test"}','transfer');
  if (select registration_id from public.registration_orders where id=v_order) <> (v_move->>'target_registration_id')::uuid then
    raise exception 'order/material attribution did not survive move';
  end if;
  if (select count(*) from public.registration_supersessions where idempotency_key='test-move-1') <> 1 then
    raise exception 'supersession missing';
  end if;
  perform public.move_registration('test-move-1',v_registration,v_s2,'customer requested','admin','{"label":"test"}','transfer');
  if (select count(*) from public.registration_supersessions where idempotency_key='test-move-1') <> 1 then
    raise exception 'move replay duplicated supersession';
  end if;

  v_walkin := public.register_participant(
    'test-walkin-1','instructor_walk_in',v_s1,
    '{"first_name":"Walk","last_name":"In","email":"walkin@example.invalid"}',
    '{"label":"Instructor"}',null,null,'[]',null,'legitimate walk-in',null
  );
  if (select registration_source from public.registrations where id=(v_walkin->>'registration_id')::uuid) <> 'instructor_walk_in' then
    raise exception 'walk-in did not use canonical registration';
  end if;

  v_corp := public.register_participant(
    'test-corporate-1','corporate',v_s1,
    '{"first_name":"Corporate","last_name":"Employee","email":"corp@example.invalid"}',
    '{"label":"Coordinator"}',v_org,
    '{"source_system":"corporate_test","source_identity":"employee-1","confidence":1}',
    '[]',null,null,null
  );
  if (select organization_id from public.customers where id=(v_corp->>'customer_id')::uuid) <> v_org then
    raise exception 'corporate organization was not associated';
  end if;

  insert into public.customers(first_name,last_name,email,phone) values
    ('Similar','One','similar@example.invalid','9105550101'),
    ('Similar','Two','other@example.invalid','9105550102');
  v_ambiguous := public.register_participant(
    'test-ambiguous-1','historical_import',v_s1,
    '{"first_name":"Similar","last_name":"Conflict","email":"similar@example.invalid","phone":"9105550102"}',
    '{"label":"test"}',null,
    '{"source_system":"historical_fixture","source_identity":"ambiguous-1","confidence":0.5}',
    '[]',null,null,null
  );
  if v_ambiguous->>'resolution' <> 'review_required' then raise exception 'conflicting identity did not fail safely'; end if;

  insert into public.participant_completions(
    customer_id,registration_id,class_session_id,course_id,completion_status,completed_at,
    source_system,source_record_identity,recorded_by
  ) values(v_customer,(v_move->>'target_registration_id')::uuid,v_s2,v_course,'passed',now(),
    'test','completion-1','test') returning id into v_completion;
  insert into public.participant_credentials(
    customer_id,registration_id,class_session_id,course_id,completion_id,credential_type,
    credential_number,issued_at,status,source_system,source_record_identity
  ) values(v_customer,(v_move->>'target_registration_id')::uuid,v_s2,v_course,v_completion,'course_card',
    'TEST-CARD',now(),'issued','test','credential-1') returning id into v_credential;
  perform public.move_registration('test-move-completed',(v_move->>'target_registration_id')::uuid,v_s3,
    'renewal scheduling','admin','{"label":"test"}','retain');
  if (select completion_status from public.participant_completions where id=v_completion) <> 'passed'
     or (select status from public.participant_credentials where id=v_credential) <> 'issued'
     or (select status from public.registrations where id=(v_move->>'target_registration_id')::uuid) <> 'confirmed' then
    raise exception 'completed history was overwritten by move';
  end if;

  insert into public.lifecycle_import_batches(
    batch_key,source_system,source_file_identity,parser_version,mode,status,created_by
  ) values('test-batch-1','historical_fixture','fixture.json','test-1','dry_run','prepared','test')
  returning id into v_batch;
  insert into public.lifecycle_import_records(
    batch_id,source_record_id,entity_type,original_values,ambiguity_state,reconciliation_status
  ) values(v_batch,'row-1','registration','{"original":"preserved"}','exact','matched')
  on conflict(batch_id,source_record_id,entity_type) do nothing;
  insert into public.lifecycle_import_records(
    batch_id,source_record_id,entity_type,original_values,ambiguity_state,reconciliation_status
  ) values(v_batch,'row-1','registration','{"original":"replay"}','exact','matched')
  on conflict(batch_id,source_record_id,entity_type) do nothing;
  if (select count(*) from public.lifecycle_import_records where batch_id=v_batch and source_record_id='row-1') <> 1 then
    raise exception 'batch restart duplicated source record';
  end if;
  if (select original_values->>'original' from public.lifecycle_import_records where batch_id=v_batch and source_record_id='row-1') <> 'preserved' then
    raise exception 'batch replay overwrote original source facts';
  end if;

  if (select count(*) from public.participant_lifecycle_events where event_type in ('registered','imported','moved')) < 5 then
    raise exception 'lifecycle events missing';
  end if;
end
$test$;
