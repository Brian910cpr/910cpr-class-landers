const test = require('node:test');
const assert = require('node:assert/strict');
const {
  EASTERN_TIME_ZONE,
  easternWallTimeIso,
  buildManualClassRecord,
} = require('../docs/admin/all-classes.js');

test('serializes winter and summer wall times with date-correct Eastern offsets', () => {
  assert.equal(EASTERN_TIME_ZONE, 'America/New_York');
  assert.equal(easternWallTimeIso('2026-01-15', '09:30'), '2026-01-15T09:30:00-05:00');
  assert.equal(easternWallTimeIso('2026-07-15', '09:30'), '2026-07-15T09:30:00-04:00');
});

test('fails closed for nonexistent and ambiguous Eastern wall times', () => {
  assert.throws(
    () => easternWallTimeIso('2026-03-08', '02:30'),
    /does not exist because daylight saving time begins/,
  );
  assert.throws(
    () => easternWallTimeIso('2026-11-01', '01:30'),
    /occurs twice because daylight saving time ends/,
  );
});

test('HOT_SYNC record preserves owner-entered Eastern wall time', () => {
  const record = buildManualClassRecord({
    visibility: 'public', courseKey: 'bls', course: 'BLS Provider',
    date: '2026-12-10', start: '08:15', end: '11:45', capacity: '8',
    client: 'Example Agency', location: 'Raleigh', instructor: '', notes: '',
  }, {id: 'hs-test', createdAt: '2026-09-11T12:00:00.000Z'});
  const hotSyncPayload = JSON.parse(JSON.stringify(record));

  assert.equal(hotSyncPayload.start, '2026-12-10T08:15:00-05:00');
  assert.equal(hotSyncPayload.end, '2026-12-10T11:45:00-05:00');
  assert.equal(hotSyncPayload.source, 'hot_sync_manual');
  assert.equal(hotSyncPayload.id, 'hs-test');
});
