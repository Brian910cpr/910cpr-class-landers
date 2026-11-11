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

const SCHEDULER_CODES = new Set(['callback_auth_denied','callback_transport_unknown','callback_completion_unknown',
  'scheduler_credential_missing','scheduler_transport_security_changed','provider_ambiguous','claim_unknown','claim_invalid',
  'duplicate_claim','settlement_unknown','mail_unconfigured','delivery_unknown','result_invalid']);
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
export function assessNativeScheduler(payload, now = Date.now()) {
  const present = object(payload) && Object.hasOwn(payload, 'scheduler');
  const s = present && object(payload.scheduler) ? payload.scheduler : {};
  const valid = present && object(payload.scheduler) &&
    ['enabled','latched','callbackFresh','observerFresh','healthy'].every(k => typeof s[k] === 'boolean') &&
    ['lastCompletedAt','lastObservedAt'].every(k => s[k] === null || timestamp(s[k]) !== null) &&
    (s.reason === null || typeof s.reason === 'string') && s.actualDeliveryConfirmed === false;
  const lastCompletedAt = timestamp(s.lastCompletedAt), lastObservedAt = timestamp(s.lastObservedAt);
  const age = value => value ? now - Date.parse(value) : Infinity;
  const callbackFresh = valid && s.callbackFresh === true && age(lastCompletedAt) >= 0 && age(lastCompletedAt) < STALE_AFTER_MS;
  const observerFresh = valid && s.observerFresh === true && age(lastObservedAt) >= 0 && age(lastObservedAt) < STALE_AFTER_MS;
  const enabled = valid && s.enabled === true, latched = valid && s.latched === true;
  const latchReason = SCHEDULER_CODES.has(s.reason) ? s.reason : latched ? 'scheduler_review_required' : null;
  const reason = !present ? 'scheduler_missing' : !valid ? 'scheduler_contract_invalid' : !enabled ? 'scheduler_disabled' :
    latched ? 'scheduler_latched' : !callbackFresh ? 'scheduler_callback_stale' : !observerFresh ? 'scheduler_observer_stale' :
    s.healthy !== true ? 'scheduler_unhealthy' : null;
  return {present, contractValid: valid, enabled, latched, latchReason, lastCompletedAt, lastObservedAt, callbackFresh, observerFresh,
    schedulerHealthy: reason === null, reason, actualDeliveryConfirmed: false};
}

export function assessMonitorState(state, now = Date.now()) {
  const checked = timestamp(state?.observerCheckedAt);
  const age = checked ? now - Date.parse(checked) : Infinity;
  const observerStale = age < -30_000 || age >= STALE_AFTER_MS;
  // Reassess timestamps at read time. A previously green result is not timeless.
  const queue = state?.queue;
  const pollAge = timestamp(queue?.lastPollAt) ? now - Date.parse(queue.lastPollAt) : Infinity;
  const consumerStale = pollAge < -30_000 || pollAge >= STALE_AFTER_MS;
  const scheduler = state?.scheduler;
  const fresh = value => timestamp(value) !== null && now - Date.parse(value) >= 0 && now - Date.parse(value) < STALE_AFTER_MS;
  const callbackStale = !fresh(scheduler?.lastCompletedAt), schedulerObserverStale = !fresh(scheduler?.lastObservedAt);
  const queueHealthy = !observerStale && !consumerStale && !state?.latch && !state?.error && queue?.queueHealthy === true;
  const schedulerHealthy = !observerStale && !callbackStale && !schedulerObserverStale && scheduler?.present === true && scheduler?.contractValid === true && scheduler?.enabled === true && scheduler?.latched === false && scheduler?.callbackFresh === true && scheduler?.observerFresh === true && scheduler?.schedulerHealthy === true;
  return {observerStale, consumerStale, callbackStale, schedulerObserverStale, retryLatched: Boolean(state?.latch),
    queueHealthy, schedulerHealthy, confirmationHealthy: queueHealthy && schedulerHealthy,
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

export async function checkNativeConfirmations({mode = 'status', ownerKey, request, stateStore, now = () => Date.now()} = {}) {
  if (!['status', 'retry'].includes(mode) || typeof request !== 'function' || !stateStore ||
      typeof stateStore.load !== 'function' || typeof stateStore.save !== 'function') throw Error('monitor_configuration_invalid');
  let previous;
  try { previous = await stateStore.load(); } catch { throw Error('monitor_state_unavailable'); }
  const state = {...previousState(previous), observerCheckedAt: null, action: 'not_started', error: null, queue: null, scheduler: null};
  const finish = async () => {
    await stateStore.save(state);
    return {...state, monitor: assessMonitorState(state, now())};
  };
  if (mode !== 'status') { state.action = 'retry_retired'; state.error = 'external_retry_retired'; return finish(); }
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
  state.scheduler = assessNativeScheduler(payload, now());
  state.action = 'status_observed';
  if (state.latch === 'retry_outcome_unknown') { state.action = 'review_required'; state.error = state.latch; return finish(); }
  return finish();
}
