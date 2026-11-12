// Synthetic fixtures only. No hosted requests, credentials, sending or activation.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {setupBlsAdmission,scalar,service} from './native-bls-admission-proof.mjs';
export {scalar,service};
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
export const migration=load('supabase/migrations/20261111233000_native_skills_offer_wallclock_lease.sql');
export const contexts=['cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended'];
export const claimSQL='select reserve_native_checkout_order($1,\'native_skills_shared\',2,$2,null,$3::jsonb,$4::jsonb,$5::jsonb,5500)';
export const footprint=db=>scalar(db,`select jsonb_build_object(
 'sessions',(select coalesce(jsonb_agg(to_jsonb(s) order by id),'[]') from class_sessions s),
 'workspaces',(select coalesce(jsonb_agg(to_jsonb(w) order by id),'[]') from landerware_sessions w),
 'witnesses',(select coalesce(jsonb_agg(to_jsonb(w) order by class_session_id),'[]') from native_checkout_generated_sessions w),
 'orders',(select coalesce(jsonb_agg(to_jsonb(o) order by id),'[]') from landerware_public_orders o),
 'students',(select coalesce(jsonb_agg(to_jsonb(s) order by id),'[]') from landerware_public_order_students s),
 'inventory',(select coalesce(jsonb_agg(to_jsonb(i) order by id),'[]') from product_inventory_units i),
 'customers',(select coalesce(jsonb_agg(to_jsonb(c) order by id),'[]') from customers c),
 'registrations',(select coalesce(jsonb_agg(to_jsonb(r) order by id),'[]') from registrations r),
 'registrationOrders',(select coalesce(jsonb_agg(to_jsonb(r) order by id),'[]') from registration_orders r),
 'legacyReceipts',(select coalesce(jsonb_agg(to_jsonb(r) order by idempotency_key),'[]') from skills_session_claim_receipts r),
 'messages',(select coalesce(jsonb_agg(to_jsonb(m) order by id),'[]') from landerware_messages m))`);
