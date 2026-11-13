-- Reviewed proposal: no activation, guessed canonical mappings or materials.
begin;
create table public.native_advanced_course_policy(
 course_number text primary key check(course_number in ('241108','209818','209805','251496')),
 course_id uuid references public.courses(id), profile_key text references public.landerware_registration_profiles(profile_key),
 page_key text not null check(page_key in ('acls','pals')), session_cents integer not null check(session_cents>0),
 instruction_minutes integer not null default 240 check(instruction_minutes=240),
 setup_minutes integer check(setup_minutes>=0),cleanup_minutes integer check(cleanup_minutes>=0),
 max_students integer check(max_students>0),location_id uuid references public.locations(id),
 resource_label text,location_label text,
 enabled boolean not null default false,publication_enabled boolean not null default false,
 verified boolean not null default false,evidence jsonb not null default '{}'
);
insert into public.native_advanced_course_policy(course_number,page_key,session_cents,evidence) values
 ('241108','acls',22500,'{"price":"data/config/block_schedule_pages.json","instruction":"data/inventory/course_consumption_rules.json:240"}'),
 ('209818','acls',22500,'{"price":"data/config/block_schedule_pages.json","instruction":"data/inventory/course_consumption_rules.json:240"}'),
 ('209805','pals',27500,'{"price":"data/config/block_schedule_pages.json","instruction":"data/inventory/course_consumption_rules.json:240"}'),
 ('251496','pals',22500,'{"price":"data/config/block_schedule_pages.json","instruction":"data/inventory/course_consumption_rules.json:240"}');
