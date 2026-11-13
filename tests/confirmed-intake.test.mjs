import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import vm from 'node:vm';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
async function fixture(){
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 await db.exec(load('tests/helpers/confirmed-intake-schema.sql'));
 await db.exec(load('supabase/reviewed/confirmed-intake-installed-contract.sql'));
 await db.exec(`create trigger canonical_projection after insert or update or delete on class_sessions for each row execute function sync_enrollware_class_session_to_landerware();
 create trigger workspace_identity before insert or update or delete on landerware_sessions for each row execute function enforce_canonical_workspace_schedule();`);
 const scalar=async(q,args=[])=>Object.values((await db.query(q,args)).rows[0])[0];
 const location=await scalar("insert into locations(name) values('Synthetic room') returning id");
 const customer=await scalar("insert into customers(first_name,last_name,email) values('Synthetic','Customer','fixture@example.invalid') returning id");
 const course=async(family,duration=75,capacity=4)=>scalar('insert into courses(course_key,name,duration_minutes,max_students_default) values($1,$2,$3,$4) returning id',['fixture-'+family,'Synthetic '+family,duration,capacity]);
 const evidence=()=>({kind:'registration_confirmation',gmail_message_id:'synthetic-message',customer_email:'fixture@example.invalid',customer_name:'Synthetic Customer',source_course_name:'Synthetic class',source_location_label:'Synthetic room'});
 const place=(id,{start='2031-01-01T14:30:00Z',proof=evidence(),person=customer,room=location,workspace=null}={})=>scalar('select record_confirmed_intake($1,$2,$3,$4,$5,$6)',[id,room,person,start,proof,workspace]);
 return {db,scalar,location,customer,course,evidence,place};
}
async function calendar(db){
 let handler;const source=load('supabase/functions/landerware-calendar/index.ts').replace(/^import .*;\r?\n/gm,'');
 const context=vm.createContext({Date,Set,Map,JSON,TextEncoder,URL,Response,encodeURIComponent,
 Deno:{env:{get:k=>({LANDERWARE_ICAL_TOKEN:'synthetic-token',SUPABASE_SERVICE_ROLE_KEY:'synthetic-local-only',SUPABASE_URL:'https://fixture.invalid'})[k]},serve:f=>handler=f},
 fetch:async url=>{
  const u=new URL(url),table=u.pathname.split('/').at(-1);
  if(table==='landerware_sessions')return Response.json((await db.query('select * from landerware_sessions order by starts_at')).rows);
  assert.ok(['registrations','landerware_registrations'].includes(table));
  const field=table==='registrations'?'class_session_id':'session_id';
  const ids=u.searchParams.get(field).slice(4,-1).split(',');const statuses=u.searchParams.get('status').slice(4,-1).split(',');
  const rows=(await db.query(`select id,${field},status from ${table} order by id`)).rows.filter(r=>ids.includes(r[field])&&statuses.includes(r.status));
  const offset=Number(u.searchParams.get('offset')),limit=Number(u.searchParams.get('limit'));return Response.json(rows.slice(offset,offset+limit));
 }});
 vm.runInContext(stripTypeScriptTypes(source),context);
 const response=await handler(new Request('https://fixture.invalid/?token=synthetic-token'));assert.equal(response.status,200);return response.text();
}
test('confirmed minimum facts project every family with missing secondary details; unbooked proposals stay hidden',async()=>{
 const f=await fixture();try{
  const families=['BLS','ACLS','PALS','Heartsaver','ARC','HSI','USCG','FamilyCPR','SharedSkills'];
  for(let i=0;i<families.length;i++){
   const id=await f.course(families[i]);const result=await f.place(id,{start:`2031-01-${String(i+1).padStart(2,'0')}T14:30:00Z`,proof:{...f.evidence(),gmail_message_id:'synthetic-'+i}});
   assert.equal(result.scheduled,true);assert.ok(result.needs_attention.includes('instructor_assignment'));
  }
  await f.db.exec("insert into landerware_sessions(course_name,starts_at,lifecycle_state,provenance,requirements_manifest) values('UNBOOKED NEGATIVE','2031-01-20T14:00Z','pending_proposal','gmail_unmatched_intake','{\"customer_commitment\":false,\"starts_at_is_window_anchor_only\":true}')");
  assert.equal(await f.scalar('select count(*)::integer from class_sessions'),families.length);
  assert.equal(await f.scalar("select count(*)::integer from class_sessions where visibility='private' and registration_status='closed' and lead_instructor_id is null"),families.length);
  const body=await calendar(f.db);assert.equal(body.split('BEGIN:VEVENT').length-1,families.length);assert.doesNotMatch(body,/UNBOOKED NEGATIVE|fixture@example/);
  assert.match(body,/Instructor: Unassigned/);assert.match(body,/Students: 1/);
 }finally{await f.db.close();}
});
test('repeat message and distinct import evidence preserve one class/customer seat and source audit history',async()=>{
 const f=await fixture();try{
  const id=await f.course('duplicates');const first=await f.place(id);assert.deepEqual(await f.place(id),first);
  await f.place(id,{proof:{...f.evidence(),gmail_message_id:'synthetic-message-two'}});
  assert.equal(await f.scalar('select count(*)::integer from class_sessions'),1);assert.equal(await f.scalar('select count(*)::integer from registrations'),1);
  assert.equal(await f.scalar('select count(*)::integer from class_session_audit'),2);
  assert.equal(await f.scalar("select count(*)::integer from class_sessions where external_session_evidence->>'gmail_message_id'='synthetic-message'"),1);
  assert.equal(await f.scalar("select count(*)::integer from registrations where status='registered' and external_reconciliation_evidence->>'payment_status' is null"),1,'placing a booking never infers paid state');
 }finally{await f.db.close();}
});
test('missing secondary contact/material/instructor details do not hide a confirmed class',async()=>{
 const f=await fixture();try{
  const id=await f.course('missing-details');await f.db.query('update customers set email=null where id=$1',[f.customer]);
  const proof=f.evidence();delete proof.customer_email;
  const result=await f.place(id,{proof});assert.equal(result.scheduled,true);
  assert.ok(result.needs_attention.includes('instructor_assignment'));
  assert.match(await calendar(f.db),/SUMMARY:Synthetic missing-details/);
  assert.equal(await f.scalar('select material_choice from registrations'),null);
 }finally{await f.db.close();}
});
test('separate confirmed participants share the existing class; proposal documents and identity survive adoption',async()=>{
 const f=await fixture();try{
  const id=await f.course('adoption');
  const workspace=await f.scalar("insert into landerware_sessions(course_id,course_name,starts_at,lifecycle_state,provenance,requirements_manifest,document_ids) values('unresolved','Source class','2031-01-01T14:30Z','pending_proposal','gmail_unmatched_intake','{\"customer_email\":\"fixture@example.invalid\"}','[\"synthetic-document\"]') returning id");
  const first=await f.place(id,{workspace});assert.equal(first.workspace_id,workspace);
  assert.deepEqual(await f.scalar('select document_ids from landerware_sessions where id=$1',[workspace]),['synthetic-document']);
  const second=await f.scalar("insert into customers(first_name,last_name,email) values('Another','Synthetic','second@example.invalid') returning id");
  await f.place(id,{person:second,proof:{...f.evidence(),gmail_message_id:'synthetic-other',customer_name:'Another Synthetic',customer_email:'second@example.invalid'}});
  assert.equal(await f.scalar('select count(*)::integer from class_sessions'),1);assert.equal(await f.scalar('select count(*)::integer from registrations'),2);
  assert.match(await calendar(f.db),/Students: 2/);
  await assert.rejects(f.place(id,{start:'2031-01-02T14:30Z',workspace}),/workspace_identity_conflict/);
 }finally{await f.db.close();}
});
test('unknown source, missing core facts and unknown duration cannot create an operational booking',async()=>{
 const f=await fixture();try{
  const id=await f.course('negative');
  for(const patch of [{kind:'availability_request'},{kind:'proposal'},{gmail_message_id:''},{customer_email:'wrong@example.invalid'},{customer_name:''},{source_course_name:''},{source_location_label:''}])await assert.rejects(f.place(id,{proof:{...f.evidence(),...patch}}),/confirmed_booking_/);
  await assert.rejects(f.place(id,{start:null}),/confirmed_booking_source_required/);
  const unknown=await f.course('unknown-duration',null);await assert.rejects(f.place(unknown),/course_duration_rule_required/);
  assert.equal(await f.scalar('select count(*)::integer from class_sessions'),0);
 }finally{await f.db.close();}
});
test('cancellation/rescheduling and source-to-session identity survive repeated confirmed evidence',async()=>{
 const f=await fixture();try{
  const id=await f.course('lifecycle');const result=await f.place(id);
  for(const status of ['canceled','rescheduled']){
   await f.db.query('update registrations set status=$1',[status]);await f.place(id);assert.equal(await f.scalar('select status from registrations'),status);
  }
  await assert.rejects(f.place(id,{start:'2031-01-02T14:30Z'}),/source_booking_already_moved/);
  assert.equal(await f.scalar('select count(*)::integer from class_sessions'),1,'rejected replay rolls back its provisional class');
  await f.db.query("update class_sessions set status='canceled' where id=$1",[result.class_session_id]);
  await assert.rejects(f.place(id),/source_booking_already_moved/);
  assert.equal(await f.scalar('select count(*)::integer from class_sessions'),1);
 }finally{await f.db.close();}
});
