import {SITE,CONTEXTS,skillsOffers,studentInput} from './policy.mjs';
import {skillsCheckout,certificateInput} from './checkout.mjs';
import {bundleRoute} from './bundle.mjs';
const ALLOWED=new Set([SITE,'https://910cpr.com']);
const PUBLIC=new Set(['generic_checkout_required','uploads_disabled','required_document_missing','invalid_document','document_storage_pending','invalid_request','invalid_context','invalid_student','idempotency_conflict','session_not_available','calendar_refresh_required','invalid_certificate','payment_unavailable','payment_mismatch','payment_reconciliation_required','reservation_not_found','hold_expired','bundle_fulfillment_unavailable','student_already_held','already_registered']);
async function boundedBody(req,limit){
  if(!req.body)return '';
  const reader=req.body.getReader(),decoder=new TextDecoder();let size=0,text='';
  while(true){const {value,done}=await reader.read();if(done)break;size+=value.byteLength;
    if(size>limit){await reader.cancel();return null;}text+=decoder.decode(value,{stream:true});}
  return text+decoder.decode();
}
export function createHandler({publication,rpc,stripe,upload,publicOrder,uploadBundle,compatCheckout,enabled=()=>false,now=()=>Date.now()}) {
  return async req=>{
    const origin=req.headers.get('origin')||'';
    const headers={'content-type':'application/json','cache-control':'no-store','access-control-allow-origin':ALLOWED.has(origin)?origin:SITE,
      'access-control-allow-headers':'content-type,idempotency-key,authorization,apikey','access-control-allow-methods':'POST,OPTIONS',vary:'Origin'};
    const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
    if(origin&&!ALLOWED.has(origin))return json({error:'origin_not_allowed'},403);
    if(req.method==='OPTIONS')return new Response(null,{status:204,headers});
    if(req.method!=='POST')return json({error:'method_not_allowed'},405);
    if(!enabled())return json({ok:false,error:'native_scheduling_not_configured'},503);
    const route=new URL(req.url).pathname.split('/').filter(Boolean).at(-1);
    const limit=['certificate','bundle-certificate'].includes(route)?2805000:8192;
    if(Number(req.headers.get('content-length')||0)>limit)return json({error:'request_too_large'},413);
    try {
      const raw=await boundedBody(req,limit);if(raw===null)return json({error:'request_too_large'},413);
      let body;try{body=JSON.parse(raw);}catch{throw Error('invalid_request');}
      const context=body.context;
      if(!CONTEXTS[context])throw Error('invalid_context');
      if(compatCheckout&&['checkout','payment-status','certificate','bundle-checkout','bundle-status','bundle-certificate'].includes(route)){
        const key=req.headers.get('idempotency-key')||'';
        if(!/^[0-9a-f-]{36}$/i.test(key))throw Error('invalid_request');
        return json(await compatCheckout(route,key.toLowerCase(),body));
      }
      if(['bundle-reserve','bundle-certificate','bundle-status','bundle-checkout'].includes(route)){
        const key=req.headers.get('idempotency-key')||'';
        if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(key))throw Error('invalid_request');
        return json(await bundleRoute(route,body,key.toLowerCase(),{rpc,publication,now,publicOrder,uploadBundle}));
      }
      if(['checkout','payment-status','certificate'].includes(route)){
        const key=req.headers.get('idempotency-key')||'';
        if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(key))throw Error('invalid_request');
        if(route!=='certificate')return json(await skillsCheckout({rpc,stripe,now},key.toLowerCase(),context,route==='payment-status'));
        const file=certificateInput(body.certificate);
        // Authorization comes from the saved receipt capability, never a
        // client-supplied registration UUID, storage path, or filename.
        const order=await rpc('skills_checkout_order',{p_key:key.toLowerCase(),p_context:context});
        const result=await upload(order,file);
        return json({ok:true,documentId:result.documentId});
      }
      if(route==='choices'){
        const publicCourse=body.publicCourse||'509474';
        if(!['509474','210549'].includes(publicCourse)||publicCourse==='210549'&&context!=='bls-skills')throw Error('invalid_context');
        if(publicCourse==='210549'&&!await rpc('bls_native_bundle_ready',{}))return json({ok:true,amountCents:9500,offers:[]});
        const selection=body.selection;
        if(!selection||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(selection.localStart||'')||
          typeof selection.instructor!=='string'||selection.instructor.length>200||typeof selection.location!=='string'||selection.location.length>300)throw Error('invalid_request');
        const candidates=skillsOffers(await publication(CONTEXTS[context]),context,now(),publicCourse).filter(o=>o.localStart===selection.localStart&&o.instructor===selection.instructor&&o.location===selection.location);
        if(candidates.length>4)throw Error('service_unavailable');
        const offers=[];
        for(const offer of candidates){
          // Read-only canonical validation before exposing a form. Only reserve
          // can materialize anything, and it rechecks under the transaction locks.
          if(await rpc('skills_session_native_option',{p_context:context,p_offer:offer}))offers.push(offer);
        }
        return json({ok:true,context,amountCents:publicCourse==='210549'?9500:5500,offers:offers.map(o=>({selectionId:o.selectionId,startsAt:o.startsAt,endsAt:o.endsAt,location:o.location,instructor:o.instructor}))});
      }
      if(route!=='reserve')return json({error:'not_found'},404);
      const key=req.headers.get('idempotency-key')||'';
      if(!/^[0-9a-f-]{36}$/i.test(key)||typeof body.selectionId!=='string'||body.selectionId.length>2048)throw Error('invalid_request');
      const student=studentInput(body.student);
      const args={p_idempotency_key:key.toLowerCase(),p_context:context,p_student:student,p_offer:{selectionId:body.selectionId}};
      const replay=await rpc('reserve_skills_session_native',args);
      if(replay?.ok===true&&replay.status==='reserved'&&replay.registrationId&&replay.sessionId)return json(replay);
      if(replay?.status!=='offer_required')throw Error('service_unavailable');
      // Only an identity is accepted from the browser. Dates, price, capacity,
      // instructor and room come from the server's current leased publication.
      const offer=skillsOffers(await publication(CONTEXTS[context]),context,now()).find(o=>o.selectionId===body.selectionId);
      if(!offer)throw Error('session_not_available');
      const result=await rpc('reserve_skills_session_native',{...args,p_offer:offer});
      if(!result?.ok||result.status!=='reserved'||!result.registrationId||!result.sessionId)throw Error('service_unavailable');
      return json(result);
    }catch(e){const error=e instanceof Error?e.message:'';return json({ok:false,error:PUBLIC.has(error)?error:'service_unavailable'},PUBLIC.has(error)?409:503);}
  };
}
