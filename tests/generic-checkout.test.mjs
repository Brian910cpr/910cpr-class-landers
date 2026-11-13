import test from 'node:test';
import assert from 'node:assert/strict';
import {genericCheckout,boundedCheckoutJSON,fullAppointmentSession} from '../supabase/functions/public-registration/generic.mjs';
const key='11111111-1111-4111-8111-111111111111';
function fixture(){
 const calls=[],receipts=new Map();let allowed=true,paid=false,storageFails=false,disabled=false;
 const profile={profile_key:'fixture_generic',version:1,active:true,course_id:'fixture-course-key',display_name:'Fixture class',requirements:[],form_schema:{schemaVersion:'native-checkout.form.v1',inventory_kind:'scheduled_session_v1',max_students:2,fields:[{key:'name',wire:'firstName',type:'text',required:true},{key:'email',wire:'email',type:'email',required:true}],option_groups:[{key:'path',type:'radio',required:true,choices:[{key:'skills',catalog_keys:[]},{key:'online',catalog_keys:['code'],bindings:{learningPath:'online-and-skills'}}]}],default_choices:['skills'],driver_rules:[{driver:'native_order'}]}};
 const catalog={unit_amount:5500,currency:'usd',addons:[{key:'code',unit_amount:4000,active:true}],billing_codes:[{secret:'NEVER-EXPOSE'}]};
 const packet={profile,physicalCourseId:'fixture-course',catalog};
 const deps={now:()=>0,catalog:async()=>({...catalog,addons:catalog.addons.map(a=>({...a,active:!disabled}))}),scheduleSession:async id=>({nativeReady:true,course_id:'fixture-course',start_at:'2031-01-01T14:00:00Z',end_at:'2031-01-01T14:45:00Z',location_name:'Fixture location'}),
  rpc:async(name,args)=>{calls.push({name,args});if(name==='native_checkout_profile')return structuredClone(packet);
   if(name==='native_checkout_release_abandoned')return 0;
   if(name==='skills_session_native_option')return {capacity:2};
   if(name==='native_checkout_receipt'){if(!receipts.has(args.p_key))throw Error('reservation_not_found');return receipts.get(args.p_key);}
   if(name==='reserve_native_checkout_order'){const r={kind:'public_order',orderId:'fixture-order',status:'held',amountCents:args.p_expected_total,currency:'usd',holdExpiresAt:'2031-01-01T13:00:00Z',students:args.p_students.map(()=>({options:{}})),profileSnapshot:{...structuredClone(packet),context:args.p_context,inputs:args.p_inputs}};receipts.set(args.p_key,r);return r;}
   if(name==='native_checkout_payment_allowed')return allowed;
   if(name==='native_checkout_begin_upload')return {id:'intent',state:'pending_storage',storage_path:'private/path'};
   if(name==='native_checkout_finish_upload')return {evidenceStatus:'received',approved:false};throw Error('unexpected_rpc');},
  verify:async()=>{if(paid)receipts.get(key).status='paid';},checkout:async()=>({url:'https://checkout.stripe.com/c/pay/fixture'}),
  store:async()=>{if(storageFails)throw Error('document_storage_pending');},hash:async()=> 'a'.repeat(64)};
 const api=genericCheckout(deps),selection={session:'123456'},student={fields:{name:'Fixture',email:'fixture@example.invalid',amountCents:1},selectedChoices:['skills']};
 return {api,deps,profile,packet,catalog,calls,receipts,selection,student,body:(s=student)=>({selection,profileKey:profile.profile_key,profileVersion:1,students:[s]}),allow:v=>allowed=v,paid:v=>paid=v,failStorage:v=>storageFails=v,disable:v=>disabled=v};
}
test('generic API calculates selected options server-side, snapshots inputs and reuses a lost response without inventory refresh',async()=>{
 const f=fixture(),m=await f.api.model(f.selection);assert.equal(JSON.stringify(m).includes('NEVER-EXPOSE'),false);
 const p=await f.api.reserve(key,f.body({...f.student,selectedChoices:['online']}));assert.equal(p.receipt.amountCents,9500);assert.equal(JSON.stringify(p).includes('fixture@example.invalid'),false);
 const saved=f.calls.find(c=>c.name==='reserve_native_checkout_order').args;assert.equal(saved.p_expected_total,9500);assert.deepEqual(saved.p_students[0].addons,[{key:'code',quantity:1}]);assert.equal(saved.p_students[0].amountCents,undefined);
 f.deps.scheduleSession=async()=>{throw Error('must_not_refresh_on_replay');};
 assert.equal((await f.api.reserve(key,f.body({...f.student,selectedChoices:['online']}))).receipt.orderId,p.receipt.orderId);
 await assert.rejects(f.api.reserve(key,f.body()),/idempotency_conflict/);
 assert.equal(f.calls.filter(c=>c.name==='reserve_native_checkout_order').length,1);
});
test('generic API rejects stale profile, unavailable choices and invalid fields before a database claim',async()=>{
 const f=fixture();await assert.rejects(f.api.reserve(key,{...f.body(),profileVersion:0}),/profile_changed/);
 f.disable(true);await assert.rejects(f.api.reserve(key,f.body({...f.student,selectedChoices:['online']})),/option_unavailable/);
 await assert.rejects(f.api.reserve(key,f.body({...f.student,fields:{name:'Fixture'}})),/required_registration_field_missing/);
 assert.equal(f.calls.filter(c=>c.name==='reserve_native_checkout_order').length,0);
});
test('payment gate permits missing optional upload, blocks required policy and trusts only server-confirmed paid state',async()=>{
 const f=fixture();await f.api.reserve(key,f.body());assert.match((await f.api.checkout(key)).checkoutUrl,/checkout.stripe.com/);
 f.allow(false);await assert.rejects(f.api.checkout(key),/required_document_missing/);
 assert.equal((await f.api.status(key)).receipt.status,'held');f.paid(true);assert.equal((await f.api.status(key)).receipt.status,'paid');
 assert.equal((await f.api.checkout(key)).receipt.status,'paid');
});
test('per-course upload disabled by default; retry after storage failure does not claim received or approve a file',async()=>{
 const f=fixture();await f.api.reserve(key,f.body());const body={studentIndex:0,requirementKey:'completion',file:{type:'application/pdf',base64:btoa('%PDF-fixture')}};
 await assert.rejects(f.api.upload(key,body),/uploads_disabled/);
 f.profile.requirements=[{key:'completion',type:'online_completion',upload_now:true,upload:{enabled:true,max_bytes:100,mime_types:['application/pdf']}}];
 f.failStorage(true);await assert.rejects(f.api.upload(key,body),/document_storage_pending/);
 assert.equal(f.calls.filter(c=>c.name==='native_checkout_finish_upload').length,0);
 f.failStorage(false);assert.deepEqual(await f.api.upload(key,body),{ok:true,evidenceStatus:'received',approved:false});
 await assert.rejects(f.api.upload(key,{...body,studentIndex:2}),/invalid_request/);
});
test('bounded JSON handles chunked bodies and rejects oversized or malformed requests before parsing',async()=>{
 assert.deepEqual(await boundedCheckoutJSON(new Request('https://fixture.invalid',{method:'POST',body:'{"ok":true}'})),{ok:true});
 await assert.rejects(boundedCheckoutJSON(new Request('https://fixture.invalid',{method:'POST',body:'x'.repeat(50)}),10),/request_too_large/);
 await assert.rejects(boundedCheckoutJSON(new Request('https://fixture.invalid',{method:'POST',body:'not json'})),/invalid_request/);
});
test('dated skills selections use a fresh server publication, reject tampering and recheck the lease at save',async()=>{
 const f=fixture(),now=Date.parse('2026-11-06T12:00:00Z');
 f.profile.form_schema.inventory_kind='leased_skills_v1';f.profile.form_schema.allowed_contexts=['cpr-aed'];f.packet.physicalCourseId='509474';
 const feed={schemaVersion:'selector-resolved-availability.v1',pageKey:'heartsaver',generatedAt:new Date(now).toISOString(),validUntil:new Date(now+60000).toISOString(),dates:[{date:'2026-11-10',startTimes:[{startTime:'10:00',courses:[{courseId:'509474',offerType:'dynamic_appointment',publicSelectable:true,durationMinutes:45,schedulerConsumptionMinutes:60,cleanupBufferMinutes:15,occupiedUntil:'2026-11-10T16:00:00Z',instructor:'Fixture Instructor',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'fixture',sourceSessionIds:[],validUntil:new Date(now+60000).toISOString()}]}]}]};
 f.deps.now=()=>now;f.deps.publication=async()=>feed;const api=genericCheckout(f.deps);
 const selection={course:'509474',skillsContext:'cpr-aed',date:'2026-11-10',startTime:'10:00'};
 const model=await api.model(selection);assert.match(model.selection.selectionId,/^skills:/);
 assert.equal(model.session.durationMinutes,45);assert.equal(model.session.capacity,2);
 await assert.rejects(api.model({...selection,startTime:'10:30'}),/session_not_available/);
 await assert.rejects(api.model({...selection,skillsContext:'hsi-blended'}),/invalid_context/);
 await api.reserve(key,{...f.body(),selection:{...model.selection,startsAt:'tampered',amountCents:1}});
 const args=f.calls.find(c=>c.name==='reserve_native_checkout_order').args;
 assert.equal(args.p_offer.startsAt,'2026-11-10T15:00:00.000Z');assert.equal(args.p_offer.consumptionEndsAt,'2026-11-10T16:00:00.000Z');assert.equal(args.p_expected_total,5500);
 feed.validUntil=new Date(now-1).toISOString();
 await assert.rejects(api.reserve('22222222-2222-4222-8222-222222222222',{...f.body(),selection:model.selection}),/session_not_available/);
});
test('two- and four-hour classes retain configured session duration and capacity overrides, distinct from an order limit',async()=>{
 for(const [minutes,capacity,remaining] of [[120,12,12],[240,6,4]]){
  const f=fixture();f.profile.form_schema.max_students=10;
  f.deps.scheduleSession=async()=>({nativeReady:true,course_id:'fixture-course',start_at:'2031-01-01T14:00:00Z',end_at:new Date(Date.parse('2031-01-01T14:00:00Z')+minutes*60000).toISOString(),seats:{capacity,remaining}});
  const model=await f.api.model(f.selection);assert.equal(model.session.durationMinutes,minutes);assert.equal(model.session.capacity,capacity);assert.equal(model.session.remainingSeats,remaining);assert.equal(model.profile.maxStudents,Math.min(10,remaining));
 }
});
test('a course remapped to another profile with the same version cannot silently accept the previously displayed form',async()=>{
 const f=fixture(),display=await f.api.model(f.selection),body={...f.body(),profileKey:display.profile.profileKey};
 f.profile.profile_key='different_profile';
 await assert.rejects(f.api.reserve(key,body),/profile_changed/);
 assert.equal(f.calls.filter(c=>c.name==='reserve_native_checkout_order').length,0);
});
test('storage success followed by a failed receipt commit retries the same intent without claiming approval',async()=>{
 const f=fixture();f.profile.requirements=[{key:'completion',type:'online_completion',upload_now:true,upload:{enabled:true,max_bytes:100,mime_types:['application/pdf']}}];
 const base=f.deps.rpc;let finishAttempts=0,storeAttempts=0;
 f.deps.rpc=async(name,args)=>{if(name==='native_checkout_finish_upload'&&finishAttempts++===0)throw Error('temporary_commit_failure');return base(name,args);};
 f.deps.store=async intent=>{assert.equal(intent.id,'intent');storeAttempts++;};
 const api=genericCheckout(f.deps);await api.reserve(key,f.body());
 const body={studentIndex:0,requirementKey:'completion',file:{type:'application/pdf',base64:btoa('%PDF-fixture')}};
 await assert.rejects(api.upload(key,body),/temporary_commit_failure/);
 assert.equal(f.receipts.get(key).students[0].options.checkoutUploads,undefined);
 const received=await api.upload(key,body);assert.equal(received.evidenceStatus,'received');assert.equal(received.approved,false);assert.equal(storeAttempts,2);
 const starts=f.calls.filter(c=>c.name==='native_checkout_begin_upload');assert.equal(starts.length,2);assert.deepEqual(starts[0].args,starts[1].args);
});
test('switching between courses cannot carry an enabled upload policy into a disabled course receipt',async()=>{
 const f=fixture();
 f.profile.requirements=[{key:'completion',type:'online_completion',upload_now:true,upload:{enabled:true,max_bytes:100,mime_types:['application/pdf']}}];
 const a=structuredClone(f.packet),b=structuredClone(a);b.physicalCourseId='other-course';b.profile.profile_key='other_profile';b.profile.course_id='other-course-key';b.profile.requirements=[];
 const base=f.deps.rpc,profileReads=[];let writes=0;
 f.deps.scheduleSession=async id=>({nativeReady:true,course_id:id==='654321'?'other-course':'fixture-course',start_at:'2031-01-01T14:00:00Z',end_at:'2031-01-01T14:45:00Z'});
 f.deps.rpc=async(name,args)=>{
  if(name==='native_checkout_profile'){profileReads.push(args.p_public_course_id);return structuredClone(args.p_public_course_id==='other-course'?b:a);}
  const r=await base(name,args);
  if(name==='reserve_native_checkout_order'){const packet=args.p_profile_key===b.profile.profile_key?b:a;r.profileSnapshot={...structuredClone(packet),context:args.p_context,inputs:args.p_inputs};}
  return r;
 };
 f.deps.store=async()=>writes++;const api=genericCheckout(f.deps),otherKey='22222222-2222-4222-8222-222222222222';
 await api.reserve(key,f.body());await api.reserve(otherKey,{...f.body(),selection:{session:'654321'},profileKey:b.profile.profile_key});
 const file={studentIndex:0,requirementKey:'completion',file:{type:'application/pdf',base64:btoa('%PDF-fixture')}};
 assert.equal((await api.upload(key,{...file,course:'other-course'})).approved,false);
 await assert.rejects(api.upload(otherKey,{...file,course:'fixture-course'}),/uploads_disabled/);
 assert.deepEqual(profileReads.slice(-2),['fixture-course','other-course']);assert.equal(writes,1);
 assert.equal(f.calls.filter(c=>c.name==='native_checkout_begin_upload').length,1);
});
test('observed payment with a failed finalizer stays processing rather than expired or another payable checkout',async()=>{
 const f=fixture();await f.api.reserve(key,f.body());Object.assign(f.receipts.get(key),{paymentObserved:true,holdExpiresAt:'1969-01-01T00:00:00Z'});
 f.deps.verify=async()=>{throw Error('fixture_finalization_failed');};f.deps.checkout=async()=>{throw Error('must_not_create_another_checkout');};
 assert.equal((await f.api.status(key)).receipt.status,'processing');assert.equal((await f.api.checkout(key)).receipt.status,'processing');
 f.receipts.get(key).status='paid';assert.equal((await f.api.status(key)).receipt.status,'paid');
});
test('unconverted concrete sessions never offer external registration or create a native reservation',async()=>{
 const f=fixture(),legacy='https://coastalcprtraining.enrollware.com/enroll?id=123456';
 f.deps.scheduleSession=async()=>({nativeReady:false,registration_url:legacy});f.deps.fallbackUrl=(_s,id)=>id==='123456'?legacy:null;
 await assert.rejects(f.api.model(f.selection),/native_registration_unavailable/);
 assert.equal(f.calls.some(c=>c.name==='native_checkout_profile'),false);
 await assert.rejects(f.api.reserve(key,f.body()),/native_registration_unavailable/);
 f.deps.fallbackUrl=()=>null;await assert.rejects(f.api.model(f.selection),/native_registration_unavailable/);
});

