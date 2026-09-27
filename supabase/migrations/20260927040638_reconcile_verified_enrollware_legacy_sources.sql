-- Existing #223 relationships used these provenance labels. Their *current*
-- authority comes only from the complete authenticated roster required by #297.
-- Keep prior evidence and registration IDs; do not promote mail counts.
do $$
declare definition text;
begin
  select pg_get_functiondef('public.reconcile_enrollware_roster_batch(jsonb,text)'::regprocedure) into definition;
  definition:=replace(definition,
    '''enrollware'',''enrollware_history'',''enrollware_reconciled''',
    '''enrollware'',''enrollware_history'',''enrollware_reconciled'',''gmail_enrollware'',''enrollware_owner_reconciliation''');
  definition:=replace(definition,'external_reconciliation_evidence=jsonb_build_object(',
    'external_reconciliation_evidence=external_reconciliation_evidence||jsonb_build_object(');
  execute definition;
end;
$$;
