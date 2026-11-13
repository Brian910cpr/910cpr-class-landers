// Fresh, isolated loopback PostgreSQL17 only. Synthetic data, no hosted URLs or sends.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
import {proveCombinedCheckout} from './combined-checkout-proof.mjs';
const database='skills_claim_test_991113',psql=localPsql(database);
const quote=v=>v==null?'null':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
function run(sql){return new Promise((resolve,reject)=>{const p=spawn(psql.command,psql.args,{env:psql.env,stdio:['pipe','pipe','pipe']});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('error',reject);p.on('close',code=>code===0?resolve(out.trim()):reject(Error(err)));p.stdin.end(sql);});}
let role=null;
const prefix=()=>role?`set role ${role};`:'';
const db={exec:async sql=>{
 if(/^set role service_role;?$/i.test(sql.trim())){role='service_role';return '';}
 if(/^reset role;?$/i.test(sql.trim())){role=null;return '';}
 return run(prefix()+sql);
},query:async(sql,args)=>{const s=bind(sql,args).trim().replace(/;$/,'');const query=/^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s;
 const out=await run(prefix()+query);return {rows:out?out.split('\n').filter(v=>v.startsWith('{')).map(v=>JSON.parse(v)):[]};}};
const server=(await db.query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
assertLocalTargetServer(server,database);await assertIsolatedPostgresServerAddress(server.address,{args:psql.args,env:psql.env,port:Number(process.env.SKILLS_TEST_PORT||5432),database});
assert.equal(await run("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';"),'0');
assert.equal(await run("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema');"),'0');

await proveCombinedCheckout(db,async({items,saved,scalar})=>{
 const key=n=>`99111300-0000-4000-8000-${String(n).padStart(12,'0')}`;
 const request=n=>items.map(item=>({...item,students:item.students.map(st=>({...st,email:`race-${n}@example.invalid`})),inputs:item.inputs.map(input=>({...input,wire:{...input.wire,email:`race-${n}@example.invalid`},submitted:{...input.submitted,fields:{...input.submitted.fields,email:`race-${n}@example.invalid`}}}))}));
 const claim=n=>run(`select reserve_native_checkout_basket(${quote(key(n))}::uuid,${quote(JSON.stringify(request(n)))}::jsonb);`).then(out=>({accepted:true,receipt:JSON.parse(out.split('\n').at(-1))}),e=>({accepted:false,error:e.message}));
 const results=await Promise.all([claim(1),claim(2)]);assert.equal(results.filter(x=>x.accepted).length,1);assert.match(results.find(x=>!x.accepted).error,/insufficient_seats/);
 const winner=results.find(x=>x.accepted).receipt,n=results[0].accepted?1:2;
 assert.equal(await scalar('select count(*) from native_checkout_baskets'),2,'losing basket, child orders and holds roll back');
 const replays=await Promise.all([claim(n),claim(n)]);assert.ok(replays.every(x=>x.accepted&&x.receipt.basketId===winner.basketId));
 assert.equal(await scalar('select count(*) from landerware_public_orders'),4);
 const evidence={id:'cs_race_basket',mode:'payment',payment_status:'paid',amount_total:winner.amountCents,currency:'usd',metadata:{landerware_basket_id:winner.basketId},livemode:false};
 await db.query('update native_checkout_baskets set stripe_checkout_session_id=$1 where id=$2',[evidence.id,winner.basketId]);
 await db.query('select native_checkout_basket_record_payment($1,$2,$3::jsonb)',[winner.basketId,'pi_race_basket',JSON.stringify(evidence)]);
 await db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 minute' where id in(select order_id from native_checkout_basket_items where basket_id=$1)",[winner.basketId]);
 const blocked=await claim(3);assert.equal(blocked.accepted,false);assert.match(blocked.error,/insufficient_seats/,'paid-unfinalized holds stay occupied after expiry');
 const finalize=()=>run(`select native_checkout_basket_finalize(${quote(winner.basketId)}::uuid,'pi_race_basket',${quote(JSON.stringify(evidence))}::jsonb);`).then(out=>JSON.parse(out.split('\n').at(-1)));
 const finals=await Promise.all([finalize(),finalize()]);assert.ok(finals.every(x=>x.status==='paid'));assert.equal(await scalar("select count(*) from registrations where registration_source='landerware_native_checkout'"),4);
 console.log('PASS independent basket seat contention, losing-transaction rollback, nonce replay, paid hold expiry protection and concurrent finalization');
 await db.exec(`insert into landerware_registration_profiles select (jsonb_populate_record(null::landerware_registration_profiles,to_jsonb(p)||'{"profile_key":"fixture_pals","course_id":"fixture-pals","active":true}')).* from landerware_registration_profiles p where profile_key='native_bls_initial';
  insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price,registration_profile_key) values('fixture-pals','Fixture PALS','209805',240,0,2,275,'fixture_pals');
  update landerware_registration_catalog set active=true,unit_amount=27500 where course_id='209805';
  insert into instructor_qualifications(instructor_id,course_id,status,expires_at) select p.id,c.id,'active',now()+interval '1 year' from people p cross join courses c where p.person_key='skills-test' and c.course_key='fixture-pals';
  update native_advanced_course_policy p set course_id=(select id from courses where course_key='fixture-pals'),profile_key='fixture_pals',setup_minutes=0,cleanup_minutes=0,max_students=2,location_id=a.location_id,resource_label=a.resource_label,location_label=a.location_label,enabled=true,publication_enabled=true,verified=true,evidence=a.evidence from native_advanced_course_policy a where p.course_number='209805' and a.course_number='241108';
  insert into native_advanced_instructor_scopes select '209805',instructor_id,availability_person_id,calendar_source_keys,verified,evidence from native_advanced_instructor_scopes where course_number='241108';`);
 const offers={};
 for(const course of ['241108','209805'])offers[course]=await scalar(`select (skills_test.offer('advanced-race',20)-'context'-'offerType')||jsonb_build_object('authority','native-full-course.v3','nativeScopeId','qualified-advanced-shipyard-b.v1','coursePolicyKey','advanced-full:'||$1::text||'.v1','courseNumber',$1::text,'canonicalCourseId',(select id from courses where enrollware_course_id=$1),'selectionId','native-full:'||encode(sha256(convert_to('advanced-race:'||$1::text,'UTF8')),'hex'),'instructorId',(select id from people where person_key='skills-test'),'availabilityPersonId','fixture-calendar-person','calendarSourceKey','fixture-calendar','resource','FIXTURE ROOM','location','FIXTURE LOCATION','endsAt',(skills_test.offer('advanced-race',20)->>'startsAt')::timestamptz+interval '4 hours','consumptionStartsAt',skills_test.offer('advanced-race',20)->>'startsAt','consumptionEndsAt',(skills_test.offer('advanced-race',20)->>'startsAt')::timestamptz+interval '4 hours','availabilityStartsAt',skills_test.offer('advanced-race',20)->>'startsAt','availabilityEndsAt',(skills_test.offer('advanced-race',20)->>'startsAt')::timestamptz+interval '4 hours','proofObservedAt',now())`,[course]);
 await scalar('select native_publish_advanced_offers($1::jsonb)',[JSON.stringify(Object.values(offers))]);
 const advancedClaim=(num,course)=>{const st={firstName:'Synthetic',lastName:'Fixture',email:`advanced-race-${num}@example.invalid`,phone:'2025550100',addons:[],manualChoice:'own-copy',firstAidChoice:'none'},input={wire:st,selectedChoices:['own_copy','no_first_aid'],submitted:{fields:{first_name:st.firstName,last_name:st.lastName,email:st.email,phone:st.phone},selectedChoices:['own_copy','no_first_aid']}};
  return run(`select reserve_native_advanced_checkout_order(${quote(key(num))},${quote(course==='241108'?'fixture_acls':'fixture_pals')},1,'',null,${quote(JSON.stringify(offers[course]))}::jsonb,${quote(JSON.stringify([st]))}::jsonb,${quote(JSON.stringify([input]))}::jsonb,${course==='241108'?22500:27500});`).then(out=>({accepted:true,receipt:JSON.parse(out.split('\n').at(-1)),course}),e=>({accepted:false,error:e.message,course}));};
 const alternatives=await Promise.all([advancedClaim(10,'241108'),advancedClaim(11,'209805')]);
 assert.equal(alternatives.filter(x=>x.accepted).length,1);assert.match(alternatives.find(x=>!x.accepted).error,/session_not_available/);
 const chosen=alternatives.find(x=>x.accepted),other=chosen.course==='241108'?'209805':'241108';
 assert.equal(await scalar('select count(*) from class_sessions where start_at=$1',[offers[chosen.course].startsAt]),1,'competing courses never duplicate room/instructor capacity');
 assert.equal(await scalar('select native_advanced_full_course_option($1,$2::jsonb)',[other,JSON.stringify(offers[other])]),null);
 assert.equal((await advancedClaim(12,chosen.course)).accepted,true);
 const third=await advancedClaim(13,chosen.course);assert.equal(third.accepted,false);assert.match(third.error,/session_not_available|insufficient_seats/);
 assert.equal(await scalar('select count(*) from class_sessions where start_at=$1',[offers[chosen.course].startsAt]),1);
 console.log('PASS independent advanced materialization race suppresses alternatives, preserves one canonical session and rejects a third seat');

});
console.log(JSON.stringify({state:'LOCAL_PROVEN',server,hostedCalls:0,payments:0,mailSends:0,activation:false}));
