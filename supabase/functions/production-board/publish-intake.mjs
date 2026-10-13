// Owner-authenticated structured declaration, never an arbitrary issue parser.
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export async function publishIntake(cardId,body,rpc){
  const keys=['issue_id','expected_version','request_id','blocked','source_state','worker_safe','source_ref','checked_at'];
  if(!uuid.test(cardId||'')||!body||typeof body!=='object'||Array.isArray(body)
    ||Object.keys(body).some(k=>!keys.includes(k))
    ||!Number.isSafeInteger(body.issue_id)||body.issue_id<1
    ||typeof body.expected_version!=='string'||!/^[1-9][0-9]{0,17}$/.test(body.expected_version)
    ||!uuid.test(body.request_id||'')||typeof body.blocked!=='boolean'||typeof body.worker_safe!=='boolean'
    ||!['action_required','already_corrected','unknown'].includes(body.source_state)
    ||typeof body.source_ref!=='string'||!body.source_ref.trim()||body.source_ref.length>2000
    ||typeof body.checked_at!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(body.checked_at)
    ||!Number.isFinite(Date.parse(body.checked_at))||new Date(body.checked_at).toISOString()!==body.checked_at){
    return {status:400,body:{error:'Invalid intake declaration',committed:false,can_execute:false}};
  }
  try{
    const result=await rpc({p_card:cardId,p_issue:body.issue_id,p_version:body.expected_version,
      p_request:body.request_id,p_blocked:body.blocked,p_source_state:body.source_state,
      p_worker_safe:body.worker_safe,p_source_ref:body.source_ref,p_checked_at:body.checked_at});
    if(!result||result.request_id!==body.request_id||result.can_execute!==false
      ||typeof result.replayed!=='boolean'||typeof result.version!=='string'
      ||!/^[1-9][0-9]*$/.test(result.version))throw Error('Invalid acknowledgement');
    return {status:200,body:{request_id:result.request_id,version:result.version,replayed:result.replayed,
      committed:true,can_execute:false,provenance:'owner_assertion_not_source_verification'}};
  }catch(error){
    const reason=error instanceof Error?error.message:"";
    if(["stale_card_version","card_resolved","intake_issue_immutable","idempotency_conflict","source_check_stale"].includes(reason)){
      return {status:409,body:{error:reason,committed:false,can_execute:false}};
    }
    return {status:503,body:{error:'Intake commit not confirmed; refresh state and retry the same request ID',
      committed:false,can_execute:false}};
  }
}
