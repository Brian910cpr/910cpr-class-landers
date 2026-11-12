import {fullCourseOffers,fullCoursePage} from './full-course.mjs';
import {normalizeCheckoutProfile,checkoutSelection,uploadPolicies,conditionApplies} from '../_shared/checkout-profile.mjs';
import {profileUploadInput} from '../_shared/checkout-upload.mjs';
import {skillsOffers,CONTEXTS,BLS_PACKAGES} from '../skills-session-reservation/policy.mjs';

const KEY=/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const WIRES=new Set(['firstName','lastName','email','phone','billingCode','onlineCompleted','onlineCompletionAcknowledged']);
export function receiptView(r,now=Date.now()){
 // Expiry releases a seat hold, not an already recorded payment. Terminal
 // native orders remain terminal even when old hold/payment evidence survives.
 const terminal=r.kind==='public_order'&&['cancelled','canceled','refunded'].includes(r.status);
 const observed=r.paymentObserved&&(['held','checkout_open'].includes(r.status)||r.kind==='public_order'&&r.status==='expired');
 const status=terminal?r.status:r.reconciliationError?'payment_review':r.status==='paid'?'paid':observed?'processing':r.holdExpiresAt&&Date.parse(r.holdExpiresAt)<=now?'expired':r.kind==='skills_reservation'&&['registered','active','confirmed'].includes(r.status)?'held':r.status;
 return {status,orderId:r.orderId,amountCents:r.amountCents,currency:r.currency,startsAt:r.startsAt,endsAt:r.endsAt,location:r.location,
  holdExpiresAt:r.holdExpiresAt,students:(r.students||[]).map((st,index)=>({selectedChoices:r.profileSnapshot?.inputs?.[index]?.selectedChoices||[],uploads:Object.fromEntries(Object.entries(st.options?.checkoutUploads||{}).map(([k,v])=>[k,{evidenceStatus:v.evidenceStatus,approved:false}]))}))};
}
// A full-course URL selects an existing canonical session; it cannot create one.
export function fullAppointmentSession(rows,selection,now=Date.now()){
 if(!/^\d{1,12}$/.test(String(selection.course||''))||selection.skillsContext||
    !/^\d{4}-\d{2}-\d{2}$/.test(selection.date||'')||!/^\d{2}:\d{2}$/.test(selection.startTime||'')||!Array.isArray(rows)||rows.length>200)throw Error('invalid_session');
 const format=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
 const matches=rows.filter(s=>{
  if(String(s.courses?.enrollware_course_id)!==String(selection.course)||s.registration_backend!=='landerware'||s.record_scope!=='operational'||s.visibility!=='public'||s.registration_status!=='open'||!['scheduled','active'].includes(s.status)||!(Date.parse(s.start_at)>now)||!s.external_class_id)return false;
  const parts=Object.fromEntries(format.formatToParts(new Date(s.start_at)).map(x=>[x.type,x.value]));
  return `${parts.year}-${parts.month}-${parts.day}`===selection.date&&`${parts.hour}:${parts.minute}`===selection.startTime&&
   (!selection.location||[s.locations?.name,s.source_location_label].includes(selection.location))&&
   (!selection.instructor||[s.people?.display_name,s.source_instructor_label].includes(selection.instructor));
 });
 if(matches.length!==1)throw Error('session_not_available');return matches[0].external_class_id;
}
// PostgreSQL JSONB does not preserve object insertion order. Arrays remain ordered.
function sameJSON(a,b){
 const canonical=value=>Array.isArray(value)?value.map(canonical):value&&typeof value==='object'?
  Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])])):value;
 return JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
}
export function genericCheckout(deps){
 const rpc=deps.rpc,now=deps.now||(()=>Date.now());
 const afterCommit=async id=>{try{await deps.afterCommit?.(id);}catch{/* Delivery cannot roll back a committed reservation. */}};
 const receipt=key=>{if(!KEY.test(key||''))throw Error('invalid_request');return rpc('native_checkout_receipt',{p_key:key});};
 async function resolve(selection={}){
  const context=String(selection.skillsContext||'');let publicCourse=String(selection.course||''),session;
  let fullOffer=null;
  // A historic dated210549 link meant skills-only. Resolve it only against a
  // current native55-dollar package; new95-dollar orders require an exact ID.
  // Receipt recovery never enters this branch.
  let legacyBlsSkills=false;
  if(context==='bls-skills'&&publicCourse==='210549'){
   if(selection.session!=null)throw Error('session_not_available');
   if(selection.selectionId==null){
    const date=selection.date,time=selection.startTime;
    if(typeof date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(date)||
       typeof time!=='string'||!/^([01]\d|2[0-3]):[0-5]\d$/.test(time)||
       !Number.isFinite(Date.parse(date+'T00:00:00Z'))||new Date(date+'T00:00:00Z').toISOString().slice(0,10)!==date||
       ['location','instructor'].some(k=>selection[k]!=null&&(typeof selection[k]!=='string'||!selection[k].trim())))throw Error('session_not_available');
    legacyBlsSkills=true;publicCourse='509474';selection={...selection,course:publicCourse};
   }else if(!/^skills:native-skills(?::[a-f0-9]{64}|-seated:(?:[0-9]+|lw-[0-9a-f-]{36})):bls-skills:heartcode-bls-online-and-skills\.v1$/.test(selection.selectionId))throw Error('session_not_available');
  }
  if(!selection.session&&!context&&/^\d{1,12}$/.test(publicCourse)){
   let id;try{if(!selection.selectionId)id=await deps.appointmentSession?.(selection);}catch(error){if(error.message!=='session_not_available')throw error;}
   if(id)selection={...selection,session:id};
   else {
    // Each full course must have an independently reviewed server-side policy.
    const fullPage=fullCoursePage(publicCourse);if(!fullPage)throw Error('session_not_available');
    const fullPolicy=deps.fullPolicy?await deps.fullPolicy(publicCourse):{materializationEnabled:await deps.fullEnabled?.(),nativePublicationEnabled:false};
    if(fullPolicy?.materializationEnabled!==true)throw Error('native_registration_unavailable');
    if(selection.skillsContext)throw Error('invalid_context');
    const all=fullCourseOffers(await deps.publication(fullPage),publicCourse,now(),{nativePublicationEnabled:fullPolicy.nativePublicationEnabled===true,coursePolicy:fullPolicy});
    const matches=all.filter(o=>selection.selectionId?o.selectionId===selection.selectionId:
     o.localStart===`${selection.date}T${selection.startTime}`&&(!selection.instructor||o.instructor===selection.instructor)&&(!selection.location||o.location===selection.location));
    if(matches.length!==1)throw Error('session_not_available');fullOffer=matches[0];
   }
  }
  if(selection.session){
   session=await deps.scheduleSession(String(selection.session));
   // Registration is owned by LanderWare. An unconverted session must not
   // redirect a new registrant to the retired external enrollment service.
   if(!session.nativeReady)throw Error(selection.date?'session_not_available':'native_registration_unavailable');
   const actualCourse=String(session.course_id||session.course_number);
   if(publicCourse&&publicCourse!==actualCourse)throw Error('invalid_session');
   publicCourse=actualCourse;
  }
  const packet=await rpc('native_checkout_profile',{p_public_course_id:publicCourse,p_context:context});
  packet.catalog=await deps.catalog(packet.physicalCourseId);
  const view=normalizeCheckoutProfile(packet.profile,packet.catalog,{context,publicCourse});
  let offer=fullOffer,capacity=session?.seats?.capacity,remaining=session?.seats?.remaining;
  if(packet.profile.form_schema.inventory_kind==='leased_skills_v1'){
   if(deps.enabled&&!deps.enabled())throw Error('native_registration_unavailable');
   const page=CONTEXTS[context];if(!page||session)throw Error('invalid_context');
   const publication=await deps.publication(page);
   const nativeSkills=['509474','210549'].includes(publicCourse)&&(publication.dates||[]).some(d=>(d.startTimes||[]).some(t=>(t.courses||[]).some(c=>['native-skills-publication.v1','native-skills-seated.v1'].includes(c.authority))));
   const skillsPolicy=nativeSkills&&deps.skillsPolicy?await deps.skillsPolicy():{};
   const blsPolicy=context==='bls-skills'&&deps.blsSkillsPolicy?await deps.blsSkillsPolicy():{};
   const all=skillsOffers(publication,context,now(),publicCourse,{nativePublicationEnabled:skillsPolicy.nativePublicationEnabled===true,
    blsSkillsEnabled:blsPolicy.skillsEnabled===true,blsBundleEnabled:blsPolicy.bundleEnabled===true,profileVersion:blsPolicy.profileVersion});
   const matches=all.filter(o=>selection.selectionId?o.selectionId===selection.selectionId:
    o.localStart===`${selection.date}T${selection.startTime}`&&(!selection.instructor||o.instructor===selection.instructor)&&(!selection.location||o.location===selection.location));
   if(matches.length!==1)throw Error('session_not_available');offer=matches[0];
   if(context==='bls-skills'){
    if(!BLS_PACKAGES[publicCourse]||(!legacyBlsSkills&&selection.selectionId!==offer.selectionId)||offer.profileVersion!==view.profileVersion||
       offer.profileKey!==view.profileKey||packet.physicalCourseId!=='509474')throw Error('session_not_available');
    const choice=publicCourse==='210549'?'online_and_skills':'skills_only';
    const group=view.optionGroups.find(g=>g.key==='learning_path'),selected=group?.choices.find(c=>c.key===choice&&c.available);
    if(!selected||view.baseCents+selected.amountCents!==(publicCourse==='210549'?9500:5500))throw Error('option_unavailable');
    // One renderer; freeze the explicitly selected product, not a silent upgrade.
    view.optionGroups=view.optionGroups.map(g=>g.key==='learning_path'?{...g,choices:[selected]}:g);
    view.defaultChoices=[choice];view.title=publicCourse==='210549'?'HeartCode BLS online access + skills session':'BLS Skills Session Only';
   }
    await rpc('native_checkout_release_abandoned',{p_starts_at:offer.startsAt,p_ends_at:offer.consumptionEndsAt});
    const canonical=await rpc('skills_session_native_option',{p_context:context,p_offer:offer});
   if(!canonical)throw Error('session_not_available');capacity=canonical.capacity;
   remaining=canonical.targetSessionId?(await rpc('landerware_public_seat_state',{p_session_id:canonical.targetSessionId})).remaining:capacity;
  }else if(packet.profile.form_schema.inventory_kind!=='scheduled_session_v1'||(!session&&!fullOffer))throw Error('invalid_session');
  if(fullOffer){
    await rpc('native_checkout_release_abandoned',{p_starts_at:fullOffer.startsAt,p_ends_at:fullOffer.consumptionEndsAt});
    const canonical=await rpc('native_full_course_option',{p_course_number:publicCourse,p_offer:fullOffer});
   if(!canonical)throw Error('session_not_available');capacity=canonical.capacity;
   remaining=canonical.targetSessionId?(await rpc('landerware_public_seat_state',{p_session_id:canonical.targetSessionId})).remaining:capacity;
  }
  if(Number.isInteger(remaining)){if(remaining<1)throw Error('insufficient_seats');view.maxStudents=Math.min(view.maxStudents,remaining);}
  const startsAt=session?.start_at||offer?.startsAt,endsAt=session?.end_at||offer?.endsAt;
  const durationMinutes=(Date.parse(endsAt)-Date.parse(startsAt))/60000;
  return {packet,view,context,offer,selection:{course:publicCourse,skillsContext:context,...(session?{session:String(selection.session)}:{selectionId:offer.selectionId})},
   session:{startsAt,endsAt,location:session?.location_name||session?.location_display||offer?.location,
    ...(Number.isFinite(durationMinutes)&&durationMinutes>0?{durationMinutes}:{}),...(Number.isInteger(capacity)&&capacity>0?{capacity}:{}),...(Number.isInteger(remaining)?{remainingSeats:remaining}:{})}};
 }
 async function model(selection){
  const m=await resolve(selection);return {ok:true,profile:m.view,selection:m.selection,session:m.session};
 }
 async function resume(key){
  let r=await receipt(key),snap=r.profileSnapshot;
  if(!snap?.profile){
   const packet=await rpc('native_checkout_profile',{p_public_course_id:r.physicalCourseId,p_context:r.context});
   await rpc('native_checkout_bind_profile',{p_key:key,p_profile_key:packet.profile.profile_key,p_version:packet.profile.version,
    p_driver:r.kind==='skills_reservation'?'skills_reservation':'native_order',p_context:r.context,p_selection:{},p_inputs:[]});
   r=await receipt(key);snap=r.profileSnapshot;
  }
  return {ok:true,context:snap.context,profile:normalizeCheckoutProfile(snap.profile,snap.catalog,{context:snap.context,publicCourse:snap.physicalCourseId}),
   receipt:receiptView(r,now()),selection:snap.selection,session:{startsAt:r.startsAt,endsAt:r.endsAt,location:r.location}};
 }
 async function reserve(key,body){
  if(!KEY.test(key||''))throw Error('invalid_request');
  // A retry after a network loss must not need a still-leased public offer.
  let existing;try{existing=await receipt(key);}catch(e){if(e.message!=='reservation_not_found')throw e;}
  if(existing){
   const snap=existing.profileSnapshot,old=snap?.inputs||[];
   if(old.length!==body.students?.length)throw Error('idempotency_conflict');
   const prior=normalizeCheckoutProfile(snap.profile,snap.catalog,{context:snap.context,publicCourse:snap.physicalCourseId});
   if(snap.selection&&(body.selection?.session&&body.selection.session!==snap.selection.externalId||body.selection?.selectionId&&body.selection.selectionId!==snap.selection.offerId)||body.selection?.skillsContext&&body.selection.skillsContext!==snap.context)throw Error('idempotency_conflict');
   if(old.some((x,i)=>{const s=checkoutSelection(prior,body.students[i].fields||{},body.students[i].selectedChoices);return !sameJSON(x.submitted,{fields:s.fields,selectedChoices:s.selectedChoices});}))throw Error('idempotency_conflict');
   if(existing.kind==='public_order')await afterCommit(existing.orderId);
   return {ok:true,receipt:receiptView(existing,now())};
  }
  const m=await resolve(body.selection),students=body.students;
  if(body.profileKey!==m.view.profileKey||body.profileVersion!==m.view.profileVersion)throw Error('profile_changed');
  if(!Array.isArray(students)||!students.length||students.length>m.view.maxStudents)throw Error('invalid_request');
  let expected=0;const inputs=[],wire=[];
  for(const student of students){
   const selected=checkoutSelection(m.view,student.fields||{},student.selectedChoices);
   if(selected.driver!=='native_order')throw Error('native_registration_unavailable');
   const w={};for(const f of m.view.fields)if(f.wire&&WIRES.has(f.wire)&&Object.hasOwn(selected.fields,f.key))w[f.wire]=selected.fields[f.key];
   Object.assign(w,selected.bindings,{addons:selected.addons,skillsContext:m.context,selectorSelectionId:m.offer?.selectionId||null});
   expected+=selected.amountCents;wire.push(w);inputs.push({...selected,wire:w,submitted:{fields:selected.fields,selectedChoices:selected.selectedChoices}});
  }
  const r=await rpc('reserve_native_checkout_order',{p_key:key,p_profile_key:m.view.profileKey,p_version:m.view.profileVersion,p_context:m.context,
   p_external_id:m.selection.session||null,p_offer:m.offer||{},p_students:wire,p_inputs:inputs,p_expected_total:expected});
  if(r.status==='offer_required')throw Error('calendar_refresh_required');
  await afterCommit(r.orderId);
  return {ok:true,receipt:receiptView(r,now())};
 }
 async function status(key){
  let r=await receipt(key);
  // A released hold may still have a payable, previously bound Checkout.
  // Verification only retrieves that Checkout; admission stays with SQL.
  try{if(r.kind==='skills_reservation')await deps.legacyPayment(key,r.context,true);else if(r.kind==='public_order'&&['held','checkout_open','expired'].includes(r.status)&&!r.reconciliationError)await deps.verify(r.orderId);}
  catch(error){r=await receipt(key);if(!r.paymentObserved)throw error;}
  r=await receipt(key);if(r.kind==='public_order'&&r.status==='paid')await afterCommit(r.orderId);return {ok:true,receipt:receiptView(r,now())};
 }
 async function checkout(key){
  const r=await receipt(key),v=receiptView(r,now());
  if(v.status==='paid'){if(r.kind==='public_order')await afterCommit(r.orderId);return {ok:true,receipt:v};}
  if(v.status==='processing')return {ok:true,receipt:v};
  if(!['held','checkout_open'].includes(v.status))throw Error(v.status==='expired'?'hold_expired':'payment_reconciliation_required');
  if(!await rpc('native_checkout_payment_allowed',{p_key:key}))throw Error('required_document_missing');
  const result=r.kind==='skills_reservation'?await deps.legacyPayment(key,r.context,false):await deps.checkout(r.orderId,r.profileSnapshot);
  if(result.paymentStatus==='paid')return {ok:true,receipt:receiptView(await receipt(key),now())};
  if(result.checkoutUrl)result.url=result.checkoutUrl;
  if(typeof result.url!=='string'||!result.url.startsWith('https://checkout.stripe.com/'))throw Error('payment_unavailable');
  return {ok:true,checkoutUrl:result.url};
 }
 async function upload(key,body){
  const r=await receipt(key),index=body.studentIndex;
  if(!Number.isInteger(index)||index<0||index>=(r.students||[]).length)throw Error('invalid_request');
  const snap=r.profileSnapshot;if(!snap?.physicalCourseId)throw Error('uploads_disabled');
  const current=await rpc('native_checkout_profile',{p_public_course_id:snap.physicalCourseId,p_context:snap.context});
  const selected=snap.inputs?.[index]?.selectedChoices||[];
  const policy=uploadPolicies(current.profile).find(p=>p.key===body.requirementKey&&conditionApplies(p,selected));
  const file=profileUploadInput(body.file,policy),sha=await deps.hash(file.bytes);
  const intent=await rpc('native_checkout_begin_upload',{p_key:key,p_student_index:index,p_requirement_key:policy.key,p_sha:sha,p_type:file.type,p_size:file.bytes.length});
  if(intent.state!=='received')await deps.store(intent,file);
  const result=await rpc('native_checkout_finish_upload',{p_intent_id:intent.id});
  return {ok:true,evidenceStatus:result.evidenceStatus,approved:false};
 }
 return {model,resume,reserve,status,checkout,upload};
}

// Limit before parsing, including chunked requests with no content-length.
export async function boundedCheckoutJSON(req,limit=32768){
 if(Number(req.headers.get('content-length')||0)>limit)throw Error('request_too_large');
 const reader=req.body?.getReader();if(!reader)throw Error('invalid_request');let size=0;const chunks=[];
 try{for(;;){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>limit){await reader.cancel();throw Error('request_too_large');}chunks.push(value);}}
 finally{reader.releaseLock();}
 const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}
 try{return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));}catch{throw Error('invalid_request');}
}

