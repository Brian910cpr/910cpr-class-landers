-- Owner-reviewed non-session deadlines stay in the existing ingest evidence,
-- never become operational sessions or scheduling demand. Decisions apply only
-- to the exact reviewed source identity; material source changes reopen review.
create or replace function public.enrollware_non_session_decision(p_source jsonb)
returns jsonb language sql stable security invoker set search_path=pg_catalog as $$
 select q.decision from public.ingest_review_queue q
 join public.ingest_facts f on f.id=q.ingest_fact_id
 where q.review_type='enrollware_reconciliation' and q.status='resolved'
   and q.decided_at is not null and q.decision->>'owner_confirmed'='true'
   and q.decision->>'classification'='renewal_deadline'
   and f.source_locator->>'external_class_id'=p_source->>'external_class_id'
   and q.decision->'source_identity'=jsonb_build_object(
     'external_class_id',p_source->>'external_class_id',
     'external_course_id',p_source->>'external_course_id',
     'external_location_id',p_source->>'external_location_id',
     'start_at',p_source->>'start_at',
     'source_end_time',p_source->>'source_end_time',
     'source_hours',p_source->>'source_hours')
 order by q.decided_at desc,q.id desc limit 1;
$$;
revoke all on function public.enrollware_non_session_decision(jsonb) from public,anon,authenticated;
grant execute on function public.enrollware_non_session_decision(jsonb) to service_role;

do $migration$
declare definition text;
begin
 select pg_get_functiondef('public.reconcile_enrollware_roster_batch(jsonb,text)'::regprocedure) into definition;
 if position('start_time := (s->>''start_at'')::timestamptz;' in definition)=0 then
   raise exception 'reconciliation source marker missing';
 end if;
 definition:=replace(definition,'touched integer := 0;', 'touched integer := 0; classified integer := 0;');
 definition:=replace(definition,'start_time := (s->>''start_at'')::timestamptz;', $insert$
      if public.enrollware_non_session_decision(s) is not null then
        if exists(select 1 from public.class_sessions cs where cs.external_class_id=external_id) then
          raise exception 'non_session_conflicting_canonical_session';
        end if;
        -- Retain the complete private source evidence without fabricating a
        -- Session/Registration relationship for a non-instructional deadline.
        update public.ingest_facts set proposed_value=s,
          resolution='classified_non_session',resolved_at=now(),
          resolution_reason='owner_confirmed_renewal_deadline' where id=fact;
        classified:=classified+1;
        result:=result||jsonb_build_array(jsonb_build_object('external_class_id',external_id,
          'status','classified_non_session','classification','renewal_deadline'));
        continue;
      end if;
      start_time := (s->>'start_at')::timestamptz;$insert$);
 definition:=replace(definition,'''reconciled'',touched,''quarantined'',quarantined',
   '''reconciled'',touched,''quarantined'',quarantined,''classified_non_sessions'',classified');
 execute definition;
end;
$migration$;

create or replace function public.enrollware_reconciliation_health(p_from timestamptz,p_to timestamptz)
returns jsonb language sql stable security invoker set search_path=pg_catalog as $$
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
    from public.registrations r where r.class_session_id=cs.id and r.status in ('registered','confirmed','completed')) actual
 from source_classes d full join public.class_sessions cs
   on cs.external_class_id=d.external_id and cs.registration_backend='enrollware' and cs.record_scope='operational'
 where (d.external_id is not null or cs.registration_backend='enrollware')
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
$$;
revoke all on function public.enrollware_reconciliation_health(timestamptz,timestamptz) from public,anon,authenticated;
grant execute on function public.enrollware_reconciliation_health(timestamptz,timestamptz) to service_role;
