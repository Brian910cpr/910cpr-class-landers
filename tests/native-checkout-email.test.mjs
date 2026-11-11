import test from 'node:test';
import assert from 'node:assert/strict';
import { renderNativeCheckoutClaim } from '../supabase/functions/_shared/native-checkout-email.mjs';
import { sendNativeCheckoutClaim, sendNativeConfirmation } from '../supabase/functions/_shared/native-resend-adapter.mjs';

const id = '123e4567-e89b-42d3-a456-426614174000';
const lease = '123e4567-e89b-42d3-a456-426614174001';
const providerId = '123e4567-e89b-42d3-a456-426614174002';
const token = '123e4567-e89b-42d3-a456-426614174003';
const confirmation = {
  kind: 'confirmation', firstName: 'Synthetic', course: 'BLS Provider Renewal', courseId: '359474',
  startsAt: '2026-11-24T15:00:00+00:00', endsAt: '2026-11-24T17:00:00+00:00',
  venue: 'Recorded venue', address: 'Recorded synthetic address', selectedOptions: [],
};
const claim = {
  messageId: id, lease, recipient: 'synthetic-student@example.test', customerTemplate: true,
  subject: 'PRIVATE_RAW_SUBJECT', body: 'PRIVATE_RAW_BODY', html: '<script>PRIVATE_RAW_HTML</script>', confirmation,
};
const recovery = { ...confirmation, kind: 'recovery', recoveryUrl: `https://www.910cpr.com/register/checkout/?recover=${token}`, holdExpiresAt: '2026-11-24T14:30:00Z' };
function fixture(response = () => Response.json({ id: providerId })) {
  const calls = [];
  return { calls, options: { apiKey: 'synthetic-not-a-secret', from: '910CPR <sender@example.test>', replyTo: 'brian@910cpr.com', request: async (...args) => { calls.push(args); return response(); } } };
}
const sent = f => JSON.parse(f.calls[0][1].body);

test('canonical customer claim renders HTML and text, never raw message fields or internal IDs', async () => {
  const f = fixture();
  const result = await sendNativeCheckoutClaim({ ...claim, confirmation: { ...confirmation, orderId: 'PRIVATE_ORDER', registrationId: 'PRIVATE_REGISTRATION', html: '<script>PRIVATE_INNER_HTML</script>' } }, f.options);
  assert.deepEqual(result, { outcome: 'sent', providerId, errorCode: null });
  assert.equal(f.calls.length, 1);
  const payload = sent(f);
  assert.match(payload.subject, /You’re registered/);
  assert.match(payload.text, /10:00 AM–12:00 PM Eastern/);
  assert.match(payload.text, /Tuesday, November 24, 2026/);
  assert.match(payload.html, /Get directions/);
  assert.doesNotMatch(JSON.stringify(payload), /PRIVATE_/);
  assert.deepEqual(payload.to, [claim.recipient]);
  assert.equal(payload.reply_to, 'brian@910cpr.com');
});

test('actual PostgreSQL timestamps and nullable fields are accepted without invented directions', () => {
  const content = renderNativeCheckoutClaim({ ...claim, confirmation: { ...confirmation, courseId: 359474, firstName: null, venue: null, address: '', endsAt: null, selectedOptions: null, startsAt: '2026-11-24T15:00:00.123456+00:00' } });
  assert.match(content.text, /Hi there/);
  assert.match(content.text, /10:00 AM Eastern/);
  assert.doesNotMatch(content.html, /Get directions/);
  assert.match(content.text, /Contact 910CPR to confirm your class location/);
});

test('HTML injection is escaped in every canonical display field', async () => {
  const f = fixture();
  await sendNativeCheckoutClaim({ ...claim, confirmation: { ...confirmation, firstName: '<img src=x onerror=evil()>', course: '<script>evil()</script>', venue: '<b>venue</b>', address: 'A & B <place>', selectedOptions: [{ key: 'synthetic', display_name: '<iframe src=x>' }] } }, f.options);
  const payload = sent(f);
  assert.doesNotMatch(payload.html, /<script>|<img src=x|<iframe|<b>venue/);
  assert.match(payload.html, /&lt;script&gt;/);
  assert.match(payload.html, /&lt;iframe/);
  assert.match(payload.html, /A &amp; B &lt;place&gt;/);
});

