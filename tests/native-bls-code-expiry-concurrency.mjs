// Isolated loopback PostgreSQL17 only. Actual BLS/code SQL; synthetic stock and observer.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {localPsql,assertLocalTargetServer} from './helpers/local-postgres.mjs';
import {assertIsolatedPostgresServerAddress} from './helpers/isolated-postgres-address.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const bundleRoot=process.env.BLS_BUNDLE_CANDIDATE_ROOT||root;
assert.equal(createHash('sha256').update(readFileSync(resolve(bundleRoot,'supabase/migrations/20261111233504_native_bls_skills_publication_disabled.sql'))).digest('hex'),'9ce785c0f8b3989a3b9ee4ef543610875de18c52f934c2dba834043bbcccc7d2');
const {setupBlsSkills,enableSkills,makeOffer,request,claim,claimSQL,scalar,service,footprint}=await import(pathToFileURL(resolve(bundleRoot,'tests/native-bls-skills-proof.mjs')));
const {makeOffer:makeSharedOffer,request:sharedRequest,claim:sharedClaim,contexts}=await import(pathToFileURL(resolve(bundleRoot,'tests/native-skills-offer-lease-proof.mjs')));
const full=process.argv.includes('--full'),database=full?'skills_claim_test_120006':'skills_claim_test_120005',psql=localPsql(database);
const quote=v=>v==null?'null':typeof v==='number'?String(v):"'"+String(v).replaceAll("'","''")+"'";
const bind=(sql,args=[])=>sql.replace(/\$(\d+)\b/g,(_,i)=>quote(args[Number(i)-1]));
function run(sql){return new Promise((resolve,reject)=>{const p=spawn(psql.command,psql.args,{env:psql.env,stdio:['pipe','pipe','pipe']});let out='',err='';p.stdout.on('data',v=>out+=v);p.stderr.on('data',v=>err+=v);p.on('error',reject);p.on('close',code=>code===0?resolve(out.trim()):reject(Error(err)));p.stdin.end(sql);});}
let role=null;const prefix=()=>role?`set role ${role};`:'';
const db={exec:async sql=>{if(/^set role service_role;?$/i.test(sql.trim())){role='service_role';return '';}if(/^reset role;?$/i.test(sql.trim())){role=null;return '';}return run(prefix()+sql);},query:async(sql,args)=>{const s=bind(sql,args).trim().replace(/;$/,'');const q=/^select\b/i.test(s)?`select row_to_json(q) from (${s}) q;`:/\breturning\b/i.test(s)?`with q as (${s}) select row_to_json(q) from q;`:s;const out=await run(prefix()+q);return {rows:out?out.split('\n').filter(v=>v.startsWith('{')).map(JSON.parse):[]};}};
const server=(await db.query("select current_database() as database,current_setting('server_version_num')::int as version,pg_is_in_recovery() as recovery,host(inet_server_addr()) as address")).rows[0];
assertLocalTargetServer(server,database);await assertIsolatedPostgresServerAddress(server.address,{args:psql.args,env:psql.env,port:Number(process.env.SKILLS_TEST_PORT||5432),database});
assert.equal(await run("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%';"),'0');
assert.equal(await run("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname not in ('pg_catalog','information_schema');"),'0');
await setupBlsSkills(db,{full});await enableSkills(db);
for(const f of ['20261109130000_native_learner_code_delivery.sql','20261109140000_native_code_delivery_events.sql','20261111235100_native_learner_code_resend_service.sql','20261112000500_native_bls_code_completion_guard.sql'])await db.exec(readFileSync(resolve(root,'supabase/migrations',f),'utf8'));
await db.exec(`update native_bls_skills_publication_policy set bundle_enabled=true,bundle_verified=true,bundle_evidence='LOCAL SYNTHETIC ONLY';
 update landerware_checkout_delivery_config set enabled=true,provider='resend';update native_code_delivery_policy set enabled=true;
 update landerware_bls_bundle_policy set enabled=true,verified=true,verification_evidence='LOCAL SYNTHETIC ONLY';
 update landerware_registration_catalog set addons=jsonb_set(addons,'{0,active}','true') where course_id='509474';
 insert into products(product_key,active,product_type,customer_price,fulfillment_mode) values('aha-25-3553-heartcode-bls-online',true,'online_program',40,'digital_code');
 insert into product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-PRIVATE-CODE-'||n,'available' from products cross join generate_series(1,8) n;
 create function public.native_checkout_scheduler_status() returns jsonb language sql stable security invoker set search_path='' as $$select jsonb_build_object('enabled',true,'latched',false,'lastObservedAt',statement_timestamp(),'lastCompletedAt',statement_timestamp())$$;
 revoke all on function public.native_checkout_scheduler_status() from public,anon,authenticated;grant execute on function public.native_checkout_scheduler_status() to service_role;
 update native_learner_code_runtime set enabled=true,configured=true,proven=true,proof_at=clock_timestamp(),proof_reference='LOCAL SYNTHETIC ONLY';
 alter role service_role nosuperuser bypassrls;`);
