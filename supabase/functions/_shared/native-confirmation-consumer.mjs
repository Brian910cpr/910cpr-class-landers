// Pure orchestration: no database client, credentials, fetch, timer or activation.
// Supply service-only RPC adapters and sendNativeCheckoutClaim(job, mailOptions).
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const PROVIDER_ID = /^[A-Za-z0-9_-]{1,128}$/;
const ERROR_CODE = /^[a-z0-9_]{1,100}$/;

function normalizedOutcome(result) {
  if (result?.outcome === 'sent' && typeof result.providerId === 'string' && PROVIDER_ID.test(result.providerId)) {
    return { outcome: 'sent', providerId: result.providerId, errorCode: null };
  }
  if (result?.outcome === 'rejected' || result?.outcome === 'ambiguous') {
    return { outcome: result.outcome, providerId: null,
      errorCode: typeof result.errorCode === 'string' && ERROR_CODE.test(result.errorCode) ? result.errorCode : 'native_mail_result_unknown' };
  }
  return { outcome: 'ambiguous', providerId: null, errorCode: 'native_mail_result_unknown' };
}

export async function dispatchNativeConfirmations({ orderId = null, limit = 10, claim, settle, send } = {}) {
  if ((orderId !== null && !UUID.test(orderId)) || !Number.isInteger(limit) || limit < 1 || limit > 10 ||
      typeof claim !== 'function' || typeof settle !== 'function' || typeof send !== 'function') {
    throw Error('native_confirmation_consumer_invalid_configuration');
  }
  const summary = {
    claimed: 0, accepted: 0, rejected: 0, ambiguous: 0, stopped: null,
    disabled: false, empty: false, actualDeliveryConfirmed: false,
  };
  const seen = new Set();
  for (let i = 0; i < limit; i++) {
    let job;
    try { job = await claim({ p_order_id: orderId }); }
    catch { summary.stopped = 'claim_unknown'; break; }
    if (job?.disabled === true && !job.messageId) { summary.disabled = true; break; }
    if (job?.empty === true && !job.messageId) { summary.empty = true; break; }
    if (!job || !UUID.test(job.messageId || '') || !UUID.test(job.lease || '') || job.disabled === true || job.empty === true) {
      // A malformed claim may have acquired a lease. Do not guess its identity.
      summary.stopped = 'claim_invalid'; break;
    }
    if (seen.has(job.messageId)) { summary.stopped = 'duplicate_claim'; break; }
    seen.add(job.messageId);
    summary.claimed++;
    let result;
    try { result = normalizedOutcome(await send(job)); }
    catch { result = { outcome: 'ambiguous', providerId: null, errorCode: 'native_mail_request_unknown' }; }
    const args = {
      p_message_id: job.messageId, p_lease: job.lease, p_outcome: result.outcome,
      p_provider_id: result.providerId, p_error: result.errorCode,
    };
    let settled;
    try { settled = await settle(args); } catch { /* A write may have completed. */ }
    if (settled?.settled !== true && settled?.replay !== true) {
      summary.stopped = 'settlement_unknown';
      // Internal reconciliation data only. The authenticated caller must retain
      // this outcome and retry/reconcile settlement, never issue a second send.
      // Do not return this private field from a public registration response.
      summary.pendingSettlement = args;
      break;
    }
    if (result.outcome === 'sent') summary.accepted++;
    else summary[result.outcome]++;
  }
  return summary;
}
