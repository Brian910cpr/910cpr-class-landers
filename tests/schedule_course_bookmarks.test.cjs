const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {execFileSync} = require('node:child_process');
const {test} = require('node:test');
const path = require('node:path');
const vm = require('node:vm');
const ResolvedSelectorAvailability = require('../docs/assets/resolved-selector-availability.js');

const root = path.join(__dirname, '..');
const docs = path.join(root, 'docs');
const schedule = readFileSync(path.join(docs, 'schedule.html'), 'utf8');
const productionOrigin = 'https://www.910cpr.com';
const defaults = {
  '/arc.html': '372258',
  '/hsi.html': '463743',
  '/uscg-elementary-first-aid-cpr.html': '209809',
};
const exact = {
  '/bls.html#provider': ['209806', 'in-person'],
  '/bls.html#renewal': ['359474', 'in-person'],
  '/bls.html#heartcode': ['210549', 'skills-session'],
  '/acls.html#provider': ['241108', 'in-person'],
  '/acls.html#renewal': ['209818', 'in-person'],
  '/acls.html#heartcode': ['209811', 'skills-session'],
  '/pals.html#provider': ['209805', 'in-person'],
  '/pals.html#renewal': ['251496', 'in-person'],
  '/pals.html#heartcode': ['209812', 'skills-session'],
  '/heartsaver.html#first-aid-cpr-aed': ['209809', 'in-person'],
  '/heartsaver.html#first-aid-cpr-aed-blended': ['329495', 'blended'],
  '/heartsaver.html#cpr-aed': ['344085', 'in-person'],
  '/heartsaver.html#cpr-aed-online': ['209808', 'blended'],
  '/heartsaver.html#pediatric-first-aid-cpr-aed-in-person': ['351632', 'in-person'],
  '/heartsaver.html#pediatric-first-aid-cpr-aed': ['251545', 'blended'],
  '/family-cpr.html#family-cpr': ['252737', 'in-person'],
};
const decode = s => s.replaceAll('&amp;', '&').replaceAll('&quot;', '"');
const links = html => [...html.matchAll(/<a class="button" href="([^"]+)"(?: aria-label="([^"]+)")?>([^<]+)<\/a>/g)]
  .map(([, href, name, text]) => [decode(href), decode(name || text)]);

class Element {
  constructor() {
    this.classList = {add() {}, remove() {}};
    this.children = [];
    this.dataset = {};
    this.attrs = {};
  }

  set innerHTML(value) { this.children = []; this.content = value; }
  setAttribute(name, value) { this.attrs[name] = value; }
  addEventListener() {}
  focus() {}
  scrollIntoView() {}
  append(...elements) { this.children.push(...elements); }
  appendChild(element) { this.append(element); }
  *descendants() {
    yield this;
    for (const child of this.children) yield* child.descendants();
  }
}

function initDestination(href, mobile = true) {
  const location = new URL(href, productionOrigin);
  const markup = readFileSync(path.join(docs, location.pathname), 'utf8');
  const script = [...markup.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1])
    .find(text => text.includes('const courseOptions ='));
  assert.ok(script, href);
  const elements = new Map();
  const listeners = new Map();
  const getElementById = id => {
    if (!elements.has(id)) {
      const node = new Element();
      node.parentNode = {insertBefore() {}};
      elements.set(id, node);
    }
    return elements.get(id);
  };
  const pressed = () => [...getElementById('course-option-list').descendants()].filter(el => el.attrs['aria-pressed'] === 'true').map(el => el.dataset.courseId);
  const box = {
    URLSearchParams, ResolvedSelectorAvailability,
    CalendarTimeFilters: {mount: () => ({constraints: {}}), filterDates: dates => dates},
    window: {
      location,
      addEventListener: (event, callback) => listeners.set(event, callback),
      matchMedia: () => ({matches: mobile}),
      requestAnimationFrame() {},
    },
    document: {getElementById, createElement: () => new Element(), querySelector: () => null, addEventListener() {}},
    fetch: () => new Promise(() => {}), setInterval() {}, setTimeout() {},
  };
  vm.createContext(box);
  vm.runInContext(script, box, {filename: location.pathname});
  return {
    pressed,
    delivery: () => vm.runInContext('courseOptions.find(c => c.courseId === selectedCourseId).deliveryMode', box),
    projectedIds: () => {
      const slot = {courses: Object.values(exact).map(([courseId]) => ({courseId})).filter((item, i, all) => all.findIndex(row => row.courseId === item.courseId) === i)};
      box.fixture = slot;
      return Array.from(vm.runInContext('filteredCourses(fixture).map(c => c.courseId)', box));
    },
    switchBookmark: hash => { location.hash = hash; listeners.get('hashchange')(); },
  };
}

test('published schedule links match the generator and all lead to existing production paths', () => {
  const generated = execFileSync('python', ['-B', '-c', 'from scripts.build_index_from_public import build_html; print(build_html([]))'], {cwd: root, encoding: 'utf8'});
  assert.deepEqual(links(schedule), links(generated));
  assert.deepEqual(links(schedule).filter(([href]) => href.includes('#')).map(([href]) => href).sort(), Object.keys(exact).sort());
  assert.deepEqual(links(schedule).filter(([href]) => !href.includes('#')).map(([href]) => href).sort(),
    [...Object.keys(defaults), '/contact.html', 'tel:9103955193'].sort());
  for (const [href, name] of links(schedule)) {
    if (href.startsWith('tel:')) continue;
    const url = new URL(href, productionOrigin);
    assert.equal(url.origin, productionOrigin, href);
    assert.equal(url.search, '', href);
    const html = readFileSync(path.join(docs, url.pathname), 'utf8');
    assert.ok(html.includes('<title>'), href);
    if (href.includes('#')) assert.ok(name.length > 8, href);
    if (href === '/contact.html') assert.match(html, /Questions about a class or training requirement/);
    if (href.startsWith('/uscg-')) assert.match(html, /AMERHA-216/);
  }
});

test('every exact schedule link presses the promised course and filters times to that ID, on both layouts', () => {
  for (const [href, [courseId, delivery]] of Object.entries(exact)) {
    for (const mobile of [true, false]) {
      const selector = initDestination(href, mobile);
      assert.deepEqual(selector.pressed(), [courseId], href);
      assert.equal(selector.delivery(), delivery, href);
      assert.deepEqual(selector.projectedIds(), [courseId], href);
    }
  }
});

test('remaining family and maritime destinations retain their production selector defaults', () => {
  for (const [href, courseId] of Object.entries(defaults)) {
    assert.deepEqual(initDestination(href).pressed(), [courseId], href);
  }
});

test('pediatric bookmark survives reload and switches exactly on hash changes', () => {
  const blended = '/heartsaver.html#pediatric-first-aid-cpr-aed';
  for (const mobile of [true, false]) {
    const selector = initDestination(blended, mobile);
    assert.deepEqual(selector.pressed(), ['251545']);
    selector.switchBookmark('#pediatric-first-aid-cpr-aed-in-person');
    assert.deepEqual(selector.pressed(), ['351632']);
    assert.deepEqual(selector.projectedIds(), ['351632']);
    selector.switchBookmark('#pediatric-first-aid-cpr-aed');
    assert.deepEqual(selector.pressed(), ['251545']);
    selector.switchBookmark('#unknown-pediatric-option');
    assert.deepEqual(selector.pressed(), ['251545']);
    assert.deepEqual(initDestination(blended, mobile).pressed(), ['251545']);
  }
});
