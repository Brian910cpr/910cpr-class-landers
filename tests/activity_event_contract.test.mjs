import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createActivityEvent } from '../scripts/activity_event_contract.mjs';

const registry = { 'validation.contract': { source: 'validation', visibility: 'owner' } };
const input = { event_id: 'b11b7f50-e4a5-4497-b1da-578e181768ff',
  correlation_id: 'c11b7f50-e4a5-4497-b1da-578e181768ff', source: 'validation',
  operation_type: 'validation.contract', timestamp: '2026-10-15T12:00:00.000Z',
  status: 'in_flight', duration_ms: null, visibility: 'owner' };
const build = (patch = {}) => createActivityEvent({ ...input, ...patch }, registry);

test('start and completion retain correlation, separate event IDs, and safe summaries', () => {
  const start = build();
  const end = build({ event_id: 'd11b7f50-e4a5-4497-b1da-578e181768ff', status: 'success', duration_ms: 42 });
  assert.equal(start.correlation_id, end.correlation_id);
  assert.notEqual(start.event_id, end.event_id);
  assert.equal(end.safe_summary, 'Operation completed');
  assert.ok(Object.isFrozen(end));
});
test('all observed lifecycle statuses have bounded summaries', () => {
  for (const status of ['queued', 'in_flight', 'retry', 'success', 'blocked', 'error']) {
    const event = build({ status, duration_ms: ['success', 'blocked', 'error'].includes(status) ? 0 : null });
    assert.ok(event.safe_summary.length < 100);
  }
});
test('reject uninstrumented sources/operations and fake idle events', () => {
  for (const patch of [{ source: 'gmail' }, { operation_type: 'gmail.read' }, { status: 'idle' },
    { operation_type: 'toString' }]) assert.throws(() => build(patch));
});
test('reject private payloads and freeform summaries rather than attempting redaction', () => {
  for (const key of ['payload', 'email', 'prompt', 'error_message', 'api_key', 'safe_summary', 'url']) {
    assert.throws(() => build({ [key]: 'private input' }));
  }
});
test('cannot downgrade owner scope or assign invalid visibility', () => {
  for (const visibility of ['staff', 'public', null]) assert.throws(() => build({ visibility }));
});
test('timestamps and opaque IDs fail closed', () => {
  for (const patch of [{ timestamp: 'yesterday' }, { timestamp: '2026-02-30T12:00:00.000Z' },
    { timestamp: '2026-10-15T08:00:00-04:00' }, { event_id: 'customer@example.com' },
    { correlation_id: 'customer-123' }]) assert.throws(() => build(patch));
});
test('duration is null while pending and nonnegative safe integer at termination', () => {
  assert.throws(() => build({ duration_ms: 0 }));
  for (const duration_ms of [null, -1, 1.5, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
    assert.throws(() => build({ status: 'error', duration_ms }));
  }
});
test('staff visibility requires explicitly registered staff-safe operation', () => {
  const event = createActivityEvent({ ...input, visibility: 'staff' },
    { 'validation.contract': { source: 'validation', visibility: 'staff' } });
  assert.equal(event.visibility, 'staff');
});
