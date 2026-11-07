-- Canonical workspace identity compatibility and explicit native skills policy.
begin;
create or replace function public.reserve_skills_session_native(p_idempotency_key text,p_context text,p_offer jsonb,p_student jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare receipt public.skills_session_claim_receipts; option jsonb; target uuid; customer uuid; registration uuid;
 fingerprint text; answer jsonb; first_name text; last_name text; email text; locked_external_id text;
begin
 if p_idempotency_key !~ '^[0-9a-f-]{36}$' or p_idempotency_key is null then raise exception 'invalid_request'; end if;
 first_name:=trim(p_student->>'firstName'); last_name:=trim(p_student->>'lastName'); email:=lower(trim(p_student->>'email'));
 if coalesce(first_name,'')='' or coalesce(last_name,'')='' or coalesce(email,'') !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
  or length(first_name)>100 or length(last_name)>100 or length(email)>254
  or p_student->>'onlineCompleted' is distinct from 'true' then raise exception 'invalid_student'; end if;
 fingerprint:=md5(jsonb_build_object('context',p_context,'selectionId',p_offer->>'selectionId',
  'firstName',first_name,'lastName',last_name,'email',email,'phone',trim(coalesce(p_student->>'phone','')),'onlineCompleted',true)::text);
 perform pg_advisory_xact_lock(hashtextextended('skills-claim|'||p_idempotency_key,0));
 select * into receipt from public.skills_session_claim_receipts where idempotency_key=p_idempotency_key;
 if receipt.idempotency_key is not null then
  if receipt.request_fingerprint<>fingerprint then raise exception 'idempotency_conflict'; end if;
  if not exists(select 1 from public.registrations where id=receipt.registration_id
    and status in ('registered','active','confirmed','completed')) then raise exception 'session_not_available'; end if;
  return receipt.result||jsonb_build_object('idempotentReplay',true,'paymentStatus',
    case when exists(select 1 from public.registration_orders where registration_id=receipt.registration_id and status='paid') then 'paid' else 'pending' end);
 end if;
 -- Service may first probe an identical saved request without fetching a new
 -- publication. A lost-response retry remains idempotent after lease expiry.
 if p_offer->>'startsAt' is null then return jsonb_build_object('ok',false,'status','offer_required'); end if;
 -- Match checkout/rescheduling lock order and identity before taking the global
 -- schedule lock. This also serializes existing-session paid/held seat claims.
 option:=public.skills_session_native_option(p_context,p_offer);
 if option is null then raise exception 'session_not_available'; end if;
 locked_external_id:=option->>'externalId';
 perform pg_advisory_xact_lock(hashtextextended('landerware-public-offer|'||locked_external_id,0));
 -- Serialize ALL overlapping offer identities, not just identical selected IDs.
 lock table public.class_sessions in share row exclusive mode;
 lock table public.skills_session_context_config,public.courses,public.people,public.locations,public.instructor_qualifications in share mode;
 option:=public.skills_session_native_option(p_context,p_offer);
 if option is null or option->>'externalId' is distinct from locked_external_id then raise exception 'session_not_available'; end if;
 target:=(option->>'targetSessionId')::uuid;
 if target is not null then
  perform 1 from public.class_sessions where id=target for update;
  perform 1 from public.landerware_public_session_inventory where external_class_id=locked_external_id for update;
  option:=public.skills_session_native_option(p_context,p_offer);
  if option is null then raise exception 'session_not_available'; end if;
 end if;
 if target is null then
  insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,
    lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,
    source_offer_id,source_location_label,source_instructor_label,external_course_id,registration_url,price,advertised_duration_minutes,external_session_evidence)
  values('landerware_event','scheduled','operational',(option->>'courseId')::uuid,(option->>'startsAt')::timestamptz,
    (option->>'endsAt')::timestamptz,'America/New_York',(option->>'startsAt')::timestamptz,(option->>'consumptionEndsAt')::timestamptz,
    (option->>'instructorId')::uuid,(option->>'locationId')::uuid,(option->>'capacity')::integer,'landerware','public','open',
    option->>'externalId',p_offer->>'availabilityBlockId',p_offer->>'location',p_offer->>'instructor','509474',
    case when p_context='arc-blended' then '/arc.html?course=509474' when p_context='hsi-blended' then '/hsi.html?course=509474' else '/heartsaver.html?course=509474' end,55,45,
    jsonb_build_object('selectorOffer',p_offer,'materializedBy','skills_session_native')) returning id into target;
 end if;
 -- The canonical demand projection requires exactly one current workspace.
 -- Never overwrite a different existing identity/timing to manufacture proof.
 if exists(select 1 from public.landerware_sessions w where (w.class_session_id=target or w.external_session_id=option->>'externalId')
   and (w.class_session_id is distinct from target or w.external_session_id is distinct from option->>'externalId'
    or w.course_id is distinct from (select course_key from public.courses where id=(option->>'courseId')::uuid) or w.starts_at is distinct from (option->>'startsAt')::timestamptz
    or w.ends_at is distinct from (option->>'endsAt')::timestamptz)) then raise exception 'session_not_available'; end if;
 insert into public.landerware_sessions(external_session_id,class_session_id,course_id,course_name,starts_at,ends_at,location_name,instructor_name,provenance,requirements_manifest)
 values(option->>'externalId',target,(select course_key from public.courses where id=(option->>'courseId')::uuid),option->>'course',(option->>'startsAt')::timestamptz,(option->>'endsAt')::timestamptz,
  p_offer->>'location',p_offer->>'instructor','skills_session_native:'||p_idempotency_key,'{}'::jsonb)
 on conflict(external_session_id,course_id,starts_at) do nothing;
 if (select count(*) from public.landerware_sessions where class_session_id=target)<>1 then raise exception 'session_not_available'; end if;
 insert into public.customers(first_name,last_name,email,phone)
 values(first_name,last_name,email,nullif(trim(p_student->>'phone'),'')) returning id into customer;
 insert into public.registrations(customer_id,class_session_id,status,registration_source,idempotency_key,optional_survey)
 values(customer,target,'registered','landerware','skills-claim:'||p_idempotency_key,
  jsonb_build_object('skillsContext',p_context,'onlineCompleted',true,'priceCents',5500,'certificateUploadRequired',false)) returning id into registration;
 insert into public.registration_orders(registration_id,status,currency,course_amount,total_amount)
 values(registration,'payment_pending','usd',55,55);
 insert into public.participant_lifecycle_events(event_key,event_type,customer_id,registration_id,class_session_id,source,actor,details)
 values('skills-reserved:'||p_idempotency_key,'registration_created',customer,registration,target,'landerware',
  '{"kind":"public_registration"}'::jsonb,jsonb_build_object('context',p_context,'selectionId',p_offer->>'selectionId',
  'priceCents',5500,'paymentState','pending','certificateUploadRequired',false));
 answer:=jsonb_build_object('ok',true,'status','reserved','registrationId',registration,'sessionId',target,
  'startsAt',option->>'startsAt','endsAt',option->>'endsAt','location',option->>'location',
  'context',p_context,'amountCents',5500,'paymentStatus','pending','idempotentReplay',false);
 insert into public.skills_session_claim_receipts(idempotency_key,request_fingerprint,registration_id,result)
 values(p_idempotency_key,fingerprint,registration,answer);
 return answer;
