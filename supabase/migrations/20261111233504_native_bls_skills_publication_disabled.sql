-- Independent, default-off BLS skills/package publication. No activation or stock writes.
-- Prerequisite: 20261111233000 native shared-skills wall-clock lease guard.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
create table public.native_bls_skills_publication_policy (
 scope_id text primary key check(scope_id='brian-shipyard-b.v1'),
 enabled boolean not null default false,
 publication_enabled boolean not null default false,
 verified boolean not null default false,
 evidence text,
 source_qualification_id uuid,
 bundle_enabled boolean not null default false,
 bundle_verified boolean not null default false,
 bundle_evidence text,
 updated_at timestamptz not null default now(),
 check(not enabled or (verified and nullif(trim(evidence),'') is not null and source_qualification_id is not null)),
 check(not bundle_enabled or (enabled and bundle_verified and nullif(trim(bundle_evidence),'') is not null))
);
insert into public.native_bls_skills_publication_policy(scope_id) values('brian-shipyard-b.v1');
alter table public.native_bls_skills_publication_policy enable row level security;
revoke all on public.native_bls_skills_publication_policy from public,anon,authenticated;
grant select,insert,update,delete on public.native_bls_skills_publication_policy to service_role;
create policy native_bls_skills_service_access on public.native_bls_skills_publication_policy
 for all to service_role using(true) with check(true);

-- The exact source qualification is linked, never copied or invented. BLS is
-- not covered by the prior four-context skills policy's qualification evidence.
create function public.native_bls_skills_ready(p_through timestamptz default now())
returns boolean language sql stable security invoker set search_path='' as $function$
 select p_through is not null and isfinite(p_through) and exists(
  select 1 from public.native_bls_skills_publication_policy scope
  join public.skills_session_context_config cfg on cfg.context_key='bls-skills'
  join public.courses c on c.id=cfg.course_id and c.enrollware_course_id='509474' and c.course_key='skills-session-only'
  join public.landerware_registration_profiles profile on profile.profile_key=c.registration_profile_key
  join public.landerware_registration_catalog catalog on catalog.course_id='509474'
  join public.instructor_qualifications source on source.id=scope.source_qualification_id
  join public.courses bls on bls.id=source.course_id and bls.enrollware_course_id='209806' and bls.course_key='aha-bls-provider'
  join public.people instructor on instructor.id=source.instructor_id and instructor.person_key='brian' and instructor.display_name='Brian Ennis' and instructor.active
  where scope.scope_id='brian-shipyard-b.v1' and scope.enabled and scope.publication_enabled and scope.verified
   and nullif(trim(scope.evidence),'') is not null
   and cfg.enabled and cfg.capacity_policy_verified and cfg.qualification_course_id=c.id
   and cfg.policy_evidence='native-bls-skills-policy.v1'
   and source.qualification_key='aha-bls-instructor:209806' and source.status='active'
   and source.expires_at is not null and isfinite(source.expires_at) and source.expires_at>=p_through
   and exists(select 1 from public.instructor_qualifications q where q.instructor_id=instructor.id and q.course_id=c.id
    and q.qualification_key='skills-session-policy.v1' and q.status='active' and (q.expires_at is null or q.expires_at>=p_through))
   and not exists(select 1 from public.instructor_qualifications q where q.instructor_id=instructor.id and q.course_id in(c.id,bls.id)
    and (q.status is distinct from 'active' or (q.expires_at is not null and (not isfinite(q.expires_at) or q.expires_at<p_through))
     or (q.course_id=bls.id and (q.qualification_key is distinct from 'aha-bls-instructor:209806' or q.expires_at is null))))
   and (select count(*) from public.courses other where other.enrollware_course_id='509474')=1
   and (select count(*) from public.courses other where other.enrollware_course_id='209806')=1
   and (select count(*) from public.people other where other.person_key='brian')=1
   and c.duration_minutes=45 and c.setup_buffer_minutes=0 and c.cleanup_buffer_minutes=15 and c.max_students_default=2 and c.base_price=55
   and profile.profile_key='native_skills_shared' and profile.course_id=c.course_key
   and profile.active and profile.registration_mode='native_public_checkout' and profile.version>0
   and profile.form_schema->>'schemaVersion'='native-checkout.form.v1' and profile.form_schema->>'inventory_kind'='leased_skills_v1'
   and profile.form_schema->>'max_students'='2' and profile.form_schema->'allowed_contexts' ? 'bls-skills'
   and profile.form_schema->'default_choices'='["skills_only"]'::jsonb
   and exists(select 1 from jsonb_array_elements(profile.form_schema->'option_groups') g,
    jsonb_array_elements(g->'choices') choice where g->>'key'='learning_path' and g->>'type'='radio'
     and g->'required'='true'::jsonb and choice->>'key'='skills_only'
     and choice->'catalog_keys'='[]'::jsonb and choice->'bindings'='{"learningPath":"skills-only"}'::jsonb)
   and catalog.active and catalog.currency='usd' and catalog.unit_amount=5500
   and exists(select 1 from public.locations l where l.location_key='910cpr-office-shipyard' and l.scheduling_status='active')
 );
