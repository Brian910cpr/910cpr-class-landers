-- REVIEW ONLY, isolated DB after collector publication draft. Not a migration.
begin;
-- Separately provisioned NOLOGIN executor; never grant it to runtime logins.
do $$ begin
  if not exists(select 1 from pg_roles where rolname='production_board_collector_executor'
    and not rolcanlogin and not rolsuper and not rolcreatedb and not rolcreaterole
    and not rolreplication and not rolbypassrls)
    or exists(select 1 from pg_auth_members where roleid='production_board_collector_executor'::regrole
      or member='production_board_collector_executor'::regrole) then
    raise exception 'isolated_executor_role_required';
  end if;
end $$;
grant usage on schema public to production_board_collector_executor;
grant select(id,row_version,resolution_state),update(updated_at) on public.production_board_cards to production_board_collector_executor;
grant select,insert,update on public.production_board_dispatch_intake to production_board_collector_executor;
grant select,insert on public.production_board_observation_events,public.production_board_collector_publications to production_board_collector_executor;
create policy executor_card_read on public.production_board_cards for select to production_board_collector_executor using(true);
create policy executor_card_touch on public.production_board_cards for update to production_board_collector_executor using(true) with check(true);
create policy executor_intake_read on public.production_board_dispatch_intake for select to production_board_collector_executor using(true);
create policy executor_intake_insert on public.production_board_dispatch_intake for insert to production_board_collector_executor with check(true);
create policy executor_intake_update on public.production_board_dispatch_intake for update to production_board_collector_executor using(true) with check(true);
create policy executor_event_insert on public.production_board_observation_events for insert to production_board_collector_executor with check(actor=session_user);
create policy executor_receipt_read on public.production_board_collector_publications for select to production_board_collector_executor using(actor=session_user);
create policy executor_receipt_insert on public.production_board_collector_publications for insert to production_board_collector_executor with check(actor=session_user);

-- Reuse the reviewed typed transaction and lock order, changing only privilege
-- boundary. No dynamic request SQL, custom GUC authority, or table-owner bypass.
do $$ declare definition text; begin
  definition:=pg_get_functiondef('public.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz)'::regprocedure);
  if strpos(definition, 'current_user<>''production_board_collector''')=0 then
    raise exception 'unexpected_publisher_baseline';
  end if;
  definition:=replace(definition,'current_user<>''production_board_collector''',
    'current_user<>''production_board_collector_executor'' or not pg_has_role(session_user,''production_board_collector'',''MEMBER'')');
  execute definition;
end $$;
alter function public.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz) security definer;
create schema production_board_private;
revoke all on schema production_board_private from public,anon,authenticated,service_role;
grant usage on schema production_board_private to production_board_collector;
grant usage,create on schema production_board_private to production_board_collector_executor;
alter function public.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz) set schema production_board_private;
alter function production_board_private.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz) owner to production_board_collector_executor;
revoke create on schema production_board_private from production_board_collector_executor;
revoke all on function production_board_private.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz) from public,anon,authenticated,service_role;
grant execute on function production_board_private.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz) to production_board_collector;

create or replace function public.production_board_intake_observation_guard() returns trigger
language plpgsql security invoker set search_path='' as $$
begin
  if new.provenance='authoritative_observation'
    and current_user <> 'production_board_collector_executor'
    and current_user <> pg_get_userbyid((select relowner from pg_class
      where oid='public.production_board_dispatch_intake'::regclass)) then
    raise exception 'authoritative_collector_required';
  end if;
  return new;
end $$;
create or replace function public.production_board_audit_collector_observation() returns trigger
language plpgsql security invoker set search_path='' as $$
begin
  if current_user='production_board_collector_executor' then
    insert into public.production_board_observation_events(card_id,actor,prior,observed,resulting_version)
    select new.card_id,session_user,case when TG_OP='UPDATE' then to_jsonb(old) else null end,
      to_jsonb(new),row_version from public.production_board_cards where id=new.card_id;
    if not found then raise exception 'collector_card_inaccessible'; end if;
  end if;
  return null;
end $$;
revoke insert,update on public.production_board_dispatch_intake from production_board_collector;
revoke update(updated_at) on public.production_board_cards from production_board_collector;
revoke insert on public.production_board_observation_events,public.production_board_collector_publications from production_board_collector;
-- Administrative owner remains trusted. Production role graph/source binding
-- still require independent proof. All publisher results remain can_execute=false.

commit;
