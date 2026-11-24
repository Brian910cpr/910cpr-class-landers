-- REVIEW ONLY: after collector gateway and reader; outside migrations.
-- Identity binding is necessary but is NOT operational source attestation.
begin;
do $$ declare definition text; marker text := '  if p_checked_at>clock_timestamp()'; begin
  definition:=pg_get_functiondef('production_board_private.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz)'::regprocedure);
  if strpos(definition, marker)=0 or strpos(definition, 'collector_source_binding_required')>0 then
    raise exception 'unexpected_source_publisher_baseline';
  end if;
  -- Existing card/intake locks protect mapping, version and resolution together.
  definition:=replace(definition,marker,
    '  if i.card_id is null then raise exception ''collector_source_binding_required''; end if;
  if p_issue>9007199254740991 or p_source_ref is distinct from
    ''https://github.com/Brian910cpr/910cpr-class-landers/issues/''||i.issue_id::text then
    raise exception ''collector_source_identity_mismatch'';
  end if;
'||marker);
  execute definition;
end $$;
commit;
