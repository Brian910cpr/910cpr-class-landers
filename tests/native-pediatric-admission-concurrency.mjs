// Fresh loopback PostgreSQL17 only. No hosted data, credentials, mail or payments.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {sourceRoot,setupPediatricAdmission,enablePediatricPolicy,makePediatricSession,adoptPediatricSession,scalar,claimSQL,request} from './native-pediatric-admission-proof.mjs';
const {localPsql,assertLocalTargetServer}=await import(pathToFileURL(sourceRoot+'/tests/helpers/local-postgres.mjs'));
const {assertIsolatedPostgresServerAddress}=await import(pathToFileURL(sourceRoot+'/tests/helpers/isolated-postgres-address.mjs'));
const optional=process.argv.includes('--optional'),database=optional?'skills_claim_test_120110':'skills_claim_test_120109',psql=localPsql(database);
const quote=v=>v==null?'null':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
function run(sql){return new Promise((resolve,reject)=>{const p=spawn(psql.command,psql.args,{env:psql.env,stdio:['pipe','pipe','pipe']});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('error',reject);p.on('close',code=>code===0?resolve(out.trim()):reject(Error(err)));p.stdin.end(sql);});}
const db={exec:run,query:async(sql,args)=>{const s=bind(sql,args).trim().replace(/;$/,'');const q=/^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s;const out=await run(q);return {rows:out?out.split('\n').filter(v=>v.startsWith('{')).map(v=>JSON.parse(v)):[]};}};
const server=(await db.query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
assertLocalTargetServer(server,database);await assertIsolatedPostgresServerAddress(server.address,{args:psql.args,env:psql.env,port:Number(process.env.SKILLS_TEST_PORT||5432),database});
assert.equal(await run("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';"),'0');
assert.equal(await run("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema');"),'0');
await setupPediatricAdmission(db,{optional});
assert.deepEqual((await db.query("select rolsuper,rolbypassrls from pg_roles where rolname='service_role'")).rows[0],{rolsuper:false,rolbypassrls:true});
let n=30000;const outcome=p=>p.then(value=>({value}),error=>({error}));
const command=req=>'set local role service_role;'+bind(claimSQL,req)+';reset role;';
const claim=async req=>JSON.parse(await run('begin;'+command(req)+'commit;'));
async function waitFor(sql,label){let yes=false;for(let i=0;i<250&&!yes;i++)yes=await run(sql)==='t';assert.ok(yes,label);}
const latch=id=>waitFor(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${id});`,'latch '+id);
const blocked=key=>waitFor(`select exists(select 1 from pg_stat_activity where query like '%${key}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`,'blocked '+key);
const absent=req=>scalar(db,'select count(*)::int from landerware_public_orders where idempotency_key=$1',['public-order:'+req[0]]).then(x=>assert.equal(x,0));
const {sessionId,external}=await makePediatricSession(db);
const ready=()=>scalar(db,'select native_pediatric_session_booking_ready(s) from class_sessions s where id=$1',[sessionId]);
const seats=()=>scalar(db,'select landerware_public_seat_state($1)',[sessionId]);
const original=await seats();assert.equal(original.registered,1);assert.equal(original.unreconciledReserved,2);assert.equal(original.remaining,5);
assert.equal(await ready(),false);
await assert.rejects(claim(request(external,++n)),/session_not_available|native_registration_unavailable|native_profile_not_configured|profile_changed/);
await enablePediatricPolicy(db);assert.equal(await ready(),true);
for(const result of [await scalar(db,'select native_pediatric_existing_session_runtime_policy()'),(await scalar(db,'select native_scheduling_seat_snapshot($1)',[sessionId])).pediatricBooking]){assert.equal(result.unitAmount,9500);assert.equal(result.currency,'usd');}
const initialReq=request(external,++n),initial=await claim(initialReq);assert.equal(initial.status,'held');assert.equal(initial.sessionId,sessionId);
const directReq=request(external,++n),wire=JSON.parse(directReq[4]);
const direct=`set local role service_role;select native_checkout_create_order('pediatric-direct',${quote(external)},'351632',${quote(wire[0].email)},'2025550100',${quote(JSON.stringify(wire))}::jsonb,null,'{"profile_fields_validated":true}'::jsonb);`;
assert.equal(JSON.parse(await run('begin;'+direct+'commit;')).status,'held');
assert.equal((await seats()).registered,1);assert.equal((await seats()).unreconciledReserved,2);assert.equal((await seats()).holds,2);assert.equal((await seats()).remaining,3);
console.log('PASS default-off; nonsuperuser wrapper and direct creator preserve canonical adopted session and 3 prior occupied seats');
// Native authority retains reviewed unknown-source seats without requiring a new
// external read. Conversely, an unadopted missing baseline must not become zero.
const retained=JSON.parse(await run(`begin;update class_sessions set external_reconciliation='{}' where id='${sessionId}';select landerware_public_seat_state('${sessionId}');rollback;`));
assert.equal(retained.unreconciledReserved,2);assert.equal(retained.remaining,3);
await assert.rejects(run(`begin;insert into class_sessions select (jsonb_populate_record(null::class_sessions,to_jsonb(s)||jsonb_build_object('id','cccccccc-1111-4111-8111-111111111111','external_class_id','990351633','external_reconciliation','{}'::jsonb))).* from class_sessions s where id='${sessionId}';select native_session_authority_snapshot('cccccccc-1111-4111-8111-111111111111');commit;`),/native_occupancy_review_required/);
console.log('PASS missing occupancy cannot be adopted as zero; prior native retained seats survive missing retired-source evidence');

// Run rejection probes as actual nonsuperuser transactions. Each failed transaction
// disconnects/rolls back its synthetic mutation; no fixture grant repairs are made.
const negativeCases=[
 ['unreviewed',"update native_pediatric_existing_session_policy set enabled=false,verified=false"],
 ['missing timing',"update native_pediatric_existing_session_policy set enabled=false,timing_evidence=null"],
 ['identity',"update class_sessions set external_course_id='251545' where id='"+sessionId+"'"],
 ['capacity',"update class_sessions set max_students=9 where id='"+sessionId+"'"],
 ['unbound',"update courses set registration_profile_key=null where enrollware_course_id='351632'"],
 ['price',"update landerware_registration_catalog set unit_amount=9600 where course_id='351632'"],
 ['null expiry',"update instructor_qualifications set expires_at=null where qualification_key='aha-bls-instructor:209806'"],
 ['infinite expiry',"update instructor_qualifications set expires_at='infinity' where qualification_key='aha-bls-instructor:209806'"],
 ['conflicting source',"insert into instructor_qualifications(instructor_id,course_id,qualification_key,status,expires_at) select instructor_id,course_id,qualification_key,'revoked',expires_at from instructor_qualifications where qualification_key='aha-bls-instructor:209806'"],
 ['phantom alias',"update landerware_registration_profiles set version=version+1,form_schema=jsonb_set(form_schema,'{public_aliases}','[{\"public_course_id\":\"351632\"}]') where profile_key='native_bls_209806_v1'"],
];
for(const [label,change] of negativeCases){
 const req=request(external,++n);
 await assert.rejects(run('begin;'+change+';'+command(req)+'commit;'),/session_not_available|native_registration_unavailable|native_profile_not_configured|profile_changed/,label);
 await absent(req);assert.equal((await seats()).unreconciledReserved,2);
}
console.log('PASS real service-role unreviewed, timing, identity, capacity, binding, price, finite qualification, conflict and alias rejection');

const scope='where public_course_id=\'351632\'',profile="where profile_key='native_heartsaver_351632_draft'";
const authorityDecision=enabled=>`select native_session_authority_record('${sessionId}',gen_random_uuid(),p->>'fingerprint',(p->>'revision')::integer,${enabled}) from (select native_session_authority_snapshot('${sessionId}') p) proof`;
const directAuthorityInsert=`insert into landerware_session_authority_events select (jsonb_populate_record(null::landerware_session_authority_events,to_jsonb(e)||jsonb_build_object('id',gen_random_uuid(),'decision_id',gen_random_uuid(),'revision',e.revision+1,'enabled',false))).* from landerware_session_authority_events e where class_session_id='${sessionId}' order by revision desc limit 1`;
const mutations=[
 ['direct authority insert',directAuthorityInsert,authorityDecision(true)],
 ['authority',authorityDecision(false),authorityDecision(true)],
 ['profile',`update landerware_registration_profiles set active=false ${profile}`,`update landerware_registration_profiles set active=true ${profile}`],
 ['catalog',"update landerware_registration_catalog set active=false where course_id='351632'","update landerware_registration_catalog set active=true where course_id='351632'"],
 ['qualification',"update instructor_qualifications set status='revoked' where qualification_key='aha-bls-instructor:209806'","update instructor_qualifications set status='active' where qualification_key='aha-bls-instructor:209806'"],
 ['disable',`update native_pediatric_existing_session_policy set publication_enabled=false ${scope}`,`update native_pediatric_existing_session_policy set publication_enabled=true ${scope}`],
];
for(const [label,change,restore] of mutations){
 const marker=++n,hold=run(`begin;select id from class_sessions where id='${sessionId}' for update;select pg_advisory_xact_lock(${marker});select pg_sleep(2);${change};commit;`);await latch(marker);
 const req=request(external,++n),pending=outcome(claim(req));await blocked(req[0]);await hold;
 assert.match((await pending).error?.message||'',/session_not_available|profile_changed|price_catalog_missing|native_authority_disabled/);await absent(req);
 assert.equal((await claim(initialReq)).orderId,initial.orderId);await run(restore+';');assert.equal((await seats()).registered,1);assert.equal((await seats()).unreconciledReserved,2);
 console.log(`PASS actual class-row wait then committed ${label} rejects atomically; prior nonce and occupancy retained`);
}
for(const [label,sql] of [
 ['policy',`update native_pediatric_existing_session_policy set evidence=evidence ${scope}`],
 ['profile',`update landerware_registration_profiles set active=active ${profile}`],
 ['catalog',"update landerware_registration_catalog set active=active where course_id='351632'"],
 ['alias','update landerware_registration_profiles set form_schema=form_schema'],
 ['source',"update instructor_qualifications set status=status where qualification_key='aha-bls-instructor:209806'"],
]){
 const req=request(external,++n),marker=++n;
 const win=run('begin;'+command(req)+`select pg_advisory_xact_lock(${marker});select pg_sleep(2);rollback;`);await latch(marker);
 const key=`ped_${label}_${n}`,mutation=outcome(run(sql+` /* ${key} */;`));await blocked(key);await win;const result=await mutation;if(result.error)throw result.error;await absent(req);
}
console.log('PASS policy/profile/catalog/alias/source writers serialize behind accepted admission');
const authorityReq=request(external,++n),authorityMarker=++n;
const authorityWinner=run('begin;'+command(authorityReq)+`select pg_advisory_xact_lock(${authorityMarker});select pg_sleep(2);rollback;`);await latch(authorityMarker);
const authorityInsertKey='pediatric_authority_insert_wait';
const authorityInsertWriter=outcome(run('begin;set local role service_role;'+directAuthorityInsert+` /* ${authorityInsertKey} */;rollback;`));await blocked(authorityInsertKey);await authorityWinner;
const authorityInsertResult=await authorityInsertWriter;if(authorityInsertResult.error)throw authorityInsertResult.error;
await absent(authorityReq);assert.equal(await ready(),true);
console.log('PASS direct service-role authority-event INSERT serializes behind accepted admission');
const duplicateReq=request(external,++n),duplicateMarker=++n;
const duplicateWinner=run('begin;'+command(duplicateReq)+`select pg_advisory_xact_lock(${duplicateMarker});select pg_sleep(2);rollback;`);await latch(duplicateMarker);
const duplicateKey='pediatric_duplicate_identity_wait';
const duplicateWriter=outcome(run(`begin;set local role service_role;insert into class_sessions select (jsonb_populate_record(null::class_sessions,to_jsonb(s)||jsonb_build_object('id',gen_random_uuid(),'start_at',s.start_at+interval '1 day','end_at',s.end_at+interval '1 day','consumption_start_at',s.consumption_start_at+interval '1 day','consumption_end_at',s.consumption_end_at+interval '1 day'))).* from class_sessions s where id='${sessionId}' /* ${duplicateKey} */;rollback;`));await blocked(duplicateKey);await duplicateWinner;
const duplicateResult=await duplicateWriter;if(duplicateResult.error)throw duplicateResult.error;await absent(duplicateReq);
console.log('PASS duplicate external-identity insertion serializes behind accepted admission');


// Low-level callers must recheck after waiting just like the public wrapper.
const directMarker=++n,directHold=run(`begin;select id from class_sessions where id='${sessionId}' for update;select pg_advisory_xact_lock(${directMarker});select pg_sleep(2);update instructor_qualifications set status='revoked' where qualification_key='aha-bls-instructor:209806';commit;`);await latch(directMarker);
const directRaceKey='pediatric-direct-race',directRace=direct.replace('pediatric-direct',directRaceKey),directPending=outcome(run('begin;'+directRace+'commit;'));await blocked(directRaceKey);await directHold;
assert.match((await directPending).error?.message||'',/session_not_available/);
assert.equal(await scalar(db,'select count(*)::int from landerware_public_orders where idempotency_key=$1',[directRaceKey]),0);
await run("update instructor_qualifications set status='active' where qualification_key='aha-bls-instructor:209806';");
console.log('PASS low-level creator waits for class row, then rejects committed qualification revocation');

const writerMarker=++n,writer=run(`begin;update landerware_registration_catalog set active=active where course_id='351632';select pg_advisory_xact_lock(${writerMarker});select pg_sleep(3);rollback;`);await latch(writerMarker);
const busyReq=request(external,++n),start=Date.now(),busy=await outcome(claim(busyReq));assert.match(busy.error?.message||'',/session_not_available/);assert.ok(Date.now()-start<2000);await absent(busyReq);await writer;
for(const level of ['repeatable read','serializable'])await assert.rejects(run(`begin isolation level ${level};`+command(request(external,++n))+'commit;'),/native_pediatric_admission_isolation_required/);
// Payment callbacks are owner-role regression only, not an expanded service ACL claim.
await run(`update landerware_public_orders set stripe_checkout_session_id='cs_pediatric' where id='${initial.orderId}';update native_pediatric_existing_session_policy set enabled=false;`);
const evidence={id:'cs_pediatric',mode:'payment',payment_status:'paid',amount_total:9500,currency:'usd',metadata:{landerware_order_id:initial.orderId}};
await scalar(db,'select native_checkout_record_payment($1,$2,$3::jsonb)',[initial.orderId,'pi_pediatric',JSON.stringify(evidence)]);
const finalize=()=>scalar(db,'select native_checkout_finalize_order($1,$2,$3::jsonb)',[initial.orderId,'pi_pediatric',JSON.stringify(evidence)]);
assert.equal((await finalize()).status,'paid');assert.equal((await finalize()).idempotentReplay,true);assert.equal((await claim(initialReq)).orderId,initial.orderId);
await run('update native_pediatric_existing_session_policy set enabled=true;');
// Preserve all existing retained occupancy while deliberately reviewing new geometry.
await run(`with t as(select clock_timestamp()+interval '2 seconds' starts) update class_sessions s set start_at=t.starts,consumption_start_at=t.starts-interval '7 minutes',end_at=t.starts+interval '123 minutes',consumption_end_at=t.starts+interval '136 minutes' from t where s.id='${sessionId}';`);
await adoptPediatricSession(db,sessionId);assert.equal(await ready(),true);
const nearMarker=++n,hold=run(`begin;select id from class_sessions where id='${sessionId}' for update;select pg_advisory_xact_lock(${nearMarker});select pg_sleep(3);commit;`);await latch(nearMarker);
const crossing=request(external,++n),pending=outcome(claim(crossing));await blocked(crossing[0]);
assert.equal(await run(`select exists(select 1 from pg_stat_activity a cross join class_sessions s where a.query like '%${crossing[0]}%' and a.pid<>pg_backend_pid() and a.wait_event_type='Lock' and s.id='${sessionId}' and a.xact_start<s.start_at);`),'t');
await hold;assert.match((await pending).error?.message||'',/session_not_available/);await absent(crossing);assert.equal((await claim(initialReq)).orderId,initial.orderId);
console.log('PASS NOWAIT lock ordering, isolation rejection, owner-role paid recovery, actual late-start lock wait');
// Regress unrelated BLS and adult Heartsaver on the chain that includes pediatric.
const adult=await import('./native-heartsaver-admission-proof.mjs');
const bls=await import('./native-bls-admission-proof.mjs');
for(const course of ['209806','359474','209809','344085']){
 const helper=course==='209806'||course==='359474'?bls:adult;
 const offer=await (helper.makeBlsOffer||helper.makeHeartsaverOffer)(db,course,80+ ++n%10);offer.validUntil=new Date(Date.now()+600000).toISOString();
 const req=helper.request(course,null,offer,++n);
 const reserve=async r=>JSON.parse(await run('begin;set local role service_role;'+bind(helper.claimSQL,r)+';commit;'));
 const fresh=await reserve(req);assert.equal(fresh.status,'held');
 const ext=await scalar(db,'select external_class_id from class_sessions where id=$1',[fresh.sessionId]);
 assert.equal((await reserve(helper.request(course,ext,{},++n))).sessionId,fresh.sessionId);
}
console.log(`PASS PostgreSQL17 ${optional?'optional code':'independent'} chain, unaffected BLS and adult Heartsaver admissions; no hosted operations`);
