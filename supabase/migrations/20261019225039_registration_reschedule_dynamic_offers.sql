-- Published dynamic choices materialize only during an atomic registration transfer.
-- Extends the canonical public-offer materialization pattern; no order or charge is created.
begin;

create or replace function public.registration_reschedule_dynamic_option(p_registration_id uuid,p_offer jsonb,p_deadline_at timestamptz)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare
 original public.class_sessions; c public.courses; instructor public.people; venue public.locations;
 target public.class_sessions; starts timestamptz; ends timestamptz; occupied_end timestamptz;
 generated timestamptz; lease timestamptz; external_id text; fingerprint text; matches integer;
 capacity integer; occupied integer; held integer; inventory public.landerware_public_session_inventory;
begin
 select s.* into original from public.registrations r join public.class_sessions s on s.id=r.class_session_id where r.id=p_registration_id;
 select * into c from public.courses where id=original.course_id;
 -- Scope is deliberately limited to the three verified course mappings and the selector's primary room.
 if p_offer->>'kind' is distinct from 'dynamic' or c.enrollware_course_id not in ('209806','359474','209809')
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
  or starts<=now() or starts=original.start_at or (p_deadline_at is not null and starts>p_deadline_at)
  or ends<=starts or occupied_end<ends or occupied_end>starts+interval '1 day'
  or to_char(starts at time zone 'America/New_York','YYYY-MM-DD"T"HH24:MI') is distinct from p_offer->>'localStart'
 then return null; end if;
 select count(*),min(id::text)::uuid into matches,instructor.id from public.people where person_key='brian' and display_name=p_offer->>'instructor' and active;
 if matches<>1 then return null; end if;
 select count(*),min(id::text)::uuid into matches,venue.id from public.locations where location_key='910cpr-office-shipyard' and scheduling_status='active';
 if matches<>1 then return null; end if;
 -- Qualifications/travel/availability are evaluated by the current public selector. An explicit
 -- canonical revocation overrides that evidence even before the next selector publication.
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
   or target.visibility not in ('public','unlisted') then return null; end if;
  external_id:=target.external_class_id;
 end if;
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
  select * into inventory from public.landerware_public_session_inventory where external_class_id=target.external_class_id;
  select count(*) into occupied from public.registrations where class_session_id=target.id and status in ('active','registered','confirmed','completed');
  select count(*) into held from public.landerware_public_order_students os join public.landerware_public_orders o on o.id=os.order_id
   where o.class_session_id=target.id and o.status in ('held','checkout_open') and o.hold_expires_at>now();
  capacity:=coalesce(inventory.capacity,target.max_students);
  if capacity is null or greatest(occupied,coalesce(inventory.externally_registered,0))+held>=capacity then return null; end if;
 else
  -- Keep the existing BLS Initial booking limit; other courses use their own canonical rules.
  capacity:=case when c.enrollware_course_id='209806' then least(6,c.max_students_default) else c.max_students_default end;
  if capacity is null or capacity<=0 then return null; end if;
 end if;
 return jsonb_build_object('id',p_offer->>'selectionId','targetSessionId',target.id,'externalId',external_id,
  'course',c.name,'courseId',c.id,'instructorId',instructor.id,'locationId',venue.id,'capacity',capacity,
  'startsAt',starts,'endsAt',ends,'consumptionEndsAt',occupied_end,'timezone','America/New_York',
  'location',(select name from public.locations where id=venue.id),'address',
  (select concat_ws(', ',address_line1,address_line2,city,state,postal_code) from public.locations where id=venue.id));
end $$;

