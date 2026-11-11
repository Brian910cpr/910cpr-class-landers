import test from 'node:test';
import assert from 'node:assert/strict';
import {setupSkillsLease,proveBasics,makeOffer,request,claim,scalar,footprint,migration} from './native-skills-offer-lease-proof.mjs';
for(const full of [false,true])test('shared-skills wall-clock guard composes with '+(full?'optional full-course scopes':'BLS-only chain'),async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  const fixture=await setupSkillsLease(db,{full});await proveBasics(db,fixture);
  const offer=await makeOffer(db,'arc-blended',70,{leaseMs:250});
  const before=await footprint(db);await db.exec('begin');
  assert.ok(await scalar(db,'select skills_session_native_option($1,$2::jsonb)',['arc-blended',JSON.stringify(offer)]));
  await new Promise(r=>setTimeout(r,300));
  await assert.rejects(claim(db,request('arc-blended',offer,4500)),/session_not_available/);await db.exec('rollback');
  assert.deepEqual(await footprint(db),before,'transaction-start now cannot admit expired lease');
 }finally{await db.close();}
});
test('native freshness/lead contract is scoped and clocks are not renewed',()=>{
 assert.match(migration,/authority' in \('native-skills-publication.v1','native-skills-seated.v1'\)/);
 assert.match(migration,/startsAt'\)::timestamptz<checked_at\+interval '24 hours'/);
 assert.match(migration,/startsAt'\)::timestamptz<=checked_at/);
 assert.match(migration,/generatedAt'\)::timestamptz<checked_at-interval '30 minutes'/);
 assert.doesNotMatch(migration,/jsonb_set|update public\.|insert into public\./i);
});
test('isolated clock injection exercises native lead and legacy freshness/start boundaries',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await setupSkillsLease(db);
  const original=await scalar(db,"select pg_get_functiondef('materialize_native_skills_checkout(text,jsonb,text)'::regprocedure)");
  assert.equal(original.split('clock_timestamp()').length,2);
  async function check(offer,checkedAt,n,accept){
   const before=await footprint(db);await db.exec('begin');
   // Only this disposable test body gets a controllable post-lock clock; the
   // production migration and all option predicates remain byte-for-byte intact.
   await db.exec(original.replace('clock_timestamp()',`'${new Date(checkedAt).toISOString()}'::timestamptz`));
   assert.ok(await scalar(db,'select skills_session_native_option($1,$2::jsonb)',['cpr-aed',JSON.stringify(offer)]),'initial predicate must admit the fixture');
   if(accept)assert.equal((await claim(db,request('cpr-aed',offer,n))).status,'held');
   else await assert.rejects(claim(db,request('cpr-aed',offer,n)),/session_not_available/);
   await db.exec('rollback');assert.deepEqual(await footprint(db),before);
  }
  // Avoid creating a valid-input fixture in the last second before a quarter
  // hour, where setup latency alone could cross the initial lead boundary.
  const untilQuarter=900000-Date.now()%900000;
  if(untilQuarter<1000)await new Promise(r=>setTimeout(r,untilQuarter+20));
  const native=await makeOffer(db,'cpr-aed',1);
  const generated=Date.parse(native.generatedAt),start=Math.ceil((generated+86400000)/900000)*900000;
  native.startsAt=new Date(start).toISOString();native.endsAt=new Date(start+45*60000).toISOString();native.consumptionEndsAt=new Date(start+60*60000).toISOString();
  native.localStart=await scalar(db,"select to_char($1::timestamptz at time zone 'America/New_York','YYYY-MM-DD\"T\"HH24:MI')",[native.startsAt]);
  native.validUntil=new Date(generated+900000).toISOString();
  assert.ok(start-86400000+1<Date.parse(native.validUntil));
  await check(native,start-86400000,4600,true);await check(native,start-86400000+1,4601,false);
  const legacy=await makeOffer(db,'cpr-aed',5,{legacy:true});
  legacy.generatedAt=new Date(Date.now()-1800000+10000).toISOString();
  await check(legacy,Date.parse(legacy.generatedAt)+1800000,4610,true);
  await check(legacy,Date.parse(legacy.generatedAt)+1800001,4611,false);
  const near=await makeOffer(db,'cpr-aed',0,{legacy:true});
  near.startsAt=new Date(Date.now()+10000).toISOString();near.endsAt=new Date(Date.parse(near.startsAt)+45*60000).toISOString();near.consumptionEndsAt=new Date(Date.parse(near.startsAt)+60*60000).toISOString();
  near.localStart=await scalar(db,"select to_char($1::timestamptz at time zone 'America/New_York','YYYY-MM-DD\"T\"HH24:MI')",[near.startsAt]);
  await check(near,Date.parse(near.startsAt)-1,4620,true);await check(near,Date.parse(near.startsAt),4621,false);
 }finally{await db.close();}
});
