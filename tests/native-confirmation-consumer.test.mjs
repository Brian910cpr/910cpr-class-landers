import test from 'node:test';
import assert from 'node:assert/strict';
import { dispatchNativeConfirmations } from '../supabase/functions/_shared/native-confirmation-consumer.mjs';
import { sendNativeCheckoutClaim } from '../supabase/functions/_shared/native-resend-adapter.mjs';

const uuid = n => `123e4567-e89b-42d3-a456-${String(n).padStart(12, '0')}`;
const job = n => ({ messageId: uuid(n), lease: uuid(n + 100), recipient: 'synthetic-student@example.test', customerTemplate: true,
  subject: 'Never copied', body: 'Never copied', confirmation: { kind: 'confirmation', course: 'Synthetic BLS', courseId: '209806', startsAt: '2026-11-24T15:00:00Z', endsAt: '2026-11-24T17:00:00Z', selectedOptions: [] } });
function fixture(jobs = [job(1)], options = {}) {
  const claims = [], sends = [], settlements = [];
  return { claims, sends, settlements, input: {
    claim: async args => { claims.push(args); return jobs.length ? jobs.shift() : {empty: true}; },
    send: async value => { sends.push(value); return {outcome: 'sent', providerId: 'synthetic-provider-id', errorCode: null}; },
    settle: async args => { settlements.push(args); return {settled: true}; }, ...options,
  } };
}

test('bounded service consumer records receipt with exact durable message and lease', async () => {
  const f = fixture();
  const result = await dispatchNativeConfirmations(f.input);
  assert.deepEqual(result, {claimed: 1, accepted: 1, rejected: 0, ambiguous: 0, stopped: null, disabled: false, empty: true, actualDeliveryConfirmed: false});
  assert.deepEqual(f.claims, [{p_order_id: null}, {p_order_id: null}]);
  assert.equal(f.sends.length, 1);
  assert.deepEqual(f.settlements, [{p_message_id: uuid(1), p_lease: uuid(101), p_outcome: 'sent', p_provider_id: 'synthetic-provider-id', p_error: null}]);
});

test('order-scoped immediate dispatch sends the same exact order scope to every claim', async () => {
  const f = fixture([job(1), job(2)]);
  const result = await dispatchNativeConfirmations({...f.input, orderId: uuid(500)});
  assert.equal(result.accepted, 2);
  assert.equal(f.claims.length, 3);
  assert.ok(f.claims.every(args => args.p_order_id === uuid(500)));
});

test('maximum loop is ten messages and custom bounded limit is honored', async () => {
  for (const limit of [1, 3, 10]) {
    const f = fixture(Array.from({length: 12}, (_, i) => job(i + 1)));
    const result = await dispatchNativeConfirmations({...f.input, limit});
    assert.equal(f.claims.length, limit); assert.equal(f.sends.length, limit); assert.equal(result.accepted, limit);
  }
});

test('bad limits, order IDs or missing dependencies fail without side effects', async () => {
  for (const patch of [{limit: 0}, {limit: 11}, {limit: 1.5}, {orderId: 'bad'}, {claim: undefined}, {send: undefined}, {settle: undefined}]) {
    const f = fixture();
    await assert.rejects(dispatchNativeConfirmations({...f.input, ...patch}), /invalid_configuration/);
    assert.equal(f.claims.length + f.sends.length + f.settlements.length, 0);
  }
});

test('disabled and empty responses cause no provider or settlement calls', async () => {
  for (const response of [{disabled: true}, {empty: true}]) {
    const f = fixture([response]);
    const result = await dispatchNativeConfirmations(f.input);
    assert.equal(f.claims.length, 1); assert.equal(f.sends.length, 0); assert.equal(f.settlements.length, 0);
    assert.equal(result[response.disabled ? 'disabled' : 'empty'], true);
  }
});

test('claim exceptions or malformed contracts stop without guessing another operation', async () => {
  const f = fixture([], {claim: async () => {throw Error('private db error');}});
  assert.equal((await dispatchNativeConfirmations(f.input)).stopped, 'claim_unknown');
  assert.equal(f.sends.length, 0);
  for (const response of [null, {}, {messageId: uuid(1)}, {...job(1), empty: true}, {...job(1), lease: 'invalid'}]) {
    const f = fixture([response, job(2)]);
    const result = await dispatchNativeConfirmations(f.input);
    assert.equal(result.stopped, 'claim_invalid'); assert.equal(f.claims.length, 1); assert.equal(f.sends.length, 0);
  }
});

