-- Synthetic disposable LOCAL fixture only. Never apply to a hosted project.
do $$begin
 if not exists(select 1 from pg_roles where rolname='anon') then create role anon; end if;
 if not exists(select 1 from pg_roles where rolname='authenticated') then create role authenticated; end if;
 if not exists(select 1 from pg_roles where rolname='service_role') then create role service_role bypassrls; end if;
end $$;
create table public.class_sessions (
 id uuid primary key, course_id uuid, start_at timestamptz, end_at timestamptz,
 consumption_start_at timestamptz, consumption_end_at timestamptz,
 lead_instructor_id uuid, location_id uuid, resource_id uuid, organization_id uuid,
 external_class_id text, record_scope text, registration_backend text,
 max_students integer, source text, external_session_evidence jsonb default '{}',
 external_reconciliation jsonb default '{}', status text, registration_status text,
 visibility text, updated_at timestamptz default now()
);
create table public.landerware_session_authority_events (
 id uuid primary key, class_session_id uuid references public.class_sessions(id), revision integer,
 enabled boolean, session_identity jsonb, capacity_ceiling integer,
 anonymous_reserved_seats integer, unmatched_external_ids text[], recorded_at timestamptz default now(),
 unique(class_session_id,revision)
);
create table public.native_checkout_generated_sessions (
 class_session_id uuid primary key references public.class_sessions(id), identity_hash text,
 state text default 'holding'
);
create table public.landerware_public_session_inventory (external_class_id text primary key, capacity integer,externally_registered integer);
create table public.registrations (id uuid primary key, class_session_id uuid references public.class_sessions(id),status text,external_registration_id text,registration_source text,canceled_at timestamptz);
create table public.landerware_public_orders (id uuid primary key,class_session_id uuid references public.class_sessions(id),status text,hold_expires_at timestamptz,payment_evidence jsonb default '{}');
create table public.landerware_public_order_students (id uuid primary key,order_id uuid references public.landerware_public_orders(id));
create function public.native_checkout_generated_identity(p_session public.class_sessions) returns text
language sql immutable security invoker set search_path='' as $$
 select md5((to_jsonb(p_session)-array['status','registration_status','updated_at'])::text)
$$;
grant usage on schema public to service_role,anon,authenticated;
grant select on all tables in schema public to service_role;
revoke all on function public.native_checkout_generated_identity(public.class_sessions) from public,anon,authenticated;
grant execute on function public.native_checkout_generated_identity(public.class_sessions) to service_role;

-- Exact legacy readers retained solely to assert unchanged mutation semantics.
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
