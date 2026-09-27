const test=require('node:test'), assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const {stripTypeScriptTypes}=require('node:module');
const root=require('node:path').resolve(__dirname,'..');
const shared=fs.readFileSync(root+'/supabase/functions/_shared/external-roster-proof.ts','utf8').replace(/export /g,'');
const owner=fs.readFileSync(root+'/supabase/functions/canonical-session-workspace/index.ts','utf8').replace(/^import .*;\r?\n/gm,'').replace(/export /g,'');
const context=vm.createContext({Date,Set,JSON,Deno:{serve(){},env:{get(){}}}});
vm.runInContext(stripTypeScriptTypes(shared+'\n'+owner)+'\nthis.api={registrationProof,summarizeSession};',context);
const api=context.api;
function row(){return {registration_backend:'enrollware',external_reconciliation:{complete:true,source_observed_at:new Date().toISOString(),active_external_registration_ids:['123'],active_registration_count:1},registrations:[{status:'registered',external_registration_id:'123',customers:{first_name:'Private',email:'private@example.test'}}]};}
test('complete source roster supplies a known canonical count and owner roster',()=>{const r=row();assert.equal(api.registrationProof(r).active_registration_count,1);assert.equal(api.summarizeSession(r).participants.length,1);});
test('stale source never becomes current because the endpoint was refreshed',()=>{const r=row();r.external_reconciliation.source_observed_at='2020-01-01T00:00:00Z';for(let i=0;i<2;i++){const p=api.summarizeSession(r);assert.equal(p.participant_count,null);assert.equal(p.participants.length,0);assert.equal(p.demand_status,'stale_reconciliation');}});
test('unknown, incomplete, mismatched and duplicate identities fail closed',()=>{for(const change of [r=>delete r.external_reconciliation,r=>r.external_reconciliation.complete=false,r=>r.registrations[0].external_registration_id='456',r=>r.external_reconciliation.active_external_registration_ids=['123','123'],r=>delete r.registrations]){const r=row();change(r);assert.equal(api.registrationProof(r).count_available,false);}});
test('last active registration removal requires a matching empty source roster',()=>{const r=row();r.registrations[0].status='canceled';assert.equal(api.registrationProof(r).active_registration_count,null);r.external_reconciliation.active_external_registration_ids=[];r.external_reconciliation.active_registration_count=0;assert.equal(api.registrationProof(r).active_registration_count,0);});
test('source timestamps in the future are not accepted',()=>{const r=row();r.external_reconciliation.source_observed_at=new Date(Date.now()+3600000).toISOString();assert.equal(api.registrationProof(r).count_available,false);});
