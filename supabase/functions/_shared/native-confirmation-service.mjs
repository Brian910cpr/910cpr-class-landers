import {dispatchNativeConfirmations} from './native-confirmation-consumer.mjs';
import {sendNativeCheckoutClaim} from './native-resend-adapter.mjs';
import {nativeLearnerCodeService} from './native-learner-code-service.mjs';

// Existing server credentials stay inside this project. No new credential,
// recipient, template, body or provider can be supplied by an HTTP caller.
export function nativeConfirmationService({rpc,env,request,report=()=>{}}) {
 const configured=()=>Boolean(env('RESEND_API_KEY'));
 const codes=nativeLearnerCodeService({rpc,env,request,report});
 async function health(){
  const confirmation=await rpc('native_checkout_confirmation_health',{});
  const codeDelivery=await codes.health();
  return {...confirmation,codeDelivery,healthy:confirmation.healthy===true &&
   (codeDelivery.enabled===false || codeDelivery.healthy===true)};
 }
 async function deliverConfirmation(orderId=null,{limit=1}={}){
  if(!configured())return {configured:false,accepted:0,rejected:0,ambiguous:0,stopped:'mail_unconfigured',actualDeliveryConfirmed:false};
  const result=await dispatchNativeConfirmations({orderId,limit,
   claim:args=>rpc('native_checkout_claim_confirmation',args),
   settle:args=>rpc('native_checkout_settle_confirmation',args),
   send:job=>sendNativeCheckoutClaim(job,{apiKey:env('RESEND_API_KEY'),from:env('RESEND_FROM_EMAIL')||env('REQUIREMENT_FROM_EMAIL')||'910CPR <brian@910cpr.com>',replyTo:'brian@910cpr.com',request})});
  if(result.pendingSettlement){
   const outcome=result.pendingSettlement;
   // Retry only the idempotent settlement of the exact known outcome. Never
   // call the provider again after acceptance or an uncertain response.
   let settled;try{settled=await rpc('native_checkout_settle_confirmation',outcome);}catch{/* Preserve the exact receipt for private reconciliation. */}
   if(settled?.settled===true||settled?.replay===true){
    result.stopped=null;result.continuationRequired=true;result[result.pendingSettlement.p_outcome==='sent'?'accepted':result.pendingSettlement.p_outcome]++;
   }else report({event:'native_confirmation_settlement_unknown',...outcome});
   delete result.pendingSettlement;
  }
  return {configured:true,...result};
 }
 async function deliver(orderId=null,{limit=10}={}){
  if(!Number.isInteger(limit)||limit<1||limit>10 || (orderId!==null &&
   (typeof orderId!=='string'||!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(orderId))))
   throw Error('native_confirmation_consumer_invalid_configuration');
  const result={configured:configured(),claimed:0,accepted:0,rejected:0,ambiguous:0,blocked:0,
   stopped:null,disabled:false,empty:false,limitReached:false,actualDeliveryConfirmed:false};
  if(!result.configured){result.stopped='mail_unconfigured';return result;}
  let slots=0,disabled=0;const exhausted=new Map();
  // A slot is one selected lane, not one successful send. Empty/disabled work
  // never falls through to a second provider attempt in the same slot. The
  // durable turn alternates across scheduled limit=1 invocations.
  for(;slots<limit;slots++){
   let choice;
   try{choice=await rpc('native_mail_next_lane',{});}catch{result.stopped='lane_unknown';break;}
   if(!['confirmation','learner_code'].includes(choice?.lane)){result.stopped='lane_invalid';break;}
   const part=await (choice.lane==='learner_code'?codes.deliver(orderId,{limit:1}):deliverConfirmation(orderId,{limit:1}));
   for(const key of ['claimed','accepted','rejected','ambiguous','blocked'])result[key]+=part[key]||0;
   exhausted.set(choice.lane,part.empty===true||part.disabled===true);
   if(part.disabled===true)disabled++;
   if(part.configured===false)result.configured=false;
   result.stopped=part.stopped||null;
   if(part.continuationRequired)result.continuationRequired=true;
   if(result.stopped||result.ambiguous||result.rejected||result.continuationRequired){slots++;break;}
  }
  result.disabled=slots>0&&disabled===slots;
  result.empty=result.claimed===0&&!result.disabled&&!result.stopped;
  result.limitReached=slots===limit&&result.claimed>0&&!result.stopped&&!result.disabled&&[...exhausted.values()].some(value=>!value);
  return result;
 }
 return {configured,deliver,health};
}
