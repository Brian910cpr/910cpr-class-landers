import {dispatchNativeConfirmations} from './native-confirmation-consumer.mjs';
import {sendNativeCheckoutClaim} from './native-resend-adapter.mjs';

// Existing server credentials stay inside this project. No new credential,
// recipient, template, body or provider can be supplied by an HTTP caller.
export function nativeConfirmationService({rpc,env,request,report=()=>{}}) {
 const configured=()=>Boolean(env('RESEND_API_KEY'));
 const health=()=>rpc('native_checkout_confirmation_health',{});
 async function deliver(orderId=null){
  if(!configured())return {configured:false,accepted:0,rejected:0,ambiguous:0,stopped:'mail_unconfigured',actualDeliveryConfirmed:false};
  const result=await dispatchNativeConfirmations({orderId,
   claim:args=>rpc('native_checkout_claim_confirmation',args),
   settle:args=>rpc('native_checkout_settle_confirmation',args),
   send:job=>sendNativeCheckoutClaim(job,{apiKey:env('RESEND_API_KEY'),from:env('RESEND_FROM_EMAIL')||env('REQUIREMENT_FROM_EMAIL')||'910CPR <brian@910cpr.com>',replyTo:'brian@910cpr.com',request})});
  if(result.pendingSettlement){
   const outcome=result.pendingSettlement;
   // Retry only the idempotent settlement of the exact known outcome. Never
   // call the provider again after acceptance or an uncertain response.
   let settled;try{settled=await rpc('native_checkout_settle_confirmation',outcome);}catch{/* Preserve the exact receipt for private reconciliation. */}
   if(settled?.settled===true||settled?.replay===true){
    result.stopped=null;result[result.pendingSettlement.p_outcome==='sent'?'accepted':result.pendingSettlement.p_outcome]++;
   }else report({event:'native_confirmation_settlement_unknown',...outcome});
   delete result.pendingSettlement;
  }
  return {configured:true,...result};
 }
 return {configured,deliver,health};
}