test('missing or malformed canonical customer payload fails closed without provider requests', async () => {
  for (const value of [null, undefined, [], {}, { ...confirmation, kind: 'paid-ish' }, { ...confirmation, kind: undefined }, { ...confirmation, course: '' }, { ...confirmation, courseId: null }, { ...confirmation, startsAt: '2026-11-24T15:00:00' }, { ...confirmation, endsAt: 'invalid' }, { ...confirmation, endsAt: '2026-11-24T14:00:00Z' }, { ...confirmation, selectedOptions: {} }, { ...confirmation, selectedOptions: [null] }, { ...confirmation, selectedOptions: [{}] }, { ...confirmation, selectedOptions: Array(101).fill({key: 'x'}) }]) {
    const f = fixture();
    assert.deepEqual(await sendNativeCheckoutClaim({ ...claim, confirmation: value }, f.options), { outcome: 'rejected', providerId: null, errorCode: 'native_mail_invalid_confirmation' });
    assert.equal(f.calls.length, 0);
  }
});

test('invalid lease, identity, template flag and recipient never reach the provider', async () => {
  for (const patch of [{ lease: 'bad' }, { messageId: 'bad' }, { customerTemplate: undefined }, { customerTemplate: 'true' }, { recipient: 'a@example.test,b@example.test' }]) {
    const f = fixture();
    assert.equal((await sendNativeCheckoutClaim({ ...claim, ...patch }, f.options)).outcome, 'rejected');
    assert.equal(f.calls.length, 0);
  }
});

test('header and size attacks are rejected before provider invocation', async () => {
  for (const patch of [{ course: 'BLS\r\nBcc: victim@example.test' }, { firstName: 'A\u0000B' }, { course: 'x'.repeat(501) }, { address: 'x'.repeat(2001) }, { selectedOptions: [{ key: 'x', display_name: 'x'.repeat(1001) }] }]) {
    const f = fixture();
    assert.equal((await sendNativeCheckoutClaim({ ...claim, confirmation: { ...confirmation, ...patch } }, f.options)).outcome, 'rejected');
    assert.equal(f.calls.length, 0);
  }
});

test('both owned recovery paths render without payment or registration confirmation claims', async () => {
  for (const path of ['/register/', '/register/checkout/']) {
    const f = fixture();
    const result = await sendNativeCheckoutClaim({ ...claim, confirmation: { ...recovery, recoveryUrl: `https://www.910cpr.com${path}?recover=${token}` } }, f.options);
    assert.equal(result.outcome, 'sent');
    const payload = sent(f);
    assert.match(payload.subject, /Finish your registration/);
    assert.match(payload.html, /Return to checkout/);
    assert.match(payload.text, /9:30 AM Eastern/);
    assert.doesNotMatch(payload.text + payload.html + payload.subject, /Payment received|You’re registered/);
  }
});

test('recovery URL allows only one UUID recovery capability on an owned HTTPS path', async () => {
  const urls = [
    `https://evil.example/register/?recover=${token}`,
    `https://www.910cpr.com.evil.example/register/?recover=${token}`,
    `http://www.910cpr.com/register/?recover=${token}`,
    `//www.910cpr.com/register/?recover=${token}`,
    `https://user:pass@www.910cpr.com/register/?recover=${token}`,
    `https://www.910cpr.com:8443/register/?recover=${token}`,
    `https://www.910cpr.com/admin/?recover=${token}`,
    `https://www.910cpr.com/register/?recover=${token}&next=https://evil.example`,
    `https://www.910cpr.com/register/?recover=${token}&recover=${token}`,
    `https://www.910cpr.com/register/?recover=${token}#fragment`,
    `https://www.910cpr.com/register/?recover=------------------------------------`,
    `https://www.910cpr.com/register/?recover=`,
    ` https://www.910cpr.com/register/?recover=${token}`,
    `javascript:alert(1)`,
  ];
  for (const recoveryUrl of urls) {
    const f = fixture();
    assert.equal((await sendNativeCheckoutClaim({ ...claim, confirmation: { ...recovery, recoveryUrl } }, f.options)).outcome, 'rejected', recoveryUrl);
    assert.equal(f.calls.length, 0);
  }
  const f = fixture();
  assert.equal((await sendNativeCheckoutClaim({ ...claim, confirmation: { ...recovery, holdExpiresAt: 'tomorrow' } }, f.options)).outcome, 'rejected');
  assert.equal(f.calls.length, 0);
});

