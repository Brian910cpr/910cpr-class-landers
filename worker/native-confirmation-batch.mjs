import {checkNativeConfirmations, EXPECTED_INTERVAL_MS, assessMonitorState} from './native-confirmation-monitor.mjs';

// Provisional bounded runner, not a daemon or scheduling guarantee. Late ticks
// are skipped, never burst-replayed; non-cancelling scheduler concurrency is also
// required. A separate observer must detect a job that never starts.
export async function runNativeConfirmationBatch({ticks = 1, sleep, now = () => Date.now(), ...options} = {}) {
  if (!Number.isInteger(ticks) || ticks < 1 || ticks > 5 || typeof sleep !== 'function') throw Error('batch_configuration_invalid');
  const started = now(), results = [];
  let skipped = 0;
  for (let i = 0; i < ticks; i++) {
    const due = started + i * EXPECTED_INTERVAL_MS;
    if (now() - due >= EXPECTED_INTERVAL_MS) { skipped++; continue; }
    if (now() < due) await sleep(due - now());
    if (now() - due >= EXPECTED_INTERVAL_MS) { skipped++; continue; }
    const result = await checkNativeConfirmations({...options, now});
    results.push(result);
    if (result.latch || result.action === 'not_configured') break;
  }
  const last = results.at(-1);
  return {ticks: results.length, skipped, results,
    queueHealthy: Boolean(last && !last.error && assessMonitorState(last, now()).queueHealthy),
    actualDeliveryConfirmed: false};
}
