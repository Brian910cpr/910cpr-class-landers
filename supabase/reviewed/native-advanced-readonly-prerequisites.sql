-- Reviewed additive READ-ONLY prerequisites; does not activate any course,
-- change an order/session/seat, replace mutation readers or add credentials.
-- Exact bodies copied from existing reviewed migrations; source equality guards
-- preserve already-installed compatible versions and refuse unexpected drift.
-- Test with synthetic schema before any hosted application. Never use fixture DDL
-- against production. Apply this before native-advanced-course-checkout.sql.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
do $prerequisites$
declare name text; fields text; field_name text;
begin
 foreach name in array ARRAY['class_sessions','landerware_session_authority_events','native_checkout_generated_sessions','registrations','landerware_public_orders','landerware_public_order_students','landerware_public_session_inventory','courses','landerware_registration_profiles','landerware_registration_catalog'] loop
  if to_regclass('public.'||name) is null then raise exception 'advanced_readonly_prerequisite_table_missing:%',name; end if;
 end loop;
 for name,fields in select key,value from jsonb_each_text('{"class_sessions":"id,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,resource_id,organization_id,external_class_id,record_scope,registration_backend,max_students,source,external_session_evidence,external_reconciliation,status,registration_status,visibility","landerware_session_authority_events":"id,class_session_id,enabled,revision,session_identity,capacity_ceiling,anonymous_reserved_seats,unmatched_external_ids,recorded_at","native_checkout_generated_sessions":"class_session_id,identity_hash,state","registrations":"class_session_id,status,external_registration_id,registration_source,canceled_at","landerware_public_orders":"id,class_session_id,status,hold_expires_at,payment_evidence,checkout_runtime_version,reconciliation_error,stripe_payment_intent_id","landerware_public_order_students":"order_id","landerware_public_session_inventory":"external_class_id,capacity,externally_registered","courses":"id,enrollware_course_id,registration_profile_key,course_key,base_price","landerware_registration_profiles":"profile_key,course_id,active,registration_mode,version,form_schema","landerware_registration_catalog":"course_id,active,currency,unit_amount"}'::jsonb) loop
  foreach field_name in array string_to_array(fields,',') loop
   if not exists(select 1 from information_schema.columns where table_schema='public' and table_name=name and column_name=field_name) then
    raise exception 'advanced_readonly_prerequisite_column_missing:%.%',name,field_name;
   end if;
  end loop;
 end loop;
