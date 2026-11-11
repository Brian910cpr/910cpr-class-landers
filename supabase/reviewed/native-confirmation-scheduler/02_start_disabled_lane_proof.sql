-- PROPOSAL ONLY. Explicit approval required; never execute as part of migration.
-- This starts real minute callbacks while customer delivery is still disabled.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
do $$
declare j record;
begin
 if current_setting('landerware.scheduler_activation_approved',true) is distinct from 'true' then raise exception 'scheduler_activation_not_approved';end if;
 if not exists(select 1 from public.landerware_checkout_delivery_config where id and not enabled) then raise exception 'customer_delivery_must_stay_disabled';end if;
 if not exists(select 1 from landerware_native_scheduler.config where id and not enabled and not latched and token_hash is not null and vault_secret_id is not null) then raise exception 'scheduler_not_ready';end if;
 if (select count(*) from cron.job where jobname in('landerware-native-confirmation-dispatch','landerware-native-confirmation-observer') and not active and schedule='* * * * *' and username=current_user and database=current_database())<>2 then raise exception 'scheduler_jobs_not_ready';end if;
 if exists(select 1 from cron.job where jobname='landerware-native-confirmation-dispatch' and command is distinct from 'select landerware_native_scheduler.dispatch();') or exists(select 1 from cron.job where jobname='landerware-native-confirmation-observer' and command is distinct from 'select landerware_native_scheduler.observe();') then raise exception 'scheduler_job_command_mismatch';end if;
 if current_setting('landerware.scheduler_redirect_behavior_reviewed',true) is distinct from 'true' then raise exception 'scheduler_redirect_review_required';end if;
 if current_setting('landerware.scheduler_worker_logging_reviewed',true) is distinct from 'true' then raise exception 'scheduler_worker_logging_review_required';end if;
 perform landerware_native_scheduler.assert_transport_runtime();
 if exists(select 1 from landerware_native_scheduler.runs where finished_at is null) then raise exception 'scheduler_inflight_review_required';end if;
 update landerware_native_scheduler.config set enabled=true where id;
 for j in select jobid from cron.job where jobname in('landerware-native-confirmation-dispatch','landerware-native-confirmation-observer') loop perform cron.alter_job(j.jobid,active:=true);end loop;
end $$;
commit;
