-- The Dockmaster corrects a finalized manifest in ink: the prior entry remains visible in the harbor log.

alter table public.nhcso_students
  add column if not exists score_or_certificate text;

alter table public.nhcso_classes
  add column if not exists finalized_at timestamptz;

create table if not exists public.nhcso_finalized_corrections (
  id uuid primary key default gen_random_uuid(),
  class_number text not null references public.nhcso_classes(class_number),
  student_id uuid not null references public.nhcso_students(id),
  correction_type text not null check (correction_type = 'identity'),
  before_value jsonb not null,
  after_value jsonb not null,
  warning_accepted boolean not null check (warning_accepted),
  created_at timestamptz not null default now()
);

alter table public.nhcso_finalized_corrections enable row level security;
revoke all on table public.nhcso_finalized_corrections from anon, authenticated;
grant all on table public.nhcso_finalized_corrections to service_role;

create or replace function public.guard_finalized_nhcso_student()
returns trigger language plpgsql set search_path = public, pg_temp as $$
declare class_status text;
begin
  select status into class_status from public.nhcso_classes where class_number = coalesce(new.class_number, old.class_number);
  if class_status <> 'finalized' then return coalesce(new, old); end if;
  if tg_op = 'UPDATE'
     and current_setting('app.nhcso_finalized_identity_correction', true) = 'allowed'
     and (to_jsonb(new) - array['name','email','updated_at']) = (to_jsonb(old) - array['name','email','updated_at']) then
    return new;
  end if;
  raise exception 'Finalized participant records are locked and cannot be %', lower(tg_op);
end $$;

drop trigger if exists guard_finalized_nhcso_student on public.nhcso_students;
create trigger guard_finalized_nhcso_student
before insert or update or delete on public.nhcso_students
for each row execute function public.guard_finalized_nhcso_student();

create or replace function public.correct_nhcso_finalized_participant(
  p_class_number text, p_student_key text, p_name text, p_email text, p_warning_accepted boolean
) returns jsonb language plpgsql security invoker set search_path = public, pg_temp as $$
declare class_status text; existing public.nhcso_students%rowtype; corrected public.nhcso_students%rowtype;
begin
  if not coalesce(p_warning_accepted, false) then raise exception 'Credential correction warning acceptance is required'; end if;
  select status into class_status from public.nhcso_classes where class_number = p_class_number for update;
  if class_status is distinct from 'finalized' then raise exception 'This correction route is only for finalized classes'; end if;
  select * into existing from public.nhcso_students where class_number = p_class_number and student_key = p_student_key for update;
  if existing.id is null then raise exception 'Participant not found'; end if;
  if nullif(trim(p_name), '') is null then raise exception 'Participant name is required'; end if;
  perform set_config('app.nhcso_finalized_identity_correction', 'allowed', true);
  update public.nhcso_students set name = trim(p_name), email = nullif(lower(trim(p_email)), ''), updated_at = now()
    where id = existing.id returning * into corrected;
  insert into public.nhcso_finalized_corrections(class_number, student_id, correction_type, before_value, after_value, warning_accepted)
    values (p_class_number, existing.id, 'identity', jsonb_build_object('name', existing.name, 'email', existing.email), jsonb_build_object('name', corrected.name, 'email', corrected.email), true);
  return to_jsonb(corrected);
end $$;

revoke all on function public.correct_nhcso_finalized_participant(text,text,text,text,boolean) from public, anon, authenticated;
grant execute on function public.correct_nhcso_finalized_participant(text,text,text,text,boolean) to service_role;
