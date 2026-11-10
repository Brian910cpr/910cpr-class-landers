import {conditionApplies,checkoutSelection,escapeCheckoutText as esc} from './checkout-profile.js';
import {legacySkillsReceipt} from './checkout-receipt.js';

const API='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/public-registration/generic';
const app=document.getElementById('app'),params=new URLSearchParams(location.search);
const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(n/100);
const originalSelection=Object.fromEntries([...params].filter(([k])=>['session','course','date','startTime','instructor','location','skillsContext'].includes(k)));
const selectionKey='native-checkout:'+JSON.stringify(Object.entries(originalSelection).sort());
let key='',model,receipt,busy=false,studentCount=0;
function stored(name){try{return sessionStorage.getItem(name)||'';}catch{return '';}}
function save(name,value){try{sessionStorage.setItem(name,value);}catch{/* The active page still retains its receipt. */}}
function message(text){const el=document.getElementById('status');if(el)el.textContent=text;}
function announceSize(){if(params.get('embed')==='1')parent.postMessage({type:'landerware:checkout-size',sessionId:params.get('session'),height:document.documentElement.scrollHeight},location.origin);}
async function request(action,body,query={}){
 const url=new URL(API+'/'+action);for(const [k,v] of Object.entries(query))url.searchParams.set(k,v);
 const r=await fetch(url,{method:body?'POST':'GET',headers:{...(body?{'content-type':'application/json'}:{}),...(key?{'idempotency-key':key}:{})},...(body?{body:JSON.stringify(body)}:{}),redirect:'error',signal:AbortSignal.timeout(30000)});
 const p=await r.json();if(!r.ok||p.ok===false)throw Error(p.error||'service_unavailable');return p;
}
const errors={ambiguous_saved_reservation:'More than one saved registration matches this time. Contact 910CPR before reserving or paying again.',session_not_available:'This time is no longer available. Please choose another time.',calendar_refresh_required:'Please return to the calendar and select a current time.',profile_changed:'Course options changed. Reload this page before continuing.',hold_expired:'Your reservation hold expired. Please select a time again.',required_document_missing:'Upload the required document before proceeding.',document_storage_pending:'The file was not received. Retry the upload. For optional files, you may remove the file and bring it to class.',invalid_document:'Choose a supported file within the displayed size limit.',option_unavailable:'That option is currently unavailable. Please choose another.',insufficient_seats:'There are not enough seats for this selection.',idempotency_conflict:'This saved reservation has different details. Return to the calendar to make another selection.',payment_processing:'Payment is processing. Check payment status before trying again.',payment_reconciliation_required:'Payment needs review. Please contact 910CPR before trying again.',payment_unavailable:'Secure payment is temporarily unavailable. Your saved hold has not been charged.',native_registration_unavailable:'Online checkout is not available for this class yet.'};
function errorText(e){return errors[e.message]||'We could not complete that step. Your payment is not confirmed. Please retry or contact 910CPR.';}
function cards(){return [...document.querySelectorAll('.student')];}
function selected(card){return [...card.querySelectorAll('[data-choice]:checked')].map(el=>el.value);}
function inputs(card){return Object.fromEntries([...card.querySelectorAll('[data-field]')].filter(el=>!el.disabled).map(el=>[el.dataset.field,el.type==='checkbox'?el.checked:el.value]));}
function update(){
 let total=0;
 for(const card of cards()){
  const choices=selected(card);
  for(const wrapper of card.querySelectorAll('[data-config-field]')){
   const f=model.profile.fields.find(f=>f.key===wrapper.dataset.configField),el=wrapper.querySelector('[data-field]');
   wrapper.hidden=!conditionApplies(f,choices);el.disabled=wrapper.hidden||!!receipt;el.required=!wrapper.hidden&&(f.required||!!f.required_when_choice&&choices.includes(f.required_when_choice));
  }
  for(const wrapper of card.querySelectorAll('[data-upload-wrapper]')){
   const policy=model.profile.uploads.find(p=>p.key===wrapper.dataset.uploadWrapper),el=wrapper.querySelector('input');
   wrapper.hidden=!conditionApplies(policy,choices);el.disabled=wrapper.hidden;el.required=!wrapper.hidden&&policy.required&&!receipt?.students?.[cards().indexOf(card)]?.uploads?.[policy.key];
  }
  for(const el of card.querySelectorAll('[data-choice],.remove'))if(receipt)el.disabled=true;
  total+=model.profile.baseCents+model.profile.optionGroups.flatMap(g=>g.choices).filter(c=>choices.includes(c.key)).reduce((n,c)=>n+c.amountCents,0);
 }
 document.getElementById('total').textContent=receipt?'Saved total: '+money(receipt.amountCents)+(receipt.holdExpiresAt?' � Seat hold ends '+new Date(receipt.holdExpiresAt).toLocaleTimeString('en-US',{timeZone:'America/New_York'})+' Eastern':''):'Estimated total: '+money(total);
 document.getElementById('add-student').disabled=!!receipt||cards().length>=model.profile.maxStudents;
 document.getElementById('pay').hidden=['processing','refunded'].includes(receipt?.status);
 announceSize();
}
function addStudent(){
 if(receipt||cards().length>=model.profile.maxStudents)return;
 const index=studentCount++,card=document.createElement('fieldset');card.className='student';
 const groups=model.profile.optionGroups.map(g=>`<fieldset class="option-group"><legend>${esc(g.label)}</legend>${g.choices.map(c=>`<label class="choice"><input data-choice type="${g.type}" name="${index}-${esc(g.key)}" value="${esc(c.key)}" ${model.profile.defaultChoices.includes(c.key)?'checked':''} ${!c.available?'disabled':''}><span>${esc(c.label)}${c.amountCents?' (+'+money(c.amountCents)+')':''}${!c.available?' - unavailable':''}</span></label>`).join('')}</fieldset>`).join('');
 const fields=model.profile.fields.map(f=>`<label data-config-field="${esc(f.key)}">${esc(f.label)}${f.type==='textarea'?`<textarea data-field="${esc(f.key)}" maxlength="${f.max_length}"></textarea>`:`<input data-field="${esc(f.key)}" type="${esc(f.type)}" maxlength="${f.max_length}" autocomplete="${esc(f.autocomplete||'off')}">`}</label>`).join('');
 const uploads=model.profile.uploads.map(p=>`<label class="wide" data-upload-wrapper="${esc(p.key)}">${esc(p.label)} (${p.required?'required':'optional'})<input data-upload="${esc(p.key)}" type="file" accept="${esc(p.mimeTypes.join(','))}"><small>Maximum ${Math.round(p.maxBytes/1048576*10)/10} MB. ${p.required?'':'You may bring the document to class instead.'} Files are private; receiving a file does not mean it has been approved.</small></label>`).join('');
 card.innerHTML=`<legend>Participant ${cards().length+1}</legend><button class="remove secondary" type="button">Remove participant</button><div class="fields">${fields}</div>${groups}${uploads}`;
 card.querySelector('.remove').addEventListener('click',()=>{if(cards().length>1&&!receipt){card.remove();update();}});
 card.addEventListener('change',update);document.getElementById('students').append(card);update();
}
async function filePacket(file,policy){
 if(file.size>policy.maxBytes||!policy.mimeTypes.includes(file.type))throw Error('invalid_document');
 const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
 return {type:file.type,base64:btoa(binary)};
}
function confirmed(){
 document.getElementById('checkout-form').hidden=true;
 document.getElementById('result').textContent='Payment received. Your registration is confirmed.';
 announceSize();
}
function rememberReceipt(){save(selectionKey,key);if(receipt.orderId)save('native-checkout-order:'+receipt.orderId,key);}
async function status(){const p=await request('status');receipt=p.receipt;if(receipt.status==='paid')confirmed();else if(receipt.status==='refunded')message('This order was refunded; it is not a confirmed registration. Contact 910CPR for help.');else if(receipt.status==='processing')message('Payment received; registration confirmation is pending. Check payment status again or contact 910CPR. Do not pay again.');else if(['expired','payment_review','cancelled','canceled'].includes(receipt.status))throw Error(receipt.status==='expired'?'hold_expired':'payment_reconciliation_required');update();return receipt;}
async function submit(event){
 event.preventDefault();if(busy)return;busy=true;const button=document.getElementById('pay');button.disabled=true;message('Saving your selection.');
 try{
  if(!receipt){
   const students=cards().map(card=>{const fields=inputs(card),selectedChoices=selected(card);checkoutSelection(model.profile,fields,selectedChoices);return {fields,selectedChoices};});
   key=key||crypto.randomUUID();save(selectionKey,key);
   const p=await request('reserve',{selection:model.selection,profileKey:model.profile.profileKey,profileVersion:model.profile.profileVersion,students});receipt=p.receipt;rememberReceipt();update();
  }
  if(['paid','processing','refunded'].includes((await status()).status))return;
  for(const [index,card] of cards().entries())for(const el of card.querySelectorAll('[data-upload]')){
   if(el.disabled||!el.files[0])continue;
   const policy=model.profile.uploads.find(p=>p.key===el.dataset.upload);message('Receiving your document.');
   await request('upload',{studentIndex:index,requirementKey:policy.key,file:await filePacket(el.files[0],policy)});
  }
  message('Opening secure payment.');const p=await request('checkout',{});
  if(p.receipt?.status==='paid'){receipt=p.receipt;confirmed();return;}
  if(['processing','refunded'].includes(p.receipt?.status)){receipt=p.receipt;await status();return;}
  const destination=new URL(p.checkoutUrl);if(destination.origin!=='https://checkout.stripe.com')throw Error('payment_unavailable');
  if(params.get('embed')==='1')window.top.location.href=destination.href;else location.assign(destination.href);
 }catch(e){message(errorText(e));}finally{busy=false;button.disabled=false;announceSize();}
}
async function init(){
 try{
  const order=params.get('order'),recover=params.get('recover');key=order?stored('native-checkout-order:'+order):stored(selectionKey);
  if(!key&&!order&&!recover)key=stored('skillsCheckout:'+JSON.stringify(['course','date','startTime','location','instructor','skillsContext'].map(k=>params.get(k)||'')));
  if(!key&&!order&&!recover)key=legacySkillsReceipt(sessionStorage,originalSelection);
  if(recover){key='';model=await request('form',null,{recover});key=model.key;}
  else if(key){try{model=await request('form');}catch(e){if(e.message!=='reservation_not_found')throw e;/* Keep the same nonce if an earlier save is still in flight. */}}
  if(!model)model=await request('form',null,originalSelection);
  if(model.nativeReady===false){
   const url=new URL(model.fallbackRegistrationUrl);
   if(url.origin!=='https://coastalcprtraining.enrollware.com'||url.pathname!=='/enroll'||url.searchParams.get('id')!==originalSelection.session||model.sessionId!==originalSelection.session)throw Error('native_registration_unavailable');
   app.innerHTML='<section class="formwrap"><h1>Registration for your selected class</h1><p>This class is still registered through our existing enrollment system. Continue there to register.</p></section>';
   const link=document.createElement('a');link.href=url.href;link.target='_top';link.textContent='Continue to existing registration';app.append(link);announceSize();return;
  }
  if(model.legacyRecovery){
   const recovery=model.legacyRecovery;
   app.innerHTML='<section class="formwrap"><h1>Your saved registration</h1><p id="recovery-status" role="status" aria-live="polite"></p></section>';
   const messages={paid:'Your registration is confirmed.',processing:'Payment received. Registration is being finalized. Please check again shortly.',payment_review:'Payment received. Your registration needs staff review. Please contact 910CPR.',expired:'Your original seat hold has expired. Please choose an available class.',cancelled:'This registration was canceled.',refunded:'This order was refunded.'};
   document.getElementById('recovery-status').textContent=messages[recovery.status]||'Your saved registration is ready for payment.';
   if(recovery.checkoutUrl){const destination=new URL(recovery.checkoutUrl);if(destination.origin!=='https://checkout.stripe.com')throw Error('payment_unavailable');const link=document.createElement('a');link.href=destination.href;link.target='_top';link.textContent='Continue to secure payment';app.querySelector('section').append(link);}
   announceSize();return;
  }
  receipt=model.receipt;
  const p=model.profile,date=new Date(model.session.startsAt).toLocaleString('en-US',{timeZone:'America/New_York',dateStyle:'full',timeStyle:'short'});
  const length=model.session.durationMinutes||(Date.parse(model.session.endsAt)-Date.parse(model.session.startsAt))/60000;
  const details=(Number.isFinite(length)&&length>0?'Class length: '+length+' minutes. ':'')+(model.session.capacity?'Class capacity: '+model.session.capacity+'. ':'')+(Number.isInteger(model.session.remainingSeats)?'Seats currently available: '+model.session.remainingSeats+'.':'');
  app.innerHTML=`<header><h1>${esc(p.title)}</h1><p>${esc(date)} Eastern time</p><p>${esc(model.session.location||'')}</p><p>${esc(details)}</p></header><section class="formwrap"><p>${esc(p.description)}</p><a href="${esc(p.backUrl)}">Choose another class or time</a><form id="checkout-form"><div id="students"></div><button id="add-student" type="button" class="secondary">Add participant</button><p id="total"></p><p id="status" role="status" aria-live="polite"></p><button id="pay" type="submit">Continue to secure payment</button><button id="check-status" type="button" class="secondary">Check payment status</button></form><p id="result" role="status" aria-live="polite"></p></section>`;
  // Render participants from configuration only; never put saved contact fields in HTML.
  const saved=receipt;receipt=null;for(let i=0;i<(saved?.students?.length||1);i++)addStudent();receipt=saved;
  if(receipt)cards().forEach((card,i)=>{if(receipt.students[i].selectedChoices.length)for(const el of card.querySelectorAll('[data-choice]'))el.checked=receipt.students[i].selectedChoices.includes(el.value);});
  if(receipt){rememberReceipt();for(const card of cards())for(const el of card.querySelectorAll('[data-field]'))el.required=false;}
  document.getElementById('add-student').addEventListener('click',addStudent);document.getElementById('checkout-form').addEventListener('submit',submit);
  document.getElementById('check-status').addEventListener('click',async()=>{if(busy||!key)return;try{const r=await status();if(!['paid','processing','refunded'].includes(r.status))message('Payment has not been confirmed. You may continue to secure payment.');}catch(e){message(errorText(e));}});
  update();if(receipt)await status();
 }catch(e){app.textContent=errorText(e);const link=document.createElement('a');link.href='/classes/';link.textContent=' Return to classes';app.append(link);}
}
if(params.get('embed')==='1')document.documentElement.classList.add('embedded-checkout');
new ResizeObserver(announceSize).observe(app);
init();

