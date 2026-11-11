import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {runNativeConfirmationBatch} from '../worker/native-confirmation-batch.mjs';
import {fetchPriorRetryGuard} from '../worker/native-confirmation-run-guard.mjs';

export async function main({argv = process.argv.slice(2), env = process.env, request = fetch, output = console.log} = {}) {
  const parsed = {};
  for (const arg of argv) {
    const match = /^--(mode|ticks|state-file)=(.+)$/.exec(arg);
    if (!match || parsed[match[1]] !== undefined) throw Error('cli_arguments_invalid');
    parsed[match[1]] = match[2];
  }
  const mode = parsed.mode || 'status', ticks = Number(parsed.ticks || 1);
  if (!['status', 'retry'].includes(mode) || !Number.isInteger(ticks) || ticks < 1 || ticks > 5) throw Error('cli_arguments_invalid');
  const retryEnabled = env.NATIVE_CHECKOUT_RETRY_ENABLED === 'true';
  if (mode === 'retry' && retryEnabled && env.GITHUB_ACTIONS === 'true') {
    const guard = await fetchPriorRetryGuard({token: env.GITHUB_TOKEN, currentRunId: Number(env.GITHUB_RUN_ID), currentAttempt: Number(env.GITHUB_RUN_ATTEMPT || 1), request,
      manual: env.GITHUB_EVENT_NAME === 'workflow_dispatch', reviewedPreviousFailure: env.NATIVE_RETRY_PREVIOUS_FAILURE_REVIEWED === 'true'});
    output(JSON.stringify({event: 'native_confirmation_run_guard', ...guard}));
    if (!guard.allowed) return 2;
  }
  const filename = path.resolve(parsed['state-file'] || './native-confirmation-state.json');
  await fs.mkdir(path.dirname(filename), {recursive: true});
  const lock = `${filename}.lock`;
  try { await fs.mkdir(lock); } catch { throw Error('monitor_lock_unavailable'); }
  try {
    const stateStore = {
      load: async () => {try { return JSON.parse(await fs.readFile(filename, 'utf8')); } catch (error) {if (error.code === 'ENOENT') return null; throw Error('monitor_state_unavailable');}},
      save: async state => {const temp = `${filename}.tmp`; await fs.writeFile(temp, JSON.stringify(state), {mode: 0o600}); await fs.rename(temp, filename);},
    };
    const result = await runNativeConfirmationBatch({mode, ticks, retryEnabled, ownerKey: env.HOT_SYNC_ADMIN_KEY, request, stateStore,
      sleep: ms => new Promise(resolve => setTimeout(resolve, ms))});
    // State contains only counts and sanitized component evidence. Never log
    // request headers, provider responses, recipients, tokens or private receipts.
    for (const check of result.results) output(JSON.stringify({event: 'native_confirmation_observer', ...check}));
    output(JSON.stringify({event: 'native_confirmation_batch', ticks: result.ticks, skipped: result.skipped, queueHealthy: result.queueHealthy, actualDeliveryConfirmed: false}));
    return result.queueHealthy ? 0 : 1;
  } finally { await fs.rmdir(lock); }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try { process.exitCode = await main(); }
  catch { console.error(JSON.stringify({event: 'native_confirmation_observer_failed', error: 'observer_unavailable'})); process.exitCode = 2; }
}
