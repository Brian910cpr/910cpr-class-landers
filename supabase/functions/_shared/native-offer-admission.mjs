// Unwired reference policy. A passing decision is not a reservation.
const KEY = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;
const OFFER = /^lw-offer-v1-[a-f0-9]{64}$/;
const MINUTE = 60_000;
const HOLD_MS = 15 * MINUTE;
const MAX_EVIDENCE_AGE_MS = 30 * MINUTE;
const id = (s) => typeof s === 'string' && KEY.test(s);
const safeTime = (s) => Number.isSafeInteger(s) && s > 0;
const minutes = (n, min = 0) => Number.isSafeInteger(n) && n >= min && Number.isSafeInteger(n * MINUTE);
const range = (x) => safeTime(x?.start) && safeTime(x?.end) && x.start < x.end;
const overlap = (a, b) => a.start < b.end && b.start < a.end;
const validConflict = (x) => range(x) &&
  (x.room == null || id(x.room)) && (x.instructor == null || id(x.instructor)) &&
  (id(x.room) || id(x.instructor));
const fail = (reason) => ({ok: false, reason});

export async function offerRef(offer) {
  if (![offer?.course, offer?.instructor, offer?.room].every(id) || !range(offer)) return null;
  const versioned = JSON.stringify(['landerware-native-offer.v1', offer.course,
    offer.instructor, offer.room, offer.start, offer.end]);
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(versioned));
  return 'lw-offer-v1-' + Array.from(new Uint8Array(bytes), (n) => n.toString(16).padStart(2, '0')).join('');
}

// These inputs are resolved by trusted server code, never accepted from a browser.
// Run this inside the future claim transaction with the locked canonical state.
export async function admitNativeOffer({activation, offer, requestedRef, evidence, lockedRevision, now} = {}) {
  if (activation !== 'test') return fail('disabled');
  if (!safeTime(now) || typeof requestedRef !== 'string' || !OFFER.test(requestedRef) ||
      requestedRef !== await offerRef(offer)) return fail('invalid_offer');
  if (!evidence || evidence.complete !== true || !id(evidence.revision) || evidence.revision !== lockedRevision ||
      !safeTime(evidence.asOf) || evidence.asOf > now ||
      now - evidence.asOf > MAX_EVIDENCE_AGE_MS ||
      !safeTime(evidence.validUntil) || evidence.validUntil <= now) return fail('stale_evidence');

  const {capability, qualification, coverage, conflicts} = evidence;
  if (capability?.mode !== 'test' || capability.course !== offer.course ||
      capability.room !== offer.room || !Array.isArray(capability.eligibleInstructors) ||
      !capability.eligibleInstructors.includes(offer.instructor) ||
      !Number.isSafeInteger(capability.priceCents) || capability.priceCents <= 0 ||
      !Number.isSafeInteger(capability.seatLimit) || capability.seatLimit <= 0 ||
      !minutes(capability.minutes, 1) || !minutes(capability.setupMinutes) ||
      !minutes(capability.turnMinutes) || !minutes(capability.leadMinutes)) {
    return fail('unsupported_capability');
  }
  const occupied = {start: offer.start - capability.setupMinutes * MINUTE,
    end: offer.end + capability.turnMinutes * MINUTE};
  const earliestStart = now + capability.leadMinutes * MINUTE;
  if (!range(occupied) || offer.end - offer.start !== capability.minutes * MINUTE ||
      !safeTime(earliestStart) || offer.start < earliestStart || occupied.start <= now) return fail('invalid_timing');
  if (!range(qualification) || qualification.course !== offer.course ||
      qualification.instructor !== offer.instructor || qualification.start > occupied.start ||
      qualification.end < occupied.end) return fail('qualification_outside_window');
  if (!Array.isArray(coverage) || !coverage.some((x) => range(x) &&
      x.instructor === offer.instructor && x.room === offer.room &&
      x.start <= occupied.start && x.end >= occupied.end)) return fail('outside_coverage');
  if (!Array.isArray(conflicts) || !conflicts.every(validConflict)) return fail('unresolved_occupancy');
  if (conflicts.some((x) => (x.room === offer.room || x.instructor === offer.instructor) &&
      overlap(occupied, x))) return fail('occupied');
  // An authenticated checkout retry and joining seats in an existing class are
  // lifecycle operations owned by the future store, not inferred from equal times.
  const holdUntil = Math.min(now + HOLD_MS, occupied.start);
  return {ok: true, admission: {offerRef: requestedRef, revision: evidence.revision,
    course: offer.course, instructor: offer.instructor, room: offer.room,
    startsAt: offer.start, endsAt: offer.end, occupiedFrom: occupied.start, occupiedUntil: occupied.end,
    priceCents: capability.priceCents, seatLimit: capability.seatLimit, holdUntil}};
}


