export const COMMITTED_OPERATIONAL_STATES=new Set(['scheduled','active','completed']);

export function isOperationalSession(session:{status?:unknown;[key:string]:unknown}){
  return COMMITTED_OPERATIONAL_STATES.has(String(session.status??'').trim().toLowerCase());
}

export function projectOperationalSession(session:any,counts:Map<string,number>,courseNames:Map<string,string>,locationNames:Map<string,string>,instructorNames:Map<string,string>){
  return{id:session.id,external_session_id:session.external_class_id,course_id:session.course_id,course_name:courseNames.get(session.course_id)||null,external_course_id:session.external_course_id,start_at:session.start_at,end_at:session.end_at,location_id:session.location_id,location_name:locationNames.get(session.location_id)||null,lead_instructor_id:session.lead_instructor_id,lead_instructor_name:instructorNames.get(session.lead_instructor_id)||null,organization_id:session.organization_id,lifecycle_state:session.status,registration_status:session.registration_status,registration_backend:session.registration_backend,registration_url:session.registration_url,provenance:session.source,registered_count:counts.get(session.id)||0,participant_count_available:true,roster_available:true};
}
