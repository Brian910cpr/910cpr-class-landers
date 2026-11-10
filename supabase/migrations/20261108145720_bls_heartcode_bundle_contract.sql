begin;
-- New BLS context is explicitly unactivated until production proof/configuration.
alter table public.skills_session_context_config drop constraint skills_session_context_config_context_key_check;
alter table public.skills_session_context_config add constraint skills_session_context_config_context_key_check
 check(context_key in ('cpr-aed','first-aid-cpr-aed','arc-blended','hsi-blended','bls-skills'));
insert into public.skills_session_context_config(context_key,course_id,qualification_course_id,enabled,capacity_policy_verified,policy_evidence)
 select 'bls-skills',id,id,false,true,'skills-session-policy.v1; BLS activation pending' from public.courses where enrollware_course_id='509474';
insert into public.landerware_registration_catalog(course_id,course_name,unit_amount,currency,addons,billing_codes,active)
 values('509474','Skills Session Only',5500,'usd',
 '[{"key":"aha_heartcode_bls_online","display_name":"Included HeartCode BLS online access","unit_amount":4000,"product_key":"aha-25-3553-heartcode-bls-online","manufacturer_sku":"25-3553","includes_online_program":true,"active":false}]','[]',true)
 on conflict(course_id) do nothing;

create or replace function public.bls_native_bundle_ready() returns boolean
language sql stable security invoker set search_path='' as $$
 select exists(select 1 from public.landerware_bls_bundle_policy b
 join public.products p on p.product_key=b.product_key and p.active and p.fulfillment_mode='digital_code' and p.customer_price*100=b.code_cents
 join public.landerware_registration_catalog c on c.course_id=b.course_id and c.active and c.currency='usd' and c.unit_amount=b.skills_cents
 where b.enabled and b.verified and b.total_cents=9500
 and exists(select 1 from jsonb_array_elements(c.addons) a where a->>'key'='aha_heartcode_bls_online' and a->>'product_key'=p.product_key
   and (a->>'unit_amount')::integer=b.code_cents and a->>'active'='true')
 and exists(select 1 from public.product_inventory_units u where u.product_id=p.id and u.status='available'
  and u.public_order_student_id is null and u.reserved_for_registration_id is null and u.exposed_at is null and u.fulfilled_at is null));
$$;

create or replace function public.skills_bundle_order(p_key text) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare o public.landerware_public_orders; st public.landerware_public_order_students; s public.class_sessions;
begin
 select * into o from public.landerware_public_orders where idempotency_key='public-order:'||p_key and course_id='509474';
 if not found then raise exception 'reservation_not_found'; end if;
 select * into strict st from public.landerware_public_order_students where order_id=o.id;
 if st.selected_options->>'skillsContext' is distinct from 'bls-skills' then raise exception 'invalid_request'; end if;
 select * into strict s from public.class_sessions where id=o.class_session_id;
 return jsonb_build_object('orderId',o.id,'sessionId',s.id,'studentId',st.id,'externalClassId',o.external_class_id,
  'status',o.status,'total',o.total,'startsAt',s.start_at,'location',(select name from public.locations where id=s.location_id),
  'reconciliationError',o.reconciliation_error,
  'checkoutId',o.stripe_checkout_session_id,'checkoutUrl',o.checkout_url,'holdExpiresAt',o.hold_expires_at,
  'certificatePrivate',exists(select 1 from storage.buckets where id='class-session-docs' and not public),
  'checkoutStudents',jsonb_build_array(jsonb_build_object('firstName',st.first_name,'lastName',st.last_name,'email',st.email,'phone',st.phone,
   'learningPath','online-and-skills','onlineCompletionAcknowledged',true,'skillsContext','bls-skills',
   'selectorSelectionId',st.selected_options->>'selectorSelectionId','addons',jsonb_build_array(jsonb_build_object('key','aha_heartcode_bls_online','quantity',1)))));
end $$;

