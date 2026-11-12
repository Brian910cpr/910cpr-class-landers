// Disposable LOCAL synthetic fixtures only. Never a hosted client, payment or send.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {skillsOffers} from '../supabase/functions/skills-session-reservation/policy.mjs';
const {loadEndpoint}=createRequire(import.meta.url)('./helpers/canonical_demand_endpoint.cjs');
const browser=createRequire(import.meta.url)('../docs/assets/resolved-selector-availability.js');
import {setupSkillsLease,makeOffer as sharedOffer,footprint,scalar,service} from './native-skills-offer-lease-proof.mjs';
import {codeDeliveryMigration,codeEventMigration} from './helpers/native-checkout-migration-plan.mjs';
export {footprint,scalar,service};
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
export const migration=load('supabase/migrations/20261111233504_native_bls_skills_publication_disabled.sql');
export const claimSQL="select reserve_native_checkout_order($1,'native_skills_shared',$2,'bls-skills',null,$3::jsonb,$4::jsonb,$5::jsonb,$6)";
export const token='SYNTHETIC-BLS-SKILLS-DELIVERY-TOKEN-ONLY-123456789';
export async function setupBlsSkills(db,{full=false,apply=true}={}){
 const fixture=await setupSkillsLease(db,{full});
 const original=await fixture.configuration();
 if(apply){
  await db.exec(migration);
  assert.deepEqual(await fixture.configuration(),original,'no prior activation/binding/catalog/qualification/delivery changes');
  const p=await scalar(db,'select native_bls_skills_publication_policy()');
  assert.equal(p.skillsEnabled,false);assert.equal(p.bundleEnabled,false);assert.equal(p.profileVersion,null);assert.equal(p.qualificationValidThrough,null);
  assert.equal(await scalar(db,'select source_qualification_id from native_bls_skills_publication_policy'),null);
  for(const role of ['anon','authenticated']){
   assert.equal(await scalar(db,"select has_table_privilege($1,'native_bls_skills_publication_policy','select')",[role]),false);
   for(const signature of ['native_bls_skills_ready(timestamptz)','native_bls_bundle_ready(timestamptz)','native_bls_skills_publication_policy()','native_bls_skills_lock_dependencies(boolean)']){
    assert.equal(await scalar(db,'select has_function_privilege($1,$2,\'execute\')',[role,signature]),false);
    assert.equal(await scalar(db,'select prosecdef from pg_proc where oid=$1::regprocedure',[signature]),false);
   }
  }
 }
 return fixture;
}
export async function enableSkills(db){
 await db.exec(`update native_bls_skills_publication_policy set enabled=true,publication_enabled=true,verified=true,evidence='LOCAL SYNTHETIC ONLY',
  source_qualification_id=(select q.id from instructor_qualifications q join people p on p.id=q.instructor_id where p.person_key='brian' and q.qualification_key='aha-bls-instructor:209806');
  update skills_session_context_config set enabled=true,capacity_policy_verified=true,qualification_course_id=course_id,policy_evidence='native-bls-skills-policy.v1' where context_key='bls-skills';`);
 assert.equal((await scalar(db,'select native_bls_skills_publication_policy()')).skillsEnabled,true);
}
export async function enableBundle(db,{stock=4}={}){
 await db.exec(load(codeDeliveryMigration));await db.exec(load(codeEventMigration));
 await db.exec(`update native_bls_skills_publication_policy set bundle_enabled=true,bundle_verified=true,bundle_evidence='LOCAL SYNTHETIC ONLY';
  update landerware_checkout_delivery_config set enabled=true,token_sha256=encode(sha256(convert_to('${token}','UTF8')),'hex');
  update native_code_delivery_policy set enabled=true;
  update landerware_bls_bundle_policy set enabled=true,verified=true,verification_evidence='LOCAL SYNTHETIC ONLY';
  update landerware_registration_catalog set addons=jsonb_set(addons,'{0,active}','true') where course_id='509474';
  insert into products(product_key,active,product_type,customer_price,fulfillment_mode) values('aha-25-3553-heartcode-bls-online',true,'online_program',40,'digital_code');
  insert into product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-PRIVATE-CODE-'||n,'available' from products cross join generate_series(1,${stock}) n;
  grant select,update on products,landerware_bls_bundle_policy,landerware_checkout_delivery_config to service_role;`);
 // Optional service contract is synthetic here, not operational sender proof.
 assert.equal(await scalar(db,'select native_bls_bundle_ready()'),false);
 await db.exec(`create table native_learner_code_runtime(id boolean primary key default true,enabled boolean default true,provider text default 'resend');
  insert into native_learner_code_runtime default values;
  revoke all on native_learner_code_runtime from public,anon,authenticated;
  grant select,update on native_learner_code_runtime to service_role;`);
 assert.equal(await scalar(db,'select native_bls_bundle_ready()'),false);
 await db.exec(`create function native_learner_code_runtime_readiness() returns jsonb language sql stable security invoker set search_path='' as $$
  select jsonb_build_object('ready',enabled,'provider',provider) from public.native_learner_code_runtime $$;
  revoke all on function native_learner_code_runtime_readiness() from public,anon,authenticated;
  grant execute on function native_learner_code_runtime_readiness() to service_role;`);
 assert.equal((await scalar(db,'select native_bls_skills_publication_policy()')).bundleEnabled,stock>0);
}
export async function makeOffer(db,day=40,{bundle=false,leaseMs=null}={}){
 const offer=await sharedOffer(db,'bls-skills',day,{leaseMs});
 const p=await scalar(db,'select native_bls_skills_publication_policy()');
 const checkoutPackage=bundle?'heartcode-bls-online-and-skills.v1':'bls-skills-only.v1';
 return {...offer,publicCourseId:bundle?'210549':'509474',physicalCourseId:'509474',checkoutPackage,profileKey:'native_skills_shared',profileVersion:p.profileVersion,
  calendarProofObservedAt:offer.proofObservedAt,policyProofObservedAt:offer.proofObservedAt,
  selectionId:'skills:'+offer.nativeOfferId+':bls-skills:'+checkoutPackage};
}
export function request(offer,n){
 const bundle=offer.checkoutPackage==='heartcode-bls-online-and-skills.v1';
 const wire={firstName:'Synthetic',lastName:'Fixture',email:`bls-skills-${n}@example.invalid`,phone:'2025550100',
  skillsContext:'bls-skills',selectorSelectionId:offer.selectionId,learningPath:bundle?'online-and-skills':'skills-only',
  onlineCompleted:!bundle,onlineCompletionAcknowledged:bundle,addons:bundle?[{key:'aha_heartcode_bls_online',quantity:1}]:[]};
 return [`${String(n).padStart(8,'0')}-1111-4111-8111-111111111111`,offer.profileVersion,JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:[bundle?'online_and_skills':'skills_only']}]),bundle?9500:5500];
}
export const claim=(db,args)=>service(db,()=>scalar(db,claimSQL,args));
export async function seatedOffer(db,offer,sessionId){
 const s=await scalar(db,'select to_jsonb(s) from class_sessions s where id=$1',[sessionId]);
 const booking=(await scalar(db,'select native_scheduling_seat_snapshot($1)',[sessionId])).skillsBooking;
 assert.ok(booking);const nativeOfferId='native-skills-seated:'+s.external_class_id;
 return {...offer,authority:'native-skills-seated.v1',offerType:'seated_class',sourceSessionId:s.external_class_id,
  sourceSessionIds:[s.external_class_id],availabilityBlockId:'seated:'+s.external_class_id,nativeOfferId,
  selectionId:'skills:'+nativeOfferId+':bls-skills:'+offer.checkoutPackage,
  identityWitness:booking.identityWitness,profileVersion:booking.profileVersion,remainingSeats:booking.remaining};
}
export async function proveBlsSkills(db,{full=false}={}){
 await setupBlsSkills(db,{full});let n=6000;
 const opt=o=>service(db,()=>scalar(db,"select skills_session_native_option('bls-skills',$1::jsonb)",[JSON.stringify(o)]));
 // Four-context switch never admits BLS. Missing optional delivery does not affect skills.
 let offer=await makeOffer(db);assert.equal(await opt(offer),null);
 await enableSkills(db);offer=await makeOffer(db);assert.ok(await opt(offer));
 for(const value of [null,'infinity','-infinity'])assert.equal(await scalar(db,'select native_bls_skills_ready($1)',[value]),false);
 for(const authority of [null,'','other'])assert.equal(await opt({...offer,authority}),null);
 await db.exec('update native_skills_publication_policy set enabled=false');assert.ok(await opt(offer));
 assert.equal(await scalar(db,"select to_regclass('native_code_delivery_policy')"),null);
 assert.equal((await scalar(db,'select native_bls_skills_publication_policy()')).bundleEnabled,false);
 const firstArgs=request(offer,++n),first=await claim(db,firstArgs);assert.equal(first.status,'held');assert.equal(first.amountCents,5500);
 let snap=await scalar(db,'select native_scheduling_seat_snapshot($1)',[first.sessionId]);
 assert.equal(snap.remaining,1);assert.ok(snap.skillsBooking.skillsContexts.includes('bls-skills'));
 assert.equal(await scalar(db,'select count(*) from product_inventory_units'),0,'skills-only reserves no code');
 const seated=await seatedOffer(db,offer,first.sessionId);
 for(const patch of [{publicCourseId:null},{physicalCourseId:null},{checkoutPackage:null},{profileKey:null},{profileVersion:null},{publicCourseId:'210549'},
  {checkoutPackage:'heartcode-bls-online-and-skills.v1'},{profileVersion:999},{identityWitness:'0'.repeat(32)},
  {proofObservedAt:'2001-01-01T00:00:00Z'},{validUntil:'2099-01-01T00:00:00Z'},
  {calendarProofObservedAt:null},{policyProofObservedAt:null},{calendarProofObservedAt:'2099-01-01T00:00:00Z'},
  {authority:null},{context:'arc-blended'},{selectionId:'skills:legacy210549'}])assert.equal(await opt({...seated,...patch}),null,JSON.stringify(patch));
 const before=await footprint(db);
 for(const change of [a=>a[2]=JSON.stringify({...offer,publicCourseId:'210549'}),a=>a[2]=JSON.stringify({...offer,checkoutPackage:'heartcode-bls-online-and-skills.v1'}),
  a=>{const st=JSON.parse(a[3]);st[0].learningPath='online-and-skills';a[3]=JSON.stringify(st);},a=>a[5]=9500,
  a=>a[4]=JSON.stringify([{wire:JSON.parse(a[3])[0],selectedChoices:['online_and_skills']}])]){
  const args=request(offer,++n);change(args);await assert.rejects(claim(db,args),/session_not_available|invalid_course_option/);assert.deepEqual(await footprint(db),before);
 }
 // Revoke every required identity/policy independently; occupancy is unaffected.
 for(const [change,restore] of [
  ["update native_bls_skills_publication_policy set publication_enabled=false","update native_bls_skills_publication_policy set publication_enabled=true"],
  ["update native_bls_skills_publication_policy set source_qualification_id=gen_random_uuid()","update native_bls_skills_publication_policy set source_qualification_id=(select id from instructor_qualifications where qualification_key='aha-bls-instructor:209806')"],
  ["update instructor_qualifications set status='revoked' where qualification_key='aha-bls-instructor:209806'","update instructor_qualifications set status='active' where qualification_key='aha-bls-instructor:209806'"],
  ["update instructor_qualifications set expires_at=null where qualification_key='aha-bls-instructor:209806'","update instructor_qualifications set expires_at=now()+interval '2 years' where qualification_key='aha-bls-instructor:209806'"],
  ["update instructor_qualifications set expires_at=now()+interval '1 day' where qualification_key='aha-bls-instructor:209806'","update instructor_qualifications set expires_at=now()+interval '2 years' where qualification_key='aha-bls-instructor:209806'"],
  ["update skills_session_context_config set policy_evidence='skills-session-policy.v1' where context_key='bls-skills'","update skills_session_context_config set policy_evidence='native-bls-skills-policy.v1' where context_key='bls-skills'"],
  ["update landerware_registration_profiles set active=false where profile_key='native_skills_shared'","update landerware_registration_profiles set active=true where profile_key='native_skills_shared'"],
  ["update landerware_registration_catalog set active=false where course_id='509474'","update landerware_registration_catalog set active=true where course_id='509474'"],
 ]){await db.exec(change);assert.equal(await opt(seated),null,change);snap=await scalar(db,'select native_scheduling_seat_snapshot($1)',[first.sessionId]);assert.equal(snap.remaining,1);assert.ok(!snap.skillsBooking?.skillsContexts.includes('bls-skills'));await db.exec(restore);}
 // Same physical seat is shared with all existing contexts, never another pool.
 await db.exec('update native_skills_publication_policy set enabled=true');
 for(const context of ['cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended']){
  const other={...seated,context,selectionId:'skills:'+seated.nativeOfferId+':'+context};
  for(const key of ['publicCourseId','physicalCourseId','checkoutPackage','profileKey','calendarProofObservedAt','policyProofObservedAt'])delete other[key];
  assert.equal((await scalar(db,'select skills_session_native_option($1,$2::jsonb)',[context,JSON.stringify(other)])).targetSessionId,first.sessionId);
 }
 const second=await claim(db,request(seated,++n));assert.equal(second.sessionId,first.sessionId);
 await assert.rejects(claim(db,request(seated,++n)),/session_not_available|insufficient_seats/);
 assert.equal((await scalar(db,'select native_scheduling_seat_snapshot($1)',[first.sessionId])).remaining,0);
 assert.equal(await scalar(db,'select count(*) from class_sessions where id=$1',[first.sessionId]),1);
 // Exact durable replay survives gate and lease expiry without rebinding price.
 await db.exec('update native_bls_skills_publication_policy set enabled=false,bundle_enabled=false');
 const replayBefore=await footprint(db),replay=[...firstArgs];replay[2]='{}';
 assert.equal((await claim(db,replay)).orderId,first.orderId);assert.deepEqual(await footprint(db),replayBefore);
 await enableSkills(db);await enableBundle(db,{stock:4});
 const bundle=await makeOffer(db,45,{bundle:true});assert.ok(await opt(bundle));
 await proveBlsPublication(db);
 for(const [disable,restore] of [
  ['update native_bls_skills_publication_policy set bundle_enabled=false','update native_bls_skills_publication_policy set bundle_enabled=true'],
  ['update native_learner_code_runtime set enabled=false','update native_learner_code_runtime set enabled=true'],
  ["update native_learner_code_runtime set provider='cloudflare'","update native_learner_code_runtime set provider='resend'"],
  ['update native_code_delivery_policy set enabled=false','update native_code_delivery_policy set enabled=true'],
  ['update landerware_checkout_delivery_config set enabled=false','update landerware_checkout_delivery_config set enabled=true'],
  ["update products set active=false","update products set active=true"],
  ["update products set customer_price=0","update products set customer_price=40"],
  ["update product_inventory_units set status='reserved'","update product_inventory_units set status='available'"],
  ["update product_inventory_units set secret_value=''","update product_inventory_units set secret_value='SYNTHETIC-PRIVATE-CODE-'||id"],
  ["update product_inventory_units set public_order_payment_observed=true","update product_inventory_units set public_order_payment_observed=false"],
 ]){await db.exec(disable);assert.equal(await opt(bundle),null,disable);assert.ok(await opt(await makeOffer(db,46)), 'skills independent of '+disable);await db.exec(restore);}
 // A corrupt blank unit chosen ahead of valid stock rolls the whole order back.
 const blank=await scalar(db,"insert into product_inventory_units(id,product_id,secret_value,status) select '00000000-0000-4000-8000-000000000001',id,'','available' from products returning id");
 const blankBefore=await footprint(db);
 await assert.rejects(claim(db,request(bundle,++n)),/bundle_fulfillment_unavailable/);assert.deepEqual(await footprint(db),blankBefore);
 await db.query("update product_inventory_units set status='unavailable' where id=$1",[blank]);
 for(const value of [null,'infinity','-infinity'])assert.equal(await scalar(db,'select native_bls_bundle_ready($1)',[value]),false);
 const readinessDefinition=await scalar(db,"select pg_get_functiondef('native_learner_code_runtime_readiness()'::regprocedure)");
 for(const expression of ["null::jsonb", "'{\"ready\":\"true\",\"provider\":\"resend\"}'::jsonb", "'{}'::jsonb"]){
  await db.exec(`create or replace function native_learner_code_runtime_readiness() returns jsonb language sql stable security invoker set search_path='' as $$select ${expression}$$`);
  assert.equal(await opt(bundle),null);assert.ok(await opt(await makeOffer(db,46)));
 }
 await db.exec(`create or replace function native_learner_code_runtime_readiness() returns jsonb language plpgsql stable security invoker set search_path='' as $$begin raise exception 'SYNTHETIC unavailable sender';end$$`);
 assert.equal(await opt(bundle),null);assert.ok(await opt(await makeOffer(db,46)));
 await db.exec(readinessDefinition);
 const args=request(bundle,++n),paid=await claim(db,args);assert.equal(paid.amountCents,9500);
 assert.equal(await scalar(db,'select count(*) from product_inventory_units where public_order_student_id is not null'),1);
 assert.equal((await claim(db,args)).orderId,paid.orderId);
 assert.equal(await scalar(db,'select count(*) from product_inventory_units where public_order_student_id is not null'),1);
 // Two students consume two seats and two distinct units in one atomic order.
 const multiOffer=await makeOffer(db,49,{bundle:true}),multiArgs=request(multiOffer,++n);
 const firstWire=JSON.parse(multiArgs[3])[0],secondWire={...firstWire,email:'second-bundle-student@example.invalid'};
 multiArgs[3]=JSON.stringify([firstWire,secondWire]);multiArgs[4]=JSON.stringify([firstWire,secondWire].map(wire=>({wire,selectedChoices:['online_and_skills']})));multiArgs[5]=19000;
 const multi=await claim(db,multiArgs);assert.equal(multi.amountCents,19000);
 assert.equal(await scalar(db,'select count(distinct u.id) from product_inventory_units u join landerware_public_order_students s on s.id=u.public_order_student_id where s.order_id=$1',[multi.orderId]),2);
 assert.equal((await scalar(db,'select native_scheduling_seat_snapshot($1)',[multi.sessionId])).remaining,0);
 const multiBefore=await footprint(db);assert.equal((await claim(db,multiArgs)).orderId,multi.orderId);assert.deepEqual(await footprint(db),multiBefore);
 // Real SQL receipt/finalization/code state machine, synthetic evidence only.
 const checkout='cs_synthetic_bls_bundle',intent='pi_synthetic_bls_bundle';
 await db.query('update landerware_public_orders set stripe_checkout_session_id=$2 where id=$1',[paid.orderId,checkout]);
 const evidence={id:checkout,mode:'payment',payment_status:'paid',amount_total:9500,currency:'usd',metadata:{landerware_order_id:paid.orderId}};
 await service(db,()=>scalar(db,'select native_checkout_record_payment($1,$2,$3::jsonb)',[paid.orderId,intent,JSON.stringify(evidence)]));
 await db.exec('update native_bls_skills_publication_policy set enabled=false,bundle_enabled=false');
 const finalize=()=>service(db,()=>scalar(db,'select native_checkout_finalize_order($1,$2,$3::jsonb)',[paid.orderId,intent,JSON.stringify(evidence)]));
 assert.equal((await finalize()).status,'paid');assert.equal((await finalize()).idempotentReplay,true);
 const paidBefore=await footprint(db),paidReplay=[...args];paidReplay[2]='{}';
 assert.equal((await claim(db,paidReplay)).orderId,paid.orderId);assert.deepEqual(await footprint(db),paidBefore);
 assert.equal(await scalar(db,'select count(*) from registrations where class_session_id=$1',[paid.sessionId]),1);
 const delivery=await scalar(db,'select landerware_claim_learner_code($1)',[token]);assert.ok(delivery.deliveryId);
 const prepared=await scalar(db,'select landerware_prepare_learner_code($1,$2,$3)',[token,delivery.deliveryId,delivery.lease]);
 assert.match(prepared.code,/^SYNTHETIC-PRIVATE-CODE-/);assert.match(prepared.recipient,/@example.invalid$/);
 assert.equal((await scalar(db,'select landerware_claim_learner_code($1)',[token])).empty,true);
 await assert.rejects(scalar(db,'select landerware_prepare_learner_code($1,$2,$3)',[token,delivery.deliveryId,delivery.lease]),/invalid_delivery_lease/);
 const settle=()=>scalar(db,'select landerware_settle_learner_code($1,$2,$3,$4,$5,$6)',[token,delivery.deliveryId,delivery.lease,'accepted','synthetic-provider-receipt',null]);
 assert.equal((await settle()).actualDeliveryConfirmed,false);assert.equal((await settle()).replay,true);
 assert.equal(await scalar(db,'select count(*) from product_inventory_units where exposed_at is not null'),1);
 assert.equal(await scalar(db,'select count(*) from native_learner_code_delivery'),1);
 assert.ok(!JSON.stringify(await scalar(db,'select native_bls_skills_publication_policy()')).includes('SYNTHETIC-PRIVATE'));
 console.log(`PASS ${full?'full':'BLS-only'}: independent BLS skills/bundle gates, qualification/package identity, shared seats, atomic stock, paid replay and one private synthetic code delivery`);
}