-- Drafts are unlisted/inactive and unbound. Missing product catalog keys
-- render book choices unavailable rather than creating zero/guessed prices.
insert into public.landerware_registration_profiles(profile_key,version,course_id,display_name,listed,registration_mode,session_policy,allowed_entry_contexts,required_fields,requirements,addons,payer_policy,pricing_behavior,confirmation_template_key,form_schema,active) values
('native_advanced_241108_draft',1,'unmapped_advanced_241108','AHA ACLS Provider (Initial)',false,'native_public_checkout','required',array[]::text[],'["first_name","last_name","email","phone"]'::jsonb,'[]'::jsonb,'[]'::jsonb,'{"mode":"customer_pays"}'::jsonb,'{"mode":"catalog_options"}'::jsonb,'native-checkout-profile-v1','{"schemaVersion":"native-checkout.form.v1","inventory_kind":"scheduled_session_v1","description":"Choose your course materials and registration options. Additional courses keep their own class times.","max_students":10,"default_choices":["own_copy"],"fields":[{"key":"first_name","wire":"firstName","type":"text","label":"First name","required":true},{"key":"last_name","wire":"lastName","type":"text","label":"Last name","required":true},{"key":"email","wire":"email","type":"email","label":"Email","required":true},{"key":"phone","wire":"phone","type":"tel","label":"Phone","required":true}],"option_groups":[{"key":"materials","label":"ACLS course materials","type":"radio","required":true,"choices":[{"key":"own_copy","label":"I have my own current manual","catalog_keys":[]},{"key":"paper_book","label":"Printed Provider Manual","catalog_keys":["advanced_241108_paper_book"]},{"key":"ebook","label":"Provider Manual eBook","catalog_keys":["advanced_241108_ebook"]}]}],"driver_rules":[{"driver":"native_order"}],"back_url":"/acls.html"}'::jsonb,false),
('native_advanced_209818_draft',1,'unmapped_advanced_209818','AHA ACLS Provider (Renewal)',false,'native_public_checkout','required',array[]::text[],'["first_name","last_name","email","phone"]'::jsonb,'[]'::jsonb,'[]'::jsonb,'{"mode":"customer_pays"}'::jsonb,'{"mode":"catalog_options"}'::jsonb,'native-checkout-profile-v1','{"schemaVersion":"native-checkout.form.v1","inventory_kind":"scheduled_session_v1","description":"Choose your course materials and registration options. Additional courses keep their own class times.","max_students":10,"default_choices":["own_copy"],"fields":[{"key":"first_name","wire":"firstName","type":"text","label":"First name","required":true},{"key":"last_name","wire":"lastName","type":"text","label":"Last name","required":true},{"key":"email","wire":"email","type":"email","label":"Email","required":true},{"key":"phone","wire":"phone","type":"tel","label":"Phone","required":true}],"option_groups":[{"key":"materials","label":"ACLS course materials","type":"radio","required":true,"choices":[{"key":"own_copy","label":"I have my own current manual","catalog_keys":[]},{"key":"paper_book","label":"Printed Provider Manual","catalog_keys":["advanced_209818_paper_book"]},{"key":"ebook","label":"Provider Manual eBook","catalog_keys":["advanced_209818_ebook"]}]}],"driver_rules":[{"driver":"native_order"}],"back_url":"/acls.html"}'::jsonb,false),
('native_advanced_209805_draft',1,'unmapped_advanced_209805','AHA PALS Provider',false,'native_public_checkout','required',array[]::text[],'["first_name","last_name","email","phone"]'::jsonb,'[]'::jsonb,'[]'::jsonb,'{"mode":"customer_pays"}'::jsonb,'{"mode":"catalog_options"}'::jsonb,'native-checkout-profile-v1','{"schemaVersion":"native-checkout.form.v1","inventory_kind":"scheduled_session_v1","description":"Choose your course materials and registration options. Additional courses keep their own class times.","max_students":10,"default_choices":["own_copy"],"fields":[{"key":"first_name","wire":"firstName","type":"text","label":"First name","required":true},{"key":"last_name","wire":"lastName","type":"text","label":"Last name","required":true},{"key":"email","wire":"email","type":"email","label":"Email","required":true},{"key":"phone","wire":"phone","type":"tel","label":"Phone","required":true}],"option_groups":[{"key":"materials","label":"PALS course materials","type":"radio","required":true,"choices":[{"key":"own_copy","label":"I have my own current manual","catalog_keys":[]},{"key":"paper_book","label":"Printed Provider Manual","catalog_keys":["advanced_209805_paper_book"]},{"key":"ebook","label":"Provider Manual eBook","catalog_keys":["advanced_209805_ebook"]}]}],"driver_rules":[{"driver":"native_order"}],"back_url":"/pals.html"}'::jsonb,false),
('native_advanced_251496_draft',1,'unmapped_advanced_251496','AHA PALS Renewal',false,'native_public_checkout','required',array[]::text[],'["first_name","last_name","email","phone"]'::jsonb,'[]'::jsonb,'[]'::jsonb,'{"mode":"customer_pays"}'::jsonb,'{"mode":"catalog_options"}'::jsonb,'native-checkout-profile-v1','{"schemaVersion":"native-checkout.form.v1","inventory_kind":"scheduled_session_v1","description":"Choose your course materials and registration options. Additional courses keep their own class times.","max_students":10,"default_choices":["own_copy"],"fields":[{"key":"first_name","wire":"firstName","type":"text","label":"First name","required":true},{"key":"last_name","wire":"lastName","type":"text","label":"Last name","required":true},{"key":"email","wire":"email","type":"email","label":"Email","required":true},{"key":"phone","wire":"phone","type":"tel","label":"Phone","required":true}],"option_groups":[{"key":"materials","label":"PALS course materials","type":"radio","required":true,"choices":[{"key":"own_copy","label":"I have my own current manual","catalog_keys":[]},{"key":"paper_book","label":"Printed Provider Manual","catalog_keys":["advanced_251496_paper_book"]},{"key":"ebook","label":"Provider Manual eBook","catalog_keys":["advanced_251496_ebook"]}]}],"driver_rules":[{"driver":"native_order"}],"back_url":"/pals.html"}'::jsonb,false)
on conflict(profile_key) do nothing;
create table public.native_advanced_instructor_scopes(
 course_number text not null references public.native_advanced_course_policy,
 instructor_id uuid not null references public.people(id),availability_person_id text not null,
 calendar_source_keys text[] not null,verified boolean not null default false,evidence text,
 primary key(course_number,instructor_id)
);
create table public.native_advanced_offer_leases(
 selection_id text primary key check(selection_id~'^native-full:[a-f0-9]{64}$'),
 course_number text not null references public.native_advanced_course_policy,
 offer jsonb not null,observed_at timestamptz not null,valid_until timestamptz not null,
 check(valid_until>observed_at and valid_until<=observed_at+interval '15 minutes')
);
alter table public.native_advanced_course_policy enable row level security;
alter table public.native_advanced_instructor_scopes enable row level security;
alter table public.native_advanced_offer_leases enable row level security;
revoke all on public.native_advanced_course_policy,public.native_advanced_instructor_scopes,public.native_advanced_offer_leases from public,anon,authenticated;
grant select,insert,update,delete on public.native_advanced_course_policy,public.native_advanced_instructor_scopes,public.native_advanced_offer_leases to service_role;

