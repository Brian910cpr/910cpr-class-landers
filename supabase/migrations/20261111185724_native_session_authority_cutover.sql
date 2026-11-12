-- Per-session LanderWare registration authority. No session is opted in here.
-- Retained source evidence is a historical occupancy baseline, never a fresh
-- external-service prerequisite after an explicit native authority decision.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';

-- Refuse to replace a reader that changed after this narrow review.
do $guard$ begin
 if (select md5(replace(prosrc,chr(13),'')) from pg_proc where oid='public.landerware_public_seat_state(uuid)'::regprocedure)
   is distinct from 'bab7bd1b55b0b55d1471e421e9608274' then raise exception 'native_authority_reader_review_required'; end if;
end $guard$;

create table public.landerware_session_authority_events (
 id uuid primary key default gen_random_uuid(),
 class_session_id uuid not null references public.class_sessions(id),
 revision integer not null check(revision>0),
 enabled boolean not null default false,
 decision_id uuid not null unique,
 recorded_at timestamptz not null default now(),
 snapshot_fingerprint text not null check(snapshot_fingerprint ~ '^[a-f0-9]{32}$'),
 session_identity jsonb not null check(jsonb_typeof(session_identity)='array'),
 capacity_ceiling integer not null check(capacity_ceiling>0),
 retained_source_observed_at timestamptz not null,
 retained_external_ids text[] not null,
 unmatched_external_ids text[] not null,
 anonymous_reserved_seats integer not null check(anonymous_reserved_seats>=0),
 canonical_registered_at_cutover integer not null check(canonical_registered_at_cutover>=0),
 unique(class_session_id,revision)
);
alter table public.landerware_session_authority_events enable row level security;
revoke all on public.landerware_session_authority_events from public,anon,authenticated,service_role;
grant select,insert on public.landerware_session_authority_events to service_role;
create policy native_authority_service_read on public.landerware_session_authority_events for select to service_role using(true);
create policy native_authority_service_insert on public.landerware_session_authority_events for insert to service_role with check(true);

-- Internal evidence reader. The MD5 value is only an optimistic-concurrency
-- fingerprint of server records, not a credential or an authorization token.
create function public.native_session_authority_snapshot(p_session_id uuid)
returns jsonb language plpgsql security invoker set search_path='' as $function$
declare s public.class_sessions; proof jsonb; observed timestamptz; ids text[]; missing text[];
 identity jsonb; roster jsonb; holds jsonb; inv jsonb; cap integer; known integer; revision integer;
 prior_ceiling integer; prior_reserved integer; first_cutover timestamptz; held integer; registered integer;
