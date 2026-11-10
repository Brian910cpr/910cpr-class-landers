// Independent psql processes against a NEW disposable LOCAL database only.
// This must run on PostgreSQL; a PGlite queue is not equivalent race evidence.
import {spawn} from 'node:child_process';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,profileRuntime,orderVersionMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration} from './helpers/native-checkout-migration-plan.mjs';
import assert from 'node:assert/strict';
const database=process.env.NATIVE_CHECKOUT_TEST_DATABASE;
if(database!=='native_checkout_test')throw Error('Create an empty localhost native_checkout_test database.');
const psql=localPsql(database),args=psql.args;
function run(sql){return new Promise(resolve=>{const p=spawn(psql.command,args,{windowsHide:true,env:psql.env,stdio:['pipe','pipe','pipe']});let out='',error='';p.stdout.on('data',s=>out+=s);p.stderr.on('data',s=>error+=s);p.on('error',e=>resolve({code:-1,out,error:String(e)}));p.on('close',code=>resolve({code,out,error}));p.stdin.end(sql);});}
function json(r){assert.equal(r.code,0,r.error);return JSON.parse(r.out.trim().split('\n').at(-1));}
const server=json(await run("select jsonb_build_object('database',current_database(),'version',current_setting('server_version_num')::integer,'recovery',pg_is_in_recovery())"));
assertLocalTargetServer(server,database);
const check=await run("select count(*) from information_schema.tables where table_schema='public'");assert.equal(check.code,0,check.error);assert.equal(+check.out.trim(),0,'Never reset or reuse a populated database');
for(const file of preProfileFiles){const r=await run(readFileSync(new URL('../'+file,import.meta.url),'utf8'));assert.equal(r.code,0,file+'\n'+r.error);}
assert.equal((await run("update courses set course_key='skills-session-only' where enrollware_course_id='509474'")).code,0);
const migrated=await run(readFileSync(new URL('../'+profileMigration,import.meta.url),'utf8'));assert.equal(migrated.code,0,migrated.error);
const profileRuntimeApplied=await run(readFileSync(new URL('../'+profileRuntime,import.meta.url),'utf8'));assert.equal(profileRuntimeApplied.code,0,profileRuntimeApplied.error);
const sharedNonceRuntime=await run(readFileSync(new URL('../'+orderVersionMigration,import.meta.url),'utf8'));assert.equal(sharedNonceRuntime.code,0,sharedNonceRuntime.error);
const legacySkillsAdapter=await run(readFileSync(new URL('../supabase/migrations/20261110213130_native_skills_payment_adapter_only.sql',import.meta.url),'utf8'));assert.equal(legacySkillsAdapter.code,0,legacySkillsAdapter.error);
const fullMigrated=await run(readFileSync(new URL('../'+fullCourseMigration,import.meta.url),'utf8'));assert.equal(fullMigrated.code,0,fullMigrated.error);
const codesMigrated=await run(readFileSync(new URL('../'+codeDeliveryMigration,import.meta.url),'utf8'));assert.equal(codesMigrated.code,0,codesMigrated.error);
const eventMigrated=await run(readFileSync(new URL('../'+codeEventMigration,import.meta.url),'utf8'));assert.equal(eventMigrated.code,0,eventMigrated.error);
const configured=await run(`update skills_session_context_config set qualification_course_id=(select id from courses where course_key='fixture-qualification'),enabled=true where context_key='bls-skills';
 update landerware_bls_bundle_policy set enabled=true,verified=true,verification_evidence='EXPLICIT DISPOSABLE LOCAL FIXTURE';
 update landerware_registration_catalog set addons=jsonb_set(addons,'{0,active}','true') where course_id='509474';
 insert into products(product_key,active,product_type,customer_price,fulfillment_mode) values('aha-25-3553-heartcode-bls-online',true,'online_program',40,'digital_code');
 insert into product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-NONREDEEMABLE-'||n,'available' from products cross join generate_series(1,3) n;`);assert.equal(configured.code,0,configured.error);
