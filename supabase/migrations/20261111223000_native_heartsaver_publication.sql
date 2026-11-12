-- Read-only publication evidence. No activation, binding, pricing or capacity changes.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
create function public.native_heartsaver_publication_policy()
returns jsonb language sql stable security invoker set search_path='' as $$
 select jsonb_build_object('schemaVersion','native-heartsaver-publication-policy.v1',
  'observedAt',statement_timestamp(),'validUntil',statement_timestamp()+interval '15 minutes',
  'courses',(select jsonb_object_agg(scope.public_course_id,
    public.native_full_course_runtime_policy(scope.public_course_id)||jsonb_build_object('qualificationValidThrough',
     case when public.native_heartsaver_full_course_ready(scope.public_course_id) and scope.publication_enabled
      then (select min(q.expires_at) from public.instructor_qualifications q
       where q.instructor_id=source.instructor_id and q.course_id in (source.course_id,scope.course_id)
        and q.status='active') else null end))
   from public.native_heartsaver_full_course_policy scope
   left join public.instructor_qualifications source on source.id=scope.source_qualification_id
   where scope.public_course_id in ('209809','344085')));
$$;
revoke all on function public.native_heartsaver_publication_policy() from public,anon,authenticated;
grant execute on function public.native_heartsaver_publication_policy() to service_role;

-- Reject drift rather than replacing an independently changed occupancy reader.
do $guard$ begin
 if (select md5(replace(prosrc,E'\r\n',E'\n')) from pg_catalog.pg_proc
  where oid=pg_catalog.to_regprocedure('public.native_scheduling_seat_snapshot(uuid)'))
  is distinct from 'ab0dac5a20dafaf136f9e45635d1783e' then raise exception 'heartsaver_snapshot_source_drift'; end if;
end $guard$;

