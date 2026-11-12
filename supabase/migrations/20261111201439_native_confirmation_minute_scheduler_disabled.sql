-- Default-off preparation only. No extensions, jobs, credentials or sends.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
create schema if not exists landerware_native_scheduler;
revoke all on schema landerware_native_scheduler from public,anon,authenticated;
grant usage on schema landerware_native_scheduler to service_role;
create table landerware_native_scheduler.config(
 id boolean primary key default true check(id), enabled boolean not null default false,
 token_hash text check(token_hash ~ '^[a-f0-9]{64}$'), vault_secret_id uuid,
 latched boolean not null default false, reason text check(reason ~ '^[a-z0-9_]{1,100}$'),
 last_dispatch_at timestamptz, last_observed_at timestamptz, observation jsonb
);
insert into landerware_native_scheduler.config(id) values(true);
create table landerware_native_scheduler.runs(
 id uuid primary key default gen_random_uuid(), request_id bigint unique,
 created_at timestamptz not null default now(), started_at timestamptz, finished_at timestamptz,
 state text not null default 'queued' check(state in('queued','running','completed','disabled','uncertain','fault')),
 result jsonb
);
create index native_scheduler_unfinished on landerware_native_scheduler.runs(created_at) where finished_at is null;
alter table landerware_native_scheduler.config enable row level security;
alter table landerware_native_scheduler.runs enable row level security;
revoke all on all tables in schema landerware_native_scheduler from public,anon,authenticated;
grant select on all tables in schema landerware_native_scheduler to service_role;
grant update(latched,reason) on landerware_native_scheduler.config to service_role;
grant update(started_at,finished_at,state,result) on landerware_native_scheduler.runs to service_role;

