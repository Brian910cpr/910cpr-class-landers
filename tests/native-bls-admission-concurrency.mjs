// Fresh loopback PostgreSQL17 only. No hosted data, credentials, mail or payments.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {sourceRoot,setupBlsAdmission,makeBlsOffer,scalar,claimSQL,request} from './native-bls-admission-proof.mjs';
const {localPsql,assertLocalTargetServer}=await import(pathToFileURL(sourceRoot+'/tests/helpers/local-postgres.mjs'));
const {assertIsolatedPostgresServerAddress}=await import(pathToFileURL(sourceRoot+'/tests/helpers/isolated-postgres-address.mjs'));
const full=process.argv.includes('--full'),database=full?'skills_claim_test_224643':'skills_claim_test_224642',psql=localPsql(database);
const quote=v=>v==null?'null':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
function run(sql){return new Promise((resolve,reject)=>{const p=spawn(psql.command,psql.args,{env:psql.env,stdio:['pipe','pipe','pipe']});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('error',reject);p.on('close',code=>code===0?resolve(out.trim()):reject(Error(err)));p.stdin.end(sql);});}
const db={exec:run,query:async(sql,args)=>{const s=bind(sql,args).trim().replace(/;$/,'');const q=/^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s;const out=await run(q);return {rows:out?out.split('\n').filter(v=>v.startsWith('{')).map(v=>JSON.parse(v)):[]};}};
const server=(await db.query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
assertLocalTargetServer(server,database);await assertIsolatedPostgresServerAddress(server.address,{args:psql.args,env:psql.env,port:Number(process.env.SKILLS_TEST_PORT||5432),database});
assert.equal(await run("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';"),'0');
assert.equal(await run("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema');"),'0');
await setupBlsAdmission(db,{full});
assert.deepEqual((await db.query("select rolsuper,rolbypassrls from pg_roles where rolname='service_role'")).rows[0],{rolsuper:false,rolbypassrls:true});
let n=10000;const outcome=p=>p.then(value=>({value}),error=>({error}));
const command=req=>'set local role service_role;'+bind(claimSQL,req)+';reset role;';
async function waitFor(sql,label){let yes=false;for(let i=0;i<200&&!yes;i++)yes=await run(sql)==='t';assert.ok(yes,label);}
const latch=id=>waitFor(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${id});`,'latch '+id);
const blocked=key=>waitFor(`select exists(select 1 from pg_stat_activity where query like '%${key}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`,'blocked '+key);
const claim=async req=>JSON.parse(await run('begin;'+command(req)+'commit;'));
const sessions=[];
for(const course of ['209806','359474']){
 const initialReq=request(course,null,await makeBlsOffer(db,course),++n),initial=await claim(initialReq);
 assert.equal(initial.status,'held');const external=await scalar(db,'select external_class_id from class_sessions where id=$1',[initial.sessionId]);
 sessions.push({course,initialReq,initial,external});
 // Qualification committed while a real existing-session row lock is awaited.
 const hold=run(`begin;select id from class_sessions where id='${initial.sessionId}' for update;select pg_advisory_xact_lock(${n});select pg_sleep(3);update instructor_qualifications set status='revoked' where qualification_key='aha-bls-instructor:${course}';commit;`);await latch(n);
 const req=request(course,external,{},++n),pending=outcome(claim(req));await blocked(req[0]);await hold;
 const result=await pending;assert.match(result.error?.message||'',/session_not_available/);assert.equal(await scalar(db,'select count(*)::int from landerware_public_orders where idempotency_key=$1',['public-order:'+req[0]]),0);
 assert.equal((await claim(initialReq)).orderId,initial.orderId,'own-key replay after revoked qualification');
 await run(`update instructor_qualifications set status='active' where qualification_key='aha-bls-instructor:${course}';`);
 console.log(`PASS ${course}: real awaited class lock sees committed qualification revocation; no new order; nonce replay retained`);
}
const {course,initialReq,initial,external}=sessions[0];
// All dependency locks survive successful validation and insertion until commit.
const winReq=request(course,external,{},++n),win=run('begin;'+command(winReq)+`select pg_advisory_xact_lock(${n});select pg_sleep(3);commit;`);await latch(n);
const mutation=outcome(run("update native_full_course_public_policy set publication_enabled=false /* bls_policy_wait */;"));await blocked('bls_policy_wait');
await win;assert.ok((await mutation).value!==undefined);assert.equal(await scalar(db,'select count(*)::int from landerware_public_orders where idempotency_key=$1',['public-order:'+winReq[0]]),1);
assert.equal((await claim(winReq)).orderId,await scalar(db,'select id from landerware_public_orders where idempotency_key=$1',['public-order:'+winReq[0]]));
assert.equal((await scalar(db,'select native_scheduling_seat_snapshot($1)',[initial.sessionId])).publicBooking,null);
await run('update native_full_course_public_policy set publication_enabled=true;');
console.log('PASS policy mutation cannot interleave admission and insertion; commits only after admitted transaction');
// An already-running configuration write makes the new reader fail closed promptly.
const pendingWriter=run(`begin;update landerware_registration_catalog set unit_amount=7600 where course_id='${course}';select pg_advisory_xact_lock(22464251);select pg_sleep(3);rollback;`);await latch(22464251);
const start=Date.now(),busy=await outcome(claim(request(course,external,{},++n)));assert.match(busy.error?.message||'',/session_not_available/);assert.ok(Date.now()-start<2000,'dependency contention must not wait/deadlock');
assert.equal((await claim(initialReq)).orderId,initial.orderId,'prior nonce replay does not enter new dependency locks');await pendingWriter;
console.log('PASS NOWAIT catalog contention rejects before cached pricing; own-key replay remains accessible');
// Mixed lower creator + reserve + queued admin profile update: no new lock inversion.
const directKey='bls-lower-mixed',wire={firstName:'Synthetic',lastName:'Direct',email:'direct@example.invalid',phone:'2025550100',manualChoice:'own-copy',addons:[]};
const lowerSql=`set local role service_role;select native_checkout_create_order('${directKey}',${quote(external)},'${course}','direct@example.invalid','2025550100',${quote(JSON.stringify([wire]))}::jsonb,null,'{"profile_fields_validated":true}'::jsonb);`;
const lower=outcome(run(`begin;select id from class_sessions where id='${initial.sessionId}' for update;select pg_advisory_xact_lock(22464252);select pg_sleep(3);${lowerSql}commit;`));await latch(22464252);
const mixedReq=request(course,external,{},++n),mixed=outcome(claim(mixedReq));await blocked(mixedReq[0]);
const admin=outcome(run(`update landerware_registration_profiles set active=false where profile_key='native_bls_${course}_v1' /* bls_profile_wait */;`));await blocked('bls_profile_wait');
const [a,b,c]=await Promise.all([lower,mixed,admin]);assert.match(a.error?.message||'',/session_not_available/);assert.match(b.error?.message||'',/session_not_available|profile_changed/);assert.ok(c.value!==undefined);
assert.equal(await scalar(db,"select count(*)::int from landerware_public_orders where idempotency_key in($1,$2)",[directKey,'public-order:'+mixedReq[0]]),0);
await run(`update landerware_registration_profiles set active=true where profile_key='native_bls_${course}_v1';`);
console.log('PASS mixed lower creator / reserve / waiting profile writer: atomic retryable rejection, no deadlock or partial order');
// Concrete seats must not start while checkout is waiting on the class lock.
// Explicitly adopt a locally reviewed identity so generated-witness drift cannot
// be the reason for rejection. No original offer or receipt timestamp is renewed.
const near=sessions[1];
await run(`with t as (select clock_timestamp()+interval '2 seconds' as starts)
 update class_sessions s set start_at=t.starts,consumption_start_at=t.starts,
 end_at=t.starts+interval '120 minutes',consumption_end_at=t.starts+interval '150 minutes',
 external_reconciliation=jsonb_build_object('complete',true,'active_external_registration_ids','[]'::jsonb,'active_registration_count',0,'source_observed_at',now())
 from t where s.id='${near.initial.sessionId}';`);
const proof=await scalar(db,'select native_session_authority_snapshot($1)',[near.initial.sessionId]);
await scalar(db,'select native_session_authority_record($1,gen_random_uuid(),$2,$3,true)',[near.initial.sessionId,proof.fingerprint,proof.revision]);
assert.equal(await scalar(db,'select native_bls_session_booking_ready(s) from class_sessions s where id=$1',[near.initial.sessionId]),true);
const startHold=run(`begin;select id from class_sessions where id='${near.initial.sessionId}' for update;select pg_advisory_xact_lock(22464253);select pg_sleep(3);commit;`);await latch(22464253);
const crossingReq=request(near.course,near.external,{},++n),crossing=outcome(claim(crossingReq));await blocked(crossingReq[0]);
assert.equal(await run(`select exists(select 1 from pg_stat_activity a cross join class_sessions s where a.query like '%${crossingReq[0]}%' and a.pid<>pg_backend_pid() and a.wait_event_type='Lock' and s.id='${near.initial.sessionId}' and a.xact_start<s.start_at);`),'t','claim transaction really began before class start');
await startHold;const crossed=await crossing;assert.match(crossed.error?.message||'',/session_not_available/);
assert.equal(await scalar(db,'select start_at<clock_timestamp() from class_sessions where id=$1',[near.initial.sessionId]),true);
assert.equal(await scalar(db,'select count(*)::int from landerware_public_orders where idempotency_key=$1',['public-order:'+crossingReq[0]]),0,'crossing start leaves no partial order');
assert.equal((await claim(near.initialReq)).orderId,near.initial.orderId,'durable nonce replay remains possible after class starts');
console.log('PASS actual concrete claim crossing class start rejects with no partial order; previously committed nonce replay preserved');
// Snapshot isolation cannot certify a revocation committed after its old snapshot.
await assert.rejects(run('begin isolation level repeatable read;'+command(request(course,external,{},++n))+'commit;'),/native_bls_admission_isolation_required/);
console.log(`PASS ${full?'full':'BLS-only'} PostgreSQL17 chain: live locks, role ACLs, revocation freshness, atomicity, replay, lock-order contention and isolation`);
