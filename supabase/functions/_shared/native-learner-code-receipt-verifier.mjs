// Server-only, read-provider/record-evidence operation. Never sends email.
// No receipt/status supplied by a caller is trusted: receipt comes from the DB.
// Retrieval schema: https://resend.com/docs/api-reference/emails/retrieve-email
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ID=/^[A-Za-z0-9_-]{1,128}$/;
const EMAIL=/^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$/;
const STATES=new Set(['sent','delivered','delivery_delayed','bounced','failed','complained','suppressed','opened','clicked']);
const fail=reason=>({verified:false,reason});
const safeText=(s,max)=>typeof s==='string'&&s.trim()&&s.length<=max&&!/[\x00-\x1f\x7f]/.test(s);
async function boundedJSON(response){
 if(!response.body)throw Error('empty');
 const reader=response.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let bytes=0,text='';
 try{for(;;){const {done,value}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>65536)throw Error('large');text+=decoder.decode(value,{stream:true});}return JSON.parse(text+decoder.decode());}
 finally{try{await reader.cancel();}catch{/* Never expose provider response. */}reader.releaseLock();}
}
function expectedText(data){
 return `Your purchased online course access code is ready.\n\nProduct: ${data.product}\nCode: ${data.code}\n\nKeep this code private. Complete the online course before your skills session. For help, reply to this email or call 910-395-5193.`;
}
export function nativeLearnerCodeReceiptVerifier({rpc,env,request,now=()=>Date.now()}){
 return async function verify(deliveryId,lease){
  if(!UUID.test(deliveryId||'')||!UUID.test(lease||''))return fail('invalid_request');
  if(typeof rpc!=='function'||typeof env!=='function'||typeof request!=='function'||typeof now!=='function')return fail('verifier_unconfigured');
  let key;try{key=env('RESEND_API_KEY');}catch{return fail('verifier_unconfigured');}
  if(typeof key!=='string'||!key.trim()||/[\r\n]/.test(key))return fail('verifier_unconfigured');
  let data;try{data=await rpc('native_learner_code_receipt_context',{p_delivery_id:deliveryId,p_lease:lease});}catch{return fail('context_unknown');}
  if(data?.blocked===true)return fail('receipt_unavailable');
  if(!data||data.deliveryId!==deliveryId||data.lease!==lease||data.provider!=='resend'||!ID.test(data.providerId||'')||
   typeof data.recipient!=='string'||data.recipient.length>254||!EMAIL.test(data.recipient)||data.recipient!==data.recipient.trim().toLowerCase()||
   !safeText(data.product,256)||!safeText(data.code,8192)||typeof data.preparedAt!=='string'||!Number.isFinite(Date.parse(data.preparedAt)))return fail('context_invalid');
  let response;
  try{response=await request(`https://api.resend.com/emails/${encodeURIComponent(data.providerId)}`,{
   method:'GET',redirect:'error',signal:AbortSignal.timeout(12000),headers:{authorization:`Bearer ${key}`,accept:'application/json'}});}
  catch{return fail('provider_unavailable');}
  if(response?.status!==200)return fail(response?.status===401||response?.status===403?'provider_access_denied':response?.status===404?'receipt_not_found':'provider_unavailable');
  let email;try{email=await boundedJSON(response);}catch{return fail('provider_response_invalid');}
  // Exact receipt binding AND exact content are required. A same-recipient
  // email, a delivery event alone, or a caller's assertion is never evidence.
  if(email?.object!=='email'||email.id!==data.providerId||!Array.isArray(email.to)||email.to.length!==1||email.to[0]!==data.recipient||
   !Array.isArray(email.cc)||email.cc.length!==0||!Array.isArray(email.bcc)||email.bcc.length!==0||
   email.subject!=='Your purchased online course access'||email.text!==expectedText(data))return fail('receipt_mismatch');
  if(!STATES.has(email.last_event))return fail('provider_status_unverified');
  const created=typeof email.created_at==='string'?Date.parse(email.created_at):NaN;let current;
  try{current=now();}catch{return fail('clock_invalid');}
  if(!Number.isFinite(current)||!Number.isFinite(created)||created<Date.parse(data.preparedAt)||created>current+300000)return fail('receipt_time_invalid');
  let digest;try{digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(data.code)))].map(n=>n.toString(16).padStart(2,'0')).join('');}catch{return fail('verifier_unavailable');}
  const args={p_delivery_id:deliveryId,p_lease:lease,p_provider_id:data.providerId,p_recipient:data.recipient,
   p_product_key:data.product,p_code_sha256:digest,p_provider_created_at:email.created_at,p_status:email.last_event};
  // Retry the exact database evidence only, never a send or receipt substitution.
  for(let attempt=0;attempt<2;attempt++){
   let result;try{result=await rpc('native_reconcile_learner_code_receipt',args);}catch{continue;}
   if(result?.verified===true&&result.status===email.last_event&&typeof result.actualDeliveryConfirmed==='boolean')
    return {verified:true,status:email.last_event,actualDeliveryConfirmed:result.actualDeliveryConfirmed};
   if(result?.blocked===true)return fail('assignment_changed');
  }
  return fail('reconciliation_unknown');
 };
}