const key=n=>`99999999-9999-4999-8999-${String(n).padStart(12,'0')}`;
function claim(n,day,online=false,offset=0){
 const wire={firstName:'Synthetic',lastName:'Fixture',email:`fixture-${n}@example.invalid`,phone:'2025550100',skillsContext:'bls-skills',learningPath:online?'online-and-skills':'skills-only',onlineCompleted:!online,onlineCompletionAcknowledged:online,addons:online?[{key:'aha_heartcode_bls_online',quantity:1}]:[]};
 return `select reserve_native_checkout_order('${key(n)}','native_skills_shared',1,'bls-skills',null,skills_test.offer('generic-${day}-${offset}',${day},${offset})||'{"context":"bls-skills"}', '${JSON.stringify([wire])}', '${JSON.stringify([{wire,selectedChoices:[online?'online_and_skills':'skills_only']}])}',${online?9500:5500})`;
}
const mixed=await Promise.all([run(claim(1,55)),run(claim(2,55,true))]);const [skills,bundle]=mixed.map(json);assert.equal(skills.sessionId,bundle.sessionId);assert.equal(skills.amountCents,5500);assert.equal(bundle.amountCents,9500);
const third=await run(claim(3,55));assert.notEqual(third.code,0);assert.match(third.error,/session_not_available|insufficient_seats/);
const replays=(await Promise.all([run(claim(4,56,true)),run(claim(4,56,true))])).map(json);assert.equal(replays[0].orderId,replays[1].orderId);
const lastCode=await Promise.all([run(claim(5,57,true)),run(claim(6,58,true))]);assert.equal(lastCode.filter(r=>r.code===0).length,1);assert.match(lastCode.find(r=>r.code!==0).error,/addon_fulfillment_unavailable|addon_inventory_exhausted|bundle_fulfillment_unavailable/);
const count=json(await run("select jsonb_build_object('reserved',(select count(*) from product_inventory_units where status='reserved'),'orders',(select count(*) from landerware_public_orders))"));assert.deepEqual(count,{reserved:3,orders:4});
const cleanup=await run(claim(7,55,false,45));assert.notEqual(cleanup.code,0);assert.match(cleanup.error,/session_not_available/);json(await run(claim(8,55,false,60)));
assert.equal((await run(`update landerware_public_orders set status='checkout_open',stripe_checkout_session_id='cs_race' where id='${bundle.orderId}'`)).code,0);
const evidence={id:'cs_race',mode:'payment',payment_status:'paid',amount_total:9500,currency:'usd',metadata:{landerware_order_id:bundle.orderId}};
const paid=(await Promise.all([run(`select landerware_record_public_payment('${bundle.orderId}','pi_race','${JSON.stringify(evidence)}');
select landerware_finalize_public_order('${bundle.orderId}','pi_race','${JSON.stringify(evidence)}')`),run(`select landerware_record_public_payment('${bundle.orderId}','pi_race','${JSON.stringify(evidence)}');
select landerware_finalize_public_order('${bundle.orderId}','pi_race','${JSON.stringify(evidence)}')`)])).map(json);
assert.ok(paid.every(p=>p.status==='paid'));assert.equal(paid.filter(p=>p.idempotentReplay===true).length,1);
const final=json(await run("select jsonb_build_object('registrations',(select count(*) from registrations),'assigned',(select count(*) from product_inventory_units where reserved_for_registration_id is not null),'exposed',(select count(*) from product_inventory_units where exposed_at is not null))"));assert.deepEqual(final,{registrations:1,assigned:1,exposed:0});
console.log('PASS: independent PostgreSQL connections serialize mixed $55/$95 seats, replay, final code stock and paid stock assignment (not delivery); cleanup overlap rejects and the exact next boundary works.');

// Full-course fixtures remain entirely inside this disposable local database.
const fullConfigured=await run(`insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price,registration_profile_key)
 values('aha-bls-provider','Synthetic BLS','209806',120,30,6,75,'native_bls_initial'),('aha-bls-provider-renewal','Synthetic Renewal','359474',120,30,6,75,'native_bls_renewal');
 insert into people(person_key,display_name) values('brian','Brian Ennis');
 insert into instructor_qualifications(instructor_id,course_id,status) select p.id,c.id,'active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id in ('209806','359474');
 update native_full_course_policy set enabled=true,verified=true,evidence='EXPLICIT DISPOSABLE LOCAL FIXTURE';
 create function skills_test.full_offer(p_day integer,p_course text) returns jsonb language sql as $$
 select skills_test.offer('full-'||p_day||'-'||p_course,p_day)||jsonb_build_object('authority','native-full-course.v1','courseNumber',p_course,'instructor','Brian Ennis','appointmentDayId','123','selectionId','dynamic:full-'||p_day||'-'||p_course,
 'endsAt',(skills_test.offer('full',p_day)->>'startsAt')::timestamptz+interval '120 minutes','consumptionEndsAt',(skills_test.offer('full',p_day)->>'startsAt')::timestamptz+interval '150 minutes') $$;`);
