-- Remove an attachment and retain its recovery record in one transaction.
-- Called only by the workbench backend after validating the existing login.
create or replace function public.remove_instructor_document(
  p_class_session_id uuid,
  p_document_id uuid,
  p_actor_session_hash text
) returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  doc public.class_session_documents%rowtype;
  audit_key text := 'document_removed:' || p_document_id::text;
begin
  if not exists (
    select 1 from public.maxim_portal_sessions
    where token_sha256 = p_actor_session_hash
      and revoked_at is null and expires_at > now()
  ) then
    return jsonb_build_object('error', 'unauthorized');
  end if;

  select * into doc from public.class_session_documents
  where id = p_document_id and class_session_id = p_class_session_id
  for update;
  if not found then
    if exists (select 1 from public.class_session_audit
      where class_session_id = p_class_session_id and event_key = audit_key) then
      return jsonb_build_object('ok', true, 'removed_id', p_document_id, 'already_removed', true);
    end if;
    return jsonb_build_object('error', 'document_not_found');
  end if;

  -- An upload used as compliance evidence must be replaced before it is removed.
  if exists (select 1 from public.session_compliance_requirements
    where evidence_document_id = p_document_id) then
    return jsonb_build_object('error', 'document_in_use');
  end if;

  insert into public.class_session_audit
    (class_session_id, event_key, event_type, actor_label, occurred_at, details)
  values (p_class_session_id, audit_key, 'document_removed',
    'Authenticated LanderWare workbench user', now(),
    jsonb_build_object('reason', 'Uploaded in error',
      'actor_session_fingerprint', left(p_actor_session_hash, 16),
      'removed_attachment', to_jsonb(doc), 'storage_object_preserved', true));

  delete from public.class_session_documents
  where id = p_document_id and class_session_id = p_class_session_id;
  return jsonb_build_object('ok', true, 'removed_id', p_document_id);
exception when foreign_key_violation then
  -- Includes evidence linked concurrently; the audit insert is rolled back too.
  return jsonb_build_object('error', 'document_in_use');
end;
$$;

revoke all on function public.remove_instructor_document(uuid, uuid, text) from public, anon, authenticated;
grant execute on function public.remove_instructor_document(uuid, uuid, text) to service_role;
