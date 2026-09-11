create or replace function public.set_historical_session_scope()
returns trigger
language plpgsql
set search_path = 'pg_catalog'
as $$
begin
  if new.source = 'enrollware_history' then
    new.record_scope := 'historical';
    new.visibility := 'unlisted';
    new.registration_status := 'closed';
    new.max_students := greatest(coalesce(new.max_students, new.historical_student_count, 1), 1);
  end if;
  return new;
end;
$$;

drop trigger if exists a_set_historical_session_scope on public.class_sessions;
create trigger a_set_historical_session_scope
before insert or update on public.class_sessions
for each row execute function public.set_historical_session_scope();
