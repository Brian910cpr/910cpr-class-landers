import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
const sql=readFileSync(new URL('../supabase/migrations/20261111201439_native_confirmation_minute_scheduler_disabled.sql',import.meta.url),'utf8');
const hash='b'.repeat(64),token='a'.repeat(64),id='11111111-1111-4111-8111-111111111111';
const good={outcome:'completed',code:null,claimed:0,accepted:0,rejected:0,ambiguous:0};
async function fixture(fn){const db=new PGlite();try{await db.exec(`create role anon;create role authenticated;create role service_role bypassrls;create schema net;create schema vault;
 create table net._http_response(id bigint,status_code int,timed_out boolean,error_msg text);
 create table vault.decrypted_secrets(id uuid,decrypted_secret text);
 create table net.captured(id bigint generated always as identity,url text,body jsonb,params jsonb,headers jsonb,timeout_milliseconds int);
 create function net.http_post(url text,body jsonb,params jsonb,headers jsonb,timeout_milliseconds int) returns bigint language plpgsql as $$declare n bigint;begin insert into net.captured(url,body,params,headers,timeout_milliseconds) values($1,$2,$3,$4,$5) returning id into n;return n;end$$;
 create function public.native_checkout_confirmation_health() returns jsonb language sql as $$select '{"healthy":true}'::jsonb$$;`);await db.exec(sql);await fn(db);}finally{await db.close();}}
