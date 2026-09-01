create or replace function public.reject_location_status_event_mutation()
returns trigger
language plpgsql
set search_path = 'public', 'pg_temp'
as $function$
begin
  raise exception 'location scheduling-status audit events are append-only';
end;
$function$;

revoke all on function public.reject_location_status_event_mutation()
  from public, anon, authenticated;

create trigger location_status_events_reject_update_delete_trg
before update or delete on public.location_scheduling_status_events
for each row execute function public.reject_location_status_event_mutation();

create trigger location_status_events_reject_truncate_trg
before truncate on public.location_scheduling_status_events
for each statement execute function public.reject_location_status_event_mutation();

revoke update, delete, truncate
  on table public.location_scheduling_status_events
  from service_role, anon, authenticated;
