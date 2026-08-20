begin;

create or replace function public.maxim_find_or_create_employee(
  p_source_ref text,
  p_first_name text,
  p_last_name text,
  p_email text,
  p_phone text,
  p_billing_account text,
  p_required_training text
) returns uuid
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  existing_profile_id uuid;
  new_customer_id uuid;
  new_profile_id uuid;
begin
  if nullif(btrim(p_source_ref), '') is null
     or nullif(btrim(p_first_name), '') is null
     or nullif(btrim(p_last_name), '') is null then
    raise exception using errcode = '22023', message = 'employee_identity_required';
  end if;

  select id into existing_profile_id
    from public.maxim_employee_profiles
   where source_ref = btrim(p_source_ref)
   limit 1;

  if existing_profile_id is not null then
    return existing_profile_id;
  end if;

  begin
    insert into public.customers (first_name, last_name, email, phone)
    values (
      btrim(p_first_name),
      btrim(p_last_name),
      nullif(btrim(p_email), ''),
      nullif(btrim(p_phone), '')
    )
    returning id into new_customer_id;

    insert into public.maxim_employee_profiles (
      customer_id,
      source_ref,
      billing_account,
      required_training,
      workflow_stage,
      status_detail,
      active
    ) values (
      new_customer_id,
      btrim(p_source_ref),
      btrim(p_billing_account),
      btrim(p_required_training),
      0,
      'Created during Maxim portal registration',
      true
    )
    returning id into new_profile_id;

    return new_profile_id;
  exception when unique_violation then
    select id into existing_profile_id
      from public.maxim_employee_profiles
     where source_ref = btrim(p_source_ref)
     limit 1;
    if existing_profile_id is null then
      raise;
    end if;
    return existing_profile_id;
  end;
end;
$$;

revoke all on function public.maxim_find_or_create_employee(
  text, text, text, text, text, text, text
) from public, anon, authenticated;
grant execute on function public.maxim_find_or_create_employee(
  text, text, text, text, text, text, text
) to service_role;

commit;
