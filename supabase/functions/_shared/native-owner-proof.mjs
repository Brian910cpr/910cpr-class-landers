import {sendNativeConfirmation} from './native-resend-adapter.mjs';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export function nativeOwnerProof({rpc,env,request,report=()=>{}}){return async()=>{
 if(!env('RESEND_API_KEY'))return {state:'unconfigured',actualDeliveryConfirmed:false};
 // Atomic durable claim precedes the sole provider attempt. Never release/retry it.
 const claim=await rpc('native_owner_transport_claim',{});
 if(claim?.claimed!==true)return {state:claim?.state||'not_authorized',replay:true,providerId:claim?.providerId||null,actualDeliveryConfirmed:false};
 if(!UUID.test(claim.proofId||''))return {state:'unknown',actualDeliveryConfirmed:false};
 let result;
 try{result=await sendNativeConfirmation({messageId:claim.proofId,recipient:'brian@910cpr.com',
 subject:'[TEST ONLY] 910CPR native checkout email transport proof',
 body:'TEST ONLY: This is the single owner-approved native checkout email transport test. No student was registered, no order was created, and no payment was charged. This tests email transport only, not the complete checkout flow.'},
 {apiKey:env('RESEND_API_KEY'),from:env('RESEND_FROM_EMAIL')||env('REQUIREMENT_FROM_EMAIL')||'910CPR <brian@910cpr.com>',replyTo:'brian@910cpr.com',request});}
 catch{result={outcome:'ambiguous',providerId:null,errorCode:'native_mail_request_unknown'};}
 const state=result.outcome==='sent'&&result.providerId?'accepted':result.outcome==='rejected'?'rejected':'unknown';
 const args={p_proof_id:claim.proofId,p_state:state,p_provider_id:state==='accepted'?result.providerId:null,p_error_code:result.errorCode||null};
 let settled;try{settled=await rpc('native_owner_transport_settle',args);}catch{/* Never resend. */}
 if(settled?.settled!==true&&settled?.replay!==true){report({event:'native_owner_proof_settlement_unknown',...args});return {state:'settlement_unknown',providerOutcome:state,providerId:args.p_provider_id,actualDeliveryConfirmed:false};}
 return {state,providerId:args.p_provider_id,actualDeliveryConfirmed:false};
};}
