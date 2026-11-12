-- Capture the original native order's booking contract. No backfill, activation,
-- catalog/price writes, class edits, historical-order rewrites or legacy changes.
begin;
set local lock_timeout='2s';
set local statement_timeout='30s';

alter table public.landerware_public_orders add column native_booking_snapshot jsonb;
comment on column public.landerware_public_orders.native_booking_snapshot is
 'Server-captured immutable original booking identity and provenance; null means original identity was not captured, never current-state backfill.';

-- Caller already owns the class row and freezes the referenced canonical rows.
-- Epoch values make comparison independent of the connection's TimeZone.
-- Exclude cosmetic labels, capacity, occupancy, prices and policy/authority
-- revisions: another legitimately reserved student does not change this booking.
create function public.native_checkout_booking_identity(p_session public.class_sessions)
returns jsonb language sql stable security invoker set search_path='' as $function$
 select jsonb_build_object(
  'sessionId',p_session.id,'externalClassId',p_session.external_class_id,
  'courseId',p_session.course_id,'courseKey',c.course_key,'publicCourseId',c.enrollware_course_id,
  'startsAtEpoch',extract(epoch from p_session.start_at),'endsAtEpoch',extract(epoch from p_session.end_at),
  'timeZone',p_session.timezone,'instructorId',p_session.lead_instructor_id,
  'locationId',p_session.location_id,'resourceId',p_session.resource_id,
  'address',jsonb_build_object('line1',nullif(trim(l.address_line1),''),'line2',nullif(trim(l.address_line2),''),
   'city',nullif(trim(l.city),''),'state',nullif(trim(l.state),''),'postalCode',nullif(trim(l.postal_code),'')))
 from public.courses c join public.locations l on l.id=p_session.location_id
 join public.people instructor on instructor.id=p_session.lead_instructor_id
 where c.id=p_session.course_id;
$function$;

create function public.native_checkout_capture_booking_identity()
returns trigger language plpgsql volatile security invoker set search_path='' as $function$
declare s public.class_sessions; identity jsonb; authority jsonb; witness jsonb;
begin
 if tg_op='UPDATE' then
  -- Null is intentionally immutable too. An old order must not acquire today's
  -- identity and pretend it was the customer's original selection.
  if new.native_booking_snapshot is distinct from old.native_booking_snapshot then
   raise exception 'native_booking_snapshot_immutable';
  end if;
  if old.checkout_runtime_version='native-v1' and
    (new.class_session_id is distinct from old.class_session_id or new.course_id is distinct from old.course_id) then
   raise exception 'native_booking_binding_immutable';
  end if;
  return new;
 end if;
 if new.checkout_runtime_version<>'native-v1' then
  if new.native_booking_snapshot is not null then raise exception 'native_booking_snapshot_not_applicable'; end if;
  return new;
 end if;
 if current_setting('transaction_isolation')<>'read committed' then raise exception 'native_booking_capture_isolation_required'; end if;
 -- This is the same lock/order used by native creation and first settlement.
 select * into s from public.class_sessions where id=new.class_session_id for update;
 -- NOWAIT avoids cycles with concurrent administrative reference edits. This
 -- uses existing service-role UPDATE rights; no new canonical write grants.
 lock table public.courses,public.locations,public.people in share mode nowait;
 identity:=public.native_checkout_booking_identity(s);
 if identity is null or identity->>'publicCourseId' is distinct from new.course_id
  or s.registration_backend is distinct from 'landerware' or s.record_scope is distinct from 'operational'
  or s.start_at is null or s.end_at is null or not isfinite(s.start_at) or not isfinite(s.end_at)
  or s.start_at>=s.end_at then raise exception 'native_booking_capture_unavailable'; end if;
 select jsonb_build_object('eventId',e.id,'revision',e.revision,'enabled',e.enabled,
   'recordedAt',e.recorded_at,'identity',e.session_identity,'fingerprint',e.snapshot_fingerprint)
 into authority from public.landerware_session_authority_events e
 where e.class_session_id=s.id order by e.revision desc limit 1;
 select to_jsonb(w) into witness from public.native_checkout_generated_sessions w where w.class_session_id=s.id;
 -- Never accept a caller-supplied identity, timestamp or provenance snapshot.
 new.native_booking_snapshot:=jsonb_build_object('schemaVersion','native-booking.v1',
  'capturedAt',clock_timestamp(),'identity',identity,'provenance',jsonb_build_object(
   'authorityEvent',authority,'source',s.source,'sourceOfferId',s.source_offer_id,
   'generatedWitness',witness,'sourceEvidence',s.external_session_evidence));
 return new;
