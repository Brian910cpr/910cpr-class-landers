-- Dedicated scheduling read: one statement snapshot, never a mutation helper.
-- Existing checkout/finalization readers remain VOLATILE and unchanged.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';

create function public.native_scheduling_seat_snapshot(p_session_id uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $function$
declare
 s public.class_sessions; e public.landerware_session_authority_events;
 g public.native_checkout_generated_sessions;
 identity jsonb; authority text; revision integer; witness text;
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
 return jsonb_build_object('registrationAuthority',authority,'authorityRevision',revision,'generatedIdentity',witness,
   'sessionIdentity',identity,'sessionStatus',s.status,'registrationStatus',s.registration_status,'visibility',s.visibility,
   'capacity',v_capacity,'registered',v_registered,'holds',v_holds,'unreconciledReserved',v_reserved,
   'remaining',v_capacity-v_registered-v_holds-v_reserved);
end $function$;

revoke all on function public.native_scheduling_seat_snapshot(uuid) from public,anon,authenticated;
grant execute on function public.native_scheduling_seat_snapshot(uuid) to service_role;
comment on function public.native_scheduling_seat_snapshot(uuid) is
 'Read-only scheduling projection at one statement snapshot. Do not reuse in mutation paths that need own-command visibility.';
commit;
