import test from 'node:test';
import assert from 'node:assert/strict';
import {easternDay,shiftMonth,monthCells,groupOffers,dayLabel} from '../docs/reschedule/calendar.js';
test('Eastern civil dates survive UTC midnight and both DST transitions',()=>{
 for(const [instant,day] of [['2026-11-01T03:59:00Z','2026-10-31'],['2026-11-01T05:30:00Z','2026-11-01'],['2026-11-01T06:30:00Z','2026-11-01'],['2026-03-08T06:59:00Z','2026-03-08'],['2026-03-08T07:01:00Z','2026-03-08']])assert.equal(easternDay(instant),day);
});
test('month navigation crosses years and leap February without overflow',()=>{
 assert.equal(shiftMonth('2026-12',1),'2027-01');assert.equal(shiftMonth('2027-01',-1),'2026-12');
 const leap=monthCells('2028-02');assert.equal(leap.filter(Boolean).length,29);assert.equal(leap.length%7,0);assert.equal(leap[2],'2028-02-01');
 assert.equal(monthCells('2026-02').filter(Boolean).length,28);assert.match(dayLabel('2026-11-01'),/Sunday, November 1, 2026/);
});
test('grouping preserves every returned offer and exact object identity for all courses',()=>{
 for(const course of ['209806','359474','209809']){
  const a={id:course+'a',course,startsAt:'2026-12-02T00:30:00Z'},b={id:course+'b',course,startsAt:'2026-12-01T20:30:00Z'},c={id:course+'c',course,startsAt:'2027-01-05T18:00:00Z'};
  const grouped=groupOffers([c,a,b]);assert.deepEqual([...grouped.keys()],['2026-12-01','2027-01-05']);assert.equal(grouped.get('2026-12-01')[0],a);assert.equal(grouped.get('2026-12-01')[1],b);assert.equal(grouped.get('2027-01-05')[0],c);
 }assert.equal(groupOffers([]).size,0);
});