test('full-course appointment intent resolves only an exact future canonical native class and keeps its own capacity/duration',async()=>{
 const f=fixture(),selection={course:'209806',date:'2031-01-01',startTime:'09:00'};
 const row={external_class_id:'123456',courses:{enrollware_course_id:'209806'},registration_backend:'landerware',record_scope:'operational',visibility:'public',registration_status:'open',status:'scheduled',start_at:'2031-01-01T14:00:00Z',locations:{name:'Fixture location'},people:{display_name:'Fixture instructor'}};
 const now=Date.parse('2030-01-01T00:00:00Z');
 assert.equal(fullAppointmentSession([row],selection,now),'123456');
 for(const changed of [{course:'359474'},{course:'210549'},{course:'509474'},{course:'unknown'},{course:''},{date:'2031-01-02'},{startTime:'10:00'},{location:'wrong'},{instructor:'wrong'},{skillsContext:'bls-skills'}])assert.throws(()=>fullAppointmentSession([row],{...selection,...changed},now),/invalid_session|session_not_available/);
 for(const rows of [[],[row,row],[{...row,registration_backend:'enrollware'}],[{...row,registration_status:'closed'}],[{...row,record_scope:'test'}],[{...row,visibility:'private'}]])assert.throws(()=>fullAppointmentSession(rows,selection,now),/session_not_available/);
 assert.throws(()=>fullAppointmentSession([row],selection,Date.parse('2032-01-01T00:00:00Z')),/session_not_available/);
 f.deps.appointmentSession=async s=>fullAppointmentSession([row],s,now);
 f.deps.scheduleSession=async()=>({nativeReady:true,course_id:'209806',start_at:row.start_at,end_at:'2031-01-01T18:00:00Z',seats:{capacity:7,remaining:5}});
 const api=genericCheckout(f.deps),m=await api.model(selection);
 assert.equal(m.selection.session,'123456');assert.equal(m.session.durationMinutes,240);assert.equal(m.session.capacity,7);
 f.deps.scheduleSession=async()=>({nativeReady:true,course_id:'359474'});
 await assert.rejects(api.model(selection),/invalid_session/);
 f.deps.scheduleSession=async()=>({nativeReady:false});f.deps.fallbackUrl=()=> 'https://coastalcprtraining.enrollware.com/enroll?id=123456';
 await assert.rejects(api.model(selection),/session_not_available/);
});

