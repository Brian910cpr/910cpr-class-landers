// Fresh loopback PostgreSQL17 only. No hosted data, credentials, mail or payments.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {sourceRoot,setupHeartsaverAdmission,makeHeartsaverOffer,scalar,claimSQL,request} from './native-heartsaver-admission-proof.mjs';
const {localPsql,assertLocalTargetServer}=await import(pathToFileURL(sourceRoot+'/tests/helpers/local-postgres.mjs'));
const {assertIsolatedPostgresServerAddress}=await import(pathToFileURL(sourceRoot+'/tests/helpers/isolated-postgres-address.mjs'));
const optional=process.argv.includes('--optional'),database=optional?'skills_claim_test_120031':'skills_claim_test_120030',psql=localPsql(database);
const quote=v=>v==null?'null':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
function run(sql){return new Promise((resolve,reject)=>{const p=spawn(psql.command,psql.args,{env:psql.env,stdio:['pipe','pipe','pipe']});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('error',reject);p.on('close',code=>code===0?resolve(out.trim()):reject(Error(err)));p.stdin.end(sql);});}
const db={exec:run,query:async(sql,args)=>{const s=bind(sql,args).trim().replace(/;$/,'');const q=/^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s;const out=await run(q);return {rows:out?out.split('\n').filter(v=>v.startsWith('{')).map(v=>JSON.parse(v)):[]};}};
const server=(await db.query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
assertLocalTargetServer(server,database);await assertIsolatedPostgresServerAddress(server.address,{args:psql.args,env:psql.env,port:Number(process.env.SKILLS_TEST_PORT||5432),database});
assert.equal(await run("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';"),'0');
assert.equal(await run("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema');"),'0');
await setupHeartsaverAdmission(db,{optional});
assert.deepEqual((await db.query("select rolsuper,rolbypassrls from pg_roles where rolname='service_role'")).rows[0],{rolsuper:false,rolbypassrls:true});
let n=30000;const outcome=p=>p.then(value=>({value}),error=>({error}));
const command=req=>'set local role service_role;'+bind(claimSQL,req)+';reset role;';
const claim=async req=>JSON.parse(await run('begin;'+command(req)+'commit;'));
async function waitFor(sql,label){let yes=false;for(let i=0;i<250&&!yes;i++)yes=await run(sql)==='t';assert.ok(yes,label);}
const latch=id=>waitFor(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${id});`,'latch '+id);
const blocked=key=>waitFor(`select exists(select 1 from pg_stat_activity where query like '%${key}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`,'blocked '+key);
const absent=req=>scalar(db,'select count(*)::int from landerware_public_orders where idempotency_key=$1',['public-order:'+req[0]]).then(x=>assert.equal(x,0));
for(const course of ['209809','344085']){
 const initialReq=request(course,null,await makeHeartsaverOffer(db,course),++n),initial=await claim(initialReq);
 assert.equal(initial.status,'held');const external=await scalar(db,'select external_class_id from class_sessions where id=$1',[initial.sessionId]);
 assert.equal(await scalar(db,'select max_students from class_sessions where id=$1',[initial.sessionId]),8,'reviewed scope capacity overrides historical canonical default');
 const wire={firstName:'Synthetic',lastName:'Direct',email:'direct@example.invalid',phone:'2025550100',addons:[]};
 const directKey=`heartsaver-direct-${course}`;
 const direct=`set local role service_role;select native_checkout_create_order('${directKey}',${quote(external)},'${course}','direct@example.invalid','2025550100',${quote(JSON.stringify([wire]))}::jsonb,null,'{"profile_fields_validated":true}'::jsonb);`;
 assert.equal(JSON.parse(await run('begin;'+direct+'commit;')).status,'held');
 const valid=await claim(request(course,external,{},++n));assert.equal(valid.sessionId,initial.sessionId);
 console.log(`PASS ${course}: nonsuperuser dynamic, concrete wrapper and direct creator; scoped capacity 8`);
 const scope=`where public_course_id='${course}'`,profile=`where profile_key='native_heartsaver_${course}_draft'`;
 const mutations=[
 ['profile',`update landerware_registration_profiles set active=false ${profile}`,`update landerware_registration_profiles set active=true ${profile}`],
 ['catalog',`update landerware_registration_catalog set active=false where course_id='${course}'`,`update landerware_registration_catalog set active=true where course_id='${course}'`],
 ['qualification',"update instructor_qualifications set status='revoked' where qualification_key='aha-bls-instructor:209806'","update instructor_qualifications set status='active' where qualification_key='aha-bls-instructor:209806'"],
 ['disable',`update native_heartsaver_full_course_policy set publication_enabled=false ${scope}`,`update native_heartsaver_full_course_policy set publication_enabled=true ${scope}`],
 ];
 for(const [label,change,restore] of mutations){
  const marker=++n,hold=run(`begin;select id from class_sessions where id='${initial.sessionId}' for update;select pg_advisory_xact_lock(${marker});select pg_sleep(2);${change};commit;`);await latch(marker);
  const req=request(course,external,{},++n),pending=outcome(claim(req));await blocked(req[0]);await hold;
  const result=await pending;assert.match(result.error?.message||'',/session_not_available|profile_changed|price_catalog_missing/);await absent(req);
  assert.equal((await claim(initialReq)).orderId,initial.orderId,'prior nonce recovery despite '+label);await run(restore+';');
  console.log(`PASS ${course}: actual class-row wait then committed ${label} rejects atomically; prior nonce retained`);
 }
 // Every admitted dependency lock must outlive the creator until transaction commit.
 const dependencyWrites=[
 ['scope',`update native_heartsaver_full_course_policy set evidence=evidence ${scope}`],
 ['profile',`update landerware_registration_profiles set active=active ${profile}`],
 ['catalog',`update landerware_registration_catalog set active=active where course_id='${course}'`],
 ['alias',"update landerware_registration_profiles set form_schema=form_schema"],
 ['source',"update instructor_qualifications set status=status where qualification_key='aha-bls-instructor:209806'"],
 ];
 for(const [label,sql] of dependencyWrites){
  const req=request(course,external,{},++n),marker=++n;
  const win=run('begin;'+command(req)+`select pg_advisory_xact_lock(${marker});select pg_sleep(2);rollback;`);await latch(marker);
  const key=`hs_${course}_${label}_${n}`,mutation=outcome(run(sql+` /* ${key} */;`));await blocked(key);await win;const result=await mutation;if(result.error)throw result.error;
  await absent(req);
 }
 console.log(`PASS ${course}: scope/profile/catalog/alias/source qualification writers serialize behind accepted admission`);
 const writerMarker=++n,writer=run(`begin;update landerware_registration_catalog set active=active where course_id='${course}';select pg_advisory_xact_lock(${writerMarker});select pg_sleep(3);rollback;`);await latch(writerMarker);
 const req=request(course,external,{},++n),start=Date.now(),busy=await outcome(claim(req));assert.match(busy.error?.message||'',/session_not_available/);assert.ok(Date.now()-start<2000,'NOWAIT conflict rejects promptly');await absent(req);
 assert.equal((await claim(initialReq)).orderId,initial.orderId);await writer;
 await assert.rejects(run('begin isolation level repeatable read;'+command(request(course,external,{},++n))+'commit;'),/native_heartsaver_admission_isolation_required/);
 await assert.rejects(run('begin isolation level serializable;'+command(request(course,external,{},++n))+'commit;'),/native_heartsaver_admission_isolation_required/);
 // Payment recovery stays accessible after sales qualification is withdrawn.
 await run(`update landerware_public_orders set stripe_checkout_session_id='cs_hs_${course}' where id='${initial.orderId}';update native_heartsaver_full_course_policy set enabled=false ${scope};`);
 const evidence={id:`cs_hs_${course}`,mode:'payment',payment_status:'paid',amount_total:course==='209809'?9500:7000,currency:'usd',metadata:{landerware_order_id:initial.orderId}};
 await scalar(db,'select native_checkout_record_payment($1,$2,$3::jsonb)',[initial.orderId,`pi_hs_${course}`,JSON.stringify(evidence)]);
 const finalize=()=>scalar(db,'select native_checkout_finalize_order($1,$2,$3::jsonb)',[initial.orderId,`pi_hs_${course}`,JSON.stringify(evidence)]);
 assert.equal((await finalize()).status,'paid');assert.equal((await finalize()).idempotentReplay,true);
 await run(`update native_heartsaver_full_course_policy set enabled=true ${scope};`);
 // Adopt a synthetic near-start identity, eliminating generated witness mismatch
 // as an alternate rejection cause. The waiting transaction starts before class.
 await run(`with t as(select clock_timestamp()+interval '2 seconds' starts) update class_sessions s set start_at=t.starts,consumption_start_at=t.starts,end_at=t.starts+interval '${course==='344085'?90:120} minutes',consumption_end_at=t.starts+interval '${course==='344085'?105:150} minutes',external_reconciliation=jsonb_build_object('complete',true,'active_external_registration_ids','[]'::jsonb,'active_registration_count',0,'source_observed_at',now()) from t where s.id='${initial.sessionId}';`);
 const proof=await scalar(db,'select native_session_authority_snapshot($1)',[initial.sessionId]);await scalar(db,'select native_session_authority_record($1,gen_random_uuid(),$2,$3,true)',[initial.sessionId,proof.fingerprint,proof.revision]);
 assert.equal(await scalar(db,'select native_heartsaver_session_booking_ready(s) from class_sessions s where id=$1',[initial.sessionId]),true);
 const nearMarker=++n,hold=run(`begin;select id from class_sessions where id='${initial.sessionId}' for update;select pg_advisory_xact_lock(${nearMarker});select pg_sleep(3);commit;`);await latch(nearMarker);
 const crossing=request(course,external,{},++n),pending=outcome(claim(crossing));await blocked(crossing[0]);
 assert.equal(await run(`select exists(select 1 from pg_stat_activity a cross join class_sessions s where a.query like '%${crossing[0]}%' and a.pid<>pg_backend_pid() and a.wait_event_type='Lock' and s.id='${initial.sessionId}' and a.xact_start<s.start_at);`),'t');
 await hold;assert.match((await pending).error?.message||'',/session_not_available/);await absent(crossing);assert.equal((await claim(initialReq)).orderId,initial.orderId);
 console.log(`PASS ${course}: NOWAIT, isolation rejection, paid recovery, and wall-clock class-start crossing with actual lock wait`);
}
console.log(`PASS PostgreSQL17 ${optional?'optional code':'independent Heartsaver'} chain; no hosted reads/writes or real sends`);