-- Metadata-only proof. Effective privileges include inherited grants. PUBLIC
-- default ACLs are checked separately, including EXECUTE on new functions.
create function landerware_native_scheduler.transport_acl_report()
returns jsonb language sql security invoker set search_path='' as $fn$
 with objects as (
  select 'schema'::text as kind,n.oid,'net'::text as name,n.nspowner as owner,
   coalesce(n.nspacl,acldefault('n',n.nspowner)) as acl
  from pg_namespace n where n.nspname='net'
  union all
  select case when c.relkind='S' then 'sequence' else 'table' end,c.oid,
   format('%I.%I',n.nspname,c.relname),c.relowner,
   coalesce(c.relacl,acldefault(case when c.relkind='S' then 's'::"char" else 'r'::"char" end,c.relowner))
  from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='net' and c.relkind in('r','p','v','m','f','S')
  union all
  select 'function',p.oid,p.oid::regprocedure::text,p.proowner,coalesce(p.proacl,acldefault('f',p.proowner))
  from pg_proc p where p.pronamespace=to_regnamespace('net') or exists(
   select 1 from pg_depend d join pg_extension e on e.oid=d.refobjid
   where d.classid='pg_proc'::regclass and d.objid=p.oid and d.deptype='e' and e.extname='pg_net')
 ), checks as (
  select o.kind,o.name,r.rolname as role,
   case o.kind when 'schema' then has_schema_privilege(r.oid,o.oid,'USAGE,CREATE')
    when 'sequence' then has_sequence_privilege(r.oid,o.oid,'SELECT,UPDATE,USAGE')
    when 'table' then has_table_privilege(r.oid,o.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
    else has_function_privilege(r.oid,o.oid,'EXECUTE') end as allowed
  from objects o cross join pg_roles r
  where r.rolname not in('postgres','supabase_admin','supabase_functions_admin') and
   (r.rolcanlogin or r.rolname in('anon','authenticated','service_role') or
    exists(select 1 from objects x cross join lateral aclexplode(x.acl) a where a.grantee=r.oid))
  union all
  select o.kind,o.name,'PUBLIC',exists(select 1 from aclexplode(o.acl) a where a.grantee=0) from objects o
 ) select jsonb_build_object(
  'safe',exists(select 1 from objects where kind='schema') and not exists(select 1 from checks where allowed)
   and not exists(select 1 from objects where pg_get_userbyid(owner) not in('postgres','supabase_admin','supabase_functions_admin')),
  'trustedRoles',jsonb_build_array('postgres','supabase_admin','supabase_functions_admin'),
  'unreviewedOwners',coalesce((select jsonb_agg(jsonb_build_object('object',name,'owner',pg_get_userbyid(owner))) from objects where pg_get_userbyid(owner) not in('postgres','supabase_admin','supabase_functions_admin')),'[]'::jsonb),
  'violations',coalesce((select jsonb_agg(jsonb_build_object('kind',kind,'object',name,'role',role)) from checks where allowed),'[]'::jsonb),
  'objects',coalesce((select jsonb_agg(jsonb_build_object('kind',kind,'object',name,'owner',pg_get_userbyid(owner))) from objects),'[]'::jsonb)
 );
$fn$;
create function landerware_native_scheduler.assert_transport_acl()
returns void language plpgsql security invoker set search_path='' as $$
begin
 if not coalesce((landerware_native_scheduler.transport_acl_report()->>'safe')::boolean,false) then raise exception 'scheduler_transport_acl_review_required';end if;
end $$;

-- Necessary runtime checks, not a claim about a background worker's complete
-- logging deployment. Activation additionally requires verified worker logging.
create function landerware_native_scheduler.assert_transport_runtime()
returns void language plpgsql security invoker set search_path='' as $$
declare p record;
begin
 perform landerware_native_scheduler.assert_transport_acl();
 select setting,reset_val,pending_restart into p from pg_settings where name='log_min_messages';
 if not found or p.pending_restart or lower(p.setting) like 'debug%' or lower(p.reset_val) like 'debug%' or
  exists(select 1 from pg_db_role_setting s,unnest(s.setconfig) v where lower(v) like 'log_min_messages=debug%') then
  raise exception 'scheduler_transport_logging_review_required';
 end if;
end $$;

create function public.native_checkout_scheduler_begin(p_run_id uuid,p_token_hash text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare c landerware_native_scheduler.config%rowtype; r landerware_native_scheduler.runs%rowtype;
begin
 -- Reject bad credentials without taking the singleton lock. Recheck under
 -- lock to close rotation/disable races after the initial read.
 select * into c from landerware_native_scheduler.config where id;
 if p_token_hash is null or p_token_hash !~ '^[a-f0-9]{64}$' or c.token_hash is null or c.token_hash<>p_token_hash then return jsonb_build_object('authorized',false); end if;
 select * into c from landerware_native_scheduler.config where id for update;
 if c.token_hash is null or c.token_hash<>p_token_hash then return jsonb_build_object('authorized',false);end if;
 if not c.enabled or c.latched then return jsonb_build_object('authorized',true,'disabled',true); end if;
 select * into r from landerware_native_scheduler.runs where id=p_run_id for update;
 if r.id is null or r.request_id is null or r.state<>'queued' or r.created_at<now()-interval '2 minutes' or r.created_at>now() then return jsonb_build_object('authorized',true,'started',false); end if;
 update landerware_native_scheduler.runs set state='running',started_at=now() where id=r.id;
 return jsonb_build_object('authorized',true,'started',true);
end $$;

create function public.native_checkout_scheduler_finish(p_run_id uuid,p_result jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare r landerware_native_scheduler.runs%rowtype; k text; n integer; total integer:=0;
begin
 if p_result is null or jsonb_typeof(p_result)<>'object' or
  (select count(*) from jsonb_object_keys(p_result))<>6 or
  not(p_result ?& array['outcome','code','claimed','accepted','rejected','ambiguous']) or
  coalesce(p_result->>'outcome','') not in('completed','disabled','uncertain','fault') or
  (p_result->>'code' is not null and p_result->>'code' !~ '^[a-z0-9_]{1,100}$') then raise exception 'invalid_scheduler_result'; end if;
 foreach k in array array['claimed','accepted','rejected','ambiguous'] loop
  if jsonb_typeof(p_result->k)<>'number' or p_result->>k !~ '^[0-9]{1,2}$' then raise exception 'invalid_scheduler_result'; end if;
  n:=(p_result->>k)::int;if n>10 then raise exception 'invalid_scheduler_result';end if;
  if k<>'claimed' then total:=total+n;end if;
 end loop;
 if total>(p_result->>'claimed')::int or
  (p_result->>'outcome'='completed' and (total<>(p_result->>'claimed')::int or (p_result->>'ambiguous')::int<>0 or p_result->>'code' is not null)) or
  (p_result->>'outcome'='disabled' and ((p_result->>'claimed')::int<>0 or p_result->>'code' is not null)) then raise exception 'invalid_scheduler_result';end if;
 perform 1 from landerware_native_scheduler.config where id for update;
 select * into r from landerware_native_scheduler.runs where id=p_run_id for update;
 if r.finished_at is not null and r.result=p_result then return jsonb_build_object('replay',true);end if;
 if r.id is null or r.state<>'running' or r.finished_at is not null then raise exception 'invalid_scheduler_run';end if;
 update landerware_native_scheduler.runs set state=p_result->>'outcome',result=p_result,finished_at=now() where id=r.id;
 if p_result->>'outcome' in('uncertain','fault') then
  update landerware_native_scheduler.config set latched=true,reason=coalesce(p_result->>'code','callback_unknown') where id;
 end if;
 return jsonb_build_object('settled',true);
end $$;

-- Read-only status does not refresh queue polls or observer evidence.
create function public.native_checkout_scheduler_status()
returns jsonb language plpgsql security invoker set search_path='' as $$
declare c landerware_native_scheduler.config%rowtype; last_finish timestamptz; h jsonb; fresh boolean; observed boolean;
begin
 select * into c from landerware_native_scheduler.config where id;
 select max(finished_at) into last_finish from landerware_native_scheduler.runs where state in('completed','disabled');
 h:=public.native_checkout_confirmation_health();
 fresh:=coalesce(last_finish>now()-interval '3 minutes' and last_finish<=now(),false);
 observed:=coalesce(c.last_observed_at>now()-interval '3 minutes' and c.last_observed_at<=now(),false);
 return jsonb_build_object('enabled',c.enabled,'latched',c.latched,'reason',c.reason,'lastCompletedAt',last_finish,
  'lastObservedAt',c.last_observed_at,'callbackFresh',fresh,'observerFresh',observed,'queue',h,
  'healthy',c.enabled and not c.latched and fresh and observed and coalesce((h->>'healthy')::boolean,false),
  'actualDeliveryConfirmed',false);
end $$;

-- Called only as the privileged cron owner. No arbitrary URL, body, token or SQL arguments.
create function landerware_native_scheduler.reconcile()
returns void language plpgsql security invoker set search_path='' as $$
declare r landerware_native_scheduler.runs%rowtype; response record; v_reason text;
begin
 perform 1 from landerware_native_scheduler.config where id for update;
 select * into r from landerware_native_scheduler.runs where finished_at is null order by created_at limit 1;
 if r.id is not null then
  select status_code,timed_out,error_msg is not null as errored into response from net._http_response where id=r.request_id;
  if found and (response.timed_out or response.errored or response.status_code is distinct from 200) then
   v_reason:=case when response.status_code in(401,403) then 'callback_auth_denied' else 'callback_transport_unknown' end;
  elsif r.created_at<now()-interval '2 minutes' then v_reason:='callback_completion_unknown';end if;
  if v_reason is not null then update landerware_native_scheduler.config set latched=true,reason=v_reason where id and not latched;end if;
 end if;
end $$;

-- This observer is a separate scheduled job; dispatch never refreshes its heartbeat.
create function landerware_native_scheduler.observe()
returns jsonb language plpgsql security invoker set search_path='' as $$
declare h jsonb;
begin
 perform landerware_native_scheduler.reconcile();
 update landerware_native_scheduler.config set last_observed_at=now() where id;
 h:=public.native_checkout_scheduler_status();
 update landerware_native_scheduler.config set observation=h where id;
 return h;
end $$;

create function landerware_native_scheduler.dispatch()
returns jsonb language plpgsql security invoker set search_path='' as $$
declare c landerware_native_scheduler.config%rowtype; run_id uuid; v_request_id bigint; token text;
begin
 select * into c from landerware_native_scheduler.config where id for update;
 if not c.enabled or c.latched then return jsonb_build_object('dispatched',false,'disabled',true);end if;
 -- An extension update can reintroduce grants. Fail closed before touching Vault.
 begin perform landerware_native_scheduler.assert_transport_runtime();exception when others then
  update landerware_native_scheduler.config set latched=true,reason='scheduler_transport_security_changed' where id;
  return jsonb_build_object('dispatched',false);end;
 perform landerware_native_scheduler.reconcile();
 select * into c from landerware_native_scheduler.config where id;
 if c.latched or exists(select 1 from landerware_native_scheduler.runs where finished_at is null) or c.last_dispatch_at>now()-interval '45 seconds' then return jsonb_build_object('dispatched',false);end if;
 select decrypted_secret into token from vault.decrypted_secrets where id=c.vault_secret_id;
 if token is null or token !~ '^[a-f0-9]{64}$' or encode(sha256(convert_to(token,'UTF8')),'hex') is distinct from c.token_hash then
  update landerware_native_scheduler.config set latched=true,reason='scheduler_credential_missing' where id;
  return jsonb_build_object('dispatched',false);
 end if;
 insert into landerware_native_scheduler.runs default values returning id into run_id;
 v_request_id:=net.http_post(
  url:='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/native-checkout-confirmations/scheduled',
  body:='{}'::jsonb,params:='{}'::jsonb,
  headers:=jsonb_build_object('Content-Type','application/json','Authorization','Bearer '||token,'x-native-scheduler-run',run_id::text),
  timeout_milliseconds:=110000);
 if v_request_id is null then raise exception 'scheduler_request_missing';end if;
 update landerware_native_scheduler.runs set request_id=v_request_id where id=run_id;
 update landerware_native_scheduler.config set last_dispatch_at=now() where id;
 return jsonb_build_object('dispatched',true);
end $$;
revoke all on all functions in schema landerware_native_scheduler from public,anon,authenticated,service_role;
revoke all on function public.native_checkout_scheduler_begin(uuid,text),public.native_checkout_scheduler_finish(uuid,jsonb),public.native_checkout_scheduler_status() from public,anon,authenticated;
grant execute on function public.native_checkout_scheduler_begin(uuid,text),public.native_checkout_scheduler_finish(uuid,jsonb),public.native_checkout_scheduler_status() to service_role;
commit;
