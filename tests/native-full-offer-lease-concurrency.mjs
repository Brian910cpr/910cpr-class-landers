// Fresh, isolated loopback PostgreSQL17 only. Synthetic data, no hosted URLs or sends.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
import {setupFullOfferLease,proveLeaseBasics,makeLeaseOffer,leaseRequest,leaseClaimSQL,claimLease,footprint,scalar,service} from './native-full-offer-lease-proof.mjs';
const mode=process.env.NATIVE_FULL_LEASE_CHAIN||'bls';
assert.ok(['bls','full'].includes(mode));
const full=mode==='full',database=full?'skills_claim_test_225501':'skills_claim_test_225500',psql=localPsql(database);
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
const fixture=await setupFullOfferLease(db,{full});await proveLeaseBasics(db,fixture);
async function waitLatch(latch){let locked=false;for(let n=0;n<200&&!locked;n++)locked=await run(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${latch});`)==='t';assert.ok(locked,'deterministic latch not reached');}
async function claimDuringLock(offer,args,lockSQL,latch,boundary='lease'){
 const before=await footprint(db);
 const blocker=run(`begin;${lockSQL};select pg_advisory_xact_lock(${latch});select pg_sleep(3);commit;`);await waitLatch(latch);
 const attempt=run('set role service_role;'+bind(leaseClaimSQL,args)+';').then(out=>({accepted:true,out}),e=>({accepted:false,error:e.message}));
 let waiting=false;for(let n=0;n<200&&!waiting;n++)waiting=await run(`select exists(select 1 from pg_stat_activity where query like '%${args[0]}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`)==='t';
 assert.ok(waiting,'lease must be valid when checkout reaches the awaited lock');
 const [,result]=await Promise.all([blocker,attempt]);
 if(boundary==='lead'){assert.ok(Date.parse(offer.validUntil)>Date.now(),'original lease remains current');assert.ok(Date.parse(offer.startsAt)<Date.now()+86400000,'test must cross original minimum lead');}
 else assert.ok(Date.parse(offer.validUntil)<Date.now(),'test must cross original lease');
 assert.equal(result.accepted,false,'expired offer must not create a held order');assert.match(result.error,/session_not_available/);
 assert.deepEqual(await footprint(db),before,'failure leaves no class/workspace/witness/inventory/hold/student/message mutation');
}
for(const [i,course] of fixture.courses.entries()){
 // Original offer becomes genuinely expired before the later identical nonce
 // replay and callback. Do not replace its timestamps to simulate that outcome.
 const original=await makeLeaseOffer(db,course,50+i);original.validUntil=new Date(Date.now()+1200).toISOString();
 const originalArgs=leaseRequest(course,original,3100+i),order=await claimLease(db,originalArgs);
 const expiredOnTable=await makeLeaseOffer(db,course,60+i);expiredOnTable.validUntil=new Date(Date.now()+1200).toISOString();
 await claimDuringLock(expiredOnTable,leaseRequest(course,expiredOnTable,3200+i),'lock table class_sessions in share row exclusive mode',22550090+i);
 console.log(`PASS ${mode}/${course}: expiry during new-target materializer lock wait rolls back all rows under service_role`);
 const expiredOnRow=await makeLeaseOffer(db,course,50+i);expiredOnRow.validUntil=new Date(Date.now()+1200).toISOString();
 await claimDuringLock(expiredOnRow,leaseRequest(course,expiredOnRow,3300+i),`select id from class_sessions where id='${order.sessionId}' for update`,22550100+i);
 console.log(`PASS ${mode}/${course}: expiry during existing-target row wait preserves its prior order and lifecycle`);
 assert.ok(Date.parse(original.validUntil)<Date.now());
 const beforeReplay=await footprint(db);assert.equal((await claimLease(db,originalArgs)).orderId,order.orderId);assert.deepEqual(await footprint(db),beforeReplay);
 const isBls=['209806','359474'].includes(course),disable=isBls?'update native_full_course_policy set enabled=false':`update native_heartsaver_full_course_policy set enabled=false where public_course_id='${course}'`;
 await db.exec(disable);
 const checkoutId=`cs_lease_${mode}_${course}`;await db.query('update landerware_public_orders set stripe_checkout_session_id=$2 where id=$1',[order.orderId,checkoutId]);
 const evidence={id:checkoutId,mode:'payment',payment_status:'paid',amount_total:originalArgs[6],currency:'usd',metadata:{landerware_order_id:order.orderId}},intent=`pi_lease_${mode}_${course}`;
 await service(db,()=>scalar(db,'select native_checkout_record_payment($1,$2,$3::jsonb)',[order.orderId,intent,JSON.stringify(evidence)]));
 const finalize=()=>scalar(db,'select native_checkout_finalize_order($1,$2,$3::jsonb)',[order.orderId,intent,JSON.stringify(evidence)]);
 assert.equal((await service(db,finalize)).status,'paid');assert.equal((await service(db,finalize)).idempotentReplay,true);
 await db.exec(disable.replace('enabled=false','enabled=true'));
 assert.equal(await scalar(db,'select count(*) from registrations where class_session_id=$1',[order.sessionId]),1);
 console.log(`PASS ${mode}/${course}: original expired-lease nonce replays; paid callback still finalizes with policy disabled`);
}
// The native 24-hour lead rule is independent of the offer's lease. Test its
// wall-clock crossing with a still-live lease, rather than relying on expiry.
const lead=await makeLeaseOffer(db,'209806',1),start=Date.now()+86400000+1200;
lead.startsAt=new Date(start).toISOString();lead.endsAt=new Date(start+120*60000).toISOString();lead.consumptionEndsAt=new Date(start+150*60000).toISOString();
lead.localStart=await scalar(db,"select to_char($1::timestamptz at time zone 'America/New_York','YYYY-MM-DD\"T\"HH24:MI')",[lead.startsAt]);
assert.ok(await scalar(db,"select native_full_course_option('209806',$1::jsonb)",[JSON.stringify(lead)]),'lead is initially eligible');
await claimDuringLock(lead,leaseRequest('209806',lead,3401),'lock table class_sessions in share row exclusive mode',22550110,'lead');
console.log(`PASS ${mode}: 24-hour lead crossing rejects despite a still-live original lease`);
assert.deepEqual(await fixture.definitions(),fixture.before,'only the shared materializer body changed');
assert.equal(await scalar(db,'select enabled from landerware_checkout_delivery_config'),false);
console.log(JSON.stringify({state:'LOCAL_PROVEN',mode,server,hostedCalls:0,payments:0,mailSends:0,hostedActivation:false}));
