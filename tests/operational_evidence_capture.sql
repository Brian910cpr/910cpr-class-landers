-- Run against the deployed schema. Synthetic evidence is rolled back.
begin;
do $$
declare
 a jsonb; b jsonb; c jsonb; d jsonb;
 before_counts jsonb; after_counts jsonb;
 rid uuid; aid uuid; n integer;
begin
 select jsonb_build_array((select count(*) from public.registrations),
   (select count(*) from public.class_sessions),(select count(*) from public.customers),
   (select count(*) from public.registration_orders),(select count(*) from public.landerware_messages),
   (select count(*) from public.landerware_roster_memberships)) into before_counts;
 if has_function_privilege('anon',
   'public.capture_operational_evidence(text,text,timestamptz,jsonb,text[],jsonb,text)','execute')
 or has_function_privilege('authenticated',
   'public.capture_operational_evidence(text,text,timestamptz,jsonb,text[],jsonb,text)','execute') then
   raise exception 'public evidence capture permission';
 end if;
 if not has_function_privilege('service_role',
   'public.capture_operational_evidence(text,text,timestamptz,jsonb,text[],jsonb,text)','execute') then
   raise exception 'service role cannot capture';
 end if;
 a := public.capture_operational_evidence('test:operational-evidence',
   txid_current()::text,'2026-10-24T12:00:00Z','{"text":"original evidence"}',
   array['communications','operations'],'{"claim":"requested"}',null);
 rid := (a->>'record_id')::uuid; aid := (a->>'assertion_id')::uuid;
 if a->>'duplicate'<>'false' or a->>'production_mutated'<>'false' then
   raise exception 'initial capture failed';
 end if;
 -- A different session timezone and reordered categories must still deduplicate.
 perform set_config('TimeZone','America/New_York',true);
 b := public.capture_operational_evidence('test:operational-evidence',
   txid_current()::text,'2026-10-24T08:00:00-04:00','{"text":"original evidence"}',
   array['operations','communications','communications'],'{"claim":"requested"}',null);
 if b->>'duplicate'<>'true' or b->>'assertion_id'<>a->>'assertion_id' then
   raise exception 'duplicate intake failed';
 end if;
 c := public.capture_operational_evidence('test:operational-evidence',
   txid_current()::text,'2026-10-24T12:00:00Z','{"text":"contradictory evidence"}',
   array['communications','operations'],'{"claim":"completed"}',null);
 if c->>'source_changed'<>'true' or c->>'record_id'=a->>'record_id' then
   raise exception 'changed source evidence was not versioned';
 end if;
 if not exists(select 1 from public.ingest_review_queue
   where id=(c->>'review_id')::uuid and review_type='evidence_source_version_conflict') then
   raise exception 'missing conflict review';
 end if;
 if not exists(select 1 from public.lifecycle_import_records
   where id=(c->>'record_id')::uuid and predecessor_import_record_id=rid) then
   raise exception 'missing predecessor link';
 end if;
 d := public.capture_operational_evidence('test:operational-evidence',
   txid_current()::text,'2026-10-24T12:00:00Z','{"text":"original evidence"}',
   array['communications','operations'],'{"claim":"interpretation corrected"}',null);
 if d->>'interpretation_changed'<>'true' or d->>'record_id'<>a->>'record_id' then
   raise exception 'interpretation correction erased/replaced original';
 end if;
 select count(*) into n from public.lifecycle_import_records
 where source_system='test:operational-evidence' and source_record_id=txid_current()::text;
 if n<>2 then raise exception 'wrong source version count: %',n; end if;
 select count(*) into n from public.lifecycle_evidence_assertions
 where source='test:operational-evidence' and source_record_id=txid_current()::text;
 if n<>3 then raise exception 'wrong interpretation count: %',n; end if;
 begin
   update public.lifecycle_import_records set original_values='{}' where id=rid;
   raise exception using message='immutable source update allowed',errcode='XX000';
 exception when raise_exception then null; end;
 begin
   delete from public.lifecycle_import_records where id=rid;
   raise exception using message='immutable source delete allowed',errcode='XX000';
 exception when raise_exception then null; end;
 begin
   update public.lifecycle_evidence_assertions set asserted_value='{}' where id=aid;
   raise exception using message='immutable interpretation update allowed',errcode='XX000';
 exception when raise_exception then null; end;
 begin
   perform public.capture_operational_evidence('test', 'invalid', now(),'{}',array['invalid'],'{}');
   raise exception using message='invalid category allowed',errcode='XX000';
 exception when raise_exception then null; end;
 select jsonb_build_array((select count(*) from public.registrations),
   (select count(*) from public.class_sessions),(select count(*) from public.customers),
   (select count(*) from public.registration_orders),(select count(*) from public.landerware_messages),
   (select count(*) from public.landerware_roster_memberships)) into after_counts;
 if before_counts<>after_counts then raise exception 'production counts changed'; end if;
 if exists(select 1 from public.ingest_operational_dashboard
   where total_jobs<>queued+processing+retry+completed+failed+review_jobs+reconciled_jobs+unknown_status_jobs)
 then raise exception 'dashboard does not account for all jobs'; end if;
end;
$$;
select 'PASS: capture, replay, timezone, source versions, interpretations, review, immutability, permissions, production isolation, dashboard coverage' result;
rollback;