test('leased full BLS materialization uses fresh server source at both display and claim, not supplied times or skills rules',async()=>{
 const f=fixture(),now=Date.parse('2030-01-01T00:00:00Z'),selection={course:'209806',date:'2030-01-02',startTime:'10:00'};
 f.deps.now=()=>now;f.deps.fullEnabled=()=>true;f.deps.appointmentSession=async()=>{throw Error('session_not_available');};
 const course={courseId:'209806',offerType:'dynamic_appointment',publicSelectable:true,instructor:'Brian Ennis',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'fixture-full',sourceSessionIds:[],durationMinutes:120,schedulerConsumptionMinutes:150,cleanupBufferMinutes:30,setupBufferMinutes:0,appointmentDayId:123,occupiedUntil:'2030-01-02T17:30:00Z',validUntil:new Date(now+600000).toISOString()};
 let payload={pageKey:'bls',schemaVersion:'selector-resolved-availability.v1',generatedAt:new Date(now).toISOString(),validUntil:new Date(now+600000).toISOString(),dates:[{date:'2030-01-02',startTimes:[{startTime:'10:00',courses:[course]}]}]};
 f.deps.publication=async()=>structuredClone(payload);const rpc=f.deps.rpc;
 f.deps.rpc=async(n,a)=>n==='native_full_course_option'?{capacity:6}:rpc(n,a);
 const api=genericCheckout(f.deps),m=await api.model(selection);assert.equal(m.session.durationMinutes,120);assert.equal(m.session.capacity,6);
 await api.reserve(key,{...f.body(),selection:{...m.selection,startsAt:'2000-01-01T00:00:00Z',capacity:999}});
 f.deps.fullEnabled=()=>false;await assert.rejects(api.model(selection),/native_registration_unavailable/);f.deps.fullEnabled=()=>true;
 const saved=f.calls.find(c=>c.name==='reserve_native_checkout_order').args;assert.equal(saved.p_external_id,null);assert.equal(saved.p_offer.startsAt,'2030-01-02T15:00:00.000Z');assert.equal(saved.p_offer.authority,'native-full-course.v1');
 payload.validUntil=new Date(now-1).toISOString();await assert.rejects(api.model(m.selection),/calendar_refresh_required/);
});


