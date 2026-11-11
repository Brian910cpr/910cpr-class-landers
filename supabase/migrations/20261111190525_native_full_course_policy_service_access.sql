-- Explicitly mirror the existing server-only ACL under RLS. This does not
-- enable materialization or grant any browser/customer role access.
begin;
set local lock_timeout='2s';
create policy native_full_course_service_access on public.native_full_course_policy
 for all to service_role using(true) with check(true);
commit;
