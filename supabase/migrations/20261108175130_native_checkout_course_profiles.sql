begin;
-- Profiles are reused as declarative configuration only. Native orders and
-- canonical registrations do not write legacy landerware_registrations/people.
alter table public.landerware_registration_profiles add column if not exists form_schema jsonb not null default '{}';
alter table public.courses add column if not exists registration_profile_key text references public.landerware_registration_profiles(profile_key);
alter table public.landerware_public_orders add column if not exists registration_profile_snapshot jsonb not null default '{}';
alter table public.registrations add column if not exists native_checkout_profile_snapshot jsonb not null default '{}';
insert into public.landerware_confirmation_templates(template_key,subject_template,body_template,delivery_provider,active)
 values('native-checkout-profile-v1','Your 910CPR registration','Your registration and payment status are tracked by the native checkout.','cloudflare',false) on conflict(template_key) do nothing;
insert into public.landerware_registration_profiles(profile_key,version,course_id,display_name,listed,registration_mode,session_policy,allowed_entry_contexts,required_fields,requirements,addons,payer_policy,pricing_behavior,confirmation_template_key,form_schema,active)
 values('native_skills_shared',1,'skills-session-only','Skills session',false,'native_public_checkout','required',array[]::text[],'["first_name","last_name","email","online_completed","online_access_ack"]'::jsonb,'[{"key":"completion_document","type":"online_completion","display_name":"Online completion certificate","upload_now":true,"submit_later":true,"required_before_registration":false,"required_before_attendance":false,"required_before_completion":false,"upload":{"enabled":true,"field":"completion_document","max_bytes":2097152,"mime_types":["application/pdf","image/jpeg","image/png"]}}]'::jsonb,'[]','{"mode":"customer_pays"}','{"mode":"catalog_options"}','native-checkout-profile-v1','{"schemaVersion":"native-checkout.form.v1","description":"Choose your course option, then complete secure payment. Online coursework must be completed before the skills session.","fields":[{"key":"first_name","wire":"firstName","type":"text","label":"First name","required":true,"autocomplete":"given-name"},{"key":"last_name","wire":"lastName","type":"text","label":"Last name","required":true,"autocomplete":"family-name"},{"key":"email","wire":"email","type":"email","label":"Email","required":true,"autocomplete":"email","max_length":254},{"key":"phone","wire":"phone","type":"tel","label":"Phone","required":false,"autocomplete":"tel","max_length":50,"required_when_choice":"online_and_skills"},{"key":"online_completed","wire":"onlineCompleted","type":"checkbox","label":"I have completed the online portion for my skills session.","required":true,"unless_choice":"online_and_skills"},{"key":"online_access_ack","wire":"onlineCompletionAcknowledged","type":"checkbox","label":"I understand I must complete the provided online course before my skills session.","required":true,"when_choice":"online_and_skills"}],"allowed_contexts":["cpr-aed","first-aid-cpr-aed","arc-blended","hsi-blended","bls-skills"],"max_students":2,"default_choices":["skills_only"],"inventory_kind":"leased_skills_v1","option_groups":[{"key":"learning_path","label":"Course option","type":"radio","required":true,"price_mode":"course_total","choices":[{"key":"skills_only","label":"Skills session only — online course not included","catalog_keys":[],"bindings":{"learningPath":"skills-only"}},{"key":"online_and_skills","label":"HeartCode BLS online access + skills session","contexts":["bls-skills"],"catalog_keys":["aha_heartcode_bls_online"],"bindings":{"learningPath":"online-and-skills"}}]}],"driver_rules":[{"driver":"native_order"}],"public_aliases":[{"public_course_id":"210549","context":"bls-skills","default_choices":["online_and_skills"],"title":"HeartCode BLS + skills session"}],"back_url":"/classes/","back_urls":{"bls-skills":"/bls.html","hsi-blended":"/hsi.html","arc-blended":"/arc.html","cpr-aed":"/heartsaver.html","first-aid-cpr-aed":"/heartsaver.html"}}'::jsonb,true) on conflict(profile_key) do nothing;
