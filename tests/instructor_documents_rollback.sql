-- Run after the migration. Every fixture and audit mutation is rolled back.
begin;
do $test$
declare
  sid uuid; other_sid uuid; did uuid := gen_random_uuid(); actor text := 'Rollback test owner';
  rid uuid; source_id uuid; result jsonb; recovered public.class_session_documents%rowtype;
begin
  select id into sid from public.class_sessions order by start_at desc limit 1;
  select id into other_sid from public.class_sessions where id <> sid limit 1;
  if sid is null or other_sid is null then raise exception 'Existing class/session test prerequisites unavailable'; end if;
  if has_function_privilege('anon','public.remove_instructor_document(uuid,uuid,text)','execute')
    or has_function_privilege('authenticated','public.remove_instructor_document(uuid,uuid,text)','execute') then
    raise exception 'Removal RPC exposed to a client role';
  end if;
  if not has_function_privilege('service_role','public.remove_instructor_document(uuid,uuid,text)','execute') then raise exception 'Backend cannot call RPC'; end if;
  insert into public.class_session_documents(id,class_session_id,document_type,file_name,storage_bucket,storage_path,content_type,file_size,source)
  values(did,sid,'other','rollback-test-only.pdf','class-session-docs',sid::text||'/'||did::text||'.pdf','application/pdf',1,'instructor_workbench');
  result := public.remove_instructor_document(other_sid,did,actor);
  if result->>'error' <> 'document_not_found' then raise exception 'Wrong class accepted'; end if;
  if not exists(select 1 from public.class_session_documents where id=did) then raise exception 'Denied attempt removed document'; end if;
  insert into public.compliance_requirement_sources(source_key,authority,title,source_type)
    values('rollback-test:'||did::text,'test','Rollback test only','test') returning id into source_id;
  insert into public.compliance_requirements(requirement_key,source_id,requirement_text,evidence_type)
    values('rollback-test:'||did::text,source_id,'Rollback test only','document') returning id into rid;
  insert into public.session_compliance_requirements(class_session_id,requirement_id,status,evidence_document_id)
  values(sid,rid,'satisfied',did);
  result := public.remove_instructor_document(sid,did,actor);
  if result->>'error' <> 'document_in_use' then raise exception 'Linked evidence removed'; end if;
  if exists(select 1 from public.class_session_audit where class_session_id=sid and event_key='document_removed:'||did::text) then raise exception 'Denied removal created audit'; end if;
  delete from public.session_compliance_requirements where class_session_id=sid and requirement_id=rid;
  result := public.remove_instructor_document(sid,did,actor);
  if result->>'ok' <> 'true' then raise exception 'Removal did not succeed: %',result; end if;
  if exists(select 1 from public.class_session_documents where id=did) then raise exception 'Attachment still present'; end if;
  select restored.* into recovered from public.class_session_audit a,
    lateral jsonb_populate_record(null::public.class_session_documents,a.details->'removed_attachment') restored
    where a.class_session_id=sid and a.event_key='document_removed:'||did::text;
  if recovered.id is distinct from did or recovered.file_name <> 'rollback-test-only.pdf' then raise exception 'Recovery snapshot invalid'; end if;
  result := public.remove_instructor_document(sid,did,actor);
  if result->>'already_removed' <> 'true' then raise exception 'Retry not idempotent'; end if;
  if (select count(*) from public.class_session_audit where class_session_id=sid and event_key='document_removed:'||did::text)<>1 then raise exception 'Duplicate removal audit'; end if;
  insert into public.class_session_documents select (recovered).*;
  if not exists(select 1 from public.class_session_documents where id=did) then raise exception 'Recovery did not restore attachment'; end if;
end
$test$;
rollback;
select 'passed: backend-only client grants, class scope, evidence protection, atomic removal, audit snapshot, retry, recovery; all fixtures rolled back' as verification;
