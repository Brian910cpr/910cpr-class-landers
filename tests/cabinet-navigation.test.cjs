'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {parent, child} = require('../docs/admin/cabinet-navigation.js');
const root = 'https://910cpr.com';
const source = fs.readFileSync(require.resolve('../docs/admin/cabinet-navigation.js'), 'utf8');
function surface(path) {
  const location = new URL(path, root), listeners = {}, control = {href: '', id: 'cabinetUp'};
  const window = {scrollY: 450, scrollTo: (x,y) => { window.restoredY = y; }};
  const document = {getElementById: () => control, addEventListener: (type, fn) => {listeners[type] = fn;}};
  vm.runInNewContext(source, {location, window, document, URL, URLSearchParams, requestAnimationFrame: fn => fn()});
  return {location, window, listeners, control};
}
test('rejects remote, executable, credentialed and non-cabinet parents', () => {
  for (const url of ['https://evil.example/admin/all-classes.html','//evil.example/admin/all-classes.html','javascript:alert(1)','https://user:pass@910cpr.com/admin/all-classes.html','/register/?session=1']) assert.equal(parent(url), '');
});
test('does not carry auth parameters or fragments', () => {
  assert.equal(parent('/admin/person-record.html?id=p&token=secret&key=secret#private'), '/admin/person-record.html?id=p');
});
test('nested registry -> class -> person has one-level parents', () => {
  const registry='/admin/class-registry.html?q=BLS&source=both&navY=350';
  const session=child('/admin/all-classes.html?session=s',registry);
  const person=child('/admin/person-record.html?id=p',session);
  assert.equal(new URL(person,root).searchParams.get('up'),session);
  assert.equal(new URL(session,root).searchParams.get('up'),registry);
});
test('nested context remains bounded', () => {
  let url='/admin/all-classes.html';
  for(let i=0;i<20;i++) url=child('/admin/person-record.html?id=p',url);
  assert.ok(url.length<12000);
  assert.equal(parent('x'.repeat(12001)), '');
});
test('person Up survives reload with explicit class, query, month and scroll', () => {
  const up='/admin/all-classes.html?session=s&q=BLS&filter=past&month=2026-09&navY=450';
  const url=child('/admin/person-record.html?id=p',up);
  for(let i=0;i<2;i++) assert.equal(surface(url).control.href,up);
});
test('direct person and untrusted parent fall back to cabinet', () => {
  assert.equal(surface('/admin/person-record.html?id=p').control.href,'/admin/all-classes.html');
  assert.equal(surface('/admin/person-record.html?id=p&up=https://evil.example').control.href,'/admin/all-classes.html');
});
test('class Up returns to registry when class originated there', () => {
  const up='/admin/class-registry.html?q=BLS&health=issues';
  assert.equal(surface(child('/admin/all-classes.html?session=s',up)).control.href,up);
});
test('direct class Up removes selection and retains current cabinet controls', () => {
  const page=surface('/admin/all-classes.html?session=s');
  page.window.LanderWareCabinetState=()=>({q:'CPR',filter:'all',month:'2026-11'});
  page.window.LanderWareCabinet.updateUp();
  const url=new URL(page.control.href,root);
  assert.equal(url.searchParams.has('session'),false);
  assert.equal(url.searchParams.get('q'),'CPR');
  assert.equal(url.searchParams.get('filter'),'all');
  assert.equal(url.searchParams.get('month'),'2026-11');
});
test('left, middle and context-menu drill-down preserve parent without history navigation', () => {
  for(const type of ['click','auxclick','contextmenu']) {
    const page=surface('/admin/all-classes.html?session=s');
    page.window.LanderWareCabinetState=()=>({q:'CPR',filter:'past',month:'2026-09'});
    const link={href:root+'/admin/person-record.html?id=p',hasAttribute:()=>false};
    page.listeners[type]({target:{closest:()=>link}});
    const up=new URL(new URL(link.href,root).searchParams.get('up'),root);
    assert.equal(up.searchParams.get('session'),'s');
    assert.equal(up.searchParams.get('q'),'CPR');
    assert.equal(up.searchParams.get('navY'),'450');
  }
});
test('Up link and cabinet-level links are never redecorated', () => {
  const page=surface('/admin/person-record.html?id=p');
  for(const link of [{id:'cabinetUp',href:'/admin/all-classes.html?session=s'},{href:root+'/admin/all-classes.html',hasAttribute:()=>false}]) {
    const original=link.href;
    page.listeners.click({target:{closest:()=>link}});
    assert.equal(link.href,original);
  }
});
test('scroll restoration is explicit and clamped', () => {
  const page=surface('/admin/all-classes.html?navY=350');
  page.window.LanderWareCabinet.restoreScroll();
  assert.equal(page.window.restoredY,350);
});
test('rendered page sources expose Up controls and version navigation assets', () => {
  for(const page of ['all-classes','person-record','admin-port']) {
    const html=fs.readFileSync(`docs/admin/${page}.html`,'utf8');
    assert.match(html,/id="cabinetUp"[^>]*>↑ Up<\/a>/);
    assert.match(html,/cabinet-navigation\.js\?v=20261014-241/);
  }
  assert.match(fs.readFileSync('docs/admin/all-classes.html','utf8'),/all-classes\.js\?v=20261014-241/);
  assert.match(fs.readFileSync('docs/admin/class-registry.html','utf8'),/class-registry\.js\?v=20261014-241/);
});