update public.courses set registration_profile_key='native_skills_shared' where course_key='skills-session-only' and registration_profile_key is null;
insert into public.landerware_registration_profiles(profile_key,version,course_id,display_name,listed,registration_mode,session_policy,allowed_entry_contexts,required_fields,requirements,addons,payer_policy,pricing_behavior,confirmation_template_key,form_schema,active)
 values('native_bls_initial',1,'aha-bls-provider','BLS Provider — Initial',false,'native_public_checkout','required',array[]::text[],'["first_name","last_name","email","phone"]'::jsonb,'[]'::jsonb,'[]','{"mode":"customer_pays"}','{"mode":"catalog_options"}','native-checkout-profile-v1','{"schemaVersion":"native-checkout.form.v1","description":"Choose any available materials or course options. The saved order determines your final total.","fields":[{"key":"first_name","wire":"firstName","type":"text","label":"First name","required":true,"autocomplete":"given-name"},{"key":"last_name","wire":"lastName","type":"text","label":"Last name","required":true,"autocomplete":"family-name"},{"key":"email","wire":"email","type":"email","label":"Email","required":true,"autocomplete":"email","max_length":254},{"key":"phone","wire":"phone","type":"tel","label":"Phone","required":true,"autocomplete":"tel","max_length":50},{"key":"billing_code","wire":"billingCode","type":"text","label":"Promo or employer billing code (optional)","required":false}],"max_students":10,"default_choices":["own_copy","no_first_aid"],"driver_rules":[{"driver":"native_order"}],"inventory_kind":"scheduled_session_v1","option_groups":[{"key":"manual","label":"BLS manual","type":"radio","required":true,"choices":[{"key":"own_copy","label":"I have my own current manual","catalog_keys":[],"bindings":{"manualChoice":"own-copy"}},{"key":"manual_ebook","label":"Provider Manual eBook","catalog_keys":["aha_bls_provider_manual_ebook"],"bindings":{"manualChoice":"ebook"}}]},{"key":"first_aid","label":"First Aid option","type":"radio","required":true,"choices":[{"key":"no_first_aid","label":"No First Aid add-on","catalog_keys":[],"bindings":{"firstAidChoice":"none"}},{"key":"first_aid_class","label":"First Aid in person","catalog_keys":["aha_heartsaver_first_aid_in_person"],"bindings":{"firstAidChoice":"in-person"}},{"key":"first_aid_online","label":"First Aid online","catalog_keys":["aha_heartsaver_first_aid_online"],"bindings":{"firstAidChoice":"online"}}]}],"back_url":"/bls.html"}'::jsonb,true) on conflict(profile_key) do nothing;
update public.courses set registration_profile_key='native_bls_initial' where course_key='aha-bls-provider' and registration_profile_key is null;
insert into public.landerware_registration_profiles(profile_key,version,course_id,display_name,listed,registration_mode,session_policy,allowed_entry_contexts,required_fields,requirements,addons,payer_policy,pricing_behavior,confirmation_template_key,form_schema,active)
 values('native_bls_renewal',1,'aha-bls-provider-renewal','BLS Provider — Renewal',false,'native_public_checkout','required',array[]::text[],'["first_name","last_name","email","phone"]'::jsonb,'[]'::jsonb,'[]','{"mode":"customer_pays"}','{"mode":"catalog_options"}','native-checkout-profile-v1','{"schemaVersion":"native-checkout.form.v1","description":"Choose any available materials or course options. The saved order determines your final total.","fields":[{"key":"first_name","wire":"firstName","type":"text","label":"First name","required":true,"autocomplete":"given-name"},{"key":"last_name","wire":"lastName","type":"text","label":"Last name","required":true,"autocomplete":"family-name"},{"key":"email","wire":"email","type":"email","label":"Email","required":true,"autocomplete":"email","max_length":254},{"key":"phone","wire":"phone","type":"tel","label":"Phone","required":true,"autocomplete":"tel","max_length":50},{"key":"billing_code","wire":"billingCode","type":"text","label":"Promo or employer billing code (optional)","required":false}],"max_students":10,"default_choices":["own_copy","no_first_aid"],"driver_rules":[{"driver":"native_order"}],"inventory_kind":"scheduled_session_v1","option_groups":[{"key":"manual","label":"BLS manual","type":"radio","required":true,"choices":[{"key":"own_copy","label":"I have my own current manual","catalog_keys":[],"bindings":{"manualChoice":"own-copy"}},{"key":"manual_ebook","label":"Provider Manual eBook","catalog_keys":["aha_bls_provider_manual_ebook"],"bindings":{"manualChoice":"ebook"}}]},{"key":"first_aid","label":"First Aid option","type":"radio","required":true,"choices":[{"key":"no_first_aid","label":"No First Aid add-on","catalog_keys":[],"bindings":{"firstAidChoice":"none"}},{"key":"first_aid_class","label":"First Aid in person","catalog_keys":["aha_heartsaver_first_aid_in_person"],"bindings":{"firstAidChoice":"in-person"}},{"key":"first_aid_online","label":"First Aid online","catalog_keys":["aha_heartsaver_first_aid_online"],"bindings":{"firstAidChoice":"online"}}]}],"back_url":"/bls.html"}'::jsonb,true) on conflict(profile_key) do nothing;