async function q(db,sql,args=[]){return (await db.query(sql,args)).rows;}
async function arm(db){await db.exec("set landerware.scheduler_secret_acl_approved='true'");await db.exec(readFileSync(new URL('../supabase/reviewed/native-confirmation-scheduler/00_restrict_transport_tables.sql',import.meta.url),'utf8'));await db.query(`insert into vault.decrypted_secrets values($1,$2)`,[id,token]);await db.query(`update landerware_native_scheduler.config set enabled=true,token_hash=encode(sha256(convert_to($1,'UTF8')),'hex'),vault_secret_id=$2`,[token,id]);}
async function dispatch(db){await db.query('select landerware_native_scheduler.dispatch()');return (await q(db,'select * from landerware_native_scheduler.runs'))[0];}
async function begin(db,r){return (await q(db,`select public.native_checkout_scheduler_begin($1,encode(sha256(convert_to($2,'UTF8')),'hex')) as r`,[r.id,token]))[0].r;}
async function finish(db,r,result=good){return (await q(db,'select public.native_checkout_scheduler_finish($1,$2) as r',[r.id,result]))[0].r;}
test('default-off installation creates no jobs, tokens, queued request or privileged definer',()=>fixture(async db=>{assert.equal((await q(db,'select landerware_native_scheduler.dispatch() as r'))[0].r.disabled,true);assert.equal((await q(db,'select count(*)::int n from net.captured'))[0].n,0);assert.equal((await q(db,"select count(*)::int n from pg_proc p join pg_namespace n on n.oid=p.pronamespace where (n.nspname='landerware_native_scheduler' or p.proname like 'native_checkout_scheduler_%') and p.prosecdef"))[0].n,0);}));
test('fixed destination, empty JSON and generated run, duplicate dispatch suppressed',()=>fixture(async db=>{await arm(db);await dispatch(db);await db.query('select landerware_native_scheduler.dispatch()');const rows=await q(db,'select url,body,params,timeout_milliseconds,headers ? \'Authorization\' as token from net.captured');assert.equal(rows.length,1);assert.equal(rows[0].url,'https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/native-checkout-confirmations/scheduled');assert.deepEqual(rows[0].body,{});assert.deepEqual(rows[0].params,{});assert.equal(rows[0].timeout_milliseconds,110000);assert.equal(rows[0].token,true);}));
test('anonymous roles cannot call RPC or read scheduler hash; service cannot enable or dispatch',()=>fixture(async db=>{for(const role of ['anon','authenticated']){await db.exec(`set role ${role}`);await assert.rejects(db.query('select public.native_checkout_scheduler_begin($1,$2)',[id,hash]),/permission denied/);await assert.rejects(db.query('select * from landerware_native_scheduler.config'),/permission denied/);await db.exec('reset role');}await db.exec('set role service_role');await assert.rejects(db.query('update landerware_native_scheduler.config set enabled=true'),/permission denied/);await assert.rejects(db.query('select landerware_native_scheduler.dispatch()'),/permission denied/);await db.exec('reset role');}));
test('service-only real role begins once and completes idempotently',()=>fixture(async db=>{await arm(db);const r=await dispatch(db);await db.exec('set role service_role');assert.equal((await begin(db,r)).started,true);assert.equal((await begin(db,r)).started,false);assert.equal((await finish(db,r)).settled,true);assert.equal((await finish(db,r)).replay,true);await assert.rejects(finish(db,r,{...good,code:'different'}),/invalid_scheduler_result/);await db.exec('reset role');}));
test('unknown run, wrong hash and expired admission fail closed',()=>fixture(async db=>{await arm(db);const r=await dispatch(db);assert.equal((await q(db,'select public.native_checkout_scheduler_begin($1,$2) as r',[r.id,hash]))[0].r.authorized,false);assert.equal((await begin(db,{id})).started,false);await db.exec("update landerware_native_scheduler.runs set created_at=now()-interval '3 minutes'");assert.equal((await begin(db,r)).started,false);}));
test('ambiguous callback latches without automatic reset or new HTTP request',()=>fixture(async db=>{await arm(db);const r=await dispatch(db);await begin(db,r);await finish(db,r,{...good,outcome:'uncertain',code:'provider_ambiguous',claimed:1,ambiguous:1});assert.equal((await q(db,'select latched from landerware_native_scheduler.config'))[0].latched,true);await db.exec("update landerware_native_scheduler.config set last_dispatch_at=now()-interval '5 minutes'");await dispatch(db);assert.equal((await q(db,'select count(*)::int n from net.captured'))[0].n,1);}));
test('lost callback or auth denial persists latch, no request replay',()=>fixture(async db=>{await arm(db);const r=await dispatch(db);await db.query('insert into net._http_response values($1,403,false,null)',[r.request_id]);await db.query('select landerware_native_scheduler.observe()');assert.equal((await q(db,'select reason from landerware_native_scheduler.config'))[0].reason,'callback_auth_denied');}));
test('missing pg_net response/crash remains unknown after two minutes',()=>fixture(async db=>{await arm(db);await dispatch(db);await db.exec("update landerware_native_scheduler.runs set created_at=now()-interval '3 minutes'");await db.query('select landerware_native_scheduler.observe()');assert.equal((await q(db,'select reason from landerware_native_scheduler.config'))[0].reason,'callback_completion_unknown');}));
test('durable finished callback wins over lost response, cadence and observer stay independent',()=>fixture(async db=>{await arm(db);const r=await dispatch(db);await begin(db,r);await finish(db,r);await db.query("insert into net._http_response values($1,null,true,'synthetic_timeout')",[r.request_id]);let h=(await q(db,'select public.native_checkout_scheduler_status() h'))[0].h;assert.equal(h.callbackFresh,true);assert.equal(h.observerFresh,false);await db.query('select landerware_native_scheduler.observe()');h=(await q(db,'select public.native_checkout_scheduler_status() h'))[0].h;assert.equal(h.observerFresh,true);await db.exec("update landerware_native_scheduler.config set last_observed_at=now()-interval '4 minutes'");h=(await q(db,'select public.native_checkout_scheduler_status() h'))[0].h;assert.equal(h.healthy,false);assert.equal(h.observerFresh,false);await db.query('select landerware_native_scheduler.observe()');assert.equal((await q(db,'select latched from landerware_native_scheduler.config'))[0].latched,false);await db.exec("update landerware_native_scheduler.runs set finished_at=now()-interval '4 minutes'");h=(await q(db,'select public.native_checkout_scheduler_status() h'))[0].h;assert.equal(h.callbackFresh,false);assert.equal(h.healthy,false);}));
test('malformed finish cannot turn uncertainty green',()=>fixture(async db=>{await arm(db);const r=await dispatch(db);await begin(db,r);for(const bad of [{...good,claimed:11},{...good,claimed:1},{...good,ambiguous:1,claimed:1},{...good,extra:'x'},null])await assert.rejects(finish(db,r,bad),/invalid_scheduler_result/);assert.equal((await q(db,'select state from landerware_native_scheduler.runs'))[0].state,'running');}));

