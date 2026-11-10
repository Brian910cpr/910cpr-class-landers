begin;

-- Service-only access after the edge validates a random saved receipt capability.
-- Receipt/order/registration remain canonical; no second booking/payment model.
create or replace function public.skills_checkout_order(p_key text,p_context text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare receipt public.skills_session_claim_receipts; r public.registrations; o public.registration_orders;
begin
 select * into receipt from public.skills_session_claim_receipts where idempotency_key=p_key;
 if not found then raise exception 'reservation_not_found'; end if;
 if receipt.result->>'context' is distinct from p_context then raise exception 'invalid_request'; end if;
 select * into r from public.registrations where id=receipt.registration_id;
 if r.status not in ('registered','active','confirmed','completed') then raise exception 'session_not_available'; end if;
 if (select count(*) from public.registration_orders where registration_id=r.id)<>1 then raise exception 'payment_mismatch'; end if;
 select * into o from public.registration_orders where registration_id=r.id;
 if o.currency<>'usd' or o.course_amount<>55 or o.materials_amount<>0 or o.total_amount<>55 then raise exception 'payment_mismatch'; end if;
 return jsonb_build_object('registrationId',r.id,'orderId',o.id,'sessionId',r.class_session_id,'status',o.status,
  'checkoutId',o.stripe_checkout_session_id,'amountCents',5500,'currency',o.currency,'createdAt',o.created_at,
  'certificatePrivate',exists(select 1 from storage.buckets where id='class-session-docs' and not public),
  'startsAt',receipt.result->>'startsAt','location',receipt.result->>'location',
  'instructor',(select p.display_name from public.class_sessions s join public.people p on p.id=s.lead_instructor_id where s.id=r.class_session_id),
  'email',(select c.email from public.customers c where c.id=r.customer_id));
end $$;

create or replace function public.bind_skills_checkout(p_registration_id uuid,p_checkout_id text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare r public.registrations; o public.registration_orders;
begin
 select * into r from public.registrations where id=p_registration_id for update;
 if not exists(select 1 from public.skills_session_claim_receipts where registration_id=r.id)
  or r.status not in ('registered','active','confirmed','completed') or p_checkout_id is null or p_checkout_id !~ '^cs_[A-Za-z0-9_]+$' then raise exception 'payment_mismatch'; end if;
 select * into strict o from public.registration_orders where registration_id=r.id for update;
 if o.currency<>'usd' or o.total_amount<>55 or o.course_amount<>55 or o.materials_amount<>0
  or o.status not in ('payment_pending','payment_failed','paid')
  or (o.stripe_checkout_session_id is not null and o.stripe_checkout_session_id<>p_checkout_id)
  or (o.status='paid' and o.stripe_checkout_session_id is null) then raise exception 'payment_mismatch'; end if;
 update public.registration_orders set stripe_checkout_session_id=p_checkout_id,updated_at=now() where id=o.id;
 return jsonb_build_object('ok',true);
end $$;

create or replace function public.confirm_skills_checkout_payment(p_registration_id uuid,p_checkout_id text,p_amount_total bigint,p_currency text,p_payment_intent text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare r public.registrations; o public.registration_orders;
begin
 select * into r from public.registrations where id=p_registration_id for update;
 if not exists(select 1 from public.skills_session_claim_receipts where registration_id=r.id)
  or r.status not in ('registered','active','confirmed','completed') then raise exception 'payment_mismatch'; end if;
 select * into strict o from public.registration_orders where registration_id=r.id for update;
 if o.stripe_checkout_session_id is null or o.stripe_checkout_session_id is distinct from p_checkout_id
  or p_amount_total is distinct from 5500::bigint or p_currency is distinct from 'usd'
  or o.total_amount<>55 or o.course_amount<>55 or o.materials_amount<>0 or o.currency<>'usd'
  or o.status not in ('payment_pending','payment_failed','paid') then raise exception 'payment_mismatch'; end if;
 if o.status='paid' then return jsonb_build_object('ok',true,'paymentStatus','paid','idempotentReplay',true); end if;
 update public.registration_orders set status='paid',stripe_payment_intent_id=p_payment_intent,paid_at=now(),updated_at=now() where id=o.id;
 return jsonb_build_object('ok',true,'paymentStatus','paid');
end $$;

create or replace function public.attach_skills_certificate(p_registration_id uuid,p_sha text,p_type text,p_size bigint)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare r public.registrations; path text; doc uuid; ext text;
begin
 select * into r from public.registrations where id=p_registration_id for update;
 if not exists(select 1 from public.skills_session_claim_receipts where registration_id=r.id)
  or r.status not in ('registered','active','confirmed','completed') then raise exception 'session_not_available'; end if;
 ext:=case p_type when 'application/pdf' then 'pdf' when 'image/jpeg' then 'jpg' when 'image/png' then 'png' end;
 if p_sha is null or p_sha !~ '^[a-f0-9]{64}$' or ext is null or p_size is null or p_size<1 or p_size>2097152 then raise exception 'invalid_certificate'; end if;
 if not exists(select 1 from storage.buckets where id='class-session-docs' and not public) then raise exception 'certificate_unavailable'; end if;
 path:=r.class_session_id::text||'/skills/'||r.id::text||'/'||p_sha||'.'||ext;
 insert into public.class_session_documents(class_session_id,document_type,file_name,storage_bucket,storage_path,content_type,file_size,sha256,source)
 values(r.class_session_id,'online_completion','Online completion certificate.'||ext,'class-session-docs',path,p_type,p_size,p_sha,'skills_registration')
 on conflict(storage_bucket,storage_path) do update set storage_path=excluded.storage_path returning id into doc;
 update public.registrations set optional_survey=coalesce(optional_survey,'{}'::jsonb)||jsonb_build_object('certificateDocumentId',doc,'certificateUploadRequired',false),updated_at=now() where id=r.id;
 return jsonb_build_object('ok',true,'documentId',doc);
end $$;

revoke all on function public.skills_checkout_order(text,text),public.bind_skills_checkout(uuid,text),public.confirm_skills_checkout_payment(uuid,text,bigint,text,text),public.attach_skills_certificate(uuid,text,text,bigint) from public,anon,authenticated;
grant execute on function public.skills_checkout_order(text,text),public.bind_skills_checkout(uuid,text),public.confirm_skills_checkout_payment(uuid,text,bigint,text,text),public.attach_skills_certificate(uuid,text,text,bigint) to service_role;
commit;
