import {SITE,CONTEXTS,skillsOffers,studentInput} from './policy.mjs';
const ALLOWED=new Set([SITE,'https://910cpr.com']);
const PUBLIC=new Set(['invalid_request','invalid_context','invalid_student','idempotency_conflict','session_not_available','calendar_refresh_required']);
export function createHandler({publication,rpc,enabled=()=>false,now=()=>Date.now()}) {
  return async req=>{
    const origin=req.headers.get('origin')||'';
    const headers={'content-type':'application/json','cache-control':'no-store','access-control-allow-origin':ALLOWED.has(origin)?origin:SITE,
      'access-control-allow-headers':'content-type,idempotency-key','access-control-allow-methods':'POST,OPTIONS',vary:'Origin'};
    const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers});
    if(origin&&!ALLOWED.has(origin))return json({error:'origin_not_allowed'},403);
    if(req.method==='OPTIONS')return new Response(null,{status:204,headers});
    if(req.method!=='POST')return json({error:'method_not_allowed'},405);
    if(!enabled())return json({ok:false,error:'native_scheduling_not_configured'},503);
    if(Number(req.headers.get('content-length')||0)>8192)return json({error:'request_too_large'},413);
    try {
      const raw=await req.text();if(raw.length>8192)return json({error:'request_too_large'},413);
      let body;try{body=JSON.parse(raw);}catch{throw Error('invalid_request');}
      const context=body.context;
      if(!CONTEXTS[context])throw Error('invalid_context');
      const route=new URL(req.url).pathname.split('/').filter(Boolean).at(-1);
      if(route==='choices'){
        const selection=body.selection;
        if(!selection||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(selection.localStart||'')||
          typeof selection.instructor!=='string'||selection.instructor.length>200||typeof selection.location!=='string'||selection.location.length>300)throw Error('invalid_request');
        const candidates=skillsOffers(await publication(CONTEXTS[context]),context,now()).filter(o=>o.localStart===selection.localStart&&o.instructor===selection.instructor&&o.location===selection.location);
        if(candidates.length>4)throw Error('service_unavailable');
        const offers=[];
        for(const offer of candidates){
          // Read-only canonical validation before exposing a form. Only reserve
          // can materialize anything, and it rechecks under the transaction locks.
          if(await rpc('skills_session_native_option',{p_context:context,p_offer:offer}))offers.push(offer);
        }
        return json({ok:true,context,amountCents:5500,offers:offers.map(o=>({selectionId:o.selectionId,startsAt:o.startsAt,endsAt:o.endsAt,location:o.location,instructor:o.instructor}))});
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
