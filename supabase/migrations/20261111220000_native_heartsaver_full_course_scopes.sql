-- Narrow, default-off full Heartsaver scopes. No canonical/course/catalog activation.
-- Existing imported course UUIDs are reused. Blended 209808/329495 are excluded.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
create table public.native_heartsaver_full_course_policy (
 public_course_id text primary key,
 course_id uuid not null,
 course_key text not null,
 profile_key text not null,
 scope_id text not null default 'brian-shipyard-b.v1' check(scope_id='brian-shipyard-b.v1'),
 policy_key text not null unique,
 enabled boolean not null default false,
 publication_enabled boolean not null default false,
 verified boolean not null default false,
 evidence text,
 instruction_minutes integer not null,
 cleanup_minutes integer not null,
 max_students integer check(max_students between 1 and 100),
 capacity_evidence text,
 unit_amount integer check(unit_amount>0),
 price_evidence text,
 source_qualification_id uuid,
 -- Optional teaching-material note; not a registration or activation prerequisite.
 instructor_manual_evidence text,
 qualification_scope_evidence text not null default 'https://cpr.heart.org/resources/faqs/course-faqs'
  check(qualification_scope_evidence='https://cpr.heart.org/resources/faqs/course-faqs'),
 updated_at timestamptz not null default now(),
 constraint exact_heartsaver_full_scope check(
  (public_course_id='209809' and course_id='23dfcfa7-4224-46ed-8d45-64d43d5425db'::uuid
   and course_key='aha-heartsaver-fa-cpr-aed' and profile_key='native_heartsaver_209809_draft'
   and policy_key='heartsaver-full:209809.v1' and instruction_minutes=120 and cleanup_minutes=30)
  or (public_course_id='344085' and course_id='306bc81a-0e09-49e1-8910-e05501222eb4'::uuid
   and course_key='hist-course:a3d354b88fbc55fd' and profile_key='native_heartsaver_344085_draft'
   and policy_key='heartsaver-full:344085.v1' and instruction_minutes=90 and cleanup_minutes=15)),
 constraint reviewed_heartsaver_full_scope check(not enabled or
  (verified and nullif(trim(evidence),'') is not null and max_students is not null
   and nullif(trim(capacity_evidence),'') is not null and unit_amount is not null
   and nullif(trim(price_evidence),'') is not null and source_qualification_id is not null))
);
-- Timing comes from layered_scheduling_policy.json, including the explicit
-- 344085 90+15 override. Neither timing nor capacity is copied from BLS.
-- Capacity is unresolved for both. 344085 price is the current first-party $70
-- offer in heartsaver.html and data/config/block_schedule_pages.json, not archive inference.
insert into public.native_heartsaver_full_course_policy
 (public_course_id,course_id,course_key,profile_key,policy_key,instruction_minutes,cleanup_minutes,unit_amount,price_evidence)
values
 ('209809','23dfcfa7-4224-46ed-8d45-64d43d5425db','aha-heartsaver-fa-cpr-aed','native_heartsaver_209809_draft','heartsaver-full:209809.v1',120,30,9500,'existing_native_catalog:209809'),
 ('344085','306bc81a-0e09-49e1-8910-e05501222eb4','hist-course:a3d354b88fbc55fd','native_heartsaver_344085_draft','heartsaver-full:344085.v1',90,15,7000,'https://www.910cpr.com/heartsaver.html?course=344085');
alter table public.native_heartsaver_full_course_policy enable row level security;
revoke all on public.native_heartsaver_full_course_policy from public,anon,authenticated;
grant select,insert,update,delete on public.native_heartsaver_full_course_policy to service_role;
create policy native_heartsaver_full_service_access on public.native_heartsaver_full_course_policy
 for all to service_role using(true) with check(true);
-- Fail rather than inventing courses or adopting a similarly named import.
do $$ begin
 if exists(select 1 from public.native_heartsaver_full_course_policy p
  where (select count(*) from public.courses c where c.id=p.course_id and c.course_key=p.course_key
   and c.enrollware_course_id=p.public_course_id)<>1
   or (select count(*) from public.courses c where c.enrollware_course_id=p.public_course_id)<>1)
 then raise exception 'heartsaver_canonical_identity_mismatch'; end if;
