(() => {
  'use strict';
  const API='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/owner-access',KEY='landerwareOwnerSession';
  const params=new URLSearchParams(location.hash.slice(1));let accessToken=params.get('access')||'';
  // Remove the access credential before any network request or navigation.
  history.replaceState(null,'',location.pathname+location.search);
  const next=new URLSearchParams(location.search).get('next')||'/admin/instructor-workbench.html';
  const target=/^\/admin\/[a-z0-9-]+\.html(?:\?[^#]*)?$/.test(next)&&!next.startsWith('/admin/access.html')?next:'/admin/instructor-workbench.html';
  const status=document.getElementById('status'),help=document.getElementById('help'),retry=document.getElementById('retry');
  function save(s){try{localStorage.setItem(KEY,JSON.stringify(s));sessionStorage.removeItem(KEY)}catch{sessionStorage.setItem(KEY,JSON.stringify(s))}}
  async function enter(){
    retry.hidden=true;help.hidden=true;
    try{
      let saved,session;try{saved=localStorage.getItem(KEY)}catch{}try{session=JSON.parse(saved||sessionStorage.getItem(KEY)||'null')}catch{}
      if(!accessToken&&session?.token&&Date.parse(session.expiresAt)>Date.now()){
        const r=await fetch(API+'/session',{headers:{'X-LanderWare-Owner-Session':session.token},cache:'no-store',redirect:'error'});
        if(r.ok){location.replace(target);return}
        if(r.status!==401)throw Error('LanderWare could not be reached. Try again in a moment.');
        localStorage.removeItem(KEY);sessionStorage.removeItem(KEY);
      }
      if(!accessToken){status.textContent='Open your private access link to enter.';help.hidden=false;return}
      status.textContent='Opening your LanderWare workspace…';
      const r=await fetch(API+'/exchange',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({access_token:accessToken}),cache:'no-store',redirect:'error',referrerPolicy:'no-referrer'});
      const p=await r.json();if(!r.ok)throw Error(p.error||'LanderWare could not be reached.');
      if(!/^lw_s_[0-9a-f]{64}$/.test(p.token)||!(Date.parse(p.expiresAt)>Date.now()))throw Error('The sign-in response was incomplete. Please try again.');
      save(p);accessToken='';status.textContent='Signed in. Opening Class History…';location.replace(target);
    }catch(error){status.textContent=error.message||'LanderWare could not be reached. Please try again.';retry.hidden=false;help.hidden=!accessToken;}
  }
  retry.addEventListener('click',enter);enter();
})();