end $function$;
create trigger native_checkout_capture_booking_identity before insert or update
 on public.landerware_public_orders for each row execute function public.native_checkout_capture_booking_identity();

-- Called only after class/order locking and paid/refunded replay. Returning a
-- reason (not raising) lets the existing paid-review path retain receipt/hold
-- evidence and staff attention without producing a registration or confirmation.
create function public.native_checkout_booking_identity_error(p_order public.landerware_public_orders,p_session public.class_sessions)
returns text language plpgsql volatile security invoker set search_path='' as $function$
declare current_identity jsonb;
begin
 if p_order.native_booking_snapshot is null
  or p_order.native_booking_snapshot->>'schemaVersion' is distinct from 'native-booking.v1'
  or jsonb_typeof(p_order.native_booking_snapshot->'identity') is distinct from 'object' then
  return 'native_booking_identity_unproven';
 end if;
 if current_setting('transaction_isolation')<>'read committed' then return 'native_booking_identity_unavailable'; end if;
 begin
  lock table public.courses,public.locations,public.people in share mode nowait;
 exception when lock_not_available then return 'native_booking_identity_unavailable'; end;
 current_identity:=public.native_checkout_booking_identity(p_session);
 if current_identity is null or current_identity is distinct from p_order.native_booking_snapshot->'identity'
  or current_identity->>'publicCourseId' is distinct from p_order.course_id then
  return 'native_booking_identity_changed';
 end if;
 return null;
end $function$;
revoke all on function public.native_checkout_booking_identity(public.class_sessions),
 public.native_checkout_capture_booking_identity(),
 public.native_checkout_booking_identity_error(public.landerware_public_orders,public.class_sessions) from public,anon,authenticated;
grant execute on function public.native_checkout_booking_identity(public.class_sessions),
 public.native_checkout_capture_booking_identity(),
 public.native_checkout_booking_identity_error(public.landerware_public_orders,public.class_sessions) to service_role;

-- All reviewed BLS/adult/pediatric and optional-code chains share this finalizer.
-- Refuse an unreviewed definition rather than overwrite unrelated changes.
do $patch$
declare signature text:='public.native_checkout_finalize_order(uuid,text,jsonb)';
 installed text; definition text; anchor text; replacement text;
begin
 select replace(prosrc,E'\r\n',E'\n') into installed from pg_proc where oid=to_regprocedure(signature);
 -- The hosted variant differs only in two subject punctuation literals.
 if installed is null or md5(installed) not in ('2e5784b3a2109ccbaa4179368211c90f','00a178e4e6c1f757c31ca502399bcf8b') then raise exception 'native_booking_finalizer_source_drift'; end if;
 definition:=replace(pg_get_functiondef(signature::regprocedure),E'\r\n',E'\n');
 anchor:='or s.start_at<=now() then v_error:=''session_not_open'';';
 replacement:='or s.start_at<=clock_timestamp() then v_error:=''session_not_open'';';
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_booking_start_anchor_missing'; end if;
 definition:=replace(definition,anchor,replacement);
 anchor:=' if o.status in (''held'',''checkout_open'') and (o.hold_expires_at>now()';
 replacement:=E' -- Original customer identity, not latest class authority. Class row is\n -- already locked; paid/refunded replay above never depends on this snapshot.\n if v_error is null then v_error:=public.native_checkout_booking_identity_error(o,s); end if;\n'||anchor;
 if (length(installed)-length(replace(installed,anchor,'')))/length(anchor)<>1 then raise exception 'native_booking_identity_anchor_missing'; end if;
 execute replace(definition,anchor,replacement);
end $patch$;
commit;
