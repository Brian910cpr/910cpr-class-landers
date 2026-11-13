import assert from 'node:assert/strict';
import {proveLocalRecoveryCapture} from './local-native-mail-capture.mjs';
import {readFileSync,realpathSync,statSync} from 'node:fs';
import {homedir} from 'node:os';
import {resolve,sep,join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHmac} from 'node:crypto';
import {proveCombinedCheckout} from './combined-checkout-proof.mjs';
import {adaptLocalSupabaseFixture,localSupabaseFixtureAdmission} from './helpers/local-supabase-fixture-plan.mjs';
let raw;try{raw=JSON.parse(readFileSync(process.argv[2],'utf8'));}catch{throw Error('invalid_private_stack_metadata');}
const env=raw.env||raw.environment||raw,api=new URL(env.API_URL||env.SUPABASE_URL),target=new URL(env.DB_URL||env.DATABASE_URL);
for(const u of [api,target])assert(['127.0.0.1','localhost','[::1]'].includes(u.hostname),'loopback stack required');
assert.equal(api.protocol,'http:');assert(['postgres:','postgresql:'].includes(target.protocol));
const key=env.SERVICE_ROLE_KEY||env.SECRET_KEY,anon=env.ANON_KEY||env.PUBLISHABLE_KEY;
for(const value of [key,anon,decodeURIComponent(target.password)])if(value)console.log('::add-mask::'+value);
const headers={apikey:key,authorization:'Bearer '+key};
const request=(path,options={})=>fetch(api.origin+path,{...options,signal:AbortSignal.timeout(30000)});
assert.equal((await request('/storage/v1/bucket',{method:'POST',headers:{...headers,'content-type':'application/json'},body:JSON.stringify({id:'class-session-docs',name:'class-session-docs',public:false})})).status,200);
const processEnv={...process.env};for(const name of Object.keys(processEnv))if(/^PG/i.test(name))delete processEnv[name];
Object.assign(processEnv,{PGPASSWORD:decodeURIComponent(target.password),PGPASSFILE:'/dev/null',PGCONNECT_TIMEOUT:'3'});
const sql=text=>{const p=spawnSync('psql',['-X','-w','-q','-t','-A','-h',target.hostname,'-p',target.port||'5432','-U',decodeURIComponent(target.username),'-d',target.pathname.slice(1),'-v','ON_ERROR_STOP=1'],{env:processEnv,input:text,encoding:'utf8',maxBuffer:16*1024*1024});if(p.status!==0)throw Error('isolated_sql_failed: '+String(p.stderr).split('\n').filter(x=>/ERROR:/.test(x)).join(' ').slice(0,250));return p.stdout.trim();};
const quote=x=>x==null?'null':typeof x==='number'?String(x):"'"+String(x).replaceAll("'","''")+"'";
const db={exec:async text=>sql(text),query:async(text,args=[])=>{text=text.replace(/\$(\d+)\b/g,(_,n)=>quote(args[Number(n)-1])).trim().replace(/;$/,'');const result=sql(`select row_to_json(q) from (${text}) q;`);return{rows:result?result.split('\n').filter(x=>x.startsWith('{')).map(x=>JSON.parse(x)):[]};}};
const backend=(await db.query("select host(inet_server_addr()) as address,current_setting('data_directory') as directory")).rows[0];
let verifiedNativeSocket=false;
if(backend.address===null){
 assert.equal(raw.runtime,'native','Unix socket requires native CLI runtime');
 const directory=realpathSync(backend.directory);
 const roots=[resolve(process.env.SUPABASE_HOME,'stacks'),resolve(homedir(),'.supabase/stacks')];
 assert(roots.some(root=>directory.startsWith(root+sep)),'native data directory outside disposable stack roots');
 assert.equal(statSync(directory).uid,process.getuid(),'native database must belong to runner');
 const pid=Number(readFileSync(join(directory,'postmaster.pid'),'utf8').split('\n')[0]);assert(Number.isSafeInteger(pid)&&pid>1);
 assert.equal(statSync('/proc/'+pid).uid,process.getuid());
 const executable=realpathSync('/proc/'+pid+'/exe');
 const caches=[resolve(process.env.SUPABASE_HOME,'cache/stack'),resolve(homedir(),'.supabase/cache/stack')];
 assert(caches.some(root=>executable.startsWith(root+sep)),'PostgreSQL executable must come from verified native stack cache');
 const args=readFileSync('/proc/'+pid+'/cmdline','utf8').split('\0');
 assert(args.includes(backend.directory)||args.includes(directory),'process must own exact database directory');
 verifiedNativeSocket=true;
}
await db.exec(localSupabaseFixtureAdmission({verifiedNativeSocket}));
const authCount=sql('select count(*) from auth.users;');
await proveCombinedCheckout(db,null,{fixtureTransform:adaptLocalSupabaseFixture,seedOnly:true});
assert.equal(sql('select count(*) from auth.users;'),authCount,'application fixtures must preserve auth');
assert.equal(sql('select count(*) from landerware_public_orders;'),'0','seed contains no orders or payment evidence');
// Schema-only fixture lacks FKs. Add the exact canonical joins needed by PostgREST.
await db.exec(`alter table class_sessions add constraint class_sessions_course_id_fkey foreign key(course_id) references courses(id);
 alter table class_sessions add constraint class_sessions_location_id_fkey foreign key(location_id) references locations(id);
 alter table class_sessions add constraint class_sessions_lead_instructor_id_fkey foreign key(lead_instructor_id) references people(id);
 alter table landerware_public_order_students add constraint landerware_public_order_students_order_id_fkey foreign key(order_id) references landerware_public_orders(id);
 notify pgrst,'reload schema';`);
