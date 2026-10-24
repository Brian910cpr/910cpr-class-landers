-- Staging only: reuse the existing immutable lifecycle ledger and review queue.
-- No operational entity writes, notifications, or worker dispatch.
create or replace function public.capture_operational_evidence(
  p_source_system text,
  p_source_record_id text,
  p_source_timestamp timestamptz,
  p_payload jsonb,
  p_categories text[],
  p_facts jsonb,
  p_reference text default null
) returns jsonb
language plpgsql security invoker
set search_path = pg_catalog
set timezone = 'UTC'
as $$
declare
  v_original jsonb;
  v_interpretation jsonb;
  v_fingerprint text;
  v_key text;
  v_batch uuid;
  v_record uuid;
  v_prior uuid;
  v_assertion uuid;
  v_job uuid;
  v_review uuid;
  v_source_changed boolean := false;
  v_interpretation_changed boolean := false;
begin
  if nullif(btrim(p_source_system),'') is null
     or nullif(btrim(p_source_record_id),'') is null
     or p_source_timestamp is null or p_payload is null
     or jsonb_typeof(p_payload) <> 'object'
     or p_facts is null or jsonb_typeof(p_facts) <> 'object'
     or coalesce(cardinality(p_categories),0) = 0
     or array_position(p_categories,null) is not null
     or not (p_categories <@ array['people','classes','registrations','financial',
          'credentials','communications','operations','engineering']::text[]) then
    raise exception 'source identity, timestamp, object payload/facts, and valid categories required';
  end if;

  -- Serialize this exact source identity. Different sources do not block each other.
  perform pg_advisory_xact_lock(hashtextextended(
    jsonb_build_array(p_source_system,p_source_record_id)::text,0));
  v_original := jsonb_build_object('payload',p_payload,
    'source_timestamp',p_source_timestamp,'source_reference',p_reference);
  v_fingerprint := encode(extensions.digest(v_original::text,'sha256'),'hex');
  v_interpretation := jsonb_build_object('categories',
    (select jsonb_agg(c order by c) from (select distinct unnest(p_categories) c) q),
    'facts',p_facts,'parser_version','operational-evidence-v1');
  v_key := 'operational-evidence:' || encode(extensions.digest(
    jsonb_build_array(p_source_system,p_source_record_id,v_fingerprint,v_interpretation)::text,
    'sha256'),'hex');

  select id into v_assertion from public.lifecycle_evidence_assertions where assertion_key=v_key;
  if found then
    select import_record_id into v_record from public.lifecycle_evidence_assertions where id=v_assertion;
    return jsonb_build_object('duplicate',true,'record_id',v_record,'assertion_id',v_assertion,
      'production_mutated',false);
  end if;

  select id into v_record from public.lifecycle_import_records
  where source_system=p_source_system and source_record_id=p_source_record_id
    and entity_type='operational_evidence' and source_fingerprint=v_fingerprint
    and source_fingerprint_algorithm='sha256:postgres-jsonb-v1';

  select id into v_prior from public.lifecycle_import_records
  where source_system=p_source_system and source_record_id=p_source_record_id
    and entity_type='operational_evidence' and source_fingerprint<>v_fingerprint
  order by created_at desc,id desc limit 1;
  v_source_changed := v_prior is not null;

  if v_record is null then
    insert into public.lifecycle_import_batches
      (batch_key,source_system,source_file_identity,parser_version,mode,status,created_by,summary)
    values ('operational-evidence:' || encode(extensions.digest(
        jsonb_build_array(p_source_system,p_source_record_id,v_fingerprint)::text,'sha256'),'hex'),
      p_source_system,p_reference,'operational-evidence-v1','dry_run','review_required',
      current_user,jsonb_build_object('production_mutation',false,'coverage','single_source_item'))
    returning id into v_batch;
    insert into public.lifecycle_import_records
      (batch_id,source_system,source_record_id,entity_type,source_document_identity,
       original_values,proposed_values,source_fingerprint,source_fingerprint_algorithm,
       predecessor_import_record_id,reconciliation_status,ambiguity_state)
    values (v_batch,p_source_system,p_source_record_id,'operational_evidence',p_reference,
      v_original,'{}',v_fingerprint,'sha256:postgres-jsonb-v1',v_prior,
      case when v_source_changed then 'ambiguous' else 'pending' end,'unknown')
    returning id into v_record;
  else
    select batch_id into v_batch from public.lifecycle_import_records where id=v_record;
    v_interpretation_changed := exists(select 1 from public.lifecycle_evidence_assertions
      where import_record_id=v_record);
  end if;

  insert into public.lifecycle_evidence_assertions
    (assertion_key,fact_type,source,source_record_id,import_batch_id,import_record_id,
     asserted_value,original_source_value,confidence_state,reconciliation_status,
     source_created_at,observed_at,reconciliation_notes)
  values (v_key,'other',p_source_system,p_source_record_id,v_batch,v_record,
    v_interpretation,v_original,
    case when v_source_changed or v_interpretation_changed then 'conflicting' else 'unknown' end,
    case when v_source_changed or v_interpretation_changed then 'conflicting' else 'unreviewed' end,
    p_source_timestamp,now(),'Captured evidence only; no operational authorization or identity merge.')
  returning id into v_assertion;

  -- needs_review is deliberately outside claim_ingest_jobs queued/retry states.
  insert into public.ingest_jobs
    (source_kind,source_name,source_ref,sha256,status,parser_status,review_status,metadata)
  values ('evidence_capture',p_source_system || ':' || p_source_record_id,p_reference,
    substring(v_key from length('operational-evidence:')+1),'needs_review','complete','open',
    jsonb_build_object('assertion_id',v_assertion,'import_record_id',v_record,
      'content_sha256',v_fingerprint,'hash_algorithm','sha256:postgres-jsonb-v1',
      'production_mutation',false)) returning id into v_job;
  insert into public.ingest_review_queue(ingest_job_id,review_type,question,candidates)
  values (v_job,
    case when v_source_changed then 'evidence_source_version_conflict'
         when v_interpretation_changed then 'evidence_interpretation_conflict'
         else 'evidence_reconciliation' end,
    'Review captured evidence and verify stable entity links; no production action has been applied.',
    jsonb_build_array(jsonb_build_object('assertion_id',v_assertion,'record_id',v_record,
      'prior_record_id',v_prior))) returning id into v_review;
  return jsonb_build_object('duplicate',false,'record_id',v_record,'assertion_id',v_assertion,
    'review_id',v_review,'source_changed',v_source_changed,
    'interpretation_changed',v_interpretation_changed,'production_mutated',false);
