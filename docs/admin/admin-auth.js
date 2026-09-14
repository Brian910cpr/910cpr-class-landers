(() => {
  'use strict';
  const KEY='landerwareOwnerSession',HEADER='X-LanderWare-Owner-Session';
  const EDGE='https://wktwgcnwdvbebcobgyey.supabase.co',ACCESS=EDGE+'/functions/v1/owner-access';
  const services=new Set(['owner-access','owner-dashboard','canonical-session-workspace','class-registry','instructor-workbench','production-board']);
  const pending=new Set();let generation=0,refreshing=null,leaving=false;
  function read(){let value;try{value=localStorage.getItem(KEY)}catch{}try{return JSON.parse(value||sessionStorage.getItem(KEY)||'null')}catch{return null}}
  function save(session){try{localStorage.setItem(KEY,JSON.stringify(session));sessionStorage.removeItem(KEY)}catch{sessionStorage.setItem(KEY,JSON.stringify(session))}}
  function get(){const s=read();return s&&/^lw_s_[0-9a-f]{64}$/.test(s.token)&&Date.parse(s.expiresAt)>Date.now()?s.token:''}
  const snapshot=()=>({generation,key:get()});
  const current=stamp=>stamp.generation===generation&&stamp.key===get();
  const expired=()=>Object.assign(Error('Your sign-in changed. Open this page again.'),{name:'AbortError'});
  function signIn(){if(leaving)return;leaving=true;const next=location.pathname+location.search;location.replace('/admin/access.html?next='+encodeURIComponent(next))}
  function invalidate(reason){generation++;for(const c of pending)c.abort();pending.clear();window.dispatchEvent(new CustomEvent('admin-auth-lock',{detail:{reason}}))}
  function forget(){try{localStorage.removeItem(KEY)}catch{}sessionStorage.removeItem(KEY);sessionStorage.removeItem('hotSyncAdminKey');invalidate('signed-out')}
  function clear(){const token=get();forget();if(token)fetch(ACCESS+'/logout',{method:'POST',headers:{[HEADER]:token},cache:'no-store',redirect:'error',keepalive:true}).catch(()=>{});signIn()}
  function allowed(value){const url=new URL(value,location.href);if(url.username||url.password)return false;if(url.origin==='https://schedule.910cpr.com')return url.pathname.startsWith('/admin/');const p=url.pathname.split('/');return url.origin===EDGE&&p[1]==='functions'&&p[2]==='v1'&&services.has(p[3])}
  async function refresh(){
    const s=read();if(!get()||Date.parse(s.expiresAt)-Date.now()>7*86400000)return;
    if(refreshing)return refreshing;
    refreshing=(async()=>{const stamp=snapshot();try{const r=await fetch(ACCESS+'/refresh',{method:'POST',headers:{[HEADER]:stamp.key},cache:'no-store',redirect:'error'});if(!current(stamp))throw expired();if(r.status===401){forget();signIn();throw expired()}if(r.ok){const p=await r.json();if(current(stamp)&&Date.parse(p.expiresAt)>Date.now())save({...s,expiresAt:p.expiresAt})}}finally{refreshing=null}})();return refreshing;
  }
  async function request(url,options={}){
    if(!allowed(url))throw Error('Owner access is restricted to LanderWare services.');
    if(!get()){signIn();throw Object.assign(Error('Open your private LanderWare access link.'),{status:401})}
    await refresh();
    const stamp=snapshot(),controller=new AbortController(),abort=()=>controller.abort();
    if(options.signal?.aborted)controller.abort();options.signal?.addEventListener('abort',abort,{once:true});pending.add(controller);
    const h=new Headers(options.headers||{});h.delete('authorization');h.delete('x-maxim-session');h.delete('x-hot-sync-admin-key');h.delete(HEADER);
    const legacy=new URL(url,location.href).origin==='https://schedule.910cpr.com';
    if(legacy){const key=sessionStorage.getItem('hotSyncAdminKey');if(!key){pending.delete(controller);options.signal?.removeEventListener('abort',abort);throw Object.assign(Error('This older service is not connected to owner access yet. Your sign-in is still active.'),{status:503})}h.set('X-Hot-Sync-Admin-Key',key)}else h.set(HEADER,stamp.key);
    const cleanup=()=>{pending.delete(controller);options.signal?.removeEventListener('abort',abort)};
    try{
      const r=await fetch(url,{...options,cache:'no-store',redirect:'error',headers:h,signal:controller.signal});
      if(!current(stamp))throw expired();
      if(r.status===401){if(legacy)throw Object.assign(Error('This older service needs its connection repaired. Your sign-in is still active.'),{status:503});forget();signIn();throw Object.assign(Error('Open your private LanderWare access link to sign in again.'),{status:401})}
      for(const method of ['json','text','blob','arrayBuffer']){const original=r[method].bind(r);r[method]=async()=>{try{const value=await original();if(!current(stamp))throw expired();return value}finally{cleanup()}}}
      cleanup();return r;
    }catch(error){cleanup();throw error}
  }
  window.LanderWareAdminAuth=Object.freeze({get,clear,headers:contentType=>({[HEADER]:get(),...(contentType?{'Content-Type':contentType}:{})}),fetch:request,snapshot,current,onLock:callback=>window.addEventListener('admin-auth-lock',callback),set:value=>{if(value!==get())throw Error('Use your private access link to sign in.')}});
  window.addEventListener('storage',event=>{if(event.key===KEY){invalidate('sign-in-changed');if(!get())signIn();else window.dispatchEvent(new Event('admin-auth-refresh'))}});
  window.addEventListener('pagehide',()=>invalidate('page-hidden'));
  window.addEventListener('pageshow',event=>{if(event.persisted){if(!get())signIn();else window.dispatchEvent(new Event('admin-auth-refresh'))}});
  if(!get())signIn();
})();
