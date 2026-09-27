export const OWNER_SESSION_HEADER = 'x-landerware-owner-session';
export const SESSION_DAYS = 30;
export type OwnerConfig = {url:string; key:string};
export function ownerConfig():OwnerConfig {
  const secret = Deno.env.get('SUPABASE_SECRET_KEYS');
  const key = secret ? JSON.parse(secret).default : Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  const url = Deno.env.get('SUPABASE_URL');
  if (!key || !url) throw Object.assign(Error('Owner access is temporarily unavailable.'), {status:503});
  return {url,key};
}
export async function tokenHash(value:string):Promise<string> {
  const bytes = await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value));
  return Array.from(new Uint8Array(bytes),b=>b.toString(16).padStart(2,'0')).join('');
}
export function newToken(prefix:string):string {
  const bytes=crypto.getRandomValues(new Uint8Array(32));
  return prefix+Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
}
export async function ownerRest(path:string,init:RequestInit={},config=ownerConfig(),send:typeof fetch=fetch) {
  let response:Response;
  try {
    response=await send(`${config.url}/rest/v1/${path}`,{...init,redirect:'error',signal:AbortSignal.timeout(15000),headers:{apikey:config.key,authorization:`Bearer ${config.key}`,'content-type':'application/json',prefer:'return=representation',...Object.fromEntries(new Headers(init.headers).entries())}});
  } catch {throw Object.assign(Error('Owner access is temporarily unavailable.'),{status:503});}
  if(!response.ok)throw Object.assign(Error('Owner access is temporarily unavailable.'),{status:503});
  const text=await response.text();return text?JSON.parse(text):null;
}
export function unexpired(value:unknown,now=Date.now()):boolean {
  return typeof value==='string' && Number.isFinite(Date.parse(value)) && Date.parse(value)>now;
}
export async function lookupOwnerSession(token:string,config=ownerConfig(),send:typeof fetch=fetch,now=Date.now()) {
  if(!/^lw_s_[0-9a-f]{64}$/.test(token))return null;
  const hash=await tokenHash(token);
  const rows=await ownerRest(`owner_browser_sessions?token_sha256=eq.${hash}&revoked_at=is.null&select=id,expires_at,revoked_at,grant:owner_access_grants!inner(id,owner_email,owner_name,expires_at,revoked_at)&limit=1`,{},config,send);
  if(!Array.isArray(rows)||rows.length!==1)return null;
  const row=rows[0],grant=row.grant;
  if(row.revoked_at||!unexpired(row.expires_at,now)||!grant||grant.revoked_at||!unexpired(grant.expires_at,now))return null;
  return row;
}
