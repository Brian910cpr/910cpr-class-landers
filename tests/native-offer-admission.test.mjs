import test from 'node:test';
import assert from 'node:assert/strict';
import {admitNativeOffer, offerRef} from '../supabase/functions/_shared/native-offer-admission.mjs';

const now = Date.parse('2026-12-25T12:00:00-05:00');
const start = Date.parse('2026-12-26T13:00:00-05:00');
const end = Date.parse('2026-12-26T17:00:00-05:00');
const plan = async (offerEdits = {}, evidenceEdits = {}) => {
  const offer = {course:'fixture-advanced-renewal', instructor:'fixture-amy', room:'fixture-room-b',
    start, end, ...offerEdits};
  return {now, lockedRevision:'fixture-revision-1', activation:'test', offer, requestedRef:await offerRef(offer), evidence:{
    complete:true, revision:'fixture-revision-1', asOf:now - 5000, validUntil:now + 60000,
    capability:{mode:'test', course:'fixture-advanced-renewal', room:'fixture-room-b',
      eligibleInstructors:['fixture-amy'], priceCents:12345, seatLimit:4, minutes:240,
      setupMinutes:15, turnMinutes:15, leadMinutes:1440},
    qualification:{course:'fixture-advanced-renewal', instructor:'fixture-amy', start:now-60000, end:end+16*60000},
    coverage:[{instructor:'fixture-amy',room:'fixture-room-b',start:start-15*60000,
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


test('setup block is covered, can collide before class, and has a legal exact bookend', async () => {
  const p = await plan();
  assert.equal((await admitNativeOffer(p)).admission.occupiedFrom, start-15*60000);
  p.evidence.conflicts=[{room:'fixture-room-b',start:start-16*60000,end:start-14*60000,public:false}];
  assert.equal((await admitNativeOffer(p)).reason,'occupied');
  p.evidence.conflicts[0].end=start-15*60000;
  assert.ok((await admitNativeOffer(p)).ok);
  p.evidence.coverage[0].start=start;
  assert.equal((await admitNativeOffer(p)).reason,'outside_coverage');
});
test('locked revision must match, and qualification must cover setup through cleanup', async () => {
  const p=await plan();
  assert.equal((await admitNativeOffer({...p,lockedRevision:'fixture-revision-2'})).reason,'stale_evidence');
  assert.equal((await admitNativeOffer({...p,lockedRevision:undefined})).reason,'stale_evidence');
  const original=p.evidence.qualification;
  for (const q of [null, {...original,start}, {...original,end}, {...original,instructor:'fixture-brian'}]) {
    p.evidence.qualification=q;
    assert.equal((await admitNativeOffer(p)).reason,'qualification_outside_window');
  }
});
test('invalid or overflowing canonical timing fails closed', async () => {
  const p=await plan();
  for (const field of ['setupMinutes','turnMinutes','leadMinutes','minutes']) {
    const saved=p.evidence.capability[field];
    p.evidence.capability[field]=Number.MAX_SAFE_INTEGER;
    assert.equal((await admitNativeOffer(p)).ok,false);
    p.evidence.capability[field]=saved;
  }
});
