const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {test} = require('node:test');
const path = require('node:path');
const vm = require('node:vm');
const ResolvedSelectorAvailability = require('../docs/assets/resolved-selector-availability.js');

const root = path.join(__dirname, '..');
const docs = path.join(root, 'docs');

const productionOrigin = 'https://www.910cpr.com';
const exact = {
  '/heartsaver.html#first-aid-cpr-aed': ['209809', 'in-person'],
  '/heartsaver.html#first-aid-cpr-aed-blended': ['329495', 'blended'],
};

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
      addEventListener() {},
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
  };
}


test('Generated Heartsaver course links select and filter the exact format', () => {
  const lander=readFileSync(path.join(docs,'courses','heartsaver-first-aid-cpr-aed.html'),'utf8');
  assert.doesNotMatch(lander, /enrollware|appointmentdayid|data-(?:row|original)-href|hybrid-inventory|live-sessions/i);
  const targets = [...lander.matchAll(/href="(\/heartsaver\.html#first-aid-cpr-aed[^"]*)"/g)].map(m => m[1]);
  assert.equal(targets.length, 2);
  assert.equal(new Set(targets).size, 2);
  for (const href of targets) {
    const [courseId, delivery]=exact[href];
    for (const mobile of [true, false]) {
      const selector = initDestination(href, mobile);
      assert.deepEqual(selector.pressed(), [courseId], href);
      assert.equal(selector.delivery(), delivery, href);
      assert.deepEqual(selector.projectedIds(), [courseId], href);
    }
  }
});