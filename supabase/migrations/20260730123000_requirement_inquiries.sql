create table if not exists public.requirement_inquiries (
  id uuid primary key default gen_random_uuid(),
  name text,
  email text,
  phone text,
  requirement_text text not null,
  selected_course jsonb not null default '{}'::jsonb,
  page_title text not null,
  page_url text not null,
  submitted_at timestamptz not null,
  client_inquiry_id text,
  prior_inquiry_id text,
  registration_id text,
  ip_hash text not null,
  user_agent text,
  delivery_status text not null default 'pending'
    check (delivery_status in ('pending', 'sent', 'failed', 'configuration_error')),
  delivered_at timestamptz,
  provider_message_id text,
  created_at timestamptz not null default now()
);

alter table public.requirement_inquiries enable row level security;

revoke all on table public.requirement_inquiries from anon, authenticated;

create index if not exists requirement_inquiries_ip_created_idx
  on public.requirement_inquiries (ip_hash, created_at desc);

create index if not exists requirement_inquiries_registration_idx
  on public.requirement_inquiries (registration_id)
  where registration_id is not null;

comment on table public.requirement_inquiries is
  'Private employer/school requirement submissions. Access is limited to server-side service-role operations.';
