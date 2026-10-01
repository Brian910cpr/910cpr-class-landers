import {PGlite} from '@electric-sql/pglite';
import fs from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';

test('real PostgreSQL canonical reconciliation lifecycle, replay, quarantine and health', async () => {
  const db=new PGlite();
  try {
    await db.exec(fs.readFileSync(new URL('schema.sql',import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20260927034822_reconcile_operational_enrollware_rosters.sql',import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20260927040638_reconcile_verified_enrollware_legacy_sources.sql',import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20260927040949_invalidate_incomplete_roster_proof.sql',import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20260927041952_preserve_committed_external_location_identity.sql',import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20260927042118_retain_existing_operational_location_gate.sql',import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20260927050745_classify_confirmed_enrollware_deadlines.sql',import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20260927051624_retain_review_for_changed_deadline_sources.sql',import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20261001024838_canonical_scheduling_projection.sql',import.meta.url),'utf8'));
    await db.exec(fs.readFileSync(new URL('../../supabase/migrations/20261001032240_native_event_identity_health.sql',import.meta.url),'utf8'));
    await db.exec(`insert into courses(course_key,name) values('fixture-course','Fixture');
      insert into people(person_key,display_name) values('fixture-instructor','Fixture');
      insert into locations(location_key,name,scheduling_status) values('fixture-room','Fixture','active');`);
    const observed = new Date().toISOString();
    const row={external_class_id:'80001',committed:true,complete_roster:true,source_kind:'authenticated_enrollware_roster',
      source_url:'https://www.enrollware.com/admin/class-edit.aspx?id=80001',source_observed_at:observed,
      start_at:'2030-09-27T13:00:00-04:00',end_at:'2030-09-27T15:00:00-04:00',
      consumption_start_at:'2030-09-27T13:00:00-04:00',consumption_end_at:'2030-09-27T15:00:00-04:00',
      duration_basis:'fixture',course_key:'fixture-course',location_key:'fixture-room',instructor_key:'fixture-instructor',
      max_students:8,roster_count:0,registrations:[]};
    let n=0;
    const reconcile=async rows=>(await db.query('select reconcile_enrollware_roster_batch($1::jsonb,$2) result',
      [JSON.stringify(rows),(++n).toString(16).padStart(64,'0')])).rows[0].result;
    const health=async()=>(await db.query("select enrollware_reconciliation_health('2030-01-01','2031-01-01') result")).rows[0].result;
    const empty=await reconcile([row]);assert.equal(empty.reconciled,1,JSON.stringify(empty));
    const id=empty.sessions[0].session_id;
    const workspace=(await db.query('select * from landerware_sessions where class_session_id=$1',[id])).rows[0];
    assert.ok(workspace,'canonical session projects immediately');
    const member={external_registration_id:'90001',first_name:'Fixture',last_name:'Person',email:'fixture@example.test',status:'Pending'};
    const one={...row,roster_count:1,registrations:[member]};
    assert.equal((await reconcile([one])).reconciled,1);
    await db.query("update landerware_sessions set document_ids='[\"fixture-document\"]',requirements_manifest=requirements_manifest||'{\"workflow_note\":\"keep\"}' where id=$1",[workspace.id]);
    const rescheduled={...one,start_at:'2030-09-27T16:00:00-04:00',end_at:'2030-09-27T18:00:00-04:00',
      consumption_start_at:'2030-09-27T16:00:00-04:00',consumption_end_at:'2030-09-27T18:00:00-04:00'};
    assert.equal((await reconcile([rescheduled])).reconciled,1);
    const movedWorkspace=(await db.query('select * from landerware_sessions where class_session_id=$1',[id])).rows[0];
    assert.equal(movedWorkspace.id,workspace.id,'reschedule preserves workspace identity');
    assert.deepEqual(movedWorkspace.document_ids,['fixture-document']);
    assert.equal(movedWorkspace.requirements_manifest.workflow_note,'keep');
    assert.equal(new Date(movedWorkspace.starts_at).toISOString(),'2030-09-27T20:00:00.000Z');
    await assert.rejects(db.query("update landerware_sessions set starts_at=starts_at+interval '1 hour' where id=$1",[workspace.id]),/edit_schedule_in_class_sessions/);
    await db.query("update class_sessions set start_at=start_at+interval '1 minute' where id=$1",[id]);
    assert.deepEqual((await db.query('select external_reconciliation from class_sessions where id=$1',[id])).rows[0].external_reconciliation,{},'timing edit invalidates source proof');
    assert.equal((await reconcile([one])).reconciled,1);
    const identity=(await db.query('select id,customer_id from registrations')).rows[0];
    await db.exec("update registrations set registration_source='gmail_enrollware',external_reconciliation_evidence=external_reconciliation_evidence||'{\"previous_source_evidence\":true}'::jsonb");
    assert.equal((await reconcile([one])).sessions[0].session_id,id);
    assert.deepEqual((await db.query('select id,customer_id from registrations')).rows,[identity]);
    assert.equal((await db.query("select external_reconciliation_evidence->>'previous_source_evidence' kept from registrations")).rows[0].kept,'true');
    assert.equal((await health()).unknown_sessions,0);
    assert.equal((await reconcile([{...one,complete_roster:false}])).quarantined,1);
    assert.deepEqual((await db.query('select external_reconciliation from class_sessions')).rows[0].external_reconciliation,{});
    assert.equal((await reconcile([one])).reconciled,1);
    const moved={...one,external_class_id:'80002'};
    assert.equal((await reconcile([moved])).reconciled,1);
    assert.equal((await db.query('select id from registrations')).rows[0].id,identity.id);
    assert.equal((await health()).unknown_sessions,1,'former session becomes unknown after move');
    assert.equal((await reconcile([row])).reconciled,1);
    assert.equal((await reconcile([{...moved,roster_count:0,registrations:[]}])).reconciled,1);
    assert.equal((await db.query('select status from registrations')).rows[0].status,'canceled');
    assert.equal((await health()).unknown_sessions,0);
    assert.equal((await reconcile([{...one,external_class_id:'80003',complete_roster:false}])).quarantined,1);
    assert.equal((await health()).sessions.find(s=>s.external_class_id==='80003').status,'missing_canonical_session');
    assert.equal((await reconcile([{...row,external_class_id:'80004',location_key:'missing-location'}])).quarantined,1,'unknown identity still fails closed');
    await db.exec("update locations set scheduling_status='inactive'");
    assert.equal((await reconcile([{...row,external_class_id:'80005'}])).quarantined,1,'inactive locations preserve the existing authority gate');
    assert.equal((await db.query('select scheduling_status from locations')).rows[0].scheduling_status,'inactive','reconciliation never enables new scheduling');
    await db.exec("update locations set scheduling_status='active'");
    const deadline={...one,external_class_id:'80006',location_key:'unapproved',external_course_id:'410205',
      external_location_id:'109182',source_end_time:'',source_hours:'2'};
    assert.equal((await reconcile([deadline])).quarantined,1);
    const sourceIdentity=Object.fromEntries(['external_class_id','external_course_id','external_location_id','start_at','source_end_time','source_hours'].map(k=>[k,deadline[k]]));
    const decision={owner_confirmed:true,classification:'renewal_deadline',approved_location_key:'fixture-room',source_identity:sourceIdentity};
    await db.query(`update ingest_review_queue set status='resolved',decided_at=now(),decision=$1::jsonb
      where ingest_fact_id in (select id from ingest_facts where source_locator->>'external_class_id'='80006')`,[JSON.stringify(decision)]);
    const classified=await reconcile([deadline]);
    assert.equal(classified.classified_non_sessions,1);
    assert.equal(classified.reconciled,0);
    assert.equal((await db.query("select count(*)::int n from class_sessions where external_class_id='80006'")).rows[0].n,0);
    assert.equal((await db.query("select proposed_value->'registrations' members from ingest_facts where resolution='classified_non_session'")).rows[0].members.length,1,'private source evidence retained');
    assert.equal((await health()).sessions.find(s=>s.external_class_id==='80006').status,'classified_non_session');
    assert.ok(!JSON.stringify(await health()).includes('fixture@example.test'),'no participant PII in health projection');
    assert.equal((await reconcile([deadline])).classified_non_sessions,1,'classification survives replay');
    const changedDeadline=await reconcile([{...deadline,location_key:'fixture-room',external_location_id:'new-active-location'}]);
    assert.equal(changedDeadline.quarantined,1,'source identity change reopens review even when its new location is active');
    assert.equal(changedDeadline.sessions[0].reason,'non_session_source_changed_requires_review');
    assert.equal((await health()).sessions.find(s=>s.external_class_id==='80006').status,'missing_canonical_session');
    assert.equal((await db.query("select has_function_privilege('anon','enrollware_non_session_decision(jsonb)','execute') allowed")).rows[0].allowed,false);
    assert.equal((await reconcile([{...one,source_observed_at:'2020-01-01T00:00:00Z'}])).quarantined,1);
    assert.equal((await reconcile([{...one,registrations:[{...member,status:'mystery'}]}])).quarantined,1);
    assert.equal((await db.query("select count(*)::int n from registrations where status='registered'")).rows[0].n,0);
    await db.exec("update class_sessions set external_reconciliation=jsonb_set(external_reconciliation,'{source_observed_at}','\"2020-01-01T00:00:00Z\"')");
    assert.ok((await health()).unknown_sessions>0);
    assert.equal((await db.query("select has_function_privilege('anon','reconcile_enrollware_roster_batch(jsonb,text)','execute') allowed")).rows[0].allowed,false);
    const native=await reconcile([{...row,external_class_id:'80007'}]);
    const nativeId=native.sessions[0].session_id;
    await db.query("update class_sessions set source='landerware_public_offer',registration_backend='landerware',visibility='public',registration_status='open' where id=$1",[nativeId]);
    const nativeCustomer=(await db.query("insert into customers(first_name,last_name,email) values('Native','Person','native@example.test') returning id")).rows[0].id;
    const nativeReg=(await db.query("insert into registrations(customer_id,class_session_id,status,registration_source) values($1,$2,'registered','landerware') returning id",[nativeCustomer,nativeId])).rows[0].id;
    const mixed=await reconcile([{...row,external_class_id:'80007',roster_count:2,registrations:[
      {...member,external_registration_id:'90007',email:'external1@example.test'},
      {...member,external_registration_id:'90008',email:'external2@example.test'}]}]);
    assert.equal(mixed.reconciled,1,JSON.stringify(mixed));
    const mixedState=(await db.query('select registration_backend,visibility,registration_status from class_sessions where id=$1',[nativeId])).rows[0];
    assert.deepEqual(mixedState,{registration_backend:'landerware',visibility:'public',registration_status:'open'});
    assert.equal((await db.query("select count(*)::int n from registrations where class_session_id=$1 and status='registered'",[nativeId])).rows[0].n,3);
    assert.equal((await reconcile([{...row,external_class_id:'80007'}])).reconciled,1);
    assert.equal((await db.query('select status from registrations where id=$1',[nativeReg])).rows[0].status,'registered','complete external absence preserves native seat');
    const proposal=(await db.query("insert into landerware_sessions(external_session_id,course_id,course_name,starts_at,lifecycle_state,provenance,requirements_manifest,document_ids) values('proposed:gmail:test','proposal-course','Fixture',$1,'pending_proposal','gmail_webhook_capture','{}','[\"proposal-document\"]') returning id",[row.start_at])).rows[0].id;
    const adopted=await reconcile([{...row,external_class_id:'80008',reconciles_workspace_id:proposal,workspace_link_basis:'verified_owner_request_and_current_roster'}]);
    assert.equal(adopted.reconciled,1,JSON.stringify(adopted));
    const linked=(await db.query('select * from landerware_sessions where id=$1',[proposal])).rows[0];
    assert.equal(linked.class_session_id,adopted.sessions[0].session_id);
    assert.equal(linked.lifecycle_state,'scheduled');
    assert.deepEqual(linked.document_ids,['proposal-document']);
    assert.equal(linked.requirements_manifest.proposal_before_reconciliation.external_session_id,'proposed:gmail:test');
    await db.query("update class_sessions set external_class_id=null,source='gmail_customer_request',visibility='private',registration_status='closed' where id=$1",[nativeId]);
    assert.equal((await db.query('select count(*)::int n from landerware_sessions where class_session_id=$1',[nativeId])).rows[0].n,1,'private manual commitment stays projected');
    await db.query("update class_sessions set external_class_id='native-event-2030',source='landerware_event' where id=$1",[nativeId]);
    assert.equal((await health()).sessions.some(s=>s.external_class_id==='native-event-2030'),false,'native event slug is outside Enrollware namespace');
    console.log('Verified lifecycle, preserved workspace/documents, mixed native/external seats, proposal adoption, private commitments, quarantine and service-only access');
  } finally {await db.close();}
});
