const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const shared = require('../docs/assets/resolved-selector-availability.js');
const paths = Object.values(JSON.parse(fs.readFileSync('data/config/block_schedule_pages.json')).pages)
  .filter(page => page.render_html !== false).flatMap(page => [page.output_path, ...(page.alias_output_paths || [])]);
const scriptFor = path => fs.readFileSync(path, 'utf8').match(/    let availabilityLoading = false;[\s\S]*?(?=  <\/script>\n<\/body>)/)[0];
const script = scriptFor('docs/bls.html');
const now = Date.parse('2026-10-29T12:00:00Z');
const data = {
  schemaVersion: shared.schemaVersion, validUntil: new Date(now + 60000).toISOString(),
  dates: [{date: '2026-11-01', startTimes: [{startTime: '09:00', courses: [
    {courseId: 'initial', offerType: 'seated_class'},
    {courseId: 'renewal', offerType: 'dynamic_appointment', validUntil: new Date(now + 60000).toISOString()},
  ]}]}],
};
function harness() {
  const timers = new Map(), renders = [];
  let id = 0;
  const context = {
    Date: class extends Date { static now() { return now; } },
    availabilityUrl: '/test-feed', resolvedAvailability: null, availabilityState: 'checking', scheduleDates: [],
    ResolvedSelectorAvailability: {...shared, fetchPublication: async () => data},
    setTimeout: (callback, delay) => { timers.set(++id, {callback, delay}); return id; },
    clearTimeout: key => timers.delete(key),
    setAvailabilityMessage: message => { context.message = message; },
    renderAll: () => renders.push(context.availabilityState),
    document: {hidden: false, addEventListener() {}}, console: {error() {}},
  };
  vm.createContext(context);
  vm.runInContext(script, context);
  return {context, timers, renders};
}
const settle = () => new Promise(resolve => setImmediate(resolve));

test('all public family pages use the same versioned loading repair', () => {
  for (const path of paths) {
    assert.equal(scriptFor(path), script, path);
    assert.match(fs.readFileSync(path, 'utf8'), /resolved-selector-availability.js\?v=20261029-calendar-recovery-1/);
  }
});
test('background refresh preserves usable controls and permits only one in-flight load', async () => {
  const {context, renders} = harness();
  await settle();
  let release, calls = 0;
  context.ResolvedSelectorAvailability.fetchPublication = () => { calls++; return new Promise(resolve => { release = resolve; }); };
  renders.length = 0;
  const refresh = context.loadResolvedAvailability();
  await context.loadResolvedAvailability();
  assert.equal(calls, 1);
  assert.equal(context.availabilityState, 'ready');
  assert.equal(context.scheduleDates.length, 1);
  assert.ok(renders.every(state => state === 'ready'));
  release(data);
  await refresh;
});
test('failed refresh keeps verified classes, filters expired appointments and retries promptly', async () => {
  const {context, timers} = harness();
  await settle();
  context.resolvedAvailability = {...data, validUntil: new Date(now - 1).toISOString()};
  context.ResolvedSelectorAvailability.fetchPublication = async () => { throw Error('offline'); };
  await context.loadResolvedAvailability();
  assert.equal(context.availabilityState, 'ready');
  assert.deepEqual(context.scheduleDates[0].startTimes[0].courses.map(course => course.offerType), ['seated_class']);
  assert.match(context.message, /Retrying automatically/);
  assert.ok([...timers.values()].some(timer => timer.delay === 30000));
});
test('initial failure leaves loading state and schedules recovery without a page reload', async () => {
  const {context, timers} = harness();
  await settle();
  context.resolvedAvailability = null;
  context.ResolvedSelectorAvailability.fetchPublication = async () => { throw Error('offline'); };
  await context.loadResolvedAvailability();
  assert.equal(context.availabilityState, 'failed');
  assert.ok([...timers.values()].some(timer => timer.delay === 30000));
});