test('proposed pg_net ACL restriction blocks inherited PUBLIC read and mutation without broad replacement grant',()=>fixture(async db=>{
 await db.exec('create table net.http_request_queue(id bigint,headers jsonb);grant usage on schema net to public;grant all on all tables in schema net to public;');
 assert.equal((await q(db,"select has_table_privilege('anon','net.http_request_queue','SELECT') p"))[0].p,true);
 const proposal=readFileSync(new URL('../supabase/reviewed/native-confirmation-scheduler/00_restrict_transport_tables.sql',import.meta.url),'utf8');
 await assert.rejects(db.exec(proposal),/scheduler_acl_change_not_approved/);await db.exec('rollback');
 await db.exec("set landerware.scheduler_secret_acl_approved='true'");await db.exec(proposal);
 for(const role of ['anon','authenticated','service_role'])for(const table of ['net.http_request_queue','net._http_response'])assert.equal((await q(db,'select has_table_privilege($1,$2,$3) p',[role,table,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER']))[0].p,false);
 assert.equal((await q(db,"select has_table_privilege(current_user,'net.http_request_queue','SELECT,INSERT') p"))[0].p,true);
}));

test('complete transport boundary denies real-role setval and even a definer enqueue wrapper, preserving owners',()=>fixture(async db=>{
 await db.exec(`create table net.http_request_queue(id bigint,headers jsonb);create sequence net.http_request_queue_id_seq;
 create function net.synthetic_definer_enqueue() returns void language sql security definer set search_path='' as $$insert into net.http_request_queue values(99,'{}')$$;
 grant usage on schema net to public;grant all on all sequences in schema net to public;grant all on all tables in schema net to public;grant execute on all functions in schema net to public;`);
 await db.exec('set role anon');await db.query("select setval('net.http_request_queue_id_seq',42)");await db.query('select net.synthetic_definer_enqueue()');await db.exec('reset role');
 const owners=await q(db,"select p.oid,p.proowner,p.prosecdef from pg_proc p where p.pronamespace='net'::regnamespace order by p.oid");
 await db.exec("set landerware.scheduler_secret_acl_approved='true'");await db.exec(readFileSync(new URL('../supabase/reviewed/native-confirmation-scheduler/00_restrict_transport_tables.sql',import.meta.url),'utf8'));
 assert.deepEqual(await q(db,"select p.oid,p.proowner,p.prosecdef from pg_proc p where p.pronamespace='net'::regnamespace order by p.oid"),owners);
 assert.equal((await q(db,'select landerware_native_scheduler.transport_acl_report() r'))[0].r.safe,true);
 for(const role of ['anon','authenticated','service_role']){
  assert.equal((await q(db,'select has_schema_privilege($1,$2,$3) p',[role,'net','USAGE,CREATE']))[0].p,false);
  assert.equal((await q(db,'select has_sequence_privilege($1,$2,$3) p',[role,'net.http_request_queue_id_seq','SELECT,UPDATE,USAGE']))[0].p,false);
  assert.equal((await q(db,'select has_function_privilege($1,$2,$3) p',[role,'net.synthetic_definer_enqueue()','EXECUTE']))[0].p,false);
  await db.exec(`set role ${role}`);await assert.rejects(db.query("select setval('net.http_request_queue_id_seq',300)"),/permission denied/);await assert.rejects(db.query('select net.synthetic_definer_enqueue()'),/permission denied/);await db.exec('reset role');
 }
 await db.query("select setval('net.http_request_queue_id_seq',43)");await db.query('select net.synthetic_definer_enqueue()');
}));
test('preflight catches inherited grants and dispatch latches privilege drift before reading token',()=>fixture(async db=>{
 await arm(db);await db.exec('create role synthetic_group;grant synthetic_group to anon;grant usage on schema net to synthetic_group');
 const report=(await q(db,'select landerware_native_scheduler.transport_acl_report() r'))[0].r;assert.equal(report.safe,false);assert.ok(report.violations.some(x=>x.role==='anon'&&x.kind==='schema'));
 await assert.rejects(db.query('select landerware_native_scheduler.assert_transport_acl()'),/scheduler_transport_acl_review_required/);
 await db.query('select landerware_native_scheduler.dispatch()');assert.equal((await q(db,'select reason from landerware_native_scheduler.config'))[0].reason,'scheduler_transport_security_changed');assert.equal((await q(db,'select count(*)::int n from net.captured'))[0].n,0);
}));
test('function and sequence effective privilege preflight is independent of denied schema access',()=>fixture(async db=>{
 await arm(db);await db.exec('grant execute on function net.http_post(text,jsonb,jsonb,jsonb,integer) to anon');
 let r=(await q(db,'select landerware_native_scheduler.transport_acl_report() r'))[0].r;assert.equal(r.safe,false);assert.ok(r.violations.some(x=>x.kind==='function'));
 await db.exec('revoke execute on function net.http_post(text,jsonb,jsonb,jsonb,integer) from anon;grant update on sequence net.captured_id_seq to public');
 r=(await q(db,'select landerware_native_scheduler.transport_acl_report() r'))[0].r;assert.equal(r.safe,false);assert.ok(r.violations.some(x=>x.kind==='sequence'&&x.role==='PUBLIC'));
}));
test('debug role override blocks runtime and provisioning even with safe current client setting',()=>fixture(async db=>{
 await arm(db);await db.exec("alter role anon set log_min_messages='debug2'");
 await assert.rejects(db.query('select landerware_native_scheduler.assert_transport_runtime()'),/scheduler_transport_logging_review_required/);
 await db.exec('alter role anon reset log_min_messages');await db.query('select landerware_native_scheduler.assert_transport_runtime()');
}));
test('activation validates exact cron command and rechecks ACLs before enabling',()=>fixture(async db=>{
 await arm(db);await db.exec(`update landerware_native_scheduler.config set enabled=false;
 create table public.landerware_checkout_delivery_config(id boolean,enabled boolean);insert into public.landerware_checkout_delivery_config values(true,false);
 create schema cron;create table cron.job(jobid bigint,jobname text,schedule text,username text,database text,command text,active boolean);
 insert into cron.job values(1,'landerware-native-confirmation-dispatch','* * * * *',current_user,current_database(),'select unexpected_operation();',false),(2,'landerware-native-confirmation-observer','* * * * *',current_user,current_database(),'select landerware_native_scheduler.observe();',false);
 create function cron.alter_job(job_id bigint,active boolean) returns void language sql as $$update cron.job set active=$2 where jobid=$1$$;
 set landerware.scheduler_activation_approved='true';set landerware.scheduler_worker_logging_reviewed='true';set landerware.scheduler_redirect_behavior_reviewed='true';`);
 const activate=readFileSync(new URL('../supabase/reviewed/native-confirmation-scheduler/02_start_disabled_lane_proof.sql',import.meta.url),'utf8');
 await assert.rejects(db.exec(activate),/scheduler_job_command_mismatch/);await db.exec('rollback');
 assert.equal((await q(db,'select enabled from landerware_native_scheduler.config'))[0].enabled,false);
 await db.exec("update cron.job set command='select landerware_native_scheduler.dispatch();' where jobid=1;grant usage on schema net to anon");
 await assert.rejects(db.exec(activate),/scheduler_transport_acl_review_required/);await db.exec('rollback');
 assert.equal((await q(db,'select count(*)::int n from cron.job where active'))[0].n,0);
}));

test('standalone custom login and non-login direct grantees are blocked without automatic revocation',()=>fixture(async db=>{
 await arm(db);await db.exec('create role synthetic_reader login;grant usage on schema net to synthetic_reader;grant select on net.captured to synthetic_reader');
 let r=(await q(db,'select landerware_native_scheduler.transport_acl_report() r'))[0].r;assert.equal(r.safe,false);assert.ok(r.violations.some(x=>x.role==='synthetic_reader'&&x.kind==='table'));
 await db.exec('revoke all on schema net from synthetic_reader;revoke all on net.captured from synthetic_reader;create role synthetic_group2;grant update on sequence net.captured_id_seq to synthetic_group2');
 r=(await q(db,'select landerware_native_scheduler.transport_acl_report() r'))[0].r;assert.equal(r.safe,false);assert.ok(r.violations.some(x=>x.role==='synthetic_group2'&&x.kind==='sequence'));
 await db.exec("set landerware.scheduler_secret_acl_approved='true'");await assert.rejects(db.exec(readFileSync(new URL('../supabase/reviewed/native-confirmation-scheduler/00_restrict_transport_tables.sql',import.meta.url),'utf8')),/scheduler_transport_acl_review_required/);await db.exec('rollback');
 assert.equal((await q(db,"select has_sequence_privilege('synthetic_group2','net.captured_id_seq','UPDATE') p"))[0].p,true);
}));