create or replace function public.native_scheduling_seat_snapshot(p_session_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $function$
declare
 s public.class_sessions; e public.landerware_session_authority_events;
 g public.native_checkout_generated_sessions;
 identity jsonb; authority text; revision integer; witness text;
 booking jsonb; skills_booking jsonb; heartsaver_booking jsonb;
 v_capacity integer; v_registered integer; v_holds integer; v_reserved integer:=0;
begin
 -- STABLE applies to every SELECT below. Do not call VOLATILE seat/authority
 -- helpers here: nested VOLATILE functions acquire their own fresh snapshots.
 select * into s from public.class_sessions where id=p_session_id;
 if s.id is null then raise exception 'session_not_open'; end if;
 identity:=jsonb_build_array(s.course_id,s.start_at,s.end_at,s.consumption_start_at,s.consumption_end_at,
   s.lead_instructor_id,s.location_id,s.resource_id,s.organization_id,s.external_class_id,s.record_scope);
 if s.registration_backend is distinct from 'landerware' then raise exception 'native_authority_identity_changed'; end if;
 select * into e from public.landerware_session_authority_events where class_session_id=s.id order by revision desc limit 1;
 if e.id is not null then
  if not e.enabled then raise exception 'native_authority_disabled'; end if;
  if identity is distinct from e.session_identity then raise exception 'native_authority_identity_changed'; end if;
  authority:='landerware-session-authority.v1'; revision:=e.revision;
 else
  -- A nonnumeric ID alone proves nothing. Fresh native materializations must
  -- have the service-only lifecycle witness and unchanged canonical identity.
  select * into g from public.native_checkout_generated_sessions where class_session_id=s.id;
  if g.class_session_id is null or g.state is distinct from 'holding'
    or g.identity_hash is distinct from public.native_checkout_generated_identity(s)
    or s.source is distinct from 'landerware_event' or s.record_scope is distinct from 'operational'
    or coalesce(s.external_class_id,'') !~ '^lw-[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
    or coalesce(s.external_session_evidence->>'materializedBy','') not in ('skills_session_native','native_full_course')
  then raise exception 'native_generated_authority_unavailable'; end if;
  authority:='landerware-generated-session.v1'; witness:=g.identity_hash;
  -- Unexpected external occupancy on a freshly generated class is unknown,
  -- never a reason to invent an empty native baseline.
  if exists(select 1 from public.registrations r where r.class_session_id=s.id
     and r.status in ('registered','confirmed','completed','active')
     and (r.external_registration_id is not null or r.registration_source in
       ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation')))
   or coalesce(s.external_reconciliation,'{}'::jsonb) <> '{}'::jsonb
   or exists(select 1 from public.landerware_public_session_inventory i where i.external_class_id=s.external_class_id and coalesce(i.externally_registered,0)<>0)
  then raise exception 'native_generated_occupancy_unknown'; end if;
 end if;
 select least(s.max_students,coalesce((select i.capacity from public.landerware_public_session_inventory i
   where i.external_class_id=s.external_class_id),s.max_students)) into v_capacity;
 if v_capacity is null or v_capacity<1 then raise exception 'unverified_capacity'; end if;
 if e.id is not null then v_capacity:=least(v_capacity,e.capacity_ceiling); end if;
 select count(*) into v_registered from public.registrations where class_session_id=s.id
   and status in ('registered','confirmed','completed','active');
 -- snapshot_registration_count_captured
 if e.id is not null then
  select e.anonymous_reserved_seats+count(*) into v_reserved from unnest(e.unmatched_external_ids) v
  where not exists(select 1 from public.registrations r where r.class_session_id=s.id and r.external_registration_id=v
    and (r.status in ('registered','confirmed','completed','active')
      or (r.status in ('canceled','cancelled') and r.canceled_at>=e.recorded_at)));
 end if;
 -- Count unresolved payment liabilities across every native course even when a
 -- late failed finalizer changed the order label to expired. Successful paid
 -- orders are represented by canonical registrations and never counted twice.
 select count(*) into v_holds from public.landerware_public_order_students st
   join public.landerware_public_orders o on o.id=st.order_id
   where o.class_session_id=s.id and (public.native_checkout_unresolved_payment(o)
    or (o.status in ('held','checkout_open') and (o.hold_expires_at>now()
     or (o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true'))))
    and not exists(select 1 from public.registrations r where r.id=st.registration_id
     and r.class_session_id=s.id and r.status in ('registered','confirmed','completed','active'));
 if v_registered+v_holds+v_reserved>v_capacity then raise exception 'native_occupancy_conflict'; end if;
 -- Booking admission is separate from occupancy: disabling a profile/catalog
 -- suppresses only its CTA, never this session or its held/registered seats.
 -- Inline STABLE reads keep profile, price, identity and capacity in one snapshot.
 select jsonb_build_object('schemaVersion','native-session-booking.v1',
   'publicCourseId',c.enrollware_course_id,'profileVersion',p.version,
   'capacity',v_capacity,'remaining',v_capacity-v_registered-v_holds-v_reserved)
 into booking
 from public.courses c
 join public.landerware_registration_profiles p on p.profile_key=c.registration_profile_key
 join public.landerware_registration_catalog catalog on catalog.course_id=c.enrollware_course_id
 where c.id=s.course_id and c.enrollware_course_id in ('209806','359474')
   and p.course_id=c.course_key and p.active and p.registration_mode='native_public_checkout'
   and p.version>0 and p.form_schema->>'schemaVersion'='native-checkout.form.v1'
   and p.form_schema->>'inventory_kind'='scheduled_session_v1'
   and catalog.active and catalog.currency='usd' and catalog.unit_amount>0
   and c.base_price*100=catalog.unit_amount::numeric
   and s.visibility='public' and s.registration_status='open' and s.status in ('scheduled','active')
   and s.start_at>now() and v_capacity-v_registered-v_holds-v_reserved>0
   and not exists(select 1 from public.landerware_public_orders o
    where o.class_session_id=s.id and public.native_checkout_unresolved_payment(o))
   -- A public alias must not select another physical course at checkout.
   and not exists(select 1 from public.courses other
     join public.landerware_registration_profiles op on op.profile_key=other.registration_profile_key
     where op.active and op.registration_mode='native_public_checkout' and other.id<>c.id
       and exists(select 1 from jsonb_array_elements(case when jsonb_typeof(op.form_schema->'public_aliases')='array'
         then op.form_schema->'public_aliases' else '[]'::jsonb end) alias
         where alias->>'public_course_id'=c.enrollware_course_id and alias->>'context' is null));
 select jsonb_build_object('schemaVersion','native-skills-session-booking.v1',
  'publicCourseId','509474','profileKey',p.profile_key,'profileVersion',p.version,
  'sourceSessionId',s.external_class_id,'identityWitness',coalesce(witness,md5(identity::text)),
  'capacity',v_capacity,'remaining',v_capacity-v_registered-v_holds-v_reserved,
  'skillsContexts',contexts.keys,'qualificationPolicy','skills-session-policy.v1') into skills_booking
 from public.courses c
 join public.landerware_registration_profiles p on p.profile_key=c.registration_profile_key
 join public.landerware_registration_catalog catalog on catalog.course_id=c.enrollware_course_id
 cross join lateral (select jsonb_agg(cfg.context_key order by cfg.context_key) keys
  from public.skills_session_context_config cfg
  where cfg.course_id=c.id and cfg.qualification_course_id=c.id
   and cfg.context_key in ('cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended')
   and cfg.enabled and cfg.capacity_policy_verified and cfg.policy_evidence='skills-session-policy.v1'
   and p.form_schema->'allowed_contexts' ? cfg.context_key
   and exists(select 1 from public.instructor_qualifications q
    join public.people person on person.id=q.instructor_id
    where person.id=s.lead_instructor_id and person.person_key='brian' and person.display_name='Brian Ennis' and person.active
     and q.course_id=cfg.qualification_course_id and q.qualification_key='skills-session-policy.v1'
     and q.status='active' and (q.expires_at is null or q.expires_at>=s.consumption_end_at))
   and not exists(select 1 from public.instructor_qualifications q where q.instructor_id=s.lead_instructor_id
    and q.course_id=cfg.qualification_course_id and (q.status is distinct from 'active'
     or (q.expires_at is not null and q.expires_at<s.consumption_end_at)))) contexts
 where c.id=s.course_id and c.enrollware_course_id='509474' and p.profile_key='native_skills_shared'
  and p.course_id=c.course_key and p.active and p.registration_mode='native_public_checkout'
  and p.version>0 and p.form_schema->>'schemaVersion'='native-checkout.form.v1'
  and p.form_schema->>'inventory_kind'='leased_skills_v1' and p.form_schema->>'max_students'='2'
  and catalog.active and catalog.currency='usd' and catalog.unit_amount=5500 and c.base_price=55
  and c.max_students_default=2 and v_capacity=2 and c.duration_minutes=45
  and c.setup_buffer_minutes=0 and c.cleanup_buffer_minutes=15
  and s.end_at=s.start_at+interval '45 minutes' and s.consumption_start_at=s.start_at
  and s.consumption_end_at=s.start_at+interval '60 minutes' and s.resource_id is null
  and exists(select 1 from public.locations l where l.id=s.location_id and l.location_key='910cpr-office-shipyard' and l.scheduling_status='active')
  and s.visibility='public' and s.registration_status='open' and s.status in ('scheduled','active')
  and s.start_at>now() and v_capacity-v_registered-v_holds-v_reserved>0 and contexts.keys is not null
  -- Unresolved payment blocks only booking; occupancy and geometry remain.
  and not exists(select 1 from public.landerware_public_orders o
   where o.class_session_id=s.id and public.native_checkout_unresolved_payment(o));
 -- Full Heartsaver is a separate, exact canonical admission, never a BLS alias.
 select jsonb_build_object('schemaVersion','native-heartsaver-session-booking.v1',
  'publicCourseId',scope.public_course_id,'canonicalCourseId',scope.course_id,
  'coursePolicyKey',scope.policy_key,'profileKey',scope.profile_key,'profileVersion',p.version,
  'sourceSessionId',s.external_class_id,'identityWitness',coalesce(witness,md5(identity::text)),
  'capacity',v_capacity,'remaining',v_capacity-v_registered-v_holds-v_reserved,
  'instructionMinutes',scope.instruction_minutes,'cleanupMinutes',scope.cleanup_minutes) into heartsaver_booking
 from public.native_heartsaver_full_course_policy scope
 join public.courses c on c.id=scope.course_id and c.enrollware_course_id=scope.public_course_id and c.course_key=scope.course_key
 join public.landerware_registration_profiles p on p.profile_key=scope.profile_key and c.registration_profile_key=p.profile_key
 join public.people person on person.id=s.lead_instructor_id and person.person_key='brian' and person.display_name='Brian Ennis' and person.active
 join public.locations l on l.id=s.location_id and l.location_key='910cpr-office-shipyard' and l.scheduling_status='active'
 where s.course_id=scope.course_id and scope.public_course_id in ('209809','344085')
  and scope.enabled and scope.publication_enabled
  and public.native_heartsaver_full_course_ready(scope.public_course_id,s.consumption_end_at)
  and s.external_course_id=scope.public_course_id
  and v_capacity<=scope.max_students and s.resource_id is null
  and s.end_at=s.start_at+make_interval(mins=>scope.instruction_minutes)
  and s.consumption_start_at=s.start_at
  and s.consumption_end_at=s.end_at+make_interval(mins=>scope.cleanup_minutes)
  and s.visibility='public' and s.registration_status='open' and s.status in ('scheduled','active')
  and s.start_at>now() and v_capacity-v_registered-v_holds-v_reserved>0
  and not exists(select 1 from public.landerware_public_orders o
   where o.class_session_id=s.id and public.native_checkout_unresolved_payment(o))
  and not exists(select 1 from public.courses other
   join public.landerware_registration_profiles op on op.profile_key=other.registration_profile_key
   where op.active and op.registration_mode='native_public_checkout' and other.id<>c.id
    and exists(select 1 from jsonb_array_elements(case when jsonb_typeof(op.form_schema->'public_aliases')='array'
     then op.form_schema->'public_aliases' else '[]'::jsonb end) alias
     where alias->>'public_course_id'=scope.public_course_id and alias->>'context' is null));
 return jsonb_build_object('registrationAuthority',authority,'authorityRevision',revision,'generatedIdentity',witness,
   'sessionIdentity',identity,'sessionStatus',s.status,'registrationStatus',s.registration_status,'visibility',s.visibility,
   'capacity',v_capacity,'registered',v_registered,'holds',v_holds,'unreconciledReserved',v_reserved,
   'remaining',v_capacity-v_registered-v_holds-v_reserved,'publicBooking',booking,'skillsBooking',skills_booking,'heartsaverBooking',heartsaver_booking);
end $function$;

commit;