end;
$$;
revoke all on function public.capture_operational_evidence(text,text,timestamptz,jsonb,text[],jsonb,text)
  from public,anon,authenticated;
grant execute on function public.capture_operational_evidence(text,text,timestamptz,jsonb,text[],jsonb,text)
  to service_role;

create or replace function public.protect_captured_evidence_delete()
returns trigger language plpgsql security invoker set search_path=pg_catalog as $$
begin
  if old.entity_type='operational_evidence' then
    raise exception 'captured source evidence is immutable; append a correction';
  end if;
  return old;
end;
$$;
revoke all on function public.protect_captured_evidence_delete() from public,anon,authenticated;
create trigger captured_evidence_delete_guard before delete on public.lifecycle_import_records
for each row execute function public.protect_captured_evidence_delete();

-- Preserve the existing first eight columns for consumers; add explicit diagnostics.
create or replace view public.ingest_operational_dashboard with (security_invoker=true) as
select count(*) filter(where status='queued') queued,
 count(*) filter(where status='processing') processing,
 count(*) filter(where status='retry') retry,
 count(*) filter(where status in ('complete','completed')) completed,
 count(*) filter(where status='failed') failed,
 coalesce(sum(attempt_count),0::bigint) total_attempts,
 (select count(*) from public.ingest_review_queue where status='open') open_reviews,
 (select count(*) from public.ingest_facts where resolution='proposed') proposed_facts,
 count(*) total_jobs,
 count(*) filter(where status in ('review','needs_review','review_required')) review_jobs,
 count(*) filter(where status='reconciled') reconciled_jobs,
 count(*) filter(where status='processing'
   and coalesce(locked_at,started_at,updated_at,created_at)<now()-interval '15 minutes') stale_processing,
 count(*) filter(where status in ('queued','retry')
   and coalesce(next_attempt_at,created_at)<now()-interval '1 hour') overdue_jobs,
 count(*) filter(where status not in ('queued','processing','retry','complete','completed',
   'failed','review','needs_review','review_required','reconciled') or status is null) unknown_status_jobs,
 max(completed_at) last_marked_completed_at,
 now() observed_at
from public.ingest_jobs;
revoke all on public.ingest_operational_dashboard from public,anon,authenticated;
grant select on public.ingest_operational_dashboard to service_role;
