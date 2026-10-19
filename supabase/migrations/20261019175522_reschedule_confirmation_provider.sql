create or replace function public.confirm_registration_reschedule(p_token_sha256 text,p_target_session_id uuid,p_published_ids text[])
returns jsonb language plpgsql security invoker set search_path='' as $$
declare t public.registration_reschedule_links; r public.registrations; target public.class_sessions; original public.class_sessions;
 c public.customers; course public.courses; moved jsonb; v_result jsonb; reg_id uuid; duplicate public.registrations;
begin
 select * into t from public.registration_reschedule_links where token_sha256=p_token_sha256 for update;
 if t.id is null or t.revoked_at is not null or t.expires_at<=now() then raise exception 'invalid_or_expired_link'; end if;
 if t.used_at is not null then
   if (t.result->>'sessionId')::uuid<>p_target_session_id then raise exception 'link_already_used'; end if;
   return t.result||jsonb_build_object('idempotentReplay',true);
 end if;
 select * into r from public.registrations where id=t.registration_id for update;
 if r.status not in ('active','registered','confirmed') or exists(select 1 from public.participant_completions where registration_id=r.id) then raise exception 'registration_not_reschedulable'; end if;
 select * into original from public.class_sessions where id=r.class_session_id;
 -- Same row lock and offer advisory lock as checkout serialize competing seat claims.
 select * into target from public.class_sessions where id=p_target_session_id;
 if target.id is null then raise exception 'session_not_available'; end if;
 perform pg_advisory_xact_lock(hashtextextended('landerware-public-offer|'||target.external_class_id,0));
 select * into target from public.class_sessions where id=p_target_session_id for update;
 perform 1 from public.landerware_public_session_inventory where external_class_id=target.external_class_id for update;
 if not exists(select 1 from jsonb_array_elements(public.registration_reschedule_targets(r.id,p_published_ids,t.deadline_at)) x where (x->>'id')::uuid=target.id) then raise exception 'session_not_available'; end if;
 perform public.assert_public_registration_open(target.consumption_start_at,target.consumption_end_at,target.external_class_id);
 if exists(select 1 from public.registrations rr where rr.customer_id=r.customer_id and rr.class_session_id=target.id) then raise exception 'already_registered_for_target'; end if;
 -- An existing second financial order is ambiguous; require staff rather than lose a payment.
 if exists(select 1 from public.registrations rr join public.class_sessions ss on ss.id=rr.class_session_id
    where rr.customer_id=r.customer_id and rr.id<>r.id and ss.course_id=original.course_id and ss.start_at=original.start_at
      and rr.status in ('active','registered','confirmed') and (exists(select 1 from public.registration_orders o where o.registration_id=rr.id)
        or exists(select 1 from public.landerware_public_order_students os where os.registration_id=rr.id))) then raise exception 'duplicate_financial_record_requires_review'; end if;
 moved:=public.move_registration('self-reschedule:'||t.id,r.id,target.id,t.reason,'self_service_reschedule',jsonb_build_object('linkId',t.id),'transfer');
 reg_id:=(moved->>'target_registration_id')::uuid;
 update public.registrations set material_choice=r.material_choice,optional_survey=r.optional_survey where id=reg_id;
 -- Preserve original order contents and payer; change only this student's seat reference.
 update public.landerware_public_order_students set registration_id=reg_id where registration_id=r.id;
 -- Retire imported mirrors for exactly the same customer, course and start time.
 for duplicate in select rr.* from public.registrations rr join public.class_sessions ss on ss.id=rr.class_session_id
   where rr.customer_id=r.customer_id and rr.id<>r.id and ss.course_id=original.course_id and ss.start_at=original.start_at
    and rr.status in ('active','registered','confirmed') for update of rr loop
   if exists(select 1 from public.participant_completions where registration_id=duplicate.id) then raise exception 'duplicate_completion_requires_review'; end if;
   update public.registrations set status='rescheduled',updated_at=now() where id=duplicate.id;
   insert into public.participant_lifecycle_events(event_key,event_type,customer_id,registration_id,class_session_id,related_registration_id,source,details)
   values('reschedule-mirror:'||t.id||':'||duplicate.id,'moved',r.customer_id,duplicate.id,duplicate.class_session_id,reg_id,'self_service_reschedule',jsonb_build_object('duplicateOf',r.id,'linkId',t.id));
 end loop;
 select * into c from public.customers where id=r.customer_id;
 select * into course from public.courses where id=target.course_id;
 v_result:=jsonb_build_object('sessionId',target.id,'registrationId',reg_id,'course',course.name,'startsAt',target.start_at,'endsAt',target.end_at,'timezone',target.timezone,
   'location',coalesce((select name from public.locations where id=target.location_id),target.source_location_label,''),'confirmationStatus','pending');
 insert into public.landerware_messages(customer_id,operational_registration_id,template_key,channel,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key)
 values(c.id,reg_id,'registration-rescheduled-v1','email',c.email,'Your new class time is confirmed — '||course.name,
 'Hi '||c.first_name||E',\n\nYour class has been rescheduled.\n\n'||course.name||E'\n'||to_char(target.start_at at time zone 'America/New_York','FMDay, FMMonth DD, YYYY at FMHH12:MI AM')||E' Eastern\n'||(v_result->>'location')||
 E'\n\nYour existing registration, payments, and selected materials carry forward. No new registration or payment is needed.\n\nBrian Ennis\n910CPR\n910-395-5193',
 'resend','pending','reschedule-confirmation:'||t.id) on conflict(idempotency_key) do nothing;
 update public.registration_reschedule_links set used_at=now(),result=v_result where id=t.id;
 update public.registration_reschedule_links set revoked_at=now() where registration_id=r.id and id<>t.id and used_at is null and revoked_at is null;
 return v_result||jsonb_build_object('idempotentReplay',false);
end $$;

create or replace function public.request_registration_reschedule_help(p_token_sha256 text,p_message text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare t public.registration_reschedule_links; r public.registrations; c public.customers;
begin
 select * into t from public.registration_reschedule_links where token_sha256=p_token_sha256 for update;
 if t.id is null or t.revoked_at is not null or t.used_at is not null or t.expires_at<=now() then raise exception 'invalid_or_expired_link'; end if;
 if length(trim(p_message)) not between 1 and 2000 then raise exception 'invalid_help_message'; end if;
 select * into r from public.registrations where id=t.registration_id;
 select * into c from public.customers where id=r.customer_id;
 insert into public.landerware_messages(customer_id,operational_registration_id,template_key,channel,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key)
 values(c.id,r.id,'reschedule-help-v1','email','brian@910cpr.com','Rescheduling help requested',
 c.first_name||' '||c.last_name||E'\n'||c.email||E'\n\n'||trim(p_message),'resend','pending','reschedule-help:'||t.id)
 on conflict(idempotency_key) do update set body_text=excluded.body_text where public.landerware_messages.delivery_status='pending';
 return jsonb_build_object('ok',true);
end $$;


