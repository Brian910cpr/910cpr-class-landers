-- Existing canonical classroom sessions only; independently default-off.
-- No class creation, course/profile/catalog mutation or dynamic offer extension.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
create table public.native_pediatric_existing_session_policy (
 public_course_id text primary key check(public_course_id='351632'),
 course_id uuid not null check(course_id='0689a2c5-c507-4e8a-b94c-15e5c5689e28'::uuid),
 course_key text not null check(course_key='aha-heartsaver-pediatric-fa-cpr-aed'),
 profile_key text not null check(profile_key='native_heartsaver_351632_draft'),
 policy_key text not null unique check(policy_key='heartsaver-pediatric-existing:351632.v1'),
 enabled boolean not null default false,
 publication_enabled boolean not null default false,
 verified boolean not null default false,
 evidence text,
 instruction_minutes integer check(instruction_minutes between 1 and 720),
 setup_minutes integer check(setup_minutes between 0 and 240),
 cleanup_minutes integer check(cleanup_minutes between 0 and 240),
 timing_evidence text,
 max_students integer check(max_students between 1 and 100),
 capacity_evidence text,
 unit_amount integer not null default 9500 check(unit_amount>0),
 source_qualification_id uuid,
 qualification_scope_evidence text not null default 'https://cpr.heart.org/en/resources/faqs/course-faqs'
  check(qualification_scope_evidence='https://cpr.heart.org/en/resources/faqs/course-faqs'),
 updated_at timestamptz not null default now(),
 constraint reviewed_pediatric_existing_policy check(not enabled or
  (verified and nullif(trim(evidence),'') is not null
   and instruction_minutes is not null and setup_minutes is not null and cleanup_minutes is not null
   and nullif(trim(timing_evidence),'') is not null and max_students is not null
   and nullif(trim(capacity_evidence),'') is not null and source_qualification_id is not null))
);
-- Timing and capacity remain unknown. No hosted defaults are treated as review.
insert into public.native_pediatric_existing_session_policy
 (public_course_id,course_id,course_key,profile_key,policy_key)
 values('351632','0689a2c5-c507-4e8a-b94c-15e5c5689e28','aha-heartsaver-pediatric-fa-cpr-aed',
 'native_heartsaver_351632_draft','heartsaver-pediatric-existing:351632.v1');
alter table public.native_pediatric_existing_session_policy enable row level security;
revoke all on public.native_pediatric_existing_session_policy from public,anon,authenticated;
grant select,insert,update,delete on public.native_pediatric_existing_session_policy to service_role;
create policy native_pediatric_existing_service_access on public.native_pediatric_existing_session_policy
 for all to service_role using(true) with check(true);
do $$ begin
 if (select count(*) from public.courses where enrollware_course_id='351632')<>1
  or not exists(select 1 from public.courses where id='0689a2c5-c507-4e8a-b94c-15e5c5689e28'
   and course_key='aha-heartsaver-pediatric-fa-cpr-aed' and enrollware_course_id='351632')
 then raise exception 'pediatric_canonical_identity_mismatch'; end if;
end $$;

