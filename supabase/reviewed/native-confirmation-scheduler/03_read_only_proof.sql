-- Metadata/counts only. Never select Vault plaintext or pg_net headers/body.
select public.native_checkout_scheduler_status();
select id,created_at,started_at,finished_at,state,result,request_id
from landerware_native_scheduler.runs order by created_at desc limit 15;
select jobname,schedule,active,username,database from cron.job
where jobname in('landerware-native-confirmation-dispatch','landerware-native-confirmation-observer');
select j.jobname,d.status,d.start_time,d.end_time
from cron.job_run_details d join cron.job j using(jobid)
where j.jobname in('landerware-native-confirmation-dispatch','landerware-native-confirmation-observer')
order by d.start_time desc limit 30;
select r.id,p.status_code,p.timed_out,(p.error_msg is not null) as transport_error,p.created
from landerware_native_scheduler.runs r left join net._http_response p on p.id=r.request_id
order by r.created_at desc limit 15;
-- Verify at least ten consecutive callback completions ~60s apart, no >180s gap,
-- both jobs advancing, no uncertainty, zero claimed while sender is disabled.
-- This is callback/cadence proof only, never a claim of customer email delivery.