end $$;
-- Current first-party price, inactive. Preserve any independently existing row.
insert into public.landerware_registration_catalog
 (course_id,source,course_name,unit_amount,currency,addons,billing_codes,source_snapshot,active)
values ('344085','reviewed_native_public_site','Heartsaver CPR AED',7000,'usd','[]'::jsonb,'[]'::jsonb,
 '{"url":"https://www.910cpr.com/heartsaver.html?course=344085","configuration":"data/config/block_schedule_pages.json","courseId":"344085","observedDate":"2026-11-11","draft":true}'::jsonb,false)
 on conflict(course_id) do nothing;
-- Reuse existing FA+CPR/AED draft. Add only the absent CPR/AED draft, inactive,
-- unlisted, and UNBOUND. max_students below is a group-order limit, not capacity.
insert into public.landerware_confirmation_templates(template_key,subject_template,body_template,delivery_provider,active)
 values('native-checkout-profile-v1','Your 910CPR registration','Your registration and payment status are tracked by the native checkout.','cloudflare',false)
 on conflict(template_key) do nothing;
insert into public.landerware_registration_profiles
 (profile_key,version,course_id,display_name,listed,registration_mode,session_policy,allowed_entry_contexts,required_fields,requirements,addons,payer_policy,pricing_behavior,confirmation_template_key,form_schema,active)
values ('native_heartsaver_344085_draft',1,'hist-course:a3d354b88fbc55fd','Heartsaver CPR AED',false,'native_public_checkout','required',array[]::text[],
 ' ["first_name","last_name","email","phone"]'::jsonb,'[]'::jsonb,'[]'::jsonb,'{"mode":"customer_pays"}'::jsonb,'{"mode":"catalog_options"}'::jsonb,'native-checkout-profile-v1',
 '{"schemaVersion":"native-checkout.form.v1","inventory_kind":"scheduled_session_v1","fields":[{"key":"first_name","wire":"firstName","type":"text","label":"First name","required":true},{"key":"last_name","wire":"lastName","type":"text","label":"Last name","required":true},{"key":"email","wire":"email","type":"email","label":"Email","required":true},{"key":"phone","wire":"phone","type":"tel","label":"Phone","required":true}],"max_students":10,"default_choices":[],"option_groups":[],"driver_rules":[{"driver":"native_order"}],"back_url":"/heartsaver.html"}'::jsonb,false)
 on conflict(profile_key) do nothing;

-- The mapping references an EXISTING verified BLS qualification. It never creates
-- a separate Heartsaver credential. Source revocation/expiry and explicit target
-- revocation override the derived scope, including after a publication refresh.
create function public.native_heartsaver_full_course_ready(p_course_number text,p_through timestamptz default now())
returns boolean language sql stable security invoker set search_path='' as $$
 select exists(select 1 from public.native_heartsaver_full_course_policy scope
  join public.courses c on c.id=scope.course_id and c.course_key=scope.course_key and c.enrollware_course_id=scope.public_course_id
  join public.landerware_registration_profiles profile on profile.profile_key=scope.profile_key
   and c.registration_profile_key=profile.profile_key and profile.course_id=c.course_key
  join public.landerware_registration_catalog catalog on catalog.course_id=scope.public_course_id
  join public.instructor_qualifications source on source.id=scope.source_qualification_id
  join public.courses bls on bls.id=source.course_id and bls.course_key='aha-bls-provider' and bls.enrollware_course_id='209806'
  join public.people instructor on instructor.id=source.instructor_id and instructor.person_key='brian' and instructor.display_name='Brian Ennis' and instructor.active
  where scope.public_course_id=p_course_number and scope.enabled and scope.verified
   and nullif(trim(scope.evidence),'') is not null and scope.max_students is not null
   and nullif(trim(scope.capacity_evidence),'') is not null and scope.unit_amount is not null
   and nullif(trim(scope.price_evidence),'') is not null
   and profile.active and profile.registration_mode='native_public_checkout' and profile.version>0
   and profile.form_schema->>'schemaVersion'='native-checkout.form.v1' and profile.form_schema->>'inventory_kind'='scheduled_session_v1'
   and catalog.active and catalog.currency='usd' and catalog.unit_amount=scope.unit_amount
   and c.base_price*100=catalog.unit_amount::numeric
   and source.qualification_key='aha-bls-instructor:209806'
   and source.status='active' and source.expires_at is not null and source.expires_at>=p_through
   and not exists(select 1 from public.instructor_qualifications revoked
    where revoked.instructor_id=instructor.id and revoked.course_id in (bls.id,c.id)
     and (revoked.status is distinct from 'active' or (revoked.expires_at is not null and revoked.expires_at<p_through)))
   and (select count(*) from public.courses other where other.enrollware_course_id=scope.public_course_id)=1);
