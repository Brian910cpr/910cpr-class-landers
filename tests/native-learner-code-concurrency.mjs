// Fresh isolated loopback PostgreSQL17, synthetic codes only. No provider calls.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
import {setupCodeConcurrency,codeScalar,codeToken} from './helpers/native-code-concurrency-fixture.mjs';
const database='skills_claim_test_235101',psql=localPsql(database);
const quote=v=>v==null?'null':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
function run(sql){return new Promise((resolve,reject)=>{const p=spawn(psql.command,psql.args,{env:psql.env,stdio:['pipe','pipe','pipe']});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('error',reject);p.on('close',code=>code===0?resolve(out.trim()):reject(Error(err)));p.stdin.end(sql);});}
const db={exec:run,query:async(sql,args=[])=>{const s=bind(sql,args).trim().replace(/;$/,'');const q=/^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s;const out=await run(q);return {rows:out?out.split('\n').filter(v=>v.startsWith('{')).map(JSON.parse):[]};}};
const scalar=(sql,args=[])=>codeScalar(db,sql,args);
const server=(await db.query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
assertLocalTargetServer(server,database);await assertIsolatedPostgresServerAddress(server.address,{args:psql.args,env:psql.env,port:Number(process.env.SKILLS_TEST_PORT||5432),database});
assert.equal(await run("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';"),'0');
assert.equal(await run("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema');"),'0');
const {order}=await setupCodeConcurrency(db);
assert.deepEqual((await db.query("select rolsuper,rolbypassrls from pg_roles where rolname='service_role'")).rows[0],{rolsuper:false,rolbypassrls:true});
// No fixture grants: the actual migrations must supply runtime access without
// expanding service-role control of enablement or delivery-token configuration.
for(const column of ['enabled','token_sha256'])assert.equal(await scalar("select has_column_privilege('service_role','public.landerware_checkout_delivery_config',$1,'update')",[column]),false);
assert.equal(await scalar("select has_column_privilege('service_role','public.landerware_checkout_delivery_config','id','update')"),true);
assert.equal(await scalar("select has_table_privilege('service_role','public.landerware_checkout_delivery_config','update')"),false);
const service=sql=>run('begin;set local role service_role;'+sql+';commit;');
const jsonRows=value=>value.split('\n').filter(s=>s.startsWith('{')).map(JSON.parse);
const claim=async()=>jsonRows(await service('select native_claim_learner_code()'))[0];
const legacy=async()=>jsonRows(await service(`select landerware_claim_learner_code(${quote(codeToken)})`))[0];
const outcome=p=>p.then(value=>({value}),error=>({error}));
async function waitFor(sql,label){let yes=false;for(let i=0;i<200&&!yes;i++)yes=await run(sql)==='t';assert.ok(yes,label);}
const latch=id=>waitFor(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${id});`,'latch '+id);
const blocked=key=>waitFor(`select exists(select 1 from pg_stat_activity where query like '%${key}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`,'blocked '+key);
const prepSql=j=>`select (native_prepare_learner_code(${quote(j.deliveryId)}::uuid,${quote(j.lease)}::uuid)->>'code') is not null`;
const settleSql=(j,state,id=null)=>`select native_settle_learner_code(${quote(j.deliveryId)}::uuid,${quote(j.lease)}::uuid,${quote(state)},${quote(id)},null)`;
// Direct real-transaction timing proof. Only the external observer is synthetic;
// the actual health/readiness functions must use wall time, not transaction now().
await run(`create function public.native_checkout_scheduler_status() returns jsonb language sql volatile as $$
 select jsonb_build_object('enabled',true,'latched',false,'observerFresh',true,'callbackFresh',true,
 'lastObservedAt',statement_timestamp(),'lastCompletedAt',statement_timestamp()) $$;
 update native_learner_code_runtime set configured=true,proven=true,proof_reference='SYNTHETIC WALLCLOCK ONLY',proof_at=clock_timestamp(),
 last_poll_at=clock_timestamp()-interval '178 seconds',last_completed_at=clock_timestamp()-interval '178 seconds';`);
const timerHold=run("begin;select id from landerware_checkout_delivery_config for update;select pg_advisory_xact_lock(23510100);select pg_sleep(4);commit;");
await latch(23510100);
const timed=service(`select jsonb_build_object('ready',(native_learner_code_runtime_readiness()->>'ready')::boolean,'transactionTime',now(),'wallTime',clock_timestamp());
 select id from landerware_checkout_delivery_config for share /* code_freshness_wait */;
 select jsonb_build_object('ready',(native_learner_code_runtime_readiness()->>'ready')::boolean,'transactionTime',now(),'wallTime',clock_timestamp())`);
await blocked('code_freshness_wait');await timerHold;
const timing=jsonRows(await timed);assert.equal(timing.length,2);assert.equal(timing[0].ready,true);assert.equal(timing[1].ready,false);
assert.equal(timing[0].transactionTime,timing[1].transactionTime,'transaction now stays fixed across actual row-lock wait');
assert.ok(Date.parse(timing[1].wallTime)-Date.parse(timing[0].wallTime)>2000);
console.log('PASS code freshness expires during an actual row-lock wait in the same transaction despite fixed transaction now');
await run('update native_learner_code_runtime set configured=false,proven=false,proof_reference=null,proof_at=null,last_poll_at=null,last_completed_at=null;');
await order(1);
// Winner holds the inventory lease transaction; competing claims see no free
// unit and cannot replace the uncommitted/live unit's unique attempt.
const winner=service("select native_claim_learner_code();select pg_advisory_xact_lock(23510101);select pg_sleep(3)");await latch(23510101);
const competitors=await Promise.all(Array.from({length:6},()=>claim()));
assert.ok(competitors.every(v=>v.empty===true));
const old=await Promise.all(Array.from({length:3},()=>legacy()));assert.ok(old.every(v=>v.disabled===true));
const j=jsonRows(await winner)[0];assert.ok(j.deliveryId&&j.lease);
assert.equal(await scalar('select count(*)::int from native_learner_code_delivery'),1);
assert.equal(await scalar('select attempts from native_learner_code_delivery'),1);
console.log('PASS concurrent native claims: one unit, one durable attempt; old Cloudflare claimant disabled in Resend lane');
// Concurrent prepares serialize on the exact delivery row; the second caller
// cannot receive the same code even with the correct original lease.
const preparation=service(prepSql(j)+";select pg_advisory_xact_lock(23510102);select pg_sleep(3)");await latch(23510102);
assert.equal(await scalar('select count(*)::int from product_inventory_units where exposed_at is not null'),0,'uncommitted exposure is not visible');
const second=outcome(service(prepSql(j)+' /* code_prepare_contender */'));await blocked('code_prepare_contender');
assert.match(await preparation,/^t(?:\n|$)/);
assert.match((await second).error?.message||'',/invalid_delivery_lease/);
assert.equal(await scalar('select count(*)::int from product_inventory_units where exposed_at is not null'),1);
assert.equal(await scalar('select count(*)::int from native_learner_code_delivery where prepared_at is not null'),1);
console.log('PASS exact concurrent prepare: one code return, one committed exposure; contender rejected after lock wait');
// Simulate provider/settlement response loss: prepared processing has no outcome.
// Aging the lease must not authorize another claim or another preparation.
await run("update native_learner_code_delivery set claimed_at=now()-interval '1 day';");
assert.ok((await Promise.all(Array.from({length:5},()=>claim()))).every(v=>v.empty===true));
assert.match((await outcome(service(prepSql(j)))).error?.message||'',/invalid_delivery_lease/);
assert.equal(await scalar('select attempts from native_learner_code_delivery'),1);
assert.equal(await scalar('select lease from native_learner_code_delivery'),j.lease);
console.log('PASS settlement-unknown prepared processing remains quarantined after stale lease; no reclaim or reprepare');
await service(settleSql(j,'ambiguous'));
assert.ok((await Promise.all(Array.from({length:5},()=>claim()))).every(v=>v.empty===true));
assert.equal(await scalar('select state from native_learner_code_delivery'),'ambiguous');
assert.equal(await scalar('select attempts from native_learner_code_delivery'),1);
console.log('PASS durable ambiguous outcome is not reclaimed and inventory assignment/exposure stays intact');
// A separate paid unit demonstrates exact acceptance settlement replay. The
// provider receipt is synthetic and no transport was invoked.
await order(2);const accepted=await claim();assert.ok(accepted.deliveryId);assert.equal(await service(prepSql(accepted)),'t');
const settlement=await Promise.all(Array.from({length:2},()=>service(settleSql(accepted,'accepted','SYNTHETIC_PROVIDER_RECEIPT'))));
assert.equal(settlement.filter(v=>jsonRows(v)[0].settled===true).length,1);
assert.equal(settlement.filter(v=>jsonRows(v)[0].replay===true).length,1);
assert.ok((await Promise.all(Array.from({length:3},()=>claim()))).every(v=>v.empty===true));
assert.equal(await scalar('select count(*)::int from product_inventory_units where fulfilled_at is not null'),0);
assert.equal(await scalar('select count(*)::int from product_inventory_units where exposed_at is not null and reserved_for_registration_id is not null and public_order_student_id is not null'),2);
assert.equal(await scalar('select count(*)::int from native_learner_code_delivery'),2);
console.log('PASS concurrent exact settlement: one accepted write plus idempotent replay; no resend or fulfillment mutation');
console.log(JSON.stringify({database,postgresMajor:17,postgresVersion:server.version,serviceRoleSuperuser:false,syntheticOnly:true,providerCalls:0,testsPassed:6}));