assert.equal(fullConfigured.code,0,fullConfigured.error);
function fullClaim(n,day,course='209806'){
 const wire={firstName:'Synthetic',lastName:'Fixture',email:`full-${n}@example.invalid`,phone:'2025550100',manualChoice:'own-copy',addons:[]};
 return `select reserve_native_checkout_order('${key(n)}','${course==='209806'?'native_bls_initial':'native_bls_renewal'}',1,'',null,skills_test.full_offer(${day},'${course}'),'${JSON.stringify([wire])}','${JSON.stringify([{wire,selectedChoices:['manual_own']}])}',7500)`;
}
const fullReplay=(await Promise.all([run(fullClaim(80,100)),run(fullClaim(80,100))])).map(json);assert.equal(fullReplay[0].orderId,fullReplay[1].orderId);
const fullSeats=(await Promise.all([run(fullClaim(81,100)),run(fullClaim(82,100))])).map(json);assert.equal(fullSeats[0].sessionId,fullReplay[0].sessionId);assert.equal(fullSeats[1].sessionId,fullReplay[0].sessionId);
const fullConflict=await Promise.all([run(fullClaim(83,101)),run(fullClaim(84,101,'359474'))]);assert.equal(fullConflict.filter(r=>r.code===0).length,1);assert.match(fullConflict.find(r=>r.code!==0).error,/session_not_available/);
console.log('PASS isolated PostgreSQL: full-course materialization replay, distinct seat claims reuse one session, cross-course instructor/venue race rejects one.');

const deliveryToken='SYNTHETIC-LOCAL-CODE-DELIVERY-TOKEN-123456789';
assert.equal((await run(`update landerware_checkout_delivery_config set enabled=true,token_sha256=encode(sha256(convert_to('${deliveryToken}','UTF8')),'hex');update native_code_delivery_policy set enabled=true;`)).code,0);
const eligibleUnits=json(await run("select coalesce(jsonb_agg(jsonb_build_object('unitId',u.id,'studentId',st.id,'orderId',st.order_id)),'[]'::jsonb) from product_inventory_units u join landerware_public_order_students st on st.id=u.public_order_student_id where native_code_delivery_eligible(u.id,st.id,lower(trim(st.email)))"));
assert.equal(eligibleUnits.length,1,'fixture must contain exactly one eligible assigned unit before claim contention');
const codeClaims=(await Promise.all(Array.from({length:12},()=>run(`select landerware_claim_learner_code('${deliveryToken}')`)))).map(json);
const claimIdentity=json(await run("select coalesce(jsonb_agg(jsonb_build_object('deliveryId',id,'unitId',unit_id,'studentId',student_id,'attempts',attempts,'state',state)),'[]'::jsonb) from native_learner_code_delivery"));
// Synthetic stable identities only: never log code values, recipients, tokens or leases.
console.log('FIXTURE code-claim identities: '+JSON.stringify({eligibleUnits,returnedDeliveryIds:codeClaims.filter(x=>x.deliveryId).map(x=>x.deliveryId),jobs:claimIdentity}));
assert.equal(claimIdentity.length,1);assert.equal(claimIdentity[0].unitId,eligibleUnits[0].unitId);assert.equal(claimIdentity[0].studentId,eligibleUnits[0].studentId);

assert.equal(codeClaims.filter(x=>x.deliveryId).length,1);const codeJob=codeClaims.find(x=>x.deliveryId);
const preparation=await Promise.all([1,2].map(()=>run(`select landerware_prepare_learner_code('${deliveryToken}','${codeJob.deliveryId}','${codeJob.lease}')`)));
assert.equal(preparation.filter(x=>x.code===0).length,1);assert.match(preparation.find(x=>x.code!==0).error,/invalid_delivery_lease/);
// Do not print the synthetic secret; actual sending is never part of this harness.
console.log('PASS isolated PostgreSQL: twelve claimers yield one code lease and one private preparation for the same assigned paid unit.');