$function$;

-- Optional delivery schema is intentionally not installed by this migration.
-- Missing delivery configuration is unavailable, not manual-fulfillment fallback.
create function public.native_bls_bundle_ready(p_through timestamptz default now())
returns boolean language plpgsql stable security invoker set search_path='' as $function$
declare ready boolean; runtime jsonb;
begin
 if not public.native_bls_skills_ready(p_through) then return false; end if;
 if not exists(select 1 from public.native_bls_skills_publication_policy where bundle_enabled and bundle_verified
  and nullif(trim(bundle_evidence),'') is not null) then return false; end if;
 if to_regclass('public.native_code_delivery_policy') is null
  or to_regclass('public.native_learner_code_runtime') is null
  or to_regprocedure('public.native_learner_code_runtime_readiness()') is null then return false; end if;
 -- An enabled legacy delivery token is not proof of an operating code sender.
 -- This optional, sanitized contract belongs to the independent Resend code lane.
 execute 'select public.native_learner_code_runtime_readiness()' into runtime;
 if runtime->'ready' is distinct from 'true'::jsonb or runtime->>'provider' is distinct from 'resend' then return false; end if;
 execute $sql$select exists(select 1 from public.native_code_delivery_policy cfg
  join public.landerware_checkout_delivery_config delivery on delivery.id and delivery.enabled
   and '509474'=any(delivery.course_ids) and delivery.not_before<=statement_timestamp()
  where cfg.product_key='aha-25-3553-heartcode-bls-online' and cfg.enabled and '509474'=any(cfg.course_ids))$sql$ into ready;
 if not ready or not public.bls_native_bundle_ready() then return false; end if;
 if not exists(select 1 from public.product_inventory_units u join public.products p on p.id=u.product_id
  where p.product_key='aha-25-3553-heartcode-bls-online' and u.status='available' and not u.public_order_payment_observed
   and u.public_order_student_id is null and u.reserved_for_registration_id is null and u.exposed_at is null and u.fulfilled_at is null
   and nullif(trim(u.secret_value),'') is not null) then return false; end if;
 return exists(select 1 from public.courses c join public.landerware_registration_profiles p on p.profile_key=c.registration_profile_key
  where c.enrollware_course_id='509474' and p.profile_key='native_skills_shared'
  and exists(select 1 from jsonb_array_elements(p.form_schema->'public_aliases') a
   where a->>'public_course_id'='210549' and a->>'context'='bls-skills' and a->'default_choices'='["online_and_skills"]'::jsonb)
  and exists(select 1 from jsonb_array_elements(p.form_schema->'option_groups') g,jsonb_array_elements(g->'choices') choice
   where g->>'key'='learning_path' and choice->>'key'='online_and_skills' and choice->'contexts'='["bls-skills"]'::jsonb
    and choice->'catalog_keys'='["aha_heartcode_bls_online"]'::jsonb and choice->'bindings'='{"learningPath":"online-and-skills"}'::jsonb)
  and not exists(select 1 from public.courses other join public.landerware_registration_profiles op on op.profile_key=other.registration_profile_key
   where other.id<>c.id and op.active and exists(select 1 from jsonb_array_elements(coalesce(op.form_schema->'public_aliases','[]')) a
    where a->>'public_course_id'='210549' and (a->>'context' is null or a->>'context'='bls-skills'))));