test('same durable message cannot be sent twice even if the claim returns another lease', async () => {
  const f = fixture([job(1), {...job(1), lease: uuid(999)}, job(2)]);
  const result = await dispatchNativeConfirmations(f.input);
  assert.equal(result.stopped, 'duplicate_claim'); assert.equal(result.accepted, 1); assert.equal(f.sends.length, 1); assert.equal(f.claims.length, 2);
});

test('explicit rejection and ambiguous sends settle once without inline retry', async () => {
  for (const outcome of ['rejected', 'ambiguous']) {
    const f = fixture([job(1)], {send: async () => ({outcome, providerId: null, errorCode: 'synthetic_error'})});
    const result = await dispatchNativeConfirmations(f.input);
    assert.equal(result[outcome], 1); assert.equal(result.accepted, 0); assert.equal(f.settlements.length, 1);
    assert.equal(f.settlements[0].p_outcome, outcome);
  }
});

test('send exception or missing receipt becomes ambiguous without leaking provider errors', async () => {
  for (const send of [async () => {throw Error('PRIVATE_SECRET');}, async () => ({outcome: 'sent'}), async () => ({}), async () => ({outcome: 'sent', providerId: 'PRIVATE\nSECRET'}), async () => ({outcome: 'ambiguous', errorCode: 'PRIVATE error text'}), async () => ({outcome: 'rejected', errorCode: 'UPPER_CODE'}), async () => ({outcome: 'rejected', errorCode: 'hyphen-code'})]) {
    const f = fixture([job(1)], {send});
    const result = await dispatchNativeConfirmations(f.input);
    assert.equal(result.ambiguous + result.rejected, 1);
    assert.ok(['rejected', 'ambiguous'].includes(f.settlements[0].p_outcome));
    assert.match(f.settlements[0].p_error, /^[a-z0-9_]{1,100}$/);
    assert.doesNotMatch(JSON.stringify(result) + JSON.stringify(f.settlements), /PRIVATE/);
  }
});

test('settlement exception preserves exact receipt for reconciliation and stops without another send', async () => {
  const f = fixture([job(1), job(2)], {settle: async () => {throw Error('private settlement error');}});
  const result = await dispatchNativeConfirmations(f.input);
  assert.equal(result.stopped, 'settlement_unknown'); assert.equal(result.accepted, 0);
  assert.equal(f.claims.length, 1); assert.equal(f.sends.length, 1);
  assert.deepEqual(result.pendingSettlement, {p_message_id: uuid(1), p_lease: uuid(101), p_outcome: 'sent', p_provider_id: 'synthetic-provider-id', p_error: null});
  assert.doesNotMatch(JSON.stringify(result), /private settlement error/);
});

test('unknown or negative settlement acknowledgment stops, while exact replay succeeds', async () => {
  for (const ack of [undefined, null, {}, {settled: false}, {replay: false}]) {
    const f = fixture([job(1), job(2)], {settle: async () => ack});
    assert.equal((await dispatchNativeConfirmations(f.input)).stopped, 'settlement_unknown');
    assert.equal(f.sends.length, 1);
  }
  const f = fixture([job(1)], {settle: async () => ({replay: true})});
  assert.equal((await dispatchNativeConfirmations(f.input)).accepted, 1);
});

test('provider plus renderer integration persists accepted receipt and rejects missing canonical payload locally', async () => {
  let requests = 0;
  const malformed = {...job(2), confirmation: null};
  const f = fixture([job(1), malformed], {send: value => sendNativeCheckoutClaim(value, {apiKey: 'synthetic-not-a-secret', from: 'sender@example.test', request: async (_url, options) => {
    requests++; const payload = JSON.parse(options.body); assert.match(payload.html, /Synthetic BLS/); assert.doesNotMatch(payload.text, /Never copied/);
    return Response.json({id: 'synthetic-integration-receipt'});
  }})});
  const result = await dispatchNativeConfirmations(f.input);
  assert.equal(result.accepted, 1); assert.equal(result.rejected, 1); assert.equal(requests, 1);
  assert.equal(f.settlements[0].p_provider_id, 'synthetic-integration-receipt');
  assert.equal(f.settlements[1].p_error, 'native_mail_invalid_confirmation');
});
