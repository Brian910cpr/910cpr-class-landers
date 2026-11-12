// Execute the real generic HTTP adapter with injected, synthetic-only requests.
// Every provider request is intercepted. No network, credentials or sending.
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import {webcrypto} from 'node:crypto';
import {nativeConfirmationService} from '../../supabase/functions/_shared/native-confirmation-service.mjs';
import {nativeConfirmationPostcommit} from '../../supabase/functions/_shared/native-confirmation-postcommit.mjs';
import {publicOrderVersion,publicOrderReturnPath,settlePublicOrder} from '../../supabase/functions/public-registration/public-order-routing.mjs';
import {genericCheckout,boundedCheckoutJSON,fullAppointmentSession} from '../../supabase/functions/public-registration/generic.mjs';
import {fullCoursePolicyRpcArgs} from '../../supabase/functions/public-registration/full-course.mjs';
import {scalar,service} from '../native-bls-admission-proof.mjs';
const source=readFileSync(new URL('../../supabase/functions/public-registration/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
export const storedOrder=(db,id)=>service(db,()=>scalar(db,`select to_jsonb(o)||jsonb_build_object('landerware_public_order_students',
 (select coalesce(jsonb_agg(to_jsonb(st)),'[]') from landerware_public_order_students st where st.order_id=o.id))
 from landerware_public_orders o where id=$1`,[id]));
export function returnHTTP(db,claim,provider){
 const calls=[];let handler,providerResponse=provider,providerError=null;
 const context=vm.createContext({nativeConfirmationService,nativeConfirmationPostcommit,publicOrderVersion,publicOrderReturnPath,
  settlePublicOrder,genericCheckout,boundedCheckoutJSON,fullAppointmentSession,fullCoursePolicyRpcArgs,
  URL,URLSearchParams,Request,Response,Headers,AbortSignal,Date,Error,Set,Promise,JSON,Object,Array,Number,String,Uint8Array,crypto:webcrypto,console,
  Deno:{env:{get:k=>({SUPABASE_URL:'https://synthetic-db.invalid',SUPABASE_SERVICE_ROLE_KEY:'synthetic-noncredential',STRIPE_SECRET_KEY:'sk_test_SYNTHETIC_NONCREDENTIAL'})[k]},serve:fn=>handler=fn},
  fetch:async(url,init={})=>{
   const u=new URL(url),method=init.method||'GET';calls.push({path:u.pathname,method});
   if(u.origin==='https://api.stripe.com'){
    assert.equal(method,'GET','return/status may never create a Checkout or charge');
    const o=await storedOrder(db,claim.orderId);
    assert.equal(u.pathname,'/v1/checkout/sessions/'+o.stripe_checkout_session_id,'lookup must use stored Checkout identity');
    if(providerError)throw Error(providerError);
    return Response.json(providerResponse);
   }
   assert.equal(u.origin,'https://synthetic-db.invalid','all other external requests prohibited');
   assert.equal(init.headers.apikey,'synthetic-noncredential');
   if(u.pathname==='/rest/v1/landerware_public_orders'){
    assert.equal(method,'GET','recovery may not overwrite binding or create an order');
    const o=await storedOrder(db,claim.orderId);
    if(u.searchParams.has('id'))assert.equal(u.searchParams.get('id'),'eq.'+claim.orderId);
    else assert.equal(u.searchParams.get('recovery_token'),'eq.'+o.recovery_token);
    return Response.json([o]);
   }
   const name=u.pathname.slice('/rest/v1/rpc/'.length),a=JSON.parse(init.body);
   assert.equal(method,'POST');
   try{
    if(name==='native_checkout_receipt'){
     assert.equal(a.p_key,claim.key);
     return Response.json(await service(db,()=>scalar(db,'select native_checkout_receipt($1)',[a.p_key])));
    }
    assert.ok(['native_checkout_record_payment','native_checkout_finalize_order'].includes(name),'unexpected RPC '+name);
    assert.equal(a.p_order_id,claim.orderId);
    if(name==='native_checkout_finalize_order')assert.equal((await storedOrder(db,claim.orderId)).payment_evidence.payment_status,'paid','payment receipt committed before finalizer request');
    const result=await service(db,()=>scalar(db,`select ${name}($1,$2,$3::jsonb)`,[a.p_order_id,a.p_stripe_payment_intent_id,JSON.stringify(a.p_evidence)]));
    return Response.json(result);
   }catch(e){return Response.json({message:e.message},{status:400});}
  }});
 vm.runInContext(stripTypeScriptTypes(source),context);
 return {calls,provider:v=>providerResponse=v,failProvider:v=>providerError=v,
  send:async(action='status')=>{
   const response=await handler(new Request('https://synthetic.invalid/public-registration/generic/'+action,{method:action==='checkout'?'POST':'GET',headers:{origin:'https://www.910cpr.com','idempotency-key':claim.key,'content-type':'application/json'},...(action==='checkout'?{body:'{}'}:{})}));
   return {status:response.status,body:await response.json()};
  }};
}
