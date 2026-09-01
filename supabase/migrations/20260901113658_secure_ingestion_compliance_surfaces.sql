-- These internal ingestion and compliance relations live in the exposed
-- public schema, but are consumed only by trusted backend/service-role code.
-- Keep the authority boundary fail-closed for browser roles: RLS is defense
-- in depth and direct privileges are removed rather than paired with broad
-- policies.

alter table public.ingest_jobs enable row level security;
alter table public.ingest_facts enable row level security;
alter table public.ingest_review_queue enable row level security;
alter table public.compliance_requirement_sources enable row level security;
alter table public.compliance_requirements enable row level security;
alter table public.session_compliance_requirements enable row level security;
alter table public.historical_registration_import_rows enable row level security;

revoke all privileges on table public.ingest_jobs from anon, authenticated;
revoke all privileges on table public.ingest_facts from anon, authenticated;
revoke all privileges on table public.ingest_review_queue from anon, authenticated;
revoke all privileges on table public.compliance_requirement_sources from anon, authenticated;
revoke all privileges on table public.compliance_requirements from anon, authenticated;
revoke all privileges on table public.session_compliance_requirements from anon, authenticated;
revoke all privileges on table public.historical_registration_import_rows from anon, authenticated;

-- Both views are internal projections over the protected relations. Views
-- otherwise retain their own browser-facing grants independently of the
-- underlying table grants/RLS.
revoke all privileges on table public.ingest_operational_dashboard from anon, authenticated;
revoke all privileges on table public.session_compliance_summary from anon, authenticated;

-- Historical staging is a privileged backend operation. SECURITY DEFINER is
-- retained because the service worker intentionally writes the staging table,
-- but execution is service-only and name resolution is restricted to trusted
-- pg_catalog objects; all application relations in the body are schema-qualified.
revoke all privileges on function public.import_historical_registration_batch(jsonb)
  from public, anon, authenticated;
grant execute on function public.import_historical_registration_batch(jsonb)
  to service_role;
alter function public.import_historical_registration_batch(jsonb)
  set search_path = pg_catalog;

-- This helper is another SECURITY DEFINER mutation path into one of the seven
-- protected tables, so it must follow the same service-only boundary.
revoke all privileges on function public.populate_session_compliance_requirements(uuid)
  from public, anon, authenticated;
grant execute on function public.populate_session_compliance_requirements(uuid)
  to service_role;
alter function public.populate_session_compliance_requirements(uuid)
  set search_path = pg_catalog;
