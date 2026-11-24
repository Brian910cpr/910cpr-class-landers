-- REVIEW DRAFT ONLY. Isolated DB after resolution/dispatch/publication drafts.
-- NO production role/login provisioning or collector source attestation.
-- A dedicated authenticated connection must SET ROLE this non-login capability.
-- Capability role must be provisioned separately by reviewed administration.
-- This draft neither creates login credentials nor assigns memberships.
do $$ begin
  if not exists(select 1 from pg_roles where rolname='production_board_collector'
    and not rolcanlogin and not rolsuper and not rolcreatedb and not rolcreaterole
    and not rolreplication and not rolbypassrls)
    or exists(select 1 from pg_auth_members where member='production_board_collector'::regrole) then
    raise exception 'restricted_collector_role_required';
  end if;
end $$;
grant usage on schema public to production_board_collector;
grant select(id,row_version,resolution_state) on public.production_board_cards to production_board_collector;
grant select on public.production_board_dispatch_intake to production_board_collector;
grant update(updated_at) on public.production_board_cards to production_board_collector;
grant insert,update on public.production_board_dispatch_intake to production_board_collector;
create policy collector_card_read on public.production_board_cards for select to production_board_collector using(true);
create policy collector_card_touch on public.production_board_cards for update to production_board_collector using(true) with check(true);
create policy collector_intake_read on public.production_board_dispatch_intake for select to production_board_collector using(true);
create policy collector_intake_insert on public.production_board_dispatch_intake for insert to production_board_collector with check(true);
create policy collector_intake_update on public.production_board_dispatch_intake for update to production_board_collector using(true) with check(true);

create table public.production_board_observation_events (
  id uuid primary key default gen_random_uuid(),
  card_id uuid not null references public.production_board_cards(id),
  actor text not null,
  prior jsonb,
  observed jsonb not null,
  resulting_version bigint not null,
  recorded_at timestamptz not null default clock_timestamp()
);
alter table public.production_board_observation_events enable row level security;
revoke all on public.production_board_observation_events from public,anon,authenticated,service_role,production_board_collector;
grant select,insert on public.production_board_observation_events to production_board_collector;
grant select on public.production_board_observation_events to service_role;
create policy collector_event_read on public.production_board_observation_events for select to production_board_collector using(true);
create policy collector_event_insert on public.production_board_observation_events for insert to production_board_collector with check(actor=session_user);

create or replace function public.production_board_intake_observation_guard() returns trigger
language plpgsql security invoker set search_path='' as $$
begin
  if new.provenance='authoritative_observation'
    and current_user <> 'production_board_collector'
    and current_user <> pg_get_userbyid((select relowner from pg_class
      where oid='public.production_board_dispatch_intake'::regclass)) then
    raise exception 'authoritative_collector_required';
  end if;
  return new;
end $$;

-- Runs after dispatch_intake_changed (alphabetical trigger order), capturing
-- each transition's actual version, including several writes in one transaction.
-- Actor is the authenticated DB session, never request text or a JWT custom GUC.
create function public.production_board_audit_collector_observation() returns trigger
language plpgsql security invoker set search_path='' as $$
begin
  if current_user='production_board_collector' then
    insert into public.production_board_observation_events(card_id,actor,prior,observed,resulting_version)
    select new.card_id,session_user,case when TG_OP='UPDATE' then to_jsonb(old) else null end,
      to_jsonb(new),row_version from public.production_board_cards where id=new.card_id;
    if not found then raise exception 'collector_card_inaccessible'; end if;
  end if;
  return null;
end $$;
revoke all on function public.production_board_audit_collector_observation() from public,anon,authenticated,service_role;
create trigger z_collector_observation_audit after insert or update on public.production_board_dispatch_intake
for each row execute function public.production_board_audit_collector_observation();
-- No membership, LOGIN, passwords, JWT mapping, HTTP endpoint or runtime install.
-- Administrative table owner is still trusted, not an authenticated collector.