-- AHA permits the existing BLS instructor qualification to teach Pediatric.
-- The explicit source reference must be live and finite; no credential is minted.
create function public.native_pediatric_existing_session_ready(p_through timestamptz default now())
returns boolean language sql stable security invoker set search_path='' as $$
 select exists(select 1 from public.native_pediatric_existing_session_policy scope
  join public.courses c on c.id=scope.course_id and c.course_key=scope.course_key and c.enrollware_course_id=scope.public_course_id
  join public.landerware_registration_profiles profile on profile.profile_key=scope.profile_key
   and c.registration_profile_key=profile.profile_key and profile.course_id=c.course_key
  join public.landerware_registration_catalog catalog on catalog.course_id=scope.public_course_id
  join public.instructor_qualifications source on source.id=scope.source_qualification_id
  join public.courses bls on bls.id=source.course_id and bls.course_key='aha-bls-provider' and bls.enrollware_course_id='209806'
  join public.people instructor on instructor.id=source.instructor_id and instructor.person_key='brian' and instructor.display_name='Brian Ennis' and instructor.active
  where scope.public_course_id='351632' and scope.enabled and scope.verified
   and isfinite(p_through) and p_through>=now()
   and nullif(trim(scope.evidence),'') is not null and nullif(trim(scope.timing_evidence),'') is not null
   and nullif(trim(scope.capacity_evidence),'') is not null
   and scope.instruction_minutes is not null and scope.setup_minutes is not null and scope.cleanup_minutes is not null and scope.max_students is not null
   and profile.active and profile.registration_mode='native_public_checkout' and profile.version>0 and profile.session_policy='required'
   and profile.form_schema->>'schemaVersion'='native-checkout.form.v1' and profile.form_schema->>'inventory_kind'='scheduled_session_v1'
   and profile.required_fields='["first_name","last_name","email","phone"]'::jsonb
   and profile.requirements='[]'::jsonb and profile.addons='[]'::jsonb
   and jsonb_typeof(coalesce(profile.form_schema->'public_aliases','[]'::jsonb))='array'
   and not exists(select 1 from jsonb_array_elements(case when jsonb_typeof(profile.form_schema->'public_aliases')='array' then profile.form_schema->'public_aliases' else '[]'::jsonb end) alias
    where jsonb_typeof(alias)<>'object' or alias->>'public_course_id' is distinct from '351632' or alias->>'context' is not null)
   and profile.form_schema->'option_groups'='[]'::jsonb and profile.form_schema->'default_choices'='[]'::jsonb
   and catalog.active and catalog.currency='usd' and catalog.unit_amount=scope.unit_amount
   and c.base_price*100=catalog.unit_amount::numeric
   and source.qualification_key='aha-bls-instructor:209806' and source.status='active'
   and source.expires_at is not null and isfinite(source.expires_at) and source.expires_at>=p_through
   and not exists(select 1 from public.instructor_qualifications q
    where q.instructor_id=instructor.id and q.course_id in (bls.id,c.id)
     and (q.status is distinct from 'active' or (q.expires_at is not null and (not isfinite(q.expires_at) or q.expires_at<p_through))
      or (q.course_id=bls.id and (q.qualification_key is distinct from 'aha-bls-instructor:209806' or q.expires_at is null))))
   and (select count(*) from public.courses other where other.enrollware_course_id='351632')=1
   and (select count(*) from public.courses other where other.enrollware_course_id='209806')=1
   and (select count(*) from public.people other where other.person_key='brian')=1
   and not exists(select 1 from public.courses other
    join public.landerware_registration_profiles op on op.profile_key=other.registration_profile_key
    where op.active and op.registration_mode='native_public_checkout'
     and exists(select 1 from jsonb_array_elements(case when jsonb_typeof(op.form_schema->'public_aliases')='array'
      then op.form_schema->'public_aliases' else '[]'::jsonb end) alias
      where (alias->>'public_course_id'='351632' and other.id<>c.id)
       or (other.id=c.id and alias->>'public_course_id' is distinct from '351632'))));
