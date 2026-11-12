// Fresh, isolated loopback PostgreSQL17 only. Synthetic data, no hosted URLs or sends.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
import {proveHeartsaverScopes} from './native-heartsaver-full-proof.mjs';
const database='skills_claim_test_344085',psql=localPsql(database);
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
const key=n=>`98989898-9898-4898-8898-${String(n).padStart(12,'0')}`;
function claim(n,course,offer){
 const wire={firstName:'Synthetic',lastName:'Fixture',email:`race-${n}@example.invalid`,phone:'2025550100',addons:[]};
 return `select reserve_native_checkout_order('${key(n)}','native_heartsaver_${course}_draft',1,'',null,${quote(JSON.stringify(offer))}::jsonb,${quote(JSON.stringify([wire]))}::jsonb,${quote(JSON.stringify([{wire,selectedChoices:[]}]))}::jsonb,${course==='344085'?3333:9500});`;
}
async function waitLatch(latch){let locked=false;for(let i=0;i<200&&!locked;i++)locked=await run(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${latch});`)==='t';assert.ok(locked,'first transaction must reach the deterministic barrier');}
const receipt=out=>JSON.parse(out.split('\n').find(line=>line.startsWith('{')));
await proveHeartsaverScopes(db,async({offer,faOffer,nextOffer})=>{
 const latch=34408591;
 const first=run(`begin;${claim(1,'344085',offer)}select pg_advisory_xact_lock(${latch});select pg_sleep(2);commit;`);await waitLatch(latch);
 const contender=run(claim(2,'209809',faOffer)).then(()=>({accepted:true}),e=>({accepted:false,error:e.message}));
 const [created,conflict]=await Promise.all([first,contender]);const order=receipt(created);
 assert.equal(conflict.accepted,false);assert.match(conflict.error,/session_not_available/);
 console.log('PASS concurrent different full Heartsaver courses cannot occupy the same instructor/room');
 const claims=await Promise.all([3,4,5].map(n=>run(claim(n,'344085',offer)).then(out=>({accepted:true,receipt:receipt(out)}),e=>({accepted:false,error:e.message}))));
 assert.equal(claims.filter(x=>x.accepted).length,2);assert.match(claims.find(x=>!x.accepted).error,/session_not_available|insufficient_seats/);
 assert.ok(claims.filter(x=>x.accepted).every(x=>x.receipt.sessionId===order.sessionId));
 assert.equal(await run(`select count(*) from class_sessions where id='${order.sessionId}';`),'1');
 assert.equal(await run(`select count(*) from landerware_public_orders where class_session_id='${order.sessionId}';`),'3');
 console.log('PASS concurrent same-course claims retain one canonical class and exactly the approved three seats');
 const replays=await Promise.all([1,2].map(()=>run(claim(1,'344085',offer))));assert.ok(replays.every(out=>receipt(out).orderId===order.orderId));
 console.log('PASS simultaneous nonce retries recover the original order without new holds');
 // A concrete-session request must recheck credential expiry after acquiring
 // the target class lock. Active-now is insufficient for a future class.
 const createdDirect=receipt(await run(`select materialize_native_full_checkout('344085',${quote(JSON.stringify(nextOffer))}::jsonb,'synthetic-direct-race');`));
 const expiryLatch=34408593;
 const heldClass=run(`begin;select id from class_sessions where id='${createdDirect.targetSessionId}' for update;select pg_advisory_xact_lock(${expiryLatch});select pg_sleep(4);commit;`);await waitLatch(expiryLatch);
 const directSQL=n=>claim(n,'344085',{}).replace(",1,'',null,",`,1,'','${createdDirect.externalId}',`);
 const direct=run(directSQL(19)).then(out=>({accepted:true,receipt:receipt(out)}),e=>({accepted:false,error:e.message}));
 let waiting=false;for(let i=0;i<200&&!waiting;i++)waiting=await run(`select exists(select 1 from pg_stat_activity where query like '%${key(19)}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`)==='t';
 assert.ok(waiting,'concrete claim must reach the class lock barrier');
 await run("update instructor_qualifications set expires_at=now()+interval '1 day' where id='11111111-1111-4111-8111-111111111111';");
 assert.equal(await run("select native_heartsaver_full_course_ready('344085');"),'t','credential remains active now');
 const [,expiryOutcome]=await Promise.all([heldClass,direct]);assert.equal(expiryOutcome.accepted,false);assert.match(expiryOutcome.error,/session_not_available/);
 assert.equal(await run(`select count(*) from landerware_public_orders where idempotency_key='public-order:${key(19)}';`),'0');
 await run("update instructor_qualifications set expires_at=now()+interval '2 years' where id='11111111-1111-4111-8111-111111111111';");
 assert.equal(receipt(await run(directSQL(20))).sessionId,createdDirect.targetSessionId,'valid concrete-session path is preserved');
 console.log('PASS concrete-session expiry shortening during a class-lock wait rejects without an order');
 const nextLatch=34408592;
 const disable=run(`begin;update native_heartsaver_full_course_policy set enabled=false where public_course_id='344085';select pg_advisory_xact_lock(${nextLatch});select pg_sleep(2);commit;`);await waitLatch(nextLatch);
 const blocked=run(claim(6,'344085',nextOffer)).then(()=>({accepted:true}),e=>({accepted:false,error:e.message}));
 const [,disabled]=await Promise.all([disable,blocked]);assert.equal(disabled.accepted,false);assert.match(disabled.error,/native_registration_unavailable|session_not_available/);
 console.log('PASS a concurrent policy revocation blocks the claim before materialization');
});
console.log(JSON.stringify({state:'LOCAL_PROVEN',server,hostedCalls:0,payments:0,mailSends:0,activation:false}));
