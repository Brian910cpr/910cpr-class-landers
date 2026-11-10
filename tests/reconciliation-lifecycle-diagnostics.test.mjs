import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
const root=new URL('../',import.meta.url),load=p=>readFileSync(new URL(p,root),'utf8');
const migration=readdirSync(new URL('supabase/migrations/',root)).find(p=>p.endsWith('_reconciliation_lifecycle_diagnostics.sql'));
test('health SQL diagnostics preserve every assessment and count across native/external/unknown active and canceled lifecycles',async()=>{
 const db=new PGlite();try{
 await db.exec(`create table ingest_facts(id int,created_at timestamptz,fact_type text,source_locator jsonb,proposed_value jsonb,resolution text,resolution_reason text);
 create table class_sessions(id text,external_class_id text,record_scope text,start_at timestamptz,status text,registration_backend text,source text,external_session_evidence jsonb,external_reconciliation jsonb);
 create table registrations(class_session_id text,status text,external_registration_id text,registration_source text);
 create function enrollware_non_session_decision(jsonb) returns jsonb language sql as 'select null::jsonb';`);
 const fixtures=[
 ['n1','lw-gmail:0123456789abcdef','scheduled','enrollware','manual',{source:'gmail_registration_reconciliation',verified_assignment:true,gmail_message_id:'0123456789abcdef'},{}],
 ['n2','lw-gmail:1123456789abcdef','canceled','manual','manual',{source:'gmail_registration_reconciliation',verified_assignment:true,gmail_message_id:'1123456789abcdef'},{}],
 ['e1','100','scheduled','enrollware','enrollware',{},{}],
 ['e2','101','canceled','enrollware','enrollware',{},{}],
 ['u1','lw-gmail:2123456789abcdef','canceled','manual','manual',{},{}],
 ['u2','lw-gmail:3123456789abcdef','active','manual','manual',{verified_assignment:true},{}],
 ['s1','102','scheduled','enrollware','enrollware',{}, {complete:true,source_observed_at:'2000-01-01T00:00:00Z',active_external_registration_ids:[]}],
 ['n3','lw-12345678-1234-1234-1234-123456789abc','active','landerware','landerware_public_offer',{},{}],
 ];
 for(const f of fixtures)await db.query(`insert into class_sessions values($1,$2,'operational','2030-01-01',$3,$4,$5,$6,$7)`,f);
 const run=async()=> (await db.query("select enrollware_reconciliation_health('2029-01-01','2031-01-01') h")).rows[0].h;
 await db.exec(load('supabase/migrations/20261029101101_canonical_roster_ownership.sql'));
 const before=await run();
 await db.exec(load('supabase/migrations/'+migration));const after=await run();
 const strip=h=>({...h,checked_at:null,sessions:h.sessions.map(({lifecycle_status,ownership_classification,ownership_basis,...rest})=>rest)});
 assert.deepEqual(strip(after),strip(before));
 const rows=Object.fromEntries(after.sessions.map(s=>[s.canonical_session_id,s]));
 for(const id of ['n1','n2','n3'])assert.equal(rows[id].ownership_classification,'native');
 for(const id of ['e1','e2','s1'])assert.equal(rows[id].ownership_classification,'external');
 for(const id of ['u1','u2'])assert.equal(rows[id].ownership_classification,'unknown');
 assert.equal(rows.u1.status,'external_reconciliation_required');assert.equal(rows.e2.status,'external_reconciliation_required');assert.equal(rows.s1.status,'stale_reconciliation');
 assert.equal(rows.n2.lifecycle_status,'canceled');assert.equal(rows.u2.lifecycle_status,'active');
 assert.equal(JSON.stringify(after).includes('verified_assignment'),false);
 assert.equal(JSON.stringify(after).includes('gmail_message_id'),false);
 }finally{await db.close();}
});