create or replace function public.reserve_bls_bundle(p_idempotency_key text,p_context text,p_offer jsonb,p_student jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare option jsonb; target uuid; locked_external_id text; o public.landerware_public_orders; students jsonb; result jsonb;
begin
 if p_context is distinct from 'bls-skills' or p_idempotency_key is null or p_idempotency_key !~ '^[a-f0-9-]{36}$'
  or p_student->'onlineCompletionAcknowledged' is distinct from 'true'::jsonb then raise exception 'invalid_request'; end if;
 students:=jsonb_build_array(jsonb_build_object('firstName',trim(p_student->>'firstName'),'lastName',trim(p_student->>'lastName'),
  'email',lower(trim(p_student->>'email')),'phone',trim(p_student->>'phone'),'learningPath','online-and-skills',
  'onlineCompletionAcknowledged',true,'skillsContext',p_context,'selectorSelectionId',p_offer->>'selectionId',
  'addons',jsonb_build_array(jsonb_build_object('key','aha_heartcode_bls_online','quantity',1))));
 perform pg_advisory_xact_lock(hashtextextended('public-order-key|public-order:'||p_idempotency_key,0));
 select * into o from public.landerware_public_orders where idempotency_key='public-order:'||p_idempotency_key;
 if found then
  perform public.landerware_create_public_order('public-order:'||p_idempotency_key,o.external_class_id,'509474',
   lower(trim(p_student->>'email')),trim(p_student->>'phone'),students,null,'{}'::jsonb);
  return public.skills_bundle_order(p_idempotency_key);
 end if;
 if not (p_offer ? 'startsAt') then return jsonb_build_object('status','offer_required'); end if;
 if not public.bls_native_bundle_ready() then raise exception 'bundle_fulfillment_unavailable'; end if;
 option:=public.skills_session_native_option(p_context,p_offer);
 if option is null then raise exception 'session_not_available'; end if;
 locked_external_id:=option->>'externalId';
 perform pg_advisory_xact_lock(hashtextextended('landerware-public-offer|'||locked_external_id,0));
 -- Serialize ALL overlapping offer identities, not just identical selected IDs.
 lock table public.class_sessions in share row exclusive mode;
 lock table public.skills_session_context_config,public.courses,public.people,public.locations,public.instructor_qualifications in share mode;
 option:=public.skills_session_native_option(p_context,p_offer);
 if option is null or option->>'externalId' is distinct from locked_external_id then raise exception 'session_not_available'; end if;
 target:=(option->>'targetSessionId')::uuid;
 if target is not null then
  perform 1 from public.class_sessions where id=target for update;
  perform 1 from public.landerware_public_session_inventory where external_class_id=locked_external_id for update;
  option:=public.skills_session_native_option(p_context,p_offer);
  if option is null then raise exception 'session_not_available'; end if;
 end if;
 if target is null then
  insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,
    lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,
    source_offer_id,source_location_label,source_instructor_label,external_course_id,registration_url,price,advertised_duration_minutes,external_session_evidence)
  values('landerware_event','scheduled','operational',(option->>'courseId')::uuid,(option->>'startsAt')::timestamptz,
    (option->>'endsAt')::timestamptz,'America/New_York',(option->>'startsAt')::timestamptz,(option->>'consumptionEndsAt')::timestamptz,
    (option->>'instructorId')::uuid,(option->>'locationId')::uuid,(option->>'capacity')::integer,'landerware','public','open',
    option->>'externalId',p_offer->>'availabilityBlockId',p_offer->>'location',p_offer->>'instructor','509474',
    case when p_context='bls-skills' then '/bls.html?course=509474' when p_context='arc-blended' then '/arc.html?course=509474' when p_context='hsi-blended' then '/hsi.html?course=509474' else '/heartsaver.html?course=509474' end,55,45,
    jsonb_build_object('selectorOffer',p_offer,'materializedBy','skills_session_native')) returning id into target;
 end if;
 -- The canonical demand projection requires exactly one current workspace.
 -- Never overwrite a different existing identity/timing to manufacture proof.
 if exists(select 1 from public.landerware_sessions w where (w.class_session_id=target or w.external_session_id=option->>'externalId')
   and (w.class_session_id is distinct from target or w.external_session_id is distinct from option->>'externalId'
    or w.course_id is distinct from (select course_key from public.courses where id=(option->>'courseId')::uuid) or w.starts_at is distinct from (option->>'startsAt')::timestamptz
    or w.ends_at is distinct from (option->>'endsAt')::timestamptz)) then raise exception 'session_not_available'; end if;
 insert into public.landerware_sessions(external_session_id,class_session_id,course_id,course_name,starts_at,ends_at,location_name,instructor_name,provenance,requirements_manifest)
 values(option->>'externalId',target,(select course_key from public.courses where id=(option->>'courseId')::uuid),option->>'course',(option->>'startsAt')::timestamptz,(option->>'endsAt')::timestamptz,
  p_offer->>'location',p_offer->>'instructor','skills_session_native:'||p_idempotency_key,'{}'::jsonb)
 on conflict(external_session_id,course_id,starts_at) do nothing;
 if (select count(*) from public.landerware_sessions where class_session_id=target)<>1 then raise exception 'session_not_available'; end if;

 -- One transaction: any seat, inventory, or identity failure also rolls back the
 -- new class/workspace. Never call the internal inventory helper as an entry point.
 result:=public.landerware_create_public_order('public-order:'||p_idempotency_key,locked_external_id,'509474',
  lower(trim(p_student->>'email')),trim(p_student->>'phone'),students,null,'{}'::jsonb);
 return public.skills_bundle_order(p_idempotency_key);
