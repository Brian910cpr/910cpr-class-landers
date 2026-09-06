create table if not exists public.landerware_group_requests (
  id uuid primary key default gen_random_uuid(),
  idempotency_key text not null unique,
  organization_id uuid references public.landerware_organizations(id),
  coordinator_person_id uuid references public.landerware_people(id),
  requested_session_id uuid references public.landerware_sessions(id),
  organization_type text not null,
  recommended_program text not null,
  selected_program text not null,
  selected_modules jsonb not null default '[]'::jsonb,
  request_details jsonb not null default '{}'::jsonb,
  availability_evidence jsonb,
  reservation_mode text not null default 'requires_confirmation' check (reservation_mode = 'requires_confirmation'),
  status text not null default 'requested' check (status in ('requested','reviewing','confirmed','declined','cancelled')),
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
alter table public.landerware_group_requests enable row level security;
revoke all on public.landerware_group_requests from anon, authenticated;
create index if not exists landerware_group_requests_status_idx on public.landerware_group_requests(status, created_at desc);
comment on table public.landerware_group_requests is 'Durable private group request linked to LanderWare organization, coordinator, and requested session records. Service role only.';
