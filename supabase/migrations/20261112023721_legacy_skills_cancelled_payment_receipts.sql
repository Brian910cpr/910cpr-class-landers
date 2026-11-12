begin;
set local lock_timeout='2s';
set local statement_timeout='30s';
-- The original legacy order owns the payment; no new booking or repricing.
alter table public.registration_orders add column if not exists skills_payment_received_at timestamptz;
alter table public.registration_orders add column if not exists skills_payment_review_reason text;
create or replace function public.skills_checkout_order(p_key text,p_context text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare receipt public.skills_session_claim_receipts; r public.registrations; o public.registration_orders;
begin
 select * into receipt from public.skills_session_claim_receipts where idempotency_key=p_key;
 if not found then raise exception 'reservation_not_found'; end if;
 if receipt.result->>'context' is distinct from p_context then raise exception 'invalid_request'; end if;
 select * into r from public.registrations where id=receipt.registration_id;
 if r.id is null or receipt.result->>'registrationId' is distinct from r.id::text
  or receipt.result->>'amountCents' is distinct from '5500' then raise exception 'payment_mismatch'; end if;
 if (select count(*) from public.registration_orders where registration_id=r.id)<>1 then raise exception 'payment_mismatch'; end if;
 select * into o from public.registration_orders where registration_id=r.id;
 if o.currency<>'usd' or o.course_amount<>55 or o.materials_amount<>0 or o.total_amount<>55 then raise exception 'payment_mismatch'; end if;
 return jsonb_build_object('registrationId',r.id,'orderId',o.id,'sessionId',r.class_session_id,'status',o.status,
  'registrationStatus',r.status,'paymentReceived',o.paid_at is not null,'paymentReviewReason',o.skills_payment_review_reason,
  'checkoutId',o.stripe_checkout_session_id,'amountCents',5500,'currency',o.currency,'createdAt',o.created_at,
  'certificatePrivate',exists(select 1 from storage.buckets where id='class-session-docs' and not public),
  'startsAt',receipt.result->>'startsAt','location',receipt.result->>'location',
  'instructor',(select p.display_name from public.class_sessions s join public.people p on p.id=s.lead_instructor_id where s.id=r.class_session_id),
  'email',(select c.email from public.customers c where c.id=r.customer_id));
end $$;

create or replace function public.confirm_skills_checkout_payment(p_registration_id uuid,p_checkout_id text,p_amount_total bigint,p_currency text,p_payment_intent text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare r public.registrations; o public.registration_orders; receipt public.skills_session_claim_receipts; reason text; observed timestamptz;
begin
 if p_payment_intent is null or p_payment_intent !~ '^pi_[A-Za-z0-9_]+$' then raise exception 'payment_mismatch'; end if;
 -- Serialize cross-order reuse of a provider intent before locking the booking.
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('legacy-skills-payment:'||p_payment_intent,0));
 select * into strict r from public.registrations where id=p_registration_id for update;
 select * into strict receipt from public.skills_session_claim_receipts where registration_id=r.id;
 if receipt.result->>'registrationId' is distinct from r.id::text
  or receipt.result->>'amountCents' is distinct from '5500' then raise exception 'payment_mismatch'; end if;
 select * into strict o from public.registration_orders where registration_id=r.id for update;
 if o.stripe_checkout_session_id is null or o.stripe_checkout_session_id is distinct from p_checkout_id
  or p_amount_total is distinct from 5500::bigint or p_currency is distinct from 'usd'
  or o.total_amount is distinct from 55::numeric or o.course_amount is distinct from 55::numeric
  or o.materials_amount is distinct from 0::numeric or o.currency is distinct from 'usd'
  or o.status not in ('payment_pending','payment_failed','paid','canceled','refunded')
  or (o.stripe_payment_intent_id is not null and o.stripe_payment_intent_id is distinct from p_payment_intent)
  or exists(select 1 from public.registration_orders x where x.id<>o.id and x.stripe_payment_intent_id=p_payment_intent)
 then raise exception 'payment_mismatch'; end if;
 -- Refunded is terminal. A paid callback is never permission to undo a refund.
 if o.status='refunded' then return jsonb_build_object('ok',true,'paymentStatus','refunded','idempotentReplay',true); end if;
 reason:=case when o.status='canceled' then 'order_cancelled'
  when r.status not in ('registered','active','confirmed','completed') then 'registration_not_active' end;
 if o.status='paid' or o.paid_at is not null or o.skills_payment_received_at is not null then
  return jsonb_build_object('ok',true,'paymentStatus',case when o.skills_payment_review_reason is not null then 'payment_review' when reason is not null then 'cancelled' else 'paid' end,'idempotentReplay',true);
 end if;
 -- Retain the existing paid_at transaction timestamp convention; this new
 -- field separately records first local observation, never provider charge time.
 observed:=clock_timestamp();
 -- Money receipt and the review reason commit atomically. Never mutate the
 -- registration, class, quote, requirements, messages, inventory or fulfillment.
 update public.registration_orders set
  status=case when status='canceled' then status else 'paid' end,
  stripe_payment_intent_id=p_payment_intent,paid_at=coalesce(paid_at,now()),
  skills_payment_received_at=observed,skills_payment_review_reason=reason,updated_at=now()
 where id=o.id;
 return jsonb_build_object('ok',true,'paymentStatus',case when reason is not null then 'payment_review' else 'paid' end);
end $$;
do $migration$
declare definition text; anchor text; replacement text;
begin
 definition:=replace(pg_get_functiondef('public.native_checkout_receipt(text)'::regprocedure),E'\r','');
 anchor:=$anchor$ select x.status,(x.total_amount*100)::integer into status,amount from public.registration_orders x where x.registration_id=r.id;
 return jsonb_build_object('kind','skills_reservation','registrationId',r.id,'physicalCourseId',(select enrollware_course_id from public.courses where id=s.course_id),'sessionId',s.id,'status',case when status='paid' then 'paid' else r.status end,
  'amountCents',amount,'currency','usd','startsAt',s.start_at,'endsAt',s.end_at,'location',(select name from public.locations where id=s.location_id),$anchor$;
 replacement:=$replacement$ select x.status,(x.total_amount*100)::integer into status,amount from public.registration_orders x where x.registration_id=r.id;
 return jsonb_build_object('kind','skills_reservation','registrationId',r.id,'physicalCourseId',(select enrollware_course_id from public.courses where id=s.course_id),'sessionId',s.id,
  'status',case when status='refunded' then 'refunded' when status='canceled' or r.status not in ('registered','active','confirmed','completed') then 'cancelled' when status='paid' then 'paid' else r.status end,
  'paymentObserved',exists(select 1 from public.registration_orders x where x.registration_id=r.id and x.paid_at is not null),
  'reconciliationError',case when status='refunded' then null else
   (select x.skills_payment_review_reason from public.registration_orders x where x.registration_id=r.id) end,
  'amountCents',amount,'currency','usd','startsAt',s.start_at,'endsAt',s.end_at,'location',(select name from public.locations where id=s.location_id),$replacement$;
 if position(replacement in definition)>0 then return; end if;
 if position(anchor in definition)=0 then raise exception 'legacy_skills_receipt_projection_changed'; end if;
 execute replace(definition,anchor,replacement);
end $migration$;

revoke all on function public.skills_checkout_order(text,text),public.confirm_skills_checkout_payment(uuid,text,bigint,text,text) from public,anon,authenticated;
grant execute on function public.skills_checkout_order(text,text),public.confirm_skills_checkout_payment(uuid,text,bigint,text,text) to service_role;
commit;
