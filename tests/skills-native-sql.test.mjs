import {readFileSync,readdirSync} from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {skillsOffers} from '../supabase/functions/skills-session-reservation/policy.mjs';
import {createHandler} from '../supabase/functions/skills-session-reservation/handler.mjs';
const require=createRequire(import.meta.url);
const {loadEndpoint}=require('./helpers/canonical_demand_endpoint.cjs');
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
const root=new URL('../',import.meta.url);
const load=name=>readFileSync(new URL(name,root),'utf8');
test('actual PostgreSQL transaction: default-off, canonical claim, capacity, rollback, cleanup and idempotency',async()=>{
  const db=new PGlite();
  try{
    await db.exec(load('tests/helpers/reschedule-production-schema.sql'));
    for(const name of ['20261019175346_registration_self_service_rescheduling.sql','20261019175522_reschedule_confirmation_provider.sql','20261019225039_registration_reschedule_dynamic_offers.sql'])
      await db.exec(load('supabase/migrations/'+name));
    const migration=readdirSync(new URL('supabase/migrations/',root)).find(name=>name.endsWith('_skills_session_native_claim.sql'));
    await db.exec(load('supabase/migrations/'+migration));
    const query=async(sql,args=[])=> (await db.query(sql,args)).rows;
    const scalar=async(sql,args=[])=>Object.values((await query(sql,args))[0])[0];
    const ids=await query(`insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price)
      values('fixture-skills','Fixture Skills','509474',45,15,2,55),('fixture-aha','Fixture AHA','fixture-aha',45,15,2,55),('fixture-arc','Fixture ARC','fixture-arc',45,15,2,55) returning id,course_key`);
    const cid=Object.fromEntries(ids.map(x=>[x.course_key,x.id]));
    const person=await scalar("insert into people(person_key,display_name) values('fixture','Fixture Instructor') returning id");
    await db.exec("insert into locations(location_key,name,scheduling_status) values('910cpr-office-shipyard',':: Wilmington; Shipyard Blvd','active')");
    let now=Date.now();
    const offer={kind:'dynamic',offerType:'dynamic_appointment',context:'cpr-aed',courseNumber:'509474',selectionId:'skills:fixture',
      startsAt:'2031-04-05T14:00:00Z',endsAt:'2031-04-05T14:45:00Z',consumptionEndsAt:'2031-04-05T15:00:00Z',localStart:'2031-04-05T10:00',
      instructor:'Fixture Instructor',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',
      availabilityBlockId:'fixture-proof',sourceSessionIds:[],generatedAt:new Date(now).toISOString(),validUntil:new Date(now+60000).toISOString()};
    const student={firstName:'Fixture',lastName:'Student',email:'fixture@example.invalid',onlineCompleted:true};
    const key=n=>`11111111-1111-4111-8111-${String(n).padStart(12,'0')}`;
    const option=(o=offer,context='cpr-aed')=>scalar('select public.skills_session_native_option($1,$2::jsonb)',[context,JSON.stringify(o)]);
    const reserve=(n,o=offer,s=student,context='cpr-aed')=>scalar('select public.reserve_skills_session_native($1,$2,$3::jsonb,$4::jsonb)',[key(n),context,JSON.stringify(o),JSON.stringify(s)]);
    assert.equal(await option(),null,'no context enabled by migration');
    await query(`insert into skills_session_context_config values('cpr-aed',$1,$2,true,true,'EXPLICIT TEST FIXTURE ONLY')`,[cid['fixture-skills'],cid['fixture-aha']]);
    assert.equal(await option(),null,'no positive qualification');
    await query("insert into instructor_qualifications(instructor_id,course_id,status) values($1,$2,'active')",[person,cid['fixture-aha']]);
    assert.ok(await option());
    const publication={schemaVersion:'selector-resolved-availability.v1',pageKey:'heartsaver',generatedAt:offer.generatedAt,validUntil:offer.validUntil,
      dates:[{date:'2031-04-05',startTimes:[{startTime:'10:00',courses:[{courseId:'509474',offerType:'dynamic_appointment',publicSelectable:true,
        durationMinutes:45,schedulerConsumptionMinutes:60,cleanupBufferMinutes:15,occupiedUntil:offer.consumptionEndsAt,
        instructor:offer.instructor,resource:offer.resource,location:offer.location,availabilityBlockId:offer.availabilityBlockId,
        sourceSessionIds:[],validUntil:offer.validUntil}]}]}]};
    const selected=skillsOffers(publication,'cpr-aed',now)[0];offer.selectionId=selected.selectionId;
    const handler=createHandler({enabled:()=>true,now:()=>now,publication:async()=>publication,rpc:async(name,args)=>{
      if(name==='skills_session_native_option')return option(args.p_offer,args.p_context);
      assert.equal(name,'reserve_skills_session_native');
      return scalar('select public.reserve_skills_session_native($1,$2,$3::jsonb,$4::jsonb)',[args.p_idempotency_key,args.p_context,JSON.stringify(args.p_offer),JSON.stringify(args.p_student)]);
    }});
    const choices=await handler(new Request('https://fixture/choices',{method:'POST',body:JSON.stringify({context:'cpr-aed',selection:{localStart:selected.localStart,instructor:selected.instructor,location:selected.location}})}));
    assert.equal((await choices.json()).offers.length,1);assert.equal(await scalar('select count(*)::int from class_sessions'),0,'listing is read-only');
    const response=await handler(new Request('https://fixture/reserve',{method:'POST',headers:{'idempotency-key':key(1),'content-type':'application/json'},
      body:JSON.stringify({context:'cpr-aed',selectionId:selected.selectionId,student,amountCents:0,startsAt:'attacker-controlled'})}));
    assert.equal(response.status,200);const first=await response.json();assert.equal(first.status,'reserved');assert.equal(first.amountCents,5500);assert.equal(first.paymentStatus,'pending');
    const replay=await reserve(1,{selectionId:offer.selectionId});assert.equal(replay.registrationId,first.registrationId);assert.equal(replay.idempotentReplay,true);
    assert.equal(await scalar('select count(*)::int from registrations'),1);
    assert.equal(await scalar('select count(*)::int from participant_lifecycle_events'),1,'replay has one durable lifecycle event');
    assert.equal(await scalar('select total_amount from registration_orders'), '55.00');
    assert.equal(await scalar('select count(*)::int from landerware_messages'),0,'no email sent or queued');
    await assert.rejects(()=>reserve(1,offer,{...student,lastName:'Changed'}),/idempotency_conflict/);
    await assert.rejects(()=>reserve(2,{...offer,validUntil:new Date(now-1).toISOString()}),/session_not_available/);
    await assert.rejects(()=>reserve(2,{...offer,context:'arc-blended'},student,'arc-blended'),/session_not_available/);
    const source=await scalar('select external_class_id from class_sessions where id=$1',[first.sessionId]);
    const hold=await scalar(`insert into landerware_public_orders(external_class_id,class_session_id,course_id,payer_email,idempotency_key,hold_expires_at)
      values($1,$2,'509474','hold@example.invalid','fixture-hold',now()+interval '5 minutes') returning id`,[source,first.sessionId]);
    await query(`insert into landerware_public_order_students(order_id,first_name,last_name,email,phone,unit_amount)
      values($1,'Fixture','Held','hold@example.invalid','',5500)`,[hold]);
    assert.equal(await option(),null,'an active checkout hold consumes the remaining seat');
    await query("update landerware_public_orders set hold_expires_at=now()-interval '1 second' where id=$1",[hold]);
    assert.ok(await option(),'expired holds do not consume a seat');
    const row=await scalar(`select to_jsonb(s)||jsonb_build_object('courses',(select jsonb_build_object('course_key',course_key,'name',name) from courses where id=s.course_id),
      'landerware_sessions',(select jsonb_agg(w) from landerware_sessions w where w.class_session_id=s.id),
      'registrations',(select jsonb_agg(r) from registrations r where r.class_session_id=s.id)) from class_sessions s where id=$1`,[first.sessionId]);
    const projected=loadEndpoint(()=>{throw Error('network forbidden')}).projectDemand(row);
    assert.equal(projected.count_available,true);assert.equal(projected.active_registration_count,1);assert.equal(projected.workspace_projection_status,'current');assert.equal(projected.external_course_id,'509474');
    const pipeline=`import sys,json\nfrom pathlib import Path\nfrom unittest.mock import patch\nfrom scripts.canonical_scheduling_demand import resolve_canonical_demand\nfrom scripts import block_start_time_selector as s\nfrom scripts.build_bls_block_schedule_pilot import public_selector_availability_payload\np=json.load(sys.stdin);rows,audit=resolve_canonical_demand([], [p]);assert len(rows)==1\nrules=s.course_rules_by_id(json.loads(Path('data/inventory/course_consumption_rules.json').read_text()));catalog=s.courses_by_id(json.loads(Path('data/config/course_catalog.json').read_text()));page=s.load_block_schedule_page_configs()['heartsaver'];opt=next(o for o in page['course_options'] if o['course_id']=='509474');course=s.contextual_course('509474',opt,catalog,rules)\nwith patch.object(s,'native_reservation_reasons',lambda c:[]):\n offers=s.seated_class_selector_offers(schedule_future_payload={'sessions':rows},selected_courses=[course],selected_course_ids={'509474'},course_rules=rules)\nassert len(offers)==1\no=offers[0];payload={'generatedAt':sys.argv[1],'validUntil':sys.argv[1],'pageKey':'heartsaver','dates':[{'date':o['date'],'startTimes':[{'startTime':o['startTime'],'courses':offers}]}]}\nprint(json.dumps(public_selector_availability_payload(payload)))`;
    const published=spawnSync(process.env.SKILLS_TEST_PYTHON||'python',['-B','-c',pipeline,new Date(now).toISOString()],{cwd:fileURLToPath(root),input:JSON.stringify(projected),encoding:'utf8',timeout:30000,windowsHide:true});
    assert.equal(published.status,0,published.stderr||String(published.error));
    const seated=skillsOffers(JSON.parse(published.stdout),'cpr-aed',now)[0];assert.ok(seated,published.stdout);assert.equal(seated.sourceSessionId,source);
    assert.equal(await option({...seated,sourceSessionId:'forged'}),null,'existing seats require the exact canonical source');
    const second=await reserve(2,seated,{...student,email:'second@example.invalid'});
    assert.equal(second.sessionId,first.sessionId,'existing skills seats reuse the same canonical session');
    await assert.rejects(()=>reserve(3,offer,{...student,email:'third@example.invalid'}),/session_not_available/);
    assert.equal(await scalar('select count(*)::int from customers'),2,'failed claim left no customer');
    assert.equal(await scalar('select count(*)::int from skills_session_claim_receipts'),2);
    await query(`insert into skills_session_context_config values('arc-blended',$1,$2,true,true,'EXPLICIT SHARED-POOL TEST FIXTURE ONLY')`,[cid['fixture-skills'],cid['fixture-arc']]);
    await query("insert into instructor_qualifications(instructor_id,course_id,status) values($1,$2,'active')",[person,cid['fixture-arc']]);
    await assert.rejects(()=>reserve(3,{...offer,context:'arc-blended',selectionId:'skills:arc-same-pool'},student,'arc-blended'),/session_not_available/,'a different context does not create another capacity pool');
    assert.equal(await scalar("select extract(epoch from (consumption_end_at-end_at))::int from class_sessions where id=$1",[first.sessionId]),900);
    const edge={...offer,selectionId:'skills:cleanup-overlap',startsAt:'2031-04-05T14:45:00Z',endsAt:'2031-04-05T15:30:00Z',consumptionEndsAt:'2031-04-05T15:45:00Z',localStart:'2031-04-05T10:45'};
    await assert.rejects(()=>reserve(4,edge),/session_not_available/);
    const later={...offer,selectionId:'skills:later',startsAt:'2031-04-05T15:00:00Z',endsAt:'2031-04-05T15:45:00Z',consumptionEndsAt:'2031-04-05T16:00:00Z',localStart:'2031-04-05T11:00'};
    await db.exec("create function public.fixture_reject_order() returns trigger language plpgsql as $$ begin raise exception 'fixture_order_failure'; end $$; create trigger fixture_fail before insert on registration_orders for each row execute function public.fixture_reject_order();");
    await assert.rejects(()=>reserve(4,later),/fixture_order_failure/);
    assert.equal(await scalar('select count(*)::int from class_sessions'),1,'late failure rolled back materialization');
    assert.equal(await scalar('select count(*)::int from customers'),2);
    await db.exec('drop trigger fixture_fail on registration_orders');
    await reserve(4,later);
    const newDay={...offer,selectionId:'skills:new-day',startsAt:'2031-04-06T14:00:00Z',endsAt:'2031-04-06T14:45:00Z',consumptionEndsAt:'2031-04-06T15:00:00Z',localStart:'2031-04-06T10:00'};
    await query("update courses set max_students_default=null where id=$1",[cid['fixture-skills']]);
    assert.equal(await option(newDay),null,'missing actual native capacity never inherits template capacity');
    await query("update courses set max_students_default=2 where id=$1",[cid['fixture-skills']]);
    assert.ok(await option(newDay));
    assert.equal(await option({...newDay,offerType:'seated_class',sourceSessionId:'deleted-source'}),null,'missing existing class is never rematerialized as a seated offer');
    await db.exec(`create or replace function public.public_registration_closure_policy() returns jsonb language sql immutable as $$select '{"closures":[{"startsAt":"2031-04-06T14:00:00Z","endsAt":"2031-04-06T16:00:00Z"}]}'::jsonb$$;`);
    assert.equal(await option(newDay),null,'closure after publication is honored');
    await query("update instructor_qualifications set status='revoked' where instructor_id=$1",[person]);
    assert.equal(await option({...later,selectionId:'skills:revoked'}),null);
    assert.equal(await scalar("select has_function_privilege('anon','public.reserve_skills_session_native(text,text,jsonb,jsonb)','execute')"),false);
    assert.equal(await scalar("select bool_and(relrowsecurity) from pg_class where oid in ('public.skills_session_context_config'::regclass,'public.skills_session_claim_receipts'::regclass)"),true);
    assert.equal(await scalar("select has_table_privilege('anon','public.skills_session_claim_receipts','select')"),false);
    assert.equal(await scalar('select count(*)::int from skills_session_context_config where enabled'),2,'only explicit test configs exist');
    await query("update registrations set status='canceled' where id=$1",[first.registrationId]);
    await assert.rejects(()=>reserve(1,{selectionId:offer.selectionId}),/session_not_available/,'canceled reservation cannot replay as confirmed');
  } finally {await db.close();}
});