$$;
create function public.native_pediatric_session_booking_ready(p_session public.class_sessions)
returns boolean language sql stable security invoker set search_path='' as $$
 select coalesce(p_session.course_id='0689a2c5-c507-4e8a-b94c-15e5c5689e28'::uuid
  and p_session.external_course_id='351632' and p_session.record_scope='operational'
  and p_session.external_class_id ~ '^([0-9]+|lw-[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})$'
  and p_session.registration_backend='landerware' and p_session.resource_id is null
  and p_session.visibility='public' and p_session.registration_status='open'
  and p_session.status in ('scheduled','active') and p_session.start_at>now()
  and isfinite(p_session.start_at) and isfinite(p_session.end_at)
  and isfinite(p_session.consumption_start_at) and isfinite(p_session.consumption_end_at)
  and (select count(*) from public.class_sessions other where other.external_class_id=p_session.external_class_id and other.record_scope='operational')=1
  and exists(select 1 from public.native_pediatric_existing_session_policy scope
   join public.instructor_qualifications source on source.id=scope.source_qualification_id
   join public.locations venue on venue.id=p_session.location_id
   where scope.course_id=p_session.course_id and scope.enabled and scope.publication_enabled
    and public.native_pediatric_existing_session_ready(p_session.consumption_end_at)
    and p_session.lead_instructor_id=source.instructor_id
    and p_session.end_at=p_session.start_at+make_interval(mins=>scope.instruction_minutes)
    and p_session.consumption_start_at=p_session.start_at-make_interval(mins=>scope.setup_minutes)
    and p_session.consumption_end_at=p_session.end_at+make_interval(mins=>scope.cleanup_minutes)
    and p_session.max_students between 1 and scope.max_students
    and venue.location_key='910cpr-office-shipyard' and venue.scheduling_status='active'
    and (select count(*) from public.locations other where other.location_key='910cpr-office-shipyard')=1)
  -- Explicit canonical session adoption only. A generated-session witness does
  -- not make Pediatric dynamic materialization part of this feature.
  and exists(select 1 from public.landerware_session_authority_events e
   where e.class_session_id=p_session.id and e.enabled
    and e.revision=(select max(latest.revision) from public.landerware_session_authority_events latest where latest.class_session_id=p_session.id)
    and e.session_identity=jsonb_build_array(p_session.course_id,p_session.start_at,p_session.end_at,p_session.consumption_start_at,p_session.consumption_end_at,
     p_session.lead_instructor_id,p_session.location_id,p_session.resource_id,p_session.organization_id,p_session.external_class_id,p_session.record_scope)),false);
$$;
create function public.native_pediatric_existing_session_runtime_policy()
returns jsonb language sql stable security invoker set search_path='' as $$
 select jsonb_build_object('schemaVersion','native-pediatric-existing-session-policy.v1',
  'observedAt',statement_timestamp(),'validUntil',statement_timestamp()+interval '15 minutes',
  'existingSessionEnabled',public.native_pediatric_existing_session_ready(),
  'nativePublicationEnabled',public.native_pediatric_existing_session_ready() and scope.publication_enabled,
  'materializationEnabled',false,'publicCourseId',scope.public_course_id,'canonicalCourseId',scope.course_id,
  'courseKey',scope.course_key,'coursePolicyKey',scope.policy_key,'profileKey',scope.profile_key,
  'profileVersion',case when public.native_pediatric_existing_session_ready() then profile.version else null end,
  'packageCode','full-course','pageKey','heartsaver','unitAmount',scope.unit_amount,'currency','usd',
  'instructionMinutes',scope.instruction_minutes,'setupMinutes',scope.setup_minutes,'cleanupMinutes',scope.cleanup_minutes,'maxStudents',scope.max_students,
  'qualificationValidThrough',case when public.native_pediatric_existing_session_ready() and scope.publication_enabled
   then (select min(q.expires_at) from public.instructor_qualifications q where q.instructor_id=source.instructor_id
    and q.course_id in (source.course_id,scope.course_id) and q.status='active') else null end)
 from public.native_pediatric_existing_session_policy scope
 left join public.instructor_qualifications source on source.id=scope.source_qualification_id
 left join public.landerware_registration_profiles profile on profile.profile_key=scope.profile_key
 where scope.public_course_id='351632';
$$;
create function public.native_pediatric_lock_booking_dependencies()
returns void language plpgsql volatile security invoker set search_path='' as $$
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'native_pediatric_admission_isolation_required'; end if;
 lock table public.class_sessions,public.courses,public.people,public.locations,public.instructor_qualifications,
  public.native_pediatric_existing_session_policy,public.landerware_registration_profiles,
  public.landerware_registration_catalog in share mode nowait;
exception when lock_not_available then raise exception 'session_not_available';
end $$;
revoke all on function public.native_pediatric_existing_session_ready(timestamptz),public.native_pediatric_session_booking_ready(public.class_sessions),
 public.native_pediatric_existing_session_runtime_policy(),public.native_pediatric_lock_booking_dependencies() from public,anon,authenticated;