create function public.native_advanced_course_runtime_policy(p_course_number text) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare p public.native_advanced_course_policy; c public.courses; ready boolean; teachers jsonb;
begin
 select * into p from public.native_advanced_course_policy where course_number=p_course_number;
 if p.course_number is null then return jsonb_build_object('materializationEnabled',false,'nativePublicationEnabled',false); end if;
 select * into c from public.courses where id=p.course_id;
 select coalesce(jsonb_agg(jsonb_build_object('id',person.id,'name',person.display_name,'availabilityPersonId',s.availability_person_id,
  'calendarSourceKeys',s.calendar_source_keys,'qualificationValidThrough',coalesce(q.expires_at,now()+interval '90 days'))),'[]') into teachers
 from public.native_advanced_instructor_scopes s join public.people person on person.id=s.instructor_id and person.active
 join public.instructor_qualifications q on q.instructor_id=person.id and q.course_id=p.course_id and q.status='active'
 where s.course_number=p_course_number and s.verified and nullif(trim(s.evidence),'') is not null
  and cardinality(s.calendar_source_keys)>0 and (q.expires_at is null or q.expires_at>now());
 ready:=p.enabled and p.verified and p.setup_minutes is not null and p.cleanup_minutes is not null and p.max_students is not null
  and p.location_id is not null and nullif(p.resource_label,'') is not null and nullif(p.location_label,'') is not null
  and c.id is not null and c.enrollware_course_id=p.course_number and c.registration_profile_key=p.profile_key
  and c.max_students_default>=p.max_students and p.evidence ?& array['price','instruction','buffers','capacity','identity']
  and exists(select 1 from public.landerware_registration_catalog cat where cat.course_id=p.course_number and cat.active and cat.unit_amount=p.session_cents and cat.currency='usd')
  and exists(select 1 from public.landerware_registration_profiles x where x.profile_key=p.profile_key and x.course_id=c.course_key and x.active and x.registration_mode='native_public_checkout')
  and jsonb_array_length(teachers)>0;
 return jsonb_build_object('materializationEnabled',coalesce(ready,false),'nativePublicationEnabled',coalesce(ready and p.publication_enabled,false),
  'pageKey',p.page_key,'nativeScopeId','qualified-advanced-shipyard-b.v1','coursePolicyKey','advanced-full:'||p.course_number||'.v1',
  'canonicalCourseId',p.course_id,'instructionMinutes',p.instruction_minutes,'setupMinutes',p.setup_minutes,'cleanupMinutes',p.cleanup_minutes,
  'maxStudents',p.max_students,'sessionCents',p.session_cents,'resource',p.resource_label,'location',p.location_label,'instructors',teachers);
end $$;

