import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import test from 'node:test';

const source = readFileSync(new URL('../docs/assets/family-hero.js', import.meta.url), 'utf8');
function visit(images, storage = new Map(), blocked = false) {
  const events = {};
  const image = {
    dataset: { familyHero: 'acls', heroImages: JSON.stringify(images) },
    addEventListener: (name, fn) => { events[name] = fn; },
    removeAttribute: name => { delete image[name]; },
  };
  vm.runInNewContext(source, {
    document: { querySelectorAll: () => [image] },
    sessionStorage: {
      getItem: key => { if (blocked) throw Error('disabled'); return storage.get(key); },
      setItem: (key, value) => storage.set(key, value),
    },
  });
  return { image, events };
}
for (const count of [1, 2, 3, 5, 12]) {
  test(`${count} approved images cycle on reload without nonexistent URLs`, () => {
    const images = Array.from({length:count}, (_, i) => ({url:`/ACLS-${i + 1}.webp`,alt:`Role ${i + 1}`}));
    const storage = new Map();
    for (let i = 0; i < count * 2; i++) {
      const { image } = visit(images, storage);
      assert.equal(image.src, images[i % count].url);
      assert.equal(image.alt, images[i % count].alt);
    }
  });
}
test('disabled storage retains the nurse as the usable first image', () => {
  assert.equal(visit([{url:'/RN.webp',alt:'Nurse'}], new Map(), true).image.src, '/RN.webp');
});
test('removed previous asset falls back to first existing candidate', () => {
  const storage = new Map([['910cpr:family-hero:acls','/removed.webp']]);
  assert.equal(visit([{url:'/RN.webp'}], storage).image.src, '/RN.webp');
});
test('load failure tries remaining candidates once then hides the broken image', () => {
  const { image, events } = visit([{url:'/RN.webp',srcset:'/RN-small.webp 480w'},{url:'/Medic.webp'}]);
  events.error();
  assert.equal(image.src, '/Medic.webp');
  assert.equal(image.srcset, undefined);
  events.error();
  assert.equal(image.hidden, true);
});