grant execute on function public.native_pediatric_existing_session_ready(timestamptz),public.native_pediatric_session_booking_ready(public.class_sessions),
 public.native_pediatric_existing_session_runtime_policy(),public.native_pediatric_lock_booking_dependencies() to service_role;

-- Append-only authority events retain their existing service ACL. Serialize new
-- Pediatric evidence with the same class row as admission, including direct
-- service INSERTs that do not call the normal authority recorder.
create function public.native_pediatric_authority_append_guard()
returns trigger language plpgsql security invoker set search_path='' as $$
begin
 perform 1 from public.class_sessions s where s.id=new.class_session_id
  and (s.course_id='0689a2c5-c507-4e8a-b94c-15e5c5689e28'::uuid
   or new.session_identity->>0='0689a2c5-c507-4e8a-b94c-15e5c5689e28') for update;
 return new;
end $$;
revoke all on function public.native_pediatric_authority_append_guard() from public,anon,authenticated;
grant execute on function public.native_pediatric_authority_append_guard() to service_role;
create trigger native_pediatric_authority_append_guard before insert on public.landerware_session_authority_events
 for each row execute function public.native_pediatric_authority_append_guard();

-- Hash-gated additive guards preserve existing orders, authority and occupancy.
do $patch$
declare signature text:='public.native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)'; installed text; definition text; anchor text; replacement text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if md5(installed) is distinct from '0c9ba795285f8c76871aa592e01802fc' then raise exception 'pediatric_native_checkout_create_order_source_drift'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$old$ select * into c from public.landerware_registration_catalog where course_id=trim(p_course_id) and active;$old$;
 replacement:=$new$ if v_course='351632' or s.course_id='0689a2c5-c507-4e8a-b94c-15e5c5689e28'::uuid or s.external_course_id='351632' then
  perform public.native_pediatric_lock_booking_dependencies();
  if not public.native_pediatric_session_booking_ready(s) then raise exception 'session_not_available'; end if;
 end if;
 select * into c from public.landerware_registration_catalog where course_id=trim(p_course_id) and active;$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'pediatric_native_checkout_create_order_anchor_0_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$old$ insert into public.landerware_public_orders(checkout_runtime_version,idempotency_key,request_fingerprint,$old$;
 replacement:=$new$ if v_course='351632' and s.start_at<=clock_timestamp() then raise exception 'session_not_available'; end if;
 insert into public.landerware_public_orders(checkout_runtime_version,idempotency_key,request_fingerprint,$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'pediatric_native_checkout_create_order_anchor_1_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
end $patch$;
do $patch$
declare signature text:='public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)'; installed text; definition text; anchor text; replacement text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if md5(installed) is distinct from '9bb3ff266f64727cdcaee5a24aa02aa7' then raise exception 'pediatric_reserve_native_checkout_order_source_drift'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$old$ select * into p from public.landerware_registration_profiles where profile_key=p_profile_key and version=p_version and active and registration_mode='native_public_checkout' for share;$old$;
 replacement:=$new$ -- Preserve saved receipt replay above all new admission rules.
 if p_profile_key='native_heartsaver_351632_draft' then
  if nullif(p_external_id,'') is null or coalesce(p_context,'')<>'' then raise exception 'session_not_available'; end if;
  perform 1 from public.class_sessions where external_class_id=p_external_id and record_scope='operational' order by updated_at desc for update;
  perform public.native_pediatric_lock_booking_dependencies();
 end if;
 select * into p from public.landerware_registration_profiles where profile_key=p_profile_key and version=p_version and active and registration_mode='native_public_checkout' for share;$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'pediatric_reserve_native_checkout_order_anchor_0_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$old$ if c.id is null then raise exception 'native_profile_not_configured'; end if;$old$;
 replacement:=$new$ if c.id is null then raise exception 'native_profile_not_configured'; end if;
 if c.id='0689a2c5-c507-4e8a-b94c-15e5c5689e28'::uuid or c.enrollware_course_id='351632' then
  if p_profile_key<>'native_heartsaver_351632_draft' or nullif(p_external_id,'') is null or coalesce(p_context,'')<>''
   then raise exception 'session_not_available'; end if;
 end if;$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'pediatric_reserve_native_checkout_order_anchor_1_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
end $patch$;
do $patch$
declare signature text:='public.native_checkout_profile(text,text)'; installed text; definition text; anchor text; replacement text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if md5(installed) is distinct from 'd39ae8a6af666982e7ff6d68ca8ca343' then raise exception 'pediatric_native_checkout_profile_source_drift'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$old$ if p.profile_key is null or p.course_id is distinct from c.course_key then raise exception 'native_profile_not_configured'; end if;$old$;
 replacement:=$new$ if p.profile_key is null or p.course_id is distinct from c.course_key then raise exception 'native_profile_not_configured'; end if;
 if p_public_course_id='351632' or c.enrollware_course_id='351632' or c.id='0689a2c5-c507-4e8a-b94c-15e5c5689e28'::uuid then
  if p_public_course_id is distinct from '351632' or c.id is distinct from '0689a2c5-c507-4e8a-b94c-15e5c5689e28'::uuid
   or coalesce(p_context,'')<>'' or not public.native_pediatric_existing_session_ready()
   or not exists(select 1 from public.native_pediatric_existing_session_policy where publication_enabled)
   then raise exception 'native_registration_unavailable'; end if;
 end if;$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'pediatric_native_checkout_profile_anchor_0_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
end $patch$;
do $patch$
declare signature text:='public.native_scheduling_seat_snapshot(uuid)'; installed text; definition text; anchor text; replacement text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if md5(installed) is distinct from '1db090312bfa83795580538f5ad04f74' then raise exception 'pediatric_native_scheduling_seat_snapshot_source_drift'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$old$booking jsonb; skills_booking jsonb; heartsaver_booking jsonb;$old$;
 replacement:=$new$booking jsonb; skills_booking jsonb; heartsaver_booking jsonb; pediatric_booking jsonb;$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'pediatric_native_scheduling_seat_snapshot_anchor_0_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$old$ return jsonb_build_object('registrationAuthority',authority,'authorityRevision',revision,'generatedIdentity',witness,$old$;
 replacement:=$new$ select jsonb_build_object('schemaVersion','native-pediatric-session-booking.v1',
  'publicCourseId',scope.public_course_id,'canonicalCourseId',scope.course_id,'coursePolicyKey',scope.policy_key,
  'packageCode','full-course','unitAmount',scope.unit_amount,'currency','usd','profileKey',scope.profile_key,'profileVersion',p.version,
  'sourceSessionId',s.external_class_id,'identityWitness',coalesce(witness,md5(identity::text)),
  'capacity',v_capacity,'remaining',v_capacity-v_registered-v_holds-v_reserved,
  'instructionMinutes',scope.instruction_minutes,'setupMinutes',scope.setup_minutes,'cleanupMinutes',scope.cleanup_minutes)
 into pediatric_booking
 from public.native_pediatric_existing_session_policy scope
 join public.landerware_registration_profiles p on p.profile_key=scope.profile_key
 where scope.course_id=s.course_id and public.native_pediatric_session_booking_ready(s)
  and v_capacity<=scope.max_students and v_capacity-v_registered-v_holds-v_reserved>0
  and not exists(select 1 from public.landerware_public_orders o where o.class_session_id=s.id and public.native_checkout_unresolved_payment(o));
 return jsonb_build_object('registrationAuthority',authority,'authorityRevision',revision,'generatedIdentity',witness,$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'pediatric_native_scheduling_seat_snapshot_anchor_1_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$old$'heartsaverBooking',heartsaver_booking);$old$;
 replacement:=$new$'heartsaverBooking',heartsaver_booking,'pediatricBooking',pediatric_booking);$new$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'pediatric_native_scheduling_seat_snapshot_anchor_2_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
end $patch$;
commit;
