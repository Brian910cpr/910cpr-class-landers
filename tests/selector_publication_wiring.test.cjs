const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const api = require('../docs/assets/resolved-selector-availability.js');
const generator = fs.readFileSync(path.join(root, 'scripts/build_bls_block_schedule_pilot.py'), 'utf8');
function fragment(begin, end) {
  const start = generator.indexOf(begin);
  assert.ok(start >= 0);
  const stop = generator.indexOf(end, start);
  assert.ok(stop > start);
  return generator.slice(start, stop).replaceAll('{{', '{').replaceAll('}}', '}');
}
const loader = fragment('    let availabilityRequestId = 0;', '\n    loadResolvedAvailability();');
const currentDates = fragment('    function currentPublicationDates()', '\n    function filteredDates()');
const click = fragment("        link.addEventListener('click', event =>", '\n        item.append');
const past = '2000-01-01T00:00:00Z';
const future = '2099-01-01T00:00:00Z';
function fixture(validUntil = future) {
  return {schemaVersion: 'selector-resolved-availability.v1', validUntil, dates: [{date: '2090-01-01', startTimes: [{startTime: '10:00', courses: [
    {courseId: 'seated', offerType: 'seated_class', appointmentUrl: '/real'},
    {courseId: 'dynamic', offerType: 'dynamic_appointment', validUntil: future, appointmentUrl: '/offer'},
  ]}]}]};
}
function box(data) {
  const context = {ResolvedSelectorAvailability: api, fetch: async () => ({ok: true, json: async () => data}),
    availabilityUrl: '/fixture', setAvailabilityMessage() {}, renderAll() {}, console,
    scheduleDates: [], resolvedAvailability: null, availabilityState: '', availabilityReady() {return this.availabilityState === 'ready';}};
  vm.createContext(context);
  vm.runInContext(loader + currentDates, context);
  return context;
}
function ids(dates) {return Array.from(dates.flatMap(d => d.startTimes.flatMap(s => s.courses.map(c => c.courseId))));}
test('business clock carries the exact lease-check instant', () => {
  const now = new Date('2030-01-01T12:00:00Z');
  assert.equal(api.businessNow('America/New_York', now).instant, now.getTime());
});
test('generator loader excludes stale dynamic offers and preserves seated identity', async () => {
  const data = fixture(past), ctx = box(data);
  await ctx.loadResolvedAvailability();
  assert.deepEqual(ids(ctx.scheduleDates), ['seated']);
  assert.equal(ctx.scheduleDates[0].startTimes[0].courses[0], data.dates[0].startTimes[0].courses[0]);
});
test('render projection rechecks whole-publication and individual course expiry after load', async () => {
  const data = fixture(), ctx = box(data);
  await ctx.loadResolvedAvailability();
  assert.deepEqual(ids(ctx.currentPublicationDates()), ['seated', 'dynamic']);
  data.dates[0].startTimes[0].courses[1].validUntil = past;
  assert.deepEqual(ids(ctx.currentPublicationDates()), ['seated']);
  data.dates[0].startTimes[0].courses[1].validUntil = future;
  data.validUntil = past;
  assert.deepEqual(ids(ctx.currentPublicationDates()), ['seated']);
});
test('mixed-slot stale link is blocked on every click while seated registration survives', async () => {
  const data = fixture(), ctx = box(data);
  await ctx.loadResolvedAvailability();
  ctx.day = data.dates[0]; ctx.slot = ctx.day.startTimes[0];
  ctx.isPastStart = (day, slot) => api.isPastStart(day, slot, api.businessNow());
  ctx.availabilityReady = () => true;
  let reloads = 0, prevented = 0, handler;
  ctx.loadResolvedAvailability = () => {reloads++;};
  ctx.link = {addEventListener(_name, fn) {handler = fn;}};
  ctx.course = ctx.slot.courses[1];
  vm.runInContext(click, ctx);
  ctx.course.validUntil = past;
  handler({preventDefault() {prevented++;}}); handler({preventDefault() {prevented++;}});
  assert.equal(prevented, 2); assert.equal(reloads, 2);
  ctx.course = ctx.slot.courses[0]; vm.runInContext(click, ctx);
  handler({preventDefault() {prevented++;}});
  assert.equal(prevented, 2);
});
test('visibility reload and overlapping responses cannot restore an older publication', async () => {
  const ctx = box(fixture()); let resolveOld;
  ctx.fetch = () => new Promise(resolve => {resolveOld = resolve;});
  const first = ctx.loadResolvedAvailability();
  const latest = fixture(past);
  ctx.fetch = async () => ({ok: true, json: async () => latest});
  await ctx.loadResolvedAvailability();
  resolveOld({ok: true, json: async () => fixture()}); await first;
  assert.equal(ctx.resolvedAvailability, latest);
  assert.deepEqual(ids(ctx.scheduleDates), ['seated']);
  assert.match(generator, /if \(!document.hidden\) loadResolvedAvailability\(\)/);
});
test('all configured families and courses preserve identity and suppress stale dynamic choices', () => {
  for (const family of ['bls', 'acls', 'pals', 'heartsaver', 'arc', 'hsi', 'uscg_first_aid_cpr_aed', 'family_cpr']) {
    const data = JSON.parse(fs.readFileSync(path.join(root, 'docs/data/block-selector-availability', family + '.json')));
    const source = data.dates.flatMap(d => d.startTimes.flatMap(s => s.courses));
    const visible = api.datesForPublication(data.dates, past);
    const retained = visible.flatMap(d => d.startTimes.flatMap(s => s.courses));
    assert.ok(retained.every(c => c.offerType === 'seated_class'), family);
    assert.equal(retained.length, source.filter(c => c.offerType === 'seated_class').length, family);
    assert.ok(retained.every(c => source.includes(c)), family);
    for (const id of new Set(source.map(c => String(c.courseId)))) {
      assert.ok(api.filterDatesByCourse(visible, id).every(d => d.startTimes.every(s => s.courses.every(c => String(c.courseId) === id))), family + ':' + id);
    }
  }
});
