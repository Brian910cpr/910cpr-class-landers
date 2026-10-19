-- Native registration transfers. Only the service role may call these RPCs.
create table if not exists public.registration_reschedule_links (
 id uuid primary key default gen_random_uuid(),
 token_sha256 text not null unique check (token_sha256 ~ '^[0-9a-f]{64}$'),
 registration_id uuid not null references public.registrations(id),
 expires_at timestamptz not null,
 deadline_at timestamptz,
 reason text not null,
 revoked_at timestamptz,
 used_at timestamptz,
 result jsonb,
 created_at timestamptz not null default now()
);
create index if not exists registration_reschedule_links_registration on public.registration_reschedule_links(registration_id);
create table if not exists public.registration_reschedule_blocks (
 class_session_id uuid primary key references public.class_sessions(id),
 reason text not null,
 created_at timestamptz not null default now()
);
alter table public.registration_reschedule_links enable row level security;
alter table public.registration_reschedule_blocks enable row level security;
revoke all on public.registration_reschedule_links,public.registration_reschedule_blocks from public,anon,authenticated;
grant all on public.registration_reschedule_links,public.registration_reschedule_blocks to service_role;

create or replace function public.issue_registration_reschedule_link(p_registration_id uuid,p_token_sha256 text,p_expires_at timestamptz,p_reason text,p_deadline_at timestamptz default null)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare r public.registrations; c public.customers; link_id uuid;
begin
 select * into r from public.registrations where id=p_registration_id for update;
 if r.id is null or r.status not in ('active','registered','confirmed') or exists(select 1 from public.participant_completions where registration_id=r.id) then raise exception 'registration_not_reschedulable'; end if;
 select * into c from public.customers where id=r.customer_id;
 if nullif(trim(c.email),'') is null then raise exception 'registration_email_missing'; end if;
 if p_expires_at<=now() or p_expires_at>now()+interval '90 days' or nullif(trim(p_reason),'') is null then raise exception 'invalid_link_policy'; end if;
 update public.registration_reschedule_links set revoked_at=now() where registration_id=r.id and used_at is null and revoked_at is null;
 insert into public.registration_reschedule_links(registration_id,token_sha256,expires_at,reason,deadline_at)
 values(r.id,p_token_sha256,p_expires_at,p_reason,p_deadline_at) returning id into link_id;
 return jsonb_build_object('linkId',link_id,'expiresAt',p_expires_at);
end $$;

-- Publication membership comes from the server's current course calendar, never the browser.
create or replace function public.registration_reschedule_targets(p_registration_id uuid,p_published_ids text[],p_deadline_at timestamptz default null)
returns jsonb language sql stable security invoker set search_path='' as $$
 select coalesce(jsonb_agg(x.option order by x.start_at),'[]'::jsonb) from (
  select s.start_at,jsonb_build_object('id',s.id,'course',c.name,'startsAt',s.start_at,'endsAt',s.end_at,'timezone',s.timezone,
   'location',coalesce(l.name,s.source_location_label,''),'address',concat_ws(', ',l.address_line1,l.address_line2,l.city,l.state,l.postal_code)) option
  from public.registrations r join public.class_sessions original on original.id=r.class_session_id
  join public.class_sessions s on s.course_id=original.course_id
  join public.courses c on c.id=s.course_id left join public.locations l on l.id=s.location_id
  left join public.landerware_public_session_inventory i on i.external_class_id=s.external_class_id
  where r.id=p_registration_id and s.external_class_id=any(p_published_ids)
   and s.start_at>now() and (p_deadline_at is null or s.start_at<=p_deadline_at)
   and s.start_at<>original.start_at and s.status in ('scheduled','active') and s.record_scope='operational'
   and s.registration_status in ('open','external') and s.visibility in ('public','unlisted')
   and not exists(select 1 from public.registration_reschedule_blocks b join public.class_sessions blocked on blocked.id=b.class_session_id
      where blocked.start_at=s.start_at and blocked.course_id=s.course_id)
   and not exists(select 1 from jsonb_array_elements(public.public_registration_closure_policy()->'closures') closure
      where coalesce(s.consumption_start_at,s.start_at)<(closure->>'endsAt')::timestamptz
       and coalesce(s.consumption_end_at,s.end_at,s.start_at+interval '1 microsecond')>(closure->>'startsAt')::timestamptz)
   and coalesce(i.capacity,s.max_students)>greatest(coalesce(i.externally_registered,0),
      (select count(*) from public.registrations rr where rr.class_session_id=s.id and rr.status in ('active','registered','confirmed','completed')))
      +(select count(*) from public.landerware_public_order_students os join public.landerware_public_orders o on o.id=os.order_id
        where o.class_session_id=s.id and o.status in ('held','checkout_open') and o.hold_expires_at>now())
 ) x
