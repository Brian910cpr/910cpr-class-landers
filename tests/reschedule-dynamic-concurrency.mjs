// Local-only integration test. First load the production-derived schema and draft RPCs.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFileSync} from 'node:fs';
const psql=process.env.RESCHEDULE_TEST_PSQL||'psql';
const database=process.env.RESCHEDULE_TEST_DATABASE;
if(!/^reschedule_concurrency_test(?:_\d+)?$/.test(database||''))throw Error('Use only a new disposable database named reschedule_concurrency_test on localhost.');
const args=['-X','-q','-t','-A','-h','127.0.0.1','-p',process.env.RESCHEDULE_TEST_PORT||'55479','-U','postgres','-d',database,'-v','ON_ERROR_STOP=1'];
function run(sql){return new Promise(resolve=>{const child=spawn(psql,args,{windowsHide:true,stdio:['pipe','pipe','pipe']});let out='',error='';child.stdout.on('data',s=>out+=s);child.stderr.on('data',s=>error+=s);child.on('error',e=>resolve({code:-1,error:String(e),out}));child.on('close',code=>resolve({code,error,out}));child.stdin.end(sql);});}
function json(result){assert.equal(result.code,0,result.error);return JSON.parse(result.out.trim().split('\n').at(-1));}
const empty=await run('select count(*) from public.customers');assert.equal(empty.code,0,empty.error);assert.equal(+empty.out.trim(),0,'Fixture requires an empty database');
const setup=await run(readFileSync(new URL('./helpers/reschedule-synthetic.sql',import.meta.url),'utf8'));assert.equal(setup.code,0,setup.error);
const a=json(await run("select reschedule_test_fixture.registration('concurrent-a','209806',10)"));
const b=json(await run("select reschedule_test_fixture.registration('concurrent-b','359474',11)"));
// The first client holds an overlapping materialization uncommitted while the second starts.
// A session advisory latch exposes the lock state so the assertion does not depend on timing.
const first=run(`begin; select public.confirm_registration_reschedule_dynamic('${a.token}',reschedule_test_fixture.offer('concurrent-a','209806',30)); select pg_advisory_xact_lock(55479001); select pg_sleep(2); commit;`);
let locked=false;for(let i=0;i<40&&!locked;i++){const r=await run('select count(*) from pg_locks where locktype=\'advisory\' and objid=55479001');assert.equal(r.code,0,r.error);locked=+r.out.trim()>0;}
assert.ok(locked,'First transaction did not acquire the concurrency latch');
const second=run(`select public.confirm_registration_reschedule_dynamic('${b.token}',reschedule_test_fixture.offer('concurrent-b','359474',30,30))`);
const [one,two]=await Promise.all([first,second]);assert.equal(one.code,0,one.error);assert.notEqual(two.code,0);assert.match(two.error,/session_not_available/);
const evidence=json(await run(`select jsonb_build_object('targets',(select count(*) from public.class_sessions where source='landerware_public_offer'),'moves',(select count(*) from public.registration_supersessions),'loserStatus',(select status from public.registrations where id='${b.registration}'),'unused',(select used_at is null from public.registration_reschedule_links where token_sha256='${b.token}'))`));
assert.deepEqual(evidence,{targets:1,moves:1,loserStatus:'registered',unused:true});
// Identical-choice retry after the commit must return the original receipt and no second target.
const replay=json(await run(`select public.confirm_registration_reschedule_dynamic('${a.token}',reschedule_test_fixture.offer('concurrent-a','209806',30))`));assert.equal(replay.idempotentReplay,true);
const c=json(await run("select reschedule_test_fixture.registration('same-a','209806',12)"));
const d=json(await run("select reschedule_test_fixture.registration('same-b','209806',13)"));
const shared="reschedule_test_fixture.offer('same-target','209806',31)";
const results=await Promise.all([run(`select public.confirm_registration_reschedule_dynamic('${c.token}',${shared})`),run(`select public.confirm_registration_reschedule_dynamic('${d.token}',${shared})`)]);
const receipts=results.map(json);assert.equal(receipts[0].sessionId,receipts[1].sessionId);
const final=json(await run("select jsonb_build_object('targets',(select count(*) from public.class_sessions where source='landerware_public_offer'),'moves',(select count(*) from public.registration_supersessions))"));
assert.deepEqual(final,{targets:2,moves:3});
console.log('PASS: overlapping concurrent course choices produce one target/move; loser source/link preserved; replay has no duplicate; concurrent identical choices reuse one target.');
