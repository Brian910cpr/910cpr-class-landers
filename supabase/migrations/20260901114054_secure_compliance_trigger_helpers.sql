-- Trigger functions execute through their triggers and do not need to be
-- callable as public RPCs. Close those indirect compliance mutation surfaces.
revoke all privileges on function public.trg_seed_session_compliance()
  from public, anon, authenticated;
alter function public.trg_seed_session_compliance()
  set search_path = pg_catalog;

revoke all privileges on function public.release_archive_when_compliant()
  from public, anon, authenticated;
alter function public.release_archive_when_compliant()
  set search_path = pg_catalog;
