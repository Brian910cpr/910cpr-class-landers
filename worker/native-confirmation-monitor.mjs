// Component observer only. Native registration and recipient delivery still
// require separate end-to-end proof. Every dependency is explicit for testing.
export const ENDPOINT = 'https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/native-checkout-confirmations';
export const EXPECTED_INTERVAL_MS = 60_000;
export const STALE_AFTER_MS = 180_000;
const MAX_RESPONSE = 64 * 1024;
const LATCHES = new Set(['authorization_denied', 'retry_outcome_unknown']);
const iso = value => new Date(value).toISOString();
const timestamp = value => typeof value === 'string' && Number.isFinite(Date.parse(value)) ? iso(Date.parse(value)) : null;
const count = value => Number.isSafeInteger(value) && value >= 0 ? value : null;

export function assessNativeQueue(payload, now = Date.now()) {
  const h = payload?.health || {};
  const lastPollAt = timestamp(h.lastPollAt), lastAcceptedAt = timestamp(h.lastAcceptedAt);
  const age = lastPollAt ? now - Date.parse(lastPollAt) : Infinity;
  const enabled = h.enabled === true && h.disabled !== true;
  const provider = h.provider === 'resend' ? 'resend' : null;
  const counts = Object.fromEntries(['queued', 'late', 'stuck', 'failures'].map(k => [k, count(h[k])]));
  const observerFresh = h.observerFresh === true && age >= -30_000 && age < STALE_AFTER_MS;
  const configured = payload?.configured === true;
  let reason = !configured ? 'mail_unconfigured' : !enabled ? 'delivery_disabled' : !provider ? 'provider_not_resend' :
    Object.values(counts).includes(null) ? 'health_contract_invalid' : !observerFresh ? 'consumer_stale' :
    counts.stuck ? 'processing_stuck' : counts.failures ? 'delivery_failures' : counts.late ? 'queue_late' :
    h.healthy !== true ? 'queue_unhealthy' : null;
  return {configured, enabled, provider, lastPollAt, lastAcceptedAt, ...counts, observerFresh,
    queueHealthy: reason === null, reason, actualDeliveryConfirmed: false};
}

export function assessMonitorState(state, now = Date.now()) {
  const checked = timestamp(state?.observerCheckedAt);
  const age = checked ? now - Date.parse(checked) : Infinity;
  const observerStale = age < -30_000 || age >= STALE_AFTER_MS;
  // Reassess timestamps at read time. A previously green result is not timeless.
  const queue = state?.queue;
  const pollAge = timestamp(queue?.lastPollAt) ? now - Date.parse(queue.lastPollAt) : Infinity;
  const consumerStale = pollAge < -30_000 || pollAge >= STALE_AFTER_MS;
  return {observerStale, consumerStale, retryLatched: Boolean(state?.latch),
    queueHealthy: !observerStale && !consumerStale && !state?.latch && !state?.error && queue?.queueHealthy === true,
    actualDeliveryConfirmed: false};
}

async function readJSON(response) {
  if (!response?.body) throw Error('response_invalid');
  const reader = response.body.getReader(), decoder = new TextDecoder('utf-8', {fatal: true});
  let bytes = 0, value = '';
  try {
    for (;;) {
      const chunk = await reader.read(); if (chunk.done) break;
      bytes += chunk.value.byteLength; if (bytes > MAX_RESPONSE) throw Error('response_invalid');
      value += decoder.decode(chunk.value, {stream: true});
    }
    return JSON.parse(value + decoder.decode());
  } finally { try { await reader.cancel(); } catch {} }
}

function previousState(previous) {
  // Never copy arbitrary old state, provider errors, private IDs or credentials.
  return {
    lastRetryAttemptAt: timestamp(previous?.lastRetryAttemptAt),
    lastRetryCompletedAt: timestamp(previous?.lastRetryCompletedAt),
    latch: LATCHES.has(previous?.latch) ? previous.latch : null,
  };
}

function deliverySummary(value) {
  if (!value || value.configured !== true || value.actualDeliveryConfirmed !== false ||
      ['accepted', 'rejected', 'ambiguous'].some(k => count(value[k]) === null || value[k] > 10) ||
      (value.stopped !== null && value.stopped !== undefined && typeof value.stopped !== 'string')) return null;
  const stops = new Set(['claim_unknown', 'claim_invalid', 'duplicate_claim', 'settlement_unknown', 'mail_unconfigured']);
  return {accepted: value.accepted, rejected: value.rejected, ambiguous: value.ambiguous,
    disabled: value.disabled === true, stopped: value.stopped ? (stops.has(value.stopped) ? value.stopped : 'delivery_stopped') : null,
    actualDeliveryConfirmed: false};
}