exception when others then return false;
end $function$;

-- Bounded service-only proof. No codes, inventory counts or private IDs leave SQL.
create function public.native_bls_skills_publication_policy()
returns jsonb language sql stable security invoker set search_path='' as $function$
 with readiness as(select public.native_bls_skills_ready() skills,public.native_bls_bundle_ready() bundle)
 select jsonb_build_object('schemaVersion','native-bls-skills-publication-policy.v1',
  'observedAt',statement_timestamp(),'validUntil',statement_timestamp()+interval '15 minutes',
  'nativeScopeId','brian-shipyard-b.v1','physicalCourseId','509474','context','bls-skills','profileKey','native_skills_shared',
  'profileVersion',case when skills then (select version from public.landerware_registration_profiles where profile_key='native_skills_shared') end,
  'skillsEnabled',skills,'bundleEnabled',bundle,
  'qualificationValidThrough',case when skills then (select min(q.expires_at) from public.native_bls_skills_publication_policy scope
   join public.instructor_qualifications source on source.id=scope.source_qualification_id
   join public.instructor_qualifications q on q.instructor_id=source.instructor_id
   where q.course_id=source.course_id or q.course_id=(select id from public.courses where enrollware_course_id='509474')) end,
  'instructionMinutes',45,'cleanupMinutes',15,'capacity',2,'skillsCents',5500,'bundleCents',9500) from readiness;
$function$;

-- Dependency locks prevent policy/profile/credential changes after admission.
-- NOWAIT avoids inverse lock order with administrative writes; a fresh separate
-- statement after the lock is required. Inventory is reserved by existing code.
create function public.native_bls_skills_lock_dependencies(p_bundle boolean)
returns void language plpgsql volatile security invoker set search_path='' as $function$
begin
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'native_bls_skills_isolation_required'; end if;
 lock table public.native_bls_skills_publication_policy,public.skills_session_context_config,
  public.courses,public.people,public.locations,public.instructor_qualifications,
  public.landerware_registration_profiles,public.landerware_registration_catalog in share mode nowait;
 if p_bundle then
  lock table public.landerware_bls_bundle_policy,public.products,public.landerware_checkout_delivery_config in share mode nowait;
  if to_regclass('public.native_code_delivery_policy') is null then raise exception 'bundle_fulfillment_unavailable'; end if;
  if to_regclass('public.native_learner_code_runtime') is null
   or to_regprocedure('public.native_learner_code_runtime_readiness()') is null then raise exception 'bundle_fulfillment_unavailable'; end if;
  execute 'lock table public.native_code_delivery_policy,public.native_learner_code_runtime in share mode nowait';
 end if;
exception when lock_not_available then raise exception 'session_not_available';
end $function$;
revoke all on function public.native_bls_skills_ready(timestamptz),public.native_bls_bundle_ready(timestamptz),
 public.native_bls_skills_publication_policy(),public.native_bls_skills_lock_dependencies(boolean) from public,anon,authenticated;
grant execute on function public.native_bls_skills_ready(timestamptz),public.native_bls_bundle_ready(timestamptz),
 public.native_bls_skills_publication_policy(),public.native_bls_skills_lock_dependencies(boolean) to service_role;

