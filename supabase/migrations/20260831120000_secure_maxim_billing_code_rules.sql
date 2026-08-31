-- Restrict MAXIM billing-code rules to trusted server-side callers.
-- Edge Functions use the service role, which bypasses RLS; no browser policy is required.
alter table public.maxim_billing_code_rules enable row level security;

revoke all on table public.maxim_billing_code_rules from anon, authenticated;
grant all on table public.maxim_billing_code_rules to service_role;

