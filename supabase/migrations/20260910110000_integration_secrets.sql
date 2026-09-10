create table if not exists public.landerware_integration_secrets (
  secret_key text primary key,
  secret_value text not null,
  updated_at timestamptz not null default now()
);

alter table public.landerware_integration_secrets enable row level security;
revoke all on table public.landerware_integration_secrets from anon, authenticated;
grant all on table public.landerware_integration_secrets to service_role;

comment on table public.landerware_integration_secrets is
  'Server-only integration material. Never expose through public APIs or client credentials.';
