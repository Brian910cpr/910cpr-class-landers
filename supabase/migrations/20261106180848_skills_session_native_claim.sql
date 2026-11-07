-- Native new-registration claim, based on the existing canonical dynamic
-- reschedule transaction. No Enrollware handoff, payment capture, or email.
-- No production capacity, qualification mapping or enabled context is seeded.
begin;
create table public.skills_session_context_config (
 context_key text primary key check(context_key in ('cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended')),
 course_id uuid not null references public.courses(id),
 qualification_course_id uuid not null references public.courses(id),
 enabled boolean not null default false,
 capacity_policy_verified boolean not null default false,
 policy_evidence text not null default ''
);
create table public.skills_session_claim_receipts (
 idempotency_key text primary key,
 request_fingerprint text not null,
 registration_id uuid not null references public.registrations(id),
 result jsonb not null,
 created_at timestamptz not null default now()
);
alter table public.skills_session_context_config enable row level security;
alter table public.skills_session_claim_receipts enable row level security;
revoke all on public.skills_session_context_config,public.skills_session_claim_receipts from public,anon,authenticated;
grant select,insert,update on public.skills_session_context_config,public.skills_session_claim_receipts to service_role;

create or replace function public.skills_session_native_option(p_context text,p_offer jsonb)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare
 cfg public.skills_session_context_config; c public.courses; instructor public.people; venue public.locations;
 target public.class_sessions; starts timestamptz; ends timestamptz; occupied_end timestamptz;
 generated timestamptz; lease timestamptz; external_id text; fingerprint text; matches integer;
 capacity integer; occupied integer; held integer; inventory public.landerware_public_session_inventory;
