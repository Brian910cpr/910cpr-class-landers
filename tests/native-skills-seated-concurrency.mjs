// Local-only PG17. Fresh schema required. No hosted URLs, passwords, or sends.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
import {proveSkillsSeats} from './native-skills-seated-proof.mjs';
const database='skills_claim_test_509474';
const psql=localPsql(database);
const quote=v=>v==null?'null':Array.isArray(v)?'ARRAY['+v.map(quote).join(',')+']::text[]':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
function run(sql){return new Promise((resolve,reject)=>{const p=spawn(psql.command,psql.args,{env:psql.env,stdio:['pipe','pipe','pipe']});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('error',reject);p.on('close',code=>code===0?resolve(out.trim()):reject(Error(err)));p.stdin.end(sql);});}
let role=null;
const prefix=()=>role?`set role ${role};`:'';
const db={exec:async sql=>{
 if(/^set role service_role;?$/i.test(sql.trim())){role='service_role';return '';}
 if(/^reset role;?$/i.test(sql.trim())){role=null;return '';}
 return run(prefix()+sql);
},query:async(sql,args)=>{const s=bind(sql,args).trim().replace(/;$/,'');const out=await run(prefix()+(/^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/^(?:insert|update|delete)\b/i.test(s)&&/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s));return {rows:out?out.split('\n').filter(v=>v.startsWith('{')).map(v=>JSON.parse(v)):[]};}};
const server=(await db.query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
assertLocalTargetServer(server,database);await assertIsolatedPostgresServerAddress(server.address,{args:psql.args,env:psql.env,port:Number(process.env.SKILLS_TEST_PORT||5432),database});
assert.equal(await run("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';"),'0');
assert.equal(await run("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema');"),'0');
await proveSkillsSeats(db,async(sql,second,third,sid)=>{
 const latch=50947491;
 const first=run(`begin;${bind(sql,second)};select pg_advisory_xact_lock(${latch});select pg_sleep(2);commit;`);
 let locked=false;
 for(let i=0;i<150&&!locked;i++)locked=await run(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${latch});`)==='t';
 assert.ok(locked,'second claim must hold its transaction before third starts');
 const contender=run(bind(sql,third)).then(()=>({accepted:true}),e=>({accepted:false,error:e.message}));
 const [receipt,result]=await Promise.all([first,contender]);
 const accepted=JSON.parse(receipt.split('\n').find(line=>line.startsWith('{')));
 assert.equal(accepted.sessionId,sid);assert.equal(result.accepted,false);assert.match(result.error,/session_not_available|insufficient_seats/);
 console.log('PASS independent PostgreSQL17 connections: cross-context second claim commits; concurrent third is rejected');
});
console.log(JSON.stringify({state:'LOCAL_PROVEN',server,hostedCalls:0,activation:false}));
