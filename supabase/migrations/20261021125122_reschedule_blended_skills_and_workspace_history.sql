
DO $repair$
declare definition text;
begin
 select pg_get_functiondef(oid) into strict definition from pg_proc where pronamespace='public'::regnamespace and proname='registration_reschedule_dynamic_option';
 if position('329495' in definition)=0 then
 definition:=replace(definition,'''209806'',''359474'',''209809''','''209806'',''359474'',''209809'',''329495''');
 definition:=replace(definition,'else c.max_students_default end','when c.enrollware_course_id=''329495'' then least(4,c.max_students_default) else c.max_students_default end');
 execute definition;
 end if;
end $repair$;
CREATE OR REPLACE FUNCTION public.sync_workspace_registration_reschedule()
RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $fn$
declare original public.landerware_registrations; target_workspace uuid;
begin
 select * into original from public.landerware_registrations where id=new.source_registration_id;
 if original.id is null then return new; end if;
 select id into strict target_workspace from public.landerware_sessions where class_session_id=new.target_session_id;
 insert into public.landerware_registrations(id,person_id,requirement_id,session_id,organization_id,status,source,supersedes_registration_id,course_id,registration_profile_key,registration_profile_snapshot,entry_context,session_selection_status,selected_options,payer_mode,pricing_state,payment_state,billing_state)
 values(new.target_registration_id,original.person_id,original.requirement_id,target_workspace,original.organization_id,'active','self_service_reschedule',original.id,original.course_id,original.registration_profile_key,original.registration_profile_snapshot,original.entry_context,'selected',original.selected_options,original.payer_mode,original.pricing_state,original.payment_state,original.billing_state)
 on conflict(id) do nothing;
 update public.landerware_registrations set status='rescheduled',superseded_by_registration_id=new.target_registration_id,updated_at=now() where id=original.id;
 return new;
end $fn$;
REVOKE ALL ON FUNCTION public.sync_workspace_registration_reschedule() FROM PUBLIC,anon,authenticated;
DROP TRIGGER IF EXISTS sync_workspace_registration_reschedule ON public.registration_supersessions;
CREATE TRIGGER sync_workspace_registration_reschedule AFTER INSERT ON public.registration_supersessions FOR EACH ROW EXECUTE FUNCTION public.sync_workspace_registration_reschedule();
