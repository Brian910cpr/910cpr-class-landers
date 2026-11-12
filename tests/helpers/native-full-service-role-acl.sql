-- DISPOSABLE LOCAL TEST ONLY. Measured hosted baseline, minimum used privileges.
-- Existing hosted grants were inspected read-only on 2026-11-11. Service role
-- has BYPASSRLS and these rights (plus other rights omitted here).
-- This fixture is NOT a proposal for new production grants.
-- The schema-only baseline omits canonical table ACLs. Never deploy this fixture.
grant select on public.courses,public.people,public.locations,public.instructor_qualifications,
 public.registration_reschedule_blocks,public.landerware_registration_catalog,
 public.registrations,public.landerware_public_orders,public.landerware_public_order_students to service_role;
grant select,insert,update on public.class_sessions,public.landerware_sessions to service_role;
grant select,update on public.landerware_public_session_inventory to service_role;
-- Existing materializer takes SHARE table locks; PostgreSQL requires UPDATE,
-- DELETE or TRUNCATE privilege even though these dependencies are not mutated.
grant update on public.courses,public.people,public.locations,public.instructor_qualifications to service_role;

-- Mirror the measured RLS/BYPASSRLS baseline, without superuser execution.
alter role service_role bypassrls;
alter table public.courses enable row level security;
alter table public.people enable row level security;
alter table public.locations enable row level security;
alter table public.instructor_qualifications enable row level security;
alter table public.registration_reschedule_blocks enable row level security;
alter table public.landerware_registration_catalog enable row level security;
alter table public.registrations enable row level security;
alter table public.landerware_public_orders enable row level security;
alter table public.landerware_public_order_students enable row level security;
alter table public.class_sessions enable row level security;
alter table public.landerware_sessions enable row level security;
alter table public.landerware_public_session_inventory enable row level security;
