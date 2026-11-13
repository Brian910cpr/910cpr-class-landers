import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const raw=JSON.parse(readFileSync(process.argv[2],'utf8'));
const env=raw.env||raw.environment||raw;
const base=env.API_URL||env.SUPABASE_URL||raw.endpoints?.api?.url||raw.endpoints?.rest?.url;
assert(base,'local API URL missing from stack JSON');
const url=new URL(base);assert(['127.0.0.1','localhost','[::1]'].includes(url.hostname),'loopback API required');
assert.equal(url.protocol,'http:');
const origin=url.origin;
const service=env.SERVICE_ROLE_KEY||env.SECRET_KEY,anon=env.ANON_KEY||env.PUBLISHABLE_KEY;
assert(service&&anon,'generated local credentials required');
// Mask before any request; never log response bodies or credential-bearing JSON.
for(const secret of [service,anon])console.log('::add-mask::'+secret);
const request=async(path,options={})=>fetch(origin+path,{...options,signal:AbortSignal.timeout(30000)});
const auth=await request('/auth/v1/settings',{headers:{apikey:anon}});assert.equal(auth.status,200,'local Auth settings');
const rest=await request('/rest/v1/',{headers:{apikey:service,authorization:'Bearer '+service}});assert.equal(rest.status,200,'local PostgREST');
const bucket='checkout-fixture-'+String(process.env.GITHUB_RUN_ID||'local').replace(/[^a-z0-9-]/gi,'');
const headers={apikey:service,authorization:'Bearer '+service};
const create=await request('/storage/v1/bucket',{method:'POST',headers:{...headers,'content-type':'application/json'},body:JSON.stringify({id:bucket,name:bucket,public:false})});assert.equal(create.status,200,'create synthetic private bucket');
const object='synthetic-proof.txt',bytes='SYNTHETIC CHECKOUT STORAGE PROOF - NO CUSTOMER DATA';
try{
 const upload=await request('/storage/v1/object/'+bucket+'/'+object,{method:'POST',headers:{...headers,'content-type':'text/plain'},body:bytes});assert.equal(upload.status,200,'private synthetic upload');
 const read=await request('/storage/v1/object/authenticated/'+bucket+'/'+object,{headers});assert.equal(read.status,200,'owned private download');assert.equal(await read.text(),bytes);
 const publicRead=await request('/storage/v1/object/public/'+bucket+'/'+object);assert.notEqual(publicRead.status,200,'private document must not be public');
 const anonymous=await request('/storage/v1/object/authenticated/'+bucket+'/'+object,{headers:{apikey:anon,authorization:'Bearer '+anon}});assert.notEqual(anonymous.status,200,'anonymous document access rejected');
 const remove=await request('/storage/v1/object/'+bucket,{method:'DELETE',headers:{...headers,'content-type':'application/json'},body:JSON.stringify({prefixes:[object]})});assert.equal(remove.status,200,'remove only synthetic object');
 console.log('PASS: real local Auth, PostgREST, private upload/download, anonymous denial and synthetic object cleanup.');
 console.log('NOT RUN: application checkout, Stripe hosted payment/webhook, confirmation delivery.');
}finally{
 // Bucket is unique to this newly-created disposable stack/run.
 await request('/storage/v1/bucket/'+bucket+'/empty',{method:'POST',headers});
 await request('/storage/v1/bucket/'+bucket,{method:'DELETE',headers});
}
