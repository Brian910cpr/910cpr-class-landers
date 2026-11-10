-- Additive shared-checkout prerequisites only. No RPC replacement or activation.
begin;
set local lock_timeout='2s';
set local statement_timeout='15s';
alter table public.landerware_registration_profiles add column if not exists form_schema jsonb not null default '{}';
alter table public.courses add column if not exists registration_profile_key text references public.landerware_registration_profiles(profile_key);
alter table public.landerware_public_orders add column if not exists registration_profile_snapshot jsonb not null default '{}';
alter table public.registrations add column if not exists native_checkout_profile_snapshot jsonb not null default '{}';
commit;