do $patch$
declare signature text; installed text; definition text; anchor text; replacement text;
begin
 signature:='public.native_skills_publication_offer_valid(text,jsonb)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if installed is null or md5(installed) not in ('54fb2b3c224217498cd7f5cef4eb9aac') then raise exception 'native_bls_skills_source_drift: %',signature; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$anchor$array['nativeOfferId','nativeScopeId','proofObservedAt','identityWitness','profileVersion']$anchor$;
 replacement:=$replacement$array['nativeOfferId','nativeScopeId','proofObservedAt','identityWitness','profileVersion','checkoutPackage','publicCourseId','physicalCourseId']$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$anchor$or p_context not in ('cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended')$anchor$;
 replacement:=$replacement$or p_context not in ('cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended','bls-skills')$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$anchor$or p_offer->>'selectionId' is distinct from 'skills:'||(p_offer->>'nativeOfferId')||':'||p_context$anchor$;
 replacement:=$replacement$or p_offer->>'selectionId' is distinct from 'skills:'||(p_offer->>'nativeOfferId')||':'||p_context||(case when p_context='bls-skills' then ':'||(p_offer->>'checkoutPackage') else '' end)$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$anchor$ if not (public.native_skills_publication_runtime_policy()->>'nativePublicationEnabled')::boolean then return false; end if;$anchor$;
 replacement:=$replacement$ if p_context='bls-skills' then
  if p_offer->>'physicalCourseId' is distinct from '509474' or p_offer->>'profileKey' is distinct from 'native_skills_shared'
   or not exists(select 1 from public.landerware_registration_profiles p where p.profile_key='native_skills_shared'
    and p.version::text=p_offer->>'profileVersion' and jsonb_typeof(p_offer->'profileVersion')='number')
   or ((p_offer->>'publicCourseId'='509474' and p_offer->>'checkoutPackage'='bls-skills-only.v1')
    or (p_offer->>'publicCourseId'='210549' and p_offer->>'checkoutPackage'='heartcode-bls-online-and-skills.v1')) is distinct from true
   then return false; end if;
 elsif not (public.native_skills_publication_runtime_policy()->>'nativePublicationEnabled')::boolean then return false;
 elsif p_offer ?| array['checkoutPackage','publicCourseId','physicalCourseId'] then return false; end if;$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$anchor$ -- Reuse exactly the pre-existing canonical policy,$anchor$;
 replacement:=$replacement$ if p_context='bls-skills' then
  if exists(select 1 from unnest(array['calendarProofObservedAt','policyProofObservedAt']) field
   where coalesce(p_offer->>field,'') !~ 'T.*(Z|[+-][0-9]{2}:[0-9]{2})$') then return false; end if;
  if observed is distinct from least((p_offer->>'calendarProofObservedAt')::timestamptz,(p_offer->>'policyProofObservedAt')::timestamptz)
   or greatest((p_offer->>'calendarProofObservedAt')::timestamptz,(p_offer->>'policyProofObservedAt')::timestamptz)>generated
   then return false; end if;
 end if;
 if p_context='bls-skills' and (not public.native_bls_skills_ready(occupied_end)
  or (p_offer->>'publicCourseId'='210549' and not public.native_bls_bundle_ready(occupied_end))) then return false; end if;
 -- Reuse exactly the pre-existing canonical policy,$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$anchor$and cfg.policy_evidence='skills-session-policy.v1' and cfg.qualification_course_id=cfg.course_id$anchor$;
 replacement:=$replacement$and cfg.policy_evidence=case when p_context='bls-skills' then 'native-bls-skills-policy.v1' else 'skills-session-policy.v1' end and cfg.qualification_course_id=cfg.course_id$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
 signature:='public.native_scheduling_seat_snapshot(uuid)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if installed is null or md5(installed) not in ('66ca3621073416061df0eb36aa3b7801','76eac7291bc3e4195a2b2002025dca55') then raise exception 'native_bls_skills_source_drift: %',signature; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$anchor$and cfg.context_key in ('cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended')$anchor$;
 replacement:=$replacement$and (cfg.context_key in ('cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended') or (cfg.context_key='bls-skills' and public.native_bls_skills_ready(s.consumption_end_at)))$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$anchor$and cfg.enabled and cfg.capacity_policy_verified and cfg.policy_evidence='skills-session-policy.v1'$anchor$;
 replacement:=$replacement$and cfg.enabled and cfg.capacity_policy_verified and cfg.policy_evidence=case when cfg.context_key='bls-skills' then 'native-bls-skills-policy.v1' else 'skills-session-policy.v1' end$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
 signature:='public.materialize_native_skills_checkout(text,jsonb,text)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if installed is null or md5(installed) not in ('5f97fc0cc58f13c970a0c8d857b9bad7') then raise exception 'native_bls_skills_source_drift: %',signature; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$anchor$begin
 option:=public.skills_session_native_option(p_context,p_offer);$anchor$;
 replacement:=$replacement$begin
 if p_context='bls-skills' then
  perform public.native_bls_skills_lock_dependencies(p_offer->>'checkoutPackage'='heartcode-bls-online-and-skills.v1');
 end if;
 option:=public.skills_session_native_option(p_context,p_offer);$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
 signature:='public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)';
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 if installed is null or md5(installed) not in ('45b3c53c9629268328bfaeefdd4a597a','e6d0b6d009f46a37e2147fde2e3c789d') then raise exception 'native_bls_skills_source_drift: %',signature; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:=$anchor$ select * into strict o from public.landerware_public_orders where id=(result->>'orderId')::uuid;$anchor$;
 replacement:=$replacement$ select * into strict o from public.landerware_public_orders where id=(result->>'orderId')::uuid;
 if p_context='bls-skills' and p_offer->>'checkoutPackage'='heartcode-bls-online-and-skills.v1' then
  -- The existing inventory writer chooses and locks canonical units. Validate
  -- that EACH reserved unit is usable before any new order can reach payment.
  -- Never return a code value or alter an already-saved order during replay.
  if exists(select 1 from public.landerware_public_order_students st where st.order_id=o.id
   and (select count(*) from public.product_inventory_units u join public.products product on product.id=u.product_id
    where u.public_order_student_id=st.id and product.product_key='aha-25-3553-heartcode-bls-online'
     and u.status='reserved' and u.reserved_for_registration_id is null and not u.public_order_payment_observed
     and u.exposed_at is null and u.fulfilled_at is null and nullif(trim(u.secret_value),'') is not null)<>1)
   then raise exception 'bundle_fulfillment_unavailable'; end if;
 end if;$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=$anchor$  option:=public.materialize_native_skills_checkout(p_context,p_offer,p_key);$anchor$;
 replacement:=$replacement$  if p_context='bls-skills' then
   -- Require explicit package identity for NEW orders only. The durable receipt
   -- branch above preserves saved legacy orders and their original snapshots.
   if p_offer->>'authority' not in ('native-skills-publication.v1','native-skills-seated.v1')
    or p_offer->>'profileKey' is distinct from p_profile_key or p_offer->>'profileVersion' is distinct from p_version::text
    or coalesce(p_offer->>'checkoutPackage','') not in ('bls-skills-only.v1','heartcode-bls-online-and-skills.v1')
    then raise exception 'session_not_available'; end if;
   if exists(select 1 from jsonb_array_elements(p_students) st where
    st->>'skillsContext' is distinct from 'bls-skills' or st->>'selectorSelectionId' is distinct from p_offer->>'selectionId'
    or st->>'learningPath' is distinct from case when p_offer->>'checkoutPackage'='bls-skills-only.v1' then 'skills-only' else 'online-and-skills' end
    or coalesce(st->'addons','[]') is distinct from case when p_offer->>'checkoutPackage'='bls-skills-only.v1' then '[]'::jsonb else '[{"key":"aha_heartcode_bls_online","quantity":1}]'::jsonb end)
    then raise exception 'invalid_course_option'; end if;
   if exists(select 1 from jsonb_array_elements(p_inputs) input where input->'selectedChoices' is distinct from
    case when p_offer->>'checkoutPackage'='bls-skills-only.v1' then '["skills_only"]'::jsonb else '["online_and_skills"]'::jsonb end)
    or p_expected_total<>wanted*(case when p_offer->>'checkoutPackage'='bls-skills-only.v1' then 5500 else 9500 end)
    then raise exception 'invalid_course_option'; end if;
  end if;
  option:=public.materialize_native_skills_checkout(p_context,p_offer,p_key);$replacement$;
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_bls_skills_anchor_missing: %',signature; end if;
 definition:=replace(definition,anchor,replacement);
 execute definition;
end $patch$;
commit;