-- Only the trusted publication runner can persist offers. This DTO contains
-- schedule/qualification evidence, never roster/contact/document information.
create function public.native_publish_advanced_offers(p_offers jsonb) returns integer
language plpgsql security invoker set search_path='' as $$
declare o jsonb; policy jsonb; instructor jsonb; observed timestamptz; lease timestamptz; n integer:=0;
begin
 if jsonb_typeof(p_offers) is distinct from 'array' or jsonb_array_length(p_offers)>10000 then raise exception 'invalid_request'; end if;
 for o in select value from jsonb_array_elements(p_offers) loop
  if jsonb_typeof(o) is distinct from 'object' or exists(select 1 from jsonb_object_keys(o) k where k not in
   ('kind','authority','courseNumber','selectionId','localStart','startsAt','endsAt','consumptionStartsAt','consumptionEndsAt',
    'instructor','instructorId','availabilityPersonId','resource','location','nativeScopeId','coursePolicyKey','canonicalCourseId',
    'proofObservedAt','availabilityBlockId','sourceSessionIds','calendarSourceKey','availabilityStartsAt','availabilityEndsAt','generatedAt','validUntil'))
   then raise exception 'invalid_offer_fields'; end if;
  policy:=public.native_advanced_course_runtime_policy(o->>'courseNumber');
  select value into instructor from jsonb_array_elements(policy->'instructors') where value->>'id'=o->>'instructorId' and value->>'availabilityPersonId'=o->>'availabilityPersonId' and value->>'name'=o->>'instructor';
  observed:=(o->>'proofObservedAt')::timestamptz;lease:=(o->>'validUntil')::timestamptz;
  if policy->>'nativePublicationEnabled' is distinct from 'true' or instructor is null
   or o->>'authority' is distinct from 'native-full-course.v3' or o->>'nativeScopeId' is distinct from policy->>'nativeScopeId'
   or o->>'canonicalCourseId' is distinct from policy->>'canonicalCourseId' or o->>'coursePolicyKey' is distinct from policy->>'coursePolicyKey'
   or o ? 'appointmentDayId' or o ? 'matchedContainerId' or coalesce(o->>'selectionId','') !~ '^native-full:[a-f0-9]{64}$'
   or coalesce(instructor->'calendarSourceKeys' ? (o->>'calendarSourceKey'),false)=false
   or nullif(o->>'availabilityStartsAt','') is null or nullif(o->>'availabilityEndsAt','') is null
   or nullif(o->>'consumptionStartsAt','') is null or nullif(o->>'consumptionEndsAt','') is null
   or observed is null or observed>now() or observed<now()-interval '15 minutes' or lease is null or lease<=now() or lease>observed+interval '15 minutes'
   or (o->>'availabilityStartsAt')::timestamptz>(o->>'consumptionStartsAt')::timestamptz
   or (o->>'availabilityEndsAt')::timestamptz<(o->>'consumptionEndsAt')::timestamptz
   or nullif(o->>'availabilityBlockId','') is null then raise exception 'unverified_advanced_offer'; end if;
  if exists(select 1 from public.native_advanced_offer_leases where selection_id=o->>'selectionId' and course_number<>o->>'courseNumber') then raise exception 'offer_identity_conflict'; end if;
  insert into public.native_advanced_offer_leases(selection_id,course_number,offer,observed_at,valid_until)
  values(o->>'selectionId',o->>'courseNumber',o,observed,lease) on conflict(selection_id) do update
   set offer=excluded.offer,observed_at=excluded.observed_at,valid_until=excluded.valid_until;
  n:=n+1;
 end loop;
 return n;
end $$;

create function public.native_advanced_full_course_option(p_course_number text,p_offer jsonb) returns jsonb
language plpgsql stable security invoker set search_path='' as $$
declare p public.native_advanced_course_policy; policy jsonb; teacher jsonb; target public.class_sessions;
 starts timestamptz; ends timestamptz; occupied_start timestamptz; occupied_end timestamptz; external_id text; count_matches integer; seats jsonb;
