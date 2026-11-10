-- Service-only full BLS materialization from server-validated leased publication.
begin;
-- Separate fail-closed backend switch; migration alone never activates creation.
create table public.native_full_course_policy (
 policy_key text primary key check(policy_key='bls-full'),
 enabled boolean not null default false, verified boolean not null default false,
 evidence text, updated_at timestamptz not null default now()
);
insert into public.native_full_course_policy(policy_key) values('bls-full');
alter table public.native_full_course_policy enable row level security;
revoke all on public.native_full_course_policy from public,anon,authenticated;
grant select,insert,update,delete on public.native_full_course_policy to service_role;
create or replace function public.native_full_course_option(p_course_number text,p_offer jsonb)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare
 c public.courses; instructor public.people; venue public.locations;
 target public.class_sessions; starts timestamptz; ends timestamptz; occupied_end timestamptz;
 generated timestamptz; lease timestamptz; external_id text; fingerprint text; matches integer;
 capacity integer; occupied integer; held integer; inventory public.landerware_public_session_inventory;
begin
 if not exists(select 1 from public.native_full_course_policy where policy_key='bls-full' and enabled and verified and nullif(trim(evidence),'') is not null) then return null; end if;
 select count(*),min(id::text)::uuid into matches,c.id from public.courses where enrollware_course_id=p_course_number;
 if matches<>1 then return null; end if;
 select * into c from public.courses where id=c.id;
 if c.max_students_default is null or c.max_students_default<=0 or c.duration_minutes is distinct from 120
  or c.cleanup_buffer_minutes is distinct from 30 then return null; end if;
 -- Scope is deliberately limited to the two BLS full-course mappings and the selector's primary room.
 if p_offer->>'kind' is distinct from 'dynamic' or p_offer->>'authority' is distinct from 'native-full-course.v1'
  or c.enrollware_course_id not in ('209806','359474')
  or p_offer->>'courseNumber' is distinct from c.enrollware_course_id
  or p_offer->>'instructor' is distinct from 'Brian Ennis'
  or p_offer->>'resource' is distinct from ':: Wilmington; Shipyard Blvd - B'
  or p_offer->>'location' is distinct from ':: Wilmington; Shipyard Blvd'
  or nullif(p_offer->>'availabilityBlockId','') is null
  or coalesce(p_offer->>'appointmentDayId','') !~ '^[0-9]+$'
  or coalesce(p_offer->>'selectionId','') not like 'dynamic:%'
  or jsonb_typeof(p_offer->'sourceSessionIds') is distinct from 'array' then return null; end if;
 starts:=(p_offer->>'startsAt')::timestamptz; ends:=(p_offer->>'endsAt')::timestamptz;
 occupied_end:=(p_offer->>'consumptionEndsAt')::timestamptz;
 generated:=(p_offer->>'generatedAt')::timestamptz; lease:=(p_offer->>'validUntil')::timestamptz;
 if starts is null or ends is null or occupied_end is null or generated is null or lease is null
  or generated>now()+interval '1 minute' or generated<now()-interval '30 minutes' or lease<=now()
  or starts<=now() or ends<>starts+interval '120 minutes' or occupied_end<>ends+interval '30 minutes'
  or ends<=starts or occupied_end<ends or occupied_end>starts+interval '1 day'
  or to_char(starts at time zone 'America/New_York','YYYY-MM-DD"T"HH24:MI') is distinct from p_offer->>'localStart'
 then return null; end if;
 select count(*),min(id::text)::uuid into matches,instructor.id from public.people where person_key='brian' and display_name=p_offer->>'instructor' and active;
 if matches<>1 then return null; end if;
 select count(*),min(id::text)::uuid into matches,venue.id from public.locations where location_key='910cpr-office-shipyard' and scheduling_status='active';
 if matches<>1 then return null; end if;
 -- Qualifications/travel/availability are evaluated by the current public selector. An explicit
 -- canonical revocation overrides that evidence even before the next selector publication.
 if not exists(select 1 from public.instructor_qualifications q where q.instructor_id=instructor.id and q.course_id=c.id
  and q.status='active' and (q.expires_at is null or q.expires_at>=occupied_end)) then return null; end if;
 if exists(select 1 from public.instructor_qualifications q where q.instructor_id=instructor.id and q.course_id=c.id
  and (q.status is distinct from 'active' or (q.expires_at is not null and q.expires_at<occupied_end))) then return null; end if;
 fingerprint:=md5(p_offer->>'selectionId');
 external_id:='lw-'||substr(fingerprint,1,8)||'-'||substr(fingerprint,9,4)||'-'||substr(fingerprint,13,4)||'-'||substr(fingerprint,17,4)||'-'||substr(fingerprint,21,12);
 select count(*),min(s.id::text)::uuid into matches,target.id from public.class_sessions s
  where s.external_class_id=external_id or (s.record_scope='operational' and s.course_id=c.id and s.start_at=starts
   and s.end_at=ends and s.consumption_end_at=occupied_end and s.lead_instructor_id=instructor.id and s.location_id=venue.id
   and s.status in ('scheduled','active'));
 if matches>1 then return null; end if;
 if target.id is not null then
  select * into target from public.class_sessions where id=target.id;
  if target.course_id is distinct from c.id or target.start_at is distinct from starts or target.end_at is distinct from ends
   or target.consumption_end_at is distinct from occupied_end or target.lead_instructor_id is distinct from instructor.id
   or target.location_id is distinct from venue.id or target.record_scope<>'operational'
   or target.status not in ('scheduled','active') or target.registration_status not in ('open','external')
   or target.visibility not in ('public','unlisted') or target.registration_backend is distinct from 'landerware' then return null; end if;
  external_id:=target.external_class_id;
 end if;
 -- A stale lease must not create a second same-course daily position. Until
 -- complete paid/unknown demand can be certified in this transaction, reject any
 -- other operational position, including empty/manual ones, without changing it.
 if exists(select 1 from public.class_sessions s where s.record_scope='operational'
  and s.id is distinct from target.id and s.course_id=c.id and s.lead_instructor_id=instructor.id
  and s.status in ('scheduled','active','tentative','pending','proposed_window')
  and (s.start_at at time zone 'America/New_York')::date=(starts at time zone 'America/New_York')::date) then return null; end if;
 if exists(select 1 from public.registration_reschedule_blocks b join public.class_sessions s on s.id=b.class_session_id
   where s.course_id=c.id and s.start_at=starts) then return null; end if;
 if exists(select 1 from jsonb_array_elements(public.public_registration_closure_policy()->'closures') closure
   where starts<(closure->>'endsAt')::timestamptz and occupied_end>(closure->>'startsAt')::timestamptz) then return null; end if;
 -- No canonical room records exist at this baseline. Reserve the whole venue conservatively;
 -- never infer permission to relocate to A/C. Also block this instructor at any other venue.
 -- The selector may explicitly share only a named source's cooldown edge, never instruction.
 if exists(select 1 from public.class_sessions s where s.record_scope='operational'
   and s.status in ('scheduled','active','tentative','pending','proposed_window') and s.id is distinct from target.id
   and (s.location_id=venue.id or s.lead_instructor_id=instructor.id)
   and coalesce(s.consumption_start_at,s.start_at)<occupied_end
   and coalesce(s.consumption_end_at,s.end_at,s.start_at+interval '1 day')>starts
   and not (s.end_at<=starts and exists(select 1 from jsonb_array_elements_text(p_offer->'sourceSessionIds') source_id
     where source_id=s.id::text or source_id=s.external_class_id))) then return null; end if;
 if target.id is not null then
  capacity:=(public.landerware_public_seat_state(target.id)->>'capacity')::integer;
  if capacity is null or (public.landerware_public_seat_state(target.id)->>'remaining')::integer<1 then return null; end if;
 else
  capacity:=case when c.enrollware_course_id='209806' then least(6,c.max_students_default) else c.max_students_default end;
  if capacity is null or capacity<=0 then return null; end if;
 end if;
 return jsonb_build_object('id',p_offer->>'selectionId','targetSessionId',target.id,'externalId',external_id,
  'course',c.name,'courseId',c.id,'instructorId',instructor.id,'locationId',venue.id,'capacity',capacity,
  'startsAt',starts,'endsAt',ends,'consumptionEndsAt',occupied_end,'timezone','America/New_York',
  'location',(select name from public.locations where id=venue.id),'address',
  (select concat_ws(', ',address_line1,address_line2,city,state,postal_code) from public.locations where id=venue.id));
