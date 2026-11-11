begin;
create table public.native_owner_transport_proof (
 slot text primary key check (slot = 'owner_transport_once'),
 proof_id uuid not null unique,
 state text not null default 'pending' check (state in ('pending','attempted','accepted','rejected','unknown')),
 created_at timestamptz not null default now(),
 attempted_at timestamptz,
 settled_at timestamptz,
 provider_id text,
 error_code text,
 check ((state = 'accepted' and provider_id is not null and provider_id ~ '^[A-Za-z0-9_-]{1,128}$') or (state <> 'accepted' and provider_id is null))
);
alter table public.native_owner_transport_proof enable row level security;
revoke all on public.native_owner_transport_proof from public, anon, authenticated, service_role;
grant select, insert, update on public.native_owner_transport_proof to service_role;
create policy native_owner_proof_service on public.native_owner_transport_proof for all to service_role using (true) with check (true);
create function public.native_owner_transport_claim() returns jsonb
language plpgsql security invoker set search_path = '' as $$
declare v public.native_owner_transport_proof;
begin
 update public.native_owner_transport_proof set state='attempted', attempted_at=clock_timestamp()
 where slot='owner_transport_once' and state='pending' returning * into v;
 if found then return jsonb_build_object('claimed',true,'proofId',v.proof_id); end if;
 select * into v from public.native_owner_transport_proof where slot='owner_transport_once';
 return jsonb_build_object('claimed',false,'state',coalesce(v.state,'not_authorized'),'providerId',v.provider_id);
end;
$$;
create function public.native_owner_transport_settle(p_proof_id uuid,p_state text,p_provider_id text,p_error_code text) returns jsonb
language plpgsql security invoker set search_path = '' as $$
declare v public.native_owner_transport_proof;
begin
 if p_state not in ('accepted','rejected','unknown') or p_state is null then raise exception 'invalid outcome'; end if;
 if (p_state='accepted' and (p_provider_id is null or p_provider_id !~ '^[A-Za-z0-9_-]{1,128}$')) or (p_state<>'accepted' and p_provider_id is not null) then raise exception 'invalid receipt'; end if;
 if p_error_code is not null and p_error_code !~ '^[a-z0-9_]{1,128}$' then raise exception 'invalid error'; end if;
 update public.native_owner_transport_proof set state=p_state,provider_id=p_provider_id,error_code=p_error_code,settled_at=clock_timestamp()
 where slot='owner_transport_once' and proof_id=p_proof_id and state='attempted' returning * into v;
 if found then return jsonb_build_object('settled',true); end if;
 select * into v from public.native_owner_transport_proof where slot='owner_transport_once' and proof_id=p_proof_id;
 return jsonb_build_object('settled',false,'replay',v.state=p_state and v.provider_id is not distinct from p_provider_id and v.error_code is not distinct from p_error_code);
end;
$$;
revoke all on function public.native_owner_transport_claim() from public,anon,authenticated;
revoke all on function public.native_owner_transport_settle(uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.native_owner_transport_claim() to service_role;
grant execute on function public.native_owner_transport_settle(uuid,text,text,text) to service_role;
-- Deliberately no operational authorization row, trigger, cron or customer configuration changes.
commit;