// Exact canonical identities, synthetic sessions/attendees, disposable database only.
const hsDraft=JSON.parse(readFileSync(new URL('../data/config/native_heartsaver_course_drafts.json',import.meta.url),'utf8'));
const plainHS=hsDraft.courses.filter(c=>['209809','351632'].includes(c.externalId));
const allHS=await run(hsDraft.courses.map(c=>`insert into courses(id,course_key,name,enrollware_course_id,duration_minutes,max_students_default,base_price,visibility_default) values('${c.canonicalId}','${c.courseKey}','Synthetic Heartsaver ${c.externalId}','${c.externalId}',${c.durationMinutes},${c.capacity},null,'${c.visibility}');`).join('\n'));
assert.equal(allHS.code,0,allHS.error);
const hsSeed=await run(readFileSync(new URL('../supabase/migrations/20261110194541_heartsaver_inactive_checkout_drafts.sql',import.meta.url),'utf8'));assert.equal(hsSeed.code,0,hsSeed.error);
for(const [i,c] of plainHS.entries()){
 const external=`synthetic-hs-${c.externalId}`;
 const setup=await run(`update courses set registration_profile_key='${c.profileKey}',base_price=95 where id='${c.canonicalId}';
 update landerware_registration_profiles set active=true where profile_key='${c.profileKey}';
 update landerware_registration_catalog set active=true where course_id='${c.externalId}';
 insert into class_sessions(source,status,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,record_scope)
 select 'landerware_event','scheduled','${c.canonicalId}',current_date+${200+i},current_date+${200+i}+make_interval(mins=>${c.durationMinutes}),current_date+${200+i},current_date+${200+i}+make_interval(mins=>${c.durationMinutes}),p.id,l.id,2,'landerware','public','open','${external}','operational'
 from people p cross join locations l where p.person_key='skills-test' and l.location_key='910cpr-office-shipyard';`);
 assert.equal(setup.code,0,setup.error);
 const claimHS=n=>{const wire={firstName:'Synthetic',lastName:'Fixture',email:`hs-${n}@example.invalid`,phone:'2025550100',addons:[]};return `select reserve_native_checkout_order('${key(n)}','${c.profileKey}',1,'','${external}','{}','${JSON.stringify([wire])}','${JSON.stringify([{wire,selectedChoices:[]}])}',9500)`;};
 const seats=await Promise.all([0,1,2].map(n=>run(claimHS(200+i*10+n))));
 assert.equal(seats.filter(r=>r.code===0).length,2,'only two fixture seats may be held');
 assert.match(seats.find(r=>r.code!==0).error,/insufficient_seats/);
 const winner=seats.findIndex(r=>r.code===0),id=200+i*10+winner,original=json(seats[winner]);
 const replay=(await Promise.all([run(claimHS(id)),run(claimHS(id))])).map(json);
 assert.equal(replay[0].orderId,original.orderId);assert.equal(replay[1].orderId,original.orderId);
}
console.log('PASS isolated PostgreSQL: both plain Heartsaver profiles serialize three claims for two session-override seats and duplicate-key replay; no online stock dependency.');


