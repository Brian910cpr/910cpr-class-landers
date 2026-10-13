// Called only after owner authentication. Identity/provenance is bound by the
// gateway; clients cannot submit canonical source/blocker/worker-safe state.
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export async function dispatchDecision(cardId, body, rpc) {
  if (!uuid.test(cardId || '') || !body || typeof body !== 'object'
      || !Number.isSafeInteger(body.issue_id) || body.issue_id < 1
      || typeof body.expected_version !== 'string' || !/^[1-9][0-9]{0,17}$/.test(body.expected_version)
      || !uuid.test(body.request_id || '') || !['selection','pre_side_effect'].includes(body.phase)
      || (body.phase === 'selection' ? body.reservation_id != null : !uuid.test(body.reservation_id || ''))
      || Object.keys(body).some(k => !['issue_id','expected_version','request_id','phase','reservation_id'].includes(k))) {
    return {status:400, body:{error:'Invalid dispatch request',can_execute:false}};
  }
  try {
    // PostgREST returns only after transaction commit, including deferred checks.
    // A transport error/timeout is indeterminate; retry the SAME request ID.
    const result = await rpc({p_card:cardId,p_issue:body.issue_id,p_version:body.expected_version,
      p_request:body.request_id,p_phase:body.phase,p_reservation:body.reservation_id ?? null});
    if (!result || result.request_id !== body.request_id || result.can_execute !== false
        || typeof result.replayed !== 'boolean' || !['skip','review','reserved'].includes(result.decision)
        || typeof result.reason !== 'string' || typeof result.version !== 'string') throw new Error('Invalid acknowledgement');
    return {status:200,body:{...result,committed:true,can_execute:false}};
  } catch {
    return {status:503,body:{error:'Dispatch commit not confirmed; retry the same request ID',committed:false,can_execute:false}};
  }
}