test('other configured course families resolve existing appointments through the same profile without dynamic creation',async()=>{
 const f=fixture();let lookup=0;
 f.packet.physicalCourseId='241108';f.catalog.course_id='241108';
 const originalRpc=f.deps.rpc;f.deps.rpc=async(name,args)=>name==='native_advanced_existing_session_ready'?true:originalRpc(name,args);f.api=genericCheckout(f.deps);
 f.deps.appointmentSession=async selection=>{lookup++;assert.equal(selection.course,'241108');return 'canonical-acls-fixture';};
 f.deps.scheduleSession=async()=>({nativeReady:true,course_id:'241108',start_at:'2031-01-01T14:00:00Z',end_at:'2031-01-01T18:00:00Z',seats:{capacity:12,remaining:7}});
 const model=await f.api.model({course:'241108',date:'2031-01-01',startTime:'09:00'});
 assert.equal(lookup,1);assert.equal(model.selection.session,'canonical-acls-fixture');
 assert.equal(model.session.durationMinutes,240);assert.equal(model.session.capacity,12);assert.equal(model.session.remainingSeats,7);
 assert.ok(f.calls.some(c=>c.name==='native_checkout_profile'&&c.args.p_public_course_id==='241108'));
 f.deps.appointmentSession=async()=>{throw Error('session_not_available');};
 await assert.rejects(f.api.model({course:'241108',date:'2031-01-01',startTime:'09:00'}),/native_registration_unavailable/);
 f.deps.appointmentSession=async()=> 'canonical-acls-fixture';
 f.deps.scheduleSession=async()=>({nativeReady:false,course_id:'241108'});
 await assert.rejects(f.api.model({course:'241108',date:'2031-01-01',startTime:'09:00'}),/session_not_available/);
});