test('reminders preserve renderer wording and never invent new payment evidence', async () => {
  const f = fixture();
  await sendNativeCheckoutClaim({ ...claim, confirmation: { ...confirmation, kind: 'reminder' } }, f.options);
  assert.match(sent(f).subject, /Class reminder/);
  assert.doesNotMatch(sent(f).text + sent(f).html, /Payment received/);
});

test('existing course-specific preparation is preserved without promising automatic code delivery', () => {
  for (const courseId of ['209806', '359474']) {
    const content = renderNativeCheckoutClaim({ ...claim, confirmation: { ...confirmation, courseId } });
    assert.match(content.text, /BLS Student Manual/);
    assert.match(content.text, /BLS Provider eCard/);
  }
  for (const courseId of ['210549', '509474']) {
    const skills = renderNativeCheckoutClaim({ ...claim, confirmation: { ...confirmation, courseId } });
    assert.match(skills.text, /skills session only/);
    assert.doesNotMatch(skills.text, /manually provides/);
    const bundle = renderNativeCheckoutClaim({ ...claim, confirmation: { ...confirmation, courseId, selectedOptions: [{key: 'aha_heartcode_bls_online', display_name: 'Synthetic HeartCode option'}] } });
    assert.match(bundle.text, /manually provides/);
    assert.doesNotMatch(bundle.text, /access code is sent in a separate email after payment/);
  }
  for (const courseId of ['209809', '351632']) {
    const content = renderNativeCheckoutClaim({ ...claim, confirmation: { ...confirmation, course: 'Synthetic Heartsaver course', courseId } });
    assert.doesNotMatch(content.text, /BLS Provider eCard|BLS Student Manual/);
  }
});

test('fulfillment lane stays plain text and restricted to the approved owner address', async () => {
  const fulfillment = { ...claim, customerTemplate: false, confirmation: null, recipient: 'brian@910cpr.com', subject: 'Synthetic fulfillment', body: 'Do not auto-release codes or materials.' };
  const f = fixture();
  assert.equal((await sendNativeCheckoutClaim(fulfillment, f.options)).outcome, 'sent');
  assert.equal(sent(f).html, undefined);
  assert.equal(sent(f).text, fulfillment.body);
  for (const patch of [{ recipient: 'student@example.test' }, { confirmation }]) {
    const f = fixture();
    assert.equal((await sendNativeCheckoutClaim({ ...fulfillment, ...patch }, f.options)).outcome, 'rejected');
    assert.equal(f.calls.length, 0);
  }
});

test('structured transport retains stable message dedupe independent of the claim lease', async () => {
  const f = fixture();
  await sendNativeCheckoutClaim(claim, f.options);
  await sendNativeCheckoutClaim({ ...claim, lease: token }, f.options);
  assert.equal(f.calls[0][1].headers['idempotency-key'], `native-checkout-${id}`);
  assert.equal(f.calls[0][1].headers['idempotency-key'], f.calls[1][1].headers['idempotency-key']);
});

test('structured transport preserves receipt and ambiguity outcomes', async () => {
  for (const [response, state] of [[() => Response.json({id: providerId}), 'sent'], [() => Response.json({}, {status: 422}), 'rejected'], [() => Response.json({}, {status: 503}), 'ambiguous'], [() => Response.json({}), 'ambiguous'], [() => {throw Error('private-provider-error');}, 'ambiguous']]) {
    const f = fixture(response);
    const result = await sendNativeCheckoutClaim(claim, f.options);
    assert.equal(result.outcome, state);
    assert.equal(f.calls.length, 1);
    assert.doesNotMatch(JSON.stringify(result), /private-provider-error/);
  }
});

test('provider-only legacy entry point cannot pass through arbitrary HTML', async () => {
  const f = fixture();
  await sendNativeConfirmation(claim, f.options);
  assert.equal(sent(f).html, undefined);
});

test('the integration has no implicit provider call or environment fallback', async () => {
  const oldFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => { calls++; throw Error('unexpected network'); };
  try {
    assert.equal((await sendNativeCheckoutClaim(claim, { apiKey: 'synthetic', from: 'sender@example.test' })).outcome, 'rejected');
    assert.equal(calls, 0);
  } finally { globalThis.fetch = oldFetch; }
});
