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
});
console.log(JSON.stringify({state:'LOCAL_PROVEN',server,hostedCalls:0,payments:0,mailSends:0,activation:false}));