begin
 select * into s from public.class_sessions where id=p_session_id;
 if s.id is null or s.record_scope<>'operational' then raise exception 'session_not_operational'; end if;
 proof:=s.external_reconciliation;
 if proof->>'complete' is distinct from 'true'
   or jsonb_typeof(proof->'active_external_registration_ids') is distinct from 'array'
   or coalesce(proof->>'active_registration_count','') !~ '^[0-9]{1,6}$'
   or nullif(proof->>'source_observed_at','') is null then raise exception 'native_occupancy_review_required'; end if;
 begin observed:=(proof->>'source_observed_at')::timestamptz;
 exception when others then raise exception 'native_occupancy_review_required'; end;
 if not isfinite(observed) or observed>now()+interval '5 minutes' then raise exception 'native_occupancy_review_required'; end if;
 if exists(select 1 from jsonb_array_elements(proof->'active_external_registration_ids') v
    where jsonb_typeof(v)<>'string' or length(v#>>'{}') not between 1 and 200) then raise exception 'native_occupancy_review_required'; end if;
 select coalesce(array_agg(v order by v),'{}'::text[]) into ids from jsonb_array_elements_text(proof->'active_external_registration_ids') v;
 if cardinality(ids)<>(proof->>'active_registration_count')::integer
   or cardinality(ids)<>(select count(distinct v) from unnest(ids) v) then raise exception 'native_occupancy_review_required'; end if;
 select to_jsonb(i) into inv from public.landerware_public_session_inventory i where i.external_class_id=s.external_class_id;
 cap:=least(s.max_students,coalesce((inv->>'capacity')::integer,s.max_students));
 if cap is null or cap<1 then raise exception 'unverified_capacity'; end if;
 select min(e.capacity_ceiling),coalesce(max(e.anonymous_reserved_seats),0),min(e.recorded_at)
   into prior_ceiling,prior_reserved,first_cutover from public.landerware_session_authority_events e where e.class_session_id=s.id and e.enabled;
 cap:=least(cap,coalesce(prior_ceiling,cap));
 known:=greatest(cardinality(ids),coalesce((inv->>'externally_registered')::integer,0),coalesce(s.historical_student_count,0));
 select coalesce(array_agg(v order by v),'{}'::text[]) into missing from (
   select unnest(ids) v union select unnest(e.unmatched_external_ids) from public.landerware_session_authority_events e where e.class_session_id=s.id and e.enabled
 ) retained where not exists(select 1 from public.registrations r where r.class_session_id=s.id and r.external_registration_id=v
   and (r.status in ('registered','confirmed','completed','active')
     or (r.status in ('canceled','cancelled') and r.canceled_at>=first_cutover)));
 select count(*) into registered from public.registrations r where r.class_session_id=s.id and r.status in ('registered','confirmed','completed','active');
 select count(*) into held from public.landerware_public_order_students st join public.landerware_public_orders o on o.id=st.order_id
   where o.class_session_id=s.id and o.status in ('held','checkout_open') and (o.hold_expires_at>now() or (o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true'));
 identity:=jsonb_build_array(s.course_id,s.start_at,s.end_at,s.consumption_start_at,s.consumption_end_at,
   s.lead_instructor_id,s.location_id,s.resource_id,s.organization_id,s.external_class_id,s.record_scope);
 select coalesce(jsonb_agg(jsonb_build_array(r.id,r.status,r.registration_source,r.external_registration_id,r.canceled_at) order by r.id),'[]'::jsonb)
   into roster from public.registrations r where r.class_session_id=s.id;
 select coalesce(jsonb_agg(jsonb_build_array(o.id,o.status,o.hold_expires_at,o.payment_evidence,
    (select count(*) from public.landerware_public_order_students st where st.order_id=o.id)) order by o.id),'[]'::jsonb)
   into holds from public.landerware_public_orders o where o.class_session_id=s.id;
 select coalesce(max(e.revision),0) into revision from public.landerware_session_authority_events e where e.class_session_id=s.id;
 return jsonb_build_object('sessionId',s.id,'revision',revision,'identity',identity,'capacity',cap,
   'sourceObservedAt',observed,'retainedExternalIds',ids,'unmatchedExternalIds',missing,
   'anonymousReservedSeats',greatest(known-cardinality(ids),prior_reserved),'canonicalRegistered',registered,'heldSeats',held,
   'unreconciledReserved',cardinality(missing)+greatest(known-cardinality(ids),prior_reserved),
   'fingerprint',md5(jsonb_build_array(identity,s.registration_backend,s.status,s.visibility,s.registration_status,
     s.max_students,s.historical_student_count,inv,proof,roster,holds,revision)::text));
end $function$;

-- Explicit scoped release admission only. It neither changes a session's
-- backend/visibility/status nor creates a registration or claims payment.
create function public.native_session_authority_record(p_session_id uuid,p_decision_id uuid,
 p_expected_fingerprint text,p_expected_revision integer,p_enabled boolean default false)
returns jsonb language plpgsql security invoker set search_path='' set lock_timeout='2s' as $function$
declare snapshot jsonb; event_id uuid; s public.class_sessions; existing public.landerware_session_authority_events;
begin
 if p_session_id is null or p_decision_id is null or p_enabled is null or p_expected_revision is null or p_expected_revision<0
   or p_expected_fingerprint is null or p_expected_fingerprint !~ '^[a-f0-9]{32}$' then raise exception 'invalid_native_authority_request'; end if;
 perform pg_advisory_xact_lock(hashtextextended('native-session-authority|'||p_session_id::text,0));
 select * into existing from public.landerware_session_authority_events where decision_id=p_decision_id;
 if existing.id is not null then
  if existing.class_session_id<>p_session_id or existing.snapshot_fingerprint<>p_expected_fingerprint
    or existing.revision<>p_expected_revision+1 or existing.enabled<>p_enabled then raise exception 'native_authority_decision_reuse'; end if;
  return jsonb_build_object('id',existing.id,'revision',existing.revision,'enabled',existing.enabled,'replayed',true);
 end if;
 -- Match checkout/finalization's session-first row lock. The short table locks
 -- then stabilize canonical imports, inventory and paid holds for admission.
 select * into s from public.class_sessions where id=p_session_id for update;
 lock table public.class_sessions,public.registrations,public.landerware_public_session_inventory,
   public.landerware_public_orders,public.landerware_public_order_students in share mode;
 if p_enabled and (s.registration_backend is distinct from 'landerware' or s.record_scope is distinct from 'operational') then raise exception 'native_backend_required'; end if;
 snapshot:=public.native_session_authority_snapshot(p_session_id);
 if snapshot->>'fingerprint'<>p_expected_fingerprint or (snapshot->>'revision')::integer<>p_expected_revision then raise exception 'native_authority_snapshot_changed'; end if;
 if p_enabled and (snapshot->>'canonicalRegistered')::integer+(snapshot->>'heldSeats')::integer+(snapshot->>'unreconciledReserved')::integer>(snapshot->>'capacity')::integer then raise exception 'native_occupancy_conflict'; end if;
 insert into public.landerware_session_authority_events(class_session_id,revision,enabled,decision_id,
   snapshot_fingerprint,session_identity,capacity_ceiling,retained_source_observed_at,
   retained_external_ids,unmatched_external_ids,anonymous_reserved_seats,canonical_registered_at_cutover)
 values(p_session_id,p_expected_revision+1,p_enabled,p_decision_id,p_expected_fingerprint,snapshot->'identity',
   (snapshot->>'capacity')::integer,(snapshot->>'sourceObservedAt')::timestamptz,
   array(select jsonb_array_elements_text(snapshot->'retainedExternalIds')),
   array(select jsonb_array_elements_text(snapshot->'unmatchedExternalIds')),
   (snapshot->>'anonymousReservedSeats')::integer,(snapshot->>'canonicalRegistered')::integer) returning id into event_id;
 return jsonb_build_object('id',event_id,'revision',p_expected_revision+1,'enabled',p_enabled,'replayed',false);
end $function$;

create function public.native_session_authority_state(p_session_id uuid)
returns jsonb language plpgsql security invoker set search_path='' as $function$
declare s public.class_sessions; e public.landerware_session_authority_events; identity jsonb; reserved integer;
begin
 select * into e from public.landerware_session_authority_events where class_session_id=p_session_id order by revision desc limit 1;
 if e.id is null then return null; end if;
 if not e.enabled then
  if exists(select 1 from public.landerware_session_authority_events prior where prior.class_session_id=p_session_id and prior.enabled) then raise exception 'native_authority_disabled'; end if;
  return null;
 end if;
 select * into s from public.class_sessions where id=p_session_id;
 identity:=jsonb_build_array(s.course_id,s.start_at,s.end_at,s.consumption_start_at,s.consumption_end_at,
   s.lead_instructor_id,s.location_id,s.resource_id,s.organization_id,s.external_class_id,s.record_scope);
 if s.registration_backend is distinct from 'landerware' or identity is distinct from e.session_identity then raise exception 'native_authority_identity_changed'; end if;
 -- Unmapped inherited seats stay reserved. A subsequently imported active row
 -- replaces the reservation once; an explicit native cancellation can release
 -- it. Anonymous count-only uncertainty never disappears automatically.
 select e.anonymous_reserved_seats+count(*) into reserved from unnest(e.unmatched_external_ids) v
 where not exists(select 1 from public.registrations r where r.class_session_id=s.id and r.external_registration_id=v
   and (r.status in ('registered','confirmed','completed','active')
     or (r.status in ('canceled','cancelled') and r.canceled_at>=e.recorded_at)));
 return jsonb_build_object('version','landerware-session-authority.v1','revision',e.revision,
   'capacityCeiling',e.capacity_ceiling,'unreconciledReserved',reserved);
end $function$;

revoke all on function public.native_session_authority_snapshot(uuid),
 public.native_session_authority_record(uuid,uuid,text,integer,boolean),
 public.native_session_authority_state(uuid) from public,anon,authenticated;
grant execute on function public.native_session_authority_snapshot(uuid),
 public.native_session_authority_record(uuid,uuid,text,integer,boolean),
 public.native_session_authority_state(uuid) to service_role;

CREATE OR REPLACE FUNCTION public.landerware_public_seat_state(p_session_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare s public.class_sessions; v_registered integer; v_holds integer; v_external integer:=0; v_native integer;
  proof jsonb; observed timestamptz; v_capacity integer; authority jsonb; v_reserved integer:=0;
begin
  select * into s from public.class_sessions where id=p_session_id;
  if s.id is null then raise exception 'session_not_open'; end if;
  -- Honor a stricter existing published inventory limit as well as the canonical
  -- physical class limit. Never increase an established seat limit at checkout.
  select least(s.max_students,coalesce((select i.capacity from public.landerware_public_session_inventory i where i.external_class_id=s.external_class_id),s.max_students)) into v_capacity;
  if v_capacity is null or v_capacity<1 then raise exception 'unverified_capacity'; end if;
  select count(*) into v_registered from public.registrations where class_session_id=s.id and status in ('registered','confirmed','completed','active');
  authority:=public.native_session_authority_state(s.id);
  if authority is not null then
    v_capacity:=least(v_capacity,(authority->>'capacityCeiling')::integer);
    v_reserved:=(authority->>'unreconciledReserved')::integer;
    select count(*) into v_external from public.registrations r where r.class_session_id=s.id
      and r.status in ('registered','confirmed','completed','active')
      and (r.external_registration_id is not null or r.registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation'));
  -- Sessions without an explicit native cutover retain the existing gate.
  elsif s.registration_backend='enrollware' or s.external_class_id ~ '^\d+$'
    or exists(select 1 from public.registrations r where r.class_session_id=s.id
      and r.status in ('registered','confirmed','completed','active')
      and (r.external_registration_id is not null or r.registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation'))) then
    proof:=coalesce(s.external_reconciliation,'{}'::jsonb);
    observed:=nullif(proof->>'source_observed_at','')::timestamptz;
    if coalesce((proof->>'complete')::boolean,false) is not true or observed is null or observed<now()-interval '1 hour' or observed>now()+interval '5 minutes'
      or jsonb_typeof(proof->'active_external_registration_ids') is distinct from 'array' then raise exception 'external_reconciliation_required'; end if;
    v_external:=jsonb_array_length(proof->'active_external_registration_ids');
    if v_external is distinct from (proof->>'active_registration_count')::integer
      or v_external<>(select count(distinct value) from jsonb_array_elements_text(proof->'active_external_registration_ids')) then raise exception 'external_reconciliation_required'; end if;
    -- Every external seat must be reconciled to the operational roster exactly once.
    if v_external<>(select count(*) from public.registrations r where r.class_session_id=s.id and r.status in ('registered','confirmed','completed','active') and proof->'active_external_registration_ids' ? r.external_registration_id)
      or exists(select 1 from public.registrations r where r.class_session_id=s.id and r.status in ('registered','confirmed','completed','active')
        and (r.external_registration_id is not null or r.registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation'))
        and not coalesce(proof->'active_external_registration_ids' ? r.external_registration_id,false)) then raise exception 'external_reconciliation_required'; end if;
  end if;
  v_native:=v_registered-v_external;
  select count(*) into v_holds from public.landerware_public_order_students st join public.landerware_public_orders o on o.id=st.order_id
    where o.class_session_id=s.id and o.status in ('held','checkout_open') and (o.hold_expires_at>now() or (o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true'));
  -- Never let a finalizer add its own hold to a clamped zero and conceal a deficit.
  if authority is not null and v_registered+v_holds+v_reserved>v_capacity then raise exception 'native_occupancy_conflict'; end if;
  return jsonb_build_object('capacity',v_capacity,'registered',v_registered,'externallyRegistered',v_external,'nativeRegistered',v_native,'holds',v_holds,'remaining',greatest(v_capacity-v_registered-v_holds-v_reserved,0))
    ||case when authority is null then '{}'::jsonb else jsonb_build_object('registrationAuthority',authority->>'version','authorityRevision',authority->'revision','unreconciledReserved',v_reserved) end;
end $function$
;

-- Preserve the already-recorded paid hold during a review outcome. The native
-- finalizer must not expire that hold, erase its protection flag, or disguise a
-- native occupancy conflict as a request for fresh retired-service evidence.
do $finalizer$
declare definition text;
 old_reader text:=$old$begin seats:=public.landerware_public_seat_state(s.id); exception when others then v_error:='external_reconciliation_required'; end;$old$;
 new_reader text:=$new$begin seats:=public.landerware_public_seat_state(s.id); exception when others then
    v_error:=case when sqlerrm in ('native_occupancy_conflict','native_authority_identity_changed','native_authority_disabled') then sqlerrm else 'external_reconciliation_required' end; end;$new$;
 old_review text:=$old$update public.landerware_public_orders set status=case when status in ('held','checkout_open') then 'expired' else status end,payment_evidence=p_evidence,reconciliation_error=v_error,updated_at=now() where id=o.id;$old$;
 new_review text:=$new$-- native_authority_paid_review_v1
   update public.landerware_public_orders set status=case
     when o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true' then status
     when status in ('held','checkout_open') then 'expired' else status end,
     payment_evidence=p_evidence||jsonb_build_object('seat_hold_protected',coalesce(o.payment_evidence->>'payment_status'='paid' and o.payment_evidence->>'seat_hold_protected'='true',false)),
     reconciliation_error=v_error,updated_at=now() where id=o.id;$new$;
begin
 definition:=pg_get_functiondef('public.native_checkout_finalize_order(uuid,text,jsonb)'::regprocedure);
 if (length(definition)-length(replace(definition,old_reader,'')))/length(old_reader)<>1
   or (length(definition)-length(replace(definition,old_review,'')))/length(old_review)<>1 then raise exception 'native_authority_finalizer_review_required'; end if;
 execute replace(replace(definition,old_reader,new_reader),old_review,new_review);
end $finalizer$;

commit;
