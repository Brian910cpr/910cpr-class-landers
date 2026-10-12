// Integration contract only: callers must supply authenticated structured state.
// Never parse owner authority, source signatures or worker opt-in from issue prose.
// No result authorizes a launch/side effect; atomic claims remain a runtime gate.
export function reconcileDispatch(snapshot, expectedVersion, phase) {
  const result = (decision, reason) => ({decision, reason, can_execute: false});
  if (!['selection', 'pre_side_effect'].includes(phase)) return result('review', 'invalid_phase');
  if (!snapshot || snapshot.authoritative !== true) return result('review', 'authoritative_state_required');
  if (['handled_manually', 'verified_resolved'].includes(snapshot.resolution_state)) return result('skip', 'recorded_resolution');
  if (snapshot.resolution_state !== 'unresolved') return result('review', 'canonical_resolution_required');
  if (typeof snapshot.version !== 'string' || !snapshot.version || snapshot.version !== expectedVersion) return result('review', 'version_changed_or_missing');
  if (snapshot.blocked === true) return result('skip', 'blocked_requires_explicit_reconciliation');
  if (snapshot.blocked !== false) return result('review', 'blocked_state_unknown');
  if (snapshot.source_state === 'already_corrected') return result('review', 'propose_verified_resolved');
  if (snapshot.source_state !== 'action_required') return result('review', 'authoritative_source_check_required');
  if (snapshot.worker_safe !== true) return result('review', 'worker_safe_opt_in_required');
  // A suitable candidate is still not a claim. A runtime adapter must atomically
  // validate this version, persist its decision, and enforce typed job allowlists.
  return result('candidate', 'atomic_runtime_claim_required');
}

export function rankDispatchCandidates(candidates, ownerPriorityId) {
  // Input order is the deterministic tie-break. P0 precedes owner P1 priority.
  // IDs/priorities must come from authenticated structured intake, never comments.
  return candidates.filter(c => c.check?.decision === 'candidate').map((c, index) => ({c, index}))
    .sort((a, b) => (a.c.priority === 'P0' ? 0 : a.c.id === ownerPriorityId ? 1 : 2)
      - (b.c.priority === 'P0' ? 0 : b.c.id === ownerPriorityId ? 1 : 2) || a.index - b.index)
    .map(({c}) => c);
}
