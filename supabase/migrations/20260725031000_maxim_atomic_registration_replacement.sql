begin;

alter table public.maxim_registration_requests
  add column if not exists location_key text,
  add column if not exists superseded_at timestamptz,
  add column if not exists commitment_released_at timestamptz;

alter table public.maxim_employee_profiles
  add column if not exists ecard_detected_at timestamptz;

update public.maxim_employee_profiles
set ecard_detected_at = coalesce(ecard_detected_at, updated_at, now())
where prior_ecard_code is not null;

create unique index if not exists maxim_one_active_requirement
  on public.maxim_registration_requests (employee_profile_id, external_course_id)
  where status = 'requested';

create or replace function public.maxim_replace_registration(
  p_employee_profile_id uuid,
  p_external_session_id text,
  p_external_course_id text,
  p_starts_at timestamptz,
  p_registration_url text,
  p_billing_account text,
  p_location_key text,
  p_replace_request_id uuid default null
) returns public.maxim_registration_requests
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  prior_request public.maxim_registration_requests;
  new_request public.maxim_registration_requests;
begin
  perform pg_advisory_xact_lock(hashtextextended(
    p_employee_profile_id::text || '|' || p_external_course_id, 0
  ));

  select *
    into prior_request
    from public.maxim_registration_requests
   where employee_profile_id = p_employee_profile_id
     and external_course_id = p_external_course_id
     and status = 'requested'
   order by created_at desc
   limit 1
   for update;

  if prior_request.id is not null
     and p_replace_request_id is distinct from prior_request.id then
    raise exception using
      errcode = '23505',
      message = 'duplicate_active_registration';
  end if;

  if prior_request.id is not null then
    update public.maxim_registration_requests
       set status = 'replacing',
           updated_at = now()
     where id = prior_request.id;
  end if;

  insert into public.maxim_registration_requests (
    employee_profile_id,
    external_session_id,
    external_course_id,
    starts_at,
    registration_url,
    billing_account,
    location_key,
    status,
    supersedes_request_id
  ) values (
    p_employee_profile_id,
    p_external_session_id,
    p_external_course_id,
    p_starts_at,
    p_registration_url,
    p_billing_account,
    p_location_key,
    'requested',
    prior_request.id
  )
  returning * into new_request;

  if prior_request.id is not null then
    update public.maxim_registration_requests
       set status = 'superseded',
           superseded_at = now(),
           commitment_released_at = now(),
           updated_at = now()
     where id = prior_request.id;
  end if;

  update public.maxim_employee_profiles
     set workflow_stage = 2,
         status_detail = 'Registered ' || to_char(p_starts_at at time zone 'America/New_York', 'Mon FMDD, YYYY FMHH12:MI AM'),
         scheduled_class_date = p_starts_at,
         current_external_class_id = p_external_session_id,
         current_external_registration_id = new_request.id::text,
         updated_at = now()
   where id = p_employee_profile_id;

  return new_request;
end;
$$;

revoke all on function public.maxim_replace_registration(
  uuid, text, text, timestamptz, text, text, text, uuid
) from public, anon, authenticated;
grant execute on function public.maxim_replace_registration(
  uuid, text, text, timestamptz, text, text, text, uuid
) to service_role;

commit;