const path='/functions/v1/public-registration/generic/',selection={course:'209806',session:'lw-22222222-2222-4222-8222-222222222222'};
const getForm=()=>request(path+'form?'+new URLSearchParams(selection),{headers:{apikey:anon}});
let response,model;
for(let n=0;n<30;n++){try{response=await getForm();model=await response.json();if(response.ok&&model.ok)break;}catch{}await new Promise(resolve=>setTimeout(resolve,1000));}
assert.equal(response?.status,200,'actual Edge form: '+String(model?.error||'unavailable'));assert.equal(model.profile.baseCents,7500);assert.equal(model.selection.course,'209806');
const idempotency='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
const body={selection,profileKey:model.profile.profileKey,profileVersion:model.profile.profileVersion,students:[{fields:{first_name:'Synthetic',last_name:'Fixture',email:'edge-fixture@example.invalid',phone:'2025550100'},selectedChoices:['own_copy','no_first_aid']}]};
const reserve=()=>request(path+'reserve',{method:'POST',headers:{apikey:anon,'content-type':'application/json','idempotency-key':idempotency},body:JSON.stringify(body)});
response=await reserve();let result=await response.json();assert.equal(response.status,200,'actual Edge reserve: '+String(result.error||''));assert.equal(result.receipt.amountCents,7500);assert.equal(result.receipt.status,'held');const order=result.receipt.orderId;
response=await reserve();result=await response.json();assert.equal(response.status,200);assert.equal(result.receipt.orderId,order);assert.equal(sql('select count(*) from landerware_public_orders;'),'1','retry must not create a second hold');
const restore=await request(path+'form',{headers:{apikey:anon,'idempotency-key':idempotency}});assert.equal(restore.status,200,'actual Edge saved form recovery');
const tamper=await request(path+'reserve',{method:'POST',headers:{apikey:anon,'content-type':'application/json','idempotency-key':'cccccccc-cccc-4ccc-8ccc-cccccccccccc'},body:JSON.stringify({...body,profileVersion:body.profileVersion+1})});assert.equal(tamper.status,400);assert.equal((await tamper.json()).error,'profile_changed');
console.log('PASS: actual candidate Edge + PostgREST + PostgreSQL bootstrap/form/$75 hold/idempotent retry/saved recovery/profile-change rejection.');
// No test credential is supplied: fail honestly rather than charge or invent payment.
const payment=await request(path+'checkout',{method:'POST',headers:{apikey:anon,'content-type':'application/json','idempotency-key':idempotency},body:'{}'});assert.equal(payment.status,500);assert.equal((await payment.json()).error,'stripe_unavailable');
assert.equal(sql('select count(*) from registrations;'),'0','unpaid hold is not registration');
assert.equal(sql("select count(*) from landerware_public_orders where status='paid' or stripe_checkout_session_id is not null or payment_evidence<>'{}'::jsonb;"),'0','no processor receipt or paid-state fabrication');
console.log('PASS: missing Stripe credential fails closed; no paid registration or processor evidence fabricated.');
console.log('NOT RUN: real Stripe test payment/webhook and confirmation delivery; secure test runtime/provider bindings absent.');

