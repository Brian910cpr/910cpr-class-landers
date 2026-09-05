do $$
declare
  v_definition text;
begin
  select pg_get_functiondef('public.promote_historical_registration_batch(jsonb,text,boolean)'::regprocedure)
    into v_definition;
  v_definition := replace(v_definition, 'min(id)', 'min(id::text)::uuid');
  v_definition := replace(v_definition, 'min(organization_id)', 'min(organization_id::text)::uuid');
  execute v_definition;
end;
$$;
