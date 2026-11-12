// Run after skills-native-concurrency in a disposable LOCAL PostgreSQL database.
import {spawn} from 'node:child_process';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import assert from 'node:assert/strict';
const database=process.env.SKILLS_TEST_DATABASE;
if(!/^skills_claim_test(?:_\d+)?$/.test(database||''))throw Error('Use a disposable localhost skills_claim_test database.');
const psql=localPsql(database),args=psql.args;
function run(sql){return new Promise(resolve=>{const p=spawn(psql.command,args,{windowsHide:true,env:psql.env,stdio:['pipe','pipe','pipe']});let out='',error='';p.stdout.on('data',s=>out+=s);p.stderr.on('data',s=>error+=s);p.on('error',e=>resolve({code:-1,error:String(e),out}));p.on('close',code=>resolve({code,error,out}));p.stdin.end(sql);});}
function json(r){assert.equal(r.code,0,r.error);return JSON.parse(r.out.trim().split('\n').at(-1));}
const server=json(await run("select jsonb_build_object('database',current_database(),'version',current_setting('server_version_num')::integer,'recovery',pg_is_in_recovery())"));
assertLocalTargetServer(server,database);
async function latched(sql,other,latch){
 const first=run(`begin;${sql};select pg_advisory_xact_lock(${latch});select pg_sleep(2);commit;`);
 let locked=false;
 for(let i=0;i<60&&!locked;i++){const r=await run(`select count(*) from pg_locks where locktype='advisory' and objid=${latch}`);assert.equal(r.code,0,r.error);locked=+r.out.trim()>0;}
 assert.ok(locked,'First transaction did not acquire test latch');
 return Promise.all([first,run(other)]);
}
const receipt=json(await run("select reserve_skills_session_native('22222222-2222-4222-8222-222222222220','cpr-aed',skills_test.offer('checkout-race',45),skills_test.student(20))"));
const reg=receipt.registrationId;
const [bound,rejected]=await latched(`select bind_skills_checkout('${reg}','cs_first')`,`select bind_skills_checkout('${reg}','cs_second')`,55479101);
assert.equal(bound.code,0,bound.error);assert.notEqual(rejected.code,0);assert.match(rejected.error,/payment_mismatch/);
const confirm=`select confirm_skills_checkout_payment('${reg}','cs_first',5500,'usd','pi_fixture')`;
const payments=await Promise.all([run(confirm),run(confirm)]);
assert.ok(payments.every(r=>r.code===0),payments.map(r=>r.error).join('\n'));
assert.equal(payments.filter(r=>json(r).idempotentReplay===true).length,1);
const paid=json(await run(`select jsonb_build_object('count',count(*),'paid',bool_and(status='paid'),'session',min(stripe_checkout_session_id)) from registration_orders where registration_id='${reg}'`));
assert.deepEqual(paid,{count:1,paid:true,session:'cs_first'});
const cancelled=json(await run("select reserve_skills_session_native('22222222-2222-4222-8222-222222222221','cpr-aed',skills_test.offer('checkout-cancel-race',46),skills_test.student(21))"));
const rid=cancelled.registrationId;json(await run(`select bind_skills_checkout('${rid}','cs_cancel')`));
const [cancel,payment]=await latched(`update registrations set status='canceled' where id='${rid}';update registration_orders set status='canceled' where registration_id='${rid}'`,`select confirm_skills_checkout_payment('${rid}','cs_cancel',5500,'usd','pi_fixture')`,55479102);
assert.equal(cancel.code,0,cancel.error);assert.notEqual(payment.code,0);assert.match(payment.error,/payment_mismatch/);
const state=await run(`select status from registration_orders where registration_id='${rid}'`);assert.equal(state.code,0,state.error);assert.equal(state.out.trim(),'canceled');
console.log('PASS: competing checkout bindings serialize; duplicate payment events record paid once; a canceled registration cannot be resurrected by a racing payment event.');
