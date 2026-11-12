-- Additive first-party publication/runtime policy. No activation or canonical-row mutation.
begin;
set local lock_timeout='2s';
-- Refuse to overwrite an independently changed deployed implementation.
-- Normalize CRLF only; all other body changes require a fresh review.
do $$
declare installed_body text;
begin
 select prosrc into installed_body from pg_catalog.pg_proc
 where oid=pg_catalog.to_regprocedure('public.native_full_course_option(text,jsonb)');
 if md5(replace(installed_body,E'\r\n',E'\n')) is distinct from 'f4e103126312d0ed6622fef28639378b' then
  raise exception 'native_full_course_option_source_drift';
 end if;
end $$;
create table public.native_full_course_public_policy (
 scope_id text primary key check(scope_id='brian-shipyard-b.v1'),
 enabled boolean not null default false,
 publication_enabled boolean not null default false,
 verified boolean not null default false,
 evidence text,
 instruction_minutes integer not null default 120 check(instruction_minutes=120),
 cleanup_minutes integer not null default 30 check(cleanup_minutes=30),
 max_students integer not null default 6 check(max_students between 1 and 6),
 updated_at timestamptz not null default now()
);
-- Timing: data/config/layered_scheduling_policy.json full_instruction_minutes/full_cleanup_minutes.
-- Capacity: data/inventory/course_consumption_rules.json default_capacity for 209806 and 359474.
-- Configuration is retained evidence, not an activation or qualification assertion.
insert into public.native_full_course_public_policy(scope_id) values('brian-shipyard-b.v1');
alter table public.native_full_course_public_policy enable row level security;
revoke all on public.native_full_course_public_policy from public,anon,authenticated;
grant select,insert,update,delete on public.native_full_course_public_policy to service_role;
create policy native_full_course_public_service_access on public.native_full_course_public_policy
 for all to service_role using(true) with check(true);

create or replace function public.native_full_course_runtime_policy()
returns jsonb language sql stable security invoker set search_path='' as $$
 with base as (
  select exists(select 1 from public.native_full_course_policy where policy_key='bls-full'
   and enabled and verified and nullif(trim(evidence),'') is not null) as enabled
 ), native as (
  select exists(select 1 from public.native_full_course_public_policy where scope_id='brian-shipyard-b.v1'
   and enabled and publication_enabled and verified and nullif(trim(evidence),'') is not null) as enabled
 )
 select jsonb_build_object('materializationEnabled',base.enabled,
  'nativePublicationEnabled',base.enabled and native.enabled,'nativeScopeId','brian-shipyard-b.v1') from base,native;
$$;
revoke all on function public.native_full_course_runtime_policy() from public,anon,authenticated;
grant execute on function public.native_full_course_runtime_policy() to service_role;

create or replace function public.native_full_course_option(p_course_number text,p_offer jsonb)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare
 c public.courses; instructor public.people; venue public.locations;
 target public.class_sessions; starts timestamptz; ends timestamptz; occupied_end timestamptz;
 generated timestamptz; lease timestamptz; proof_observed timestamptz; external_id text; fingerprint text; matches integer;
 native_v2 boolean; native_policy public.native_full_course_public_policy;
 capacity integer; occupied integer; held integer; inventory public.landerware_public_session_inventory;
begin
 if not exists(select 1 from public.native_full_course_policy where policy_key='bls-full' and enabled and verified and nullif(trim(evidence),'') is not null) then return null; end if;
 native_v2:=coalesce(p_offer->>'authority'='native-full-course.v2',false);
 if native_v2 then
  select * into native_policy from public.native_full_course_public_policy where scope_id='brian-shipyard-b.v1'
   and enabled and publication_enabled and verified and nullif(trim(evidence),'') is not null;
  if native_policy.scope_id is null then return null; end if;
 end if;
 select count(*),min(id::text)::uuid into matches,c.id from public.courses where enrollware_course_id=p_course_number;
 if matches<>1 then return null; end if;
 select * into c from public.courses where id=c.id;
 -- V2 owns its public-session policy; never rewrite canonical global defaults.
 if c.max_students_default is null or c.max_students_default<=0 then return null; end if;
 if not native_v2 and (c.duration_minutes is distinct from 120
  or c.cleanup_buffer_minutes is distinct from 30) then return null; end if;
 -- Scope is deliberately limited to the two BLS full-course mappings and the selector's primary room.
 if p_offer->>'kind' is distinct from 'dynamic' or (not native_v2 and p_offer->>'authority' is distinct from 'native-full-course.v1')
  or c.enrollware_course_id not in ('209806','359474')
  or p_offer->>'courseNumber' is distinct from c.enrollware_course_id
  or p_offer->>'instructor' is distinct from 'Brian Ennis'
  or p_offer->>'resource' is distinct from ':: Wilmington; Shipyard Blvd - B'
  or p_offer->>'location' is distinct from ':: Wilmington; Shipyard Blvd'
  or nullif(p_offer->>'availabilityBlockId','') is null
  or (not native_v2 and (coalesce(p_offer->>'appointmentDayId','') !~ '^[0-9]+$'
   or coalesce(p_offer->>'selectionId','') not like 'dynamic:%'))
  or (native_v2 and (p_offer->>'nativeScopeId' is distinct from 'brian-shipyard-b.v1'
   or coalesce(p_offer->>'selectionId','') !~ '^native-full:[a-f0-9]{64}$'
   or p_offer ? 'appointmentDayId' or p_offer ? 'matchedContainerId'))
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
 if native_v2 then
  if coalesce(p_offer->>'proofObservedAt','') !~ 'T.*(Z|[+-][0-9]{2}:[0-9]{2})$' then return null; end if;
  proof_observed:=(p_offer->>'proofObservedAt')::timestamptz;
  if proof_observed is null or proof_observed>generated or proof_observed>now()
   or proof_observed<now()-interval '15 minutes' or lease>proof_observed+interval '15 minutes' then return null; end if;
 end if;
 if native_v2 and (generated>now() or generated<now()-interval '15 minutes'
  or lease>generated+interval '15 minutes' or starts<now()+interval '24 hours' or starts>now()+interval '90 days') then return null; end if;
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
  capacity:=case when native_v2 then least(native_policy.max_students,c.max_students_default) when c.enrollware_course_id='209806' then least(6,c.max_students_default) else c.max_students_default end;
  if capacity is null or capacity<=0 then return null; end if;
 end if;
 return jsonb_build_object('id',p_offer->>'selectionId','targetSessionId',target.id,'externalId',external_id,
  'course',c.name,'courseId',c.id,'instructorId',instructor.id,'locationId',venue.id,'capacity',capacity,
  'startsAt',starts,'endsAt',ends,'consumptionEndsAt',occupied_end,'timezone','America/New_York',
  'location',(select name from public.locations where id=venue.id),'address',
  (select concat_ws(', ',address_line1,address_line2,city,state,postal_code) from public.locations where id=venue.id));
end $$;

revoke all on function public.native_full_course_option(text,jsonb) from public,anon,authenticated;
grant execute on function public.native_full_course_option(text,jsonb) to service_role;
commit;
