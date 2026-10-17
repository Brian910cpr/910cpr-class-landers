begin;
-- Immutable links make resume recoverable after reload, without trusting a tab's selection.
create table public.customer_interruption_events (
  request_id uuid primary key,
  actor text not null,
  input jsonb not null,
  result jsonb not null,
  occurred_at timestamptz not null default now()
);
create unique index customer_interruption_resume_once
  on public.customer_interruption_events ((input->>'interrupt_request_id'))
  where input->>'operation'='resume';
alter table public.customer_interruption_events enable row level security;
revoke all on public.customer_interruption_events from public,anon,authenticated,service_role;
grant select,insert on public.customer_interruption_events to service_role;

create function public.switch_customer_interaction(p_request_id uuid,p_actor text,p_input jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare
  prior public.customer_interruption_events;
  interruption public.customer_interruption_events;
  current_row public.customer_interactions;
  previous_id uuid := (p_input->'previous'->>'id')::uuid;
  active_id uuid := (p_input->'active'->>'id')::uuid;
  previous_result jsonb;
  active_result jsonb;
  result jsonb;
  lock_id uuid;
begin
  if p_request_id is null or coalesce(length(p_actor),0)=0 or
     previous_id is null or active_id is null or previous_id=active_id or
     coalesce(p_input->>'operation','') not in ('interrupt','resume') then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_request_id::text,2));
  select * into prior from public.customer_interruption_events where request_id=p_request_id;
  if found then
    if prior.input is distinct from p_input or prior.actor is distinct from p_actor then
      raise exception 'idempotency_conflict' using errcode='23505';
    end if;
    return prior.result;
  end if;
  -- Same lock family as single-record saves, in deterministic order for two-record switches.
  for lock_id in select v from (values(previous_id),(active_id)) ids(v) order by v loop
    perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(lock_id::text,1));
  end loop;
  select * into current_row from public.customer_interactions where id=previous_id;
  if not found then raise exception 'missing_previous' using errcode='22023'; end if;
  if (p_input->'previous'->>'expected_version')::integer is distinct from current_row.version then
    raise exception 'version_conflict' using errcode='40001';
  end if;
  if p_input->>'operation'='interrupt' then
    if current_row.status not in ('new','in_progress','awaiting_data','awaiting_approval','follow_up_due') or
       coalesce(p_input->'previous'->>'status','')<>'paused' or
       coalesce(p_input->'active'->>'status','')<>'in_progress' or
       coalesce(p_input->'active'->>'kind','')<>'phone' or
       coalesce(p_input->'active'->>'expected_version','')<>'0' or
       p_input->'active'->>'person_id' is not null or
       exists(select 1 from public.customer_interactions where id=active_id) or
       exists(select 1 from public.customer_cases where id=(p_input->'active'->>'case_id')::uuid) then
      raise exception 'invalid_interrupt' using errcode='22023';
    end if;
  else
    select * into interruption from public.customer_interruption_events
      where request_id=(p_input->>'interrupt_request_id')::uuid;
    if not found or interruption.input->>'operation'<>'interrupt' or
       interruption.input->'previous'->>'id' is distinct from previous_id::text or
       interruption.input->'active'->>'id' is distinct from active_id::text or
       current_row.status<>'paused' or
       not exists(select 1 from public.customer_interactions where id=active_id and status='in_progress' and kind='phone') or
       coalesce(p_input->'previous'->>'status','')<>'in_progress' or
       coalesce(p_input->'active'->>'status','') not in ('resolved','follow_up_due','awaiting_data','awaiting_approval') then
      raise exception 'invalid_resume' using errcode='22023';
    end if;
  end if;
  -- Both saves and their immutable note histories commit together or not at all.
  previous_result := public.save_customer_interaction(pg_catalog.gen_random_uuid(),p_actor,p_input->'previous');
  active_result := public.save_customer_interaction(pg_catalog.gen_random_uuid(),p_actor,p_input->'active');
  result := jsonb_build_object('previous',previous_result,'active',active_result,'request_id',p_request_id,'operation',p_input->>'operation');
  insert into public.customer_interruption_events(request_id,actor,input,result) values(p_request_id,p_actor,p_input,result);
  return result;
end $$;
revoke all on function public.switch_customer_interaction(uuid,text,jsonb) from public,anon,authenticated,service_role;
grant execute on function public.switch_customer_interaction(uuid,text,jsonb) to service_role;
commit;
