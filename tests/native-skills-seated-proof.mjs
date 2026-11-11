// Synthetic local proof shared by PGlite and the guarded PostgreSQL17 harness.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {preProfileFiles,profileRuntime,fullCourseMigration} from './helpers/native-checkout-migration-plan.mjs';
import {publishedOffers,localStart} from '../supabase/functions/registration-reschedule/policy.mjs';
import {skillsOffers} from '../supabase/functions/skills-session-reservation/policy.mjs';
const {loadEndpoint}=createRequire(import.meta.url)('./helpers/canonical_demand_endpoint.cjs');
const browser=createRequire(import.meta.url)('../docs/assets/resolved-selector-availability.js');
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
export async function proveSkillsSeats(db,race){
 const sql=async(s,a=[])=>Object.values((await db.query(s,a)).rows[0]||{})[0];
 for(const f of preProfileFiles)await db.exec(load(f));
 await db.exec("update courses set course_key='skills-session-only' where enrollware_course_id='509474'");
 for(const f of [profileRuntime,fullCourseMigration,'supabase/migrations/20261111195655_native_full_course_v2_policy.sql',
  'supabase/migrations/20261110231103_native_checkout_generated_session_lifecycle.sql','supabase/migrations/20261111200908_native_full_course_lifecycle_hooks.sql',
  'supabase/migrations/20261111185724_native_session_authority_cutover.sql','supabase/migrations/20261111200810_native_scheduling_seat_snapshot.sql'])await db.exec(load(f));
 await db.exec("insert into landerware_confirmation_templates values('native-checkout-profile-v1','Fixture','Fixture','cloudflare',false)");
 await db.exec(load('supabase/migrations/20261110213818_native_plain_skills_profile_draft_only.sql'));
 await db.exec(load('supabase/migrations/20261111202622_native_skills_publication_guard.sql'));
 assert.equal((await sql('select native_skills_publication_runtime_policy()')).nativePublicationEnabled,false);
 assert.equal(await sql("select active from landerware_registration_profiles where profile_key='native_skills_shared'"),false);
 await db.exec(`update native_skills_publication_policy set enabled=true,publication_enabled=true,verified=true,evidence='LOCAL SYNTHETIC ONLY';
  update landerware_registration_profiles set active=true,version=2 where profile_key='native_skills_shared';
  update courses set registration_profile_key='native_skills_shared' where enrollware_course_id='509474';
  update landerware_registration_catalog set active=true where course_id='509474';
  insert into people(person_key,display_name) values('brian','Brian Ennis');
  update skills_session_context_config set qualification_course_id=course_id,policy_evidence='skills-session-policy.v1';
  insert into instructor_qualifications(instructor_id,course_id,qualification_key,status)
   select p.id,c.id,'skills-session-policy.v1','active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id='509474';
  insert into skills_session_context_config(context_key,course_id,qualification_course_id,enabled,capacity_policy_verified,policy_evidence)
   select k,c.id,c.id,true,true,'skills-session-policy.v1' from courses c cross join unnest(array['first-aid-cpr-aed','arc-blended','hsi-blended']) k where c.enrollware_course_id='509474';`);
 const dynamic=await sql("select skills_test.offer('native-seated',40,-540)||jsonb_build_object('authority','native-skills-publication.v1','nativeScopeId','brian-shipyard-b.v1','nativeOfferId','native-skills:'||repeat('a',64),'selectionId','skills:native-skills:'||repeat('a',64)||':cpr-aed','proofObservedAt',now(),'qualificationPolicy','skills-session-policy.v1','capacity',2,'instructor','Brian Ennis')");
 const key=n=>`${String(n).padStart(8,'0')}-1111-4111-8111-111111111111`;
 const request=(n,context,offer)=>{
  const wire={firstName:'Synthetic',lastName:'Fixture',email:`fixture-${n}@example.invalid`,phone:'',onlineCompleted:true,learningPath:'skills-only',skillsContext:context};
  return [key(n),'native_skills_shared',2,context,null,JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:['skills_only']}]),5500];
 };
 const claimSQL='select reserve_native_checkout_order($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8::jsonb,$9)';
 const first=await sql(claimSQL,request(1,'cpr-aed',dynamic));
 assert.equal(first.status,'held');assert.equal(first.amountCents,5500);
 const sid=first.sessionId;
 const snapshot=()=>sql('select native_scheduling_seat_snapshot($1)',[sid]);
 await db.exec(load('tests/helpers/native-full-service-role-acl.sql'));
 for(const role of ['anon','authenticated'])assert.equal(await sql("select has_function_privilege($1,$2,'EXECUTE')",[role,'public.native_checkout_unresolved_payment(public.landerware_public_orders)']),false);
 // Schema-only profile fixture omits its normal reader ACL (not a production grant).
 await db.exec('grant select on landerware_registration_profiles to service_role');
 await db.exec('set role service_role');assert.equal(await sql('select current_user'),'service_role');assert.equal((await snapshot()).remaining,1);await db.exec('reset role');
 let state=await snapshot();assert.equal(state.holds,1);assert.equal(state.remaining,1);assert.equal(state.publicBooking,null);assert.equal(state.skillsBooking.remaining,1);
 const row=await sql(`select to_jsonb(s)||jsonb_build_object('courses',(select jsonb_build_object('course_key',course_key,'name',name) from courses where id=s.course_id),
  'landerware_sessions',(select jsonb_agg(w) from landerware_sessions w where w.class_session_id=s.id),
  'native_checkout_generated_sessions',(select jsonb_agg(w) from native_checkout_generated_sessions w where w.class_session_id=s.id)) from class_sessions s where id=$1`,[sid]);
 const endpoint=loadEndpoint(()=>{throw Error('network forbidden')});
 const projected=endpoint.projectDemand(row,state);assert.equal(projected.active_registration_count,1);
 const stamp=new Date().toISOString();
 const pipeline=spawnSync(process.env.SKILLS_TEST_PYTHON||'python',['-B','-m','tests.helpers.native-skills-seated-publication',stamp],{cwd:fileURLToPath(new URL('../',import.meta.url)),input:JSON.stringify(projected),encoding:'utf8',timeout:30000});
 assert.equal(pipeline.status,0,pipeline.stderr||String(pipeline.error));
 const feeds=JSON.parse(pipeline.stdout),offers={};
 const partial=structuredClone(feeds.heartsaver);partial.dates[0].startTimes[0].courses[0].skillsContexts=['cpr-aed'];
 assert.deepEqual(skillsOffers(partial,'first-aid-cpr-aed',Date.now(),'509474',{nativePublicationEnabled:true}),[]);
 assert.deepEqual(browser.datesForPublication(partial.dates,partial.validUntil,Date.now(),'first-aid-cpr-aed'),[]);
 assert.equal(browser.datesForPublication(partial.dates,partial.validUntil,Date.now(),'cpr-aed').length,1);
 for(const [page,context] of [['heartsaver','cpr-aed'],['heartsaver','first-aid-cpr-aed'],['arc','arc-blended'],['hsi','hsi-blended']]){
  const found=skillsOffers(feeds[page],context,Date.now(),'509474',{nativePublicationEnabled:true});assert.equal(found.length,1);offers[context]=found[0];
  assert.equal(found[0].sourceSessionId,row.external_class_id);assert.equal(found[0].remainingSeats,1);
  assert.deepEqual(skillsOffers(feeds[page],context,Date.now()+900001,'509474',{nativePublicationEnabled:true}),[]);
  assert.deepEqual(browser.datesForPublication(feeds[page].dates,'2099-01-01T00:00:00Z',Date.now()+900001),[]);
 }
 const seated=offers['arc-blended'];assert.notEqual(seated.selectionId,offers['cpr-aed'].selectionId);
 const opt=(o=seated,c='arc-blended')=>sql('select skills_session_native_option($1,$2::jsonb)',[c,JSON.stringify(o)]);
 assert.equal((await opt()).targetSessionId,sid);
 for(const patch of [{authority:'native-skills-publication.v1'},{authority:null},{profileVersion:1},{identityWitness:'a'.repeat(32)},
  {sourceSessionId:'lw-00000000-0000-0000-0000-000000000000'},{sourceSessionIds:[]},{remainingSeats:99},
  {proofObservedAt:new Date(Date.now()-16*60000).toISOString()},{validUntil:new Date(Date.now()+20*60000).toISOString()}]){
  assert.equal(await opt({...seated,...patch}),null,JSON.stringify(patch));
 }
 for(const [disable,restore] of [
  ["update landerware_registration_catalog set active=false where course_id='509474'","update landerware_registration_catalog set active=true where course_id='509474'"],
  ["update landerware_registration_profiles set active=false,version=3 where profile_key='native_skills_shared'","update landerware_registration_profiles set active=true,version=4 where profile_key='native_skills_shared'"],
  ["update instructor_qualifications set status='revoked' where qualification_key='skills-session-policy.v1'","update instructor_qualifications set status='active' where qualification_key='skills-session-policy.v1'"],
  ["update instructor_qualifications set expires_at=now()+interval '1 day' where qualification_key='skills-session-policy.v1'","update instructor_qualifications set expires_at=null where qualification_key='skills-session-policy.v1'"],
 ]){await db.exec(disable);assert.equal((await snapshot()).skillsBooking,null);assert.equal(await opt(),null);await db.exec(restore);}
 // Restore test version with actual version guard intentionally bypassed only by
 // forward-compatible refreshed selection and claim arguments, never profile edit.
 const version=await sql("select version from landerware_registration_profiles where profile_key='native_skills_shared'");
 for(const o of Object.values(offers))o.profileVersion=version;
 assert.equal((await opt()).targetSessionId,sid);
 await db.query("update skills_session_context_config set enabled=false where context_key='arc-blended'");
 assert.ok(!(await snapshot()).skillsBooking.skillsContexts.includes('arc-blended'));assert.equal(await opt(),null);
 assert.ok(await sql('select skills_session_native_option($1,$2::jsonb)',['hsi-blended',JSON.stringify(offers['hsi-blended'])]));
 await db.query("update skills_session_context_config set enabled=true where context_key='arc-blended'");
 // Paid expired hold remains occupied; ambiguous payment never releases its seat/geometry.
 await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute',payment_evidence='{\"payment_status\":\"paid\",\"seat_hold_protected\":true}' where id=$1",[first.orderId]);
 assert.equal((await snapshot()).holds,1);assert.equal((await snapshot()).skillsBooking.remaining,1);assert.equal(await sql('select native_checkout_release_abandoned($1,$2)',[dynamic.startsAt,dynamic.consumptionEndsAt]),0);
 await db.query("update landerware_public_orders set payment_evidence='{\"unknown\":true}' where id=$1",[first.orderId]);
 state=await snapshot();assert.equal(state.holds,1);assert.equal(state.skillsBooking,null);assert.equal(await opt(),null);assert.equal(await sql('select native_checkout_release_abandoned($1,$2)',[dynamic.startsAt,dynamic.consumptionEndsAt]),0);
 await db.query("update landerware_public_orders set hold_expires_at=now()+interval '10 minutes',payment_evidence='{}' where id=$1",[first.orderId]);
 const second=request(2,'arc-blended',offers['arc-blended']);second[2]=version;
 const third=request(3,'hsi-blended',offers['hsi-blended']);third[2]=version;
 if(race)await race(claimSQL,second,third,sid);else{assert.equal((await sql(claimSQL,second)).sessionId,sid);await assert.rejects(sql(claimSQL,third),/session_not_available|insufficient_seats/);}
 state=await snapshot();assert.equal(state.holds,2);assert.equal(state.remaining,0);assert.equal(state.skillsBooking,null);
 assert.equal(await sql('select count(*)::int from class_sessions where id=$1',[sid]),1);
 assert.equal(await sql('select count(*)::int from landerware_public_orders where class_session_id=$1',[sid]),2);
 // Abandoned unpaid capacity releases, then dynamic selection reuses same class.
 await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute',payment_evidence='{}' where class_session_id=$1",[sid]);
 assert.equal(await sql('select native_checkout_release_abandoned($1,$2)',[dynamic.startsAt,dynamic.consumptionEndsAt]),1);
 await assert.rejects(snapshot(),/native_generated_authority_unavailable/);
 await assert.rejects(opt(),/native_generated_authority_unavailable/);
 const reopen=request(4,'cpr-aed',dynamic);reopen[2]=version;
 assert.equal((await sql(claimSQL,reopen)).sessionId,sid);assert.equal((await snapshot()).skillsBooking.remaining,1);
 await db.query("update class_sessions set source_location_label='Changed identity' where id=$1",[sid]);
 await assert.rejects(snapshot(),/native_generated_authority_unavailable/);await assert.rejects(opt(),/native_generated_authority_unavailable/);
 await proveNativePaymentLiability(db);
 console.log('PASS native skills: first real hold, atomic remaining seat, three provider feeds/four contexts, same-session second claim, rejected third, expiry/revocation/identity/paid/unknown/cleanup safeguards');
}