// Preserve actual hosted legacy API contracts while validating the additive namespace.
const legacyLoaded=await run(readFileSync(new URL('helpers/native-checkout-legacy-hosted-functions.sql',import.meta.url),'utf8'));assert.equal(legacyLoaded.code,0,legacyLoaded.error);const legacySkillsLoaded=await run(readFileSync(new URL('helpers/native-skills-legacy-hosted-function.sql',import.meta.url),'utf8'));assert.equal(legacySkillsLoaded.code,0,legacySkillsLoaded.error);
const legacyFingerprint=()=>run("select md5(string_agg(proname||pg_get_function_identity_arguments(p.oid)||replace(prosrc,'(/* native_paid_hold_reader_v1 */ o.hold_expires_at>now() or (o.payment_evidence->>''payment_status''=''paid'' and o.payment_evidence->>''seat_hold_protected''=''true''))','o.hold_expires_at>now()')||prosecdef::text||coalesce(proacl::text,''),'' order by proname,pg_get_function_identity_arguments(p.oid))) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in ('landerware_create_public_order','landerware_finalize_public_order')");
const oldAPI=(await legacyFingerprint()).out;
const additive=await run(readFileSync(new URL('../supabase/migrations/20261110212444_native_checkout_additive_order_runtime.sql',import.meta.url),'utf8'));assert.equal(additive.code,0,additive.error);assert.equal((await legacyFingerprint()).out,oldAPI);const versioned=await run(readFileSync(new URL('../'+orderVersionMigration,import.meta.url),'utf8'));assert.equal(versioned.code,0,versioned.error);
const compatibilitySetup=await run(`insert into courses(course_key,name,enrollware_course_id,duration_minutes,max_students_default,base_price) values('fixture-compat','Synthetic Compatibility Course','fixture-compat',120,2,75);
 insert into landerware_registration_catalog(course_id,course_name,unit_amount,active) values('fixture-compat','Synthetic Compatibility Course',7500,true);
 insert into class_sessions(source,status,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,record_scope)
 select 'landerware_event','scheduled',c.id,current_date+333,current_date+333+interval '2 hours',current_date+333,current_date+333+interval '2 hours',p.id,l.id,2,'landerware','public','open','fixture-compat-session','operational' from courses c cross join people p cross join locations l where c.course_key='fixture-compat' and p.person_key='skills-test' and l.location_key='910cpr-office-shipyard';`);assert.equal(compatibilitySetup.code,0,compatibilitySetup.error);
const compatibilityClaim=(n,legacy=false)=>{const wire={firstName:'Synthetic',lastName:'Fixture',email:`compat-${n}@example.invalid`,phone:'2025550100',addons:[]};return `select ${legacy?'landerware_create_public_order':'native_checkout_create_order'}('compat-${n}','fixture-compat-session','fixture-compat','compat-${n}@example.invalid','2025550100','${JSON.stringify([wire])}',null,'{}')`;};
const compatibilityRaces=await Promise.all([run(compatibilityClaim(410,true)),run(compatibilityClaim(411)),run(compatibilityClaim(412))]);
assert.equal(compatibilityRaces.filter(r=>r.code===0).length,2);assert.match(compatibilityRaces.find(r=>r.code!==0).error,/insufficient_seats/);
const nativeWinner=compatibilityRaces[1].code===0?411:412,nativeOriginal=json(compatibilityRaces[nativeWinner===411?1:2]);
const nativeReplays=(await Promise.all([run(compatibilityClaim(nativeWinner)),run(compatibilityClaim(nativeWinner))])).map(json);assert.equal(nativeReplays[0].orderId,nativeOriginal.orderId);assert.equal(nativeReplays[1].orderId,nativeOriginal.orderId);
console.log('PASS isolated PostgreSQL: actual legacy and additive native order APIs share two-seat contention and replay; legacy bodies differ only by paid-hold predicate; security and grants remain unchanged.');

assert.equal((await run(`update landerware_public_orders set status='checkout_open',stripe_checkout_session_id='cs_compat_synthetic' where id='${nativeOriginal.orderId}'`)).code,0);
const compatPayment={id:'cs_compat_synthetic',mode:'payment',payment_status:'paid',amount_total:7500,currency:'usd',metadata:{landerware_order_id:nativeOriginal.orderId}};
const nativeSettlement=(await Promise.all([1,2].map(()=>run(`select native_checkout_record_payment('${nativeOriginal.orderId}','pi_compat_synthetic','${JSON.stringify(compatPayment)}');select native_checkout_finalize_order('${nativeOriginal.orderId}','pi_compat_synthetic','${JSON.stringify(compatPayment)}')`)))).map(json);
assert.equal(nativeSettlement[0].status,'paid');assert.equal(nativeSettlement[1].status,'paid');
console.log('PASS isolated PostgreSQL: additive payment evidence and duplicate finalization serialize with legacy holds preserved; synthetic processor evidence only.');

// Simulate wall-clock expiry AFTER verified receipt, before finalization. Old and
// new claimers must still compete for only the other seat; no sending involved.
const paidSession=await run(`insert into class_sessions(source,status,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,record_scope)
 select source,status,course_id,start_at+interval '1 day',end_at+interval '1 day',consumption_start_at+interval '1 day',consumption_end_at+interval '1 day',lead_instructor_id,location_id,2,registration_backend,visibility,registration_status,'fixture-paid-expiry','operational' from class_sessions where external_class_id='fixture-compat-session'`);assert.equal(paidSession.code,0,paidSession.error);
