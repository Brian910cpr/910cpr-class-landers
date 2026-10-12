import {reconcileDispatch} from './dispatch-reconciliation.mjs';

// Adapter boundary, not a runtime claim. The injected reader must authenticate
// canonical intake; never implement it by parsing issue prose or cached checks.
// Deliberately exposes no launch/mutation callback or execution permission.
// Each adapter gets an AbortSignal; adapters should cancel network work on abort.
// The deadline bounds this caller even when an adapter ignores cancellation.
async function boundedCall(callback, value, timeoutMs) {
  const controller = new AbortController();
  let timer;
  try {
    return await Promise.race([
      Promise.resolve().then(() => callback(value, {signal:controller.signal})),
      new Promise((_, reject) => {
        timer = setTimeout(() => {
          reject(new Error('adapter_deadline_exceeded'));
          controller.abort();
        }, timeoutMs);
      })
    ]);
  } finally {
    clearTimeout(timer);
  }
}

export async function checkLiveDispatch(request, {readSnapshot, recordDecision, timeoutMs = 5000} = {}) {
  const review = reason => ({decision:'review', reason, can_execute:false});
  const {issue_id, expectedVersion, phase} = request || {};
  if (!Number.isSafeInteger(issue_id) || issue_id <= 0
      || typeof expectedVersion !== 'string' || !expectedVersion
      || !['selection', 'pre_side_effect'].includes(phase)) return review('invalid_request');
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 30000) return review('invalid_adapter_deadline');
  if (typeof readSnapshot !== 'function' || typeof recordDecision !== 'function') return review('adapter_required');
  let snapshot;
  let evaluatedState;
  const fields = ['issue_id', 'authoritative', 'version', 'resolution_state',
    'blocked', 'source_state', 'worker_safe'];
  const values = state => fields.map(field => state?.[field]);
  let check;
  try {
    snapshot = await boundedCall(readSnapshot, issue_id, timeoutMs);
    evaluatedState = values(snapshot);
    check = snapshot?.issue_id === issue_id
      ? reconcileDispatch(snapshot, expectedVersion, phase)
      : review('canonical_identity_mismatch');
  } catch {
    check = review('canonical_read_failed');
  }
  // Record only an allowlisted decision envelope, never private source/evidence.
  // Acknowledgement means persisted by the adapter, not merely queued locally.
  const event = Object.freeze({issue_id, phase, expected_version:expectedVersion,
    observed_version:typeof snapshot?.version === 'string' ? snapshot.version : null,
    decision:check.decision, reason:check.reason, can_execute:false});
  try {
    if (await boundedCall(recordDecision, event, timeoutMs) !== true) return review('decision_not_persisted');
  } catch {
    return review('decision_not_persisted');
  }
  // A reader may share a mutable cache object. Do not return a decision whose
  // input changed while the audit adapter was awaited. This local drift check
  // cannot detect remote changes and does not replace transactional fencing.
  if (evaluatedState && values(snapshot).some((value, index) => !Object.is(value, evaluatedState[index]))) {
    return review('canonical_snapshot_changed_during_persistence');
  }
  return {...check, can_execute:false};
}
