// Isolated synthetic proof only; consumes the independent BLS admission fixture.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {setupBlsAdmission,makeBlsOffer,scalar,service,request,claimSQL} from './native-bls-admission-proof.mjs';
export {scalar,service};
export const leaseMigration=readFileSync(new URL('../supabase/migrations/20261111225500_native_full_offer_wallclock_lease.sql',import.meta.url),'utf8');
export async function setupFullOfferLease(db,{full=false}={}){
 await setupBlsAdmission(db,{full});
 // Fixture-only fulfillment ACLs for exercising unchanged callbacks as the
 // nonsuperuser service role; these are not new deployment grants.
 await db.exec('grant select,update on product_inventory_units to service_role;grant select,insert,update on customers,registrations,registration_orders,landerware_messages to service_role;');
 const untouched=['reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)',
  'native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)','native_checkout_record_payment(uuid,text,jsonb)',
  'native_checkout_finalize_order(uuid,text,jsonb)','native_checkout_release_abandoned(timestamptz,timestamptz)',
  'native_full_course_option(text,jsonb)','native_bls_session_booking_ready(class_sessions)','native_scheduling_seat_snapshot(uuid)'];
 const definitions=()=>Promise.all(untouched.map(fn=>scalar(db,'select pg_get_functiondef($1::regprocedure)',[fn])));
 const configuration=()=>scalar(db,"select jsonb_build_object('courses',(select jsonb_agg(to_jsonb(c) order by id) from courses c),'profiles',(select jsonb_agg(to_jsonb(p) order by profile_key) from landerware_registration_profiles p),'catalog',(select jsonb_agg(to_jsonb(c) order by course_id) from landerware_registration_catalog c),'base',(select jsonb_agg(to_jsonb(p)) from native_full_course_policy p),'scope',(select jsonb_agg(to_jsonb(p)) from native_full_course_public_policy p))");
 const before=await definitions(),config=await configuration(),signature='materialize_native_full_checkout(text,jsonb,text)';
 const prior=await scalar(db,'select pg_get_functiondef($1::regprocedure)',[signature]);
 await db.exec(prior.replace('begin\n','begin\n -- unreviewed change\n'));
 await assert.rejects(db.exec(leaseMigration),/native_full_offer_wallclock_source_drift/);await db.exec('rollback');
 assert.deepEqual(await definitions(),before);await db.exec(prior.replaceAll('\n','\r\n'));
 await db.exec(leaseMigration);assert.deepEqual(await definitions(),before);assert.deepEqual(await configuration(),config);
 for(const role of ['anon','authenticated'])assert.equal(await scalar(db,"select has_function_privilege($1,$2,'execute')",[role,signature]),false);
 assert.equal(await scalar(db,'select prosecdef from pg_proc where oid=$1::regprocedure',[signature]),false);
 assert.deepEqual((await db.query("select rolsuper,rolbypassrls from pg_roles where rolname='service_role'")).rows[0],{rolsuper:false,rolbypassrls:true});
 if(full){
  // Explicit local-only capacities/prices. No real readiness is inferred.
  await db.exec(`update courses set registration_profile_key='native_heartsaver_209809_draft',base_price=95 where enrollware_course_id='209809';
   update courses set registration_profile_key='native_heartsaver_344085_draft',base_price=70 where enrollware_course_id='344085';
   update landerware_registration_profiles set active=true where profile_key in('native_heartsaver_209809_draft','native_heartsaver_344085_draft');
   update landerware_registration_catalog set active=true where course_id in('209809','344085');
   update native_heartsaver_full_course_policy set max_students=2,capacity_evidence='LOCAL FIXTURE ONLY',price_evidence='LOCAL FIXTURE ONLY',
    enabled=true,verified=true,publication_enabled=true,evidence='LOCAL FIXTURE ONLY',
    source_qualification_id=(select id from instructor_qualifications where qualification_key='aha-bls-instructor:209806');`);
 }
 return {full,courses:full?['209806','359474','209809','344085']:['209806','359474'],definitions,before};
}
export async function makeLeaseOffer(db,course,day){
 const offer=await makeBlsOffer(db,course,day);
 if(['209809','344085'].includes(course)){
  offer.coursePolicyKey=`heartsaver-full:${course}.v1`;
  offer.endsAt=new Date(Date.parse(offer.startsAt)+(course==='344085'?90:120)*60000).toISOString();
  offer.consumptionEndsAt=new Date(Date.parse(offer.startsAt)+(course==='344085'?105:150)*60000).toISOString();
 }
 return offer;
}
export function leaseRequest(course,offer,n){
 const args=request(course,null,offer,n);
 if(['209809','344085'].includes(course)){
  args[1]=`native_heartsaver_${course}_draft`;
  const wire={firstName:'Synthetic',lastName:'Fixture',email:`lease-${course}-${n}@example.invalid`,phone:'2025550100',addons:[]};
  args[4]=JSON.stringify([wire]);args[5]=JSON.stringify([{wire,selectedChoices:[]}]);
 }
 args.push(course==='209809'?9500:course==='344085'?7000:7500);
 return args;
}
export const leaseClaimSQL=claimSQL.replace(',7500)',',$7)');
export const claimLease=(db,args)=>service(db,()=>scalar(db,leaseClaimSQL,args));
export const footprint=db=>scalar(db,`select jsonb_build_object(
 'sessions',(select coalesce(jsonb_agg(to_jsonb(s) order by id),'[]') from class_sessions s),
 'workspaces',(select coalesce(jsonb_agg(to_jsonb(w) order by id),'[]') from landerware_sessions w),
 'witnesses',(select coalesce(jsonb_agg(to_jsonb(w) order by class_session_id),'[]') from native_checkout_generated_sessions w),
 'orders',(select coalesce(jsonb_agg(to_jsonb(o) order by id),'[]') from landerware_public_orders o),
 'students',(select coalesce(jsonb_agg(to_jsonb(s) order by id),'[]') from landerware_public_order_students s),
 'inventory',(select coalesce(jsonb_agg(to_jsonb(i) order by id),'[]') from product_inventory_units i),
 'registrations',(select coalesce(jsonb_agg(to_jsonb(r) order by id),'[]') from registrations r),
 'messages',(select coalesce(jsonb_agg(to_jsonb(m) order by id),'[]') from landerware_messages m))`);
export async function proveLeaseBasics(db,fixture){
 let n=2200;
 for(const [i,course] of fixture.courses.entries()){
  const offer=await makeLeaseOffer(db,course,40+i),args=leaseRequest(course,offer,++n);
  const valid=await claimLease(db,args);assert.equal(valid.status,'held');
  assert.equal(await scalar(db,'select count(*) from native_checkout_generated_sessions where class_session_id=$1',[valid.sessionId]),1);
  const before=await footprint(db),expired={...offer,validUntil:'2020-01-01T00:00:00Z'};
  await assert.rejects(claimLease(db,leaseRequest(course,expired,++n)),/session_not_available/);assert.deepEqual(await footprint(db),before);
  const replay=[...args];replay[3]=JSON.stringify(expired);
  assert.equal((await claimLease(db,replay)).orderId,valid.orderId);assert.deepEqual(await footprint(db),before);
  console.log(`PASS ${course}: service-role valid admission, expired-before-call rollback, durable prior nonce replay`);
 }
 assert.deepEqual(await fixture.definitions(),fixture.before);
}
