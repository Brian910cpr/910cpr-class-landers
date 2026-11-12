// Private token/lease transport. Never log or return learner codes to callers.
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export async function dispatchLearnerCodes(env,rpc){
 if(env.CHECKOUT_CODE_DELIVERY_ENABLED!=='true')return {disabled:true,accepted:0,failed:0,actualDeliveryConfirmed:false};
 let accepted=0,failed=0;
 for(let i=0;i<10;i++){
  const job=await rpc(env,'landerware_claim_learner_code');if(!job?.deliveryId)break;
  const args={p_delivery_id:job.deliveryId,p_lease:job.lease};
  const data=await rpc(env,'landerware_prepare_learner_code',args);
  if(data.blocked)continue;
  if(typeof data.code!=='string'||!data.code.trim()||typeof data.recipient!=='string'||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.recipient))throw Error('learner_code_data_invalid');
  const text=`Your purchased online course access code is ready.\n\nProduct: ${data.product}\nCode: ${data.code}\n\nKeep this code private. Complete the online course before your skills session. For help, reply to this email or call 910-395-5193.`;
  let result;
  try{result=await env.EMAIL.send({from:{email:env.FROM_EMAIL,name:'910CPR'},...(env.REPLY_TO_EMAIL?{replyTo:env.REPLY_TO_EMAIL}:{}),to:data.recipient,subject:'Your purchased online course access',text,html:'<p>'+escape(text).replace(/\n/g,'<br>')+'</p>'});}
  catch(error){const known=['E_SENDER_NOT_VERIFIED','E_RATE_LIMIT_EXCEEDED'].includes(error?.code);
   await rpc(env,'landerware_settle_learner_code',{...args,p_outcome:known?'rejected':'ambiguous',p_provider_id:null,p_error:known?error.code:'provider_result_unknown'});failed++;continue;}
  if(!result?.messageId){await rpc(env,'landerware_settle_learner_code',{...args,p_outcome:'ambiguous',p_provider_id:null,p_error:'provider_receipt_missing'});failed++;continue;}
  // A failed durable acceptance write cannot cause an automatic resend.
  await rpc(env,'landerware_settle_learner_code',{...args,p_outcome:'accepted',p_provider_id:result.messageId,p_error:null});accepted++;
 }
 return {accepted,failed,actualDeliveryConfirmed:false};
}
