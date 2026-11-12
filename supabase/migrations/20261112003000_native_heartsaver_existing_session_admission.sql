-- Additive native Heartsaver admission. No activation, binding or commercial writes.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';

-- One canonical predicate for published seats and new mutations. Qualification
-- remains derived from the existing explicitly referenced BLS source credential.
create function public.native_heartsaver_session_booking_ready(p_session public.class_sessions)
returns boolean language sql stable security invoker set search_path='' as $function$
 select coalesce(
  p_session.record_scope='operational' and p_session.registration_backend='landerware'
  and p_session.resource_id is null
  and p_session.visibility='public' and p_session.registration_status='open'
  and p_session.status in ('scheduled','active') and p_session.start_at>now()
  and isfinite(p_session.start_at) and isfinite(p_session.end_at)
  and isfinite(p_session.consumption_start_at) and isfinite(p_session.consumption_end_at)
  and exists(select 1 from public.native_heartsaver_full_course_policy scope
   join public.courses c on c.id=scope.course_id
   join public.instructor_qualifications source on source.id=scope.source_qualification_id
   join public.people instructor on instructor.id=source.instructor_id
   join public.locations venue on venue.id=p_session.location_id
   where scope.public_course_id in ('209809','344085') and scope.course_id=p_session.course_id
    and scope.enabled and scope.publication_enabled
    and public.native_heartsaver_full_course_ready(scope.public_course_id,p_session.consumption_end_at)
    and p_session.external_course_id=scope.public_course_id
    and p_session.lead_instructor_id=source.instructor_id
    and isfinite(source.expires_at)
    and p_session.end_at=p_session.start_at+make_interval(mins=>scope.instruction_minutes)
    and p_session.consumption_start_at=p_session.start_at
    and p_session.consumption_end_at=p_session.end_at+make_interval(mins=>scope.cleanup_minutes)
    and p_session.max_students between 1 and scope.max_students
    and (select count(*) from public.people other where other.person_key='brian')=1
    and (select count(*) from public.courses other where other.enrollware_course_id='209806')=1
    and venue.location_key='910cpr-office-shipyard' and venue.scheduling_status='active'
    and (select count(*) from public.locations other where other.location_key='910cpr-office-shipyard')=1
    -- Missing target credentials are not fabricated. Existing explicit target
    -- revocations still win; an infinite asserted expiry is never valid proof.
    and not exists(select 1 from public.instructor_qualifications q
     where q.instructor_id=source.instructor_id and q.course_id in (source.course_id,scope.course_id)
      and q.expires_at is not null and not isfinite(q.expires_at))
    and not exists(select 1 from public.courses other
     join public.landerware_registration_profiles op on op.profile_key=other.registration_profile_key
     where op.active and op.registration_mode='native_public_checkout' and other.id<>c.id
      and exists(select 1 from jsonb_array_elements(case when jsonb_typeof(op.form_schema->'public_aliases')='array'
       then op.form_schema->'public_aliases' else '[]'::jsonb end) alias
       where alias->>'public_course_id'=scope.public_course_id and alias->>'context' is null))
  ),false);
$function$;

-- Prevent concurrent edits and inserted revocations/aliases until order commit.
-- A fresh READ COMMITTED snapshot after these locks must see committed changes.
create function public.native_heartsaver_lock_booking_dependencies()
returns void language plpgsql volatile security invoker set search_path='' as $function$
begin
 if current_setting('transaction_isolation')<>'read committed' then
  raise exception 'native_heartsaver_admission_isolation_required';
 end if;
 lock table public.courses,public.people,public.locations,public.instructor_qualifications,
  public.native_heartsaver_full_course_policy,public.landerware_registration_profiles,
  public.landerware_registration_catalog in share mode nowait;
exception when lock_not_available then raise exception 'session_not_available';
end $function$;
revoke all on function public.native_heartsaver_session_booking_ready(public.class_sessions),public.native_heartsaver_lock_booking_dependencies() from public,anon,authenticated;
grant execute on function public.native_heartsaver_session_booking_ready(public.class_sessions),public.native_heartsaver_lock_booking_dependencies() to service_role;