$$;
create function public.native_full_course_runtime_policy(p_course_number text)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare scope public.native_heartsaver_full_course_policy; ready boolean;
begin
 if p_course_number in ('209806','359474') then return public.native_full_course_runtime_policy(); end if;
 select * into scope from public.native_heartsaver_full_course_policy where public_course_id=p_course_number;
 if scope.public_course_id is null then return jsonb_build_object('materializationEnabled',false,'nativePublicationEnabled',false); end if;
 ready:=public.native_heartsaver_full_course_ready(p_course_number);
 return jsonb_build_object('materializationEnabled',ready,'nativePublicationEnabled',ready and scope.publication_enabled,
  'nativeScopeId',scope.scope_id,'coursePolicyKey',scope.policy_key,'canonicalCourseId',scope.course_id,
  'pageKey','heartsaver','instructionMinutes',scope.instruction_minutes,'cleanupMinutes',scope.cleanup_minutes,'maxStudents',scope.max_students);
end $$;
revoke all on function public.native_heartsaver_full_course_ready(text,timestamptz),public.native_full_course_runtime_policy(text) from public,anon,authenticated;
grant execute on function public.native_heartsaver_full_course_ready(text,timestamptz),public.native_full_course_runtime_policy(text) to service_role;
-- Extend only reviewed anchors; preserve every installed lock and lifecycle guard.
do $patch$
declare definition text; installed text; old_text text; new_text text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc where oid=to_regprocedure('public.native_full_course_option(text,jsonb)');
 if md5(installed) is distinct from '1693a947b79060795fa46b963a879b8c' then raise exception 'native_full_course_option_heartsaver_source_drift'; end if;
 definition:=replace(pg_get_functiondef('public.native_full_course_option(text,jsonb)'::regprocedure),E'\r\n',E'\n');
 old_text:=$old$native_v2 boolean; native_policy public.native_full_course_public_policy;$old$;
 new_text:=$new$native_v2 boolean; native_policy public.native_full_course_public_policy;
 heartsaver boolean; course_policy public.native_heartsaver_full_course_policy; instruction_minutes integer:=120; cleanup_minutes integer:=30;$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_full_course_option_heartsaver_anchor_0_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$ if not exists(select 1 from public.native_full_course_policy where policy_key='bls-full' and enabled and verified and nullif(trim(evidence),'') is not null) then return null; end if;$old$;
 new_text:=$new$ heartsaver:=coalesce(p_course_number in ('209809','344085'),false);
 if heartsaver then
  select * into course_policy from public.native_heartsaver_full_course_policy where public_course_id=p_course_number;
  if not public.native_heartsaver_full_course_ready(p_course_number) or not course_policy.publication_enabled
   or p_offer->>'authority' is distinct from 'native-full-course.v2'
   or p_offer->>'coursePolicyKey' is distinct from course_policy.policy_key then return null; end if;
  instruction_minutes:=course_policy.instruction_minutes; cleanup_minutes:=course_policy.cleanup_minutes;
 elsif not exists(select 1 from public.native_full_course_policy where policy_key='bls-full' and enabled and verified and nullif(trim(evidence),'') is not null) then return null; end if;$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_full_course_option_heartsaver_anchor_1_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$ if native_v2 then
  select * into native_policy$old$;
 new_text:=$new$ if native_v2 and not heartsaver then
  select * into native_policy$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_full_course_option_heartsaver_anchor_2_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$ if c.max_students_default is null or c.max_students_default<=0 then return null; end if;$old$;
 new_text:=$new$ if heartsaver then
  if c.id is distinct from course_policy.course_id or c.course_key is distinct from course_policy.course_key then return null; end if;
 elsif c.max_students_default is null or c.max_students_default<=0 then return null; end if;$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_full_course_option_heartsaver_anchor_3_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$or c.enrollware_course_id not in ('209806','359474')$old$;
 new_text:=$new$or (not heartsaver and c.enrollware_course_id not in ('209806','359474'))$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_full_course_option_heartsaver_anchor_4_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$or starts<=now() or ends<>starts+interval '120 minutes' or occupied_end<>ends+interval '30 minutes'$old$;
 new_text:=$new$or starts<=now() or ends<>starts+make_interval(mins=>instruction_minutes) or occupied_end<>ends+make_interval(mins=>cleanup_minutes)$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_full_course_option_heartsaver_anchor_5_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$ if not exists(select 1 from public.instructor_qualifications q where q.instructor_id=instructor.id and q.course_id=c.id$old$;
 new_text:=$new$ if heartsaver and not public.native_heartsaver_full_course_ready(p_course_number,occupied_end) then return null; end if;
 if not heartsaver and not exists(select 1 from public.instructor_qualifications q where q.instructor_id=instructor.id and q.course_id=c.id$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_full_course_option_heartsaver_anchor_6_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$  if capacity is null or (public.landerware_public_seat_state(target.id)->>'remaining')::integer<1 then return null; end if;$old$;
 new_text:=$new$  if capacity is null or (public.landerware_public_seat_state(target.id)->>'remaining')::integer<1 then return null; end if;
  if heartsaver and (capacity>course_policy.max_students or exists(select 1 from public.landerware_public_orders pending where pending.class_session_id=target.id and public.native_checkout_unresolved_payment(pending))) then return null; end if;$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_full_course_option_heartsaver_anchor_7_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$capacity:=case when native_v2 then least(native_policy.max_students,c.max_students_default)$old$;
 new_text:=$new$capacity:=case when heartsaver then course_policy.max_students when native_v2 then least(native_policy.max_students,c.max_students_default)$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_full_course_option_heartsaver_anchor_8_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 execute definition;
end $patch$;

-- Extend only reviewed anchors; preserve every installed lock and lifecycle guard.
do $patch$
declare definition text; installed text; old_text text; new_text text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc where oid=to_regprocedure('public.materialize_native_full_checkout(text,jsonb,text)');
 if md5(installed) is distinct from 'bc2a1da16cf3ff1d2ea1c08d8cb46044' then raise exception 'materialize_native_full_checkout_heartsaver_source_drift'; end if;
 definition:=replace(pg_get_functiondef('public.materialize_native_full_checkout(text,jsonb,text)'::regprocedure),E'\r\n',E'\n');
 old_text:=$old$ lock table public.courses,public.people,public.locations,public.instructor_qualifications in share mode;$old$;
 new_text:=$new$ lock table public.courses,public.people,public.locations,public.instructor_qualifications in share mode;
 if p_course_number in ('209809','344085') then
  perform 1 from public.native_heartsaver_full_course_policy where public_course_id=p_course_number for share;
  perform 1 from public.landerware_registration_catalog where course_id=p_course_number for share;
  perform 1 from public.landerware_registration_profiles where profile_key=(select profile_key from public.native_heartsaver_full_course_policy where public_course_id=p_course_number) for share;
 end if;$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'materialize_native_full_checkout_heartsaver_anchor_0_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$'/bls.html?course='||p_course_number,(select unit_amount/100.0 from public.landerware_registration_catalog where course_id=p_course_number and active),120,$old$;
 new_text:=$new$(case when p_course_number in ('209809','344085') then '/heartsaver.html?course=' else '/bls.html?course=' end)||p_course_number,
    (select unit_amount/100.0 from public.landerware_registration_catalog where course_id=p_course_number and active),
    extract(epoch from (option->>'endsAt')::timestamptz-(option->>'startsAt')::timestamptz)::integer/60,$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'materialize_native_full_checkout_heartsaver_anchor_1_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 execute definition;
end $patch$;

-- Extend only reviewed anchors; preserve every installed lock and lifecycle guard.
do $patch$
declare definition text; installed text; old_text text; new_text text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc where oid=to_regprocedure('public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)');
 if md5(installed) is distinct from '45b3c53c9629268328bfaeefdd4a597a' then raise exception 'reserve_native_checkout_order_heartsaver_source_drift'; end if;
 definition:=replace(pg_get_functiondef('public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)'::regprocedure),E'\r\n',E'\n');
 old_text:=$old$ if c.id is null then raise exception 'native_profile_not_configured'; end if;$old$;
 new_text:=$new$ if c.id is null then raise exception 'native_profile_not_configured'; end if;
 if c.enrollware_course_id in ('209809','344085') then
  perform 1 from public.native_heartsaver_full_course_policy where public_course_id=c.enrollware_course_id for share;
  if not public.native_heartsaver_full_course_ready(c.enrollware_course_id) then raise exception 'native_registration_unavailable'; end if;
 end if;$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'reserve_native_checkout_order_heartsaver_anchor_0_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$and c.enrollware_course_id in ('209806','359474') and coalesce(p_context,'')=''$old$;
 new_text:=$new$and c.enrollware_course_id in ('209806','359474','209809','344085') and coalesce(p_context,'')=''$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'reserve_native_checkout_order_heartsaver_anchor_1_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 old_text:=$old$  external_id:=p_external_id;$old$;
 new_text:=$new$  if c.enrollware_course_id in ('209809','344085') then
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
  external_id:=p_external_id;$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'reserve_native_checkout_order_heartsaver_anchor_2_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 execute definition;
end $patch$;

-- Extend only reviewed anchors; preserve every installed lock and lifecycle guard.
do $patch$
declare definition text; installed text; old_text text; new_text text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc where oid=to_regprocedure('public.native_checkout_profile(text,text)');
 if md5(installed) is distinct from 'c6e5c6b95187e0f2b203aa6fc61ade82' then raise exception 'native_checkout_profile_heartsaver_source_drift'; end if;
 definition:=replace(pg_get_functiondef('public.native_checkout_profile(text,text)'::regprocedure),E'\r\n',E'\n');
 old_text:=$old$ if p.profile_key is null or p.course_id is distinct from c.course_key then raise exception 'native_profile_not_configured'; end if;$old$;
 new_text:=$new$ if p.profile_key is null or p.course_id is distinct from c.course_key then raise exception 'native_profile_not_configured'; end if;
 if p_public_course_id in ('209809','344085') or c.enrollware_course_id in ('209809','344085') then
  if p_public_course_id is distinct from c.enrollware_course_id or not public.native_heartsaver_full_course_ready(c.enrollware_course_id)
  then raise exception 'native_registration_unavailable'; end if;
 end if;$new$;
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'native_checkout_profile_heartsaver_anchor_0_missing'; end if;
 definition:=replace(definition,old_text,new_text);
 execute definition;
end $patch$;
-- Invoker functions retain the installed service-only execution boundary.
revoke all on function public.native_full_course_option(text,jsonb),public.materialize_native_full_checkout(text,jsonb,text),
 public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer),public.native_checkout_profile(text,text) from public,anon,authenticated;
grant execute on function public.native_full_course_option(text,jsonb),public.materialize_native_full_checkout(text,jsonb,text),
 public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer),public.native_checkout_profile(text,text) to service_role;
commit;
