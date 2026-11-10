import {skillsOffers} from './policy.mjs';
import {certificateInput} from './checkout.mjs';
function studentInput(value){
  const student={firstName:String(value?.firstName||'').trim(),lastName:String(value?.lastName||'').trim(),email:String(value?.email||'').trim().toLowerCase(),phone:String(value?.phone||'').trim(),onlineCompletionAcknowledged:value?.onlineCompletionAcknowledged===true};
  if(!student.firstName||!student.lastName||student.firstName.length>100||student.lastName.length>100||student.email.length>254||!/^\S+@\S+\.\S+$/.test(student.email)||!student.phone||student.phone.length>50||!student.onlineCompletionAcknowledged)throw Error('invalid_student');
  return student;
}
export async function bundleRoute(route,body,key,{rpc,publication,now,publicOrder,uploadBundle}){
  if(body.context!=='bls-skills')throw Error('invalid_context');
  if(route==='bundle-reserve'){
    if(typeof body.selectionId!=='string'||body.selectionId.length>2048)throw Error('invalid_request');
    const args={p_idempotency_key:key,p_context:body.context,p_offer:{selectionId:body.selectionId},p_student:studentInput(body.student)};
    let order=await rpc('reserve_bls_bundle',args);
    if(order?.status==='offer_required'){
      const offer=skillsOffers(await publication('bls'),body.context,now(),'210549').find(o=>o.selectionId===body.selectionId);
      if(!offer)throw Error('session_not_available');
      order=await rpc('reserve_bls_bundle',{...args,p_offer:offer});
    }
    if(!order?.orderId||!order.sessionId||order.total!==9500)throw Error('payment_mismatch');
    return {ok:true,status:'held',orderId:order.orderId,sessionId:order.sessionId,holdExpiresAt:order.holdExpiresAt};
  }
  const order=await rpc('skills_bundle_order',{p_key:key});
  if(!order?.orderId||order.total!==9500)throw Error('payment_mismatch');
  if(route==='bundle-certificate')return {ok:true,...await uploadBundle(key,order,certificateInput(body.certificate))};
  const reservation={startsAt:order.startsAt,location:order.location};
  if(order.status==='paid')return {ok:true,paymentStatus:'paid',reservation};
  if(order.reconciliationError)throw Error('payment_reconciliation_required');
  if(!['held','checkout_open'].includes(order.status)||Date.parse(order.holdExpiresAt)<=now())throw Error('hold_expired');
  if(route==='bundle-status'){
    const status=order.checkoutId?await publicOrder('status',key,order):{status:'payment_pending'};
    if(status.status==='payment_review')throw Error('payment_reconciliation_required');
    return {ok:true,paymentStatus:status.status==='paid'?'paid':'pending',reservation,holdExpiresAt:order.holdExpiresAt};
  }
  if(route!=='bundle-checkout')throw Error('invalid_request');
  const payment=await publicOrder('checkout',key,order);
  if(typeof payment.checkoutUrl!=='string'||!payment.checkoutUrl.startsWith('https://checkout.stripe.com/'))throw Error('payment_unavailable');
  return {ok:true,paymentStatus:'pending',checkoutUrl:payment.checkoutUrl,reservation};
}