export async function setupSkillsLease(db,{full=false,apply=true}={}){
 await setupBlsAdmission(db,{full});
 await db.exec(load('supabase/migrations/20261111225500_native_full_offer_wallclock_lease.sql'));
 await db.exec(load('supabase/migrations/20261110213818_native_plain_skills_profile_draft_only.sql'));
 await db.exec(`update courses set course_key='skills-session-only',registration_profile_key='native_skills_shared' where enrollware_course_id='509474';
  update landerware_registration_profiles set active=true,version=2 where profile_key='native_skills_shared';
  update native_skills_publication_policy set enabled=true,publication_enabled=true,verified=true,evidence='LOCAL SYNTHETIC ONLY';
  update skills_session_context_config set qualification_course_id=course_id,policy_evidence='skills-session-policy.v1' where context_key='cpr-aed';
  insert into instructor_qualifications(instructor_id,course_id,qualification_key,status)
   select p.id,c.id,'skills-session-policy.v1','active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id='509474';
  insert into skills_session_context_config(context_key,course_id,qualification_course_id,enabled,capacity_policy_verified,policy_evidence)
   select k,c.id,c.id,true,true,'skills-session-policy.v1' from courses c cross join unnest(array['first-aid-cpr-aed','arc-blended','hsi-blended']) k where c.enrollware_course_id='509474';
  grant select,update on product_inventory_units to service_role;
  grant select,insert,update on customers,registrations,registration_orders,landerware_messages to service_role;`);
 const signature='materialize_native_skills_checkout(text,jsonb,text)';
 const definitions=()=>db.query("select p.oid::regprocedure::text as signature,md5(p.prosrc) as body from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname<>'materialize_native_skills_checkout' order by 1").then(r=>r.rows);
 const configuration=()=>scalar(db,"select jsonb_build_object('courses',(select jsonb_agg(to_jsonb(c) order by id) from courses c),'profiles',(select jsonb_agg(to_jsonb(p) order by profile_key) from landerware_registration_profiles p),'catalog',(select jsonb_agg(to_jsonb(c) order by course_id) from landerware_registration_catalog c),'contexts',(select jsonb_agg(to_jsonb(c) order by context_key) from skills_session_context_config c),'policy',(select jsonb_agg(to_jsonb(p)) from native_skills_publication_policy p),'delivery',(select jsonb_agg(to_jsonb(p)) from landerware_checkout_delivery_config p))");
 const before=await definitions(),config=await configuration();
 if(apply){
  const original=await scalar(db,'select pg_get_functiondef($1::regprocedure)',[signature]);
  await db.exec(original.replace('begin\n','begin\n -- unexpected source drift\n'));
  await assert.rejects(db.exec(migration),/native_skills_offer_wallclock_source_drift/);await db.exec('rollback');
  await db.exec(original.replaceAll('\n','\r\n'));await db.exec(migration);
  assert.deepEqual(await definitions(),before);assert.deepEqual(await configuration(),config);
  for(const role of ['anon','authenticated'])assert.equal(await scalar(db,"select has_function_privilege($1,$2,'execute')",[role,signature]),false);
  assert.equal(await scalar(db,'select prosecdef from pg_proc where oid=$1::regprocedure',[signature]),false);
 }
 return {full,definitions,before,configuration,config};
}
export async function makeOffer(db,context,day,{legacy=false,leaseMs=null}={}){
 const offer=await scalar(db,"select skills_test.offer('lease-'||$1::text,$2,-540)||jsonb_build_object('context',$1::text,'authority','native-skills-publication.v1','nativeScopeId','brian-shipyard-b.v1','nativeOfferId','native-skills:'||repeat('a',64),'selectionId','skills:native-skills:'||repeat('a',64)||':'||$1::text,'proofObservedAt',now(),'qualificationPolicy','skills-session-policy.v1','capacity',2,'instructor','Brian Ennis')",[context,day]);
 if(legacy){for(const key of ['authority','nativeScopeId','nativeOfferId','proofObservedAt','qualificationPolicy','capacity'])delete offer[key];offer.selectionId='skills:synthetic-legacy:'+context+':'+day;}
 if(leaseMs!==null)offer.validUntil=new Date(Date.now()+leaseMs).toISOString();
 return offer;
}
export function request(context,offer,n){
 const wire={firstName:'Synthetic',lastName:'Fixture',email:`lease-${n}@example.invalid`,phone:'',onlineCompleted:true,learningPath:'skills-only',skillsContext:context};
 return [`${String(n).padStart(8,'0')}-1111-4111-8111-111111111111`,context,JSON.stringify(offer),JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:['skills_only']}])];
}
export const claim=(db,args)=>service(db,()=>scalar(db,claimSQL,args));
export async function seatedOffer(db,offer,sessionId){
 const s=await scalar(db,'select to_jsonb(s) from class_sessions s where id=$1',[sessionId]);
 const booking=(await scalar(db,'select native_scheduling_seat_snapshot($1)',[sessionId])).skillsBooking;
 assert.ok(booking);const id=s.external_class_id;
 return {...offer,authority:'native-skills-seated.v1',offerType:'seated_class',sourceSessionId:id,availabilityBlockId:'seated:'+id,sourceSessionIds:[id],
  nativeOfferId:'native-skills-seated:'+id,selectionId:'skills:native-skills-seated:'+id+':'+offer.context,
  profileVersion:booking.profileVersion,identityWitness:booking.identityWitness,remainingSeats:booking.remaining};
}
export async function proveBasics(db,fixture){
 let n=4000;
 for(const [i,context] of contexts.entries()){
  const offer=await makeOffer(db,context,40+i),args=request(context,offer,++n),first=await claim(db,args);assert.equal(first.status,'held');
  const before=await footprint(db),expired={...offer,validUntil:'2020-01-01T00:00:00Z'};
  await assert.rejects(claim(db,request(context,expired,++n)),/session_not_available/);assert.deepEqual(await footprint(db),before);
  const replay=[...args];replay[2]=JSON.stringify(expired);assert.equal((await claim(db,replay)).orderId,first.orderId);assert.deepEqual(await footprint(db),before);
  const seated=await seatedOffer(db,offer,first.sessionId),second=await claim(db,request(context,seated,++n));assert.equal(second.sessionId,first.sessionId);
  assert.equal((await scalar(db,'select native_scheduling_seat_snapshot($1)',[first.sessionId])).remaining,0);
  console.log('PASS '+context+': new and existing native seats, expired-before-call rollback, nonce replay');
 }
 // Legacy marker-free publication has no native 24-hour admission rule.
 const legacy=await makeOffer(db,'cpr-aed',0,{legacy:true});
 const start=await scalar(db,"select date_trunc('minute',now()+interval '2 hours')");
 legacy.startsAt=new Date(start).toISOString();legacy.endsAt=new Date(Date.parse(start)+45*60000).toISOString();legacy.consumptionEndsAt=new Date(Date.parse(start)+60*60000).toISOString();
 legacy.localStart=await scalar(db,"select to_char($1::timestamptz at time zone 'America/New_York','YYYY-MM-DD\"T\"HH24:MI')",[legacy.startsAt]);
 assert.equal((await claim(db,request('cpr-aed',legacy,++n))).status,'held','legacy near-term eligibility retained');
 const excluded=await makeOffer(db,'bls-skills',80);
 assert.equal(await scalar(db,'select skills_session_native_option($1,$2::jsonb)',['bls-skills',JSON.stringify(excluded)]),null);
 assert.equal(await scalar(db,"select enabled from skills_session_context_config where context_key='bls-skills'"),false);
 assert.deepEqual(await fixture.definitions(),fixture.before);assert.deepEqual(await fixture.configuration(),fixture.config);
}