async function proveNativePaymentLiability(db){
 const scalar=async(s,a=[])=>Object.values((await db.query(s,a)).rows[0]||{})[0];
 await db.exec(`insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price)
  values('aha-bls-provider','Synthetic BLS','209806',120,0,12,75),('aha-bls-provider-renewal','Synthetic renewal','359474',120,0,12,75);
  insert into landerware_registration_catalog(course_id,course_name,unit_amount,currency,addons,billing_codes,active)
  values('209806','Synthetic BLS',7500,'usd','[]','[]',true),('359474','Synthetic renewal',7500,'usd','[]','[]',true)
  on conflict(course_id) do update set unit_amount=7500,currency='usd',active=true;`);
 await db.exec(load('supabase/migrations/20261111185535_native_bls_profiles_inactive_unbound.sql'));
 await db.exec(`update courses set registration_profile_key='native_bls_209806_v1' where enrollware_course_id='209806';
  update landerware_registration_profiles set active=true,version=2 where profile_key='native_bls_209806_v1';
  insert into instructor_qualifications(instructor_id,course_id,status) select p.id,c.id,'active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id='209806';
  update native_full_course_policy set enabled=true,verified=true,evidence='LOCAL SYNTHETIC';
  update native_full_course_public_policy set enabled=true,publication_enabled=true,verified=true,evidence='LOCAL SYNTHETIC';`);
 for(const course of ['509474','209806']){
  const skills=course==='509474',context=skills?'cpr-aed':'',profile=skills?'native_skills_shared':'native_bls_209806_v1';
  const version=await scalar('select version from landerware_registration_profiles where profile_key=$1',[profile]);
  const offer=await scalar(`select skills_test.offer('payment-cycle',${skills?43:70})||jsonb_build_object(
   'authority','${skills?'native-skills-publication.v1':'native-full-course.v2'}','proofObservedAt',now(),'nativeScopeId','brian-shipyard-b.v1',
   'courseNumber','${course}','instructor','Brian Ennis','selectionId','${skills?'skills:native-skills:'+('b'.repeat(64))+':cpr-aed':'native-full:'+('d'.repeat(64))}',
   'endsAt',(skills_test.offer('payment-cycle',${skills?43:70})->>'startsAt')::timestamptz+interval '${skills?45:120} minutes',
   'consumptionEndsAt',(skills_test.offer('payment-cycle',${skills?43:70})->>'startsAt')::timestamptz+interval '${skills?60:150} minutes')`);
  if(skills)Object.assign(offer,{nativeOfferId:'native-skills:'+'b'.repeat(64),qualificationPolicy:'skills-session-policy.v1',capacity:2});
  const request=n=>{
   const wire={firstName:'Synthetic',lastName:'Fixture',email:`payment-${course}-${n}@example.invalid`,phone:'2025550100',addons:[],
    ...(skills?{onlineCompleted:true,learningPath:'skills-only',skillsContext:context}:{manualChoice:'own-copy'})};
   return [`${course.padStart(8,'0')}-000${n}-4000-8000-111111111111`,profile,version,context,null,JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:[skills?'skills_only':'customer_supplied_manual']}]),skills?5500:7500];
  };
  const claimSQL='select reserve_native_checkout_order($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8::jsonb,$9)';
  const first=await scalar(claimSQL,request(1));
  const state=()=>scalar('select native_scheduling_seat_snapshot($1)',[first.sessionId]);
  const initial=await state();assert.equal(initial.holds,1);assert.equal(initial.registered,0);assert.equal(initial.remaining,skills?1:5);
  const pay=async(order,n,late=false)=>{
   await db.query(`update landerware_public_orders set stripe_checkout_session_id=$2${late?",hold_expires_at=now()-interval '1 minute'":''} where id=$1`,[order.orderId,`cs_${course}_${n}`]);
   const evidence={id:`cs_${course}_${n}`,mode:'payment',payment_status:'paid',amount_total:skills?5500:7500,currency:'usd',metadata:{landerware_order_id:order.orderId}};
   await scalar('select native_checkout_record_payment($1,$2,$3::jsonb)',[order.orderId,`pi_${course}_${n}`,JSON.stringify(evidence)]);
   return evidence;
  };
  const finalize=(order,n,evidence)=>scalar('select native_checkout_finalize_order($1,$2,$3::jsonb)',[order.orderId,`pi_${course}_${n}`,JSON.stringify(evidence)]);
  const e1=await pay(first,1);assert.equal((await finalize(first,1,e1)).status,'paid');
  let snapshot=await state();assert.equal(snapshot.registered,1);assert.equal(snapshot.holds,0);assert.equal(snapshot.remaining,skills?1:5);
  assert.equal((await finalize(first,1,e1)).idempotentReplay,true);assert.equal((await state()).registered,1);
  const second=await scalar(claimSQL,request(2));assert.equal(second.sessionId,first.sessionId);
  const email=`payment-${course}-2@example.invalid`;
  await db.query("insert into customers(first_name,last_name,email) values('Different','Identity',$1)",[email]);
  // The BLS adversarial case is physically full: five paid registrations plus
  // one late-paid unresolved seat, not merely a conservative empty-class veto.
  if(!skills)for(let n=5;n<=8;n++){
   const filler=await scalar(claimSQL,request(n));const evidence=await pay(filler,n);
   assert.equal((await finalize(filler,n,evidence)).status,'paid');
  }
  const committed=skills?1:5;
  const e2=await pay(second,2,true);assert.equal((await finalize(second,2,e2)).status,'payment_review');
  const saved=await scalar('select to_jsonb(o) from (select status,payment_evidence,reconciliation_error from landerware_public_orders where id=$1) o',[second.orderId]);
  assert.equal(saved.status,'expired');assert.equal(saved.payment_evidence.payment_status,'paid');assert.equal(saved.reconciliation_error,'identity_review_required');
  snapshot=await state();assert.equal(snapshot.registered,committed);assert.equal(snapshot.holds,1);assert.equal(snapshot.remaining,0);
  assert.equal(snapshot.publicBooking,null);assert.equal(snapshot.skillsBooking,null);
  await assert.rejects(scalar(claimSQL,request(3)),/payment_reconciliation_required|session_not_available/);
  if(!skills){const concrete=request(4);concrete[4]=first.profileSnapshot.selection.externalId;concrete[5]='{}';await assert.rejects(scalar(claimSQL,concrete),/payment_reconciliation_required/);}
  assert.equal(await scalar('select count(*)::int from landerware_public_orders where class_session_id=$1',[first.sessionId]),skills?2:6);
  assert.equal(await scalar('select native_checkout_release_abandoned($1,$2)',[offer.startsAt,offer.consumptionEndsAt]),0);
  const transfer=await rescheduleFixture(db,first.sessionId,course);
  const blocked=await scalar('select registration_reschedule_context($1,$2)',[transfer.token,transfer.ids]);
  assert.deepEqual(blocked.options,[],'current context cannot offer a payment-review liability even with an accepted stale publication');
  await assert.rejects(scalar('select confirm_registration_reschedule($1,$2,$3)',[transfer.token,first.sessionId,transfer.ids]),/session_not_available/);
  assert.equal(await scalar('select class_session_id from registrations where id=$1',[transfer.registration]),transfer.origin);
  assert.equal(await scalar('select used_at from registration_reschedule_links where token_sha256=$1',[transfer.token]),null);
  assert.equal((await state()).registered,committed);assert.equal((await state()).holds,1);
  // Staff resolves the identity issue; the same paid callback recovers once.
  await db.query("update customers set first_name='Synthetic',last_name='Fixture' where email=$1",[email]);
  assert.equal((await finalize(second,2,e2)).status,'paid');snapshot=await state();
  assert.equal(snapshot.registered,committed+1);assert.equal(snapshot.holds,0);assert.equal(snapshot.remaining,0);
  // Ordinary permitted self-rescheduling still transfers once and replays.
  const shifted=ms=>new Date(Date.parse(ms)+86400000).toISOString();
  const normalOffer={...offer,startsAt:shifted(offer.startsAt),endsAt:shifted(offer.endsAt),consumptionEndsAt:shifted(offer.consumptionEndsAt)};
  normalOffer.localStart=localStart(normalOffer.startsAt);
  if(!skills)normalOffer.selectionId='native-full:'+'e'.repeat(64);
  const normal=await scalar(skills?'select materialize_native_skills_checkout($1,$2::jsonb,$3)':'select materialize_native_full_checkout($1,$2::jsonb,$3)',[skills?context:course,JSON.stringify(normalOffer),'synthetic-normal-transfer']);
  const normalIds=[normal.externalId];
  const available=await scalar('select registration_reschedule_context($1,$2)',[transfer.token,normalIds]);
  assert.equal(available.options.length,1);assert.equal(available.options[0].id,normal.targetSessionId);
  const moved=await scalar('select confirm_registration_reschedule($1,$2,$3)',[transfer.token,normal.targetSessionId,normalIds]);
  assert.equal(moved.sessionId,normal.targetSessionId);assert.equal(moved.idempotentReplay,false);
  assert.equal((await scalar('select confirm_registration_reschedule($1,$2,$3)',[transfer.token,normal.targetSessionId,normalIds])).idempotentReplay,true);
  assert.equal((await scalar('select native_scheduling_seat_snapshot($1)',[normal.targetSessionId])).registered,1);
  assert.equal((await finalize(second,2,e2)).idempotentReplay,true,'self-reschedule checks never alter payment callback recovery');
  // Explicit refunded state is terminal in the existing payment contract. A
  // cancelled label with retained paid evidence is not evidence of a refund.
  await db.query("update landerware_public_orders set status='cancelled' where id=$1",[second.orderId]);
  assert.equal(await scalar('select native_checkout_unresolved_payment(o) from landerware_public_orders o where id=$1',[second.orderId]),true);
  await db.query("update landerware_public_orders set status='refunded' where id=$1",[second.orderId]);
  assert.equal(await scalar('select native_checkout_unresolved_payment(o) from landerware_public_orders o where id=$1',[second.orderId]),false);
  assert.equal((await finalize(second,2,e2)).status,'refunded');
  assert.equal((await state()).registered,committed+1,'refund does not silently cancel an active registration');
  assert.equal((await state()).holds,0);
  console.log(`PASS ${course}: late-paid review blocks stale checkout and public reschedule context/confirm; normal transfer/replay and payment recovery remain valid`);
 }
}

