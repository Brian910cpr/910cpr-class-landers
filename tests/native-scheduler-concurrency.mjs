#!/usr/bin/env node
// Local synthetic race harness only. Refuses nonempty/non-loopback/non-PG17 DBs.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
const database='native_scheduler_concurrency_test';
const port=Number(process.env.NATIVE_SCHEDULER_TEST_PORT||55438);
assert(Number.isInteger(port)&&port>0&&port<65536);
const env={...process.env};
for(const key of Object.keys(env))if(/^PG/i.test(key)||/DATABASE_URL/.test(key))delete env[key];
Object.assign(env,{PGHOSTADDR:'127.0.0.1',PGCONNECT_TIMEOUT:'3',PGPASSWORD:'',PGPASSFILE:'/dev/null',PGOPTIONS:'-c statement_timeout=20000 -c lock_timeout=15000'});
const args=['-X','-w','-q','-t','-A','-h','127.0.0.1','-p',String(port),'-U','postgres','-d',database,'-v','ON_ERROR_STOP=1'];
class Connection {
  constructor(label) {
    this.label = label;
    this.buffer = '';
    this.stderr = '';
    this.pending = null;
    this.exited = false;
    this.child = spawn('psql', args, { env, stdio: ['pipe', 'pipe', 'pipe'] });
    this.child.stdout.setEncoding('utf8');
    this.child.stderr.setEncoding('utf8');
    this.child.stderr.on('data', chunk => { this.stderr += chunk; });
    this.child.stdout.on('data', chunk => {
      this.buffer += chunk;
      const p = this.pending;
      if (!p) return;
      const index = this.buffer.indexOf(`${p.token}\n`);
      if (index === -1) return;
      const output = this.buffer.slice(0, index).trim();
      this.buffer = this.buffer.slice(index + p.token.length + 1);
      this.pending = null;
      clearTimeout(p.timer);
      p.resolve(output);
    });
    this.child.on('error', error => { this.exited = true; this.fail(error); });
    this.child.stdin.on('error', error => this.fail(error));
    this.child.on('exit', (code, signal) => {
      this.exited = true;
      this.fail(new Error(`${label}: psql exited (${code ?? signal}): ${this.stderr}`));
    });
  }
  fail(error) {
    if (!this.pending) return;
    const p = this.pending;
    this.pending = null;
    clearTimeout(p.timer);
    p.reject(error);
  }
  query(sql) {
    assert(!this.pending, `${this.label}: concurrent command on one connection`);
    assert(!this.exited, `${this.label}: connection already closed`);
    return new Promise((resolve, reject) => {
      const token = `done_${randomUUID().replaceAll('-', '')}`;
      const timer = setTimeout(() => {
        this.fail(new Error(`${this.label}: command timed out: ${this.stderr}`));
        this.child.kill('SIGTERM');
      }, 25000);
      this.pending = { token, resolve, reject, timer };
      this.child.stdin.write(`${sql}\n\\echo ${token}\n`);
    });
  }
  close() { this.child.stdin.end('\\q\n'); this.child.kill('SIGTERM'); }
}

const c=new Connection('control'),a=new Connection('first'),b=new Connection('second');
const connections=[c,a,b],result={server:null,cases:[]};
const value=async(connection,sql)=>JSON.parse(await connection.query(sql));
let pidA,pidB;
async function waitBlocked(pid,blocker=null){const until=Date.now()+10000;do{const blocked=await c.query(`select pg_stat_clear_snapshot();select exists(select 1 from pg_stat_activity where pid=${pid} and wait_event_type='Lock' and ${blocker===null?'cardinality(pg_blocking_pids(pid))>0':`${blocker}=any(pg_blocking_pids(pid))`});`);if(blocked==='t')return;}while(Date.now()<until);throw Error('deterministic lock barrier not reached');}
const secretId='11111111-1111-4111-8111-111111111111',syntheticToken='a'.repeat(64);
const digest=`encode(sha256(convert_to('${syntheticToken}','UTF8')),'hex')`;
const finish={outcome:'completed',code:null,claimed:0,accepted:0,rejected:0,ambiguous:0};
const beginSQL=id=>`select public.native_checkout_scheduler_begin('${id}',${digest});`;
const finishSQL=id=>`select public.native_checkout_scheduler_finish('${id}','${JSON.stringify(finish)}'::jsonb);`;
async function reset(){await c.query(`truncate landerware_native_scheduler.runs,net.captured,net._http_response restart identity;
 update landerware_native_scheduler.config set enabled=true,latched=false,reason=null,last_dispatch_at=null,last_observed_at=null,observation=null;`);}
