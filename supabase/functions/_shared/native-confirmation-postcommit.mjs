// Only invoke after the registration/order RPC has committed. This starts no
// transaction, never changes registration status, and cannot send to a caller-
// chosen recipient. Durable queue eligibility is still checked by the service.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export function nativeConfirmationPostcommit({service,waitUntil,report=()=>{}}){
 const record=value=>{try{report(value);}catch{/* Logging cannot alter a committed booking. */}};
 return async function afterNativeCommit(orderId){
  if(typeof orderId!=='string'||!UUID.test(orderId))return;
  const work=Promise.resolve().then(async()=>{
   if(!service.configured())return;
   // A supported ten-student order can also include one owner fulfillment
   // notice. Two bounded batches cover that order without an unbounded drain.
   for(let batch=0;batch<2;batch++){
    const result=await service.deliver(orderId);
    if(result.stopped||result.rejected||result.ambiguous){record({event:'native_confirmation_requires_attention',orderId,
     accepted:result.accepted||0,rejected:result.rejected||0,ambiguous:result.ambiguous||0,
     reason:['claim_unknown','claim_invalid','duplicate_claim','settlement_unknown','mail_unconfigured'].includes(result.stopped)?result.stopped:'delivery_failure'});break;}
    if(!result.limitReached&&!result.continuationRequired)break;
    if(batch===1)record({event:'native_confirmation_requires_attention',orderId,reason:'batch_limit_reached'});
   }
  }).catch(()=>record({event:'native_confirmation_postcommit_failed',orderId}));
  if(typeof waitUntil==='function'){
   try{waitUntil(work);return;}catch{record({event:'native_confirmation_background_unavailable',orderId});}
  }
  // Local/test runtimes without waitUntil await the same task, not a new send.
  await work;
 };
}