$$;

create or replace function public.registration_reschedule_context(p_token_sha256 text,p_published_ids text[] default '{}')
returns jsonb language plpgsql security invoker set search_path='' as $$
declare t public.registration_reschedule_links; r public.registrations; s public.class_sessions; c public.customers; course public.courses;
begin
 select * into t from public.registration_reschedule_links where token_sha256=p_token_sha256;
 if t.id is null or t.revoked_at is not null or t.expires_at<=now() then raise exception 'invalid_or_expired_link'; end if;
 if t.used_at is not null then return jsonb_build_object('status','confirmed','result',t.result); end if;
 select * into r from public.registrations where id=t.registration_id;
 if r.status not in ('active','registered','confirmed') or exists(select 1 from public.participant_completions where registration_id=r.id) then raise exception 'registration_not_reschedulable'; end if;
 select * into s from public.class_sessions where id=r.class_session_id;
 select * into c from public.customers where id=r.customer_id;
 select * into course from public.courses where id=s.course_id;
 return jsonb_build_object('status','pending','firstName',c.first_name,'course',course.name,'courseNumber',course.enrollware_course_id,
   'currentStartsAt',s.start_at,'deadlineAt',t.deadline_at,'expiresAt',t.expires_at,
   'options',public.registration_reschedule_targets(r.id,p_published_ids,t.deadline_at));
end $$;

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
 'gmail','pending','reschedule-confirmation:'||t.id) on conflict(idempotency_key) do nothing;
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
 c.first_name||' '||c.last_name||E'\n'||c.email||E'\n\n'||trim(p_message),'gmail','pending','reschedule-help:'||t.id)
 on conflict(idempotency_key) do update set body_text=excluded.body_text where public.landerware_messages.delivery_status='pending';
 return jsonb_build_object('ok',true);
end $$;

revoke all on function public.issue_registration_reschedule_link(uuid,text,timestamptz,text,timestamptz),public.registration_reschedule_targets(uuid,text[],timestamptz),public.registration_reschedule_context(text,text[]),public.confirm_registration_reschedule(text,uuid,text[]),public.request_registration_reschedule_help(text,text) from public,anon,authenticated;
grant execute on function public.issue_registration_reschedule_link(uuid,text,timestamptz,text,timestamptz),public.registration_reschedule_targets(uuid,text[],timestamptz),public.registration_reschedule_context(text,text[]),public.confirm_registration_reschedule(text,uuid,text[]),public.request_registration_reschedule_help(text,text) to service_role;

-- Lease/retry state belongs to the email outcome, independently of the seat move.
create table if not exists public.registration_reschedule_deliveries (
 message_id uuid primary key references public.landerware_messages(id),
 status text not null default 'pending' check(status in ('pending','sending','sent','failed','needs_review')),
 attempts integer not null default 0,locked_at timestamptz,next_attempt_at timestamptz not null default now(),
 last_error text,created_at timestamptz not null default now()
);
alter table public.registration_reschedule_deliveries enable row level security;
revoke all on public.registration_reschedule_deliveries from public,anon,authenticated;
grant all on public.registration_reschedule_deliveries to service_role;
create or replace function public.claim_reschedule_confirmations(p_registration_id uuid default null)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare claimed jsonb;
begin
 insert into public.registration_reschedule_deliveries(message_id)
 select m.id from public.landerware_messages m where m.template_key in ('registration-rescheduled-v1','reschedule-help-v1') and m.delivery_status='pending'
 on conflict do nothing;
 -- Provider deduplication expires after 24h: ambiguous old attempts need review.
 update public.registration_reschedule_deliveries set status='needs_review',last_error='delivery_attempt_window_expired'
 where status in ('failed','sending') and created_at<now()-interval '23 hours';
 with candidates as (
  select d.message_id from public.registration_reschedule_deliveries d join public.landerware_messages m on m.id=d.message_id
  where (p_registration_id is null or m.operational_registration_id=p_registration_id)
   and ((d.status in ('pending','failed') and d.next_attempt_at<=now()) or (d.status='sending' and d.locked_at<now()-interval '5 minutes'))
  order by d.created_at limit 10 for update of d skip locked
 ), updated as (
  update public.registration_reschedule_deliveries d set status='sending',attempts=attempts+1,locked_at=now()
  from candidates c where d.message_id=c.message_id returning d.message_id
 ) select coalesce(jsonb_agg(jsonb_build_object('id',m.id,'recipient',m.recipient,'subject',m.subject,'body',m.body_text)),'[]'::jsonb)
 into claimed from updated u join public.landerware_messages m on m.id=u.message_id;
 return claimed;
end $$;
revoke all on function public.claim_reschedule_confirmations(uuid) from public,anon,authenticated;
grant execute on function public.claim_reschedule_confirmations(uuid) to service_role;
