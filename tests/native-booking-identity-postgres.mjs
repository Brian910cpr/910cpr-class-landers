// Native original booking protection, isolated PostgreSQL 17, synthetic data only.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import * as bls from './native-bls-admission-proof.mjs';
import * as skills from './native-bls-skills-proof.mjs';
import {createPg,quote} from './helpers/native-booking-postgres.mjs';
import {settlePublicOrder} from '../supabase/functions/public-registration/public-order-routing.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const full=process.argv.includes('--full'),optional=process.argv.includes('--optional');
const hs=full?await import('./native-heartsaver-admission-proof.mjs'):null;
const ped=full?await import('./native-pediatric-admission-proof.mjs'):null;
const load=p=>readFileSync(root+'/'+p,'utf8');
const migration=load('supabase/migrations/20261112023203_native_order_booking_identity.sql');
const {scalar,service}=bls;const db=await createPg(root);let n=60000,day=5;
const results=[];const record=(name,details={})=>{results.push({name,...details});console.log('PASS',name,JSON.stringify(details));};
const row=id=>scalar(db,'select to_jsonb(o) from landerware_public_orders o where id=$1',[id]);
const count=id=>scalar(db,"select jsonb_build_object('registrations',(select count(*) from landerware_public_order_students where order_id=$1 and registration_id is not null),'messages',(select count(*) from landerware_messages where idempotency_key like 'public-order-%:'||$1::text||'%'))",[id]);
const retire=c=>db.query("update class_sessions set status='cancelled',registration_status='closed' where id=$1",[c.sessionId]);
async function adopt(id){await db.query("update class_sessions set external_reconciliation=jsonb_build_object('complete',true,'active_external_registration_ids','[]'::jsonb,'active_registration_count',0,'source_observed_at',now()) where id=$1",[id]);const p=await scalar(db,'select native_session_authority_snapshot($1)',[id]);return scalar(db,'select native_session_authority_record($1,gen_random_uuid(),$2,$3,true)',[id,p.fingerprint,p.revision]);}
async function seed(course){let offer,sql,args;day+=2;
 if(course==='351632'){const p=await ped.makePediatricSession(db,{external:String(990000000+(++n))});sql=ped.claimSQL;args=ped.request(p.external,++n);}
 else if(course==='509474'){offer=await skills.makeOffer(db,day);sql=skills.claimSQL;args=skills.request(offer,++n);}
 else if(['209806','359474'].includes(course)){offer=await bls.makeBlsOffer(db,course,day);offer.validUntil=await scalar(db,"select now()+interval '10 minutes'");sql=bls.claimSQL;args=bls.request(course,null,offer,++n);}
 else {offer=await hs.makeHeartsaverOffer(db,course,day);sql=hs.claimSQL;args=hs.request(course,null,offer,++n);}
 return {...await service(db,()=>scalar(db,sql,args)),offer,sql,args};
}
async function seated(course,c){const ext=await scalar(db,'select external_class_id from class_sessions where id=$1',[c.sessionId]);let sql,args;
 if(course==='351632'){sql=ped.claimSQL;args=ped.request(ext,++n);}
 else if(course==='509474'){sql=skills.claimSQL;args=skills.request(await skills.seatedOffer(db,c.offer,c.sessionId),++n);}
 else if(['209806','359474'].includes(course)){sql=bls.claimSQL;args=bls.request(course,ext,{},++n);}
 else {sql=hs.claimSQL;args=hs.request(course,ext,{},++n);}
 return {...await service(db,()=>scalar(db,sql,args)),sql,args};
}
async function bind(c){const o=await row(c.orderId);const e={id:'cs_synthetic_identity_'+(++n),mode:'payment',payment_status:'paid',amount_total:o.total,currency:o.currency,metadata:{landerware_order_id:o.id},payment_intent:'pi_synthetic_identity_'+n};await db.query('update landerware_public_orders set stripe_checkout_session_id=$2 where id=$1',[o.id,e.id]);return e;}
const rpc=(name,a)=>service(db,()=>scalar(db,`select ${name}($1,$2,$3::jsonb)`,[a.p_order_id,a.p_stripe_payment_intent_id,JSON.stringify(a.p_evidence)]));
const settle=async(c,e)=>settlePublicOrder(rpc,await row(c.orderId),e,e);
const receipt=async(c,e)=>db.serviceQuery('select native_checkout_record_payment($1,$2,$3::jsonb)',[c.orderId,e.payment_intent,JSON.stringify(e)]);
async function unchanged(c,before){const after=await row(c.orderId);for(const key of ['native_booking_snapshot','registration_profile_snapshot','subtotal','discount_total','total','currency','course_id','class_session_id'])assert.deepEqual(after[key],before[key],key);}
let controller;
try {
 if(full)await ped.setupPediatricAdmission(db,{enabled:true,optional});else await bls.setupBlsAdmission(db);
 if(!full)for(const file of ['20261111225500_native_full_offer_wallclock_lease.sql','20261111233000_native_skills_offer_wallclock_lease.sql','20261111233504_native_bls_skills_publication_disabled.sql'])await db.exec(load('supabase/migrations/'+file));
 {await db.exec(load('supabase/migrations/20261110213818_native_plain_skills_profile_draft_only.sql'));
 await db.exec(`update courses set course_key='skills-session-only',registration_profile_key='native_skills_shared' where enrollware_course_id='509474';update landerware_registration_profiles set active=true,version=2 where profile_key='native_skills_shared';update native_skills_publication_policy set enabled=true,publication_enabled=true,verified=true,evidence='LOCAL SYNTHETIC ONLY';insert into instructor_qualifications(instructor_id,course_id,qualification_key,status) select p.id,c.id,'skills-session-policy.v1','active' from people p cross join courses c where p.person_key='brian' and c.enrollware_course_id='509474';`);await skills.enableSkills(db);}
 await db.exec(load('tests/helpers/native-booking-paid-fixture-acl.sql'));
 if(process.env.NATIVE_BOOKING_TEST_HOSTED_FINALIZER){await db.exec(readFileSync(process.env.NATIVE_BOOKING_TEST_HOSTED_FINALIZER,'utf8'));assert.equal(await scalar(db,"select md5(prosrc) from pg_proc where oid='native_checkout_finalize_order(uuid,text,jsonb)'::regprocedure"),'00a178e4e6c1f757c31ca502399bcf8b');}
 const old=await seed('209806'),oldPaid=await seed('359474'),oldSkills=await seed('509474');assert.equal((await row(oldSkills.orderId)).total,5500);const oldPaidEvidence=await bind(oldPaid);assert.equal((await settle(oldPaid,oldPaidEvidence)).status,'paid');
 const preservedSQL="select jsonb_build_object('orders',(select jsonb_agg(to_jsonb(o)-'native_booking_snapshot' order by id) from landerware_public_orders o),'sessions',(select jsonb_agg(to_jsonb(s) order by id) from class_sessions s),'prices',(select jsonb_agg(to_jsonb(c) order by course_id) from landerware_registration_catalog c),'authority',(select jsonb_agg(to_jsonb(e) order by id) from landerware_session_authority_events e))";
 const preserved=await scalar(db,preservedSQL),funcSQL="select p.oid::regprocedure::text signature,md5(prosrc) body,proacl::text acl from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and proname not in('native_checkout_finalize_order','native_checkout_booking_identity','native_checkout_capture_booking_identity','native_checkout_booking_identity_error') order by 1";
 const funcs=(await db.query(funcSQL)).rows,tableACL=(await db.query("select oid::regclass::text name,relacl::text acl from pg_class where relnamespace='public'::regnamespace and relkind='r' order by 1")).rows;
 await db.exec(migration);
 assert.deepEqual(await scalar(db,preservedSQL),preserved);assert.deepEqual((await db.query(funcSQL)).rows,funcs);assert.deepEqual((await db.query("select oid::regclass::text name,relacl::text acl from pg_class where relnamespace='public'::regnamespace and relkind='r' order by 1")).rows,tableACL);
 for(const fn of ['native_checkout_booking_identity(class_sessions)','native_checkout_capture_booking_identity()','native_checkout_booking_identity_error(landerware_public_orders,class_sessions)']){assert.equal(await scalar(db,'select prosecdef from pg_proc where oid=$1::regprocedure',[fn]),false);for(const role of ['anon','authenticated'])assert.equal(await scalar(db,"select has_function_privilege($1,$2,'execute')",[role,fn]),false);assert.equal(await scalar(db,"select has_function_privilege('service_role',$1,'execute')",[fn]),true);}
 assert.equal((await row(old.orderId)).native_booking_snapshot,null);assert.equal((await settle(oldPaid,oldPaidEvidence)).idempotentReplay,true);
 const oldEvidence=await bind(old);assert.equal((await settle(old,oldEvidence)).reason,'native_booking_identity_unproven');assert.deepEqual(await count(old.orderId),{messages:0,registrations:0});assert.equal((await row(old.orderId)).payment_evidence.payment_status,'paid');
 await assert.rejects(service(db,()=>db.query("update landerware_public_orders set native_booking_snapshot='{}' where id=$1",[old.orderId])),/native_booking_snapshot_immutable/);
 await db.query("update landerware_public_orders set status='refunded' where id=$1",[oldPaid.orderId]);assert.equal((await settle(oldPaid,oldPaidEvidence)).status,'refunded');
 const oldSkillsE=await bind(oldSkills);assert.equal((await settle(oldSkills,oldSkillsE)).reason,'native_booking_identity_unproven');assert.equal((await row(oldSkills.orderId)).total,5500);assert.deepEqual(await count(oldSkills.orderId),{messages:0,registrations:0});await retire(oldSkills);
 await retire(old);await retire(oldPaid);record('migration preserves records, amounts, authority, functions and table ACLs; old paid replay and unproven review');
 const courses=full?['209806','359474','209809','344085','509474','351632']:['209806','359474','509474'];
 for(const course of courses){
  // Normal and late finalization plus full occupancy from legitimate held seats.
  const c=await seed(course),before=await row(c.orderId);assert.equal(before.native_booking_snapshot.schemaVersion,'native-booking.v1');assert.equal(before.native_booking_snapshot.provenance.generatedWitness?.identity_hash!=null,course!=='351632');
  assert.equal((await service(db,()=>scalar(db,c.sql,c.args))).orderId,c.orderId);assert.deepEqual((await row(c.orderId)).native_booking_snapshot,before.native_booking_snapshot);
  const second=await seated(course,c);const e=await bind(c),e2=await bind(second);assert.equal((await settle(second,e2)).status,'paid');assert.equal((await settle(c,e)).status,'paid');await unchanged(c,before);
  await db.query("update class_sessions set start_at=start_at+interval '1 day',end_at=end_at+interval '1 day' where id=$1",[c.sessionId]);assert.equal((await settle(c,e)).idempotentReplay,true);await retire(c);
  const late=await seed(course);await db.query("update landerware_public_orders set status='expired',hold_expires_at=now()-interval '1 hour' where id=$1",[late.orderId]);const lateEvidence=await bind(late);assert.equal((await settle(late,lateEvidence)).status,'paid');await retire(late);
  record('unchanged identity, other student settlement, late recovery, replay',{course});
  for(const path of course==='351632'?['adopted_seated','adopted_then_rereviewed']:['generated_dynamic','generated_seated','adopted_seated','adopted_then_rereviewed']){
   let c=await seed(course);
   if(path!=='generated_dynamic'&&course!=='351632'){await db.query("update landerware_public_orders set status='cancelled' where id=$1",[c.orderId]);if(path.startsWith('adopted')){await db.query("update class_sessions set source='manual' where id=$1",[c.sessionId]);await adopt(c.sessionId);}c=await seated(course,c);}
   const before=await row(c.orderId),e=await bind(c);
   await db.query("update class_sessions set start_at=start_at+interval '1 day',end_at=end_at+interval '1 day',consumption_start_at=consumption_start_at+interval '1 day',consumption_end_at=consumption_end_at+interval '1 day' where id=$1",[c.sessionId]);
   if(path==='adopted_then_rereviewed')await adopt(c.sessionId);
   const result=await settle(c,e);assert.equal(result.status,'payment_review');assert.equal(result.reason,path==='adopted_seated'?'native_authority_identity_changed':'native_booking_identity_changed');
   const after=await row(c.orderId);assert.equal(await scalar(db,'select native_checkout_unresolved_payment(o) from landerware_public_orders o where id=$1',[c.orderId]),true);assert.equal(after.payment_evidence.payment_status,'paid');assert.equal(after.payment_evidence.seat_hold_protected,true);assert.deepEqual(await count(c.orderId),{messages:0,registrations:0});await unchanged(c,before);await retire(c);record('date drift rejected',{course,path,reason:result.reason});
  }
 }

 if(!full){
 // A completely occupied class still includes this customer's legitimate hold.
 const filled=await seed('209806'),filledBefore=await row(filled.orderId),filledE=await bind(filled);
 const capacity=await scalar(db,'select max_students from class_sessions where id=$1',[filled.sessionId]);
 for(let i=1;i<capacity;i++){const other=await seated('209806',filled);const otherE=await bind(other);assert.equal((await settle(other,otherE)).status,'paid');}
 assert.equal((await scalar(db,'select landerware_public_seat_state($1)',[filled.sessionId])).remaining,0);
 assert.equal((await settle(filled,filledE)).status,'paid');await unchanged(filled,filledBefore);await retire(filled);record('all other seats filled without invalidating original hold');
 const noSeat=await seed('209806');await db.query("update landerware_public_orders set status='expired',hold_expires_at=now()-interval '1 hour' where id=$1",[noSeat.orderId]);
 for(let i=0;i<capacity;i++){const other=await seated('209806',noSeat);const otherE=await bind(other);assert.equal((await settle(other,otherE)).status,'paid');}
 const noSeatE=await bind(noSeat);assert.equal((await settle(noSeat,noSeatE)).reason,'paid_seat_unavailable');assert.deepEqual(await count(noSeat.orderId),{messages:0,registrations:0});await retire(noSeat);record('existing late-payment capacity gate remains enforced');
 const mismatch=await seed('209806'),mismatchE=await bind(mismatch);await assert.rejects(settle(mismatch,{...mismatchE,amount_total:mismatchE.amount_total+1}),/payment_evidence_mismatch/);assert.deepEqual(await count(mismatch.orderId),{messages:0,registrations:0});await retire(mismatch);record('existing payment-evidence amount gate remains enforced');
 // Single-field identity changes, separately, not a coarse session fingerprint.
 for(const [label,change] of [
  ['start',"start_at=start_at+interval '1 minute'"],['end',"end_at=end_at+interval '1 minute'"],
  ['course',"course_id=(select id from courses where enrollware_course_id='359474')"],
  ['location',"location_id=(select id from locations where location_key='synthetic-other')"],
  ['instructor',"lead_instructor_id=(select id from people where person_key='synthetic-other')"],
  ['resource',"resource_id='ffffffff-1111-4111-8111-111111111111'"],['timezone',"timezone='America/Chicago'"]]){
  if(label==='location')await db.exec("insert into locations(location_key,name,address_line1) values('synthetic-other','Synthetic venue','999 Other St')");
  if(label==='instructor')await db.exec("insert into people(person_key,display_name) values('synthetic-other','Synthetic Instructor')");
  const c=await seed('209806'),e=await bind(c);await db.query(`update class_sessions set ${change} where id=$1`,[c.sessionId]);assert.equal((await settle(c,e)).reason,'native_booking_identity_changed');assert.deepEqual(await count(c.orderId),{messages:0,registrations:0});await retire(c);record('material field drift rejected',{label});
 }
 const address=await seed('209806'),addressEvidence=await bind(address),location=await scalar(db,'select location_id from class_sessions where id=$1',[address.sessionId]);
 await db.query("update locations set address_line1='Synthetic changed address' where id=$1",[location]);assert.equal((await settle(address,addressEvidence)).reason,'native_booking_identity_changed');await retire(address);record('same-location address edit rejected');
 // Cosmetic names, capacity and live price changes are not accepted identity.
 const cosmetic=await seed('209806'),cosmeticBefore=await row(cosmetic.orderId),cosmeticE=await bind(cosmetic);
 await db.exec("update people set display_name='Brian Ennis ' where person_key='brian';update locations set name='Cosmetic venue name' where location_key='910cpr-office-shipyard';update courses set name='Cosmetic BLS name',base_price=1 where enrollware_course_id='209806';update landerware_registration_catalog set unit_amount=100 where course_id='209806';");
 assert.equal((await settle(cosmetic,cosmeticE)).status,'paid');await unchanged(cosmetic,cosmeticBefore);await retire(cosmetic);
 await db.exec("update people set display_name='Brian Ennis' where person_key='brian';update courses set base_price=75 where enrollware_course_id='209806';update landerware_registration_catalog set unit_amount=7500 where course_id='209806';");record('cosmetic labels and new prices do not invalidate durable order');
 const immutable=await seed('209806');await assert.rejects(service(db,()=>db.query("update landerware_public_orders set native_booking_snapshot='{}' where id=$1",[immutable.orderId])),/native_booking_snapshot_immutable/);await assert.rejects(service(db,()=>db.query("update landerware_public_orders set class_session_id=$2 where id=$1",[immutable.orderId,old.sessionId])),/native_booking_binding_immutable/);
 const forged=await service(db,()=>scalar(db,"insert into landerware_public_orders select (jsonb_populate_record(null::landerware_public_orders,to_jsonb(o)||jsonb_build_object('id',gen_random_uuid(),'recovery_token',gen_random_uuid(),'idempotency_key','synthetic-forgery','stripe_checkout_session_id',null,'native_booking_snapshot',jsonb_build_object('forged',true)))).* from landerware_public_orders o where id=$1 returning native_booking_snapshot",[immutable.orderId]));assert.equal(forged.schemaVersion,'native-booking.v1');assert.equal(forged.forged,undefined);await retire(immutable);record('immutable snapshot/binding and forged input overwritten');
 // Current references are read after acquiring the row lock, not from a snapshot
 // established before the wait. Newer authority cannot amend original consent.
 const race=await seed('209806'),raceE=await bind(race);await receipt(race,raceE);
 controller=await db.controller('booking-drift-controller');await controller.send(`begin;select id from class_sessions where id=${quote(race.sessionId)} for update;update class_sessions set start_at=start_at+interval '1 day',end_at=end_at+interval '1 day' where id=${quote(race.sessionId)};`);
 const pending=db.serviceQuery('select native_checkout_finalize_order($1,$2,$3::jsonb)',[race.orderId,raceE.payment_intent,JSON.stringify(raceE)],{label:'booking-drift-finalizer'});
 let observed;for(let i=0;i<100;i++){observed=(await db.adminQuery("select a.xact_start,pg_blocking_pids(a.pid) blockers from pg_stat_activity a where application_name='booking-drift-finalizer'")).rows[0];if(observed?.blockers.length)break;await new Promise(r=>setTimeout(r,20));}assert.ok(observed?.blockers.length);await controller.send('commit;');await controller.close();controller=null;
 assert.equal((await pending).rows[0].native_checkout_finalize_order.reason,'native_booking_identity_changed');assert.deepEqual(await count(race.orderId),{messages:0,registrations:0});await retire(race);record('real class-lock wait sees committed drift');
 const referenceWait=await seed('209806'),referenceE=await bind(referenceWait);await receipt(referenceWait,referenceE);
 controller=await db.controller('booking-reference-controller');await controller.send("begin;update locations set name=name where location_key='910cpr-office-shipyard';");
 const referenceResult=await db.serviceQuery('select native_checkout_finalize_order($1,$2,$3::jsonb)',[referenceWait.orderId,referenceE.payment_intent,JSON.stringify(referenceE)],{label:'booking-reference-finalizer'});
 assert.equal(referenceResult.rows[0].native_checkout_finalize_order.reason,'native_booking_identity_unavailable');assert.deepEqual(await count(referenceWait.orderId),{messages:0,registrations:0});assert.equal((await row(referenceWait.orderId)).payment_evidence.payment_status,'paid');await controller.send('rollback;');await controller.close();controller=null;await retire(referenceWait);record('concurrent canonical-reference edit fails safely into durable review');
 // A local fixture moves a class near its start BEFORE the next standard
 // existing-session checkout. The real creator captures this original identity.
 const clockSeed=await seed('209806');await db.query("update landerware_public_orders set status='cancelled' where id=$1",[clockSeed.orderId]);
 await db.query("update class_sessions set start_at=t.starts,end_at=t.starts+interval '120 minutes',consumption_start_at=t.starts,consumption_end_at=t.starts+interval '150 minutes' from (select clock_timestamp()+interval '5 seconds' starts)t where id=$1",[clockSeed.sessionId]);
 const clockOrder=await seated('209806',clockSeed);
 const clockE=await bind(clockOrder);await receipt(clockOrder,clockE);controller=await db.controller('booking-clock-controller');await controller.send(`begin;select id from class_sessions where id=${quote(clockOrder.sessionId)} for update;`);
 const clockPending=db.serviceQuery('select native_checkout_finalize_order($1,$2,$3::jsonb)',[clockOrder.orderId,clockE.payment_intent,JSON.stringify(clockE)],{label:'booking-clock-finalizer'});
 for(let i=0;i<100;i++){observed=(await db.adminQuery("select a.xact_start,s.start_at,pg_blocking_pids(a.pid) blockers from pg_stat_activity a cross join class_sessions s where application_name='booking-clock-finalizer' and s.id=$1",[clockOrder.sessionId])).rows[0];if(observed?.blockers.length)break;await new Promise(r=>setTimeout(r,20));}assert.ok(observed?.blockers.length);assert.ok(Date.parse(observed.xact_start)<Date.parse(observed.start_at));
 await new Promise(r=>setTimeout(r,Math.max(0,Date.parse(observed.start_at)-Date.now())+200));await controller.send('commit;');await controller.close();controller=null;
 assert.equal((await clockPending).rows[0].native_checkout_finalize_order.reason,'session_not_open');assert.equal((await row(clockOrder.orderId)).payment_evidence.payment_status,'paid');assert.deepEqual(await count(clockOrder.orderId),{messages:0,registrations:0});record('real lock wait across class start retains receipt, no admission');
 }
 console.log('IDENTITY_PROOF',JSON.stringify({full,optional,checks:results.length,serviceTransactions:db.proofs.length}));
 if(process.env.NATIVE_BOOKING_REPORT)writeFileSync(process.env.NATIVE_BOOKING_REPORT,JSON.stringify({full,optional,results,serviceTransactions:db.proofs.length},null,2));
}finally{if(controller)await controller.close();await db.close();}