begin
 policy:=public.native_advanced_course_runtime_policy(p_course_number);
 if policy->>'nativePublicationEnabled' is distinct from 'true' then return null; end if;
 select * into p from public.native_advanced_course_policy where course_number=p_course_number;
 if not exists(select 1 from public.native_advanced_offer_leases l where l.selection_id=p_offer->>'selectionId'
  and l.course_number=p_course_number and l.offer=p_offer and l.valid_until>now() and l.observed_at<=now() and l.observed_at>now()-interval '15 minutes') then return null; end if;
 select value into teacher from jsonb_array_elements(policy->'instructors') where value->>'id'=p_offer->>'instructorId' and value->>'availabilityPersonId'=p_offer->>'availabilityPersonId' and value->>'name'=p_offer->>'instructor';
 if teacher is null or p_offer->>'canonicalCourseId' is distinct from p.course_id::text or p_offer->>'courseNumber' is distinct from p_course_number
  or p_offer->>'resource' is distinct from p.resource_label or p_offer->>'location' is distinct from p.location_label then return null; end if;
 starts:=(p_offer->>'startsAt')::timestamptz;ends:=(p_offer->>'endsAt')::timestamptz;
 occupied_start:=(p_offer->>'consumptionStartsAt')::timestamptz;occupied_end:=(p_offer->>'consumptionEndsAt')::timestamptz;
 if starts is null or ends is null or occupied_start is null or occupied_end is null or starts<now()+interval '24 hours' or starts>now()+interval '90 days'
  or ends<>starts+make_interval(mins=>p.instruction_minutes) or occupied_start<>starts-make_interval(mins=>p.setup_minutes)
  or occupied_end<>ends+make_interval(mins=>p.cleanup_minutes) or occupied_end>(teacher->>'qualificationValidThrough')::timestamptz
  or to_char(starts at time zone 'America/New_York','YYYY-MM-DD"T"HH24:MI') is distinct from p_offer->>'localStart' then return null; end if;
 external_id:='lw-'||substr(md5(p_offer->>'selectionId'),1,8)||'-'||substr(md5(p_offer->>'selectionId'),9,4)||'-'||substr(md5(p_offer->>'selectionId'),13,4)||'-'||substr(md5(p_offer->>'selectionId'),17,4)||'-'||substr(md5(p_offer->>'selectionId'),21,12);
 select count(*),min(s.id::text)::uuid into count_matches,target.id from public.class_sessions s where s.external_class_id=external_id
  or (s.record_scope='operational' and s.course_id=p.course_id and s.start_at=starts and s.end_at=ends and s.lead_instructor_id=(teacher->>'id')::uuid and s.location_id=p.location_id and s.status in ('scheduled','active'));
 if count_matches>1 then return null; end if;
 if target.id is not null then
  select * into target from public.class_sessions where id=target.id;
  if target.course_id is distinct from p.course_id or target.start_at is distinct from starts or target.end_at is distinct from ends or target.consumption_start_at is distinct from occupied_start or target.consumption_end_at is distinct from occupied_end
   or target.registration_backend is distinct from 'landerware' or target.record_scope is distinct from 'operational' or target.lead_instructor_id is distinct from (teacher->>'id')::uuid or target.location_id is distinct from p.location_id
   or target.visibility not in ('public','unlisted') or ((target.status not in ('scheduled','active') or target.registration_status<>'open') and not public.native_checkout_generated_reusable(target.id)) then return null; end if;
  external_id:=target.external_class_id;seats:=public.landerware_public_seat_state(target.id);
  if coalesce((seats->>'remaining')::integer,0)<1 then return null; end if;
 end if;
 if exists(select 1 from public.class_sessions s where s.record_scope='operational' and s.id is distinct from target.id
  and s.status in ('scheduled','active','tentative','pending','proposed_window') and (s.location_id=p.location_id or s.lead_instructor_id=(teacher->>'id')::uuid)
  and coalesce(s.consumption_start_at,s.start_at)<occupied_end and coalesce(s.consumption_end_at,s.end_at,s.start_at+interval '1 day')>occupied_start) then return null; end if;
 if exists(select 1 from public.class_sessions s where s.record_scope='operational' and s.id is distinct from target.id and s.course_id=p.course_id
  and s.lead_instructor_id=(teacher->>'id')::uuid and s.status in ('scheduled','active','tentative','pending','proposed_window') and (s.start_at at time zone 'America/New_York')::date=(starts at time zone 'America/New_York')::date) then return null; end if;
 if exists(select 1 from jsonb_array_elements(public.public_registration_closure_policy()->'closures') closure where occupied_start<(closure->>'endsAt')::timestamptz and occupied_end>(closure->>'startsAt')::timestamptz)
  or exists(select 1 from public.registration_reschedule_blocks b join public.class_sessions s on s.id=b.class_session_id where s.course_id=p.course_id and s.start_at=starts) then return null; end if;
 return p_offer||jsonb_build_object('targetSessionId',target.id,'externalId',external_id,'courseId',p.course_id,'locationId',p.location_id,'capacity',coalesce((seats->>'capacity')::integer,p.max_students),'course',(select name from public.courses where id=p.course_id),'pageKey',p.page_key,'sessionCents',p.session_cents);
exception when invalid_text_representation or datetime_field_overflow then return null;
end $$;

