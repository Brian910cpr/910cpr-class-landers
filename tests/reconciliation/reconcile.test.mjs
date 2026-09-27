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
    const member={external_registration_id:'90001',first_name:'Fixture',last_name:'Person',email:'fixture@example.test',status:'Pending'};
    const one={...row,roster_count:1,registrations:[member]};
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
    assert.equal((await reconcile([{...deadline,start_at:'2030-09-28T13:00:00-04:00'}])).quarantined,1,'source identity change reopens review');
    assert.equal((await health()).sessions.find(s=>s.external_class_id==='80006').status,'missing_canonical_session');
    assert.equal((await db.query("select has_function_privilege('anon','enrollware_non_session_decision(jsonb)','execute') allowed")).rows[0].allowed,false);
    assert.equal((await reconcile([{...one,source_observed_at:'2020-01-01T00:00:00Z'}])).quarantined,1);
    assert.equal((await reconcile([{...one,registrations:[{...member,status:'mystery'}]}])).quarantined,1);
    assert.equal((await db.query("select count(*)::int n from registrations where status='registered'")).rows[0].n,0);
    await db.exec("update class_sessions set external_reconciliation=jsonb_set(external_reconciliation,'{source_observed_at}','\"2020-01-01T00:00:00Z\"')");
    assert.ok((await health()).unknown_sessions>0);
    assert.equal((await db.query("select has_function_privilege('anon','reconcile_enrollware_roster_batch(jsonb,text)','execute') allowed")).rows[0].allowed,false);
    console.log('Verified empty→registered→repeat→rescheduled→removed; exact IDs, stale/partial/unknown status, quarantine, private RPC');
  } finally {await db.close();}
});