end $$;

create or replace function public.materialize_native_full_checkout(p_course_number text,p_offer jsonb,p_idempotency_key text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare option jsonb; target uuid; locked_external_id text;
begin
 option:=public.native_full_course_option(p_course_number,p_offer);
 if option is null then raise exception 'session_not_available'; end if;
 locked_external_id:=option->>'externalId';
 perform pg_advisory_xact_lock(hashtextextended('landerware-public-offer|'||locked_external_id,0));
 -- Serialize ALL overlapping offer identities, not just identical selected IDs.
 lock table public.class_sessions in share row exclusive mode;
 lock table public.courses,public.people,public.locations,public.instructor_qualifications in share mode;
 option:=public.native_full_course_option(p_course_number,p_offer);
 if option is null or option->>'externalId' is distinct from locked_external_id then raise exception 'session_not_available'; end if;
 target:=(option->>'targetSessionId')::uuid;
 if target is not null then
  perform 1 from public.class_sessions where id=target for update;
  perform 1 from public.landerware_public_session_inventory where external_class_id=locked_external_id for update;
  option:=public.native_full_course_option(p_course_number,p_offer);
  if option is null then raise exception 'session_not_available'; end if;
 end if;
 if target is null then
  insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,
    lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,
    source_offer_id,source_location_label,source_instructor_label,external_course_id,registration_url,price,advertised_duration_minutes,external_session_evidence)
  values('landerware_event','scheduled','operational',(option->>'courseId')::uuid,(option->>'startsAt')::timestamptz,
    (option->>'endsAt')::timestamptz,'America/New_York',(option->>'startsAt')::timestamptz,(option->>'consumptionEndsAt')::timestamptz,
    (option->>'instructorId')::uuid,(option->>'locationId')::uuid,(option->>'capacity')::integer,'landerware','public','open',
    option->>'externalId',p_offer->>'availabilityBlockId',p_offer->>'location',p_offer->>'instructor',p_course_number,
    '/bls.html?course='||p_course_number,(select unit_amount/100.0 from public.landerware_registration_catalog where course_id=p_course_number and active),120,
    jsonb_build_object('selectorOffer',p_offer,'materializedBy','native_full_course')) returning id into target;
 end if;
 -- The canonical demand projection requires exactly one current workspace.
 -- Never overwrite a different existing identity/timing to manufacture proof.
 if exists(select 1 from public.landerware_sessions w where (w.class_session_id=target or w.external_session_id=option->>'externalId')
   and (w.class_session_id is distinct from target or w.external_session_id is distinct from option->>'externalId'
    or w.course_id is distinct from (select course_key from public.courses where id=(option->>'courseId')::uuid) or w.starts_at is distinct from (option->>'startsAt')::timestamptz
    or w.ends_at is distinct from (option->>'endsAt')::timestamptz)) then raise exception 'session_not_available'; end if;
 if not exists(select 1 from public.landerware_sessions where class_session_id=target) then
 insert into public.landerware_sessions(external_session_id,class_session_id,course_id,course_name,starts_at,ends_at,location_name,instructor_name,provenance,requirements_manifest)
 values(option->>'externalId',target,(select course_key from public.courses where id=(option->>'courseId')::uuid),option->>'course',(option->>'startsAt')::timestamptz,(option->>'endsAt')::timestamptz,
  p_offer->>'location',p_offer->>'instructor','native_full_course:'||p_idempotency_key,'{}'::jsonb)
 on conflict(external_session_id,course_id,starts_at) do nothing;
 end if;
 if (select count(*) from public.landerware_sessions where class_session_id=target)<>1 then raise exception 'session_not_available'; end if;

 return option||jsonb_build_object('targetSessionId',target,'externalId',locked_external_id);
