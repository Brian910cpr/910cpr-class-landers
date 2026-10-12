begin;
-- Owner-only operational records. No direct browser Data API access.
create table public.customer_cases (
  id uuid primary key,
  person_id uuid references public.landerware_people(id),
  created_at timestamptz not null default now()
);
create table public.customer_interactions (
  id uuid primary key,
  case_id uuid not null references public.customer_cases(id),
  kind text not null check (kind in ('phone','email','manual')),
  status text not null check (status in ('new','in_progress','paused','awaiting_data','awaiting_approval','follow_up_due','resolved')),
  source text not null check (source in ('manual','gmail','fieldy','pbx')),
  source_id text not null check (length(source_id) between 1 and 200),
  document jsonb not null check (jsonb_typeof(document)='object' and octet_length(document::text)<=200000),
  version integer not null default 1 check (version>0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(source,source_id)
);
create index customer_interactions_case on public.customer_interactions(case_id,updated_at desc);
create table public.customer_follow_up_tasks (
  id uuid primary key,
  case_id uuid not null references public.customer_cases(id),
  interaction_id uuid not null references public.customer_interactions(id),
  title text not null check (length(title) between 1 and 500),
  status text not null check (status in ('proposed','pending','snoozed','complete')),
  due_at timestamptz,
  provenance jsonb not null,
  version integer not null default 1,
  created_at timestamptz not null default now()
);
-- Immutable request receipts preserve raw notes and earlier revisions, plus actor/time.
create table public.customer_interaction_events (
  request_id uuid primary key,
  interaction_id uuid not null references public.customer_interactions(id),
  actor text not null,
  input jsonb not null,
  result jsonb not null,
  occurred_at timestamptz not null default now()
);
alter table public.customer_cases enable row level security;
alter table public.customer_interactions enable row level security;
alter table public.customer_follow_up_tasks enable row level security;
alter table public.customer_interaction_events enable row level security;
revoke all on public.customer_cases,public.customer_interactions,public.customer_follow_up_tasks,public.customer_interaction_events from public,anon,authenticated,service_role;
grant select,insert,update on public.customer_cases,public.customer_interactions,public.customer_follow_up_tasks to service_role;
grant select,insert on public.customer_interaction_events to service_role;

create function public.save_customer_interaction(p_request_id uuid,p_actor text,p_input jsonb)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare
  prior public.customer_interaction_events;
  current_row public.customer_interactions;
  saved public.customer_interactions;
  interaction_id uuid := (p_input->>'id')::uuid;
  case_id uuid := (p_input->>'case_id')::uuid;
  expected integer := (p_input->>'expected_version')::integer;
begin
  if p_request_id is null or interaction_id is null or case_id is null or expected is null or expected<0 or coalesce(length(p_actor),0)=0 then
    raise exception 'invalid_input' using errcode='22023';
  end if;
  -- Serialize retries before checking the receipt; a lost HTTP response is safe to retry.
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_request_id::text,0));
  select * into prior from public.customer_interaction_events e where e.request_id=p_request_id;
  if found then
    if prior.input is distinct from p_input or prior.actor is distinct from p_actor then
      raise exception 'idempotency_conflict' using errcode='23505';
    end if;
    return prior.result;
  end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(interaction_id::text,1));
  select * into current_row from public.customer_interactions i where i.id=interaction_id for update;
  if found then
    if expected<>current_row.version then raise exception 'version_conflict' using errcode='40001'; end if;
    if case_id<>current_row.case_id or p_input->>'source'<>current_row.source or p_input->>'source_id'<>current_row.source_id then
      raise exception 'immutable_identity' using errcode='22023';
    end if;
    update public.customer_interactions i set kind=p_input->>'kind',status=p_input->>'status',document=p_input->'document',version=i.version+1,updated_at=now()
      where i.id=interaction_id returning * into saved;
  else
    if expected<>0 then raise exception 'version_conflict' using errcode='40001'; end if;
    insert into public.customer_cases(id,person_id) values(case_id,(p_input->>'person_id')::uuid) on conflict(id) do nothing;
    -- No fuzzy contact merging: matching an external source must be reviewed explicitly.
    insert into public.customer_interactions(id,case_id,kind,status,source,source_id,document)
      values(interaction_id,case_id,p_input->>'kind',p_input->>'status',p_input->>'source',p_input->>'source_id',p_input->'document') returning * into saved;
  end if;
  insert into public.customer_interaction_events(request_id,interaction_id,actor,input,result)
    values(p_request_id,interaction_id,p_actor,p_input,to_jsonb(saved));
  return to_jsonb(saved);
end $$;
revoke all on function public.save_customer_interaction(uuid,text,jsonb) from public,anon,authenticated,service_role;
grant execute on function public.save_customer_interaction(uuid,text,jsonb) to service_role;
commit;
