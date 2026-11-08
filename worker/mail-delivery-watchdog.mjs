// Uses the existing same-repository Actions token. Never stores mail contents or recipients.
export const MAIL_WORKFLOW='https://api.github.com/repos/Brian910cpr/910cpr-class-landers/actions/workflows/reschedule-confirmations.yml';
export const MAIL_STATE_KEY='mail-delivery-watchdog';
const MINUTE=60_000;
export async function checkMailDelivery(env,{now=Date.now(),request=fetch}={}){
 const previous=await env.STATE.get(MAIL_STATE_KEY,'json')||{};
 const state={checkedAt:new Date(now).toISOString(),lastDispatchAttemptAt:previous.lastDispatchAttemptAt||null,lastSuccessAt:previous.lastSuccessAt||null};
 try{
  if(!env.GITHUB_ACTIONS_TOKEN)throw Error('github_token_missing');
  const headers={Authorization:`Bearer ${env.GITHUB_ACTIONS_TOKEN}`,Accept:'application/vnd.github+json','User-Agent':'910cpr-mail-watchdog','X-GitHub-Api-Version':'2022-11-28'};
  const options={signal:AbortSignal.timeout(20_000),redirect:'error',headers};
  const response=await request(`${MAIL_WORKFLOW}/runs?branch=main&per_page=10`,options);
  if(!response.ok)throw Error(`mail_runs_http_${response.status}`);
  const text=await response.text();if(text.length>1024*1024)throw Error('mail_runs_too_large');
  const runs=JSON.parse(text).workflow_runs;if(!Array.isArray(runs))throw Error('invalid_mail_runs');
  const success=runs.filter(r=>r.status==='completed'&&r.conclusion==='success').sort((a,b)=>Date.parse(b.updated_at)-Date.parse(a.updated_at))[0];
  if(success){state.lastSuccessAt=success.updated_at;state.lastSuccessRunId=success.id;}
  const active=runs.find(r=>r.status!=='completed');
  if(active){
   state.action='delivery_running';state.runId=active.id;
   if(now-Date.parse(active.created_at)>15*MINUTE)state.error='mail_delivery_stalled';
  }else if(now-Date.parse(previous.lastDispatchAttemptAt)<5*MINUTE-30_000){state.action='dispatch_cooldown';}
  else if(success&&now-Date.parse(success.updated_at)<2*MINUTE){state.action='recent_delivery_run';}
  else{
   // Persist the attempt before requesting dispatch. A timeout has uncertain
   // outcome and must not cause an immediate duplicate request.
   state.lastDispatchAttemptAt=state.checkedAt;state.action='dispatch_attempt';
   await env.STATE.put(MAIL_STATE_KEY,JSON.stringify(state));
   const dispatched=await request(`${MAIL_WORKFLOW}/dispatches`,{...options,method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({ref:'main'})});
   if(dispatched.status!==204)throw Error(`mail_dispatch_http_${dispatched.status}`);
   state.action='delivery_dispatched';
  }
 }catch(error){
  const allowed=/^(github_token_missing|invalid_mail_runs|mail_runs_too_large|mail_runs_http_\d{3}|mail_dispatch_http_\d{3})$/;
  state.error=allowed.test(error?.message)?error.message:'mail_check_failed';
 }
 await env.STATE.put(MAIL_STATE_KEY,JSON.stringify(state));
 console.log(JSON.stringify({event:'mail_delivery_watchdog',...state}));
 return state;
}
export function mailHealth(state,now=Date.now()){
 const checked=Date.parse(state?.checkedAt),success=Date.parse(state?.lastSuccessAt);
 const heartbeatStale=!Number.isFinite(checked)||now-checked>12*MINUTE;
 const deliveryRunStale=!Number.isFinite(success)||now-success>20*MINUTE;
 return {...state,ok:!heartbeatStale&&!deliveryRunStale&&!state?.error,heartbeatStale,deliveryRunStale};
}
