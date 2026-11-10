-- Immutable creator lineage, independent of optional profile snapshots attached
-- during legacy receipt recovery. Existing rows remain legacy; no backfill.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
lock table public.landerware_public_orders in access exclusive mode;
do $guard$ begin
 if not exists(select 1 from information_schema.columns where table_schema='public' and table_name='landerware_public_orders' and column_name='checkout_runtime_version') then
  if exists(select 1 from public.landerware_public_orders where request_fingerprint is not null) then raise exception 'native_orders_require_version_reconciliation'; end if;
 end if;
end $guard$;
alter table public.landerware_public_orders add column if not exists checkout_runtime_version text not null default 'legacy' check(checkout_runtime_version in ('legacy','native-v1'));
create or replace function public.native_checkout_order_version_immutable() returns trigger
language plpgsql security invoker set search_path='' as $$
begin
 if new.checkout_runtime_version is distinct from old.checkout_runtime_version then raise exception 'order_version_immutable'; end if;
 return new;
end $$;
revoke all on function public.native_checkout_order_version_immutable() from public,anon,authenticated;
grant execute on function public.native_checkout_order_version_immutable() to service_role;
create or replace trigger native_checkout_order_version_immutable before update on public.landerware_public_orders for each row execute function public.native_checkout_order_version_immutable();
do $versions$ declare definition text; old_text text; new_text text;
begin
 definition:=pg_get_functiondef('public.native_checkout_create_order(text,text,text,text,text,jsonb,text,jsonb)'::regprocedure);
 if position('checkout_runtime_version' in definition)=0 then
  old_text:='insert into public.landerware_public_orders(idempotency_key,request_fingerprint,';
  new_text:='insert into public.landerware_public_orders(checkout_runtime_version,idempotency_key,request_fingerprint,';
  if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'unsupported_native_creator_version'; end if;
  definition:=replace(definition,old_text,new_text);
  old_text:='values(trim(p_idempotency_key),v_fingerprint,';new_text:='values(''native-v1'',trim(p_idempotency_key),v_fingerprint,';
  if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'unsupported_native_creator_version'; end if;
  execute replace(definition,old_text,new_text);
 end if;
 definition:=pg_get_functiondef('public.native_checkout_finalize_order(uuid,text,jsonb)'::regprocedure);
 if position('checkout_runtime_version' in definition)=0 then
  old_text:='if o.id is null then raise exception ''order_not_found''; end if;';
  new_text:=old_text||E'\n if o.checkout_runtime_version<>''native-v1'' then raise exception ''unsupported_order_version''; end if;';
  if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'unsupported_native_finalizer_version'; end if;
  execute replace(definition,old_text,new_text);
 end if;
 definition:=pg_get_functiondef('public.native_checkout_finalize_legacy_order(uuid,text,jsonb)'::regprocedure);
 if position('checkout_runtime_version' in definition)=0 then
  old_text:='if coalesce(o.registration_profile_snapshot,''{}''::jsonb)<>''{}''::jsonb then raise exception ''unsupported_order_version''; end if;';
  new_text:='if o.checkout_runtime_version<>''legacy'' then raise exception ''unsupported_order_version''; end if;';
  if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'unsupported_legacy_finalizer_version'; end if;
  execute replace(definition,old_text,new_text);
 end if;
end $versions$;

-- Old/new receipt namespaces share the ORIGINAL nonce lock. A recovered old
-- receipt must not race a new order into two independent ledgers.
do $receipts$ declare definition text; old_text text; new_text text;
begin
 definition:=pg_get_functiondef('public.reserve_skills_session_native(text,text,jsonb,jsonb)'::regprocedure);
 if position('native_checkout_legacy_nonce_v1' in definition)=0 then
  old_text:='if p_offer->>''startsAt'' is null then return jsonb_build_object(''ok'',false,''status'',''offer_required''); end if;';
  new_text:='-- native_checkout_legacy_nonce_v1'||E'\n if exists(select 1 from public.landerware_public_orders where idempotency_key=''public-order:''||p_idempotency_key) then raise exception ''generic_checkout_required''; end if;'||E'\n if exists(select 1 from public.skills_session_context_config cfg join public.courses c on c.id=cfg.course_id where cfg.context_key=p_context and c.registration_profile_key is not null) then raise exception ''generic_checkout_required''; end if;'||E'\n '||old_text;
  if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'unsupported_legacy_receipt_contract'; end if;
  execute replace(definition,old_text,new_text);
 end if;
 if to_regprocedure('public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)') is not null then
  definition:=pg_get_functiondef('public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer)'::regprocedure);
  if position('native_checkout_shared_nonce_v1' in definition)=0 then
   old_text:='perform pg_advisory_xact_lock(hashtextextended(''native-checkout-key|''||p_key,0));';
   new_text:='-- native_checkout_shared_nonce_v1'||E'\n perform pg_advisory_xact_lock(hashtextextended(''skills-claim|''||p_key,0));'||E'\n '||old_text;
   if (length(definition)-length(replace(definition,old_text,'')))/length(old_text)<>1 then raise exception 'unsupported_native_receipt_contract'; end if;
   execute replace(definition,old_text,new_text);
  end if;
 end if;
end $receipts$;
commit;
