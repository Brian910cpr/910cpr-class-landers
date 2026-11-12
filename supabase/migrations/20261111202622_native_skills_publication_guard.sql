-- Additive, default-off first-party skills publication. No course/profile activation.
-- Existing skills-session-policy.v1 owns qualification, contexts, 45+15 and capacity 2.
begin;
set local lock_timeout='2s';
create table public.native_skills_publication_policy (
 scope_id text primary key check(scope_id='brian-shipyard-b.v1'),
 enabled boolean not null default false,
 publication_enabled boolean not null default false,
 verified boolean not null default false,
 evidence text,
 updated_at timestamptz not null default now()
);
insert into public.native_skills_publication_policy(scope_id) values('brian-shipyard-b.v1');
alter table public.native_skills_publication_policy enable row level security;
revoke all on public.native_skills_publication_policy from public,anon,authenticated;
grant select,insert,update,delete on public.native_skills_publication_policy to service_role;
create policy native_skills_publication_service_access on public.native_skills_publication_policy
 for all to service_role using(true) with check(true);

create or replace function public.native_skills_publication_runtime_policy()
returns jsonb language sql stable security invoker set search_path='' as $$
 select jsonb_build_object('nativePublicationEnabled',exists(
  select 1 from public.native_skills_publication_policy where scope_id='brian-shipyard-b.v1'
   and enabled and publication_enabled and verified and nullif(trim(evidence),'') is not null),
  'nativeScopeId','brian-shipyard-b.v1');
$$;

