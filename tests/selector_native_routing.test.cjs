const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm');
const {execFileSync}=require('node:child_process');
const api=require('../docs/assets/resolved-selector-availability.js');
const legacy='https://coastalcprtraining.enrollware.com/enroll?id=123456';
test('existing BLS Initial seated retail route survives a legacy-source refresh without activating other offerings',()=>{
 assert.equal(api.registrationDestination({courseId:'209806',offerType:'seated_class',appointmentUrl:legacy}),'/register/?session=123456');
 for(const courseId of ['359474','209809','241108','209805','248288','448630','253768','252737'])assert.equal(api.registrationDestination({courseId,offerType:'seated_class',appointmentUrl:legacy}),legacy);
 assert.equal(api.registrationDestination({courseId:'209806',offerType:'dynamic_appointment',appointmentUrl:legacy}),legacy);
 for(const url of [legacy+'&id=999',legacy.replace('id=123456','id=unknown'),legacy.replace('coastalcprtraining.enrollware.com','unverified.invalid')])assert.equal(api.registrationDestination({courseId:'209806',offerType:'seated_class',appointmentUrl:url}),url);
});
test('explicit owned checkout destinations preserve exact session/course/context and take precedence over stale external URLs',()=>{
 for(const prefix of ['/register/','/register/checkout/']){
  const destination=prefix+'?session=lw-11111111-1111-4111-8111-111111111111&course=209809&context=heartsaver';
  assert.equal(api.registrationDestination({courseId:'209809',registrationUrl:destination,appointmentUrl:legacy}),destination);
 }
 const skills='/register/skills-session/?course=509474&date=2031-01-01&startTime=09%3A30&skillsContext=arc-blended';
 assert.equal(api.registrationDestination({registrationUrl:skills,appointmentUrl:legacy}),skills);
});
test('actual family templates preserve native links on repeated rebuilds and version the changed shared resolver',()=>{
 const script=String.raw`
import copy,json,re
from scripts import build_bls_block_schedule_pilot as generator
configs=generator.load_block_schedule_page_configs();result=[]
for family,cid in [('bls','209806'),('heartsaver','209809'),('acls','241108'),('pals','209805'),('arc','248288'),('hsi','448630'),('uscg_first_aid_cpr_aed','253768'),('family_cpr','252737')]:
 row=dict(courseId=cid,courseName='Synthetic class',displayStartTime='9:30 AM',durationMinutes=75,location='Synthetic room')
 slot=dict(startTime='09:30',displayStartTime='9:30 AM',courses=[row]);day=dict(date='2031-01-01',displayDate='January 1, 2031',startTimes=[slot])
 p=dict(pageKey=family,pageConfig=configs[family],dates=[day],counts={},generatedAt='2030-12-30T10:00:00-05:00',validUntil='2031-01-02T10:00:00-05:00')
 row.update(courseId=cid,courseFamily=family,offerType='seated_class',appointmentUrl='https://coastalcprtraining.enrollware.com/enroll?id=123456',registrationUrl='/register/?session=123456&course='+cid+'&context='+family)
 row.pop('authority',None);slot['courses']=[row];day['startTimes']=[slot];p['dates']=[day]
 a=generator.render_html(p);b=generator.render_html(p)
 compact=generator.public_selector_availability_payload(p)
 result.append(dict(family=family,expected=row['registrationUrl'],embedded=compact['dates'][0]['startTimes'][0]['courses'][0],stable=a==b,usesResolver='link.href = ResolvedSelectorAvailability.registrationDestination(course);' in a,versioned='/assets/resolved-selector-availability.js?v=20261113-native-routing1' in a))
print(json.dumps(result))
`;
 const rows=JSON.parse(execFileSync(process.env.PYTHON||'python',['-B','-c',script],{cwd:require('node:path').resolve(__dirname,'..'),encoding:'utf8',timeout:30000}));
 assert.equal(rows.length,8);
 for(const row of rows){
  assert.ok(row.stable,row.family);assert.ok(row.usesResolver,row.family);assert.ok(row.versioned,row.family);
  const context=vm.createContext({course:row.embedded,link:{},ResolvedSelectorAvailability:api});
  vm.runInContext('link.href = ResolvedSelectorAvailability.registrationDestination(course);',context);
  assert.equal(context.link.href,row.expected,row.family);
 }
});
