-- REVIEW DRAFT ONLY. Not in migrations; do not apply to production.
-- Owner-authenticated proxy must bind actor and request ID. No evidence upload
-- or worker execution permission is provided by this transaction.
alter table public.production_board_cards
  add column row_version bigint not null default 1,
  add column resolution_state text not null default 'unresolved'
    check (resolution_state in ('unresolved','handled_manually','verified_resolved'));

create function public.production_board_bump_version() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin
  new.row_version := old.row_version + 1;
  new.updated_at := clock_timestamp();
  return new;
end $$;
create trigger production_board_version before update on public.production_board_cards
for each row execute function public.production_board_bump_version();
revoke all on function public.production_board_bump_version() from public, anon, authenticated;

create table public.production_board_resolution_events (
  request_id uuid primary key,
  card_id uuid not null references public.production_board_cards(id),
  actor text not null,
  request jsonb not null,
  prior_state text not null,
  new_state text not null,
  resulting_version bigint not null,
  recorded_at timestamptz not null default clock_timestamp()
);
alter table public.production_board_resolution_events enable row level security;
revoke all on public.production_board_resolution_events from public, anon, authenticated, service_role;
grant select, insert on public.production_board_resolution_events to service_role;

create function public.production_board_resolve(
  p_card uuid, p_version bigint, p_request uuid, p_actor text,
  p_state text, p_explanation text, p_source text, p_completed_at timestamptz
) returns jsonb language plpgsql security invoker set search_path = '' as $$
declare
  c public.production_board_cards%rowtype;
  e public.production_board_resolution_events%rowtype;
  payload jsonb;
begin
  if p_request is null or p_version is null or p_version < 1
     or p_actor is null or length(trim(p_actor)) not between 1 and 180
     or p_state is null or p_state not in ('unresolved','handled_manually','verified_resolved')
     or p_explanation is null or length(trim(p_explanation)) not between 1 and 10000
     or p_source is null or length(trim(p_source)) not between 1 and 2000
     or p_completed_at is null or not isfinite(p_completed_at) then
    raise exception 'invalid_resolution_request';
  end if;
  payload := jsonb_build_object('card_id',p_card,'expected_version',p_version,
    'actor',p_actor,'state',p_state,'explanation',p_explanation,
    'source',p_source,'completed_at',p_completed_at);
  -- Serialize a request ID even when callers incorrectly reuse it across cards.
  perform pg_advisory_xact_lock(hashtextextended(p_request::text, 380));
  select * into e from public.production_board_resolution_events where request_id=p_request;
  if found then
    if e.request <> payload then raise exception 'idempotency_conflict'; end if;
    return jsonb_build_object('replayed',true,'version',e.resulting_version,'state',e.new_state);
  end if;
  select * into c from public.production_board_cards where id=p_card for update;
  if not found then raise exception 'card_not_found'; end if;
  if c.row_version <> p_version then raise exception 'stale_card_version'; end if;
  if c.resolution_state = p_state then raise exception 'no_resolution_transition'; end if;
  update public.production_board_cards set resolution_state=p_state where id=p_card;
  insert into public.production_board_resolution_events
    (request_id,card_id,actor,request,prior_state,new_state,resulting_version)
    values(p_request,p_card,p_actor,payload,c.resolution_state,p_state,c.row_version+1);
  insert into public.production_board_activity(card_id,action,actor,detail)
    values(p_card,'resolution_transition',p_actor,jsonb_build_object('request_id',p_request,
      'prior_state',c.resolution_state,'new_state',p_state,'version',c.row_version+1));
  return jsonb_build_object('replayed',false,'version',c.row_version+1,'state',p_state);
end $$;
revoke all on function public.production_board_resolve(uuid,bigint,uuid,text,text,text,text,timestamptz)
  from public, anon, authenticated;
grant execute on function public.production_board_resolve(uuid,bigint,uuid,text,text,text,text,timestamptz)
  to service_role;
