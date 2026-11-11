-- Metadata-only read-back. No request headers, secrets or transport bodies.
select landerware_native_scheduler.transport_acl_report();
select landerware_native_scheduler.assert_transport_acl();
select n.nspname,p.proname,pg_get_function_identity_arguments(p.oid) as arguments,
 pg_get_userbyid(p.proowner) as owner,p.prosecdef as security_definer,p.proacl
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='net' or exists(select 1 from pg_depend d join pg_extension e on e.oid=d.refobjid where d.classid='pg_proc'::regclass and d.objid=p.oid and d.deptype='e' and e.extname='pg_net');
select n.nspname,c.relname,c.relkind,pg_get_userbyid(c.relowner) as owner,c.relacl
from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='net';
-- Review every explicit custom/internal grantee and owner. The approved cron
-- owner and actual extension/worker owners must retain owned privileges.

-- Current client settings are not proof of the background worker's logging.
select name,setting,reset_val,source,pending_restart from pg_settings where name='log_min_messages';
select setdatabase,setrole,v as log_min_messages_override from pg_db_role_setting s,unnest(s.setconfig) v where lower(v) like 'log_min_messages=%';
