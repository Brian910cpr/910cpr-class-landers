begin;

create unique index if not exists ingest_review_queue_historical_fact_uidx
  on public.ingest_review_queue (ingest_job_id, ingest_fact_id, review_type)
  where ingest_fact_id is not null;

create or replace function public.promote_historical_registration_batch(
  p_rows jsonb,
  p_source_sha256 text,
  p_dry_run boolean default true
) returns jsonb
language plpgsql
security definer
set search_path = 'pg_catalog'
as $$
declare
  r jsonb;
  v_source_file text;
  v_import_key text;
  v_external_class_id text;
  v_first_name text;
  v_last_name text;
  v_email text;
  v_phone text;
  v_identity_key text;
  v_session_id uuid;
  v_session_matches integer;
  v_customer_id uuid;
  v_customer_matches integer;
  v_registration_id uuid;
  v_existing_import_key text;
  v_org_id uuid;
  v_job_id uuid;
  v_fact_id uuid;
  v_fact_exists boolean;
  v_reason text;
  v_status text;
  v_seen boolean;
  v_registration_inserted boolean;
  n_scanned integer := 0;
  n_matched_existing integer := 0;
  n_inserted integer := 0;
  n_repaired integer := 0;
  n_duplicates integer := 0;
  n_quarantined integer := 0;
  n_failed integer := 0;
  n_sessions_matched integer := 0;
  n_customers_matched integer := 0;
  n_customers_inserted integer := 0;
  n_registrations_matched integer := 0;
  n_registrations_inserted integer := 0;
  n_organizations_matched integer := 0;
  n_audit_inserted integer := 0;
  n_audit_matched integer := 0;