update public.courses set registration_profile_key='native_bls_renewal' where course_key='aha-bls-provider-renewal' and registration_profile_key is null;

create or replace function public.native_checkout_profile_version_guard() returns trigger
language plpgsql security invoker set search_path='' as $$
begin
 if old.registration_mode='native_public_checkout' or new.registration_mode='native_public_checkout' then
  if new.version<old.version or ((to_jsonb(new)-array['version','updated_at','active','listed']) is distinct from (to_jsonb(old)-array['version','updated_at','active','listed']) and new.version<=old.version)
  then raise exception 'registration_profile_version_required'; end if;
 end if;
 return new;
end $$;
revoke all on function public.native_checkout_profile_version_guard() from public,anon,authenticated;
create trigger native_checkout_profile_version_guard before update on public.landerware_registration_profiles
 for each row execute function public.native_checkout_profile_version_guard();

create or replace function public.native_checkout_profile(p_public_course_id text,p_context text default null) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare c public.courses; p public.landerware_registration_profiles; catalog public.landerware_registration_catalog;
begin
 if (select count(*) from public.landerware_registration_profiles r join public.courses x on x.registration_profile_key=r.profile_key
      where r.active and r.registration_mode='native_public_checkout' and exists(select 1 from jsonb_array_elements(coalesce(r.form_schema->'public_aliases','[]')) a
       where a->>'public_course_id'=p_public_course_id and (a->>'context' is null or a->>'context'=p_context)))>1 then raise exception 'native_profile_not_configured'; end if;
 select x.* into c from public.landerware_registration_profiles r join public.courses x on x.registration_profile_key=r.profile_key
   where r.active and r.registration_mode='native_public_checkout' and exists(select 1 from jsonb_array_elements(coalesce(r.form_schema->'public_aliases','[]')) a where a->>'public_course_id'=p_public_course_id and (a->>'context' is null or a->>'context'=p_context));
 if c.id is null then select * into c from public.courses where enrollware_course_id=p_public_course_id; end if;
 select * into p from public.landerware_registration_profiles where profile_key=c.registration_profile_key and active and registration_mode='native_public_checkout';
 if p.profile_key is null or p.course_id is distinct from c.course_key then raise exception 'native_profile_not_configured'; end if;
 select * into catalog from public.landerware_registration_catalog where course_id=c.enrollware_course_id and active;
 if catalog.course_id is null or catalog.currency<>'usd' or catalog.unit_amount<=0 or c.base_price*100 is distinct from catalog.unit_amount::numeric then raise exception 'price_catalog_missing'; end if;
 return jsonb_build_object('profile',to_jsonb(p),'physicalCourseId',c.enrollware_course_id,'catalog',jsonb_build_object('course_id',catalog.course_id,'course_name',catalog.course_name,'unit_amount',catalog.unit_amount,'currency',catalog.currency,'addons',catalog.addons));
end $$;