export async function checkNativeConfirmations({mode = 'status', retryEnabled = false, ownerKey, request, stateStore, now = () => Date.now()} = {}) {
  if (!['status', 'retry'].includes(mode) || typeof request !== 'function' || !stateStore ||
      typeof stateStore.load !== 'function' || typeof stateStore.save !== 'function') throw Error('monitor_configuration_invalid');
  let previous;
  try { previous = await stateStore.load(); } catch { throw Error('monitor_state_unavailable'); }
  const state = {...previousState(previous), observerCheckedAt: null, action: 'not_started', error: null, queue: null};
  const finish = async () => {
    await stateStore.save(state);
    return {...state, monitor: assessMonitorState(state, now())};
  };
  if (state.latch === 'authorization_denied') { state.action = 'review_required'; state.error = state.latch; return finish(); }
  if (typeof ownerKey !== 'string' || !ownerKey.trim() || /[\x00-\x20\x7f]/.test(ownerKey)) {
    state.action = 'not_configured'; state.error = 'owner_auth_unconfigured'; return finish();
  }
  const options = {redirect: 'error', headers: {'x-hot-sync-admin-key': ownerKey, accept: 'application/json'}};
  let response, payload;
  try { response = await request(`${ENDPOINT}/status`, {...options, method: 'GET', signal: AbortSignal.timeout(45_000)}); }
  catch { state.action = 'status_unknown'; state.error = 'status_request_unknown'; return finish(); }
  state.observerCheckedAt = iso(now());
  if ([401, 403].includes(response.status)) {
    state.action = 'authorization_denied'; state.error = 'owner_auth_denied'; state.latch = 'authorization_denied'; return finish();
  }
  if (response.status !== 200) { state.action = 'status_failed'; state.error = `status_http_${Number.isInteger(response.status) ? response.status : 'invalid'}`; return finish(); }
  try { payload = await readJSON(response); } catch { state.action = 'status_invalid'; state.error = 'status_contract_invalid'; return finish(); }
  state.queue = assessNativeQueue(payload, now());
  state.action = 'status_observed';
  if (state.latch === 'retry_outcome_unknown') { state.action = 'review_required'; state.error = state.latch; return finish(); }
  if (mode === 'status') return finish();
  if (retryEnabled !== true) { state.action = 'retry_not_enabled'; return finish(); }
  if (!state.queue.configured || !state.queue.enabled || state.queue.provider !== 'resend') {
    state.action = 'server_not_enabled'; return finish();
  }
  if (state.queue.reason === 'health_contract_invalid') { state.action = 'status_invalid'; state.error = 'status_contract_invalid'; return finish(); }
  const lastAttempt = state.lastRetryAttemptAt ? Date.parse(state.lastRetryAttemptAt) : -Infinity;
  if (now() - lastAttempt < EXPECTED_INTERVAL_MS) { state.action = 'retry_cooldown'; return finish(); }
  // Persist before the side effect. A crashed process or lost response leaves a
  // durable latch. A later process may not blindly issue the same retry request.
  state.lastRetryAttemptAt = iso(now()); state.latch = 'retry_outcome_unknown'; state.action = 'retry_pending';
  await stateStore.save(state);
  try {
    response = await request(`${ENDPOINT}/retry`, {...options, method: 'POST', headers: {...options.headers, 'content-type': 'application/json'},
      body: '{}', signal: AbortSignal.timeout(90_000)});
  } catch { state.action = 'retry_unknown'; state.error = 'retry_request_unknown'; return finish(); }
  if ([401, 403].includes(response.status)) {
    state.action = 'authorization_denied'; state.error = 'owner_auth_denied'; state.latch = 'authorization_denied'; return finish();
  }
  try { payload = await readJSON(response); } catch { state.action = 'retry_unknown'; state.error = 'retry_contract_unknown'; return finish(); }
  const delivery = deliverySummary(payload?.delivery);
  if (![200, 503].includes(response.status) || !delivery || !payload.health || typeof payload.health !== 'object') {
    state.action = 'retry_unknown'; state.error = 'retry_contract_unknown'; return finish();
  }
  // A well-formed completed response may report provider rejection, ambiguity or
  // stale health. Preserve those failures, rather than turning HTTP success green.
  state.lastRetryCompletedAt = iso(now()); state.observerCheckedAt = iso(now()); state.latch = null;
  state.delivery = delivery;
  state.queue = assessNativeQueue({configured: payload.delivery.configured, health: payload.health}, now());
  state.action = 'retry_completed';
  if (delivery.stopped === 'claim_unknown' || delivery.stopped === 'settlement_unknown') {
    state.latch = 'retry_outcome_unknown'; state.error = delivery.stopped;
  } else if (delivery.stopped) state.error = delivery.stopped;
  else if (delivery.rejected || delivery.ambiguous) state.error = 'delivery_requires_review';
  return finish();
}