begin
 select * into cfg from public.skills_session_context_config where context_key=p_context and enabled
  and capacity_policy_verified and nullif(policy_evidence,'') is not null;
 if cfg.context_key is null then return null; end if;
 select * into c from public.courses where id=cfg.course_id;
 if c.id is null or c.enrollware_course_id is distinct from '509474'
  or c.max_students_default is distinct from 2 or c.base_price is distinct from 55
  or c.duration_minutes is distinct from 45 or c.cleanup_buffer_minutes is distinct from 15
  or c.setup_buffer_minutes is distinct from 0 then return null; end if;
 -- Only the explicitly configured skills context and primary venue are eligible.
 if p_offer->>'kind' is distinct from 'dynamic' or c.enrollware_course_id is distinct from '509474'
  or coalesce(p_offer->>'offerType','') not in ('dynamic_appointment','seated_class')
  or p_offer->>'courseNumber' is distinct from c.enrollware_course_id
  or p_offer->>'context' is distinct from p_context
  or p_offer->>'resource' is distinct from ':: Wilmington; Shipyard Blvd - B'
  or p_offer->>'location' is distinct from ':: Wilmington; Shipyard Blvd'
  or nullif(p_offer->>'availabilityBlockId','') is null
  or coalesce(p_offer->>'selectionId','') not like 'skills:%'
  or jsonb_typeof(p_offer->'sourceSessionIds') is distinct from 'array' then return null; end if;
 starts:=(p_offer->>'startsAt')::timestamptz; ends:=(p_offer->>'endsAt')::timestamptz;
 occupied_end:=(p_offer->>'consumptionEndsAt')::timestamptz;
 generated:=(p_offer->>'generatedAt')::timestamptz; lease:=(p_offer->>'validUntil')::timestamptz;
 if starts is null or ends is null or occupied_end is null or generated is null or lease is null
  or generated>now()+interval '1 minute' or generated<now()-interval '30 minutes' or lease<=now()
  or starts<=now()
  or ends<>starts+interval '45 minutes' or occupied_end<>ends+interval '15 minutes'
  or to_char(starts at time zone 'America/New_York','YYYY-MM-DD"T"HH24:MI') is distinct from p_offer->>'localStart'
 then return null; end if;
 select count(*),min(id::text)::uuid into matches,instructor.id from public.people where display_name=p_offer->>'instructor' and active;
 if matches<>1 then return null; end if;
 select count(*),min(id::text)::uuid into matches,venue.id from public.locations where location_key='910cpr-office-shipyard' and scheduling_status='active';
 if matches<>1 then return null; end if;
 -- Qualifications/travel/availability are evaluated by the current public selector. An explicit
 -- canonical revocation overrides that evidence even before the next selector publication.
 if not exists(select 1 from public.instructor_qualifications q where q.instructor_id=instructor.id
  and q.course_id=cfg.qualification_course_id and q.status='active'
  and (q.expires_at is null or q.expires_at>=occupied_end)) then return null; end if;
 if exists(select 1 from public.instructor_qualifications q where q.instructor_id=instructor.id
  and q.course_id=cfg.qualification_course_id and (q.status is distinct from 'active'
  or (q.expires_at is not null and q.expires_at<occupied_end))) then return null; end if;
 fingerprint:=md5(concat_ws('|',c.id,starts,ends,occupied_end,instructor.id,venue.id));
 external_id:='lw-'||substr(fingerprint,1,8)||'-'||substr(fingerprint,9,4)||'-'||substr(fingerprint,13,4)||'-'||substr(fingerprint,17,4)||'-'||substr(fingerprint,21,12);
 select count(*),min(s.id::text)::uuid into matches,target.id from public.class_sessions s
  where s.external_class_id=external_id or (s.record_scope='operational' and s.course_id=c.id and s.start_at=starts
   and s.end_at=ends and s.consumption_end_at=occupied_end and s.lead_instructor_id=instructor.id and s.location_id=venue.id
   and s.status in ('scheduled','active'));
 if matches>1 then return null; end if;
 if p_offer->>'offerType'='seated_class' and target.id is null then return null; end if;
 if target.id is not null then
  select * into target from public.class_sessions where id=target.id;
  if target.registration_backend is distinct from 'landerware' or target.price is distinct from 55 or target.resource_id is not null
   or target.course_id is distinct from c.id or target.start_at is distinct from starts or target.end_at is distinct from ends
   or target.consumption_end_at is distinct from occupied_end or target.lead_instructor_id is distinct from instructor.id
   or target.location_id is distinct from venue.id or target.record_scope<>'operational'
   or target.status not in ('scheduled','active') or target.registration_status is distinct from 'open'
   or target.visibility is distinct from 'public' then return null; end if;
  if p_offer->>'offerType'='seated_class' and p_offer->>'sourceSessionId' is distinct from target.id::text
    and p_offer->>'sourceSessionId' is distinct from target.external_class_id then return null; end if;
  external_id:=target.external_class_id;
 end if;
 if exists(select 1 from public.registration_reschedule_blocks b join public.class_sessions s on s.id=b.class_session_id
   where s.course_id=c.id and s.start_at=starts) then return null; end if;
 if exists(select 1 from jsonb_array_elements(public.public_registration_closure_policy()->'closures') closure
   where starts<(closure->>'endsAt')::timestamptz and occupied_end>(closure->>'startsAt')::timestamptz) then return null; end if;
 -- No canonical room records exist at this baseline. Reserve the whole venue conservatively;
 -- never infer permission to relocate to A/C. Also block this instructor at any other venue.
 -- This new-registration path never waives another class's cleanup interval.
 if exists(select 1 from public.class_sessions s where s.record_scope='operational'
   and s.status in ('scheduled','active','tentative','pending','proposed_window') and s.id is distinct from target.id
   and (s.location_id=venue.id or s.lead_instructor_id=instructor.id)
   and coalesce(s.consumption_start_at,s.start_at)<occupied_end
   and coalesce(s.consumption_end_at,s.end_at,s.start_at+interval '1 day')>starts
   ) then return null; end if;
 if target.id is not null then
  select * into inventory from public.landerware_public_session_inventory where external_class_id=target.external_class_id;
  select count(*) into occupied from public.registrations where class_session_id=target.id and status in ('active','registered','confirmed','completed');
  select count(*) into held from public.landerware_public_order_students os join public.landerware_public_orders o on o.id=os.order_id
   where o.class_session_id=target.id and o.status in ('held','checkout_open') and o.hold_expires_at>now();
  capacity:=least(coalesce(inventory.capacity,target.max_students),target.max_students,c.max_students_default);
  if capacity is null or greatest(occupied,coalesce(inventory.externally_registered,0))+held>=capacity then return null; end if;
 else
  -- Capacity must be configured on the actual canonical 509474 course.
  capacity:=c.max_students_default;
  if capacity is null or capacity<=0 then return null; end if;
 end if;
 return jsonb_build_object('id',p_offer->>'selectionId','targetSessionId',target.id,'externalId',external_id,
  'course',c.name,'courseId',c.id,'instructorId',instructor.id,'locationId',venue.id,'capacity',capacity,
  'startsAt',starts,'endsAt',ends,'consumptionEndsAt',occupied_end,'timezone','America/New_York',
  'location',(select name from public.locations where id=venue.id),'address',
  (select concat_ws(', ',address_line1,address_line2,city,state,postal_code) from public.locations where id=venue.id));
end $$;

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
    or w.course_id is distinct from '509474' or w.starts_at is distinct from (option->>'startsAt')::timestamptz
    or w.ends_at is distinct from (option->>'endsAt')::timestamptz)) then raise exception 'session_not_available'; end if;
 insert into public.landerware_sessions(external_session_id,class_session_id,course_id,course_name,starts_at,ends_at,location_name,instructor_name,provenance,requirements_manifest)
 values(option->>'externalId',target,'509474',option->>'course',(option->>'startsAt')::timestamptz,(option->>'endsAt')::timestamptz,
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
revoke all on function public.skills_session_native_option(text,jsonb),public.reserve_skills_session_native(text,text,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.skills_session_native_option(text,jsonb),public.reserve_skills_session_native(text,text,jsonb,jsonb) to service_role;
commit;
