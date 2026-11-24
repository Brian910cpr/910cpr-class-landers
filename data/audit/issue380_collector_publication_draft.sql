-- REVIEW DRAFT ONLY. Apply after collector capability draft in isolated DB.
-- Source acquisition/attestation and production rollout remain unimplemented.
-- INVOKER preserves R30 privileges; raw capability DML is still possible.
create table public.production_board_collector_publications (
  request_id uuid primary key,
  card_id uuid not null references public.production_board_cards(id),
  actor text not null,
  request jsonb not null,
  resulting_version bigint not null,
  recorded_at timestamptz not null default clock_timestamp()
);
alter table public.production_board_collector_publications enable row level security;
revoke all on public.production_board_collector_publications from public,anon,authenticated,service_role,production_board_collector;
grant select,insert on public.production_board_collector_publications to production_board_collector;
create policy collector_publication_read on public.production_board_collector_publications
  for select to production_board_collector using(actor=session_user);
create policy collector_publication_insert on public.production_board_collector_publications
  for insert to production_board_collector with check(actor=session_user);

create function public.production_board_publish_observation(
  p_card uuid, p_issue bigint, p_version bigint, p_request uuid,
  p_blocked boolean, p_source_state text, p_worker_safe boolean,
  p_source_ref text, p_checked_at timestamptz
) returns jsonb language plpgsql security invoker set search_path='' as $$
declare
  c record;
  i public.production_board_dispatch_intake%rowtype;
  e public.production_board_collector_publications%rowtype;
  payload jsonb;
begin
  if current_user<>'production_board_collector' then raise exception 'collector_role_required'; end if;
  if p_card is null or p_issue is null or p_issue<1 or p_version is null or p_version<1
    or p_request is null or p_blocked is null or p_worker_safe is null
    or p_source_state is null or p_source_state not in ('action_required','already_corrected','unknown')
    or p_source_ref is null or length(trim(p_source_ref)) not between 1 and 2000
    or p_checked_at is null or not isfinite(p_checked_at) then
    raise exception 'invalid_intake_request';
  end if;
  payload:=jsonb_build_object('card_id',p_card,'issue_id',p_issue,'expected_version',p_version::text,
    'blocked',p_blocked,'source_state',p_source_state,'worker_safe',p_worker_safe,
    'source_ref',p_source_ref,'checked_at',p_checked_at,'actor',session_user);
  -- Same lock namespace/order as owner publisher and dispatch.
  perform pg_advisory_xact_lock(hashtextextended(p_request::text,382));
  select * into e from public.production_board_collector_publications where request_id=p_request;
  if found then
    if e.request<>payload then raise exception 'idempotency_conflict'; end if;
    return jsonb_build_object('request_id',p_request,'version',e.resulting_version::text,
      'replayed',true,'can_execute',false);
  end if;
  perform pg_advisory_xact_lock(hashtextextended(p_card::text,3820));
  select * into i from public.production_board_dispatch_intake where card_id=p_card for update;
  select id,row_version,resolution_state into c from public.production_board_cards where id=p_card for update;
  if not found then raise exception 'card_not_found'; end if;
  if c.row_version<>p_version then raise exception 'stale_card_version'; end if;
  if c.resolution_state<>'unresolved' then raise exception 'card_resolved'; end if;
  if i.card_id is not null and i.issue_id<>p_issue then raise exception 'intake_issue_immutable'; end if;
  if p_checked_at>clock_timestamp() or p_checked_at<clock_timestamp()-interval '5 minutes' then
    raise exception 'source_check_stale';
  end if;
  insert into public.production_board_dispatch_intake
    (card_id,issue_id,blocked,source_state,worker_safe,source_ref,checked_at,provenance)
    values(p_card,p_issue,p_blocked,p_source_state,p_worker_safe,p_source_ref,p_checked_at,'authoritative_observation')
    on conflict(card_id) do update set blocked=excluded.blocked,source_state=excluded.source_state,
      worker_safe=excluded.worker_safe,source_ref=excluded.source_ref,checked_at=excluded.checked_at,
      provenance='authoritative_observation';
  select row_version into c from public.production_board_cards where id=p_card;
  -- Existing automatic observation trigger records actor/prior/new/version.
  -- Receipt insertion failure rolls observation, version and audit back too.
  insert into public.production_board_collector_publications
    (request_id,card_id,actor,request,resulting_version)
    values(p_request,p_card,session_user,payload,c.row_version);
  return jsonb_build_object('request_id',p_request,'version',c.row_version::text,
    'replayed',false,'can_execute',false);
end $$;
revoke all on function public.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz)
  from public,anon,authenticated,service_role;
grant execute on function public.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz)
  to production_board_collector;
-- Result is provisional until COMMIT; replay confirms historical publication,
-- never current eligibility. No endpoint, login, membership or runtime install.
