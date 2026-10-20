import {providerFailure,deliveryFailure} from './delivery-errors.mjs';
import {authorizedOwner} from '../_shared/owner-auth.ts';
import {ownerRest,tokenHash,newToken} from '../_shared/owner-session.ts';
import {SITE,familyPath,publishedOffers,localStart,validToken} from './policy.mjs';

const ORIGINS=new Set([SITE,'https://910cpr.com']);
function headers(origin) {return {'content-type':'application/json','cache-control':'no-store','referrer-policy':'no-referrer','access-control-allow-origin':ORIGINS.has(origin)?origin:SITE,'access-control-allow-headers':'content-type,x-reschedule-token,x-landerware-owner-session,x-hot-sync-admin-key','access-control-allow-methods':'POST,OPTIONS',vary:'Origin'};}
function json(origin,value,status=200){return new Response(JSON.stringify(value),{status,headers:headers(origin)});}
async function rpc(name,body){
 const {ownerConfig}=await import('../_shared/owner-session.ts'); const config=ownerConfig();
 const response=await fetch(`${config.url}/rest/v1/rpc/${name}`,{method:'POST',redirect:'error',signal:AbortSignal.timeout(15000),headers:{apikey:config.key,authorization:`Bearer ${config.key}`,'content-type':'application/json'},body:JSON.stringify(body)});
 const result=await response.json();
 if(!response.ok) throw Error(result.message||'service_unavailable');
 return result;
}
async function choices(hash){
 const context=await rpc('registration_reschedule_context',{p_token_sha256:hash});
 if(context.status==='confirmed')return context;
 const response=await fetch(`${SITE}/data/block-selector-availability/${familyPath(context.course)}.json`,{cache:'no-store',redirect:'error',signal:AbortSignal.timeout(15000)});
 if(!response.ok)throw Error('calendar_refresh_required');
 const offers=publishedOffers(await response.json(),context.courseNumber);
 const ids=[...new Set(offers.filter(o=>o.externalId).map(o=>o.externalId))];
 const current=await rpc('registration_reschedule_context',{p_token_sha256:hash,p_published_ids:ids});
 if(current.status==='confirmed')return current;
 // Match publication time to canonical time as well as external identity.
 const sessionIds=current.options.map(o=>o.id);
 const sessions=sessionIds.length?await ownerRest(`class_sessions?id=in.(${sessionIds.join(',')})&select=id,external_class_id`):[];
 current.options=current.options.filter(o=>offers.some(p=>p.externalId===sessions.find(s=>s.id===o.id)?.external_class_id&&p.localStart===localStart(o.startsAt)));
 const dynamicOffers=offers.filter(o=>o.kind==='dynamic');
 if(dynamicOffers.length){
  const dynamic=await rpc('registration_reschedule_dynamic_targets',{p_token_sha256:hash,p_offers:dynamicOffers});
  current.options.push(...dynamic);
 }
 current.options.sort((a,b)=>Date.parse(a.startsAt)-Date.parse(b.startsAt));
 return {...current,publishedIds:ids,dynamicOffers};
}
const PUBLIC_ERRORS=new Set(['invalid_or_expired_link','registration_not_reschedulable','registration_email_missing','invalid_link_policy','session_not_available','already_registered_for_target','link_already_used','duplicate_financial_record_requires_review','duplicate_completion_requires_review','registration_date_closed','calendar_refresh_required','course_calendar_unavailable','invalid_help_message']);
export async function deliverConfirmations(registrationId=null){
 const key=Deno.env.get('RESEND_API_KEY');
 if(!key)return {configured:false,sent:0,failed:0};
 const messages=await rpc('claim_reschedule_confirmations',{p_registration_id:registrationId});
 let sent=0,failed=0;
 for(const m of messages){
  let stage='provider_request';
  try{
   const response=await fetch('https://api.resend.com/emails',{method:'POST',signal:AbortSignal.timeout(12000),headers:{authorization:`Bearer ${key}`,'content-type':'application/json','idempotency-key':`reschedule-${m.id}`},body:JSON.stringify({from:Deno.env.get('RESEND_FROM_EMAIL')||'910CPR <registration@notify.910cpr.com>',reply_to:'brian@910cpr.com',to:[m.recipient],subject:m.subject,text:m.body})});
   stage='provider_response';
   let result;
   try{result=await response.json();}catch{throw providerFailure(response.status,null);}
   if(!response.ok||!result?.id)throw providerFailure(response.status,result);
   stage='message_record';
   await ownerRest(`landerware_messages?id=eq.${m.id}`,{method:'PATCH',body:JSON.stringify({delivery_provider:'resend',delivery_status:'sent',provider_message_id:result.id,sent_at:new Date().toISOString(),failure_detail:null})});
   stage='queue_record';
   await ownerRest(`registration_reschedule_deliveries?message_id=eq.${m.id}`,{method:'PATCH',body:JSON.stringify({status:'sent',last_error:null})});sent++;
  }catch(error){
   const code=deliveryFailure(stage,error);
   console.error(JSON.stringify({event:'reschedule_delivery_failed',messageId:m.id,code}));
   await ownerRest(`registration_reschedule_deliveries?message_id=eq.${m.id}`,{method:'PATCH',body:JSON.stringify({status:'failed',last_error:code,next_attempt_at:new Date(Date.now()+5*60000).toISOString()})});failed++;
  }
 }
 return {configured:true,sent,failed};
}
async function confirmationStatus(result){
 // Seat success must survive a mail-provider outage. Retry uses the same provider key.
 try{await deliverConfirmations(result.registrationId);}catch{/* Durable queue remains retryable. */}
 try{const rows=await ownerRest(`landerware_messages?operational_registration_id=eq.${result.registrationId}&template_key=eq.registration-rescheduled-v1&select=delivery_status&limit=1`);
  return {...result,confirmationStatus:rows[0]?.delivery_status==='sent'?'sent':'pending'};
 }catch{return {...result,confirmationStatus:'pending'};}
}
export async function handler(req){
 const origin=req.headers.get('origin')||'';
 if(origin&&!ORIGINS.has(origin))return json(origin,{error:'origin_not_allowed'},403);
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers:headers(origin)});
 if(req.method==='GET'&&new URL(req.url).pathname.endsWith('/status'))return json(origin,{version:1,mailConfigured:Boolean(Deno.env.get('RESEND_API_KEY'))});
 if(req.method!=='POST')return json(origin,{error:'method_not_allowed'},405);
 if(Number(req.headers.get('content-length')||0)>8192)return json(origin,{error:'request_too_large'},413);
 const route=new URL(req.url).pathname.split('/').filter(Boolean).at(-1);
 try{
  if(['lookup','issue','block','revoke','health','retry-confirmations'].includes(route)){
   if(!await authorizedOwner(req))return json(origin,{error:'owner_access_required'},401);
   const body=await req.json();
   if(route==='lookup'){
    const email=String(body.email||'').trim();
    if(!/^[a-z0-9.!#$&'+\/=^`{|}~@_-]+$/i.test(email)||!email.includes('@'))return json(origin,{error:'invalid_email'},400);
    const customers=await ownerRest(`customers?email=ilike.${encodeURIComponent(email.replace(/_/g,'\\_'))}&select=id,first_name,last_name&limit=10`);
    const registrations=[];
    for(const c of customers){
     const rows=await ownerRest(`registrations?customer_id=eq.${c.id}&status=in.(active,registered,confirmed)&select=id,registration_orders(id),session:class_sessions!inner(start_at,course_id,external_class_id,course:courses(name))&session.start_at=gt.${encodeURIComponent(new Date().toISOString())}&limit=100`);
     const grouped=new Map();
     for(const r of rows){const s=r.session,key=s.course_id+'|'+s.start_at,score=(r.registration_orders?.length?2:0)+(/^\d+$/.test(s.external_class_id)?1:0);if(!grouped.has(key)||score>grouped.get(key).score)grouped.set(key,{id:r.id,name:`${c.first_name} ${c.last_name}`,course:s.course?.name||'',startsAt:s.start_at,score});}
     registrations.push(...[...grouped.values()].map(({score,...r})=>r));
    }
    return json(origin,{registrations});
   }
   if(route==='retry-confirmations'){
    const delivery=await deliverConfirmations();
    const stuck=await ownerRest(`registration_reschedule_deliveries?status=in.(failed,needs_review)&select=message_id,status,last_error,attempts&limit=20`);
    return json(origin,{...delivery,pendingFailures:stuck.length},!delivery.configured||delivery.failed||stuck.length?503:200);
   }
   if(route==='issue'){
    const token=newToken('lw_r_');
    const issued=await rpc('issue_registration_reschedule_link',{p_registration_id:body.registrationId,p_token_sha256:await tokenHash(token),p_expires_at:body.expiresAt||new Date(Date.now()+30*86400000).toISOString(),p_reason:body.reason||'Instructor unavailable',p_deadline_at:body.deadlineAt||null});
    return json(origin,{...issued,url:`${SITE}/reschedule/#${token}`});
   }
   if(route==='block'){
    if(!Array.isArray(body.sessionIds)||!body.sessionIds.length||body.sessionIds.length>100||body.sessionIds.some(id=>! /^[0-9a-f-]{36}$/i.test(id)))return json(origin,{error:'invalid_sessions'},400);
    await ownerRest('registration_reschedule_blocks',{method:'POST',headers:{prefer:'resolution=merge-duplicates'},body:JSON.stringify(body.sessionIds.map(id=>({class_session_id:id,reason:String(body.reason||'Instructor unavailable').slice(0,500)})))});
    return json(origin,{ok:true});
   }
   if(route==='revoke'){
    if(!/^[0-9a-f-]{36}$/i.test(body.linkId||''))return json(origin,{error:'invalid_link'},400);
    await ownerRest(`registration_reschedule_links?id=eq.${body.linkId}`,{method:'PATCH',body:JSON.stringify({revoked_at:new Date().toISOString()})});return json(origin,{ok:true});
   }
   const messages=await ownerRest('landerware_messages?template_key=eq.registration-rescheduled-v1&select=delivery_status,created_at,sent_at&order=created_at.desc&limit=100');
   return json(origin,{ok:true,checkedAt:new Date().toISOString(),confirmations:messages});
  }
  const token=req.headers.get('x-reschedule-token')||'';
  if(!validToken(token))return json(origin,{error:'invalid_or_expired_link'},401);
  const hash=await tokenHash(token);
  if(route==='help'){const body=await req.json();const result=await rpc('request_registration_reschedule_help',{p_token_sha256:hash,p_message:body.message});try{await deliverConfirmations();}catch{}return json(origin,result);}
  if(route!=='context'&&route!=='confirm')return json(origin,{error:'not_found'},404);
  const current=await choices(hash);
  if(route==='context'){delete current.publishedIds;delete current.dynamicOffers;if(current.status==='confirmed')current.result=await confirmationStatus(current.result);return json(origin,current);}
  const body=await req.json();
  if(current.status==='confirmed'){
   if((current.result.selectionId||current.result.sessionId)!==body.sessionId)throw Error('link_already_used');
   return json(origin,await confirmationStatus({...current.result,idempotentReplay:true}));
  }
  if(!current.options.some(o=>o.id===body.sessionId))throw Error('session_not_available');
  const offer=current.dynamicOffers?.find(o=>o.selectionId===body.sessionId);
  if(offer)return json(origin,await confirmationStatus(await rpc('confirm_registration_reschedule_dynamic',{p_token_sha256:hash,p_offer:offer})));
  return json(origin,await confirmationStatus(await rpc('confirm_registration_reschedule',{p_token_sha256:hash,p_target_session_id:body.sessionId,p_published_ids:current.publishedIds})));
 }catch(error){
  const message=error instanceof Error?error.message:'';
  return json(origin,{error:PUBLIC_ERRORS.has(message)?message:'service_unavailable'},message==='invalid_or_expired_link'?401:PUBLIC_ERRORS.has(message)?409:503);
 }
}
if(import.meta.main)Deno.serve(handler);
