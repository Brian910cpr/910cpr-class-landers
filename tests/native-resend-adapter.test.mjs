import test from 'node:test';
import assert from 'node:assert/strict';
import { sendNativeConfirmation } from '../supabase/functions/_shared/native-resend-adapter.mjs';

const claim = {
  messageId: '123e4567-e89b-42d3-a456-426614174000',
  recipient: 'synthetic-student@example.test',
  subject: 'Synthetic native confirmation',
  body: 'Synthetic registration facts. No real customer data.',
  lease: '123e4567-e89b-42d3-a456-426614174001',
};
const receipt = '123e4567-e89b-42d3-a456-426614174002';
const base = { apiKey: 'synthetic-key-not-a-credential', from: '910CPR <sender@example.test>', replyTo: 'reply@example.test' };
function fixture(response = () => Response.json({ id: receipt })) {
  const calls = [];
  return { calls, options: { ...base, request: async (...args) => { calls.push(args); return response(); } } };
}

test('accepted native message requires provider receipt and fixed endpoint', async () => {
  const f = fixture();
  assert.deepEqual(await sendNativeConfirmation(claim, f.options), { outcome: 'sent', providerId: receipt, errorCode: null });
  assert.equal(f.calls.length, 1);
  const [url, request] = f.calls[0];
  assert.equal(url, 'https://api.resend.com/emails');
  assert.equal(request.redirect, 'error');
  assert.equal(request.method, 'POST');
  assert.equal(request.headers['idempotency-key'], `native-checkout-${claim.messageId}`);
  assert.deepEqual(JSON.parse(request.body), {
    from: base.from, to: [claim.recipient], subject: claim.subject, text: claim.body, reply_to: base.replyTo,
  });
  assert.ok(request.signal instanceof AbortSignal);
});

test('replay uses stable durable message key, never the changing lease', async () => {
  const f = fixture();
  await sendNativeConfirmation(claim, f.options);
  await sendNativeConfirmation({ ...claim, lease: 'other-lease' }, f.options);
  assert.equal(f.calls[0][1].headers['idempotency-key'], f.calls[1][1].headers['idempotency-key']);
});

test('missing configuration makes no request', async () => {
  for (const missing of ['apiKey', 'from', 'request']) {
    const f = fixture();
    const options = { ...f.options }; delete options[missing];
    assert.deepEqual(await sendNativeConfirmation(claim, options), { outcome: 'rejected', providerId: null, errorCode: 'native_mail_not_configured' });
    assert.equal(f.calls.length, 0);
  }
});

test('invalid or injectable claim/config makes no request', async () => {
  for (const patch of [{ messageId: 'bad' }, { recipient: 'a@example.test,b@example.test' }, { recipient: 'a,b@example.test' }, { recipient: 'a;b@example.test' }, { subject: 'x\r\nBCC: victim@example.test' }, { body: '' }, { body: 'x'.repeat(256 * 1024 + 1) }]) {
    const f = fixture();
    assert.equal((await sendNativeConfirmation({ ...claim, ...patch }, f.options)).outcome, 'rejected');
    assert.equal(f.calls.length, 0);
  }
  for (const patch of [{ from: 'x\r\nBCC: y' }, { from: 'invalid-sender' }, { apiKey: 'x\r\nsecret' }, { replyTo: 'x\r\ny@example.test' }]) {
    const f = fixture();
    assert.equal((await sendNativeConfirmation(claim, { ...f.options, ...patch })).outcome, 'rejected');
    assert.equal(f.calls.length, 0);
  }
});

test('explicit ordinary provider 4xx is rejected without persisting arbitrary body', async () => {
  for (const status of [400, 401, 403, 404, 422, 429]) {
    const f = fixture(() => Response.json({ message: 'secret-bearing provider response', key: base.apiKey }, { status }));
    const result = await sendNativeConfirmation(claim, f.options);
    assert.deepEqual(result, { outcome: 'rejected', providerId: null, errorCode: `native_mail_http_${status}` });
    assert.ok(!JSON.stringify(result).includes('secret-bearing'));
    assert.ok(!JSON.stringify(result).includes(base.apiKey));
    assert.equal(f.calls.length, 1);
  }
});

test('timeout, concurrent attempt, server error and redirect remain ambiguous', async () => {
  for (const status of [302, 408, 409, 500, 502, 503]) {
    const f = fixture(() => new Response('arbitrary body', { status }));
    assert.deepEqual(await sendNativeConfirmation(claim, f.options), { outcome: 'ambiguous', providerId: null, errorCode: `native_mail_http_${status}` });
    assert.equal(f.calls.length, 1);
  }
});

test('network exceptions never masquerade as rejection or leak secrets', async () => {
  for (const error of [new Error(base.apiKey), new DOMException('private', 'TimeoutError'), new DOMException('private', 'AbortError')]) {
    const f = fixture(() => { throw error; });
    assert.deepEqual(await sendNativeConfirmation(claim, f.options), { outcome: 'ambiguous', providerId: null, errorCode: 'native_mail_request_unknown' });
    assert.equal(f.calls.length, 1);
  }
});

test('2xx without a usable receipt is ambiguous', async () => {
  for (const value of [{}, { id: '' }, { id: 7 }, { id: 'provider\nsecret' }]) {
    const f = fixture(() => Response.json(value));
    assert.deepEqual(await sendNativeConfirmation(claim, f.options), { outcome: 'ambiguous', providerId: null, errorCode: 'native_mail_receipt_missing' });
  }
});

test('invalid, empty, or oversized provider response is ambiguous', async () => {
  for (const response of [() => new Response('not JSON'), () => new Response(null, { status: 204 }), () => new Response('x'.repeat(64 * 1024 + 1))]) {
    const f = fixture(response);
    assert.equal((await sendNativeConfirmation(claim, f.options)).outcome, 'ambiguous');
    assert.equal(f.calls.length, 1);
  }
});

test('no implicit global network fallback exists', async () => {
  const original = globalThis.fetch;
  let called = false;
  globalThis.fetch = async () => { called = true; throw Error('must not run'); };
  try {
    assert.equal((await sendNativeConfirmation(claim, base)).outcome, 'rejected');
    assert.equal(called, false);
  } finally { globalThis.fetch = original; }
});
