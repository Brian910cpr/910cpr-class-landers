// Coverage gaps are explicit, not a declaration that these courses are migrated.
// All sessions and RPC responses below are synthetic; no network or database.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {genericCheckout} from '../supabase/functions/public-registration/generic.mjs';
import {fullCoursePage} from '../supabase/functions/public-registration/full-course.mjs';
const load=path=>JSON.parse(readFileSync(new URL('../'+path,import.meta.url),'utf8'));
const master=load('data/config/course_master.json').courses;
const selected=master.filter(c=>c.status==='active'&&['ARC','HSI'].includes(c.course_family));
const expected={
 '248287':['ARC','BL'],'248288':['ARC','IP'],'369209':['ARC','IP'],
 '372258':['ARC','BL'],'410694':['ARC','BL'],'444919':['ARC','IP'],
 '371954':['HSI','BL'],'374378':['HSI','IP'],'422270':['HSI','IP'],
 '445670':['HSI','BL'],'448630':['HSI','IP'],'449422':['HSI','BL'],'463743':['HSI','IP']
};
const configuredDrafts=[
 ...load('data/config/native_advanced_checkout.json').courses.map(c=>String(c.courseNumber)),
 ...load('data/config/native_heartsaver_course_drafts.json').courses.map(c=>String(c.externalId))
];
test('ARC/HSI checkout gap inventory covers each active source identity and distinguishes seven full classes',()=>{
 assert.deepEqual(selected.map(c=>String(c.enrollware_course_id)).sort(),Object.keys(expected).sort());
 assert.equal(selected.filter(c=>c.format==='IP').length,7);
 assert.equal(selected.filter(c=>c.format==='BL').length,6);
});
for(const c of selected){
 const id=String(c.enrollware_course_id);
 test(`${c.course_family} ${id} ${c.format}: missing native mapping rejects without claiming seats or substituting shared skills`,async()=>{
  assert.deepEqual([c.course_family,c.format],expected[id]);
  assert.equal(configuredDrafts.includes(id),false,'new draft must replace this explicit missing-coverage fixture with reviewed acceptance evidence');
  assert.equal(fullCoursePage(id),null,'new matcher must be reviewed as exact course coverage');
  const calls=[];
  const api=genericCheckout({
   scheduleSession:async externalId=>({nativeReady:true,course_id:id,start_at:'2031-01-01T14:00:00Z',end_at:'2031-01-01T18:00:00Z',external_class_id:externalId}),
   rpc:async(name,args)=>{calls.push({name,args});if(name==='native_checkout_profile')throw Error('native_profile_not_configured');throw Error('unexpected_mutation');},
   catalog:async()=>{throw Error('unexpected_catalog_fallback');}
  });
  // Even if a valid canonical session is supplied, its exact profile is needed.
  await assert.rejects(api.model({course:id,session:'fixture-'+id}),/native_profile_not_configured/);
  assert.deepEqual(calls,[{name:'native_checkout_profile',args:{p_public_course_id:id,p_context:''}}]);
  calls.length=0;
  // A dated full/blended course may not borrow a shared skills availability slot.
  await assert.rejects(api.model({course:id,date:'2031-01-01',startTime:'09:00'}),/session_not_available/);
  assert.deepEqual(calls,[]);
  // Providing an agency skills context still must not rewrite the purchased ID.
  await assert.rejects(api.model({course:id,session:'fixture-'+id,skillsContext:c.course_family==='ARC'?'arc-blended':'hsi-blended'}),/native_profile_not_configured/);
  assert.equal(calls[0].args.p_public_course_id,id);
  assert.notEqual(calls[0].args.p_public_course_id,'509474');
 });
}