test('post-commit trigger sees a durable reservation and cannot erase it on mail failure',async()=>{
 const f=fixture(),notified=[];f.deps.afterCommit=async id=>{assert.ok(f.receipts.has(key));notified.push(id);throw Error('private mail failure');};
 const saved=await f.api.reserve(key,f.body());assert.equal(saved.receipt.status,'held');assert.deepEqual(notified,['fixture-order']);
 assert.equal((await f.api.reserve(key,f.body())).receipt.status,'held');assert.equal(notified.length,2);assert.equal(f.calls.filter(c=>c.name==='reserve_native_checkout_order').length,1);
 await assert.rejects(f.api.reserve(key,{...f.body(),students:[]}));assert.equal(notified.length,2);
});
test('paid generic status and checkout retries nudge only the committed public order',async()=>{
 const f=fixture(),notified=[];await f.api.reserve(key,f.body());f.deps.afterCommit=async id=>notified.push(id);
 assert.equal((await f.api.status(key)).receipt.status,'held');assert.equal(notified.length,0);
 f.paid(true);assert.equal((await f.api.status(key)).receipt.status,'paid');assert.deepEqual(notified,['fixture-order']);
 assert.equal((await f.api.checkout(key)).receipt.status,'paid');assert.equal(notified.length,2);
});