export async function proveBlsPublication(db){
 const offer=await makeOffer(db,47),held=await claim(db,request(offer,6900));
 const row=await scalar(db,`select to_jsonb(s)||jsonb_build_object('courses',(select jsonb_build_object('course_key',course_key,'name',name) from courses where id=s.course_id),
  'landerware_sessions',(select jsonb_agg(w) from landerware_sessions w where w.class_session_id=s.id),
  'native_checkout_generated_sessions',(select jsonb_agg(w) from native_checkout_generated_sessions w where w.class_session_id=s.id)) from class_sessions s where id=$1`,[held.sessionId]);
 const snapshot=await scalar(db,'select native_scheduling_seat_snapshot($1)',[held.sessionId]);
 const source=loadEndpoint(()=>{throw Error('network forbidden')}).projectDemand(row,snapshot);
 const proof=await scalar(db,'select native_bls_skills_publication_policy()');
 const result=spawnSync(process.env.SKILLS_TEST_PYTHON||'python',['-B','-m','tests.helpers.native-bls-skills-publication'],{
  cwd:fileURLToPath(new URL('../',import.meta.url)),input:JSON.stringify({source,proof}),encoding:'utf8',timeout:30000});
 assert.equal(result.status,0,result.stderr||String(result.error));const feed=JSON.parse(result.stdout);
 assert.equal(browser.datesForPublication(feed.dates,feed.validUntil,Date.now(),'bls-skills').length,1);
 assert.deepEqual(browser.datesForPublication(feed.dates,'2099-01-01T00:00:00Z',Date.now()+900001),[]);
 const runtime={blsSkillsEnabled:true,blsBundleEnabled:true,profileVersion:proof.profileVersion};
 for(const course of ['509474','210549']){
  const rows=skillsOffers(feed,'bls-skills',Date.now(),course,runtime);assert.equal(rows.length,1);
  assert.equal(rows[0].sourceSessionId,row.external_class_id);assert.equal(rows[0].remainingSeats,1);
  assert.equal((await scalar(db,"select skills_session_native_option('bls-skills',$1::jsonb)",[JSON.stringify(rows[0])])).targetSessionId,held.sessionId);
  assert.deepEqual(skillsOffers(feed,'bls-skills',Date.now(),course,{nativePublicationEnabled:true}),[]);
 }
 assert.equal(skillsOffers(feed,'bls-skills',Date.now(),'210549',{...runtime,blsBundleEnabled:false}).length,0);
 assert.equal(skillsOffers(feed,'bls-skills',Date.now(),'509474',{...runtime,blsBundleEnabled:false}).length,1);
 console.log('PASS SQL snapshot -> canonical endpoint -> Python publication/renderer -> browser/server readers -> same canonical remaining seat');
}
