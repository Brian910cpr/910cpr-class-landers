import {authorizedOwner} from '../_shared/owner-auth.ts';
import {ownerRest} from '../_shared/owner-session.ts';
import {nativeConfirmationService} from '../_shared/native-confirmation-service.mjs';
import {nativeLearnerCodeReceiptVerifier} from '../_shared/native-learner-code-receipt-verifier.mjs';
import {nativeOwnerProof} from '../_shared/native-owner-proof.mjs';
import {nativeConfirmationHandler} from './handler.mjs';
import {nativeScheduledHandler} from './scheduled.mjs';
// Scheduled one-slot worst case: ten bounded 7s RPCs plus one 12s send,
// within the existing 110s durable scheduler lease. No second lane fallback.
const service=nativeConfirmationService({
 rpc:(name:string,args:unknown)=>ownerRest(`rpc/${name}`,{method:'POST',body:JSON.stringify(args),signal:AbortSignal.timeout(7000)}),
 env:(name:string)=>Deno.env.get(name),request:fetch,
 // Private operational receipt only; contains no recipient, body or credentials.
 report:(receipt:unknown)=>console.error(JSON.stringify(receipt))
});
const proof=nativeOwnerProof({
 rpc:(name:string,args:unknown)=>ownerRest(`rpc/${name}`,{method:'POST',body:JSON.stringify(args),signal:AbortSignal.timeout(7000)}),
 env:(name:string)=>Deno.env.get(name),request:fetch,
 report:(receipt:unknown)=>console.error(JSON.stringify(receipt))
});
// Optional owner action: exact delivery selection only, never a queue drain/send.
const verifyBoundReceipt=nativeLearnerCodeReceiptVerifier({
 rpc:(name:string,args:unknown)=>ownerRest(`rpc/${name}`,{method:'POST',body:JSON.stringify(args),signal:AbortSignal.timeout(7000)}),
 env:(name:string)=>Deno.env.get(name),request:fetch
});
const verifyReceipt=async(deliveryId:string)=>{
 const target=await ownerRest('rpc/native_learner_code_receipt_target',{
  method:'POST',body:JSON.stringify({p_delivery_id:deliveryId}),signal:AbortSignal.timeout(7000)
 });
 if(target?.blocked===true)return {verified:false,reason:'receipt_unavailable'};
 if(target?.deliveryId!==deliveryId||typeof target?.lease!=='string')return {verified:false,reason:'context_invalid'};
 return verifyBoundReceipt(deliveryId,target.lease);
};
const ownerHandler=nativeConfirmationHandler({authorized:authorizedOwner,service,proof,verifyReceipt,
 schedulerStatus:()=>ownerRest('rpc/native_checkout_scheduler_status',{method:'POST',body:'{}',signal:AbortSignal.timeout(7000)})
});
const scheduledHandler=nativeScheduledHandler({service,
 rpc:(name:string,args:unknown)=>ownerRest(`rpc/${name}`,{method:'POST',body:JSON.stringify(args),signal:AbortSignal.timeout(7000)})
});
Deno.serve(req=>new URL(req.url).pathname.endsWith('/scheduled')?scheduledHandler(req):ownerHandler(req));
