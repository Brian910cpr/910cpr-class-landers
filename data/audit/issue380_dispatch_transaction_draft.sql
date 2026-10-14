-- REVIEW DRAFT ONLY; apply after issue380_resolution_transaction_draft.sql in
-- an isolated database. Not a migration, external side-effect fence or rollout.
-- Intake is trusted service-written structured state, never parsed issue prose.
-- Changing intake bumps the card version and invalidates every prior reservation.
create table public.production_board_dispatch_intake (
  card_id uuid primary key references public.production_board_cards(id),
  issue_id bigint unique not null check (issue_id > 0),
  blocked boolean not null,
  source_state text not null check (source_state in ('action_required','already_corrected','unknown')),
  worker_safe boolean not null,
  source_ref text not null check (length(trim(source_ref)) between 1 and 2000),
  checked_at timestamptz not null check (isfinite(checked_at)),
  -- A structured owner assertion does not prove the source was inspected.
  -- Only a future reviewed collector may establish authoritative_observation.
  provenance text not null default 'owner_assertion'
    check (provenance in ('owner_assertion','authoritative_observation'))
);
create function public.production_board_dispatch_intake_changed() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin
  if TG_OP='UPDATE' and new.card_id<>old.card_id then
    raise exception 'dispatch_intake_identity_immutable';
  end if;
  if TG_OP='UPDATE' and new.issue_id<>old.issue_id then
    raise exception 'intake_issue_immutable';
  end if;
  update public.production_board_cards set updated_at=clock_timestamp()
    where id=coalesce(new.card_id,old.card_id);
  return null;
end $$;
create trigger dispatch_intake_changed after insert or update or delete
on public.production_board_dispatch_intake for each row
execute function public.production_board_dispatch_intake_changed();
-- Immutable decisions also serve as reservations; no mutable parallel card state.
create table public.production_board_dispatch_decisions (
  request_id uuid primary key,
  card_id uuid not null references public.production_board_cards(id),
  request jsonb not null,
  decision text not null check (decision in ('skip','review','reserved')),
  reason text not null,
  card_version bigint not null,
  lease_until timestamptz,
  recorded_at timestamptz not null default clock_timestamp()
);
create index dispatch_card_reservations on public.production_board_dispatch_decisions(card_id,lease_until);
alter table public.production_board_dispatch_intake enable row level security;
alter table public.production_board_dispatch_decisions enable row level security;
revoke all on public.production_board_dispatch_intake, public.production_board_dispatch_decisions
  from public, anon, authenticated, service_role;
-- Canonical identity must survive routine caller writes. Publication updates in
-- place; DELETE/reinsert would bypass UPDATE identity checks. No retention or
-- administrative identity-replacement protocol is authorized by this draft.
grant select,insert,update on public.production_board_dispatch_intake to service_role;
grant select,insert on public.production_board_dispatch_decisions to service_role;
revoke all on function public.production_board_dispatch_intake_changed() from public,anon,authenticated;

create function public.production_board_dispatch_decide(
  p_card uuid, p_issue bigint, p_version bigint, p_request uuid,
  p_phase text, p_reservation uuid
) returns jsonb language plpgsql security invoker set search_path = '' as $$
declare
  c public.production_board_cards%rowtype;
  i public.production_board_dispatch_intake%rowtype;
  e public.production_board_dispatch_decisions%rowtype;
  payload jsonb;
  outcome text := 'review'; why text; expiry timestamptz;
begin
  if p_card is null or p_issue is null or p_issue < 1 or p_version is null or p_version < 1
    or p_request is null or p_phase is null or p_phase not in ('selection','pre_side_effect')
    or (p_phase='selection' and p_reservation is not null)
    or (p_phase='pre_side_effect' and p_reservation is null) then
    raise exception 'invalid_dispatch_request';
  end if;
  payload:=jsonb_build_object('card_id',p_card,'issue_id',p_issue,'version',p_version,
    'phase',p_phase,'reservation',p_reservation);
  perform pg_advisory_xact_lock(hashtextextended(p_request::text, 381));
  select * into e from public.production_board_dispatch_decisions where request_id=p_request;
  if found then
    if e.request<>payload then raise exception 'idempotency_conflict'; end if;
    -- A replay reports history, never a fresh authorization or renewed lease.
    return jsonb_build_object('replayed',true,'decision',e.decision,'reason',e.reason,
      'version',e.card_version::text,'request_id',p_request,'can_execute',false);
  end if;
  -- Match intake DML and its AFTER trigger: intake row BEFORE card row.
  -- Never take a card lock and then wait for intake. A missing intake row has
  -- no gap lock for trusted direct DML: an insert outside the approved
  -- publisher protocol may be unseen, yielding a safe review.
  -- Future publisher RPCs must preserve this order (including version checks).
  -- Same missing-row serialization as the typed publisher.
  perform pg_advisory_xact_lock(hashtextextended(p_card::text,3820));
  select * into i from public.production_board_dispatch_intake where card_id=p_card for share;
  select * into c from public.production_board_cards where id=p_card for update;
  if not found then raise exception 'card_not_found'; end if;
  if i.card_id is null or i.issue_id<>p_issue then why:='canonical_intake_required';
  elsif c.resolution_state<>'unresolved' then outcome:='skip'; why:='recorded_resolution';
  elsif c.row_version<>p_version then why:='stale_card_version';
  elsif i.blocked then outcome:='skip'; why:='blocked_requires_explicit_reconciliation';
  elsif i.checked_at>clock_timestamp() or i.checked_at<clock_timestamp()-interval '5 minutes' then why:='source_check_stale';
  elsif i.source_state='already_corrected' then why:='propose_verified_resolved';
  elsif i.source_state<>'action_required' then why:='authoritative_source_check_required';
  elsif i.provenance<>'authoritative_observation' then why:='authoritative_source_check_required';
  elsif not i.worker_safe then why:='worker_safe_opt_in_required';
  elsif p_phase='selection' then
    if exists(select 1 from public.production_board_dispatch_decisions
      where card_id=p_card and card_version=c.row_version and decision='reserved'
        and lease_until>clock_timestamp()) then why:='reservation_active';
    else outcome:='reserved'; why:='runtime_fence_required'; expiry:=clock_timestamp()+interval '60 seconds'; end if;
  else
    select * into e from public.production_board_dispatch_decisions
      where request_id=p_reservation and card_id=p_card and card_version=c.row_version
        and decision='reserved' and lease_until>clock_timestamp()
        and request->>'phase'='selection' and request->>'issue_id'=p_issue::text;
    if not found then why:='reservation_missing_or_expired';
    else why:='runtime_fence_required'; end if;
  end if;
  insert into public.production_board_dispatch_decisions
    (request_id,card_id,request,decision,reason,card_version,lease_until)
    values(p_request,p_card,payload,outcome,why,c.row_version,expiry);
  insert into public.production_board_activity(card_id,action,actor,detail)
    values(p_card,'dispatch_decision','owner_authenticated_gateway',
      jsonb_build_object('request_id',p_request,'phase',p_phase,'decision',outcome,
        'reason',why,'version',c.row_version::text));
  return jsonb_build_object('replayed',false,'decision',outcome,'reason',why,
    'version',c.row_version::text,'request_id',p_request,'can_execute',false);
end $$;
revoke all on function public.production_board_dispatch_decide(uuid,bigint,bigint,uuid,text,uuid)
  from public, anon, authenticated;
grant execute on function public.production_board_dispatch_decide(uuid,bigint,bigint,uuid,text,uuid)
  to service_role;
