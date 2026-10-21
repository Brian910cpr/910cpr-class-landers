// Workspace appointments remain visible before operational reconciliation.
// Their IDs must never be passed to the operational move RPC.
export async function unresolvedCommitments(email, rest) {
 const escaped=encodeURIComponent(email.replace(/_/g,'\\_'));
 const people=await rest(`landerware_people?current_email=ilike.${escaped}&select=id,current_first_name,current_last_name&limit=100`);
 const result=[];
 for(const p of people){
  const rows=await rest(`landerware_registrations?person_id=eq.${p.id}&status=in.(active,scheduled,registered,confirmed)&select=id,status,session:landerware_sessions!inner(id,class_session_id,course_name,starts_at,lifecycle_state,location_name,requirements_manifest)&limit=100`);
  for(const r of rows){
   const s=r.session;
   if(!s||s.class_session_id||['proposed','draft','tentative','pending_proposal','cancelled','canceled','completed'].includes(s.lifecycle_state))continue;
   result.push({personId:p.id,workspaceRegistrationId:r.id,workspaceSessionId:s.id,
    name:[p.current_first_name,p.current_last_name].filter(Boolean).join(' '),course:s.course_name,
    startsAt:s.starts_at,status:r.status,reason:'operational_session_link_missing',
    locationRequiresVerification:!s.location_name||Boolean(s.requirements_manifest?.location_requires_verification),
    outboundSuppressed:Boolean(s.requirements_manifest?.suppress_outbound_until_location_verified)});
  }
  if(rows.length===100)throw Error('commitment_lookup_incomplete');
 }
 if(people.length===100)throw Error('commitment_lookup_incomplete');
 return result.sort((a,b)=>Date.parse(a.startsAt)-Date.parse(b.startsAt));
}