const expiryClaim=(n,legacy=false)=>compatibilityClaim(n,legacy).replaceAll('fixture-compat-session','fixture-paid-expiry');
const protectedOrder=json(await run(expiryClaim(501)));
assert.equal((await run(`update landerware_public_orders set stripe_checkout_session_id='cs_expiry' where id='${protectedOrder.orderId}'`)).code,0);
const expiryEvidence={id:'cs_expiry',mode:'payment',payment_status:'paid',amount_total:7500,currency:'usd',metadata:{landerware_order_id:protectedOrder.orderId}};
json(await run(`select native_checkout_record_payment('${protectedOrder.orderId}','pi_expiry','${JSON.stringify(expiryEvidence)}')`));
assert.equal((await run(`update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id='${protectedOrder.orderId}'`)).code,0);
const expiredRace=await Promise.all([run(expiryClaim(502,true)),run(expiryClaim(503))]);assert.equal(expiredRace.filter(r=>r.code===0).length,1);assert.match(expiredRace.find(r=>r.code!==0).error,/insufficient_seats/);
const expiryFinalized=(await Promise.all([1,2].map(()=>run(`select native_checkout_finalize_order('${protectedOrder.orderId}','pi_expiry','${JSON.stringify(expiryEvidence)}')`)))).map(json);assert.ok(expiryFinalized.every(x=>x.status==='paid'));
assert.equal(json(await run(`select jsonb_build_object('registered',(select count(*) from registrations where class_session_id=(select class_session_id from landerware_public_orders where id='${protectedOrder.orderId}')))`)).registered,1);
console.log('PASS isolated PostgreSQL: paid receipt survives original hold expiry across old/new competing claims and concurrent finalization replay.');

// Profile recovery is not creator migration. The legacy order still uses the
// original finalizer and cannot be relabeled by an UPDATE or a processor replay.
const legacyVersion=json(await run("select jsonb_build_object('legacy',(select checkout_runtime_version from landerware_public_orders where idempotency_key='compat-410'),'native',(select checkout_runtime_version from landerware_public_orders where id='"+nativeOriginal.orderId+"'))"));
if(compatibilityRaces[0].code===0)assert.equal(legacyVersion.legacy,'legacy');assert.equal(legacyVersion.native,'native-v1');
const mutation=await run(`update landerware_public_orders set checkout_runtime_version='legacy' where id='${nativeOriginal.orderId}'`);assert.notEqual(mutation.code,0);assert.match(mutation.error,/order_version_immutable/);
console.log('PASS isolated PostgreSQL: creator version stays distinct for native/legacy orders and cannot change during recovery or replay.');

const crossKey=key(610),crossWire={firstName:'Synthetic',lastName:'Fixture',email:'cross-nonce@example.invalid',phone:'2025550100',onlineCompleted:true,learningPath:'skills-only',skillsContext:'cpr-aed',addons:[]};
const crossOffer="skills_test.offer('cross-nonce',710)||'{\"context\":\"cpr-aed\"}'::jsonb";
const oldCross=run(`begin;select pg_advisory_xact_lock(hashtextextended('skills-claim|${crossKey}',0));update courses set registration_profile_key=null where enrollware_course_id='509474';select reserve_skills_session_native('${crossKey}','cpr-aed',${crossOffer},'${JSON.stringify(crossWire)}');update courses set registration_profile_key='native_skills_shared' where enrollware_course_id='509474';commit;`);
const newCross=run(`select reserve_native_checkout_order('${crossKey}','native_skills_shared',1,'cpr-aed',null,${crossOffer},'${JSON.stringify([crossWire])}','${JSON.stringify([{wire:crossWire,selectedChoices:['skills_only']}])}',5500)`);
const crossed=await Promise.all([oldCross,newCross]);assert.ok(crossed.some(r=>r.code===0));for(const r of crossed)if(r.code!==0)assert.match(r.error,/generic_checkout_required/);
const crossLedgers=json(await run(`select jsonb_build_object('legacy',(select count(*) from skills_session_claim_receipts where idempotency_key='${crossKey}'),'native',(select count(*) from landerware_public_orders where idempotency_key='public-order:${crossKey}'))`));assert.equal(crossLedgers.legacy+crossLedgers.native,1);
const crossReplay=json(await run(`select reserve_native_checkout_order('${crossKey}','native_skills_shared',1,'cpr-aed',null,${crossOffer},'${JSON.stringify([crossWire])}','${JSON.stringify([{wire:crossWire,selectedChoices:['skills_only']}])}',5500)`));assert.equal(crossReplay.kind,crossLedgers.legacy?'skills_reservation':'public_order');
console.log('PASS isolated PostgreSQL: an old/new nonce race across profile activation produces exactly one ledger and recovery retains the winning creator.');

