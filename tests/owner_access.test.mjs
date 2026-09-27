import test from 'node:test';
import assert from 'node:assert/strict';
import {createOwnerAccessHandler} from '../supabase/functions/owner-access/handler.ts';
import {lookupOwnerSession,tokenHash} from '../supabase/functions/_shared/owner-session.ts';
const config={url:'https://database.example',key:'server-fixture'},access='lw_p_'+'a'.repeat(64),base='https://service.example/functions/v1/owner-access/';
const future=new Date(Date.now()+365*86400000).toISOString(),past='2020-01-01T00:00:00Z';
function database(){
 const grant={id:'00000000-0000-4000-8000-000000000001',owner_email:'owner@example.com',owner_name:'Owner',expires_at:future,revoked_at:null};let row=null;
 const send=async(url,options={})=>{const u=new URL(url),name=u.pathname.split('/').pop(),hash=u.searchParams.get('token_sha256');
  if(name==='owner_access_grants')return Response.json(hash==='eq.'+await tokenHash(access)?[grant]:[]);
  if(name==='owner_browser_sessions'){
   if(options.method==='POST'){row={...JSON.parse(options.body),id:'00000000-0000-4000-8000-000000000002',revoked_at:null};return Response.json([row])}
   if(options.method==='PATCH'){Object.assign(row,JSON.parse(options.body));return Response.json([row])}
   return Response.json(row&&hash==='eq.'+row.token_sha256?[{...row,grant}]:[]);
  }throw Error('unexpected route');
 };return {grant,send,row:()=>row};
}
const post=(path,body,token)=>new Request(base+path,{method:'POST',headers:{origin:'https://www.910cpr.com','content-type':'application/json',...(token?{'x-landerware-owner-session':token}:{})},body:JSON.stringify(body)});
test('exchange creates a hashed browser session, refresh extends it, logout revokes it',async()=>{const db=database(),handler=createOwnerAccessHandler(config,db.send);const r=await handler(post('exchange',{access_token:access}));assert.equal(r.status,200);const s=await r.json();assert.match(s.token,/^lw_s_[0-9a-f]{64}$/);assert.equal(db.row().token_sha256,await tokenHash(s.token));assert.ok(!JSON.stringify(db.row()).includes(s.token));assert.equal((await lookupOwnerSession(s.token,config,db.send)).grant.owner_name,'Owner');assert.equal((await handler(post('refresh',{},s.token))).status,200);assert.equal((await handler(post('logout',{},s.token))).status,200);assert.equal(await lookupOwnerSession(s.token,config,db.send),null)});
test('wrong, malformed, expired, and revoked links cannot create a session',async()=>{for(const change of ['wrong','malformed','expired','revoked']){const db=database();if(change==='expired')db.grant.expires_at=past;if(change==='revoked')db.grant.revoked_at=new Date().toISOString();const token=change==='wrong'?'lw_p_'+'b'.repeat(64):change==='malformed'?'bad':access;assert.equal((await createOwnerAccessHandler(config,db.send)(post('exchange',{access_token:token}))).status,401);assert.equal(db.row(),null)}});
test('grant revocation and session expiry immediately deny subsequent requests',async()=>{for(const condition of ['grant','session']){const db=database(),h=createOwnerAccessHandler(config,db.send),s=await(await h(post('exchange',{access_token:access}))).json();if(condition==='grant')db.grant.revoked_at=new Date().toISOString();else db.row().expires_at=past;assert.equal(await lookupOwnerSession(s.token,config,db.send),null)}});
test('anonymous requests and hostile origins are denied; preflight permits only the first-party header',async()=>{const h=createOwnerAccessHandler(config,()=>assert.fail('no database call'));assert.equal((await h(new Request(base+'session'))).status,401);assert.equal((await h(new Request(base+'session',{headers:{origin:'https://evil.example'}}))).status,403);const r=await h(new Request(base+'session',{method:'OPTIONS',headers:{origin:'https://www.910cpr.com'}}));assert.equal(r.status,204);assert.match(r.headers.get('access-control-allow-headers'),/x-landerware-owner-session/);assert.match(r.headers.get('cache-control'),/no-store/)});
test('database outages fail closed without leaking underlying error text',async()=>{const h=createOwnerAccessHandler(config,async()=>Response.json({message:'private database detail'},{status:500}));const r=await h(post('exchange',{access_token:access}));assert.equal(r.status,503);assert.doesNotMatch(await r.text(),/private database detail/)});
