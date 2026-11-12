-- Bound new shared-skills materialization to the original publication lease even
-- when PostgreSQL transaction-start now() precedes an awaited lock's release.
-- Existing native publications already require 15-minute proof and 24-hour lead.
-- Unmarked legacy offers retain their existing 30-minute proof and future-start rule.
-- No enablement, canonical rows, order/payment logic or prior receipts change.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
do $wallclock_guard$
declare signature text:='public.materialize_native_skills_checkout(text,jsonb,text)';
 installed text; definition text; anchor text; replacement text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_catalog.pg_proc where oid=pg_catalog.to_regprocedure(signature);
 -- Reviewed shared-skills lifecycle body, unchanged by optional full-course scopes.
 if installed is null or md5(installed) is distinct from '1edef38982d22cbaa056ce94b93c2628' then
  raise exception 'native_skills_offer_wallclock_source_drift';
 end if;
 anchor:=$anchor$ return option||jsonb_build_object('targetSessionId',target,'externalId',locked_external_id);$anchor$;
 replacement:=$replacement$ -- All class, policy, inventory and canonical-workspace lock waits above
 -- have completed. Never renew generatedAt, proofObservedAt or validUntil.
 -- An exception rolls back target creation/reopening and lifecycle witnesses.
 declare checked_at timestamptz:=clock_timestamp();
 begin
  if nullif(p_offer->>'validUntil','')::timestamptz is null
   or (p_offer->>'validUntil')::timestamptz<=checked_at
   or nullif(p_offer->>'generatedAt','')::timestamptz is null
   or (p_offer->>'generatedAt')::timestamptz<checked_at-interval '30 minutes'
   or nullif(p_offer->>'startsAt','')::timestamptz is null
   or (p_offer->>'startsAt')::timestamptz<=checked_at then
   raise exception 'session_not_available';
  end if;
  if p_offer->>'authority' in ('native-skills-publication.v1','native-skills-seated.v1') and (
   nullif(p_offer->>'proofObservedAt','')::timestamptz is null
   or (p_offer->>'proofObservedAt')::timestamptz<checked_at-interval '15 minutes'
   or (p_offer->>'generatedAt')::timestamptz<checked_at-interval '15 minutes'
   or (p_offer->>'startsAt')::timestamptz<checked_at+interval '24 hours') then
   raise exception 'session_not_available';
  end if;
 end;
 return option||jsonb_build_object('targetSessionId',target,'externalId',locked_external_id);$replacement$;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then
  raise exception 'native_skills_offer_wallclock_anchor_missing';
 end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 execute replace(definition,anchor,replacement);
end $wallclock_guard$;
revoke all on function public.materialize_native_skills_checkout(text,jsonb,text) from public,anon,authenticated;
grant execute on function public.materialize_native_skills_checkout(text,jsonb,text) to service_role;
commit;
