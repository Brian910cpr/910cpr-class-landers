-- Keep local event slugs and historical rows out of Enrollware reconciliation health.
CREATE OR REPLACE FUNCTION public.enrollware_reconciliation_health(p_from timestamp with time zone, p_to timestamp with time zone)
 RETURNS jsonb
 LANGUAGE sql
 STABLE
 SET search_path TO 'pg_catalog'
AS $function$
with latest as (
 select distinct on (source_locator->>'external_class_id') * from public.ingest_facts
 where fact_type='enrollware_committed_session'
 order by source_locator->>'external_class_id',created_at desc,id desc
), source_classes as (
 select source_locator->>'external_class_id' external_id,proposed_value->>'start_at' start_at,
   resolution,resolution_reason,source_locator->>'source_observed_at' observed_at,
   public.enrollware_non_session_decision(proposed_value) non_session_decision
 from latest
), joined as (
 select coalesce(d.external_id,cs.external_class_id) external_class_id,cs.id session_id,
   coalesce(cs.start_at,d.start_at::timestamptz) start_at,cs.external_reconciliation proof,
   d.resolution,d.resolution_reason,d.non_session_decision,d.observed_at,
   (select coalesce(jsonb_agg(r.external_registration_id order by r.external_registration_id),'[]'::jsonb)
    from public.registrations r where r.class_session_id=cs.id and r.status in ('registered','confirmed','completed')
      and (cs.registration_backend='enrollware' or r.external_registration_id is not null
        or r.registration_source in ('enrollware','enrollware_history','enrollware_reconciled','gmail_enrollware','enrollware_owner_reconciliation'))) actual
 from source_classes d full join public.class_sessions cs
   on cs.external_class_id=d.external_id and cs.record_scope='operational'
 where (d.external_id is not null or (cs.record_scope='operational' and cs.external_class_id is not null
   and not (cs.source='landerware_event' and cs.registration_backend in ('landerware','manual') and cs.external_class_id !~ '^[0-9]+$')))
   and coalesce(cs.start_at,d.start_at::timestamptz)>=p_from and coalesce(cs.start_at,d.start_at::timestamptz)<p_to
), assessed as (
 select *,case when non_session_decision is not null and session_id is not null then 'non_session_conflicting_canonical_session'
   when non_session_decision is not null then 'classified_non_session'
   when session_id is null then 'missing_canonical_session'
   when resolution='needs_review' then 'registration_evidence_without_canonical_relationship'
   when proof->>'complete' is distinct from 'true' then 'external_reconciliation_required'
   when (proof->>'source_observed_at')::timestamptz < now()-interval '60 minutes'
     or (proof->>'source_observed_at')::timestamptz > now()+interval '5 minutes' then 'stale_reconciliation'
   when proof->'active_external_registration_ids' is distinct from actual then 'registration_relationship_mismatch'
   else 'current' end status from joined
)
select jsonb_build_object('checked_at',now(),'freshness_minutes',60,'sessions',coalesce(jsonb_agg(jsonb_build_object(
  'external_class_id',external_class_id,'canonical_session_id',session_id,'start_at',start_at,'status',status,
  'source_observed_at',coalesce(proof->>'source_observed_at',observed_at),'reconciled_at',proof->>'reconciled_at',
  'source_sha256',proof->>'source_sha256','reason',case when status='classified_non_session' then 'owner_confirmed_renewal_deadline' else resolution_reason end,
  'non_session_classification',non_session_decision->>'classification',
  'approved_location_key',non_session_decision->>'approved_location_key')), '[]'),
  'unknown_sessions',count(*) filter(where status not in ('current','classified_non_session')),
  'classified_non_sessions',count(*) filter(where status='classified_non_session'),
  'total_sessions',count(*) filter(where status<>'classified_non_session')) from assessed;
$function$;
