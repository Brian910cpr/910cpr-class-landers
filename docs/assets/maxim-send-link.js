(() => {
  const API = 'https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/maxim-scheduler';
  const DEFAULT_SENDER = 'WilmingtonNCoffice@maxhealth.com';

  function headers() {
    const h = {'content-type':'application/json'};
    const token = sessionStorage.getItem('maximPortalSession');
    if (token) h['x-maxim-session'] = token;
    return h;
  }
  function esc(v){return String(v||'').replace(/[<>&"]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c]));}
  function dateOnly(v){const m=String(v||'').match(/^(\d{4})-(\d{2})-(\d{2})/);return m?`${m[2]}/${m[3]}/${m[1]}`:String(v||'');}

  function ensureUi(){
    if(document.getElementById('maximSendModal')) return;
    const style=document.createElement('style');
    style.textContent=`
      .mx-send-backdrop{display:none;position:fixed;inset:0;z-index:90;background:rgba(2,8,23,.72);place-items:center;padding:18px}.mx-send-backdrop.open{display:grid}
      .mx-send-card{width:min(560px,96vw);background:#111827;color:#e5eef9;border:1px solid #334155;border-radius:14px;box-shadow:0 24px 70px rgba(0,0,0,.45);padding:20px}
      .mx-send-card h2{margin:0 0 5px;font-size:22px}.mx-send-muted{color:#9fb0c4}.mx-send-summary{margin:15px 0;display:grid;grid-template-columns:130px 1fr;gap:7px 12px;padding:12px;background:#0b1220;border:1px solid #263448;border-radius:10px}.mx-send-summary b{color:#9fb0c4}.mx-send-card label{display:block;font-weight:700;margin-top:12px}.mx-send-card input{width:100%;margin-top:5px;padding:10px;border-radius:8px;border:1px solid #475569;background:#0b1220;color:#fff}.mx-send-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}.mx-send-actions button{border:1px solid #475569;border-radius:8px;padding:8px 12px;cursor:pointer;background:#172033;color:#e5eef9}.mx-send-actions .primary{background:#1577b8;border-color:#2388ca;color:#fff;font-weight:700}.mx-send-result{display:none;margin-top:13px;padding:10px 12px;border-radius:9px}.mx-send-result.ok{display:block;background:#123626;border:1px solid #2e7d57;color:#c8f6df}.mx-send-result.bad{display:block;background:#431d22;border:1px solid #91404b;color:#ffd7dc}.mx-toast{position:fixed;right:18px;bottom:18px;z-index:120;background:#123626;color:#d9fbe8;border:1px solid #2e7d57;border-radius:10px;padding:12px 14px;box-shadow:0 10px 30px rgba(0,0,0,.3);font-weight:700}
    `;
    document.head.appendChild(style);
    const wrap=document.createElement('div');
    wrap.id='maximSendModal';wrap.className='mx-send-backdrop';wrap.innerHTML=`<section class="mx-send-card" role="dialog" aria-modal="true" aria-labelledby="mxSendTitle"><h2 id="mxSendTitle">Send scheduling link</h2><div class="mx-send-muted">Confirm exactly who will receive this before anything is sent.</div><div class="mx-send-summary" id="mxSendSummary"></div><label>Maxim confirmation copy<input id="mxSenderCopy" type="email" value="${DEFAULT_SENDER}"></label><div class="mx-send-muted" style="margin-top:5px">Leave the Wilmington shared office address, replace it with your own, or delete it completely. The employee email still goes out from brian@910cpr.com, with info@910cpr.com BCC'd.</div><div id="mxSendResult" class="mx-send-result"></div><div class="mx-send-actions"><button type="button" id="mxSendCancel">Cancel</button><button type="button" class="primary" id="mxSendConfirm">Send link</button></div></section>`;
    document.body.appendChild(wrap);
    document.getElementById('mxSendCancel').onclick=()=>wrap.classList.remove('open');
    wrap.addEventListener('click',e=>{if(e.target===wrap)wrap.classList.remove('open')});
  }
  function toast(text){const t=document.createElement('div');t.className='mx-toast';t.textContent=text;document.body.appendChild(t);setTimeout(()=>t.remove(),5000);}

  async function liveSend(id){
    const person = typeof trainingFlow!=='undefined' ? trainingFlow.find(p=>p.id===id) : null;
    if(!person) return;
    ensureUi();
    const modal=document.getElementById('maximSendModal');
    const result=document.getElementById('mxSendResult');
    const sender=document.getElementById('mxSenderCopy');
    const confirm=document.getElementById('mxSendConfirm');
    sender.value=DEFAULT_SENDER;
    result.className='mx-send-result';result.textContent='';
    document.getElementById('mxSendSummary').innerHTML=`<b>Employee</b><span>${esc(person.name)}</span><b>Employee email</b><span>${esc(person.email||'MISSING')}</span><b>Training</b><span>${esc(person.course)}</span><b>Renew by</b><span>${esc(dateOnly(person.expirationDate))}</span><b>Billing</b><span>Maxim ${esc(person.billing)}</span><b>Link</b><span>Secure employee-specific LanderWare scheduling page</span>`;
    modal.classList.add('open');
    confirm.disabled=false;confirm.textContent='Send link';
    confirm.onclick=async()=>{
      confirm.disabled=true;confirm.textContent='Sending…';result.className='mx-send-result';
      try{
        const res=await fetch(API+'/send-link',{method:'POST',headers:headers(),body:JSON.stringify({employeeId:id,senderCopy:sender.value.trim()})});
        const data=await res.json().catch(()=>({}));
        if(!res.ok) throw new Error(data.error||'Send failed');
        person.linkSentDate=data.linkSentDate;person.stage=data.workflowStage;
        if(typeof renderTrainingFlow==='function') renderTrainingFlow();
        result.className='mx-send-result ok';
        result.textContent=`✓ Sent to ${data.to}${data.senderCopy?` · confirmation to ${data.senderCopy}`:''}`+(data.copyWarning?` · office-copy warning: ${data.copyWarning}`:'');
        toast(`✓ Scheduling link sent to ${person.name}`);
        setTimeout(()=>modal.classList.remove('open'),1800);
      }catch(err){
        result.className='mx-send-result bad';result.textContent='NOT SENT: '+err.message;
      }finally{confirm.disabled=false;confirm.textContent='Send link';}
    };
  }

  window.addEventListener('DOMContentLoaded',()=>{
    ensureUi();
    window.emailScheduleLink=liveSend;
    const note=document.querySelector('#registerBox .muted');
    if(note) note.textContent='No payment or promo code is needed. Send Link now sends a secure employee-specific scheduling page and records the send only after successful delivery.';
  });
})();