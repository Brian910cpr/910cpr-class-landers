// Uses existing isolated loopback guards. Never connects to hosted PostgreSQL.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
export async function createPg(root){
 const {localPsql,assertLocalTargetServer}=await import(pathToFileURL(root+'/tests/helpers/local-postgres.mjs'));
 const {assertIsolatedPostgresServerAddress}=await import(pathToFileURL(root+'/tests/helpers/isolated-postgres-address.mjs'));
 const database='skills_claim_test_121197',psql=localPsql(database);
 let role=null,serviceCalls=0;
 const quote=v=>v==null?'null':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
 const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
 const run=sql=>new Promise((resolve,reject)=>{
  const p=spawn(psql.command,psql.args,{env:psql.env,stdio:['pipe','pipe','pipe']});let out='',err='';
  p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('error',reject);
  p.on('close',code=>code===0?resolve(out.trim()):reject(Error(err)));p.stdin.end(sql);
 });
 const serviceWrap=sql=>{
  if(!role)return sql;
  if(role==='service_role')serviceCalls++;
  return `begin;set local role ${role};do $$begin
   if current_user<>'${role}' or (select rolsuper from pg_roles where rolname=current_user)
    or ('${role}'='service_role' and not (select rolbypassrls from pg_roles where rolname=current_user))
   then raise exception 'actual_nonsuperuser_role_required';end if;end$$;${sql};commit;`;
 };
 const db={
  exec:async sql=>{if(/^set role (service_role|anon|authenticated)$/.test(sql)){assert.equal(role,null);role=sql.slice(9);return;}if(sql==='reset role'){role=null;return;}return run(serviceWrap(sql));},
  query:async(sql,args)=>{const s=bind(sql,args).trim().replace(/;$/,'');
   const q=/^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s+';';
   const out=await run(serviceWrap(q));return {rows:out?out.split('\n').filter(v=>v.startsWith('{')).map(v=>JSON.parse(v)):[]};},
  close:async()=>console.log('PostgreSQL17 actual non-superuser service-role calls:',serviceCalls)
 };
 const server=(await db.query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
 assertLocalTargetServer(server,database);await assertIsolatedPostgresServerAddress(server.address,{args:psql.args,env:psql.env,port:Number(process.env.SKILLS_TEST_PORT),database});
 assert.equal(await run("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';"),'0');
 assert.equal(await run("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in('pg_catalog','information_schema');"),'0');
 console.log('Verified fresh isolated PostgreSQL server:',JSON.stringify(server));return db;
}