const actualRpc=async(name,body)=>{
 assert(/^[a-z_]+$/.test(name));
 const response=await request('/rest/v1/rpc/'+name,{method:'POST',headers:{...headers,'content-type':'application/json'},body:JSON.stringify(body)});
 assert.equal(response.status,200,'isolated notification RPC '+name);return response.json();
};
await proveLocalRecoveryCapture({orderId:order,sql,rpc:actualRpc});

const webhookSecret=readFileSync(process.argv[3],'utf8').split('\n').find(x=>x.startsWith('STRIPE_WEBHOOK_SECRET='))?.slice('STRIPE_WEBHOOK_SECRET='.length);
assert(/^whsec_local_[a-f0-9]{64}$/.test(webhookSecret||''),'generated local signing binding required');console.log('::add-mask::'+webhookSecret);
const rawEvent=JSON.stringify({id:'evt_local_synthetic_unpaid',type:'checkout.session.completed',livemode:false,data:{object:{id:'cs_test_local_synthetic',mode:'payment',payment_status:'unpaid',livemode:false}}});
const stamp=String(Math.floor(Date.now()/1000));
const signature=createHmac('sha256',webhookSecret).update(stamp+'.'+rawEvent).digest('hex');
const webhook=(value)=>request('/functions/v1/stripe-registration-webhook',{method:'POST',headers:{'content-type':'application/json','stripe-signature':value},body:rawEvent});
let invalid;for(let n=0;n<30;n++){try{invalid=await webhook('t='+stamp+',v1=invalid');if(invalid.status===400)break;}catch{}await new Promise(resolve=>setTimeout(resolve,1000));}
if(invalid?.status!==400){
 const log=readFileSync(join(process.env.RUNNER_TEMP,'checkout-functions-private.log'),'utf8');
 const markers=[['remote_import',/import|module|dependency/i],['esm_dependency',/esm\.sh/],['tls_certificate',/certificate|UnknownIssuer|TLS/i],['network_fetch',/fetch|network|connection|dns/i],['missing_service_key',/supabaseKey is required|supabaseUrl is required/],['boot_failure',/boot|worker/i]].filter(([,pattern])=>pattern.test(log)).map(([name])=>name);
 console.log('SAFE webhook startup categories: '+markers.join(','));
 // Only dependency/startup error lines; remove every generated credential first.
 const privateValues=[];
 const collect=value=>{if(typeof value==='string'&&value.length>=16)privateValues.push(value);else if(value&&typeof value==='object')for(const child of Object.values(value))collect(child);};collect(raw);privateValues.push(webhookSecret);
 const diagnostics=[];
 for(let line of log.split('\n')){
  if(!/\b(?:Error|SyntaxError|TypeError|ReferenceError):|worker boot error|Module not found|does not provide an export/.test(line))continue;
  for(const value of privateValues)line=line.split(value).join('<private>');
  if(/secret|token|authorization|api.?key|eyJ|whsec_|sb_secret_/i.test(line))continue;
  line=line.replace(/\x1b\[[0-9;]*m/g,'').replace(/\/home\/runner\/[^\s:]+/g,'<runtime>');
  if(!diagnostics.includes(line))diagnostics.push(line.slice(0,350));
  if(diagnostics.length===4)break;
 }
 for(const line of diagnostics)console.log('SAFE dependency error: '+line);

 const body=await invalid?.json().catch(()=>({}));if(/^[A-Z_]{3,50}$/.test(body?.code||''))console.log('SAFE webhook response code: '+body.code);
}
assert.equal(invalid?.status,400,'actual webhook must reject invalid signature');
const signed=await webhook('t='+stamp+',v1='+signature);assert.equal(signed.status,200,'actual webhook must accept locally signed unpaid event');assert.equal((await signed.json()).ok,true);
assert.equal(sql("select count(*) from landerware_public_orders where status='paid' or payment_evidence<>'{}'::jsonb;"),'0');
assert.equal(sql('select count(*) from registrations;'),'0');
console.log('PASS: actual webhook handler/local signing binding rejects invalid signature and safely ignores valid synthetic unpaid event.');
console.log('NOT PROVEN: Stripe-origin delivery, real test payment settlement or paid-class confirmation.');
