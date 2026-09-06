(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.LanderWareSession=api})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const EXCLUDED=new Set(['cancelled','canceled','removed','superseded','replacing','deleted']);
  const text=value=>String(value??'').trim();
  function locator(row={}){return{sessionId:text(row.durable_session_id||row.session_workspace_id),externalSessionId:text(row.external_session_id||row.session_id||row.class_id||row.id),courseId:text(row.course_id||row.course_key),courseName:text(row.course_name||row._name||row.mapped_clean_title),startsAt:text(row.start_at||row.start||row._start?.toISOString?.()),source:text(row.source||row.provenance)}}
  function workspaceUrl(row={}){const l=locator(row),q=new URLSearchParams();Object.entries(l).forEach(([k,v])=>{if(v)q.set(k,v)});return `https://www.910cpr.com/admin/session-workspace.html?${q.toString()}#participants`}
  function canonicalRegistrationCount(registrations=[]){return registrations.filter(r=>!EXCLUDED.has(text(r.status).toLowerCase())).length}
  function participantState(row={}){
    if(Number.isInteger(row.durable_participant_count)&&row.durable_participant_count>=0)return{count:row.durable_participant_count,available:true,rosterAvailable:true,source:'landerware_durable'};
    if(row.participant_count_available===true&&Number.isFinite(Number(row.registered_count)))return{count:Number(row.registered_count),available:true,rosterAvailable:row.roster_available===true,source:text(row.participant_count_source)||'aggregate'};
    return{count:null,available:false,rosterAvailable:false,source:'unavailable'};
  }
  function participantLabel(row={}){const state=participantState(row);return `Participants (${state.available?state.count:'—'})`}
  async function hydrate(rows=[],endpoint='https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/session-workspace/summaries'){
    const sessions=rows.map(row=>{const l=locator(row),state=participantState(row);return{...l,registeredCount:state.count,countAvailable:state.available,rosterAvailable:state.rosterAvailable}});
    const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sessions}),cache:'no-store'});if(!response.ok)throw Error(`session_workspace_${response.status}`);const payload=await response.json(),byExternal=new Map((payload.summaries||[]).map(s=>[text(s.externalSessionId),s]));
    rows.forEach(row=>{const s=byExternal.get(locator(row).externalSessionId);if(!s)return;if(s.session?.id)row.durable_session_id=s.session.id;if(s.count_source==='landerware_durable_registrations'){row.durable_participant_count=s.participant_count;row.roster_available=true}else if(s.count_available===true){row.registered_count=s.participant_count;row.participant_count_available=true;row.roster_available=s.roster_available===true;row.participant_count_source=s.count_source}});return rows;
  }
  return{EXCLUDED,locator,workspaceUrl,canonicalRegistrationCount,participantState,participantLabel,hydrate};
});
