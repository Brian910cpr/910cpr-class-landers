-- Private capability links and revocable browser sessions. Only hashes are stored.
create table if not exists public.owner_access_grants (
  id uuid primary key default gen_random_uuid(),
  owner_email text not null,
  owner_name text not null,
  token_sha256 text not null unique check (token_sha256 ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  revoked_at timestamptz,
  label text not null
);
create table if not exists public.owner_browser_sessions (
  id uuid primary key default gen_random_uuid(),
  grant_id uuid not null references public.owner_access_grants(id),
  token_sha256 text not null unique check (token_sha256 ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default now(),
  expires_at timestamptz not null,
  revoked_at timestamptz
);
create index if not exists owner_browser_sessions_grant_id_idx on public.owner_browser_sessions(grant_id);
alter table public.owner_access_grants enable row level security;
alter table public.owner_browser_sessions enable row level security;
revoke all on public.owner_access_grants, public.owner_browser_sessions from public, anon, authenticated;
grant select, insert, update, delete on public.owner_access_grants, public.owner_browser_sessions to service_role;