create function public.materialize_native_advanced_checkout(p_course_number text,p_offer jsonb) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare option jsonb; target uuid;
begin
 lock table public.class_sessions in share row exclusive mode;
 lock table public.native_advanced_course_policy,public.native_advanced_instructor_scopes,public.native_advanced_offer_leases,public.courses,public.people,public.locations,public.instructor_qualifications in share mode;
 option:=public.native_advanced_full_course_option(p_course_number,p_offer);
 if option is null then raise exception 'session_not_available'; end if;
 target:=(option->>'targetSessionId')::uuid;
 if target is not null and public.native_checkout_generated_reusable(target) then
  perform public.native_checkout_reopen_generated(target);option:=public.native_advanced_full_course_option(p_course_number,p_offer);
  if option is null then raise exception 'session_not_available'; end if;
 end if;
 if target is null then
  insert into public.class_sessions(source,status,record_scope,course_id,start_at,end_at,timezone,consumption_start_at,consumption_end_at,
   lead_instructor_id,location_id,max_students,registration_backend,visibility,registration_status,external_class_id,external_course_id,
   source_offer_id,source_location_label,source_instructor_label,registration_url,price,advertised_duration_minutes,external_session_evidence)
  values('landerware_event','scheduled','operational',(option->>'courseId')::uuid,(option->>'startsAt')::timestamptz,(option->>'endsAt')::timestamptz,'America/New_York',
   (option->>'consumptionStartsAt')::timestamptz,(option->>'consumptionEndsAt')::timestamptz,(option->>'instructorId')::uuid,(option->>'locationId')::uuid,
   (option->>'capacity')::integer,'landerware','public','open',option->>'externalId',p_course_number,option->>'availabilityBlockId',option->>'location',option->>'instructor',
   '/register/checkout/?course='||p_course_number,(option->>'sessionCents')::integer/100.0,240,
   jsonb_build_object('materializedBy','native_full_course','selectorOffer',p_offer,'coursePolicyKey',option->>'coursePolicyKey')) returning id into target;
  perform public.native_checkout_witness_generated(target);
 end if;
 return option||jsonb_build_object('targetSessionId',target);
end $$;

create function public.reserve_native_advanced_checkout_order(p_key text,p_profile_key text,p_version integer,p_context text,p_external_id text,p_offer jsonb,p_students jsonb,p_inputs jsonb,p_expected_total integer)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare p public.native_advanced_course_policy; option jsonb;
begin
 if p_key is null or p_key !~ '^[a-f0-9-]{36}$' or coalesce(p_context,'')<>'' then raise exception 'invalid_request'; end if;
 perform pg_advisory_xact_lock(hashtextextended('skills-claim|'||p_key,0));perform pg_advisory_xact_lock(hashtextextended('native-checkout-key|'||p_key,0));
 if exists(select 1 from public.landerware_public_orders where idempotency_key='public-order:'||p_key) then
  return public.reserve_native_checkout_order(p_key,p_profile_key,p_version,p_context,p_external_id,p_offer,p_students,p_inputs,p_expected_total);
 end if;
 select * into p from public.native_advanced_course_policy where profile_key=p_profile_key;
 if p.course_number is null or public.native_advanced_course_runtime_policy(p.course_number)->>'materializationEnabled' is distinct from 'true' then raise exception 'native_profile_not_configured'; end if;
 if nullif(p_external_id,'') is null then
  option:=public.materialize_native_advanced_checkout(p.course_number,p_offer);p_external_id:=option->>'externalId';
 end if;
 return public.reserve_native_checkout_order(p_key,p_profile_key,p_version,p_context,p_external_id,p_offer,p_students,p_inputs,p_expected_total);
end $$;

revoke all on function public.native_advanced_course_runtime_policy(text),public.native_publish_advanced_offers(jsonb),public.native_advanced_full_course_option(text,jsonb),public.materialize_native_advanced_checkout(text,jsonb),public.reserve_native_advanced_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer) from public,anon,authenticated;
grant execute on function public.native_advanced_course_runtime_policy(text),public.native_publish_advanced_offers(jsonb),public.native_advanced_full_course_option(text,jsonb),public.materialize_native_advanced_checkout(text,jsonb),public.reserve_native_advanced_checkout_order(text,text,integer,text,text,jsonb,jsonb,jsonb,integer) to service_role;
commit;
