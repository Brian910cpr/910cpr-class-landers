import test from 'node:test';
import assert from 'node:assert/strict';
import {paymentSummary} from '../supabase/functions/canonical-session-workspace/payment-summary.ts';

const row = (changes = {}) => ({id: 'order-a', registration_id: 'reg-a', status: 'paid',
  stripe_payment_intent_id: 'pi_private', ...changes});

test('registration without evidence never implies paid', () => {
  assert.equal(paymentSummary('reg-a', []).status, 'unknown_unreconciled');
});
test('only explicit registration links count', () => {
  assert.equal(paymentSummary('reg-b', [row()]).reason, 'no_linked_payment_evidence');
  assert.equal(paymentSummary('', [row({registration_id: ''})]).status, 'unknown_unreconciled');
});
test('paid summary strips amounts, payer identity, URLs, and provider IDs', () => {
  const summary = paymentSummary('reg-a', [row({total: 9900, payer_email: 'private@example.test',
    checkout_url: 'https://private.example.test', recovery_token: 'secret'})]);
  assert.deepEqual(summary, {provider: 'Stripe', status: 'paid', evidence: 'native_order', reason: null});
});
test('refund remains distinct from paid', () => {
  assert.equal(paymentSummary('reg-a', [row({status: 'refunded'})]).status, 'refunded');
});
test('held, cancelled, expired and open checkout do not prove money due', () => {
  for (const status of ['held', 'checkout_open', 'expired', 'cancelled', 'other']) {
    assert.equal(paymentSummary('reg-a', [row({status})]).status, 'unknown_unreconciled');
  }
});
test('does not assume Stripe for every native payment', () => {
  assert.equal(paymentSummary('reg-a', [row({stripe_payment_intent_id: null})]).provider, 'LanderWare');
});
test('duplicate identical source rows collapse', () => {
  assert.equal(paymentSummary('reg-a', [row(), row()]).status, 'paid');
});
test('conflicting duplicates fail closed', () => {
  assert.equal(paymentSummary('reg-a', [row(), row({status: 'refunded'})]).reason, 'conflicting_source_records');
});
test('multiple orders require reconciliation even when both say paid', () => {
  assert.equal(paymentSummary('reg-a', [row(), row({id: 'order-b'})]).reason, 'multiple_orders_require_reconciliation');
});
test('missing order identifier fails closed', () => {
  assert.equal(paymentSummary('reg-a', [row({id: ''})]).reason, 'invalid_source_record');
});
