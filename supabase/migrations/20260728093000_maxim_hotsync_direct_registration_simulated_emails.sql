begin;

alter table public.maxim_registration_requests
  add column if not exists registration_source text not null default 'maxim_portal_hot_sync',
  add column if not exists source_booking_url text,
  add column if not exists class_date date,
  add column if not exists start_time text,
  add column if not exists timezone text not null default 'America/New_York',
  add column if not exists simulated_email_payloads jsonb not null default '[]'::jsonb,
  add column if not exists simulated_email_created_at timestamptz;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'maxim_registration_requests_registration_source_check'
  ) then
    alter table public.maxim_registration_requests
      add constraint maxim_registration_requests_registration_source_check
      check (registration_source in ('maxim_portal_hot_sync')) not valid;
  end if;

  if not exists (
    select 1
    from pg_constraint
    where conname = 'maxim_registration_requests_timezone_check'
  ) then
    alter table public.maxim_registration_requests
      add constraint maxim_registration_requests_timezone_check
      check (timezone = 'America/New_York') not valid;
  end if;

  if not exists (
    select 1
    from pg_constraint
    where conname = 'maxim_registration_requests_start_time_check'
  ) then
    alter table public.maxim_registration_requests
      add constraint maxim_registration_requests_start_time_check
      check (start_time is null or start_time ~ '^\d{2}:\d{2}$') not valid;
  end if;
end $$;

commit;
