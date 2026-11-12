-- PROPOSAL ONLY. Do not run without explicit scoped setup authorization.
-- Requires approved installation of pg_cron and pg_net first. This script does
-- NOT install extensions, enable a schedule, enable customer mail, or return a secret.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
do $$
declare token text; secret_id uuid; job_id bigint; r record;
begin
 if current_setting('landerware.scheduler_setup_approved',true) is distinct from 'true' then raise exception 'scheduler_setup_not_approved';end if;
 if not exists(select 1 from pg_extension where extname='pg_cron') or not exists(select 1 from pg_extension where extname='pg_net') then raise exception 'scheduler_extensions_required';end if;
 if exists(select 1 from landerware_native_scheduler.config where enabled or latched or token_hash is not null or vault_secret_id is not null) then raise exception 'scheduler_already_configured_or_unresolved';end if;
 if exists(select 1 from vault.secrets where name='landerware_native_checkout_scheduler') or exists(select 1 from cron.job where jobname in('landerware-native-confirmation-dispatch','landerware-native-confirmation-observer')) then raise exception 'scheduler_existing_setup_review_required';end if;
 if current_setting('landerware.scheduler_redirect_behavior_reviewed',true) is distinct from 'true' then raise exception 'scheduler_redirect_review_required';end if;
 if current_setting('landerware.scheduler_worker_logging_reviewed',true) is distinct from 'true' then raise exception 'scheduler_worker_logging_review_required';end if;
 perform landerware_native_scheduler.assert_transport_runtime();
 -- Queued pg_net headers necessarily contain the transient credential. Deny
 -- public client access; do not print/read queue headers for proof.
 for r in select unnest(array['anon','authenticated','service_role']) as role_name loop
  if has_table_privilege(r.role_name,'net.http_request_queue','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') or has_table_privilege(r.role_name,'net._http_response','SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') or has_table_privilege(r.role_name,'vault.decrypted_secrets','SELECT') then raise exception 'scheduler_secret_acl_review_required';end if;
 end loop;
 token:=encode(extensions.gen_random_bytes(32),'hex');
 secret_id:=vault.create_secret(token,'landerware_native_checkout_scheduler','Native confirmation fixed callback only');
 update landerware_native_scheduler.config set vault_secret_id=secret_id,token_hash=encode(sha256(convert_to(token,'UTF8')),'hex') where id;
 job_id:=cron.schedule('landerware-native-confirmation-dispatch','* * * * *','select landerware_native_scheduler.dispatch();');
 perform cron.alter_job(job_id,active:=false);
 job_id:=cron.schedule('landerware-native-confirmation-observer','* * * * *','select landerware_native_scheduler.observe();');
 perform cron.alter_job(job_id,active:=false);
end $$;
commit;
