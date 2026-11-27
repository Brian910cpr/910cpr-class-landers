'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const code = fs.readFileSync(path.join(__dirname, '../docs/assets/family-hero.js'), 'utf8');

function visit({random, storage, images = ['1','2','3']} = {}) {
  const calls = {}, element = {
    parentElement: {},
    dataset:{familyHero:'bls',heroImages:JSON.stringify(images.map(url=>({url,alt:'alt '+url,srcset:url+' 480w'})))},
    addEventListener(type,fn){calls[type]=fn},
    removeAttribute(){}
  };
  const math = Object.create(Math); math.random = () => random;
  vm.runInNewContext(code,{document:{querySelectorAll:()=>[element]},sessionStorage:storage,Math:math});
  return {element,calls};
}
test('first load can choose any approved picture, rather than fixed number one',()=>{
  assert.deepEqual([0,.4,.999].map(random=>visit({random}).element.src),['1','2','3']);
});
test('same-tab reload chooses randomly among other shots, not in sequence',()=>{
  let previous;
  const storage = {getItem:()=>previous,setItem:(_,url)=>{previous=url}};
  const first=visit({random:0,storage}); first.calls.load();
  const reload=visit({random:.999,storage});
  assert.equal(reload.element.src,'3');
  reload.calls.load();
  assert.equal(visit({random:.999,storage}).element.src,'2');
});
test('blocked storage does not fix the first choice and broken files try a distinct fallback',()=>{
  const storage={getItem(){throw Error()},setItem(){throw Error()}};
  const {element,calls}=visit({random:.999,storage});
  assert.equal(element.src,'3');
  calls.error(); assert.equal(element.src,'2');
  calls.error(); assert.equal(element.src,'1');
  calls.load();
  calls.error(); assert.equal(element.parentElement.hidden,true);
});
