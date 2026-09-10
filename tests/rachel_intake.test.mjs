import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { intakeDetails, normalizeRachelPayload, normalizePhone } from '../supabase/functions/rachel-intake/normalize.mjs';

const fixture = JSON.parse(fs.readFileSync(new URL('./fixtures/marblism_rachel_completed_test_call.json', import.meta.url), 'utf8'));

test('normalizes North American phone numbers', () => {
  assert.equal(normalizePhone('(910) 395-5193'), '+19103955193');
  assert.equal(normalizePhone('+1 910-395-5193'), '+19103955193');
});
test('retains the completed Marblism fixture as a test call', () => {
  const result = normalizeRachelPayload(fixture);
  assert.equal(result.external_call_id, 'fixture-test-reschedule-20260909T2118-0400');
  assert.equal(result.is_test, true);
  assert.equal(result.intake.requested_credential, 'BLS');
  assert.deepEqual(result.intake.preferred_windows, ['2026-09-24 5:00 PM']);
});

test('requires a stable external call id for idempotency', () => {
  assert.throws(() => normalizeRachelPayload({call:{summary:'no id'}}), /external_call_id is required/);
});

test('renders an action-required intake without promising an operation', () => {
  const details = intakeDetails(normalizeRachelPayload(fixture));
  assert.match(details, /Credential: BLS/);
  assert.match(details, /Verify requested class availability/);
  assert.doesNotMatch(details, /scheduled|registered|invoiced/i);
});
