-- REVIEW ONLY: after collector gateway draft in disposable PostgreSQL.
-- Not a migration or attestation service. Existing intake owns issue identity.
begin;
create function production_board_private.production_board_read_source_binding(p_card uuid)
returns jsonb language plpgsql stable security invoker set search_path='' as $$
declare b record;
begin
  if current_user<>'production_board_collector'
    or not pg_has_role(session_user,'production_board_collector','MEMBER') then
    raise exception 'collector_role_required';
  end if;
  if p_card is null then raise exception 'invalid_card_id'; end if;
  -- One statement snapshot binds version/state to canonical intake. No lease:
  -- the publisher must revalidate expected version after source acquisition.
  select c.id,c.row_version,c.resolution_state,i.issue_id into b
    from public.production_board_cards c
    join public.production_board_dispatch_intake i on i.card_id=c.id
    where c.id=p_card;
  if not found then
    return jsonb_build_object('decision','review','reason','canonical_binding_missing','can_execute',false);
  end if;
  if b.resolution_state<>'unresolved' then
    return jsonb_build_object('decision','skip','reason','card_resolved','can_execute',false);
  end if;
  if b.issue_id<1 or b.issue_id>9007199254740991 then
    return jsonb_build_object('decision','review','reason','unsupported_issue_identity','can_execute',false);
  end if;
  return jsonb_build_object('decision','review','reason','underlying_source_check_required',
    'can_execute',false,'card_id',b.id,'issue_id',b.issue_id,'version',b.row_version::text,
    'source_ref','https://github.com/Brian910cpr/910cpr-class-landers/issues/'||b.issue_id::text);
end $$;
revoke all on function production_board_private.production_board_read_source_binding(uuid)
  from public,anon,authenticated,service_role;
grant execute on function production_board_private.production_board_read_source_binding(uuid)
  to production_board_collector;
commit;