end $prerequisites$;
do $install$
declare existing oid:=to_regprocedure('public.native_scheduling_seat_snapshot(uuid)');
begin
 if existing is not null then
  if not exists(select 1 from pg_proc p join pg_language l on l.oid=p.prolang where p.oid=existing
   and p.prosrc=$expected$
declare
 s public.class_sessions; e public.landerware_session_authority_events;
 g public.native_checkout_generated_sessions;
 identity jsonb; authority text; revision integer; witness text;
 booking jsonb;
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
 select count(*) into v_holds from public.landerware_public_order_students st
   join public.landerware_public_orders o on o.id=st.order_id
   where o.class_session_id=s.id and o.status in ('held','checkout_open')
     and (o.hold_expires_at>now() or (o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true'));
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
   -- A public alias must not select another physical course at checkout.
   and not exists(select 1 from public.courses other
     join public.landerware_registration_profiles op on op.profile_key=other.registration_profile_key
     where op.active and op.registration_mode='native_public_checkout' and other.id<>c.id
       and exists(select 1 from jsonb_array_elements(case when jsonb_typeof(op.form_schema->'public_aliases')='array'
         then op.form_schema->'public_aliases' else '[]'::jsonb end) alias
         where alias->>'public_course_id'=c.enrollware_course_id and alias->>'context' is null));
 return jsonb_build_object('registrationAuthority',authority,'authorityRevision',revision,'generatedIdentity',witness,
   'sessionIdentity',identity,'sessionStatus',s.status,'registrationStatus',s.registration_status,'visibility',s.visibility,
   'capacity',v_capacity,'registered',v_registered,'holds',v_holds,'unreconciledReserved',v_reserved,
   'remaining',v_capacity-v_registered-v_holds-v_reserved,'publicBooking',booking);
end $expected$ and p.provolatile='s' and not p.prosecdef
   and p.proargnames=ARRAY['p_session_id'] and pg_get_function_result(p.oid)='jsonb' and l.lanname='plpgsql'
   and p.proconfig @> ARRAY['search_path=""']) then raise exception 'advanced_readonly_prerequisite_source_drift:native_scheduling_seat_snapshot'; end if;
 else
  execute $ddl$create function public.native_scheduling_seat_snapshot(p_session_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $function$
declare
 s public.class_sessions; e public.landerware_session_authority_events;
 g public.native_checkout_generated_sessions;
 identity jsonb; authority text; revision integer; witness text;
 booking jsonb;
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
 select count(*) into v_holds from public.landerware_public_order_students st
   join public.landerware_public_orders o on o.id=st.order_id
   where o.class_session_id=s.id and o.status in ('held','checkout_open')
     and (o.hold_expires_at>now() or (o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true'));
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
   -- A public alias must not select another physical course at checkout.
   and not exists(select 1 from public.courses other
     join public.landerware_registration_profiles op on op.profile_key=other.registration_profile_key
     where op.active and op.registration_mode='native_public_checkout' and other.id<>c.id
       and exists(select 1 from jsonb_array_elements(case when jsonb_typeof(op.form_schema->'public_aliases')='array'
         then op.form_schema->'public_aliases' else '[]'::jsonb end) alias
         where alias->>'public_course_id'=c.enrollware_course_id and alias->>'context' is null));
 return jsonb_build_object('registrationAuthority',authority,'authorityRevision',revision,'generatedIdentity',witness,
   'sessionIdentity',identity,'sessionStatus',s.status,'registrationStatus',s.registration_status,'visibility',s.visibility,
   'capacity',v_capacity,'registered',v_registered,'holds',v_holds,'unreconciledReserved',v_reserved,
   'remaining',v_capacity-v_registered-v_holds-v_reserved,'publicBooking',booking);
end $function$;$ddl$;
 end if;
end $install$;
revoke all on function public.native_scheduling_seat_snapshot(uuid) from public,anon,authenticated;
grant execute on function public.native_scheduling_seat_snapshot(uuid) to service_role;

do $install$
declare existing oid:=to_regprocedure('public.native_checkout_unresolved_payment(public.landerware_public_orders)');
begin
 if existing is not null then
  if not exists(select 1 from pg_proc p join pg_language l on l.oid=p.prolang where p.oid=existing
   and p.prosrc=$expected$
 select o.status not in ('paid','refunded') and (
  o.reconciliation_error is not null
  or (o.status in ('expired','cancelled') and (o.checkout_runtime_version is distinct from 'native-v1'
   or o.payment_evidence is distinct from '{}'::jsonb or o.stripe_payment_intent_id is not null))
  or (o.status in ('held','checkout_open') and (o.hold_expires_at is null
   or (o.hold_expires_at<=now() and (o.checkout_runtime_version is distinct from 'native-v1'
    or ((o.payment_evidence is distinct from '{}'::jsonb or o.stripe_payment_intent_id is not null)
     and not coalesce(o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true',false)))))))
$expected$ and p.provolatile='s' and not p.prosecdef
   and p.proargnames=ARRAY['o'] and pg_get_function_result(p.oid)='boolean' and l.lanname='sql'
   and p.proconfig @> ARRAY['search_path=""']) then raise exception 'advanced_readonly_prerequisite_source_drift:native_checkout_unresolved_payment'; end if;
 else
  execute $ddl$create function public.native_checkout_unresolved_payment(o public.landerware_public_orders)
returns boolean language sql stable security invoker set search_path='' as $$
 select o.status not in ('paid','refunded') and (
  o.reconciliation_error is not null
  or (o.status in ('expired','cancelled') and (o.checkout_runtime_version is distinct from 'native-v1'
   or o.payment_evidence is distinct from '{}'::jsonb or o.stripe_payment_intent_id is not null))
  or (o.status in ('held','checkout_open') and (o.hold_expires_at is null
   or (o.hold_expires_at<=now() and (o.checkout_runtime_version is distinct from 'native-v1'
    or ((o.payment_evidence is distinct from '{}'::jsonb or o.stripe_payment_intent_id is not null)
     and not coalesce(o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true',false)))))))
$$;$ddl$;
 end if;
end $install$;
revoke all on function public.native_checkout_unresolved_payment(public.landerware_public_orders) from public,anon,authenticated;
grant execute on function public.native_checkout_unresolved_payment(public.landerware_public_orders) to service_role;

commit;