end $$;

create or replace function public.attach_bls_bundle_certificate(p_key text,p_sha text,p_type text,p_size bigint) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare o public.landerware_public_orders; st public.landerware_public_order_students; path text; doc uuid; ext text;
begin
 select * into strict o from public.landerware_public_orders where idempotency_key='public-order:'||p_key and course_id='509474' for update;
 select * into strict st from public.landerware_public_order_students where order_id=o.id for update;
 if st.selected_options->>'skillsContext' is distinct from 'bls-skills' or o.status not in ('held','checkout_open','paid')
  or (o.status<>'paid' and o.hold_expires_at<=now()) then raise exception 'session_not_available'; end if;
 ext:=case p_type when 'application/pdf' then 'pdf' when 'image/jpeg' then 'jpg' when 'image/png' then 'png' end;
 if p_sha is null or p_sha !~ '^[a-f0-9]{64}$' or ext is null or p_size is null or p_size<1 or p_size>2097152 then raise exception 'invalid_certificate'; end if;
 if not exists(select 1 from storage.buckets where id='class-session-docs' and not public) then raise exception 'certificate_unavailable'; end if;
 path:=o.class_session_id::text||'/skills/bundle/'||st.id::text||'/'||p_sha||'.'||ext;
 insert into public.class_session_documents(class_session_id,document_type,file_name,storage_bucket,storage_path,content_type,file_size,sha256,source)
 values(o.class_session_id,'online_completion','Online completion certificate.'||ext,'class-session-docs',path,p_type,p_size,p_sha,'skills_registration')
 on conflict(storage_bucket,storage_path) do update set storage_path=excluded.storage_path returning id into doc;
 update public.landerware_public_order_students set selected_options=selected_options||jsonb_build_object('certificateDocumentId',doc) where id=st.id;
 if st.registration_id is not null then update public.registrations set optional_survey=optional_survey||jsonb_build_object('certificateDocumentId',doc),updated_at=now() where id=st.registration_id; end if;
 return jsonb_build_object('ok',true,'documentId',doc);