-- Failed/late finalization may leave a paid receipt in expired state. The
-- payment/review evidence, not the hold status label, protects physical capacity.
create function public.native_checkout_unresolved_payment(o public.landerware_public_orders)
returns boolean language sql stable security invoker set search_path='' as $$
 select o.status not in ('paid','refunded') and (
  o.reconciliation_error is not null
  or (o.status in ('expired','cancelled') and (o.checkout_runtime_version is distinct from 'native-v1'
   or o.payment_evidence is distinct from '{}'::jsonb or o.stripe_payment_intent_id is not null))
  or (o.status in ('held','checkout_open') and (o.hold_expires_at is null
   or (o.hold_expires_at<=now() and (o.checkout_runtime_version is distinct from 'native-v1'
    or ((o.payment_evidence is distinct from '{}'::jsonb or o.stripe_payment_intent_id is not null)
     and not coalesce(o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true',false)))))))
$$;
revoke all on function public.native_checkout_unresolved_payment(public.landerware_public_orders) from public,anon,authenticated;
grant execute on function public.native_checkout_unresolved_payment(public.landerware_public_orders) to service_role;

create or replace function public.native_skills_publication_offer_valid(p_context text,p_offer jsonb)
returns boolean language plpgsql stable security invoker set search_path='' as $$
declare seated boolean; target public.class_sessions; admission jsonb; observed timestamptz; generated timestamptz; lease timestamptz; starts timestamptz; occupied_end timestamptz;
begin
 seated:=p_offer->>'authority'='native-skills-seated.v1';
 -- Leave existing legacy/HeartCode bundle contracts unchanged. Native markers
 -- cannot fall through by removing/changing just the authority discriminator.
 if coalesce(p_offer->>'authority','')='' and not(p_offer ?| array['nativeOfferId','nativeScopeId','proofObservedAt','identityWitness','profileVersion'])
  and coalesce(p_offer->>'selectionId','') not like 'skills:native-skills%' then return true; end if;
 if coalesce(p_offer->>'authority','') not in ('native-skills-publication.v1','native-skills-seated.v1')
  or p_offer->>'nativeScopeId' is distinct from 'brian-shipyard-b.v1'
  or p_offer->>'qualificationPolicy' is distinct from 'skills-session-policy.v1'
  or p_offer->>'courseNumber' is distinct from '509474'
  or p_offer->>'capacity' is distinct from '2'
  or p_context not in ('cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended')
  or p_offer->>'context' is distinct from p_context
  or p_offer->>'instructor' is distinct from 'Brian Ennis'
  or (not seated and (p_offer->>'offerType' is distinct from 'dynamic_appointment'
    or coalesce(p_offer->>'nativeOfferId','') !~ '^native-skills:[a-f0-9]{64}$'))
  or (seated and (p_offer->>'offerType' is distinct from 'seated_class'
    or coalesce(p_offer->>'sourceSessionId','') !~ '^(lw-[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}|[0-9]+)$'
    or p_offer->>'nativeOfferId' is distinct from 'native-skills-seated:'||(p_offer->>'sourceSessionId')
    or p_offer->>'availabilityBlockId' is distinct from 'seated:'||(p_offer->>'sourceSessionId')
    or p_offer->'sourceSessionIds' is distinct from jsonb_build_array(p_offer->>'sourceSessionId')
    or jsonb_typeof(p_offer->'profileVersion') is distinct from 'number'
    or jsonb_typeof(p_offer->'remainingSeats') is distinct from 'number'
    or p_offer->>'remainingSeats' not in ('1','2')))
  or p_offer->>'selectionId' is distinct from 'skills:'||(p_offer->>'nativeOfferId')||':'||p_context
  or p_offer ? 'appointmentDayId' or p_offer ? 'matchedContainerId'
  then return false; end if;
 if not (public.native_skills_publication_runtime_policy()->>'nativePublicationEnabled')::boolean then return false; end if;
 if exists(select 1 from unnest(array['proofObservedAt','generatedAt','validUntil','startsAt','consumptionEndsAt']) field
  where coalesce(p_offer->>field,'') !~ 'T.*(Z|[+-][0-9]{2}:[0-9]{2})$') then return false; end if;
 observed:=(p_offer->>'proofObservedAt')::timestamptz;
 generated:=(p_offer->>'generatedAt')::timestamptz;
 lease:=(p_offer->>'validUntil')::timestamptz;
 starts:=(p_offer->>'startsAt')::timestamptz;
 occupied_end:=(p_offer->>'consumptionEndsAt')::timestamptz;
 if observed>generated or observed>now() or observed<now()-interval '15 minutes'
  or generated>now() or generated<now()-interval '15 minutes'
  or lease<=now() or lease>observed+interval '15 minutes' or lease>generated+interval '15 minutes'
  or starts<now()+interval '24 hours' or starts>now()+interval '90 days'
  or extract(minute from starts at time zone 'America/New_York')::integer%15<>0
  or extract(second from starts)<>0
  or occupied_end<>starts+interval '60 minutes' then return false; end if;
 -- Reuse exactly the pre-existing canonical policy, not a broad instructor-family
 -- exception. Its current active qualification and any revocation still apply.
 if not exists(select 1 from public.skills_session_context_config cfg
  join public.courses c on c.id=cfg.course_id
  join public.people p on p.person_key='brian' and p.display_name='Brian Ennis' and p.active
  join public.instructor_qualifications q on q.instructor_id=p.id and q.course_id=cfg.qualification_course_id
  where cfg.context_key=p_context and cfg.enabled and cfg.capacity_policy_verified
   and cfg.policy_evidence='skills-session-policy.v1' and cfg.qualification_course_id=cfg.course_id
   and c.enrollware_course_id='509474' and q.qualification_key='skills-session-policy.v1'
   and q.status='active' and (q.expires_at is null or q.expires_at>=occupied_end)) then return false; end if;
 -- Also protect an old dynamic selection while publication is refreshing.
 -- Unresolved payment cannot be bypassed by switching context or offer version.
 if exists(select 1 from public.class_sessions session
  join public.skills_session_context_config cfg on cfg.course_id=session.course_id and cfg.context_key=p_context
  join public.landerware_public_orders o on o.class_session_id=session.id
  where session.start_at=starts and public.native_checkout_unresolved_payment(o)) then return false; end if;
 if seated then
  select * into target from public.class_sessions where external_class_id=p_offer->>'sourceSessionId';
  if target.id is null then return false; end if;
  admission:=public.native_scheduling_seat_snapshot(target.id)->'skillsBooking';
  if admission is null or admission='null'::jsonb
   or admission->>'identityWitness' is distinct from p_offer->>'identityWitness'
   or admission->>'profileVersion' is distinct from p_offer->>'profileVersion'
   or not (admission->'skillsContexts' ? p_context)
   or target.start_at is distinct from starts or target.consumption_end_at is distinct from occupied_end
   then return false; end if;
 end if;
 return true;
exception when invalid_datetime_format or datetime_field_overflow then return false;
end $$;
revoke all on function public.native_skills_publication_runtime_policy(),public.native_skills_publication_offer_valid(text,jsonb) from public,anon,authenticated;
grant execute on function public.native_skills_publication_runtime_policy(),public.native_skills_publication_offer_valid(text,jsonb) to service_role;

-- Preserve every installed capacity, closure, protected-payment and generated-
-- session lifecycle guard. Only the four known source variants are accepted.
do $patch$ declare definition text; installed text; old_text text:=E'begin\n select * into cfg from public.skills_session_context_config';
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc
  where oid=pg_catalog.to_regprocedure('public.skills_session_native_option(text,jsonb)');
 if md5(installed) is null or md5(installed) not in ('697778a82f63f8fad1c32832031c28f6','79081046a318f3bdcec138b467584a4c','88c0c376fc9e1281f7c860da06272fa7','e0bb140f88b5c77b832425dcab71c81a') then
  raise exception 'skills_session_native_option_source_drift';
 end if;
 definition:=replace(pg_get_functiondef('public.skills_session_native_option(text,jsonb)'::regprocedure),E'\r\n',E'\n');
 if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'skills_publication_guard_anchor_missing'; end if;
 execute replace(definition,old_text,E'begin\n if not public.native_skills_publication_offer_valid(p_context,p_offer) then return null; end if;\n select * into cfg from public.skills_session_context_config');
end $patch$;
-- The native order writer is shared by concrete BLS sessions and both leased
-- paths. Recheck under its class row lock, the same lock used by payment receipt
-- and finalization. An old publication cannot sell around unresolved payment.
do $payment_guard$
declare definition text; installed text;
 anchor text:='seats:=public.landerware_public_seat_state(s.id);';
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc
  where oid=pg_catalog.to_regprocedure('public.native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)');
 if md5(installed) is distinct from 'aa1fc2710f1db49c047a49374aba162d' then raise exception 'native_order_payment_guard_source_drift'; end if;
 definition:=replace(pg_get_functiondef('public.native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)'::regprocedure),E'\r\n',E'\n');
 if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_order_payment_guard_anchor_missing'; end if;
 execute replace(definition,anchor,E'if exists(select 1 from public.landerware_public_orders pending where pending.class_session_id=s.id and public.native_checkout_unresolved_payment(pending)) then raise exception ''payment_reconciliation_required''; end if;\n '||anchor);
end $payment_guard$;

-- Public self-rescheduling consumes the same physical seats as new checkout.
-- Filter obsolete choices and independently recheck after the existing target
-- row lock; that lock serializes transfer against payment receipt/finalization.
do $reschedule_payment_guard$
declare signature text; expected_hash text; installed text; definition text; anchor text; replacement text;
begin
 for signature,expected_hash,anchor,replacement in select * from (values
  ('public.registration_reschedule_targets(uuid,text[],timestamptz)',
   '3f4f208ed41ea9acd1788875e009437f',
   'where r.id=p_registration_id and s.external_class_id=any(p_published_ids)',
   E'where r.id=p_registration_id and s.external_class_id=any(p_published_ids)\n   and not exists(select 1 from public.landerware_public_orders pending\n    where pending.class_session_id=s.id and public.native_checkout_unresolved_payment(pending))'),
  ('public.confirm_registration_reschedule(text,uuid,text[])',
   'ace5b72eb45472d57946db2cdf6d18a4',
   'select * into target from public.class_sessions where id=p_target_session_id for update;',
   E'select * into target from public.class_sessions where id=p_target_session_id for update;\n if exists(select 1 from public.landerware_public_orders pending where pending.class_session_id=target.id\n  and public.native_checkout_unresolved_payment(pending)) then raise exception ''session_not_available''; end if;')
 ) changes(signature,expected_hash,anchor,replacement)
 loop
  select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc
   where oid=pg_catalog.to_regprocedure(signature);
  if md5(installed) is distinct from expected_hash then raise exception 'native_reschedule_payment_guard_source_drift: %',signature; end if;
  definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
  if (length(definition)-length(replace(definition,anchor,'')))/length(anchor)<>1 then raise exception 'native_reschedule_payment_guard_anchor_missing: %',signature; end if;
  execute replace(definition,anchor,replacement);
 end loop;
end $reschedule_payment_guard$;

-- Additive skills DTO; normal BLS booking shape remains unchanged. Both paths
-- now retain unresolved payment capacity and suppress a new booking CTA.

create or replace function public.native_scheduling_seat_snapshot(p_session_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $function$
declare
 s public.class_sessions; e public.landerware_session_authority_events;
 g public.native_checkout_generated_sessions;
 identity jsonb; authority text; revision integer; witness text;
 booking jsonb; skills_booking jsonb;
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
 return jsonb_build_object('registrationAuthority',authority,'authorityRevision',revision,'generatedIdentity',witness,
   'sessionIdentity',identity,'sessionStatus',s.status,'registrationStatus',s.registration_status,'visibility',s.visibility,
   'capacity',v_capacity,'registered',v_registered,'holds',v_holds,'unreconciledReserved',v_reserved,
   'remaining',v_capacity-v_registered-v_holds-v_reserved,'publicBooking',booking,'skillsBooking',skills_booking);
end $function$;

commit;
