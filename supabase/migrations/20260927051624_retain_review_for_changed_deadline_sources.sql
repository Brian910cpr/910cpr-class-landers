-- A changed reviewed deadline must not silently become instructional merely
-- because the replacement source location is active. Preserve prior decisions.
do $migration$
declare definition text;
begin
 select pg_get_functiondef('public.reconcile_enrollware_roster_batch(jsonb,text)'::regprocedure) into definition;
 if position('public.enrollware_non_session_decision(s)' in definition)=0
    or position('start_time := (s->>''start_at'')::timestamptz;' in definition)=0 then
   raise exception 'reviewed deadline source marker missing';
 end if;
 definition:=replace(definition,'start_time := (s->>''start_at'')::timestamptz;', $insert$
      if exists(select 1 from public.ingest_review_queue q join public.ingest_facts f on f.id=q.ingest_fact_id
          where q.review_type='enrollware_reconciliation' and q.status='resolved'
            and q.decision->>'owner_confirmed'='true' and q.decision->>'classification'='renewal_deadline'
            and f.source_locator->>'external_class_id'=external_id) then
        raise exception 'non_session_source_changed_requires_review';
      end if;
      start_time := (s->>'start_at')::timestamptz;$insert$);
 execute definition;
end;
$migration$;
