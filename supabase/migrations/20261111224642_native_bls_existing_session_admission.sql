-- Additive BLS admission only. No activation, binding, price, capacity or occupancy writes.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';

-- One STABLE statement snapshot for publication; mutation callers separately
-- serialize these dependencies before invoking this predicate.
create function public.native_bls_session_booking_ready(p_session public.class_sessions)
returns boolean language sql stable security invoker set search_path='' as $function$
 select coalesce(
  p_session.record_scope='operational' and p_session.registration_backend='landerware'
  and p_session.resource_id is null
  and p_session.visibility='public' and p_session.registration_status='open'
  and p_session.status in ('scheduled','active') and p_session.start_at>now()
  and isfinite(p_session.start_at) and isfinite(p_session.end_at) and isfinite(p_session.consumption_end_at)
  and p_session.end_at>p_session.start_at and p_session.consumption_end_at>=p_session.end_at
  and p_session.consumption_start_at=p_session.start_at
  and p_session.consumption_end_at<=p_session.start_at+interval '1 day'
  and exists(select 1 from public.native_full_course_policy where policy_key='bls-full'
   and enabled and verified and nullif(trim(evidence),'') is not null)
  and exists(select 1 from public.native_full_course_public_policy where scope_id='brian-shipyard-b.v1'
   and enabled and publication_enabled and verified and nullif(trim(evidence),'') is not null
   and p_session.end_at=p_session.start_at+make_interval(mins=>instruction_minutes)
   and p_session.consumption_end_at=p_session.end_at+make_interval(mins=>cleanup_minutes)
   and p_session.max_students between 1 and max_students)
  and exists(
   select 1 from public.courses c
   join public.people instructor on instructor.id=p_session.lead_instructor_id
   join public.locations venue on venue.id=p_session.location_id
   join public.landerware_registration_profiles profile on profile.profile_key=c.registration_profile_key
   join public.landerware_registration_catalog catalog on catalog.course_id=c.enrollware_course_id
   where c.id=p_session.course_id
    and (c.enrollware_course_id,c.course_key) in (('209806','aha-bls-provider'),('359474','aha-bls-provider-renewal'))
    and (select count(*) from public.courses other where other.enrollware_course_id=c.enrollware_course_id)=1
    and c.max_students_default>0 and p_session.max_students<=c.max_students_default
    and instructor.person_key='brian' and instructor.display_name='Brian Ennis' and instructor.active
    and (select count(*) from public.people other where other.person_key='brian')=1
    and venue.location_key='910cpr-office-shipyard' and venue.scheduling_status='active'
    and (select count(*) from public.locations other where other.location_key='910cpr-office-shipyard')=1
    and profile.course_id=c.course_key and profile.active and profile.registration_mode='native_public_checkout'
    and profile.version>0 and profile.form_schema->>'schemaVersion'='native-checkout.form.v1'
    and profile.form_schema->>'inventory_kind'='scheduled_session_v1'
    and catalog.active and catalog.currency='usd' and catalog.unit_amount>0
    and c.base_price*100=catalog.unit_amount::numeric
    and exists(select 1 from public.instructor_qualifications q
     where q.instructor_id=instructor.id and q.course_id=c.id
      and q.qualification_key='aha-bls-instructor:'||c.enrollware_course_id
      and q.status='active' and q.expires_at is not null and isfinite(q.expires_at)
      and q.expires_at>=p_session.consumption_end_at)
    and not exists(select 1 from public.instructor_qualifications q
     where q.instructor_id=instructor.id and q.course_id=c.id
      and (q.qualification_key is distinct from 'aha-bls-instructor:'||c.enrollware_course_id
       or q.status is distinct from 'active' or q.expires_at is null or not isfinite(q.expires_at)
       or q.expires_at<p_session.consumption_end_at))
    and not exists(select 1 from public.courses other
     join public.landerware_registration_profiles op on op.profile_key=other.registration_profile_key
     where op.active and op.registration_mode='native_public_checkout' and other.id<>c.id
      and exists(select 1 from jsonb_array_elements(case when jsonb_typeof(op.form_schema->'public_aliases')='array'
       then op.form_schema->'public_aliases' else '[]'::jsonb end) alias
       where alias->>'public_course_id'=c.enrollware_course_id and alias->>'context' is null))
  ),false);
