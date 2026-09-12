-- Run after all migrations against an isolated test database. Every fixture is
-- rolled back. Any failed assertion aborts the script.
begin;

do $$
declare
  v_org uuid;
  v_person uuid;
  v_requirement uuid;
  v_session uuid;
  v_roster uuid;
  v_registration uuid;
  v_membership uuid;
  v_result jsonb;
  v_asserted_at timestamptz := now();
  v_before_messages bigint;
  v_after_messages bigint;
begin
  insert into public.landerware_organizations(display_name) values ('Issue 141 SQL test') returning id into v_org;
  insert into public.landerware_people(current_first_name,current_last_name) values ('Test','Participant') returning id into v_person;
  insert into public.landerware_certification_requirements(person_id,organization_id,course_id,course_name)
    values (v_person,v_org,'issue-141-test','Issue 141 test course') returning id into v_requirement;
  insert into public.landerware_sessions(course_id,course_name,starts_at,ends_at,organization_id,lifecycle_state,provenance,requirements_manifest)
    values ('issue-141-test','Issue 141 test course',now()-interval '3 hours',now()-interval '1 hour',v_org,'completed','sql_test','{}') returning id into v_session;
  insert into public.landerware_rosters(session_id) values (v_session) returning id into v_roster;
  insert into public.landerware_registrations(person_id,requirement_id,session_id,roster_id,organization_id,status,source)
    values (v_person,v_requirement,v_session,v_roster,v_org,'active','system') returning id into v_registration;
  insert into public.landerware_roster_memberships(roster_id,session_id,person_id,registration_id,display_name,source)
    values (v_roster,v_session,v_person,v_registration,'Test Participant','system') returning id into v_membership;

  begin
    perform public.landerware_request_scheduling(v_requirement,null,'explicit_sender_deadline','issue141-request-missing-date');
    raise exception 'expected required_by_required';
  exception when others then
    if sqlerrm <> 'required_by_required' then raise; end if;
  end;

  v_result := public.landerware_request_scheduling(v_requirement,current_date+30,'explicit_sender_deadline','issue141-request-1');
  if (v_result->>'idempotentReplay')::boolean then raise exception 'first request incorrectly marked replay'; end if;
  v_result := public.landerware_request_scheduling(v_requirement,current_date+30,'explicit_sender_deadline','issue141-request-1');
  if not (v_result->>'idempotentReplay')::boolean then raise exception 'request replay was not idempotent'; end if;
  begin
    perform public.landerware_request_scheduling(v_requirement,current_date+31,'explicit_sender_deadline','issue141-request-1');
    raise exception 'expected idempotency_key_payload_conflict';
  exception when others then
    if sqlerrm <> 'idempotency_key_payload_conflict' then raise; end if;
  end;

  begin
    perform public.landerware_assert_attendance(v_membership,'absent','',now(),'authorized_human',null,null,'issue141-absence-no-actor');
    raise exception 'expected attendance_assertion_provenance_required';
  exception when others then
    if sqlerrm <> 'attendance_assertion_provenance_required' then raise; end if;
  end;

  begin
    perform public.landerware_assert_attendance(v_membership,'absent','importer',now(),'attendance_artifact',null,null,'issue141-absence-no-evidence');
    raise exception 'expected attendance_assertion_evidence_required';
  exception when others then
    if sqlerrm <> 'attendance_assertion_evidence_required' then raise; end if;
  end;

  begin
    insert into public.landerware_participant_session_state(roster_membership_id,attendance_status)
      values (v_membership,'absent');
    raise exception 'expected affirmative_attendance_requires_assertion';
  exception when others then
    if sqlerrm <> 'affirmative_attendance_requires_assertion' then raise; end if;
  end;

  select count(*) into v_before_messages from public.landerware_messages;
  v_result := public.landerware_queue_unknown_attendance_closeout(now());
  select count(*) into v_after_messages from public.landerware_messages;
  if v_after_messages <> v_before_messages then raise exception 'unknown attendance created outbound message'; end if;
  if not exists (
    select 1 from public.landerware_participant_session_state
    where roster_membership_id=v_membership and attendance_status='unknown' and closeout_status='instructor_closeout_required'
  ) then raise exception 'passed session did not create internal closeout state'; end if;

  v_result := public.landerware_assert_attendance(v_membership,'absent','authorized-test-user',v_asserted_at,'authorized_human',null,null,'issue141-absence-1');
  if (v_result->>'idempotentReplay')::boolean then raise exception 'first attendance assertion incorrectly marked replay'; end if;
  v_result := public.landerware_assert_attendance(v_membership,'absent','authorized-test-user',v_asserted_at,'authorized_human',null,null,'issue141-absence-1');
  if not (v_result->>'idempotentReplay')::boolean then raise exception 'attendance replay was not idempotent'; end if;
  begin
    perform public.landerware_assert_attendance(v_membership,'present','authorized-test-user',v_asserted_at,'authorized_human',null,null,'issue141-absence-1');
    raise exception 'expected idempotency_key_payload_conflict';
  exception when others then
    if sqlerrm <> 'idempotency_key_payload_conflict' then raise; end if;
  end;
  if (select count(*) from public.landerware_attendance_assertions where idempotency_key='issue141-absence-1') <> 1 then
    raise exception 'attendance replay duplicated assertion';
  end if;
  if (select attendance_status from public.landerware_participant_session_state where roster_membership_id=v_membership) <> 'absent' then
    raise exception 'affirmative attendance fact was not projected';
  end if;
  select count(*) into v_after_messages from public.landerware_messages;
  if v_after_messages <> v_before_messages then raise exception 'attendance assertion created outbound message'; end if;
end;
$$;

rollback;