async function queued(){assert.equal((await value(c,'select landerware_native_scheduler.dispatch();')).dispatched,true);return value(c,'select json_build_object(\'id\',id,\'request_id\',request_id) from landerware_native_scheduler.runs;');}
const check=async(name,fn)=>{await reset();await fn();result.cases.push({name,passed:true});console.log('PASS '+name);};
try{
 result.server=await value(c,`select json_build_object('database',current_database(),'version',current_setting('server_version_num')::int,'address',host(inet_server_addr()),'recovery',pg_is_in_recovery());`);
 assert.equal(result.server.database,database);assert.equal(Math.floor(result.server.version/10000),17);assert.equal(result.server.address,'127.0.0.1');assert.equal(result.server.recovery,false);
 assert.equal(await c.query(`select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';`),'0','refusing nonempty DB');
 assert.equal(await c.query(`select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in('pg_catalog','information_schema');`),'0','refusing existing routines');
 await c.query(await readFile(new URL('./helpers/native-scheduler-concurrency-schema.sql',import.meta.url),'utf8'));
 await c.query(await readFile(new URL('../supabase/migrations/20261111201439_native_confirmation_minute_scheduler_disabled.sql',import.meta.url),'utf8'));
 await c.query("set landerware.scheduler_secret_acl_approved='true';");
 await c.query(await readFile(new URL('../supabase/reviewed/native-confirmation-scheduler/00_restrict_transport_tables.sql',import.meta.url),'utf8'));
 await c.query(`insert into vault.decrypted_secrets values('${secretId}','${syntheticToken}');update landerware_native_scheduler.config set vault_secret_id='${secretId}',token_hash=${digest};`);
 pidA=Number(await a.query('select pg_backend_pid();'));pidB=Number(await b.query('select pg_backend_pid();'));
 await check('two concurrent dispatches enqueue exactly one durable run',async()=>{
  await c.query('begin;select id from landerware_native_scheduler.config where id for update;');
  const pa=value(a,'select landerware_native_scheduler.dispatch();'),pb=value(b,'select landerware_native_scheduler.dispatch();');
  await waitBlocked(pidA);await waitBlocked(pidB);await c.query('commit;');
  const outputs=await Promise.all([pa,pb]);assert.equal(outputs.filter(x=>x.dispatched===true).length,1);
  assert.equal(await c.query('select count(*) from net.captured;'),'1');assert.equal(await c.query('select count(*) from landerware_native_scheduler.runs;'),'1');
 });
 await check('same queued run admits once; invalid auth never waits on singleton',async()=>{
  const r=await queued();await a.query('begin;set local role service_role;');assert.equal((await value(a,beginSQL(r.id))).started,true);
  await b.query('set role service_role;');const pending=value(b,beginSQL(r.id));await waitBlocked(pidB,pidA);
  await c.query("set statement_timeout='1000ms';set role service_role;");assert.equal((await value(c,`select public.native_checkout_scheduler_begin('${r.id}','${'b'.repeat(64)}');`)).authorized,false);await c.query("reset role;set statement_timeout='20s';");
  await a.query('commit;');assert.equal((await pending).started,false);await b.query('reset role;');
  assert.equal(await c.query("select state from landerware_native_scheduler.runs;"),'running');
 });
 await check('concurrent exact finish becomes one settlement plus one replay',async()=>{
  const r=await queued();await value(c,beginSQL(r.id));await a.query('begin;set local role service_role;');assert.equal((await value(a,finishSQL(r.id))).settled,true);
  await b.query('set role service_role;');const pending=value(b,finishSQL(r.id));await waitBlocked(pidB,pidA);await a.query('commit;');assert.equal((await pending).replay,true);await b.query('reset role;');
  assert.equal(await c.query("select count(*) from landerware_native_scheduler.runs where state='completed';"),'1');
 });
 await check('observer behind a definitive finish does not latch lost HTTP response',async()=>{
  const r=await queued();await value(c,beginSQL(r.id));await c.query(`insert into net._http_response values(${r.request_id},null,true,'synthetic_timeout');`);
  await a.query('begin;set local role service_role;');await value(a,finishSQL(r.id));const observed=value(b,'select landerware_native_scheduler.observe();');await waitBlocked(pidB,pidA);await a.query('commit;');assert.equal((await observed).latched,false);
 });
 await check('finish behind an unknown-outcome observer never clears its durable latch',async()=>{
  const r=await queued();await value(c,beginSQL(r.id));await c.query(`insert into net._http_response values(${r.request_id},null,true,'synthetic_timeout');`);
  await a.query('begin;');assert.equal((await value(a,'select landerware_native_scheduler.observe();')).latched,true);
  await b.query('set role service_role;');const finished=value(b,finishSQL(r.id));await waitBlocked(pidB,pidA);await a.query('commit;');assert.equal((await finished).settled,true);await b.query('reset role;');
  assert.equal(await c.query('select latched from landerware_native_scheduler.config;'),'t');assert.equal(await c.query("select state from landerware_native_scheduler.runs;"),'completed');
 });
 await check('concurrent dispatch and observer serialize unknown latch without replay',async()=>{
  await queued();await c.query("update landerware_native_scheduler.runs set created_at=now()-interval '3 minutes';begin;select id from landerware_native_scheduler.config where id for update;");
  const observed=value(a,'select landerware_native_scheduler.observe();'),sent=value(b,'select landerware_native_scheduler.dispatch();');await waitBlocked(pidA);await waitBlocked(pidB);await c.query('commit;');await observed;assert.equal((await sent).dispatched,false);
  assert.equal(await c.query("select reason from landerware_native_scheduler.config;"),'callback_completion_unknown');assert.equal(await c.query('select count(*) from net.captured;'),'1');
 });
 await check('disable commits before waiting admission; no stale-config start',async()=>{
  const r=await queued();await a.query('begin;update landerware_native_scheduler.config set enabled=false where id;');await b.query('set role service_role;');const admission=value(b,beginSQL(r.id));await waitBlocked(pidB,pidA);await a.query('commit;');assert.equal((await admission).disabled,true);await b.query('reset role;');assert.equal(await c.query('select state from landerware_native_scheduler.runs;'),'queued');
 });
 result.passed=result.cases.length;result.scope='Local PostgreSQL17 concurrency with mock network/Vault only; no hosted calls, actual scheduler, secrets or sends.';console.log(JSON.stringify(result));
}finally{for(const connection of connections)connection.close();}
