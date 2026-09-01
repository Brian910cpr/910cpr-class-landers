-- Dockmaster: crossed ledgers are rejected before a credential can be tied to the wrong voyage.
create or replace function public.validate_participant_fact_identity()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_customer uuid;
  v_session uuid;
  v_course uuid;
  v_completion public.participant_completions%rowtype;
begin
  select r.customer_id,r.class_session_id,s.course_id
    into v_customer,v_session,v_course
  from public.registrations r
  join public.class_sessions s on s.id=r.class_session_id
  where r.id=new.registration_id;
  if v_customer is null
     or new.customer_id<>v_customer
     or new.class_session_id<>v_session
     or new.course_id<>v_course then
    raise exception 'participant fact identity does not match canonical registration/session/course';
  end if;
  if tg_table_name='participant_credentials' and (to_jsonb(new)->>'completion_id') is not null then
    select * into v_completion from public.participant_completions
      where id=(to_jsonb(new)->>'completion_id')::uuid;
    if not found
       or v_completion.customer_id<>new.customer_id
       or v_completion.registration_id<>new.registration_id
       or v_completion.class_session_id<>new.class_session_id
       or v_completion.course_id<>new.course_id then
      raise exception 'credential completion does not match canonical participant fact identity';
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists participant_completions_identity_guard on public.participant_completions;
create trigger participant_completions_identity_guard
before insert or update on public.participant_completions
for each row execute function public.validate_participant_fact_identity();

drop trigger if exists participant_credentials_identity_guard on public.participant_credentials;
create trigger participant_credentials_identity_guard
before insert or update on public.participant_credentials
for each row execute function public.validate_participant_fact_identity();

create or replace function public.validate_registration_supersession()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
declare
  v_source public.registrations%rowtype;
  v_target public.registrations%rowtype;
  v_source_course uuid;
  v_target_course uuid;
begin
  select * into v_source from public.registrations where id=new.source_registration_id;
  select * into v_target from public.registrations where id=new.target_registration_id;
  select course_id into v_source_course from public.class_sessions where id=v_source.class_session_id;
  select course_id into v_target_course from public.class_sessions where id=v_target.class_session_id;
  if v_source.customer_id<>v_target.customer_id
     or v_source.class_session_id<>new.source_session_id
     or v_target.class_session_id<>new.target_session_id
     or v_source_course<>v_target_course then
    raise exception 'supersession does not preserve canonical customer/session/course identity';
  end if;
  return new;
end;
$$;

drop trigger if exists registration_supersessions_identity_guard on public.registration_supersessions;
create trigger registration_supersessions_identity_guard
before insert or update on public.registration_supersessions
for each row execute function public.validate_registration_supersession();

create or replace function public.protect_append_only_lifecycle_event()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  raise exception 'participant lifecycle events are append-only; create a correction event';
end;
$$;

drop trigger if exists participant_lifecycle_events_append_only on public.participant_lifecycle_events;
create trigger participant_lifecycle_events_append_only
before update or delete on public.participant_lifecycle_events
for each row execute function public.protect_append_only_lifecycle_event();

create or replace function public.protect_import_source_identity()
returns trigger
language plpgsql
security invoker
set search_path = public, pg_temp
as $$
begin
  if new.batch_id<>old.batch_id
     or new.source_record_id<>old.source_record_id
     or new.entity_type<>old.entity_type
     or new.original_values<>old.original_values then
    raise exception 'import source identity and original values are immutable';
  end if;
  return new;
end;
$$;

drop trigger if exists lifecycle_import_records_source_guard on public.lifecycle_import_records;
create trigger lifecycle_import_records_source_guard
before update on public.lifecycle_import_records
for each row execute function public.protect_import_source_identity();

revoke all on function public.validate_participant_fact_identity() from public, anon, authenticated;
revoke all on function public.validate_registration_supersession() from public, anon, authenticated;
revoke all on function public.protect_append_only_lifecycle_event() from public, anon, authenticated;
revoke all on function public.protect_import_source_identity() from public, anon, authenticated;
