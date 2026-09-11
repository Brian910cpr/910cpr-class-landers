begin;

-- Backend-only safety slice for issue #141. Nothing in this migration sends a
-- participant or employer message; outbound delivery remains deliberately absent.

create table if not exists public.landerware_requirement_scheduling_state (
  requirement_id uuid primary key references public.landerware_certification_requirements(id) on delete cascade,
  scheduling_status text not null default 'not_requested'
    check (scheduling_status in ('not_requested','requested','selected','change_requested','rescheduled','closed')),
  required_by date,
  required_by_source text,
  current_registration_id uuid references public.landerware_registrations(id),
  current_session_id uuid references public.landerware_sessions(id),
  employer_visibility text not null default 'participant_only'
    check (employer_visibility in ('participant_only','status_visible','joint_followup')),
  missed_count integer not null default 0 check (missed_count >= 0),
  last_participant_communication_at timestamptz,
  request_idempotency_key text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint landerware_scheduling_deadline_required check (
    scheduling_status = 'not_requested'
    or scheduling_status = 'closed'
    or (required_by is not null and nullif(btrim(required_by_source), '') is not null)
  ),
  constraint landerware_scheduling_selection_consistent check (
    scheduling_status not in ('selected','rescheduled')
    or (current_registration_id is not null and current_session_id is not null)
  )
);

create unique index if not exists landerware_scheduling_request_idempotency
  on public.landerware_requirement_scheduling_state(request_idempotency_key)
  where request_idempotency_key is not null;

