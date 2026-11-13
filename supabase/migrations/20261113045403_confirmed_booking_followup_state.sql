alter table public.class_sessions drop constraint class_sessions_operational_fields_check;
alter table public.class_sessions add constraint class_sessions_operational_fields_check check (
record_scope<>'operational' or (end_at is not null and consumption_start_at is not null and consumption_end_at is not null
and (lead_instructor_id is not null or (source='confirmed_booking_intake'
and coalesce(external_session_evidence->>'kind','') in ('registration_confirmation','owner_confirmed_booking')
and nullif(external_session_evidence->>'gmail_message_id','') is not null))));
create or replace function public.record_confirmed_intake(
 p_course_id uuid, p_location_id uuid, p_customer_id uuid, p_starts_at timestamptz,
 p_evidence jsonb, p_workspace_id uuid default null, p_duration_minutes integer default null
) returns jsonb language plpgsql security invoker
set search_path=pg_catalog
as $fn$
declare
 v_course public.courses%rowtype; v_customer public.customers%rowtype;
 v_w public.landerware_sessions%rowtype; v_session uuid; v_workspace uuid; v_registration uuid;
 v_minutes integer; v_matches integer; v_evidence jsonb; v_flags jsonb; v_key text;
begin
 if p_starts_at is null or coalesce(p_evidence->>'kind','')<>'registration_confirmation'
    or nullif(btrim(p_evidence->>'gmail_message_id'),'') is null then
  raise exception 'confirmed_booking_source_required';
 end if;
 select * into strict v_course from public.courses where id=p_course_id;
 select * into strict v_customer from public.customers where id=p_customer_id;
 if nullif(btrim(v_customer.first_name||' '||v_customer.last_name),'') is null
    or lower(coalesce(v_customer.email,''))<>lower(coalesce(p_evidence->>'customer_email',''))
    or nullif(btrim(p_evidence->>'customer_name'),'') is null
    or nullif(btrim(p_evidence->>'source_course_name'),'') is null
    or nullif(btrim(p_evidence->>'source_location_label'),'') is null then
  raise exception 'confirmed_booking_identity_and_place_required';
 end if;
 v_minutes:=coalesce(p_duration_minutes,v_course.duration_minutes);
 if v_minutes is null or v_minutes<1 or v_minutes>1440 then
  raise exception 'course_duration_rule_required';
 end if;
 perform pg_advisory_xact_lock(hashtextextended(p_course_id::text||':'||p_location_id::text||':'||p_starts_at::text,0));
 if p_workspace_id is not null then
  select * into strict v_w from public.landerware_sessions where id=p_workspace_id for update;
  if v_w.starts_at<>p_starts_at or (v_w.class_session_id is null and (
    v_w.lifecycle_state<>'pending_proposal'
    or lower(coalesce(v_w.requirements_manifest->>'customer_email',''))<>lower(coalesce(v_customer.email,''))
  )) then raise exception 'workspace_identity_conflict'; end if;
 end if;
 select count(*),(array_agg(id))[1] into v_matches,v_session
 from public.class_sessions where course_id=p_course_id and location_id=p_location_id
  and start_at=p_starts_at and record_scope='operational'
  and status not in ('canceled','cancelled','deleted');
 if v_matches>1 then raise exception 'multiple_matching_classes_require_review'; end if;
 if v_w.class_session_id is not null and v_w.class_session_id is distinct from v_session then
  raise exception 'workspace_canonical_identity_conflict';
 end if;
 v_evidence:=p_evidence||jsonb_build_object(
   'placement_rule','confirmed_booking_minimum_fields_v1',
   'duration_minutes',v_minutes,
   'duration_basis',case when p_duration_minutes is null then 'configured_course' else 'owner_course_duration_rule' end,
   'observed_at',now());
 if v_session is null then
  if p_workspace_id is not null then
   v_evidence:=v_evidence||jsonb_build_object('reconciles_workspace_id',p_workspace_id,
    'workspace_link_basis','confirmed_registration_minimum_fields');
  end if;
  insert into public.class_sessions(source,status,course_id,start_at,end_at,timezone,
    consumption_start_at,consumption_end_at,location_id,max_students,
    registration_backend,visibility,registration_status,record_scope,source_location_label,
    public_notes,external_session_evidence)
  values('confirmed_booking_intake','scheduled',p_course_id,p_starts_at,
    p_starts_at+make_interval(mins=>v_minutes),'America/New_York',
    p_starts_at,p_starts_at+make_interval(mins=>v_minutes),p_location_id,
    coalesce(nullif((p_evidence->>'reported_capacity')::integer,0),v_course.max_students_default,20),
    'landerware','private','closed','operational',p_evidence->>'source_location_label',
    'Confirmed booking. Needs attention: instructor assignment; source roster reconciliation. End time follows course duration rule.',
    v_evidence) returning id into v_session;
 end if;
 v_key:='gmail-confirmation:'||(p_evidence->>'gmail_message_id');
 -- A repeated source must not revive a subsequently cancelled/rescheduled registration.
 if exists(select 1 from public.registrations where idempotency_key=v_key and class_session_id<>v_session) then
  raise exception 'source_booking_already_moved';
 end if;
 insert into public.registrations(customer_id,class_session_id,status,registration_source,
    idempotency_key,material_choice,external_reconciliation_evidence)
 values(p_customer_id,v_session,
    case when p_evidence->>'registration_status' in ('cancelled','canceled','refund_requested') then 'canceled' else 'registered' end,
    'enrollware_email_confirmation',v_key,p_evidence->>'material_choice',v_evidence)
 on conflict(customer_id,class_session_id) do update set
    external_reconciliation_evidence=public.registrations.external_reconciliation_evidence||excluded.external_reconciliation_evidence,
    updated_at=now()
 returning id into v_registration;
 select id into strict v_workspace from public.landerware_sessions where class_session_id=v_session;
 v_flags:=jsonb_build_array('external_class_id','external_registration_id','source_roster_reconciliation');
 if (select lead_instructor_id from public.class_sessions where id=v_session) is null then
   v_flags:=v_flags||jsonb_build_array('instructor_assignment');
 end if;
 update public.landerware_sessions set
   requirements_manifest=requirements_manifest||jsonb_build_object(
    'status','scheduled','inventory_reserved',true,'needs_attention',true,'missing_field_flags',v_flags,'placement_rule','confirmed_booking_minimum_fields_v1',
    'duration_basis',v_evidence->>'duration_basis','record_scope','operational',
    'customer_commitment_created',true,'consumes_confirmed_inventory',true,
    'execution_status','Confirmed booking placed; remaining details are follow-up, not schedule gates.',
    'next_action','Complete instructor assignment and reconcile remaining source roster; preserve the scheduled booking.',
    'last_placement_verified_at',now()),updated_at=now()
 where id=v_workspace;
 if p_workspace_id is not null and p_workspace_id<>v_workspace then
  update public.landerware_sessions set lifecycle_state='superseded',
   requirements_manifest=requirements_manifest||jsonb_build_object('superseded_by_workspace_id',v_workspace,
     'class_session_id',v_session,'schedule_blocking',false,'placement_rule','confirmed_booking_minimum_fields_v1'),
   updated_at=now() where id=p_workspace_id and class_session_id is null;
  update public.landerware_sessions set document_ids=(
   select coalesce(jsonb_agg(distinct val),'[]'::jsonb)
   from jsonb_array_elements(coalesce(document_ids,'[]'::jsonb)||coalesce(v_w.document_ids,'[]'::jsonb)) val
  ) where id=v_workspace;
 end if;
 insert into public.class_session_audit(class_session_id,event_key,event_type,actor_label,occurred_at,details)
 select v_session,v_key,'confirmed_booking_placed','authorized_registration_intake',now(),
  jsonb_build_object('gmail_message_id',p_evidence->>'gmail_message_id','registration_id',v_registration,
   'workspace_id',v_workspace,'placement_rule','confirmed_booking_minimum_fields_v1')
 where not exists(select 1 from public.class_session_audit where class_session_id=v_session and event_key=v_key);
 return jsonb_build_object('class_session_id',v_session,'workspace_id',v_workspace,
  'registration_id',v_registration,'needs_attention',v_flags,'scheduled',true);
end
$fn$;
revoke all on function public.record_confirmed_intake(uuid,uuid,uuid,timestamptz,jsonb,uuid,integer) from public,anon,authenticated;
grant execute on function public.record_confirmed_intake(uuid,uuid,uuid,timestamptz,jsonb,uuid,integer) to service_role;
comment on function public.record_confirmed_intake(uuid,uuid,uuid,timestamptz,jsonb,uuid,integer)
 is 'Service-only atomic placement of verified registration confirmations; incomplete administrative data remains visible follow-up. Never charge, publish an offer, or infer a complete roster.';
