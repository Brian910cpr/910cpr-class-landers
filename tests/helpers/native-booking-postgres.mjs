// Test-only PostgreSQL clients. All targets pass the existing isolated-address guard.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';

export const quote=v=>v==null?'null':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
const resultSQL=(sql,args)=>{
 const s=bind(sql,args).trim().replace(/;$/,'');
 return /^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s+';';
};
const rows=out=>out.split('\n').filter(v=>v.startsWith('{')).map(v=>JSON.parse(v));
export async function createPg(root){
 const {localPsql,assertLocalTargetServer}=await import(pathToFileURL(root+'/tests/helpers/local-postgres.mjs'));
 const {assertIsolatedPostgresServerAddress}=await import(pathToFileURL(root+'/tests/helpers/isolated-postgres-address.mjs'));
 const database='skills_claim_test_121198',config=localPsql(database),proofs=[];
 let legacyRole=false;
 function launch(sql,{label='paid-race-admin',service=false,responseLatch=null}={}){
  assert(/^[a-zA-Z0-9_-]{1,63}$/.test(label));
  let text=`set application_name=${quote(label)};`;
  if(service)text+=`begin;set local role service_role;do $$begin
   if current_user<>'service_role' or (select rolsuper or not rolbypassrls from pg_roles where rolname=current_user)
   then raise exception 'actual_nonsuperuser_service_role_required';end if;end$$;
   select 'ROLE|'||jsonb_build_object('role',current_user,'superuser',(select rolsuper from pg_roles where rolname=current_user),'bypassrls',(select rolbypassrls from pg_roles where rolname=current_user),'isolation',current_setting('transaction_isolation'),'pid',pg_backend_pid())::text;`;
  text+=sql;
  if(service)text+='commit;';
  if(responseLatch!==null){assert(Number.isSafeInteger(responseLatch));text+=`select pg_advisory_lock(${responseLatch});`;}
  const process=spawn(config.command,config.args,{env:config.env,stdio:['pipe','pipe','pipe']});
  let stdout='',stderr='';
  const promise=new Promise((resolve,reject)=>{
   process.stdout.on('data',b=>stdout+=b);process.stderr.on('data',b=>stderr+=b);process.on('error',reject);
   process.on('close',(code,signal)=>{
    try{
     if(service){
      const line=stdout.split('\n').find(v=>v.startsWith('ROLE|'));assert.ok(line,`${label}: service-role assertion missing`);
      const proof=JSON.parse(line.slice(5));assert.equal(proof.role,'service_role');assert.equal(proof.superuser,false);assert.equal(proof.bypassrls,true);assert.equal(proof.isolation,'read committed');proofs.push({label,...proof,commandExit:code});
     }
     if(code!==0){const e=Error(`${label}: psql connection ended (${code}/${signal}): ${stderr}`);e.sqlRows=rows(stdout);e.commandExit=code;reject(e);}
     else resolve(stdout.trim());
    }catch(e){reject(e);}
   });
   process.stdin.end(text);
  });
  // A caller may deliberately hold this command behind a database latch.
  promise.catch(()=>{});
  return {promise,process};
 }
 const query=async(sql,args=[],options={})=>({rows:rows(await launch(resultSQL(sql,args),options).promise)});
 const db={
  exec:async sql=>{if(sql==='set role service_role'){assert.equal(legacyRole,false);legacyRole=true;return;}if(sql==='reset role'){legacyRole=false;return;}return launch(sql,{service:legacyRole}).promise;},
  query:(sql,args)=>query(sql,args,{service:legacyRole}),
  serviceQuery:(sql,args,options={})=>query(sql,args,{...options,service:true}),
  adminQuery:(sql,args,options={})=>query(sql,args,options),
  proofs,
  async controller(label){
   assert(/^[a-zA-Z0-9_-]{1,63}$/.test(label));
   const p=spawn(config.command,config.args,{env:config.env,stdio:['pipe','pipe','pipe']});
   let buffer='',sequence=0,pending=null,errors='',closed=false;
   p.stdout.on('data',v=>{buffer+=v;const marker=pending?.marker;if(marker&&buffer.includes(marker+'\n')){const prefix=buffer.slice(0,buffer.indexOf(marker+'\n'));buffer=buffer.slice(buffer.indexOf(marker+'\n')+marker.length+1);const {resolve}=pending;pending=null;resolve(prefix.trim());}});
   p.stderr.on('data',v=>errors+=v);
   const done=new Promise(resolve=>{p.on('close',code=>{closed=true;if(pending){pending.reject(Error(`${label}: controller exited ${code}: ${errors}`));pending=null;}resolve(code);});});
   const send=sql=>new Promise((resolve,reject)=>{assert(!pending,'controller commands must be awaited');assert(!closed,'controller already closed');const marker=`CONTROLLER_${++sequence}`;pending={resolve,reject,marker};p.stdin.write(sql+'\n\\echo '+marker+'\n');});
   await send(`set application_name=${quote(label)};`);
   return {send,async close(){if(!closed)p.stdin.end('rollback;\n\\q\n');await done;}};
  },
  close:async()=>console.log('SERVICE_ROLE_TRANSACTIONS',proofs.length)
 };
 const server=(await query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
 assertLocalTargetServer(server,database);
 await assertIsolatedPostgresServerAddress(server.address,{args:config.args,env:config.env,port:Number(process.env.SKILLS_TEST_PORT),database});
 assert.equal((await query("select count(*)::int as n from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in('pg_catalog','information_schema') and n.nspname not like 'pg_toast%'")).rows[0].n,0);
 assert.equal((await query("select count(*)::int as n from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in('pg_catalog','information_schema')")).rows[0].n,0);
 console.log('ISOLATED_POSTGRES',JSON.stringify(server));
 return db;
}
