const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'docs/admin/toolbox.html'), 'utf8');
const js = fs.readFileSync(path.join(root, 'docs/admin/toolbox.js'), 'utf8');
const nav = fs.readFileSync(path.join(root, 'docs/admin/admin-nav.js'), 'utf8');

test('admin navigation exposes the toolbox as its front door', () => {
  assert.match(nav, /\['\/admin\/toolbox\.html','ADMIN Toolbox'\]/);
  assert.ok(nav.indexOf('ADMIN Toolbox') < nav.indexOf('LanderWare Operations'));
});

test('toolbox exposes stable operations and a clearly marked beta dock', () => {
  assert.match(html, /ADMIN Toolbox/);
  assert.match(js, /group:'Beta dock',status:'beta'/);
  assert.match(js, /LanderWare Operations/);
  assert.match(js, /NHCSO Training Workspace v6/);
  assert.match(js, /Add-on Catalog Workbench/);
  assert.match(js, /LanderWare Supervisor/);
});

test('local tools are surfaced as copyable commands, not fake web links', () => {
  assert.match(js, /python scripts\/check_schedule_integrity\.py/);
  assert.match(js, /data-command/);
  assert.match(js, /Needs integration/);
});
