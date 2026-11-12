import {createHandler} from './handler.mjs';
import {SITE} from './policy.mjs';
import {ownerConfig,ownerRest} from '../_shared/owner-session.ts';
export const handler=createHandler({
  async compatCheckout(route:string,key:string,body:any){
    // Cached older forms retain their receipt, but cannot bypass current
    // per-course upload configuration or the common payment gate.
    const c=ownerConfig();
    async function call(action:string,payload?:unknown){
      const r=await fetch(`${c.url}/functions/v1/public-registration/generic/${action}`,{method:payload?'POST':'GET',redirect:'error',signal:AbortSignal.timeout(25000),headers:{apikey:c.key,authorization:`Bearer ${c.key}`,'content-type':'application/json','idempotency-key':key},...(payload?{body:JSON.stringify(payload)}:{})});
      const p=await r.json();if(!r.ok)throw Error(p.error||'payment_unavailable');return p;
    }
    const form=await call('form');
    if(form.context!==body.context)throw Error('invalid_context');
    if(route.endsWith('certificate')){
      const p=form.profile.uploads.filter((p:any)=>p.documentType==='online_completion');if(p.length!==1)throw Error('uploads_disabled');
      return call('upload',{studentIndex:0,requirementKey:p[0].key,file:body.certificate});
    }
    const p=await call(route.endsWith('status')?'status':'checkout',route.endsWith('status')?undefined:{});
    return {...p,paymentStatus:p.receipt?.status==='paid'?'paid':'pending',reservation:{startsAt:form.session.startsAt,location:form.session.location}};
  },
  async publicOrder(action:string,key:string,order:any){
    const c=ownerConfig(),student=order.checkoutStudents[0];
    const path=action==='status'?`order/${order.orderId}`:'start';
    const r=await fetch(`${c.url}/functions/v1/public-registration/${path}`,{method:action==='status'?'GET':'POST',redirect:'error',signal:AbortSignal.timeout(20000),
      headers:{apikey:c.key,authorization:`Bearer ${c.key}`,'content-type':'application/json','idempotency-key':key},
      ...(action==='status'?{}:{body:JSON.stringify({sessionId:order.externalClassId,students:order.checkoutStudents,payerEmail:student.email,payerPhone:student.phone})})});
    const result=await r.json();
    if(!r.ok&&!(action==='status'&&r.status===409&&['payment_pending','payment_review'].includes(result.status)))throw Error('payment_unavailable');
    return result;
  },
  async uploadBundle(key:string,order:any,file:any){
    if(order.certificatePrivate!==true)throw Error('certificate_unavailable');
    const c=ownerConfig(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',file.bytes)),b=>b.toString(16).padStart(2,'0')).join('');
    const path=`${order.sessionId}/skills/bundle/${order.studentId}/${hash}.${file.extension}`;
    const r=await fetch(`${c.url}/storage/v1/object/class-session-docs/${path}`,{method:'POST',redirect:'error',signal:AbortSignal.timeout(15000),
      headers:{apikey:c.key,authorization:`Bearer ${c.key}`,'content-type':file.type,'x-upsert':'false'},body:file.bytes});
    if(!r.ok){const error=await r.json().catch(()=>({}));if(!['Duplicate','ResourceAlreadyExists'].includes(error.error)&&String(error.statusCode)!=='409')throw Error('certificate_unavailable');}
    return ownerRest('rpc/attach_bls_bundle_certificate',{method:'POST',body:JSON.stringify({p_key:key,p_sha:hash,p_type:file.type,p_size:file.bytes.length})},c);
  },
  async stripe(method:string,path:string,params?:URLSearchParams,idempotencyKey?:string){
    const key=Deno.env.get('STRIPE_SECRET_KEY');if(!key)throw Error('payment_unavailable');
    const r=await fetch(`https://api.stripe.com/v1/${path}`,{method,redirect:'error',signal:AbortSignal.timeout(15000),
      headers:{authorization:`Bearer ${key}`,...(params?{'content-type':'application/x-www-form-urlencoded'}:{}),...(idempotencyKey?{'idempotency-key':idempotencyKey}:{})},...(params?{body:params}:{})});
    if(!r.ok)throw Error('payment_unavailable');return r.json();
  },
  async upload(order:any,file:any){
    if(order.certificatePrivate!==true)throw Error('certificate_unavailable');
    const c=ownerConfig(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',file.bytes)),b=>b.toString(16).padStart(2,'0')).join('');
    const path=`${order.sessionId}/skills/${order.registrationId}/${hash}.${file.extension}`;
    const r=await fetch(`${c.url}/storage/v1/object/class-session-docs/${path}`,{method:'POST',redirect:'error',signal:AbortSignal.timeout(15000),
      headers:{apikey:c.key,authorization:`Bearer ${c.key}`,'content-type':file.type,'x-upsert':'false'},body:file.bytes});
    // A retry uploads the exact same hash/path. Other errors must not claim a
    // document was attached. The registration remains payable without upload.
    if(!r.ok){const error=await r.json().catch(()=>({}));if(!['Duplicate','ResourceAlreadyExists'].includes(error.error)&&String(error.statusCode)!=='409')throw Error('certificate_unavailable');}
    return ownerRest('rpc/attach_skills_certificate',{method:'POST',body:JSON.stringify({p_registration_id:order.registrationId,p_sha:hash,p_type:file.type,p_size:file.bytes.length})},c);
  },
  enabled:()=>Deno.env.get('SKILLS_SESSION_RESERVATIONS_ENABLED')!=='false',
  async publication(page:string){
    const r=await fetch(`${SITE}/data/block-selector-availability/${page}.json`,{cache:'no-store',redirect:'error',signal:AbortSignal.timeout(15000)});
    if(!r.ok)throw Error('calendar_refresh_required');return r.json();
  },
  async rpc(name:string,body:unknown){
    const c=ownerConfig();
    const r=await fetch(`${c.url}/rest/v1/rpc/${name}`,{method:'POST',redirect:'error',signal:AbortSignal.timeout(15000),
      headers:{apikey:c.key,authorization:`Bearer ${c.key}`,'content-type':'application/json'},body:JSON.stringify(body)});
    const value=await r.json();if(!r.ok)throw Error(value.message||'service_unavailable');return value;
  }
});
if(import.meta.main)Deno.serve(handler);
