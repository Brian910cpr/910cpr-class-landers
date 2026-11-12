import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
// Focused compatibility test: execute the actual optional scheduler DO block,
// not a rewritten algorithm or the unrelated learner schema. No live proof.
const sql=readFileSync(new URL('../supabase/migrations/20261111201439_native_confirmation_minute_scheduler_disabled.sql',import.meta.url),'utf8');
const learnerSql=readFileSync(new URL('../supabase/migrations/20261111235100_native_learner_code_resend_service.sql',import.meta.url),'utf8');
const schedulerBlock=learnerSql.match(/DO \$scheduler\$[\s\S]*?end \$scheduler\$;/)?.[0];
assert.ok(schedulerBlock,'actual optional scheduler replacement must be present');
const hash='b'.repeat(64),token='a'.repeat(64),id='11111111-1111-4111-8111-111111111111';
const good={outcome:'completed',code:null,claimed:0,accepted:0,rejected:0,ambiguous:0};
async function fixture(fn){const db=new PGlite();try{await db.exec(`create role anon;create role authenticated;create role service_role bypassrls;create schema net;create schema vault;
 create table net._http_response(id bigint,status_code int,timed_out boolean,error_msg text);
 create table vault.decrypted_secrets(id uuid,decrypted_secret text);
 create table net.captured(id bigint generated always as identity,url text,body jsonb,params jsonb,headers jsonb,timeout_milliseconds int);
 create function net.http_post(url text,body jsonb,params jsonb,headers jsonb,timeout_milliseconds int) returns bigint language plpgsql as $$declare n bigint;begin insert into net.captured(url,body,params,headers,timeout_milliseconds) values($1,$2,$3,$4,$5) returning id into n;return n;end$$;
 create function public.native_checkout_confirmation_health() returns jsonb language sql as $$select '{"healthy":true}'::jsonb$$;`);await db.exec(sql);await db.exec(schedulerBlock);await fn(db);}finally{await db.close();}}
async function q(db,sql,args=[]){return (await db.query(sql,args)).rows;}
async function arm(db){await db.exec("set landerware.scheduler_secret_acl_approved='true'");await db.exec(readFileSync(new URL('../supabase/reviewed/native-confirmation-scheduler/00_restrict_transport_tables.sql',import.meta.url),'utf8'));await db.query(`insert into vault.decrypted_secrets values($1,$2)`,[id,token]);await db.query(`update landerware_native_scheduler.config set enabled=true,token_hash=encode(sha256(convert_to($1,'UTF8')),'hex'),vault_secret_id=$2`,[token,id]);}
async function dispatch(db){await db.query('select landerware_native_scheduler.dispatch()');return (await q(db,'select * from landerware_native_scheduler.runs'))[0];}
async function begin(db,r){return (await q(db,`select public.native_checkout_scheduler_begin($1,encode(sha256(convert_to($2,'UTF8')),'hex')) as r`,[r.id,token]))[0].r;}
async function finish(db,r,result=good){return (await q(db,'select public.native_checkout_scheduler_finish($1,$2) as r',[r.id,result]))[0].r;}

test('actual optional replacement accepts blocked terminal claim, with exact idempotent settlement',()=>fixture(async db=>{
 await arm(db);const r=await dispatch(db);await db.exec('set role service_role');await begin(db,r);
 const result={...good,claimed:1,blocked:1};
 assert.equal((await finish(db,r,result)).settled,true);
 assert.equal((await finish(db,r,result)).replay,true);
 await db.exec('reset role');
 assert.deepEqual((await q(db,'select result from landerware_native_scheduler.runs'))[0].result,result);
 assert.equal((await q(db,'select latched from landerware_native_scheduler.config'))[0].latched,false);
}));

test('unknown seventh key, null and incorrect counters cannot complete a running claim',()=>fixture(async db=>{
 await arm(db);const r=await dispatch(db);await begin(db,r);
 for(const bad of [
  {...good,unknown:0},{...good,blocked:null},{...good,blocked:'1'},
  {...good,blocked:1},{...good,claimed:1,blocked:0},
  {...good,claimed:1,accepted:1,blocked:1},{...good,claimed:1,blocked:11},
  {...good,claimed:1,blocked:-1},{...good,claimed:1,blocked:0.5},
  {...good,claimed:1,blocked:1,unknown:0},{...good,claimed:null,blocked:0},null
 ])await assert.rejects(finish(db,r,bad),/invalid_scheduler_result/);
 assert.equal((await q(db,'select state from landerware_native_scheduler.runs'))[0].state,'running');
 assert.equal((await finish(db,r,{...good,claimed:1,blocked:1})).settled,true);
}));

test('optional replacement preserves uncertain latch and prevents another provider dispatch',()=>fixture(async db=>{
 await arm(db);const r=await dispatch(db);await begin(db,r);
 const result={...good,outcome:'uncertain',code:'provider_ambiguous',claimed:1,ambiguous:1,blocked:0};
 assert.equal((await finish(db,r,result)).settled,true);
 assert.equal((await finish(db,r,result)).replay,true);
 assert.equal((await q(db,'select latched from landerware_native_scheduler.config'))[0].latched,true);
 await db.exec("update landerware_native_scheduler.config set last_dispatch_at=now()-interval '5 minutes'");
 await dispatch(db);assert.equal((await q(db,'select count(*)::int n from net.captured'))[0].n,1);
 await assert.rejects(finish(db,r,{...good,claimed:1,blocked:1}),/invalid_scheduler_run/);
 assert.equal((await q(db,'select latched from landerware_native_scheduler.config'))[0].latched,true);
}));

test('six-field legacy completion remains valid and disabled schema remains default-off',()=>fixture(async db=>{
 assert.equal((await q(db,'select enabled from landerware_native_scheduler.config'))[0].enabled,false);
 assert.equal((await q(db,'select count(*)::int n from net.captured'))[0].n,0);
 await arm(db);const r=await dispatch(db);await begin(db,r);assert.equal((await finish(db,r)).settled,true);
}));
