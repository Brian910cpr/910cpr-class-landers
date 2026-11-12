// Fresh, isolated loopback PostgreSQL17 only. Synthetic data, no hosted URLs or sends.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {randomUUID} from 'node:crypto';
import {spawn} from 'node:child_process';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
import {proveHeartsaverScopes} from './native-heartsaver-full-proof.mjs';
const database='skills_claim_test_223000',psql=localPsql(database);
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

const args=psql.args,env=psql.env;
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

await proveHeartsaverScopes(db);
const migration=readFileSync(new URL('../supabase/migrations/20261111223000_native_heartsaver_publication.sql',import.meta.url),'utf8');
await db.exec(migration);
console.log('PASS actual publication migration on PostgreSQL17 after complete Heartsaver checkout proof');
const reader=new Connection('reader'),writer=new Connection('writer');
try {
 await writer.query("update native_heartsaver_full_course_policy set enabled=true,publication_enabled=true;");
 const session=await writer.query("select id from class_sessions where external_course_id='209809' and source='landerware_event' and status='scheduled' limit 1;");
 const order=await writer.query(`select id from landerware_public_orders where class_session_id='${session}' and status='paid' limit 1;`);
 const registration=await writer.query(`select id from registrations where class_session_id='${session}' limit 1;`);
 // Multiple qualification rows cannot widen the ready-through horizon.
 await writer.query(`begin;
  insert into instructor_qualifications(instructor_id,course_id,status,expires_at)
   select instructor_id,'23dfcfa7-4224-46ed-8d45-64d43d5425db','active',expiry
   from instructor_qualifications source cross join (values(now()+interval '2 days'),(now()+interval '4 days'),(null::timestamptz)) dates(expiry)
   where source.id='11111111-1111-4111-8111-111111111111';`);
 let proof=JSON.parse(await writer.query('select native_heartsaver_publication_policy();'));
 const expected=await writer.query(`select min(expires_at) from instructor_qualifications where course_id='23dfcfa7-4224-46ed-8d45-64d43d5425db';`);
 assert.equal(Date.parse(proof.courses['209809'].qualificationValidThrough),Date.parse(expected));
 assert.equal(proof.courses['209809'].nativePublicationEnabled,true,'ready now but future offers must respect earliest expiry');
 assert.equal(JSON.parse(await writer.query(`select native_scheduling_seat_snapshot('${session}');`)).heartsaverBooking,null,'through consumed end rejects earlier target qualification expiry');
 await writer.query(`update instructor_qualifications set status='revoked' where course_id='23dfcfa7-4224-46ed-8d45-64d43d5425db' and expires_at is null;`);
 proof=JSON.parse(await writer.query('select native_heartsaver_publication_policy();'));
 assert.equal(proof.courses['209809'].nativePublicationEnabled,false);assert.equal(proof.courses['209809'].qualificationValidThrough,null);
 await writer.query('rollback;');
 console.log('PASS multiple qualifications: earliest expiry bounds proof, consumed end rechecks, revocation overrides');
 const actual=await writer.query("select pg_get_functiondef('native_scheduling_seat_snapshot(uuid)'::regprocedure);");
 const lock=22300091;
 const barrier=` PERFORM pg_catalog.pg_advisory_lock(${lock}); PERFORM pg_catalog.pg_advisory_unlock(${lock});`;
 assert.equal(actual.split('-- snapshot_registration_count_captured').length,2);
 await writer.query('create schema publication_race;grant usage on schema publication_race to service_role;');
 for(const stable of [true,false]){
  const name=stable?'stable_reader':'volatile_control';
  let clone=actual.replace('public.native_scheduling_seat_snapshot(',`publication_race.${name}(`).replace('-- snapshot_registration_count_captured',barrier);
  if(!stable)clone=clone.replace(/\bSTABLE\b/,'VOLATILE');
  await writer.query(clone+`;revoke all on function publication_race.${name}(uuid) from public;grant execute on function publication_race.${name}(uuid) to service_role;`);
 }
 const readerPid=Number(await reader.query('select pg_backend_pid();')),writerPid=Number(await writer.query('select pg_backend_pid();'));
 await reader.query('set role service_role;');
 const read=async()=>JSON.parse(await reader.query(`select native_scheduling_seat_snapshot('${session}');`));
 let passed=0;
 for(const gate of ['policy','qualification'])for(const stable of [true,false]){
  await writer.query(`begin;
   update native_heartsaver_full_course_policy set enabled=true,publication_enabled=true;
   update instructor_qualifications set status='active',expires_at=now()+interval '2 years' where id='11111111-1111-4111-8111-111111111111';
   update registrations set status='cancelled' where id='${registration}';
   update landerware_public_orders set status='held',hold_expires_at=now()+interval '1 hour',payment_evidence='{}',stripe_payment_intent_id=null,reconciliation_error=null where id='${order}';
   commit;`);
  const before=await read();assert.equal(before.registered,0);assert.equal(before.holds,1);assert.equal(before.heartsaverBooking.remaining,1);
  await writer.query(`select pg_advisory_lock(${lock});`);
  const name=stable?'stable_reader':'volatile_control';
  const pending=reader.query(`select publication_race.${name}('${session}');`).then(value=>({value}),error=>({error}));
  let blocked=false;const deadline=Date.now()+12000;
  while(Date.now()<deadline&&!blocked)blocked=(await writer.query(`select exists(select 1 from pg_stat_activity where pid=${readerPid} and wait_event='advisory' and ${writerPid}=any(pg_blocking_pids(pid)));`))==='t';
  assert.ok(blocked,'deterministic reader barrier');
  await writer.query(`begin;
   update registrations set status='registered' where id='${registration}';
   update landerware_public_orders set status='paid' where id='${order}';
   ${gate==='policy'?"update native_heartsaver_full_course_policy set publication_enabled=false where public_course_id='209809';":"update instructor_qualifications set expires_at=now()+interval '1 day' where id='11111111-1111-4111-8111-111111111111';"}
   commit;select pg_advisory_unlock(${lock});`);
  const result=await pending;if(result.error)throw result.error;const during=JSON.parse(result.value);
  if(stable)assert.deepEqual(during,before,'admission and occupancy remain same statement snapshot');
  else {assert.equal(during.registered+during.holds,0,'volatile control observes torn occupancy');assert.equal(during.heartsaverBooking,null);}
  const after=await read();assert.equal(after.registered,1);assert.equal(after.holds,0);assert.equal(after.remaining,1);assert.equal(after.heartsaverBooking,null,'next statement rechecks revoked publication/through-time gate');
  console.log(`PASS ${name}: concurrent ${gate} change and hold-to-registration conversion`);passed++;
 }
 assert.equal(await writer.query("select pg_get_functiondef('native_scheduling_seat_snapshot(uuid)'::regprocedure);"),actual);
 console.log(`PASS ${passed} deterministic races; actual STABLE definition unchanged`);
}finally{reader.close();writer.close();}