const refresh=()=>db.exec('update native_learner_code_runtime set last_poll_at=clock_timestamp(),last_completed_at=clock_timestamp()');
await refresh();assert.equal((await scalar(db,'select native_learner_code_runtime_readiness()')).ready,true);
assert.equal(await scalar(db,"select has_column_privilege('service_role','landerware_checkout_delivery_config','enabled','UPDATE')"),false);
assert.equal(await scalar(db,"select has_column_privilege('service_role','landerware_checkout_delivery_config','token_sha256','UPDATE')"),false);
async function until(sql,message){let ok=false;for(let i=0;i<200&&!ok;i++)ok=await run(sql)==='t';assert.ok(ok,message);}
async function workspaceWait(day,n,{stale=false,mutations=false}={}){
 await refresh();const offer=await makeOffer(db,day,{bundle:true}),args=request(offer,n);
 const option=await service(db,()=>scalar(db,"select skills_session_native_option('bls-skills',$1::jsonb)",[JSON.stringify(offer)]));assert.ok(option);
 const before=await footprint(db);
 const insert=`insert into landerware_sessions(external_session_id,course_id,course_name,starts_at,ends_at,provenance,requirements_manifest) values(${quote(option.externalId)},'skills-session-only','Synthetic',${quote(offer.startsAt)},${quote(offer.endsAt)},'fixture','{}')`;
 const latch=n+90000;
 const blocker=run(`begin;${insert};select pg_advisory_xact_lock(${latch});select pg_sleep(5);rollback;`);
 await until(`select exists(select 1 from pg_locks where locktype='advisory' and objid=${latch});`,'workspace blocker latch');
 if(stale)await db.exec("update native_learner_code_runtime set last_poll_at=clock_timestamp()-interval '177 seconds',last_completed_at=clock_timestamp()-interval '177 seconds'");
 assert.equal((await scalar(db,'select native_learner_code_runtime_readiness()')).ready,true,'sender fresh when materializer begins');
 const attempt=run('begin;set local role service_role;'+bind(claimSQL,args)+';commit;').then(out=>({out}),error=>({error}));
 try{await until(`select exists(select 1 from pg_stat_activity where query like '%${args[0]}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`,'actual reservation must wait on late workspace unique row');}catch(error){await blocker;const early=await attempt;throw Error(early.error?.message||error.message);}
 const writers=[];
 if(mutations){
  for(const [label,sql] of [['product',"update products set active=false where product_key='aha-25-3553-heartcode-bls-online'"],['config','update landerware_checkout_delivery_config set enabled=false where id']]){
   const marker='bundle_dependency_'+label+'_'+n;
   const writer=run(sql+' /* '+marker+' */;');writers.push(writer);
   await until(`select exists(select 1 from pg_stat_activity where query like '%${marker}%' and pid<>pg_backend_pid() and wait_event_type='Lock');`,label+' update must wait on materializer-held SHARE row');
  }
 }
 const [,result]=await Promise.all([blocker,attempt]);
 if(mutations){await Promise.all(writers);assert.equal(await scalar(db,"select active from products where product_key='aha-25-3553-heartcode-bls-online'"),false);assert.equal(await scalar(db,'select enabled from landerware_checkout_delivery_config'),false);await db.exec("update products set active=true where product_key='aha-25-3553-heartcode-bls-online';update landerware_checkout_delivery_config set enabled=true where id");console.log('PASS concurrent product and config writers wait until materializer transaction completes');}
 assert.ok(Date.parse(offer.validUntil)>Date.now(),'offer itself remains valid; only code runtime proof expires');
 if(stale){assert.match(result.error?.message||'',/session_not_available/);assert.deepEqual(await footprint(db),before,'expired sender rolls back complete session/workspace/order/inventory footprint');assert.equal((await scalar(db,'select native_learner_code_runtime_readiness()')).ready,false);return {offer,args};}
 assert.equal(result.error,undefined);const held=JSON.parse(result.out);assert.equal(held.amountCents,9500);return {offer,args,held};
}
const fresh=await workspaceWait(67,9101,{mutations:true});console.log('PASS fresh code runtime survives same late workspace wait and admits9500');
await workspaceWait(68,9102,{stale:true});console.log('PASS code proof expires during final workspace unique wait; materializer rejects and all writes roll back');
const replay=await claim(db,fresh.args);assert.equal(replay.orderId,fresh.held.orderId);console.log('PASS prior9500 nonce replay survives stale code readiness');
const skills=await makeOffer(db,69),held55=await claim(db,request(skills,9103));assert.equal(held55.amountCents,5500);console.log('PASS skills-only5500 still admits with stale code readiness');
const checkout='cs_synthetic_expiry_recovery',intent='pi_synthetic_expiry_recovery';
await db.query('update landerware_public_orders set stripe_checkout_session_id=$2 where id=$1',[fresh.held.orderId,checkout]);
const evidence={id:checkout,mode:'payment',payment_status:'paid',amount_total:9500,currency:'usd',metadata:{landerware_order_id:fresh.held.orderId}};
await service(db,()=>scalar(db,'select native_checkout_record_payment($1,$2,$3::jsonb)',[fresh.held.orderId,intent,JSON.stringify(evidence)]));
const finalize=()=>service(db,()=>scalar(db,'select native_checkout_finalize_order($1,$2,$3::jsonb)',[fresh.held.orderId,intent,JSON.stringify(evidence)]));
assert.equal((await finalize()).status,'paid');assert.equal((await finalize()).idempotentReplay,true);
console.log('PASS paid recovery and finalization replay preserve original order despite stale code runtime');
for(const [i,context] of contexts.entries()){
 const offer=await makeSharedOffer(db,context,80+i),held=await sharedClaim(db,sharedRequest(context,offer,9200+i));assert.equal(held.total??held.amountCents,5500);
 console.log(`PASS original context ${context} admits5500 despite unavailable code runtime`);
}
console.log(JSON.stringify({state:'LOCAL_SYNTHETIC_PROVEN',full,server,checks:11,mailSends:0,hostedCalls:0,syntheticPaidRecovery:true,boundary:'materializer completion, not transaction commit'}));