async function rescheduleFixture(db,targetSession,course){
 const scalar=async(s,a=[])=>Object.values((await db.query(s,a)).rows[0]||{})[0];
 const target=await scalar('select to_jsonb(s) from class_sessions s where id=$1',[targetSession]);
 const origin=await scalar(`insert into class_sessions(source,status,record_scope,course_id,start_at,end_at,consumption_start_at,consumption_end_at,lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id)
  select 'manual','scheduled','operational',course_id,start_at-interval '1 day',end_at-interval '1 day',consumption_start_at-interval '1 day',consumption_end_at-interval '1 day',lead_instructor_id,location_id,max_students,'landerware','public','open',$2 from class_sessions where id=$1 returning id`,[targetSession,'fixture-transfer-origin-'+course]);
 const customer=await scalar("insert into customers(first_name,last_name,email) values('Transfer','Student',$1) returning id",['transfer-'+course+'@example.invalid']);
 const registration=await scalar("insert into registrations(customer_id,class_session_id,status,registration_source) values($1,$2,'registered','landerware_native_checkout') returning id",[customer,origin]);
 const token=(course==='509474'?'a':'b').repeat(64);
 await scalar("select issue_registration_reschedule_link($1,$2,now()+interval '1 day','Local synthetic transfer',null)",[registration,token]);
 const local=localStart(target.start_at);
 const stale={generatedAt:new Date().toISOString(),validUntil:new Date(Date.now()+900000).toISOString(),dates:[{date:local.slice(0,10),startTimes:[{startTime:local.slice(11),courses:[{courseId:course,offerType:'seated_class',authority:'native-session-booking.v1',registrationUrl:'/register/?session='+target.external_class_id}]}]}]};
 const ids=publishedOffers(stale,course).map(o=>o.externalId);
 assert.deepEqual(ids,[target.external_class_id],'the public publication adapter accepts the old seated route; SQL must independently deny it');
 return {token,ids,origin,registration};
}
