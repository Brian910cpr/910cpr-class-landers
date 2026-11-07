// Multi-client PostgreSQL, never Supabase/live. Explicit fresh localhost database only.
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const database=process.env.SKILLS_TEST_DATABASE;
if(!/^skills_claim_test(?:_\d+)?$/.test(database||''))throw Error('Use a fresh disposable localhost database named skills_claim_test.');
const args=['-X','-q','-t','-A','-h','127.0.0.1','-p',process.env.SKILLS_TEST_PORT||'5432','-U','postgres','-d',database,'-v','ON_ERROR_STOP=1'];
function run(sql){return new Promise(resolve=>{const p=spawn(process.env.SKILLS_TEST_PSQL||'psql',args,{windowsHide:true,stdio:['pipe','pipe','pipe']});let out='',error='';p.stdout.on('data',s=>out+=s);p.stderr.on('data',s=>error+=s);p.on('error',e=>resolve({code:-1,error:String(e),out}));p.on('close',code=>resolve({code,error,out}));p.stdin.end(sql);});}
function json(r){assert.equal(r.code,0,r.error);return JSON.parse(r.out.trim().split('\n').at(-1));}
const key=n=>`11111111-1111-4111-8111-${String(n).padStart(12,'0')}`;
const claim=(n,identity,day,offset=0)=>`public.reserve_skills_session_native('${key(n)}','cpr-aed',skills_test.offer('${identity}',${day},${offset}),skills_test.student(${n}))`;
const empty=await run('select count(*) from customers');assert.equal(empty.code,0,empty.error);assert.equal(+empty.out.trim(),0,'Fixture requires empty database');
const setup=await run(readFileSync(new URL('./helpers/skills-native-synthetic.sql',import.meta.url),'utf8'));assert.equal(setup.code,0,setup.error);
const first=run(`begin;select ${claim(1,'first',30)};select pg_advisory_xact_lock(55479021);select pg_sleep(2);commit;`);
let locked=false;for(let i=0;i<60&&!locked;i++){const r=await run("select count(*) from pg_locks where locktype='advisory' and objid=55479021");assert.equal(r.code,0,r.error);locked=+r.out.trim()>0;}
assert.ok(locked,'First claim did not acquire latch');
const second=run(`select ${claim(2,'overlap',30,30)}`);
const [a,b]=await Promise.all([first,second]);assert.equal(a.code,0,a.error);assert.notEqual(b.code,0);assert.match(b.error,/session_not_available/);
const original=json(await run(`select ${claim(1,'first',30)}`));assert.equal(original.idempotentReplay,true);
const evidence=json(await run("select jsonb_build_object('sessions',(select count(*) from class_sessions),'registrations',(select count(*) from registrations),'receipts',(select count(*) from skills_session_claim_receipts),'customers',(select count(*) from customers))"));
assert.deepEqual(evidence,{sessions:1,registrations:1,receipts:1,customers:1});
json(await run(`select ${claim(3,'same',31)}`));
const same=await Promise.all([run(`select ${claim(4,'same',31)}`),run(`select ${claim(5,'same',31)}`)]);
assert.equal(same.filter(r=>r.code===0).length,1,'one final seat only');assert.match(same.find(r=>r.code!==0).error,/session_not_available/);
const end=json(await run("select jsonb_build_object('sessions',(select count(*) from class_sessions),'registrations',(select count(*) from registrations),'receipts',(select count(*) from skills_session_claim_receipts))"));
assert.deepEqual(end,{sessions:2,registrations:3,receipts:3});
json(await run(`select ${claim(6,'next',31,60)}`));
const cleanup=await run(`select ${claim(7,'cleanup-conflict',31,45)}`);assert.notEqual(cleanup.code,0);assert.match(cleanup.error,/session_not_available/);
console.log('PASS: overlapping claims serialize; two seats share one session; concurrent final-seat claims reject the third person; exact cleanup boundary chains; cleanup overlap fails; replay is stable.');
