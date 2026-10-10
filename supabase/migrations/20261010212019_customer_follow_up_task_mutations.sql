begin;
alter table public.customer_follow_up_tasks add column source_key text;
create unique index customer_follow_up_source_key on public.customer_follow_up_tasks(source_key);
create table public.customer_task_events (
  request_id uuid primary key,
  task_id uuid not null references public.customer_follow_up_tasks(id),
  actor text not null,
  input jsonb not null,
  result jsonb not null,
  occurred_at timestamptz not null default now()
);
alter table public.customer_task_events enable row level security;
revoke all on public.customer_task_events from public,anon,authenticated;
grant select,insert on public.customer_task_events to service_role;
create function public.save_customer_follow_up_task(p_request_id uuid,p_actor text,p_input jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare
  prior public.customer_task_events;
  current_row public.customer_follow_up_tasks;
  saved public.customer_follow_up_tasks;
  task_id uuid := (p_input->>'id')::uuid;
  expected integer := (p_input->>'expected_version')::integer;
begin
  if p_request_id is null or task_id is null or expected is null or expected<0 or coalesce(length(p_actor),0)=0 or
    coalesce(length(btrim(p_input->>'source_key')),0) not between 1 and 200 or
    coalesce(length(btrim(p_input->>'title')),0) not between 1 and 500 or
    coalesce(p_input->>'status','') not in ('proposed','pending','snoozed','complete') or
    jsonb_typeof(p_input->'provenance') is distinct from 'object' or
    coalesce(length(btrim(p_input->'provenance'->>'evidence')),0)=0 or
    octet_length(p_input::text)>200000 or
    (p_input->>'status'='snoozed' and p_input->>'due_at' is null) or
    (p_input->>'status'='complete' and coalesce(length(btrim(p_input->>'completion_evidence')),0)=0) then
    raise exception 'invalid_task' using errcode='22023';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_request_id::text,3));
  select * into prior from public.customer_task_events where request_id=p_request_id;
  if found then
    if prior.input is distinct from p_input or prior.actor is distinct from p_actor then
      raise exception 'idempotency_conflict' using errcode='23505';
    end if;
    return prior.result;
  end if;
  -- Tasks reference the actual interaction/case pair, never a same-name match.
  if not exists(select 1 from public.customer_interactions where id=(p_input->>'interaction_id')::uuid and case_id=(p_input->>'case_id')::uuid) then
    raise exception 'invalid_task_link' using errcode='22023';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(task_id::text,4));
  select * into current_row from public.customer_follow_up_tasks where id=task_id for update;
  if found then
    if expected<>current_row.version then raise exception 'version_conflict' using errcode='40001'; end if;
    if p_input->>'source_key' is distinct from current_row.source_key or
       (p_input->>'case_id')::uuid is distinct from current_row.case_id or
       (p_input->>'interaction_id')::uuid is distinct from current_row.interaction_id or
       p_input->'provenance' is distinct from current_row.provenance then
      raise exception 'immutable_task_provenance' using errcode='22023';
    end if;
    update public.customer_follow_up_tasks set title=p_input->>'title',status=p_input->>'status',due_at=(p_input->>'due_at')::timestamptz,version=version+1
      where id=task_id returning * into saved;
  else
    if expected<>0 then raise exception 'version_conflict' using errcode='40001'; end if;
    insert into public.customer_follow_up_tasks(id,case_id,interaction_id,title,status,due_at,provenance,source_key)
      values(task_id,(p_input->>'case_id')::uuid,(p_input->>'interaction_id')::uuid,p_input->>'title',p_input->>'status',(p_input->>'due_at')::timestamptz,p_input->'provenance',p_input->>'source_key') returning * into saved;
  end if;
  insert into public.customer_task_events(request_id,task_id,actor,input,result) values(p_request_id,task_id,p_actor,p_input,to_jsonb(saved));
  return to_jsonb(saved);
end $$;
revoke all on function public.save_customer_follow_up_task(uuid,text,jsonb) from public,anon,authenticated;
grant execute on function public.save_customer_follow_up_task(uuid,text,jsonb) to service_role;
commit;
