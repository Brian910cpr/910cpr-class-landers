// Read-only advisory check. This is never a lease or permission for a side effect.
export async function executionCheck(id, expectedUpdatedAt, readCard) {
  const respond = (status, body) => ({status, body: {can_execute: false, ...body}});
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) {
    return respond(400, {decision: 'review', reason: 'invalid_card_id'});
  }
  let card;
  try { card = await readCard(id); }
  catch { return respond(503, {decision: 'review', reason: 'card_state_unavailable'}); }
  if (!card) return respond(404, {decision: 'skip', reason: 'card_not_found'});
  if (card.id !== id) return respond(503, {decision: 'review', reason: 'card_identity_mismatch'});
  const version = typeof card.updated_at === 'string' ? card.updated_at : null;
  const context = {card_id: id, observed_updated_at: version};
  // Reserved canonical contract for the reviewed resolution migration. Legacy
  // cards have no resolution_state; lane/free text cannot substitute for it.
  if (['handled_manually', 'verified_resolved'].includes(card.resolution_state)) {
    return respond(200, {...context, decision: 'skip', reason: 'recorded_resolution', resolution_state: card.resolution_state});
  }
  if (!version || !Number.isFinite(Date.parse(version))) {
    return respond(409, {...context, decision: 'review', reason: 'card_version_unavailable'});
  }
  if (!expectedUpdatedAt) return respond(428, {...context, decision: 'review', reason: 'expected_version_required'});
  if (version !== expectedUpdatedAt) return respond(409, {...context, decision: 'review', reason: 'card_changed'});
  return respond(200, {...context, decision: 'review', reason: 'authoritative_source_check_required',
    next_action: 'Inspect current authoritative business state. If already corrected, propose Verified Resolved with evidence; if ambiguous, request review. Recheck immediately before any side effect.'});
}
