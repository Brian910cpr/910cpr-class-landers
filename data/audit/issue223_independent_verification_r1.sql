with audit as (
select a.id audit_id,a.class_session_id,a.details,a.details->'source_snapshot' snap,a.occurred_at from public.class_session_audit a
where a.event_type='enrollware_owner_reconciliation' and a.details->>'issue_url'='https://github.com/Brian910cpr/910cpr-class-landers/issues/223'
), rows as (
select a.audit_id,a.class_session_id,a.snap->>'number' class_number,a.snap->>'external_id' expected_external_id,
a.snap->>'count' expected_enrolled_count,s.external_class_id,s.start_at,s.end_at,s.max_students,s.record_scope,
a.details->>'action' action,a.details->>'raw_end_time_valid' raw_end_time_valid,a.details->>'pediatric_end_time_provisional' pediatric_end_time_provisional,
(s.external_class_id=a.snap->>'external_id' and s.course_id::text=a.snap->>'course_id' and s.location_id::text=a.snap->>'location_id' and s.lead_instructor_id::text=a.snap->>'instructor_id' and s.start_at=(a.snap->>'start')::timestamptz and s.end_at=(a.snap->>'end')::timestamptz and s.max_students=(a.snap->>'capacity')::int) matches_snapshot,
(select count(*) from public.class_sessions d where d.external_class_id=s.external_class_id) external_id_matches,
(select count(*) from public.class_sessions d where d.course_id=s.course_id and d.start_at=s.start_at and d.location_id=s.location_id and d.record_scope='operational' and d.status in ('scheduled','active','completed')) slot_matches,
(select count(*) from public.registrations r where r.class_session_id=s.id and r.status in ('registered','confirmed','completed')) active_registration_count,
(select count(*) from public.class_session_audit x where x.class_session_id=s.id and x.event_type='enrollware_live_roster_verified' and x.occurred_at>=a.occurred_at) roster_audit_count,
(a.details ? 'before_class') before_key_present,(a.details ? 'after_class') after_key_present,a.snap->>'end_source' end_source,
exists(select 1 from public.courses c where c.id=s.course_id) course_join_exists,exists(select 1 from public.locations l where l.id=s.location_id) location_join_exists
from audit a join public.class_sessions s on s.id=a.class_session_id)
select jsonb_build_object('verified_at',now(),'rows',(select jsonb_agg(rows order by class_number) from rows),'audit_count',(select count(*) from audit)) assessment;

-- Supplemental read-only identity, projection eligibility and source-drift checks.
with a as (select class_session_id,details from public.class_session_audit where event_type='enrollware_owner_reconciliation' and details->>'issue_url'='https://github.com/Brian910cpr/910cpr-class-landers/issues/223'),
joined as (select a.*,s.status,s.record_scope,s.start_at,s.external_class_id,s.external_course_id,s.registration_url,s.updated_at from a join public.class_sessions s on s.id=a.class_session_id)
select jsonb_build_object('verified_at',now(),'classes',(select count(*) from joined),
'stable_before_after_ids',(select count(*) from joined where details->'after_class'->>'id'=class_session_id::text and (details->'before_class'='null'::jsonb or details->'before_class'->>'id'=class_session_id::text)),
'endpoint_filter_eligible',(select count(*) from joined where status in ('scheduled','active','completed') and record_scope='operational' and start_at >= '2026-09-14T00:00:00-04:00'::timestamptz and start_at < '2026-09-30T00:00:00-04:00'::timestamptz),
'matching_registration_urls',(select count(*) from joined where registration_url=details->'source_snapshot'->>'registration_url'),
'duplicate_active_customer_class_groups',(select count(*) from (select r.class_session_id,r.customer_id from public.registrations r join a on a.class_session_id=r.class_session_id where r.status in ('registered','confirmed','completed') group by r.class_session_id,r.customer_id having count(*)>1) d),
'external_course_id_differences',(select jsonb_agg(jsonb_build_object('class_number',details->'source_snapshot'->>'number','external_class_id',external_class_id,'current_course_id',external_course_id,'snapshot_course_id',details->'source_snapshot'->>'external_course_id','updated_at',updated_at)) from joined where external_course_id is distinct from details->'source_snapshot'->>'external_course_id')) assessment;