create or replace function public.registration_reschedule_dynamic_targets(p_token_sha256 text,p_offers jsonb)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare t public.registration_reschedule_links; result jsonb;
begin
 select * into t from public.registration_reschedule_links where token_sha256=p_token_sha256;
 if t.id is null or t.revoked_at is not null or t.expires_at<=now() or t.used_at is not null then raise exception 'invalid_or_expired_link'; end if;
 if not exists(select 1 from public.registrations r where r.id=t.registration_id and r.status in ('active','registered','confirmed'))
  or exists(select 1 from public.participant_completions where registration_id=t.registration_id) then raise exception 'registration_not_reschedulable'; end if;
 if jsonb_typeof(p_offers) is distinct from 'array' or jsonb_array_length(p_offers)>10000 then raise exception 'session_not_available'; end if;
 select coalesce(jsonb_agg(option order by option->>'startsAt'),'[]') into result from (
  select public.registration_reschedule_dynamic_option(t.registration_id,value,t.deadline_at) option from jsonb_array_elements(p_offers)
 ) options where option is not null;
 return result;
end $$;

create or replace function public.confirm_registration_reschedule_dynamic(p_token_sha256 text,p_offer jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare t public.registration_reschedule_links; option jsonb; target uuid; v_result jsonb;
begin
 select * into t from public.registration_reschedule_links where token_sha256=p_token_sha256 for update;
 if t.id is null or t.revoked_at is not null or t.expires_at<=now() then raise exception 'invalid_or_expired_link'; end if;
 if t.used_at is not null then
  if t.result->>'selectionId' is distinct from p_offer->>'selectionId' then raise exception 'link_already_used'; end if;
  return t.result||jsonb_build_object('idempotentReplay',true);
 end if;
 perform 1 from public.registrations where id=t.registration_id for update;
 -- Match checkout's offer-lock order, then serialize all canonical schedule writes, including
 -- different overlapping offer identities. Recheck after waiting, never trust the list read.
 option:=public.registration_reschedule_dynamic_option(t.registration_id,p_offer,t.deadline_at);
 if option is null then raise exception 'session_not_available'; end if;
 perform pg_advisory_xact_lock(hashtextextended('landerware-public-offer|'||(option->>'externalId'),0));
 lock table public.class_sessions in share row exclusive mode;
 option:=public.registration_reschedule_dynamic_option(t.registration_id,p_offer,t.deadline_at);
 if option is null then raise exception 'session_not_available'; end if;
 target:=(option->>'targetSessionId')::uuid;
 if target is null then
  insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,
    lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,
    appointment_day_id,source_offer_id,registration_url,source_location_label,external_session_evidence)
  values('landerware_public_offer','scheduled','operational',(option->>'courseId')::uuid,(option->>'startsAt')::timestamptz,
    (option->>'endsAt')::timestamptz,'America/New_York',(option->>'startsAt')::timestamptz,(option->>'consumptionEndsAt')::timestamptz,
    (option->>'instructorId')::uuid,(option->>'locationId')::uuid,(option->>'capacity')::integer,'landerware','unlisted','open',
    option->>'externalId',p_offer->>'appointmentDayId',p_offer->>'availabilityBlockId',p_offer->>'registrationUrl',
    option->>'location',jsonb_build_object('selectorOffer',p_offer,'materializedBy','registration_reschedule')) returning id into target;
 end if;
 -- Existing transfer owns financial/provenance/requirements/mirror retirement and durable mail.
 -- Any exception below rolls back materialization as well as the transfer.
 v_result:=public.confirm_registration_reschedule(p_token_sha256,target,array[option->>'externalId']);
 v_result:=v_result||jsonb_build_object('selectionId',p_offer->>'selectionId');
 update public.registration_reschedule_links set result=v_result where id=t.id;
 return v_result;
end $$;

revoke all on function public.registration_reschedule_dynamic_option(uuid,jsonb,timestamptz),
 public.registration_reschedule_dynamic_targets(text,jsonb),public.confirm_registration_reschedule_dynamic(text,jsonb) from public,anon,authenticated;
grant execute on function public.registration_reschedule_dynamic_option(uuid,jsonb,timestamptz),
 public.registration_reschedule_dynamic_targets(text,jsonb),public.confirm_registration_reschedule_dynamic(text,jsonb) to service_role;
commit;
