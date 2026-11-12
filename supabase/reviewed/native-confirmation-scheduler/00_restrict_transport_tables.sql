-- PROPOSAL ONLY. Security-sensitive ACL changes require concrete approval.
-- No ownership changes or new grants. Review existing consumers and actual
-- pg_proc owners/prosecdef first; upstream v0.20.4 wrappers are INVOKER.
-- Schema, sequences and executable functions are part of the boundary too.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
do $$declare obj record;begin
 if current_setting('landerware.scheduler_secret_acl_approved',true) is distinct from 'true' then raise exception 'scheduler_acl_change_not_approved';end if;
 -- Refuse partial revocation from a caller that does not own/cannot administer
 -- every affected object. Function/table owners retain owned privileges.
 for obj in
  select nspowner as owner from pg_namespace where nspname='net'
  union select c.relowner from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='net' and c.relkind in('r','p','v','m','f','S')
  union select p.proowner from pg_proc p where p.pronamespace='net'::regnamespace or exists(select 1 from pg_depend d join pg_extension e on e.oid=d.refobjid where d.classid='pg_proc'::regclass and d.objid=p.oid and d.deptype='e' and e.extname='pg_net')
 loop
  if not exists(select 1 from pg_roles where rolname=current_user and rolsuper) and not pg_has_role(current_user,obj.owner,'USAGE') then raise exception 'scheduler_acl_owner_review_required';end if;
 end loop;
end $$;
revoke all on schema net from public,anon,authenticated,service_role;
revoke all on all tables in schema net from public,anon,authenticated,service_role;
revoke all on all sequences in schema net from public,anon,authenticated,service_role;
revoke all on all functions in schema net from public,anon,authenticated,service_role;
-- Include any extension-owned function outside net without revoking access to
-- an unrelated shared schema (such as extensions).
do $$declare f record;begin
 for f in select p.oid::regprocedure as signature from pg_proc p join pg_depend d on d.classid='pg_proc'::regclass and d.objid=p.oid and d.deptype='e' join pg_extension e on e.oid=d.refobjid where e.extname='pg_net' and p.pronamespace<>'net'::regnamespace loop
  execute format('revoke all on function %s from public,anon,authenticated,service_role',f.signature);
 end loop;
 perform landerware_native_scheduler.assert_transport_acl();
end $$;
commit;
