// Fresh, isolated loopback PostgreSQL17 only. Synthetic data, no hosted URLs or sends.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
import {setupBlsSkills,enableSkills,enableBundle,makeOffer,request,claimSQL,claim,seatedOffer,footprint,scalar,service} from './native-bls-skills-proof.mjs';
const mode=process.env.NATIVE_BLS_SKILLS_CHAIN||'bls';
assert.ok(['bls','full'].includes(mode));
const full=mode==='full',database=full?'skills_claim_test_233505':'skills_claim_test_233504',psql=localPsql(database);
const quote=v=>v==null?'null':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
function run(sql){return new Promise((resolve,reject)=>{const p=spawn(psql.command,psql.args,{env:psql.env,stdio:['pipe','pipe','pipe']});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('error',reject);p.on('close',code=>code===0?resolve(out.trim()):reject(Error(err)));p.stdin.end(sql);});}
let role=null;
const prefix=()=>role?`set role ${role};`:'';
const db={exec:async sql=>{
 if(/^set role service_role;?$/i.test(sql.trim())){role='service_role';return '';}
 if(/^reset role;?$/i.test(sql.trim())){role=null;return '';}
 return run(prefix()+sql);
},query:async(sql,args)=>{const s=bind(sql,args).trim().replace(/;$/,'');const query=/^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s;
 const out=await run(prefix()+query);return {rows:out?out.split('\n').filter(v=>v.startsWith('{')).map(v=>JSON.parse(v)):[]};}};