create or replace function public.native_checkout_bind_profile(p_key text,p_profile_key text,p_version integer,p_driver text,p_context text,p_selection jsonb,p_inputs jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare p public.landerware_registration_profiles; c public.courses; o public.landerware_public_orders; receipt public.skills_session_claim_receipts; r public.registrations; snap jsonb;
begin
 if p_driver is null or p_driver not in ('native_order','public_session','skills_reservation','skills_bundle') then raise exception 'invalid_checkout_profile'; end if;
 select * into strict p from public.landerware_registration_profiles where profile_key=p_profile_key and version=p_version and active and registration_mode='native_public_checkout' for share;
 select * into o from public.landerware_public_orders where idempotency_key='public-order:'||p_key for update;
 select * into receipt from public.skills_session_claim_receipts where idempotency_key=p_key;
 if o.id is not null and receipt.registration_id is not null then raise exception 'ambiguous_checkout_receipt'; end if;
 if o.id is not null then select x.* into c from public.class_sessions s join public.courses x on x.id=s.course_id where s.id=o.class_session_id;
 else select * into r from public.registrations where id=receipt.registration_id for update;select x.* into c from public.class_sessions s join public.courses x on x.id=s.course_id where s.id=r.class_session_id; end if;
 if c.id is null or c.registration_profile_key is distinct from p.profile_key or c.course_key is distinct from p.course_id then raise exception 'invalid_checkout_profile'; end if;
 snap:=public.native_checkout_profile(c.enrollware_course_id,p_context)||jsonb_build_object('driver',p_driver,'context',p_context,'selection',p_selection,'inputs',p_inputs);
 if o.id is not null then
  if o.registration_profile_snapshot<>'{}'::jsonb then return o.registration_profile_snapshot; end if;
  update public.landerware_public_orders set registration_profile_snapshot=snap where id=o.id;
  if jsonb_array_length(p_inputs)>0 then
   update public.landerware_public_order_students st set selected_options=st.selected_options||jsonb_build_object('clientIndex',input.ordinality-1)
   from jsonb_array_elements(p_inputs) with ordinality input(value,ordinality)
   where st.order_id=o.id and st.email=lower(trim(input.value->'wire'->>'email'));
   if (select count(*) from public.landerware_public_order_students st where st.order_id=o.id and st.selected_options ? 'clientIndex')<>jsonb_array_length(p_inputs) then raise exception 'invalid_request'; end if;
  end if;
 else
  if r.native_checkout_profile_snapshot<>'{}'::jsonb then return r.native_checkout_profile_snapshot; end if;
  update public.registrations set native_checkout_profile_snapshot=snap where id=r.id;
 end if;
 return snap;
end $$;

create table public.native_checkout_upload_intents(
 id uuid primary key default gen_random_uuid(),registration_id uuid references public.registrations(id),
 public_order_student_id uuid references public.landerware_public_order_students(id),class_session_id uuid not null references public.class_sessions(id),
 profile_key text not null references public.landerware_registration_profiles(profile_key),profile_version integer not null,
 requirement_key text not null,requirement_snapshot jsonb not null,sha256 text not null check(sha256~'^[a-f0-9]{64}$'),
 content_type text not null,file_size bigint not null check(file_size>0 and file_size<=10485760),storage_bucket text not null default 'class-session-docs' check(storage_bucket='class-session-docs'),
 storage_path text not null unique,state text not null default 'pending_storage' check(state in ('pending_storage','received')),
 document_id uuid references public.class_session_documents(id),created_at timestamptz not null default now(),received_at timestamptz,
 check(num_nonnulls(registration_id,public_order_student_id)=1),check((state='received')=(document_id is not null))
);
create unique index native_checkout_upload_identity on public.native_checkout_upload_intents(coalesce(registration_id,public_order_student_id),(registration_id is not null),requirement_key,sha256);
alter table public.native_checkout_upload_intents enable row level security;
revoke all on public.native_checkout_upload_intents from public,anon,authenticated;
grant all on public.native_checkout_upload_intents to service_role;

create or replace function public.native_checkout_receipt(p_key text) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare o public.landerware_public_orders; receipt public.skills_session_claim_receipts; r public.registrations; s public.class_sessions; c public.courses; snap jsonb; status text; amount integer;
begin
 select * into o from public.landerware_public_orders where idempotency_key='public-order:'||p_key;
 select * into receipt from public.skills_session_claim_receipts where idempotency_key=p_key;
 if o.id is not null and receipt.registration_id is not null then raise exception 'ambiguous_checkout_receipt'; end if;
 if o.id is not null then
  select * into s from public.class_sessions where id=o.class_session_id;
  return jsonb_build_object('kind','public_order','orderId',o.id,'physicalCourseId',(select enrollware_course_id from public.courses where id=s.course_id),'context',(select st.selected_options->>'skillsContext' from public.landerware_public_order_students st where st.order_id=o.id limit 1),'sessionId',s.id,'status',o.status,'amountCents',o.total,'currency',o.currency,
   'startsAt',s.start_at,'endsAt',s.end_at,'location',(select name from public.locations where id=s.location_id),
   'holdExpiresAt',o.hold_expires_at,'paymentObserved',coalesce(o.payment_evidence->>'payment_status'='paid',false),'reconciliationError',o.reconciliation_error,'profileSnapshot',o.registration_profile_snapshot,
   'students',(select jsonb_agg(jsonb_build_object('id',st.id,'registrationId',st.registration_id,'options',st.selected_options,'addons',st.selected_addons) order by coalesce((st.selected_options->>'clientIndex')::integer,2147483647),st.created_at,st.id) from public.landerware_public_order_students st where st.order_id=o.id));
 end if;
 if receipt.registration_id is null then raise exception 'reservation_not_found'; end if;
 select * into r from public.registrations where id=receipt.registration_id;
 select * into s from public.class_sessions where id=r.class_session_id;
 select x.status,(x.total_amount*100)::integer into status,amount from public.registration_orders x where x.registration_id=r.id;
 return jsonb_build_object('kind','skills_reservation','registrationId',r.id,'physicalCourseId',(select enrollware_course_id from public.courses where id=s.course_id),'sessionId',s.id,'status',case when status='paid' then 'paid' else r.status end,
  'amountCents',amount,'currency','usd','startsAt',s.start_at,'endsAt',s.end_at,'location',(select name from public.locations where id=s.location_id),
  'context',receipt.result->>'context','profileSnapshot',r.native_checkout_profile_snapshot,'students',jsonb_build_array(jsonb_build_object('id',r.id,'registrationId',r.id)));
end $$;

create or replace function public.native_checkout_begin_upload(p_key text,p_student_index integer,p_requirement_key text,p_sha text,p_type text,p_size bigint)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare receipt jsonb; student jsonb; c public.courses; p public.landerware_registration_profiles; req jsonb; reg uuid; student_id uuid; intent public.native_checkout_upload_intents; path text; ext text;
begin
 receipt:=public.native_checkout_receipt(p_key);
 if receipt->>'status' not in ('held','checkout_open','paid','registered','active','confirmed','completed') or
  (receipt->>'kind'='public_order' and receipt->>'status'<>'paid' and (receipt->>'holdExpiresAt')::timestamptz<=now()) then raise exception 'session_not_available'; end if;
 if p_student_index is null or p_student_index<0 or p_student_index>=jsonb_array_length(receipt->'students') or p_requirement_key is null or p_requirement_key !~ '^[A-Za-z][A-Za-z0-9_-]{0,79}$' then raise exception 'invalid_request'; end if;
 student:=receipt->'students'->p_student_index;
 select x.* into c from public.class_sessions s join public.courses x on x.id=s.course_id where s.id=(receipt->>'sessionId')::uuid;
 select * into p from public.landerware_registration_profiles where profile_key=c.registration_profile_key and active and registration_mode='native_public_checkout' for share;
 select value into req from jsonb_array_elements(coalesce(p.requirements,'[]')) where value->>'key'=p_requirement_key and value->>'upload_now'='true' and coalesce(value->'upload'->>'enabled','true')='true';
 if req is null then raise exception 'uploads_disabled'; end if;
 ext:=case p_type when 'application/pdf' then 'pdf' when 'image/jpeg' then 'jpg' when 'image/png' then 'png' when 'image/webp' then 'webp' end;
 if p_sha is null or p_sha !~ '^[a-f0-9]{64}$' or ext is null or p_size is null or p_size<1 or p_size>least(coalesce((req->'upload'->>'max_bytes')::bigint,2097152),10485760)
  or not coalesce(req->'upload'->'mime_types' ? p_type,false) then raise exception 'invalid_document'; end if;
 if not exists(select 1 from storage.buckets where id='class-session-docs' and not public) then raise exception 'document_unavailable'; end if;
 if receipt->>'kind'='public_order' then student_id:=(student->>'id')::uuid; else reg:=(student->>'registrationId')::uuid; end if;
 perform pg_advisory_xact_lock(hashtextextended('native-upload|'||coalesce(reg,student_id)::text||'|'||p_requirement_key||'|'||p_sha,0));
 select * into intent from public.native_checkout_upload_intents where registration_id is not distinct from reg and public_order_student_id is not distinct from student_id and requirement_key=p_requirement_key and sha256=p_sha;
 if intent.id is not null then
  if intent.content_type<>p_type or intent.file_size<>p_size then raise exception 'invalid_document'; end if;
  return to_jsonb(intent);
 end if;
 path:=(receipt->>'sessionId')||'/checkout/'||coalesce(reg,student_id)::text||'/'||p_requirement_key||'/'||p_sha||'.'||ext;
 insert into public.native_checkout_upload_intents(registration_id,public_order_student_id,class_session_id,profile_key,profile_version,requirement_key,requirement_snapshot,sha256,content_type,file_size,storage_path)
 values(reg,student_id,(receipt->>'sessionId')::uuid,p.profile_key,p.version,p_requirement_key,req,p_sha,p_type,p_size,path) returning * into intent;
 return to_jsonb(intent);
end $$;

create or replace function public.native_checkout_record_received(p_registration_id uuid,p_intent_id uuid) returns void
language plpgsql security invoker set search_path='' as $$
declare i public.native_checkout_upload_intents; existing public.registration_requirements;
begin
 select * into strict i from public.native_checkout_upload_intents where id=p_intent_id and state='received';
 if i.registration_id is distinct from p_registration_id and not exists(select 1 from public.landerware_public_order_students st where st.id=i.public_order_student_id and st.registration_id=p_registration_id) then raise exception 'invalid_request'; end if;
 perform pg_advisory_xact_lock(hashtextextended('native-requirement|'||p_registration_id::text||'|'||i.requirement_key,0));
 select * into existing from public.registration_requirements where registration_id=p_registration_id and requirement_key=i.requirement_key order by created_at,id limit 1 for update;
 if existing.id is null then
  insert into public.registration_requirements(registration_id,requirement_key,requirement_type,state,source,provenance)
  values(p_registration_id,i.requirement_key,i.requirement_snapshot->>'type','unknown','native_checkout',jsonb_build_object('evidence_status','received','review_state','pending','document_id',i.document_id,'profile_key',i.profile_key,'profile_version',i.profile_version));
 else
  -- Keep any earlier staff decision/evidence intact. A new upload is another
  -- pending item, never an automatic replacement for an approved document.
  update public.registration_requirements set provenance=provenance||jsonb_build_object('pending_uploads',coalesce(provenance->'pending_uploads','{}')||jsonb_build_object(i.id::text,jsonb_build_object('evidence_status','received','review_state','pending','document_id',i.document_id,'profile_key',i.profile_key,'profile_version',i.profile_version))),updated_at=now() where id=existing.id;
 end if;
end $$;

create or replace function public.native_checkout_finish_upload(p_intent_id uuid) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare i public.native_checkout_upload_intents; doc uuid; reg uuid;
begin
 select * into strict i from public.native_checkout_upload_intents where id=p_intent_id for update;
 if i.state='received' then return jsonb_build_object('ok',true,'documentId',i.document_id,'evidenceStatus','received','approved',false,'idempotentReplay',true); end if;
 if not exists(select 1 from storage.buckets where id=i.storage_bucket and not public) or not exists(select 1 from storage.objects where bucket_id=i.storage_bucket and name=i.storage_path) then raise exception 'document_storage_pending'; end if;
 insert into public.class_session_documents(class_session_id,document_type,file_name,storage_bucket,storage_path,content_type,file_size,sha256,source)
 values(i.class_session_id,i.requirement_snapshot->>'type',left(coalesce(i.requirement_snapshot->>'display_name','Supporting document'),150),i.storage_bucket,i.storage_path,i.content_type,i.file_size,i.sha256,'native_checkout')
 on conflict(storage_bucket,storage_path) do update set storage_path=excluded.storage_path returning id into doc;
 update public.native_checkout_upload_intents set state='received',document_id=doc,received_at=now() where id=i.id;
 reg:=i.registration_id;
 if i.public_order_student_id is not null then
  select registration_id into reg from public.landerware_public_order_students where id=i.public_order_student_id for update;
  update public.landerware_public_order_students set selected_options=selected_options||jsonb_build_object('checkoutUploads',coalesce(selected_options->'checkoutUploads','{}')||jsonb_build_object(i.requirement_key,jsonb_build_object('documentId',doc,'evidenceStatus','received','approved',false))) where id=i.public_order_student_id;
 end if;
 if reg is not null then perform public.native_checkout_record_received(reg,i.id); end if;
 return jsonb_build_object('ok',true,'documentId',doc,'evidenceStatus','received','approved',false);
end $$;

revoke all on function public.native_checkout_profile(text,text),public.native_checkout_bind_profile(text,text,integer,text,text,jsonb,jsonb),public.native_checkout_receipt(text),public.native_checkout_begin_upload(text,integer,text,text,text,bigint),public.native_checkout_record_received(uuid,uuid),public.native_checkout_finish_upload(uuid) from public,anon,authenticated;
grant execute on function public.native_checkout_profile(text,text),public.native_checkout_bind_profile(text,text,integer,text,text,jsonb,jsonb),public.native_checkout_receipt(text),public.native_checkout_begin_upload(text,integer,text,text,text,bigint),public.native_checkout_record_received(uuid,uuid),public.native_checkout_finish_upload(uuid) to service_role;

-- One entry point for every new form. Existing registration receipts keep their
-- original payment adapter, but new enrollments use canonical atomic orders.
create or replace function public.materialize_native_skills_checkout(p_context text,p_offer jsonb,p_idempotency_key text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare option jsonb; target uuid; locked_external_id text;
begin
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

 return option||jsonb_build_object('targetSessionId',target,'externalId',locked_external_id);
end $$;

create or replace function public.reserve_native_checkout_order(p_key text,p_profile_key text,p_version integer,p_context text,p_external_id text,p_offer jsonb,p_students jsonb,p_inputs jsonb,p_expected_total integer)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare p public.landerware_registration_profiles; c public.courses; o public.landerware_public_orders; old_receipt public.skills_session_claim_receipts;
 option jsonb; external_id text; result jsonb; snapshot jsonb; wanted integer;
begin
 if p_key is null or p_key !~ '^[a-f0-9-]{36}$' or jsonb_typeof(p_students) is distinct from 'array' or jsonb_typeof(p_inputs) is distinct from 'array'
  or p_expected_total is null or p_expected_total<=0 or p_expected_total>10000000 then raise exception 'invalid_request'; end if;
 perform pg_advisory_xact_lock(hashtextextended('native-checkout-key|'||p_key,0));
 select * into o from public.landerware_public_orders where idempotency_key='public-order:'||p_key;
 select * into old_receipt from public.skills_session_claim_receipts where idempotency_key=p_key;
 if o.id is not null or old_receipt.registration_id is not null then
  if o.id is not null and o.registration_profile_snapshot<>'{}'::jsonb and o.registration_profile_snapshot->'inputs' is distinct from p_inputs then raise exception 'idempotency_conflict'; end if;
  return public.native_checkout_receipt(p_key);
 end if;
 select * into p from public.landerware_registration_profiles where profile_key=p_profile_key and version=p_version and active and registration_mode='native_public_checkout' for share;
 if p.profile_key is null then raise exception 'profile_changed'; end if;
 wanted:=jsonb_array_length(p_students);
 if wanted<1 or wanted>least(coalesce((p.form_schema->>'max_students')::integer,1),10) or jsonb_array_length(p_inputs)<>wanted then raise exception 'invalid_request'; end if;
 select * into c from public.courses where course_key=p.course_id and registration_profile_key=p.profile_key;
 if c.id is null then raise exception 'native_profile_not_configured'; end if;
 if nullif(p_external_id,'') is null then
  if p.form_schema->>'inventory_kind' is distinct from 'leased_skills_v1' or not coalesce(p.form_schema->'allowed_contexts' ? p_context,false) then raise exception 'invalid_context'; end if;
  if not (p_offer ? 'startsAt') then return jsonb_build_object('status','offer_required'); end if;
  option:=public.materialize_native_skills_checkout(p_context,p_offer,p_key);
  if (option->>'courseId')::uuid is distinct from c.id then raise exception 'invalid_checkout_profile'; end if;
  external_id:=option->>'externalId';
 else
  if p.form_schema->>'inventory_kind' is distinct from 'scheduled_session_v1' or
   (select count(*) from public.class_sessions s where s.external_class_id=p_external_id and s.record_scope='operational' and s.course_id=c.id)<>1 then raise exception 'session_not_open'; end if;
  external_id:=p_external_id;
 end if;
 result:=public.landerware_create_public_order('public-order:'||p_key,external_id,c.enrollware_course_id,lower(trim(p_students->0->>'email')),trim(p_students->0->>'phone'),p_students,null,
  jsonb_build_object('profile_fields_validated',true,'profile_key',p.profile_key,'profile_version',p.version));
 select * into strict o from public.landerware_public_orders where id=(result->>'orderId')::uuid;
 if o.total<=0 then raise exception 'billing_approval_required'; end if;
 if o.total>p_expected_total or (o.total<>p_expected_total and not exists(select 1 from jsonb_array_elements(p_students) st where nullif(trim(st->>'billingCode'),'') is not null)) then raise exception 'profile_price_mismatch'; end if;
 snapshot:=public.native_checkout_bind_profile(p_key,p.profile_key,p.version,'native_order',p_context,
  jsonb_build_object('externalId',external_id,'offerId',p_offer->>'selectionId'),p_inputs);
 return public.native_checkout_receipt(p_key);
end $$;

create or replace function public.native_checkout_payment_allowed(p_key text) returns boolean
language plpgsql stable security invoker set search_path='' as $$
declare receipt jsonb; profile jsonb; req jsonb; student jsonb; idx integer:=0; choices jsonb;
begin
 receipt:=public.native_checkout_receipt(p_key);
 if receipt->>'status'='paid' then return true; end if;
 profile:=receipt->'profileSnapshot'->'profile';
 if profile is null then return true; end if; -- existing pre-profile quotes
 for student in select value from jsonb_array_elements(receipt->'students') loop
  choices:=coalesce(receipt->'profileSnapshot'->'inputs'->idx->'selectedChoices','[]');
  for req in select value from jsonb_array_elements(coalesce(profile->'requirements','[]')) where value->>'required_before_registration'='true' loop
   if (req->>'when_choice' is null or choices ? (req->>'when_choice')) and (req->>'unless_choice' is null or not (choices ? (req->>'unless_choice'))) then
    if not exists(select 1 from public.native_checkout_upload_intents i where i.state='received' and i.requirement_key=req->>'key' and i.requirement_snapshot->>'type'=req->>'type' and i.file_size<=coalesce((req->'upload'->>'max_bytes')::bigint,2097152) and coalesce(req->'upload'->'mime_types','[]') ? i.content_type
      and ((receipt->>'kind'='public_order' and i.public_order_student_id=(student->>'id')::uuid) or (receipt->>'kind'='skills_reservation' and i.registration_id=(student->>'registrationId')::uuid))) then return false; end if;
   end if;
  end loop;
  idx:=idx+1;
 end loop;
 return true;
end $$;
revoke all on function public.materialize_native_skills_checkout(text,jsonb,text),public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer),public.native_checkout_payment_allowed(text) from public,anon,authenticated;
grant execute on function public.materialize_native_skills_checkout(text,jsonb,text),public.reserve_native_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer),public.native_checkout_payment_allowed(text),public.native_checkout_profile_version_guard() to service_role;

commit;
