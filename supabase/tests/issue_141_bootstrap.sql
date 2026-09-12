-- Minimal repository-side prerequisites for exercising the checked-in
-- LanderWare durable-record migration in disposable vanilla PostgreSQL.
-- Production migrations are applied unchanged after this bootstrap.
create role anon nologin;
create role authenticated nologin;
create role service_role nologin;

create table public.maxim_employee_profiles (
  id uuid primary key default gen_random_uuid()
);

create table public.maxim_registration_requests (
  id uuid primary key default gen_random_uuid()
);
