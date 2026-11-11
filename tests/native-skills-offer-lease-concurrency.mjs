// Fresh, isolated loopback PostgreSQL17 only. Synthetic data, no hosted URLs or sends.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
import {setupSkillsLease,proveBasics,makeOffer,request,claimSQL,claim,seatedOffer,footprint,scalar,service,contexts} from './native-skills-offer-lease-proof.mjs';
const mode=process.env.NATIVE_SKILLS_LEASE_CHAIN||'bls';
assert.ok(['bls','full'].includes(mode));
const full=mode==='full',database=full?'skills_claim_test_233001':'skills_claim_test_233000',psql=localPsql(database);
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
const fixture=await setupSkillsLease(db,{full});await proveBasics(db,fixture);
async function waitLatch(latch){let locked=false;for(let n=0;n<200&&!locked;n++)locked=await run(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${latch});`)==='t';assert.ok(locked,'deterministic latch not reached');}
async function claimDuringLock(offer,args,lockSQL,latch,{rollbackBlocker=false,expired=true}={}){
 const before=await footprint(db);
 const blocker=run(`begin;${lockSQL};select pg_advisory_xact_lock(${latch});select pg_sleep(3);${rollbackBlocker?'rollback':'commit'};`);await waitLatch(latch);
 const attempt=run('set role service_role;'+bind(claimSQL,args)+';').then(out=>({accepted:true,out}),e=>({accepted:false,error:e.message}));
 let waiting=false;for(let n=0;n<200&&!waiting;n++)waiting=await run(`select exists(select 1 from pg_stat_activity where query like '%${args[0]}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`)==='t';
 assert.ok(waiting,'offer must be eligible when reservation reaches awaited lock');
 const [,result]=await Promise.all([blocker,attempt]);
 if(expired)assert.ok(Date.parse(offer.validUntil)<Date.now(),'test crosses original lease');
 assert.equal(result.accepted,false,'invalid original lease must not create an order');assert.match(result.error,/session_not_available/);
 assert.deepEqual(await footprint(db),before,'complete footprint rollback including prior paid/held records');
}
for(const [i,context] of contexts.entries()){
 const original=await makeOffer(db,context,60+i,{leaseMs:1200}),args=request(context,original,5000+i),order=await claim(db,args);
 const fresh=await makeOffer(db,context,50+i,{leaseMs:1200});
 await claimDuringLock(fresh,request(context,fresh,5100+i),'lock table class_sessions in share row exclusive mode',23300090+i);
 console.log(`PASS ${mode}/${context}: native new-target expiry across schedule-table wait`);
 const existing=await seatedOffer(db,await makeOffer(db,context,60+i,{leaseMs:1200}),order.sessionId);
 await claimDuringLock(existing,request(context,existing,5200+i),`select id from class_sessions where id='${order.sessionId}' for update`,23300100+i);
 console.log(`PASS ${mode}/${context}: native existing-seat expiry across target-row wait`);
 assert.ok(Date.parse(original.validUntil)<Date.now());
 const beforeReplay=await footprint(db);assert.equal((await claim(db,args)).orderId,order.orderId);assert.deepEqual(await footprint(db),beforeReplay);
 // Only synthetic database evidence is used, with every delivery gate still off.
 await db.exec('update native_skills_publication_policy set enabled=false');
 const checkoutId=`cs_synthetic_skills_${mode}_${i}`,intent=`pi_synthetic_skills_${mode}_${i}`;
 await db.query('update landerware_public_orders set stripe_checkout_session_id=$2 where id=$1',[order.orderId,checkoutId]);
 const evidence={id:checkoutId,mode:'payment',payment_status:'paid',amount_total:5500,currency:'usd',metadata:{landerware_order_id:order.orderId}};
 await service(db,()=>scalar(db,'select native_checkout_record_payment($1,$2,$3::jsonb)',[order.orderId,intent,JSON.stringify(evidence)]));
 const finalize=()=>scalar(db,'select native_checkout_finalize_order($1,$2,$3::jsonb)',[order.orderId,intent,JSON.stringify(evidence)]);
 assert.equal((await service(db,finalize)).status,'paid');assert.equal((await service(db,finalize)).idempotentReplay,true);
 assert.equal(await scalar(db,'select count(*) from registrations where class_session_id=$1',[order.sessionId]),1);
 await db.exec('update native_skills_publication_policy set enabled=true');
 console.log(`PASS ${mode}/${context}: original expired nonce replays; synthetic paid recovery survives policy disable`);
}
// Marker-free published offers use the same generic materializer, without native
// 15-minute proof/24-hour rules. They still have an original unrenewable lease.
for(const [i,day] of [79,80].entries()){
 const legacy=await makeOffer(db,'cpr-aed',day,{legacy:true});let lockSQL='lock table class_sessions in share row exclusive mode';
 if(i){const prior=await claim(db,request('cpr-aed',legacy,5300));lockSQL=`select id from class_sessions where id='${prior.sessionId}' for update`;}
 legacy.validUntil=new Date(Date.now()+1200).toISOString();
 await claimDuringLock(legacy,request('cpr-aed',legacy,5301+i),lockSQL,23300120+i);
 console.log(`PASS ${mode}: legacy ${i?'existing':'new'} generic skills expiry across lock wait`);
}
// Reopening an abandoned generated class is also rolled back completely.
const abandoned=await makeOffer(db,'arc-blended',70),prior=await claim(db,request('arc-blended',abandoned,5400));
await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id=$1",[prior.orderId]);
assert.equal(await scalar(db,'select native_checkout_release_abandoned($1,$2)',[abandoned.startsAt,abandoned.consumptionEndsAt]),1);
abandoned.validUntil=new Date(Date.now()+1200).toISOString();
await claimDuringLock(abandoned,request('arc-blended',abandoned,5401),`select id from class_sessions where id='${prior.sessionId}' for update`,23300130);
assert.equal(await scalar(db,'select state from native_checkout_generated_sessions where class_session_id=$1',[prior.sessionId]),'released');
console.log(`PASS ${mode}: expired reopening rolls back session and lifecycle witness`);
// A workspace lock is later than the last original option validator. Block the
// unique workspace insertion with an uncommitted matching synthetic row.
const workspace=await makeOffer(db,'hsi-blended',81,{leaseMs:1200});
const option=await scalar(db,'select skills_session_native_option($1,$2::jsonb)',['hsi-blended',JSON.stringify(workspace)]);
const sql=`insert into landerware_sessions(external_session_id,course_id,course_name,starts_at,ends_at,provenance,requirements_manifest) values(${quote(option.externalId)},'skills-session-only','Synthetic',${quote(workspace.startsAt)},${quote(workspace.endsAt)},'fixture','{}')`;
await claimDuringLock(workspace,request('hsi-blended',workspace,5500),sql,23300140,{rollbackBlocker:true});
console.log(`PASS ${mode}: expiry during final workspace unique wait rolls back newly created session/witness`);
assert.deepEqual(await fixture.definitions(),fixture.before);assert.deepEqual(await fixture.configuration(),fixture.config);
assert.equal(await scalar(db,'select enabled from landerware_checkout_delivery_config'),false);
console.log(JSON.stringify({state:'LOCAL_SYNTHETIC_PROVEN',mode,server,hostedCalls:0,payments:0,mailSends:0,hostedActivation:false}));