const generatedLifecycle=await run(readFileSync(new URL('../supabase/reviewed/native-checkout-generated-session-lifecycle.sql',import.meta.url),'utf8'));assert.equal(generatedLifecycle.code,0,generatedLifecycle.error);
const abandoned=json(await run(claim(701,820)));
const releaseWindow=day=>`select native_checkout_release_abandoned((skills_test.offer('maintenance',${day})->>'startsAt')::timestamptz,(skills_test.offer('maintenance',${day})->>'consumptionEndsAt')::timestamptz)`;
assert.equal((await run(`update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id='${abandoned.orderId}'`)).code,0);
const closedTwice=await Promise.all([run(releaseWindow(820)),run(releaseWindow(820))]);assert.ok(closedTwice.every(r=>r.code===0));assert.equal(closedTwice.reduce((n,r)=>n+Number(r.out.trim()),0),1);
const reclaimed=(await Promise.all([run(claim(702,820)),run(claim(703,820))])).map(json);assert.ok(reclaimed.every(r=>r.sessionId===abandoned.sessionId));
const rejectedThird=await run(claim(704,820));assert.notEqual(rejectedThird.code,0);assert.match(rejectedThird.error,/session_not_available|insufficient_seats/);
assert.equal(json(await run(`select jsonb_build_object('status',status) from landerware_public_orders where id='${abandoned.orderId}'`)).status,'expired');
console.log('PASS isolated PostgreSQL: concurrent cleanup closes one abandoned automatic session; two fresh claimers reuse original identity and the third is rejected.');

const paidCleanup=json(await run(claim(705,821)));
assert.equal((await run(`update landerware_public_orders set stripe_checkout_session_id='cs_cleanup_paid' where id='${paidCleanup.orderId}'`)).code,0);
const cleanupPayment={id:'cs_cleanup_paid',mode:'payment',payment_status:'paid',amount_total:5500,currency:'usd',metadata:{landerware_order_id:paidCleanup.orderId}};
json(await run(`select native_checkout_record_payment('${paidCleanup.orderId}','pi_cleanup_paid','${JSON.stringify(cleanupPayment)}')`));
assert.equal((await run(`update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id='${paidCleanup.orderId}'`)).code,0);
const paymentMaintenance=await Promise.all([run(releaseWindow(821)),run(`select native_checkout_finalize_order('${paidCleanup.orderId}','pi_cleanup_paid','${JSON.stringify(cleanupPayment)}')`)]);assert.equal(paymentMaintenance[0].code,0,paymentMaintenance[0].error);assert.equal(Number(paymentMaintenance[0].out.trim()),0);assert.equal(json(paymentMaintenance[1]).status,'paid');
console.log('PASS isolated PostgreSQL: cleanup racing paid-unfinalized recovery never closes or reclaims the paid session.');

const alternateSource=json(await run(claim(706,822)));
assert.equal((await run(`update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id='${alternateSource.orderId}'`)).code,0);assert.equal(Number((await run(releaseWindow(822))).out.trim()),1);
const alternative=claim(707,822,false,30).replaceAll("'bls-skills'","'cpr-aed'").replaceAll('"bls-skills"','"cpr-aed"');
const crossContext=json(await run(alternative));assert.notEqual(crossContext.sessionId,alternateSource.sessionId);
const forbiddenReopen=await run(claim(708,822));assert.notEqual(forbiddenReopen.code,0);assert.match(forbiddenReopen.error,/session_not_available/);
console.log('PASS isolated PostgreSQL: released unpaid interval admits another eligible skills context; surviving new commitment blocks conflicting old-position reopening.');