create table if not exists public.landerware_participant_session_state (
  roster_membership_id uuid primary key references public.landerware_roster_memberships(id) on delete cascade,
  attendance_status text not null default 'unknown'
    check (attendance_status in ('unknown','present','absent','excused','other_verified')),
  completion_status text not null default 'unknown'
    check (completion_status in ('unknown','incomplete','completed')),
  closeout_status text not null default 'not_due'
    check (closeout_status in ('not_due','instructor_closeout_required','verified','exception')),
  latest_attendance_assertion_id uuid,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.landerware_attendance_assertions (
  id uuid primary key default gen_random_uuid(),
  roster_membership_id uuid not null references public.landerware_roster_memberships(id) on delete cascade,
  asserted_status text not null
    check (asserted_status in ('present','absent','excused','other_verified')),
  asserted_by text not null check (nullif(btrim(asserted_by), '') is not null),
  asserted_at timestamptz not null,
  source_type text not null
    check (source_type in ('authorized_human','attendance_artifact','approved_authoritative_source')),
  source_record_id text,
  document_id uuid references public.landerware_documents(id),
  idempotency_key text not null unique,
  created_at timestamptz not null default now(),
  constraint landerware_attendance_source_evidence check (
    source_type = 'authorized_human'
    or nullif(btrim(source_record_id), '') is not null
    or document_id is not null
  )
);

alter table public.landerware_participant_session_state
  drop constraint if exists landerware_participant_state_latest_assertion_fk;
alter table public.landerware_participant_session_state
  add constraint landerware_participant_state_latest_assertion_fk
  foreign key (latest_attendance_assertion_id)
  references public.landerware_attendance_assertions(id);

create or replace function public.landerware_enforce_attendance_fact_provenance()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
declare
  v_assertion public.landerware_attendance_assertions;
begin
  if new.attendance_status = 'unknown' then
    if new.latest_attendance_assertion_id is not null then
      raise exception 'unknown_attendance_cannot_reference_affirmative_assertion';
    end if;
    return new;
  end if;

  if new.latest_attendance_assertion_id is null then
    raise exception 'affirmative_attendance_requires_assertion';
  end if;
  select * into v_assertion from public.landerware_attendance_assertions
  where id = new.latest_attendance_assertion_id;
  if v_assertion.id is null
    or v_assertion.roster_membership_id <> new.roster_membership_id
    or v_assertion.asserted_status <> new.attendance_status then
    raise exception 'attendance_assertion_does_not_match_state';
  end if;
  return new;
end;
$$;

drop trigger if exists landerware_enforce_attendance_fact_provenance_trg
  on public.landerware_participant_session_state;
create trigger landerware_enforce_attendance_fact_provenance_trg
before insert or update of attendance_status, latest_attendance_assertion_id
on public.landerware_participant_session_state
for each row execute function public.landerware_enforce_attendance_fact_provenance();

create table if not exists public.landerware_closeout_tasks (
  id uuid primary key default gen_random_uuid(),
  roster_membership_id uuid not null references public.landerware_roster_memberships(id) on delete cascade,
  task_type text not null default 'verify_attendance'
    check (task_type = 'verify_attendance'),
  status text not null default 'open' check (status in ('open','resolved','cancelled')),
  reason text not null default 'passed_session_attendance_unknown',
  created_at timestamptz not null default now(),
  resolved_at timestamptz,
  unique (roster_membership_id, task_type)
);

create or replace function public.landerware_request_scheduling(
  p_requirement_id uuid,
  p_required_by date,
  p_required_by_source text,
  p_idempotency_key text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_state public.landerware_requirement_scheduling_state;
begin
  if p_required_by is null then raise exception 'required_by_required'; end if;
  if nullif(btrim(p_required_by_source), '') is null then raise exception 'required_by_source_required'; end if;
  if nullif(btrim(p_idempotency_key), '') is null then raise exception 'idempotency_key_required'; end if;

  select * into v_state
  from public.landerware_requirement_scheduling_state
  where request_idempotency_key = p_idempotency_key;
  if v_state.requirement_id is not null then
    return jsonb_build_object('requirementId', v_state.requirement_id, 'status', v_state.scheduling_status, 'idempotentReplay', true, 'outboundEnabled', false);
  end if;

  insert into public.landerware_requirement_scheduling_state(
    requirement_id, scheduling_status, required_by, required_by_source, request_idempotency_key
  ) values (
    p_requirement_id, 'requested', p_required_by, btrim(p_required_by_source), p_idempotency_key
  )
  on conflict (requirement_id) do update set
    scheduling_status = 'requested', required_by = excluded.required_by,
    required_by_source = excluded.required_by_source,
    request_idempotency_key = excluded.request_idempotency_key, updated_at = now()
  returning * into v_state;

  insert into public.landerware_activity_events(
    event_type, actor_source, requirement_id, person_id, organization_id, details
  )
  select 'scheduling_requested', 'system', r.id, r.person_id, r.organization_id,
    jsonb_build_object('requiredBy', v_state.required_by, 'requiredBySource', v_state.required_by_source,
      'idempotencyKey', p_idempotency_key, 'outboundEnabled', false)
  from public.landerware_certification_requirements r where r.id = p_requirement_id;

  return jsonb_build_object('requirementId', v_state.requirement_id, 'status', v_state.scheduling_status, 'idempotentReplay', false, 'outboundEnabled', false);
end;
$$;

create or replace function public.landerware_assert_attendance(
  p_roster_membership_id uuid,
  p_asserted_status text,
  p_asserted_by text,
  p_asserted_at timestamptz,
  p_source_type text,
  p_source_record_id text,
  p_document_id uuid,
  p_idempotency_key text
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_assertion public.landerware_attendance_assertions;
begin
  if p_asserted_status not in ('present','absent','excused','other_verified') then raise exception 'invalid_affirmative_attendance_status'; end if;
  if nullif(btrim(p_asserted_by), '') is null or p_asserted_at is null then raise exception 'attendance_assertion_provenance_required'; end if;
  if p_source_type not in ('authorized_human','attendance_artifact','approved_authoritative_source') then raise exception 'attendance_assertion_source_not_authorized'; end if;
  if p_source_type <> 'authorized_human' and nullif(btrim(p_source_record_id), '') is null and p_document_id is null then raise exception 'attendance_assertion_evidence_required'; end if;
  if nullif(btrim(p_idempotency_key), '') is null then raise exception 'idempotency_key_required'; end if;

  select * into v_assertion from public.landerware_attendance_assertions where idempotency_key = p_idempotency_key;
  if v_assertion.id is not null then
    return jsonb_build_object('assertionId', v_assertion.id, 'attendanceStatus', v_assertion.asserted_status, 'idempotentReplay', true, 'outboundEnabled', false);
  end if;

  insert into public.landerware_attendance_assertions(
    roster_membership_id, asserted_status, asserted_by, asserted_at, source_type,
    source_record_id, document_id, idempotency_key
  ) values (
    p_roster_membership_id, p_asserted_status, btrim(p_asserted_by), p_asserted_at, p_source_type,
    nullif(btrim(p_source_record_id), ''), p_document_id, p_idempotency_key
  ) returning * into v_assertion;

  insert into public.landerware_participant_session_state(
    roster_membership_id, attendance_status, closeout_status, latest_attendance_assertion_id
  ) values (
    p_roster_membership_id, p_asserted_status, 'verified', v_assertion.id
  ) on conflict (roster_membership_id) do update set
    attendance_status = excluded.attendance_status, closeout_status = 'verified',
    latest_attendance_assertion_id = excluded.latest_attendance_assertion_id, updated_at = now();

  update public.landerware_closeout_tasks
  set status = 'resolved', resolved_at = now()
  where roster_membership_id = p_roster_membership_id and task_type = 'verify_attendance' and status = 'open';

  insert into public.landerware_activity_events(
    event_type, actor_source, person_id, registration_id, session_id, details
  )
  select 'attendance_asserted', 'system', m.person_id, m.registration_id, m.session_id,
    jsonb_build_object('assertionId', v_assertion.id, 'assertedStatus', v_assertion.asserted_status,
      'assertedBy', v_assertion.asserted_by, 'assertedAt', v_assertion.asserted_at,
      'sourceType', v_assertion.source_type, 'sourceRecordId', v_assertion.source_record_id,
      'documentId', v_assertion.document_id, 'outboundEnabled', false)
  from public.landerware_roster_memberships m where m.id = p_roster_membership_id;

  return jsonb_build_object('assertionId', v_assertion.id, 'attendanceStatus', v_assertion.asserted_status, 'idempotentReplay', false, 'outboundEnabled', false);
end;
$$;

create or replace function public.landerware_queue_unknown_attendance_closeout(
  p_as_of timestamptz default now()
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_state_count integer := 0;
  v_task_count integer := 0;
begin
  insert into public.landerware_participant_session_state(roster_membership_id, closeout_status)
  select m.id, 'instructor_closeout_required'
  from public.landerware_roster_memberships m
  join public.landerware_sessions s on s.id = m.session_id
  where s.ends_at is not null and s.ends_at < p_as_of
  on conflict (roster_membership_id) do update set
    closeout_status = case
      when public.landerware_participant_session_state.attendance_status = 'unknown'
        then 'instructor_closeout_required'
      else public.landerware_participant_session_state.closeout_status
    end,
    updated_at = now()
  where public.landerware_participant_session_state.attendance_status = 'unknown';
  get diagnostics v_state_count = row_count;

  insert into public.landerware_closeout_tasks(roster_membership_id)
  select ps.roster_membership_id
  from public.landerware_participant_session_state ps
  where ps.attendance_status = 'unknown' and ps.closeout_status = 'instructor_closeout_required'
  on conflict (roster_membership_id, task_type) do nothing;
  get diagnostics v_task_count = row_count;

  return jsonb_build_object('stateRowsTouched', v_state_count, 'tasksInserted', v_task_count,
    'messagesInserted', 0, 'outboundEnabled', false);
end;
$$;

alter table public.landerware_requirement_scheduling_state enable row level security;
alter table public.landerware_participant_session_state enable row level security;
alter table public.landerware_attendance_assertions enable row level security;
alter table public.landerware_closeout_tasks enable row level security;

revoke all on public.landerware_requirement_scheduling_state,
  public.landerware_participant_session_state,
  public.landerware_attendance_assertions,
  public.landerware_closeout_tasks from anon, authenticated;

revoke execute on function public.landerware_request_scheduling(uuid,date,text,text) from public, anon, authenticated;
revoke execute on function public.landerware_assert_attendance(uuid,text,text,timestamptz,text,text,uuid,text) from public, anon, authenticated;
revoke execute on function public.landerware_queue_unknown_attendance_closeout(timestamptz) from public, anon, authenticated;
grant execute on function public.landerware_request_scheduling(uuid,date,text,text) to service_role;
grant execute on function public.landerware_assert_attendance(uuid,text,text,timestamptz,text,text,uuid,text) to service_role;
grant execute on function public.landerware_queue_unknown_attendance_closeout(timestamptz) to service_role;

commit;