-- Only replace reviewed definitions. Unknown independent changes abort atomically.
do $patch$
declare signature text; installed text; definition text; anchor text; replacement text;
begin
 -- Keep the existing derived qualification method, but require finite source
 -- evidence across dynamic publication and seated admission alike.
 signature:='public.native_heartsaver_full_course_ready(text,timestamp with time zone)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if md5(installed) is distinct from '5f43ce08bb726ec6e320f444abcf6772' then raise exception 'native_heartsaver_ready_source_drift'; end if;
 anchor:=$old$   and source.status='active' and source.expires_at is not null and source.expires_at>=p_through$old$;
 replacement:=anchor||$new$
   and isfinite(source.expires_at)
   and not exists(select 1 from public.instructor_qualifications contradictory
    where contradictory.instructor_id=instructor.id and contradictory.course_id=bls.id
     and (contradictory.qualification_key is distinct from 'aha-bls-instructor:209806'
      or contradictory.status is distinct from 'active' or contradictory.expires_at is null
      or not isfinite(contradictory.expires_at) or contradictory.expires_at<p_through))$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_heartsaver_ready_anchor_missing'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 execute replace(definition,anchor,replacement);
 signature:='public.native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if installed is null or md5(installed) not in ('a4d3860269ecb38eb7619be5a47794d8') then raise exception 'native_heartsaver_creator_source_drift'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$old$ select * into c from public.landerware_registration_catalog where course_id=trim(p_course_id) and active;$old$;
 replacement:=$new$ if v_course in ('209809','344085') then
  perform public.native_heartsaver_lock_booking_dependencies();
  if not public.native_heartsaver_session_booking_ready(s) then raise exception 'session_not_available'; end if;
 end if;
 select * into c from public.landerware_registration_catalog where course_id=trim(p_course_id) and active;$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_heartsaver_creator_anchor_0_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$old$ insert into public.landerware_public_orders(checkout_runtime_version,idempotency_key,request_fingerprint,$old$;
 replacement:=$new$ if v_course in ('209809','344085') and s.start_at<=clock_timestamp() then raise exception 'session_not_available'; end if;
 insert into public.landerware_public_orders(checkout_runtime_version,idempotency_key,request_fingerprint,$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_heartsaver_creator_anchor_1_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
 signature:='public.native_scheduling_seat_snapshot(uuid)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if installed is null or md5(installed) not in ('2c7a07bbe6ac06c5237f60e4110c7ef9') then raise exception 'native_heartsaver_snapshot_source_drift'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$old$ where s.course_id=scope.course_id and scope.public_course_id in ('209809','344085')$old$;
 replacement:=$new$ where s.course_id=scope.course_id and scope.public_course_id in ('209809','344085')
  and public.native_heartsaver_session_booking_ready(s)$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_heartsaver_snapshot_anchor_0_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
 signature:='public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if installed is null or md5(installed) not in ('5c751ffba0f7897367570dd00be895a7') then raise exception 'native_heartsaver_reserve_source_drift'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$old$  if c.enrollware_course_id in ('209809','344085') then
   -- Existing-session claims need the same protected qualification snapshot as
   -- dynamic materialization. Recheck after the class lock, not before waiting.
   perform 1 from public.class_sessions where external_class_id=p_external_id and record_scope='operational' and course_id=c.id for update;
   lock table public.courses,public.people,public.locations,public.instructor_qualifications in share mode;
   perform 1 from public.landerware_registration_catalog where course_id=c.enrollware_course_id for share;
   if not exists(select 1 from public.class_sessions s
    join public.native_heartsaver_full_course_policy scope on scope.course_id=s.course_id
    join public.people instructor on instructor.id=s.lead_instructor_id and instructor.person_key='brian' and instructor.display_name='Brian Ennis' and instructor.active
    join public.locations venue on venue.id=s.location_id and venue.location_key='910cpr-office-shipyard' and venue.scheduling_status='active'
    where s.external_class_id=p_external_id and s.record_scope='operational' and s.course_id=c.id and s.max_students<=scope.max_students
     and public.native_heartsaver_full_course_ready(c.enrollware_course_id,coalesce(s.consumption_end_at,s.end_at)))
   then raise exception 'session_not_available'; end if;
  end if;
$old$;
 replacement:=$new$  -- The low-level creator owns the shared locked admission below.
$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_heartsaver_reserve_anchor_0_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$old$ if c.enrollware_course_id in ('209809','344085') then
  perform 1 from public.native_heartsaver_full_course_policy where public_course_id=c.enrollware_course_id for share;
  if not public.native_heartsaver_full_course_ready(c.enrollware_course_id) then raise exception 'native_registration_unavailable'; end if;
 end if;$old$;
 replacement:=$new$ -- Heartsaver new orders validate policy after acquiring the class lock.
 -- Dynamic offers retain their materializer's validation and wall-clock lease.$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_heartsaver_reserve_anchor_1_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$old$ select * into p from public.landerware_registration_profiles where profile_key=p_profile_key and version=p_version and active and registration_mode='native_public_checkout' for share;$old$;
 replacement:=$new$ -- Existing Heartsaver claims acquire their class before profile/policy locks.
 -- Preserve the earlier durable replay branch and every other course's ordering.
 if p_profile_key in ('native_heartsaver_209809_draft','native_heartsaver_344085_draft')
  and nullif(p_external_id,'') is not null then
  perform 1 from public.class_sessions where external_class_id=p_external_id and record_scope='operational' order by updated_at desc for update;
  perform public.native_heartsaver_lock_booking_dependencies();
 end if;
$new$||anchor;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_heartsaver_reserve_anchor_2_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
end $patch$;
commit;