const server=(await db.query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
assertLocalTargetServer(server,database);await assertIsolatedPostgresServerAddress(server.address,{args:psql.args,env:psql.env,port:Number(process.env.SKILLS_TEST_PORT||5432),database});
assert.equal(await run("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';"),'0');
assert.equal(await run("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema');"),'0');
await setupBlsSkills(db,{full});await enableSkills(db);await enableBundle(db,{stock:20});
async function waitLatch(latch){let locked=false;for(let n=0;n<200&&!locked;n++)locked=await run(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${latch});`)==='t';assert.ok(locked,'deterministic latch not reached');}
const attempt=args=>run('set role service_role;'+bind(claimSQL,args)+';').then(out=>({accepted:true,out}),e=>({accepted:false,error:e.message}));
let counter=7000;
async function rejectAcrossWait(offer,lockSQL,latch){
 const before=await footprint(db),args=request(offer,++counter);
 const blocker=run(`begin;${lockSQL};select pg_advisory_xact_lock(${latch});select pg_sleep(3);commit;`);await waitLatch(latch);
 const pending=attempt(args);let waiting=false;
 for(let n=0;n<200&&!waiting;n++)waiting=await run(`select exists(select 1 from pg_stat_activity where query like '%${args[0]}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`)==='t';
 assert.ok(waiting,'originally live selection must reach awaited lock');
 const [,result]=await Promise.all([blocker,pending]);assert.equal(result.accepted,false);assert.match(result.error,/session_not_available/);
 assert.ok(Date.parse(offer.validUntil)<Date.now());assert.deepEqual(await footprint(db),before);
}
for(const bundle of [false,true]){
 const day=bundle?51:50;
 const fresh=await makeOffer(db,day,{bundle,leaseMs:1200});
 await rejectAcrossWait(fresh,'lock table class_sessions in share row exclusive mode',23350400+day);
 const original=await makeOffer(db,day,{bundle}),args=request(original,++counter),held=await claim(db,args);
 const seated=await seatedOffer(db,await makeOffer(db,day,{bundle,leaseMs:1200}),held.sessionId);
 await rejectAcrossWait(seated,`select id from class_sessions where id='${held.sessionId}' for update`,23350500+day);
 const before=await footprint(db),replay=[...args];replay[2]='{}';assert.equal((await claim(db,replay)).orderId,held.orderId);assert.deepEqual(await footprint(db),before);
 console.log(`PASS ${mode}/${bundle?'bundle':'skills'}: new/remaining seat lease expiry across actual locks; immutable nonce replay`);
}
// A dependency write that precedes admission must defeat it without selling from
// a stale transaction snapshot. The writer rolls back so fixture state is exact.
for(const [i,change] of [
 "update native_bls_skills_publication_policy set publication_enabled=false",
 "update instructor_qualifications set status='revoked' where qualification_key='aha-bls-instructor:209806'",
 "update skills_session_context_config set enabled=false where context_key='bls-skills'",
 "update landerware_registration_catalog set active=false where course_id='509474'",
 "update products set active=false",
 "update native_code_delivery_policy set enabled=false",
 "update native_learner_code_runtime set enabled=false",
 "update landerware_checkout_delivery_config set enabled=false",
].entries()){
 const offer=await makeOffer(db,55+i,{bundle:true}),before=await footprint(db),latch=23350600+i;
 const blocker=run(`begin;${change};select pg_advisory_xact_lock(${latch});select pg_sleep(0.7);rollback;`);await waitLatch(latch);
 const result=await attempt(request(offer,++counter));await blocker;
 assert.equal(result.accepted,false,change);assert.match(result.error,/session_not_available/);assert.deepEqual(await footprint(db),before);
 console.log(`PASS ${mode}: prior dependency edit rejects stale admission: ${change.split(' ')[1]}`);
}
// Real concurrent contexts race for the final physical seat, not separate pools.
const common=await makeOffer(db,65),first=await claim(db,request(common,++counter));
const bls=await seatedOffer(db,await makeOffer(db,65,{bundle:true}),first.sessionId);
const other={...bls,context:'arc-blended',selectionId:'skills:'+bls.nativeOfferId+':arc-blended'};
for(const key of ['publicCourseId','physicalCourseId','checkoutPackage','profileKey','calendarProofObservedAt','policyProofObservedAt'])delete other[key];
const otherWire={firstName:'Synthetic',lastName:'Other',email:'cross-context@example.invalid',phone:'',onlineCompleted:true,learningPath:'skills-only',skillsContext:'arc-blended'};
const otherSQL="select reserve_native_checkout_order($1,'native_skills_shared',2,'arc-blended',null,$2::jsonb,$3::jsonb,$4::jsonb,5500)";
const otherArgs=['77777777-1111-4111-8111-111111111111',JSON.stringify(other),JSON.stringify([otherWire]),JSON.stringify([{wire:otherWire,selectedChoices:['skills_only']}])];
const latch=23350700,blocker=run(`begin;lock table class_sessions in share row exclusive mode;select pg_advisory_xact_lock(${latch});select pg_sleep(1);commit;`);await waitLatch(latch);
const pair=[attempt(request(bls,++counter)),run('set role service_role;'+bind(otherSQL,otherArgs)+';').then(out=>({accepted:true,out}),e=>({accepted:false,error:e.message}))];
await blocker;const outcomes=await Promise.all(pair);assert.equal(outcomes.filter(x=>x.accepted).length,1);
assert.equal(await scalar(db,'select count(*) from landerware_public_orders where class_session_id=$1',[first.sessionId]),2);
assert.equal((await scalar(db,'select native_scheduling_seat_snapshot($1)',[first.sessionId])).remaining,0);
console.log(`PASS ${mode}: explicit BLS bundle versus ARC final-seat race, one shared capacity2 session`);
// One remaining code cannot back two orders even at different physical times.
await db.exec("update product_inventory_units set status='unavailable' where public_order_student_id is null;insert into product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-SOLE-CODE','available' from products");
const a=await makeOffer(db,70,{bundle:true}),b=await makeOffer(db,71,{bundle:true}),aa=request(a,++counter),bb=request(b,++counter);
const lastLatch=23350800,stockLock=run(`begin;lock table class_sessions in share row exclusive mode;select pg_advisory_xact_lock(${lastLatch});select pg_sleep(1);commit;`);await waitLatch(lastLatch);
const stockPair=[attempt(aa),attempt(bb)];await stockLock;const stockOutcomes=await Promise.all(stockPair);assert.equal(stockOutcomes.filter(x=>x.accepted).length,1);
assert.equal(await scalar(db,"select count(*) from landerware_public_orders where idempotency_key in($1,$2)",['public-order:'+aa[0],'public-order:'+bb[0]]),1);
assert.equal(await scalar(db,"select count(*) from product_inventory_units where secret_value='SYNTHETIC-SOLE-CODE' and public_order_student_id is not null"),1);
console.log(`PASS ${mode}: one synthetic code across concurrent bundle sessions, no losing order/seat`);
console.log(JSON.stringify({state:'LOCAL_SYNTHETIC_PROVEN',mode,server,hostedCalls:0,payments:0,mailSends:0,hostedActivation:false}));