$function$;

-- Table SHARE locks also prevent newly inserted revocations, duplicate mappings
-- and cross-profile aliases. Existing service-role UPDATE rights permit them.
-- READ COMMITTED is required: an older REPEATABLE READ snapshot cannot certify
-- a revocation that committed before an awaited lock was acquired.
create function public.native_bls_lock_booking_dependencies()
returns void language plpgsql volatile security invoker set search_path='' as $function$
begin
 if current_setting('transaction_isolation')<>'read committed' then
  raise exception 'native_bls_admission_isolation_required';
 end if;
 lock table public.courses,public.people,public.locations,public.instructor_qualifications,
  public.native_full_course_policy,public.native_full_course_public_policy,
  public.landerware_registration_profiles,public.landerware_registration_catalog in share mode nowait;
exception when lock_not_available then raise exception 'session_not_available';
end $function$;
revoke all on function public.native_bls_session_booking_ready(public.class_sessions),public.native_bls_lock_booking_dependencies() from public,anon,authenticated;
grant execute on function public.native_bls_session_booking_ready(public.class_sessions),public.native_bls_lock_booking_dependencies() to service_role;

-- Patch only reviewed definitions; reject drift before replacing any code.
do $patch$
declare signature text; installed text; definition text; anchor text; replacement text;
begin
 signature:='public.native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if md5(installed) is distinct from '01d82d2d76eacf221becb16e01a3535c' then raise exception 'native_bls_creator_source_drift'; end if;
 anchor:=' select enrollware_course_id into v_course from public.courses where id=s.course_id;';
 replacement:=E' -- Freeze mapping before classifying this already-locked session. NOWAIT\n -- avoids a lock-order cycle with a concurrent administrative edit.\n begin lock table public.courses in share mode nowait;\n exception when lock_not_available then raise exception ''session_not_available''; end;\n'||anchor;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_mapping_anchor_missing'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 definition:=replace(definition,anchor,replacement);
 anchor:=' select * into c from public.landerware_registration_catalog where course_id=trim(p_course_id) and active;';
 replacement:=E' if v_course in (''209806'',''359474'') then\n  -- The class row was already awaited and locked above. The following separate\n  -- statement gets a fresh snapshot after every dependency lock is acquired.\n  perform public.native_bls_lock_booking_dependencies();\n  if not public.native_bls_session_booking_ready(s) then raise exception ''session_not_available''; end if;\n end if;\n'||anchor;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_creator_anchor_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=' insert into public.landerware_public_orders(checkout_runtime_version,idempotency_key,request_fingerprint,';
 replacement:=E' -- Existing-session admission must still be in the future after any wait.\n -- Do not change the STABLE snapshot reader or earlier durable replay branch.\n if v_course in (''209806'',''359474'') and s.start_at<=clock_timestamp() then raise exception ''session_not_available''; end if;\n'||anchor;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_insert_anchor_missing'; end if;
 execute replace(definition,anchor,replacement);

 signature:='public.native_scheduling_seat_snapshot(uuid)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if md5(installed) not in ('ab0dac5a20dafaf136f9e45635d1783e','c77699d212430e51af1235f56b6abd40') or installed is null then
  raise exception 'native_bls_snapshot_source_drift';
 end if;
 anchor:=' where c.id=s.course_id and c.enrollware_course_id in (''209806'',''359474'')';
 replacement:=anchor||E'\n   and public.native_bls_session_booking_ready(s)';
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_snapshot_anchor_missing'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 execute replace(definition,anchor,replacement);
end $patch$;
commit;
