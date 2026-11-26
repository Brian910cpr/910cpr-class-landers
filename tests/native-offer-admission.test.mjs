import test from 'node:test';
import assert from 'node:assert/strict';
import {admitNativeOffer, offerRef} from '../supabase/functions/_shared/native-offer-admission.mjs';

const now = Date.parse('2026-12-25T12:00:00-05:00');
const start = Date.parse('2026-12-26T13:00:00-05:00');
const end = Date.parse('2026-12-26T17:00:00-05:00');
const plan = async (offerEdits = {}, evidenceEdits = {}) => {
  const offer = {course:'fixture-advanced-renewal', instructor:'fixture-amy', room:'fixture-room-b',
    start, end, ...offerEdits};
  return {now, activation:'test', offer, requestedRef:await offerRef(offer), evidence:{
    complete:true, revision:'fixture-revision-1', asOf:now - 5000, validUntil:now + 60000,
    capability:{mode:'test', course:'fixture-advanced-renewal', room:'fixture-room-b',
      eligibleInstructors:['fixture-amy'], priceCents:12345, seatLimit:4, minutes:240,
      turnMinutes:15, leadMinutes:1440},
    coverage:[{instructor:'fixture-amy',room:'fixture-room-b',start,
      end:Date.parse('2026-12-26T18:00:00-05:00')}], conflicts:[], ...evidenceEdits}};
};

test('qualified test coverage produces a stable opaque selector, never a URL or session', async () => {
  const p = await plan();
  assert.match(p.requestedRef, /^lw-offer-v1-[a-f0-9]{64}$/);
  assert.equal(await offerRef({...p.offer, priceCents:1, revision:'next'}), p.requestedRef);
  const a = await admitNativeOffer(p);
  assert.ok(a.ok);
  assert.equal(a.admission.holdUntil, now + 15*60000);
  assert.equal(a.admission.priceCents, 12345);
  assert.equal(a.admission.occupiedUntil, end + 15*60000);
  assert.doesNotMatch(JSON.stringify(a), /https:|checkoutUrl|sessionId/);
});
test('live or absent activation never admits; mismatched selector never admits', async () => {
  const p = await plan();
  for (const activation of [undefined, 'live', true])
    assert.equal((await admitNativeOffer({...p,activation})).reason,'disabled');
  const q = await plan({course:'fixture-different-course'});
  assert.equal((await admitNativeOffer({...q,requestedRef:p.requestedRef})).reason,'invalid_offer');
  assert.equal((await admitNativeOffer(q)).reason,'unsupported_capability');
});
test('unknown capability and unqualified instructor cannot admit', async () => {
  assert.equal((await admitNativeOffer(await plan({}, {capability:null}))).reason,'unsupported_capability');
  assert.equal((await admitNativeOffer(await plan({instructor:'fixture-brian'}))).reason,'unsupported_capability');
});
test('stale, future, and incomplete evidence and missing room coverage fail closed', async () => {
  for (const e of [{validUntil:now}, {asOf:now+1}, {asOf:now-31*60000}, {complete:false}])
    assert.equal((await admitNativeOffer(await plan({},e))).reason,'stale_evidence');
  assert.equal((await admitNativeOffer(await plan({},{coverage:[]}))).reason,'outside_coverage');
  const p=await plan();
  p.evidence.coverage[0].end=end;
  assert.equal((await admitNativeOffer(p)).reason,'outside_coverage');
});
test('private conflict blocks either room or instructor; exact bookend stays open', async () => {
  for (const field of [{room:'fixture-room-b'},{instructor:'fixture-amy'}]) {
    const p = await plan({},{conflicts:[{...field,start:end,end:end+60000,public:false}]});
    assert.equal((await admitNativeOffer(p)).reason,'occupied');
    p.evidence.conflicts[0].start=end+15*60000;
    p.evidence.conflicts[0].end=end+16*60000;
    assert.ok((await admitNativeOffer(p)).ok);
  }
  assert.equal((await admitNativeOffer(await plan({},{conflicts:[{room:'fixture-room-b'}]}))).reason,'unresolved_occupancy');
});
test('server duration, lead and current price are authoritative', async () => {
  assert.equal((await admitNativeOffer(await plan({end:end-60000}))).reason,'invalid_timing');
  const p = await plan();
  p.evidence.capability.leadMinutes=3600;
  assert.equal((await admitNativeOffer(p)).reason,'invalid_timing');
  p.evidence.capability.priceCents=NaN;
  assert.equal((await admitNativeOffer(p)).reason,'unsupported_capability');
});
