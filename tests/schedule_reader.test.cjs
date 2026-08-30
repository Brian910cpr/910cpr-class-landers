const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'docs/admin/schedule-reader.html'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'docs/data/admin_schedule.json'), 'utf8'));

test('emergency reader is standalone and reads the authoritative schedule file', () => {
  assert.match(html, /\/data\/admin_schedule\.json/);
  assert.match(html, /type="file"/);
  assert.match(html, /cache:'no-store'/);
  assert.doesNotMatch(html, /dashboard\.js|schedule-model\.js/);
});

test('reader covers the fields in the current schedule schema', () => {
  assert.ok(data.sessions.length > 0);
  for (const field of ['start_at','end_at','course_name','location_name','lead_instructor_name','registration_url']) {
    assert.match(html, new RegExp(field));
  }
  assert.match(html, /LanderWareSession\.participantLabel/);
});
