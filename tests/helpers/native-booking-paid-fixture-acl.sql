-- DISPOSABLE LOCAL FIXTURE ONLY; never deploy this file.
-- Matches the measured baseline for the existing native payment path.
-- Measurement provenance is retained separately in the private release evidence.
-- All named tables already grant service_role table-wide SELECT/INSERT/UPDATE
-- in hosted postgres-owned ACLs. This explicit subset models only accesses used
-- by native_checkout_record_payment/finalize_order/record_received.
-- No default grants, GRANT ALL, public/anonymous grants or SECURITY DEFINER.
-- Existing setup supplies orders/students/class/courses/location/read ACLs.
grant select on public.product_inventory_units to service_role;
grant update(public_order_payment_observed,updated_at,reserved_for_registration_id,public_order_hold_expires_at)
 on public.product_inventory_units to service_role;
grant insert(first_name,last_name,email,phone),update(id) on public.customers to service_role;
grant insert(customer_id,class_session_id,status,registration_source,optional_survey),
 update(native_checkout_profile_snapshot) on public.registrations to service_role;
grant insert(template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key),
 select(idempotency_key) on public.landerware_messages to service_role;
-- Conditional received-upload branch; hosted metadata confirms these rights.
grant select,insert on public.registration_requirements to service_role;
grant update(provenance,updated_at) on public.registration_requirements to service_role;
-- Match hosted RLS on tables omitted by the prior admission fixture.
alter table public.customers enable row level security;
alter table public.product_inventory_units enable row level security;
alter table public.landerware_messages enable row level security;
alter table public.registration_requirements enable row level security;