test('async backend policy is awaited; native publication gate is independent and claims revalidate stable ID without date lookup',async()=>{
 const f=fixture(),now=Date.parse('2030-01-01T00:00:00Z');
 f.deps.now=()=>now;let policy={materializationEnabled:false,nativePublicationEnabled:false},policyCalls=0,publications=0;
 f.deps.fullPolicy=async()=>{await Promise.resolve();policyCalls++;return policy;};
 f.deps.appointmentSession=async s=>{assert.ok(s.date,'selection ID claims must not use the date-only canonical lookup');throw Error('session_not_available');};
 const course={courseId:'209806',offerType:'dynamic_appointment',authority:'native-full-course.v2',proofObservedAt:new Date(now-60000).toISOString(),nativeScopeId:'brian-shipyard-b.v1',selectionId:'native-full:'+'a'.repeat(64),publicSelectable:true,instructor:'Brian Ennis',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'fixture-full',sourceSessionIds:[],durationMinutes:120,schedulerConsumptionMinutes:150,cleanupBufferMinutes:30,setupBufferMinutes:0,occupiedUntil:'2030-01-02T17:30:00Z',validUntil:new Date(now+600000).toISOString()};
 let payload={pageKey:'bls',schemaVersion:'selector-resolved-availability.v1',generatedAt:new Date(now).toISOString(),validUntil:new Date(now+600000).toISOString(),dates:[{date:'2030-01-02',startTimes:[{startTime:'10:00',courses:[course]}]}]};
 f.deps.publication=async()=>{publications++;return structuredClone(payload);};const rpc=f.deps.rpc;
 f.deps.rpc=async(n,a)=>n==='native_full_course_option'?{capacity:6}:rpc(n,a);
 const api=genericCheckout(f.deps),selection={course:'209806',date:'2030-01-02',startTime:'10:00'};
 await assert.rejects(api.model(selection),/native_registration_unavailable/);assert.equal(publications,0);
 policy={materializationEnabled:true,nativePublicationEnabled:false};await assert.rejects(api.model(selection),/session_not_available/);
 policy={materializationEnabled:true,nativePublicationEnabled:true};const m=await api.model(selection);assert.equal(m.selection.selectionId,course.selectionId);assert.equal(m.session.capacity,6);
 await api.reserve(key,{...f.body(),selection:m.selection});assert.equal(publications,3);assert.equal(policyCalls,4);
 const offer=f.calls.find(c=>c.name==='reserve_native_checkout_order').args.p_offer;assert.equal(offer.authority,'native-full-course.v2');assert.equal(offer.proofObservedAt,course.proofObservedAt);assert.equal(Object.hasOwn(offer,'appointmentDayId'),false);
 policy={materializationEnabled:false,nativePublicationEnabled:false};await api.reserve(key,{...f.body(),selection:m.selection});assert.equal(policyCalls,4,'nonce replay precedes policy/publication fetch');
 f.deps.fullPolicy=async()=>{throw Error('backend_unavailable');};await assert.rejects(api.model(selection),/backend_unavailable/);
});
