-- DISPOSABLE LOCAL ONLY. Minimum privileges measured in hosted metadata on
-- 2026-11-12; metadata evidence is retained in the private local proof package.
-- No hosted grants are proposed. No grant-on-error or default ACL modifications.
alter role service_role nosuperuser bypassrls;
grant usage on schema storage to service_role;
grant select on public.registration_orders,public.registrations,public.customers,
 public.class_sessions,public.courses,public.locations,public.people,storage.buckets to service_role;
grant update(id) on public.registrations to service_role;
grant update(status,stripe_checkout_session_id,stripe_payment_intent_id,paid_at,updated_at,skills_payment_received_at,skills_payment_review_reason) on public.registration_orders to service_role;
alter table public.registration_orders enable row level security;
alter table public.registrations enable row level security;
