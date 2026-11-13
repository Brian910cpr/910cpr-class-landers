import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {catalogChoices,catalogOptionsMarkup,catalogOptionSelections} from '../docs/assets/checkout-catalog-options.js';
const addon=(key,amount=2345)=>({key,display_name:'Fixture eBook',description:'<private> & course materials',unit_amount:amount,active:true});
test('every family projects only its own server catalog and exact current prices',()=>{
 for(const courseId of ['209806','359474','210549','509474','209809','351632','329495','241108','209818','209805','251496','arc-fixture','hsi-fixture','uscg-fixture']){
  const session={courseId,addons:[addon('fixture_paper',3101),addon('fixture_ebook',2202)]};
  const html=catalogOptionsMarkup(0,session,n=>'$'+n.toFixed(2));
  assert.match(html,/31\.01/);assert.match(html,/22\.02/);assert.doesNotMatch(html,/17\.49|data-manual-choice/);
  assert.match(html,/&lt;private&gt; &amp;/);assert.deepEqual(catalogOptionSelections(session,['fixture_ebook']).addons,[{key:'fixture_ebook',quantity:1}]);
  if(!['209806','359474','210549'].includes(courseId))assert.equal(catalogOptionSelections(session,[]).manualChoice,undefined,'do not attach BLS manual semantics to other families');
 }
});
test('unavailable, missing and malformed catalog options cannot become purchasable',()=>{
 const session={addons:[addon('valid'),{...addon('disabled'),active:false},addon('negative',-1),addon('fraction',1.2),addon('bad"key'),addon('valid',9999)]};
 assert.equal(catalogChoices(session).length,2);assert.match(catalogOptionsMarkup(0,session,String),/disabled/);
 for(const keys of [['disabled'],['missing'],['valid','valid']])assert.throws(()=>catalogOptionSelections(session,keys),/invalid_addon/);
 assert.equal(catalogOptionsMarkup(0,{},String),'');
});
test('legacy option wires preserve existing server contract and reject incompatible combinations',()=>{
 const session={addons:['aha_bls_provider_manual_ebook','aha_heartsaver_first_aid_in_person','aha_heartsaver_first_aid_online','aha_heartsaver_first_aid_manual_ebook'].map(k=>addon(k))};
 const chosen=catalogOptionSelections(session,['aha_bls_provider_manual_ebook','aha_heartsaver_first_aid_in_person','aha_heartsaver_first_aid_manual_ebook']);
 assert.equal(chosen.manualChoice,'ebook');assert.equal(chosen.firstAidChoice,'in-person');assert.equal(chosen.firstAidManualChoice,'ebook');
 assert.throws(()=>catalogOptionSelections(session,['aha_heartsaver_first_aid_in_person','aha_heartsaver_first_aid_online']),/invalid_course_option/);
 assert.throws(()=>catalogOptionSelections(session,['aha_heartsaver_first_aid_manual_ebook']),/invalid_course_option/);
});
test('original checkout shell remains, with configured options and version-aware native driver',()=>{
 const page=readFileSync(new URL('../docs/register/index.html',import.meta.url),'utf8');
 for(const retained of ['COMPANY_BILLING_CODES','billing-suggestions','student-body','registrationOrder:','catalogOptionsMarkup','catalogOptionSelections','p.session.nativeReady===true','/assets/generic-checkout.js?v=20261113-existing1'])assert.ok(page.includes(retained),retained);
 assert.doesNotMatch(page,/17\.49|data-manual-choice|String\(session.courseId\)!==/);
});