end $$;

create or replace function public.reserve_native_checkout_order(p_key text,p_profile_key text,p_version integer,p_context text,p_external_id text,p_offer jsonb,p_students jsonb,p_inputs jsonb,p_expected_total integer)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare p public.landerware_registration_profiles; c public.courses; o public.landerware_public_orders; old_receipt public.skills_session_claim_receipts;
 option jsonb; external_id text; result jsonb; snapshot jsonb; wanted integer;
begin
 if p_key is null or p_key !~ '^[a-f0-9-]{36}$' or jsonb_typeof(p_students) is distinct from 'array' or jsonb_typeof(p_inputs) is distinct from 'array'
  or p_expected_total is null or p_expected_total<=0 or p_expected_total>10000000 then raise exception 'invalid_request'; end if;
 perform pg_advisory_xact_lock(hashtextextended('native-checkout-key|'||p_key,0));
 select * into o from public.landerware_public_orders where idempotency_key='public-order:'||p_key;
 select * into old_receipt from public.skills_session_claim_receipts where idempotency_key=p_key;
 if o.id is not null or old_receipt.registration_id is not null then
  if o.id is not null and o.registration_profile_snapshot<>'{}'::jsonb and o.registration_profile_snapshot->'inputs' is distinct from p_inputs then raise exception 'idempotency_conflict'; end if;
  return public.native_checkout_receipt(p_key);
 end if;
 select * into p from public.landerware_registration_profiles where profile_key=p_profile_key and version=p_version and active and registration_mode='native_public_checkout' for share;
 if p.profile_key is null then raise exception 'profile_changed'; end if;
 wanted:=jsonb_array_length(p_students);
 if wanted<1 or wanted>least(coalesce((p.form_schema->>'max_students')::integer,1),10) or jsonb_array_length(p_inputs)<>wanted then raise exception 'invalid_request'; end if;
 select * into c from public.courses where course_key=p.course_id and registration_profile_key=p.profile_key;
 if c.id is null then raise exception 'native_profile_not_configured'; end if;
 if nullif(p_external_id,'') is null then
  if not (p_offer ? 'startsAt') then return jsonb_build_object('status','offer_required'); end if;
  if p.form_schema->>'inventory_kind'='scheduled_session_v1' and c.enrollware_course_id in ('209806','359474') and coalesce(p_context,'')='' then
   option:=public.materialize_native_full_checkout(c.enrollware_course_id,p_offer,p_key);
  else
   if p.form_schema->>'inventory_kind' is distinct from 'leased_skills_v1' or not coalesce(p.form_schema->'allowed_contexts' ? p_context,false) then raise exception 'invalid_context'; end if;
   option:=public.materialize_native_skills_checkout(p_context,p_offer,p_key);
  end if;
  if (option->>'courseId')::uuid is distinct from c.id then raise exception 'invalid_checkout_profile'; end if;
  external_id:=option->>'externalId';
 else
  if p.form_schema->>'inventory_kind' is distinct from 'scheduled_session_v1' or
   (select count(*) from public.class_sessions s where s.external_class_id=p_external_id and s.record_scope='operational' and s.course_id=c.id)<>1 then raise exception 'session_not_open'; end if;
  external_id:=p_external_id;
 end if;
 result:=public.landerware_create_public_order('public-order:'||p_key,external_id,c.enrollware_course_id,lower(trim(p_students->0->>'email')),trim(p_students->0->>'phone'),p_students,null,
  jsonb_build_object('profile_fields_validated',true,'profile_key',p.profile_key,'profile_version',p.version));
 select * into strict o from public.landerware_public_orders where id=(result->>'orderId')::uuid;
 if o.total<=0 then raise exception 'billing_approval_required'; end if;
 if o.total>p_expected_total or (o.total<>p_expected_total and not exists(select 1 from jsonb_array_elements(p_students) st where nullif(trim(st->>'billingCode'),'') is not null)) then raise exception 'profile_price_mismatch'; end if;
 snapshot:=public.native_checkout_bind_profile(p_key,p.profile_key,p.version,'native_order',p_context,
  jsonb_build_object('externalId',external_id,'offerId',p_offer->>'selectionId'),p_inputs);
 return public.native_checkout_receipt(p_key);
end $$;

revoke all on function public.native_full_course_option(text,jsonb),public.materialize_native_full_checkout(text,jsonb,text),public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer) from public,anon,authenticated;
grant execute on function public.native_full_course_option(text,jsonb),public.materialize_native_full_checkout(text,jsonb,text),public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer) to service_role;
commit;