end $$;

insert into public.courses(course_key,name,course_family,subtype,certifying_body,delivery_mode,duration_minutes,setup_buffer_minutes,cleanup_buffer_minutes,max_students_default,base_price,registration_backend_default,visibility_default,enrollware_course_id)
 values('skills-session-only','Skills Session Only','Skills','Skills Session Only','910CPR','skills',45,0,15,2,55,'landerware','public','509474')
 on conflict(enrollware_course_id) do nothing;
do $$ declare c public.courses; p public.people; begin
 select * into strict c from public.courses where enrollware_course_id='509474';
 if c.course_key<>'skills-session-only' or c.duration_minutes<>45 or c.cleanup_buffer_minutes<>15 or c.setup_buffer_minutes<>0 or c.max_students_default<>2 or c.base_price<>55 then raise exception 'skills_policy_conflict'; end if;
 select * into strict p from public.people where person_key='brian' and display_name='Brian Ennis' and active;
 if exists(select 1 from public.instructor_qualifications where instructor_id=p.id and course_id=c.id and (status is distinct from 'active' or expires_at is not null)) then raise exception 'skills_qualification_requires_review'; end if;
 insert into public.instructor_qualifications(instructor_id,course_id,qualification_key,status)
 select p.id,c.id,'skills-session-policy.v1','active' where not exists(select 1 from public.instructor_qualifications where instructor_id=p.id and course_id=c.id);
 insert into public.skills_session_context_config(context_key,course_id,qualification_course_id,enabled,capacity_policy_verified,policy_evidence)
 select k,c.id,c.id,false,true,'skills-session-policy.v1' from unnest(array['cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended']) k;
end $$;
commit;