begin
  if jsonb_typeof(p_rows) <> 'array' then
    raise exception 'p_rows must be a JSON array';
  end if;
  if p_source_sha256 is null or p_source_sha256 !~ '^[a-f0-9]{64}$' then
    raise exception 'p_source_sha256 must be a lowercase SHA-256 hex digest';
  end if;

  create temporary table if not exists _hist_seen_customers (
    identity_key text primary key
  ) on commit drop;
  create temporary table if not exists _hist_seen_relationships (
    identity_key text not null,
    class_session_id uuid not null,
    primary key (identity_key, class_session_id)
  ) on commit drop;
  create temporary table if not exists _hist_seen_organizations (
    organization_id uuid primary key
  ) on commit drop;
  truncate _hist_seen_customers, _hist_seen_relationships, _hist_seen_organizations;

  if not p_dry_run then
    perform public.import_historical_registration_batch(p_rows);
    v_source_file := coalesce(p_rows->0->>'source_file', 'students_raw_live.csv');
    insert into public.ingest_jobs(
      source_kind, source_name, source_ref, sha256, mime_type, status,
      parser_status, ai_status, review_status, document_type, metadata,
      started_at, attempt_count, updated_at
    ) values (
      'enrollware_history', v_source_file, 'historical_registration_import_rows',
      p_source_sha256, 'text/csv', 'processing', 'complete', 'not_needed',
      'none', 'historical_registration_export',
      jsonb_build_object('importer', 'promote_historical_registration_batch', 'schema_version', 1),
      now(), 1, now()
    )
    on conflict (sha256) where sha256 is not null do update set
      status = 'processing', parser_status = 'complete', error = null,
      started_at = coalesce(public.ingest_jobs.started_at, now()),
      attempt_count = public.ingest_jobs.attempt_count + 1, updated_at = now()
    returning id into v_job_id;
  else
    select id into v_job_id
    from public.ingest_jobs
    where sha256 = p_source_sha256
    limit 1;
  end if;

  for r in select value from jsonb_array_elements(p_rows)
  loop
    n_scanned := n_scanned + 1;
    begin
      v_source_file := coalesce(r->>'source_file', 'students_raw_live.csv');
      v_import_key := nullif(btrim(r->>'import_key'), '');
      v_external_class_id := nullif(btrim(r->>'external_class_id'), '');
      v_first_name := nullif(btrim(r->>'first_name'), '');
      v_last_name := nullif(btrim(r->>'last_name'), '');
      v_email := nullif(lower(btrim(r->>'email')), '');
      v_phone := nullif(regexp_replace(coalesce(r->>'phone', ''), '[^0-9]', '', 'g'), '');
      v_identity_key := case
        when v_email is not null then 'email:' || v_email
        when length(coalesce(v_phone, '')) >= 7 and v_first_name is not null and v_last_name is not null
          then 'phone_name:' || v_phone || '|' || lower(v_first_name) || '|' || lower(v_last_name)
        else null
      end;
      v_reason := null;
      v_session_id := null;
      v_customer_id := null;
      v_registration_id := null;
      v_existing_import_key := null;
      v_org_id := null;
      v_registration_inserted := false;

      if v_import_key is null then
        v_reason := 'missing_import_key';
      elsif v_external_class_id is null then
        v_reason := 'missing_external_class_id';
      elsif v_first_name is null or v_last_name is null then
        v_reason := 'missing_customer_name';
      elsif v_identity_key is null then
        v_reason := 'unresolved_customer_identity';
      end if;

      if v_reason is null then
        select count(*), min(id::text)::uuid, min(organization_id::text)::uuid
          into v_session_matches, v_session_id, v_org_id
        from public.class_sessions
        where external_class_id = v_external_class_id;
        if v_session_matches = 0 then
          v_reason := 'unresolved_class_id';
        elsif v_session_matches > 1 then
          v_reason := 'ambiguous_class_id';
        else
          n_sessions_matched := n_sessions_matched + 1;
        end if;
      end if;

      if v_reason is null then
        if v_email is not null then
          select count(*), min(id::text)::uuid into v_customer_matches, v_customer_id
          from public.customers where lower(btrim(email)) = v_email;
        else
          select count(*), min(id::text)::uuid into v_customer_matches, v_customer_id
          from public.customers
          where regexp_replace(coalesce(phone, ''), '[^0-9]', '', 'g') = v_phone
            and lower(btrim(first_name)) = lower(v_first_name)
            and lower(btrim(last_name)) = lower(v_last_name);
        end if;
        if v_customer_matches > 1 then
          v_reason := 'ambiguous_customer_identity';
        end if;
      end if;

      if v_reason is not null then
        n_quarantined := n_quarantined + 1;
        if not p_dry_run then
          update public.historical_registration_import_rows
          set import_status = 'quarantined', last_error = v_reason, updated_at = now()
          where import_key = v_import_key;

          select exists(
            select 1 from public.ingest_facts
            where ingest_job_id = v_job_id and deterministic_key = v_import_key
          ) into v_fact_exists;
          insert into public.ingest_facts(
            ingest_job_id, fact_type, source_locator, proposed_value,
            confidence, resolution, resolution_reason, deterministic_key
          ) values (
            v_job_id, 'historical_registration',
            jsonb_build_object('source_file', v_source_file, 'source_row_number', r->>'source_row_number', 'import_key', v_import_key),
            jsonb_build_object('external_class_id', v_external_class_id, 'historical_status', r->>'status'),
            0, 'needs_review', v_reason, v_import_key
          )
          on conflict (ingest_job_id, deterministic_key) where deterministic_key is not null
          do update set resolution = 'needs_review', resolution_reason = excluded.resolution_reason,
            proposed_value = excluded.proposed_value, matched_entity_type = null,
            matched_entity_id = null, resolved_at = null, committed_at = null
          returning id into v_fact_id;
          if v_fact_exists then n_audit_matched := n_audit_matched + 1;
          else n_audit_inserted := n_audit_inserted + 1; end if;

          insert into public.ingest_review_queue(
            ingest_job_id, ingest_fact_id, review_type, question, candidates, status
          ) values (
            v_job_id, v_fact_id, 'historical_registration_quarantine',
            'Resolve historical registration quarantine reason: ' || v_reason,
            '[]'::jsonb, 'open'
          ) on conflict (ingest_job_id, ingest_fact_id, review_type)
            where ingest_fact_id is not null do nothing;
        end if;
        continue;
      end if;

      insert into _hist_seen_organizations(organization_id)
      select v_org_id where v_org_id is not null
      on conflict do nothing;
      get diagnostics v_session_matches = row_count;
      n_organizations_matched := n_organizations_matched + v_session_matches;

      insert into _hist_seen_customers(identity_key) values(v_identity_key)
      on conflict do nothing;
      get diagnostics v_session_matches = row_count;
      v_seen := v_session_matches = 0;

      if p_dry_run then
        if not v_seen then
          if v_customer_id is null then n_customers_inserted := n_customers_inserted + 1;
          else n_customers_matched := n_customers_matched + 1; end if;
        end if;

        if v_customer_id is not null then
          select id, historical_import_key into v_registration_id, v_existing_import_key
          from public.registrations
          where historical_import_key = v_import_key
             or (customer_id = v_customer_id and class_session_id = v_session_id)
          order by case when historical_import_key = v_import_key then 0 else 1 end
          limit 1;
        end if;
        if v_registration_id is not null then
          n_matched_existing := n_matched_existing + 1;
          n_registrations_matched := n_registrations_matched + 1;
          n_duplicates := n_duplicates + 1;
        else
          insert into _hist_seen_relationships(identity_key, class_session_id)
          values(v_identity_key, v_session_id) on conflict do nothing;
          get diagnostics v_session_matches = row_count;
          if v_session_matches = 1 then
            n_inserted := n_inserted + 1;
            n_registrations_inserted := n_registrations_inserted + 1;
          else
            n_matched_existing := n_matched_existing + 1;
            n_duplicates := n_duplicates + 1;
          end if;
        end if;
        if v_job_id is null or not exists(
          select 1 from public.ingest_facts
          where ingest_job_id = v_job_id and deterministic_key = v_import_key
        ) then n_audit_inserted := n_audit_inserted + 1;
        else n_audit_matched := n_audit_matched + 1; end if;
        continue;
      end if;

      perform pg_advisory_xact_lock(hashtextextended('historical_customer|' || v_identity_key, 0));
      if v_email is not null then
        select count(*), min(id::text)::uuid into v_customer_matches, v_customer_id
        from public.customers where lower(btrim(email)) = v_email;
      else
        select count(*), min(id::text)::uuid into v_customer_matches, v_customer_id
        from public.customers
        where regexp_replace(coalesce(phone, ''), '[^0-9]', '', 'g') = v_phone
          and lower(btrim(first_name)) = lower(v_first_name)
          and lower(btrim(last_name)) = lower(v_last_name);
      end if;
      if v_customer_matches > 1 then
        raise exception 'customer identity became ambiguous during promotion';
      elsif v_customer_id is null then
        insert into public.customers(first_name, last_name, email, phone)
        values(v_first_name, v_last_name, v_email, nullif(btrim(r->>'phone'), ''))
        returning id into v_customer_id;
        n_customers_inserted := n_customers_inserted + 1;
      elsif not v_seen then
        n_customers_matched := n_customers_matched + 1;
      end if;

      select id, historical_import_key into v_registration_id, v_existing_import_key
      from public.registrations
      where historical_import_key = v_import_key
         or (customer_id = v_customer_id and class_session_id = v_session_id)
      order by case when historical_import_key = v_import_key then 0 else 1 end
      limit 1 for update;

      if v_registration_id is not null then
        if exists(
          select 1 from public.registrations
          where id = v_registration_id
            and (customer_id <> v_customer_id or class_session_id <> v_session_id)
        ) then
          raise exception 'historical import key conflicts with canonical relationship';
        end if;
        n_matched_existing := n_matched_existing + 1;
        n_registrations_matched := n_registrations_matched + 1;
        n_duplicates := n_duplicates + 1;
      else
        v_status := case lower(coalesce(r->>'status', ''))
          when 'complete' then 'completed'
          when 'completed' then 'completed'
          when 'cancelled' then 'canceled'
          when 'canceled' then 'canceled'
          when 'no show' then 'no_show'
          when 'no-show' then 'no_show'
          else 'registered'
        end;
        insert into public.registrations(
          customer_id, class_session_id, status, registration_source,
          historical_import_key, historical_status, historical_score,
          historical_checked_in, historical_ecard_code, historical_codes,
          historical_comments, created_at, updated_at
        ) values (
          v_customer_id, v_session_id, v_status, 'enrollware_history',
          v_import_key, r->>'status', r->>'score', r->>'checked_in',
          r->>'ecard_code', r->>'codes', r->>'comments',
          coalesce(nullif(r->>'registration_date', '')::timestamptz, now()), now()
        ) returning id into v_registration_id;
        v_registration_inserted := true;
        n_inserted := n_inserted + 1;
        n_registrations_inserted := n_registrations_inserted + 1;
      end if;

      select registration_id is null or customer_id is null into v_seen
      from public.historical_registration_import_rows
      where import_key = v_import_key;
      update public.historical_registration_import_rows
      set customer_id = v_customer_id, registration_id = v_registration_id,
        class_session_id = v_session_id, import_status = 'promoted',
        imported_at = coalesce(imported_at, now()), last_error = null, updated_at = now()
      where import_key = v_import_key;
      if coalesce(v_seen, false) and v_registration_id is not null and not v_registration_inserted then
        n_repaired := n_repaired + 1;
      end if;

      select exists(
        select 1 from public.ingest_facts
        where ingest_job_id = v_job_id and deterministic_key = v_import_key
      ) into v_fact_exists;
      insert into public.ingest_facts(
        ingest_job_id, fact_type, source_locator, proposed_value,
        matched_entity_type, matched_entity_id, confidence, resolution,
        resolution_reason, resolved_at, deterministic_key, committed_at
      ) values (
        v_job_id, 'historical_registration',
        jsonb_build_object('source_file', v_source_file, 'source_row_number', r->>'source_row_number', 'import_key', v_import_key),
        jsonb_build_object('external_class_id', v_external_class_id, 'historical_status', r->>'status'),
        'registration', v_registration_id, 1, 'committed',
        'deterministic customer identity and canonical session match', now(), v_import_key, now()
      )
      on conflict (ingest_job_id, deterministic_key) where deterministic_key is not null
      do update set matched_entity_type = 'registration',
        matched_entity_id = excluded.matched_entity_id, confidence = 1,
        resolution = 'committed', resolution_reason = excluded.resolution_reason,
        resolved_at = coalesce(public.ingest_facts.resolved_at, now()),
        committed_at = coalesce(public.ingest_facts.committed_at, now())
      returning id into v_fact_id;
      if v_fact_exists then n_audit_matched := n_audit_matched + 1;
      else n_audit_inserted := n_audit_inserted + 1; end if;

    exception when others then
      n_failed := n_failed + 1;
      if not p_dry_run and v_import_key is not null then
        update public.historical_registration_import_rows
        set import_status = 'failed', last_error = sqlstate || ': ' || sqlerrm, updated_at = now()
        where import_key = v_import_key;
      end if;
    end;
  end loop;

  if not p_dry_run then
    update public.ingest_jobs set
      status = case when n_failed > 0 then 'partial' else 'complete' end,
      review_status = case when n_quarantined > 0 then 'needs_review' else 'none' end,
      completed_at = now(), updated_at = now(),
      metadata = metadata || jsonb_build_object(
        'last_batch', jsonb_build_object(
          'scanned', n_scanned, 'matched_existing', n_matched_existing,
          'inserted', n_inserted, 'repaired', n_repaired,
          'duplicates_suppressed', n_duplicates, 'quarantined', n_quarantined,
          'failed', n_failed
        )
      )
    where id = v_job_id;
  end if;

  return jsonb_build_object(
    'dry_run', p_dry_run,
    'scanned', n_scanned,
    'matched_existing', n_matched_existing,
    'inserted', n_inserted,
    'repaired', n_repaired,
    'duplicates_suppressed', n_duplicates,
    'quarantined', n_quarantined,
    'failed', n_failed,
    'class_sessions', jsonb_build_object('matched_existing', n_sessions_matched, 'inserted', 0),
    'participants', jsonb_build_object('matched_existing', n_customers_matched, 'inserted', n_customers_inserted),
    'registrations', jsonb_build_object('matched_existing', n_registrations_matched, 'inserted', n_registrations_inserted),
    'customers_organizations', jsonb_build_object('matched_existing', n_organizations_matched, 'inserted', 0),
    'audit_provenance', jsonb_build_object('matched_existing', n_audit_matched, 'inserted', n_audit_inserted)
  );
end;
$$;

revoke all on function public.promote_historical_registration_batch(jsonb, text, boolean)
  from public, anon, authenticated;
grant execute on function public.promote_historical_registration_batch(jsonb, text, boolean)
  to service_role;

commit;
