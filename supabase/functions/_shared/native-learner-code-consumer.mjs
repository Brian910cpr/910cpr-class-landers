// Service-only orchestration. Prepared content never leaves the send call.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const RECEIPT = /^[A-Za-z0-9_-]{1,128}$/;
const SAFE_ERROR = /^native_mail_(?:not_configured|invalid_code|invalid_claim|request_unknown|response_unknown|receipt_missing|receipt_unreadable|http_[0-9]{3})$/;
function normalize(result) {
  if (result?.outcome === 'sent' && typeof result.providerId === 'string' && RECEIPT.test(result.providerId))
    return {outcome:'accepted', providerId:result.providerId, errorCode:null};
  if (result?.outcome === 'rejected' || result?.outcome === 'ambiguous')
    return {outcome:result.outcome, providerId:null,
      errorCode:typeof result.errorCode === 'string' && SAFE_ERROR.test(result.errorCode) ? result.errorCode : 'native_mail_result_unknown'};
  return {outcome:'ambiguous', providerId:null, errorCode:'native_mail_result_unknown'};
}
export async function dispatchNativeLearnerCodes({orderId=null,limit=10,claim,prepare,send,settle}={}) {
  if ((orderId !== null && (typeof orderId !== 'string' || !UUID.test(orderId))) ||
      !Number.isInteger(limit) || limit < 1 || limit > 10 ||
      [claim,prepare,send,settle].some(f=>typeof f !== 'function')) throw Error('native_code_consumer_invalid_configuration');
  const result={claimed:0,accepted:0,rejected:0,ambiguous:0,blocked:0,stopped:null,
    disabled:false,empty:false,limitReached:false,actualDeliveryConfirmed:false};
  const seen=new Set();
  for(let i=0;i<limit;i++) {
    let job;
    try {job=await claim({p_order_id:orderId});} catch {result.stopped='claim_unknown';break;}
    if(job?.disabled===true && !job.deliveryId){result.disabled=true;break;}
    if(job?.empty===true && !job.deliveryId){result.empty=true;break;}
    if(!job || !UUID.test(job.deliveryId||'') || !UUID.test(job.lease||'') || job.disabled===true || job.empty===true) {result.stopped='claim_invalid';break;}
    if(seen.has(job.deliveryId)){result.stopped='duplicate_claim';break;}
    seen.add(job.deliveryId);result.claimed++;
    const identity={p_delivery_id:job.deliveryId,p_lease:job.lease};
    let prepared;
    try {prepared=await prepare(identity);} catch {result.stopped='prepare_unknown';break;}
    if(prepared?.blocked===true){result.blocked++;continue;}
    // Malformed prepare may have exposed a code. Do not guess or resend.
    if(!prepared || typeof prepared.recipient!=='string' || typeof prepared.product!=='string' || typeof prepared.code!=='string') {result.stopped='prepare_invalid';break;}
    let outcome;
    try {outcome=normalize(await send({deliveryId:job.deliveryId,recipient:prepared.recipient,product:prepared.product,code:prepared.code}));}
    catch {outcome={outcome:'ambiguous',providerId:null,errorCode:'native_mail_request_unknown'};}
    prepared=null;
    const args={...identity,p_outcome:outcome.outcome,p_provider_id:outcome.providerId,p_error:outcome.errorCode};
    let settled;
    try {settled=await settle(args);} catch { /* Outcome may already be durable. */ }
    if(settled?.settled!==true && settled?.replay!==true){result.stopped='settlement_unknown';result.pendingSettlement=args;break;}
    result[outcome.outcome]++;
    if(outcome.outcome==='ambiguous'){result.stopped='provider_ambiguous';break;}
  }
  result.limitReached=result.claimed===limit && !result.stopped && !result.disabled && !result.empty;
  return result;
}
