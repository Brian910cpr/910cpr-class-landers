const test=require('node:test'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');const path=require('node:path');
const api=require('../docs/assets/resolved-selector-availability.js');const root=path.resolve(__dirname,'..');
const caps=JSON.parse(execFileSync('python',['-B','-c','import json;from scripts.build_bls_block_schedule_pilot import selector_registration_capabilities;print(json.dumps(selector_registration_capabilities()))'],{cwd:root,encoding:'utf8'}));
const legacy=id=>'https://coastalcprtraining.enrollware.com/enroll?id='+id;
function row(id='15026275'){const c=caps.sessions[id];return {courseId:c.courseId,courseName:'Synthetic BLS',offerType:'seated_class',date:c.date,startTime:c.startTime,location:c.location,appointmentUrl:legacy(id),registrationUrl:legacy(id)};}
function request(action){assert.equal(action.mode,'request');assert.equal(action.label,'Request this class');assert.ok(action.href.startsWith('mailto:brian@910cpr.com?'));assert.match(action.notice,/No seat is reserved/);return new URL(action.href).searchParams.get('body');}
test('only previously approved sessions with exact course/day/time/public venue keep their own production checkout',()=>{
 assert.equal(Object.keys(caps.sessions).length,6);
 for(const id of Object.keys(caps.sessions)){const action=api.registrationAction(row(id),{},caps);assert.equal(action.mode,'native');assert.equal(action.href,'https://www.910cpr.com/register/?session='+id);assert.equal(new URL(action.href,'https://preview.pages.dev').origin,'https://www.910cpr.com');}
});
test('unsupported families and Skills without verified variant context receive context-specific requests, never external/dev fallbacks',()=>{
 for(const courseId of ['359474','209809','241108','209805','248288','448630','253768','252737','509474']){
  const c={...row(),courseId,courseName:'Synthetic selected '+courseId,appointmentUrl:legacy('14732872'),registrationUrl:legacy('14732872')};const body=request(api.registrationAction(c,{pagePath:'/acls.html'},caps));
  for(const value of [courseId,c.courseName,c.date,c.startTime,c.location,'14732872','https://www.910cpr.com/acls.html'])assert.ok(body.includes(value),value);
  assert.match(body,/not a confirmed reservation/);assert.doesNotMatch(body,/enrollware|pages[.]dev/);
 }
});
test('unknown owned routes and incomplete, conflicting, closed or tampered identities fail to request',()=>{
 for(const patch of [{date:'2031-01-01'},{startTime:'23:59'},{location:'Different venue'},{courseId:'359474'},{offerType:'dynamic_appointment'},{isFull:true},{registration_status:'closed'},{appointmentUrl:legacy('15026275')+'&id=999'}, {appointmentUrl:'https://example.pages.dev/register/?session=15026275'}, {registrationUrl:'/register/?session=999'}, {registrationUrl:'/register/checkout/?session=15026275'}])request(api.registrationAction({...row(),...patch},{},caps));
 request(api.registrationAction({...row(),registrationUrl:'/register/?session=15026275&course=359474'},{},caps));
 request(api.registrationAction(row()));
});
test('explicit verified owned URL is canonicalized but does not authorize a different session',()=>{
 const c={...row(),registrationUrl:'/register/?session=15026275&course=209806'};assert.equal(api.registrationAction(c,{},caps).href,'https://www.910cpr.com/register/?session=15026275');
 request(api.registrationAction({...c,registrationUrl:'/register/?session=14996400'},{},caps));
});
test('actual eight family templates use the shared action and cannot bypass it through full-width Skills',()=>{
 const script=String.raw`
import json,re
from scripts import build_bls_block_schedule_pilot as g
result=[]
for family,config in g.load_block_schedule_page_configs().items():
 cid={'bls':'209806','acls':'241108','pals':'209805','heartsaver':'209809','uscg_first_aid_cpr_aed':'253768','arc':'248288','hsi':'448630','family_cpr':'252737'}[family]
 c=dict(courseId=cid,courseName='Synthetic class',offerType='seated_class',durationMinutes=120,displayStartTime='2:00 PM',location='Wilmington; Shipyard Blvd',appointmentUrl='https://coastalcprtraining.enrollware.com/enroll?id=999')
 slot=dict(startTime='14:00',displayStartTime='2:00 PM',courses=[c]);day=dict(date='2031-01-01',displayDate='January 1,2031',startTimes=[slot])
 p=dict(pageKey=family,pageConfig=config,dates=[day],counts={},generatedAt='2030-12-30T10:00:00-05:00',validUntil='2031-01-02T10:00:00-05:00')
 a=g.render_html(p);b=g.render_html(p)
 result.append(dict(family=family,stable=a==b,action='ResolvedSelectorAvailability.registrationAction(course,' in a,version='resolved-selector-availability.js?v=20261119-request-containment2' in a,bypass="link.href = '/register/skills-session/?'" in a,registry=g.selector_registration_capabilities()))
print(json.dumps(result))
`;
 const rows=JSON.parse(execFileSync('python',['-B','-c',script],{cwd:root,encoding:'utf8',timeout:30000}));assert.equal(rows.length,8);
 for(const r of rows){assert.ok(r.stable,r.family);assert.ok(r.action,r.family);assert.ok(r.version,r.family);assert.equal(r.bypass,false,r.family);assert.doesNotMatch(JSON.stringify(r.registry),/Room B|Shipyard Blvd - B/);}
});

function skillsRow(){const q=new URLSearchParams({course:'509474',date:'2026-11-20',startTime:'10:00',location:':: Wilmington; Shipyard Blvd',instructor:'Synthetic Instructor'});const url='https://www.910cpr.com/register/skills-session/?'+q;return {courseId:'509474',date:'2026-11-20',startTime:'10:00',location:'Wilmington; Shipyard Blvd',instructor:'Synthetic Instructor',publicSelectable:true,offerType:'dynamic_appointment',durationMinutes:45,schedulerConsumptionMinutes:60,cleanupBufferMinutes:15,availabilityBlockId:'synthetic-block',registrationUrl:url,appointmentUrl:url};}
function skillsContext(variant){return {pagePath:'/heartsaver.html',familyContext:'heartsaver',skillsContext:variant,skillsContextVerified:true};}
test('both verified Heartsaver Skills variants preserve exact context and canonical reservation-only route',()=>{
 for(const variant of ['cpr-aed','first-aid-cpr-aed']){const c=skillsRow(),a=api.registrationAction(c,skillsContext(variant),caps),u=new URL(a.href);assert.equal(a.mode,'skills-reservation');assert.equal(a.label,'Schedule skills session');assert.match(a.notice,/does not collect payment/);assert.equal(u.origin,'https://www.910cpr.com');assert.equal(u.searchParams.get('skillsContext'),variant);assert.equal(u.searchParams.get('context'),'heartsaver');for(const k of ['course','date','startTime','instructor'])assert.equal(u.searchParams.get(k),String(k==='course'?c.courseId:c[k]));assert.equal(u.searchParams.get('location'),c.location);}
});
test('Skills missing/mismatched variant, source identities or unsupported modes never bypass containment',()=>{
 const c=skillsRow(),ctx=skillsContext('first-aid-cpr-aed');
 for(const patch of [{skillsContext:''},{skillsContext:'arc-blended'},{familyContext:'arc'},{skillsContextVerified:false},{pagePath:'/arc.html'}])request(api.registrationAction(c,{...ctx,...patch},caps));
 for(const suffix of ['&skillsContext=cpr-aed&context=heartsaver','&context=heartsaver','&skillsContext=cpr-aed','&date=2026-11-21','&unknown=x'])request(api.registrationAction({...c,registrationUrl:c.registrationUrl+suffix},ctx,caps));
 for(const patch of [{publicSelectable:false},{location:'Other venue'},{instructor:'Other Instructor'},{durationMinutes:120},{isFull:true},{offerType:'unknown'},{courseId:'344085'},{registrationUrl:'https://preview.pages.dev/register/skills-session/'}])request(api.registrationAction({...c,...patch},ctx,caps));
 request(api.registrationAction(c,{},caps));
});
