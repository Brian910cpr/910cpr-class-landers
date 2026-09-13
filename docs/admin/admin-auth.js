(() => {
  'use strict';
  const KEY = 'hotSyncAdminKey';
  const HEADER = 'X-Hot-Sync-Admin-Key';
  const edge = 'https://wktwgcnwdvbebcobgyey.supabase.co';
  const functions = new Set(['owner-dashboard','canonical-session-workspace','class-registry','instructor-workbench','production-board']);
  const pending = new Set();
  let generation = 0;
  const get = () => sessionStorage.getItem(KEY) || '';
  const snapshot = () => ({generation, key:get()});
  const current = stamp => stamp.generation === generation && stamp.key === get();
  const expired = () => Object.assign(new Error('The admin session changed. Reload to continue.'), {name:'AbortError'});
  function invalidate(reason) {
    generation++;
    for (const controller of pending) controller.abort();
    pending.clear();
    window.dispatchEvent(new CustomEvent('admin-auth-lock', {detail:{reason}}));
  }
  function set(value) {
    value = String(value || '').trim();
    if (value === get()) return;
    if (value) sessionStorage.setItem(KEY,value); else sessionStorage.removeItem(KEY);
    invalidate('credential-changed');
  }
  function clear() { sessionStorage.removeItem(KEY); invalidate('locked'); }
  function allowed(value) {
    const url = new URL(value,location.href);
    if (url.username || url.password) return false;
    if (url.origin === 'https://schedule.910cpr.com') return url.pathname.startsWith('/admin/');
    if (url.origin !== edge) return false;
    const parts = url.pathname.split('/');
    return parts[1] === 'functions' && parts[2] === 'v1' && functions.has(parts[3]);
  }
  const headers = (contentType) => ({[HEADER]:get(), ...(contentType?{'Content-Type':contentType}:{})});
  async function request(url, options={}) {
    if (!allowed(url)) throw Error('Admin credentials are restricted to LanderWare admin services.');
    const stamp = snapshot();
    if (!stamp.key) throw Object.assign(new Error('Enter your LanderWare owner key.'),{status:401});
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (options.signal?.aborted) controller.abort();
    options.signal?.addEventListener('abort',abort,{once:true});
    pending.add(controller);
    const h = new Headers(options.headers || {});
    h.delete('x-maxim-session');
    h.delete('authorization');
    h.set(HEADER,stamp.key);
    const cleanup = () => {pending.delete(controller);options.signal?.removeEventListener('abort',abort);};
    try {
      const response = await fetch(url,{...options,cache:'no-store',redirect:'error',headers:h,signal:controller.signal});
      if (!current(stamp)) throw expired();
      if (response.status === 401 || response.status === 403) {
        clear();
        throw Object.assign(new Error('The owner key was not accepted. Enter it again.'),{status:response.status});
      }
      // Locking while a response body is arriving must not restore private content.
      for (const method of ['json','text','blob','arrayBuffer']) {
        const read = response[method].bind(response);
        response[method] = async () => {
          try {const value = await read();if (!current(stamp)) throw expired();return value;}
          finally {cleanup();}
        };
      }
      cleanup();
      return response;
    } catch (error) {cleanup();throw error;}
  }
  window.LanderWareAdminAuth = Object.freeze({get,set,clear,headers,fetch:request,snapshot,current,onLock:callback=>window.addEventListener('admin-auth-lock',callback)});
  // Discard rendered private state before a page can be stored in the back/forward cache.
  window.addEventListener('pagehide',()=>invalidate('page-hidden'));
  window.addEventListener('pageshow',event=>{if(event.persisted){invalidate('page-restored');window.dispatchEvent(new Event('admin-auth-refresh'));}});
})();
