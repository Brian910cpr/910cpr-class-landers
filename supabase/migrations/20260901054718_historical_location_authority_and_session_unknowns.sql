-- Review-only migration. Do not apply before the associated authority review.

alter table public.locations
  add column scheduling_status text;

-- Preserve the behavior of every pre-migration location. New records fail safe.
update public.locations set scheduling_status = 'active';

alter table public.locations
  alter column scheduling_status set default 'inactive',
  alter column scheduling_status set not null,
  add constraint locations_scheduling_status_check
    check (scheduling_status in ('active', 'inactive', 'historical_only')),
  add constraint locations_public_requires_active_check
    check (not public or scheduling_status = 'active');

create index locations_scheduling_status_idx
  on public.locations (scheduling_status, name);

create table public.location_scheduling_status_events (
  id uuid primary key default gen_random_uuid(),
  location_id uuid not null references public.locations(id) on delete restrict,
  previous_status text,
  new_status text not null,
  reason text not null check (btrim(reason) <> ''),
  changed_by text not null,
  changed_at timestamptz not null default now(),
  provenance jsonb not null default '{}'::jsonb,
  check (previous_status is null or previous_status in ('active', 'inactive', 'historical_only')),
  check (new_status in ('active', 'inactive', 'historical_only')),
  check (previous_status is distinct from new_status)
);

create index location_scheduling_status_events_location_time_idx
  on public.location_scheduling_status_events (location_id, changed_at desc);

alter table public.location_scheduling_status_events enable row level security;
revoke all on table public.location_scheduling_status_events from anon, authenticated;

create or replace function public.audit_location_scheduling_status()
returns trigger
language plpgsql
set search_path = 'public', 'pg_temp'
as $function$
declare
  v_reason text;
  v_actor text;
begin
  if new.scheduling_status <> 'active' and exists (
    select 1
    from public.class_sessions
    where location_id = new.id and record_scope = 'operational'
  ) then
    raise exception 'a location referenced by an operational session cannot become inactive or historical-only';
  end if;

  if tg_op = 'INSERT' then
    v_reason := coalesce(nullif(btrim(current_setting('app.location_status_reason', true)), ''), 'created_inactive');
    v_actor := coalesce(auth.uid()::text, current_user);
    if new.scheduling_status <> 'inactive'
       and nullif(btrim(current_setting('app.location_status_reason', true)), '') is null then
      raise exception 'explicit app.location_status_reason is required to create an active or historical-only location';
    end if;
    insert into public.location_scheduling_status_events(
      location_id, previous_status, new_status, reason, changed_by
    ) values (new.id, null, new.scheduling_status, v_reason, v_actor);
  elsif new.scheduling_status is distinct from old.scheduling_status then
    v_reason := nullif(btrim(current_setting('app.location_status_reason', true)), '');
    if v_reason is null then
      raise exception 'explicit app.location_status_reason is required for a location scheduling-status transition';
    end if;
    v_actor := coalesce(auth.uid()::text, current_user);
    insert into public.location_scheduling_status_events(
      location_id, previous_status, new_status, reason, changed_by
    ) values (new.id, old.scheduling_status, new.scheduling_status, v_reason, v_actor);
  end if;
  return new;
end;
$function$;

revoke all on function public.audit_location_scheduling_status() from public, anon, authenticated;

create trigger locations_audit_scheduling_status_trg
after insert or update of scheduling_status on public.locations
for each row execute function public.audit_location_scheduling_status();

alter table public.class_sessions
  add column record_scope text;

update public.class_sessions
set record_scope = case when source = 'enrollware_history' then 'historical' else 'operational' end;

alter table public.class_sessions
  alter column record_scope set default 'operational',
  alter column record_scope set not null,
  alter column lead_instructor_id drop not null,
  alter column end_at drop not null,
  alter column consumption_start_at drop not null,
  alter column consumption_end_at drop not null,
  drop constraint class_sessions_check,
  drop constraint class_sessions_check1,
  add constraint class_sessions_record_scope_check
    check (record_scope in ('operational', 'historical')),
  add constraint class_sessions_end_after_start_check
    check (end_at is null or end_at > start_at),
  add constraint class_sessions_consumption_window_check
    check (
      (consumption_start_at is null and consumption_end_at is null)
      or (consumption_start_at is not null and consumption_end_at is not null
          and consumption_end_at > consumption_start_at)
    ),
  add constraint class_sessions_historical_contract_check
    check (
      record_scope <> 'historical'
      or (
        historical_import_key is not null
        and historical_imported_at is not null
        and visibility <> 'public'
        and registration_status = 'closed'
        and status not in ('scheduled', 'active', 'proposed_window', 'draft', 'tentative', 'pending')
      )
    ),
  add constraint class_sessions_operational_fields_check
    check (
      record_scope <> 'operational'
      or (
        lead_instructor_id is not null
        and end_at is not null
        and consumption_start_at is not null
        and consumption_end_at is not null
      )
    );

create index class_sessions_record_scope_start_idx
  on public.class_sessions (record_scope, start_at);

drop trigger if exists class_sessions_historical_required_defaults_trg
  on public.class_sessions;
drop function if exists public.class_sessions_historical_required_defaults();

create or replace function public.class_sessions_default_consumption_window()
returns trigger
language plpgsql
set search_path = 'public', 'pg_temp'
as $function$
begin
  if new.record_scope = 'operational' then
    if new.consumption_start_at is null then
      new.consumption_start_at := new.start_at;
    end if;
    if new.consumption_end_at is null then
      new.consumption_end_at := new.end_at;
    end if;
  end if;
  return new;
end;
$function$;

revoke all on function public.class_sessions_default_consumption_window()
  from public, anon, authenticated;

create or replace function public.enforce_session_location_authority()
returns trigger
language plpgsql
set search_path = 'public', 'pg_temp'
as $function$
declare
  v_location_status text;
begin
  select scheduling_status into v_location_status
  from public.locations
  where id = new.location_id;

  if v_location_status is null then
    raise exception 'canonical location not found';
  end if;

  if new.record_scope = 'operational' and v_location_status <> 'active' then
    raise exception 'operational sessions require an active/schedulable location';
  end if;

  if new.visibility = 'public'
     and (new.record_scope <> 'operational' or v_location_status <> 'active') then
    raise exception 'public sessions require operational scope and an active/schedulable location';
  end if;

  return new;
end;
$function$;

revoke all on function public.enforce_session_location_authority() from public, anon, authenticated;

create trigger class_sessions_enforce_location_authority_trg
before insert or update of record_scope, location_id, visibility
on public.class_sessions
for each row execute function public.enforce_session_location_authority();

-- These pre-existing rows are referenced only by completed Enrollware-history
-- sessions. The transition changes no public flag and no operational session.
select set_config(
  'app.location_status_reason',
  'classify pre-existing history-only authority during reviewed migration',
  true
);
update public.locations
set scheduling_status = 'historical_only'
where location_key like 'hist_location\_%' escape '\'
   or location_key = 'historical_unknown_location';

-- Deliberately no grants are added for browser roles. Existing RLS remains enabled.
-- The 126 reviewed candidates and aliases are not inserted by this migration.