end $$;
revoke all on function public.bls_native_bundle_ready(),public.skills_bundle_order(text),public.reserve_bls_bundle(text,text,jsonb,jsonb),public.attach_bls_bundle_certificate(text,text,text,bigint) from public,anon,authenticated;
grant execute on function public.bls_native_bundle_ready(),public.skills_bundle_order(text),public.reserve_bls_bundle(text,text,jsonb,jsonb),public.attach_bls_bundle_certificate(text,text,text,bigint) to service_role;
create or replace function public.reserve_skills_session_native(p_idempotency_key text,p_context text,p_offer jsonb,p_student jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare receipt public.skills_session_claim_receipts; option jsonb; target uuid; customer uuid; registration uuid;
 fingerprint text; answer jsonb; first_name text; last_name text; email text; locked_external_id text;
begin
 if p_idempotency_key !~ '^[0-9a-f-]{36}$' or p_idempotency_key is null then raise exception 'invalid_request'; end if;
 first_name:=trim(p_student->>'firstName'); last_name:=trim(p_student->>'lastName'); email:=lower(trim(p_student->>'email'));
 if coalesce(first_name,'')='' or coalesce(last_name,'')='' or coalesce(email,'') !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
  or length(first_name)>100 or length(last_name)>100 or length(email)>254
  or p_student->>'onlineCompleted' is distinct from 'true' then raise exception 'invalid_student'; end if;
 fingerprint:=md5(jsonb_build_object('context',p_context,'selectionId',p_offer->>'selectionId',
  'firstName',first_name,'lastName',last_name,'email',email,'phone',trim(coalesce(p_student->>'phone','')),'onlineCompleted',true)::text);
 perform pg_advisory_xact_lock(hashtextextended('skills-claim|'||p_idempotency_key,0));
 select * into receipt from public.skills_session_claim_receipts where idempotency_key=p_idempotency_key;
 if receipt.idempotency_key is not null then
  if receipt.request_fingerprint<>fingerprint then raise exception 'idempotency_conflict'; end if;
  if not exists(select 1 from public.registrations where id=receipt.registration_id
    and status in ('registered','active','confirmed','completed')) then raise exception 'session_not_available'; end if;
  return receipt.result||jsonb_build_object('idempotentReplay',true,'paymentStatus',
    case when exists(select 1 from public.registration_orders where registration_id=receipt.registration_id and status='paid') then 'paid' else 'pending' end);
 end if;
 -- Service may first probe an identical saved request without fetching a new
 -- publication. A lost-response retry remains idempotent after lease expiry.
 if p_offer->>'startsAt' is null then return jsonb_build_object('ok',false,'status','offer_required'); end if;
 if exists(select 1 from public.skills_session_context_config cfg join public.courses c on c.id=cfg.course_id where cfg.context_key=p_context and nullif(to_jsonb(c)->>'registration_profile_key','') is not null) then raise exception 'generic_checkout_required'; end if;
 -- Match checkout/rescheduling lock order and identity before taking the global
 -- schedule lock. This also serializes existing-session paid/held seat claims.
 option:=public.skills_session_native_option(p_context,p_offer);
 if option is null then raise exception 'session_not_available'; end if;
 locked_external_id:=option->>'externalId';
 perform pg_advisory_xact_lock(hashtextextended('landerware-public-offer|'||locked_external_id,0));
 -- Serialize ALL overlapping offer identities, not just identical selected IDs.
 lock table public.class_sessions in share row exclusive mode;
 lock table public.skills_session_context_config,public.courses,public.people,public.locations,public.instructor_qualifications in share mode;
 option:=public.skills_session_native_option(p_context,p_offer);
 if option is null or option->>'externalId' is distinct from locked_external_id then raise exception 'session_not_available'; end if;
 target:=(option->>'targetSessionId')::uuid;
 if target is not null then
  perform 1 from public.class_sessions where id=target for update;
  perform 1 from public.landerware_public_session_inventory where external_class_id=locked_external_id for update;
  option:=public.skills_session_native_option(p_context,p_offer);
  if option is null then raise exception 'session_not_available'; end if;
 end if;
 if target is null then
  insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,
    lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,
    source_offer_id,source_location_label,source_instructor_label,external_course_id,registration_url,price,advertised_duration_minutes,external_session_evidence)
  values('landerware_event','scheduled','operational',(option->>'courseId')::uuid,(option->>'startsAt')::timestamptz,
    (option->>'endsAt')::timestamptz,'America/New_York',(option->>'startsAt')::timestamptz,(option->>'consumptionEndsAt')::timestamptz,
    (option->>'instructorId')::uuid,(option->>'locationId')::uuid,(option->>'capacity')::integer,'landerware','public','open',
    option->>'externalId',p_offer->>'availabilityBlockId',p_offer->>'location',p_offer->>'instructor','509474',
    case when p_context='bls-skills' then '/bls.html?course=509474' when p_context='arc-blended' then '/arc.html?course=509474' when p_context='hsi-blended' then '/hsi.html?course=509474' else '/heartsaver.html?course=509474' end,55,45,
    jsonb_build_object('selectorOffer',p_offer,'materializedBy','skills_session_native')) returning id into target;
 end if;
 -- The canonical demand projection requires exactly one current workspace.
 -- Never overwrite a different existing identity/timing to manufacture proof.
 if exists(select 1 from public.landerware_sessions w where (w.class_session_id=target or w.external_session_id=option->>'externalId')
   and (w.class_session_id is distinct from target or w.external_session_id is distinct from option->>'externalId'
    or w.course_id is distinct from (select course_key from public.courses where id=(option->>'courseId')::uuid) or w.starts_at is distinct from (option->>'startsAt')::timestamptz
    or w.ends_at is distinct from (option->>'endsAt')::timestamptz)) then raise exception 'session_not_available'; end if;
 insert into public.landerware_sessions(external_session_id,class_session_id,course_id,course_name,starts_at,ends_at,location_name,instructor_name,provenance,requirements_manifest)
 values(option->>'externalId',target,(select course_key from public.courses where id=(option->>'courseId')::uuid),option->>'course',(option->>'startsAt')::timestamptz,(option->>'endsAt')::timestamptz,
  p_offer->>'location',p_offer->>'instructor','skills_session_native:'||p_idempotency_key,'{}'::jsonb)
 on conflict(external_session_id,course_id,starts_at) do nothing;
 if (select count(*) from public.landerware_sessions where class_session_id=target)<>1 then raise exception 'session_not_available'; end if;
 if exists(select 1 from public.landerware_public_order_students st join public.landerware_public_orders o on o.id=st.order_id
   where o.class_session_id=target and st.email=lower(trim(p_student->>'email')) and o.status in ('held','checkout_open') and o.hold_expires_at>now())
 then raise exception 'student_already_held'; end if;
 if exists(select 1 from public.registrations r join public.customers c on c.id=r.customer_id
  where r.class_session_id=target and r.status in ('registered','active','confirmed','completed')
   and lower(trim(c.email))=lower(trim(p_student->>'email')) and lower(trim(c.first_name))=lower(trim(p_student->>'firstName'))
   and lower(trim(c.last_name))=lower(trim(p_student->>'lastName')))
 then raise exception 'already_registered'; end if;
 insert into public.customers(first_name,last_name,email,phone)
 values(first_name,last_name,email,nullif(trim(p_student->>'phone'),'')) returning id into customer;
 insert into public.registrations(customer_id,class_session_id,status,registration_source,idempotency_key,optional_survey)
 values(customer,target,'registered','landerware','skills-claim:'||p_idempotency_key,
  jsonb_build_object('skillsContext',p_context,'onlineCompleted',true,'priceCents',5500,'certificateUploadRequired',false)) returning id into registration;
 insert into public.registration_orders(registration_id,status,currency,course_amount,total_amount)
 values(registration,'payment_pending','usd',55,55);
 insert into public.participant_lifecycle_events(event_key,event_type,customer_id,registration_id,class_session_id,source,actor,details)
 values('skills-reserved:'||p_idempotency_key,'registration_created',customer,registration,target,'landerware',
  '{"kind":"public_registration"}'::jsonb,jsonb_build_object('context',p_context,'selectionId',p_offer->>'selectionId',
  'priceCents',5500,'paymentState','pending','certificateUploadRequired',false));
 answer:=jsonb_build_object('ok',true,'status','reserved','registrationId',registration,'sessionId',target,
  'startsAt',option->>'startsAt','endsAt',option->>'endsAt','location',option->>'location',
  'context',p_context,'amountCents',5500,'paymentStatus','pending','idempotentReplay',false);
 insert into public.skills_session_claim_receipts(idempotency_key,request_fingerprint,registration_id,result)
 values(p_idempotency_key,fingerprint,registration,answer);
 return answer;
end $$;
commit;
