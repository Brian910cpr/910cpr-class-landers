-- Issue #297: the requested attendees already belong to the correct native session.
-- Correct the two anomalous statuses; never create/move seats or touch billing/notes.
-- Default is a dry run. Replace only the final ROLLBACK with COMMIT after review.
BEGIN;
DO $repair$
DECLARE
  target uuid := 'eb020e4a-b74a-443e-acd8-05727c2a8170';
  ids uuid[] := ARRAY['8b844672-5823-4c98-9772-9514b7c574be'::uuid,
                      'a9963887-6dca-4d1d-96ab-e3edd5d1b0b8'::uuid];
  item public.registrations%ROWTYPE;
BEGIN
  PERFORM 1 FROM public.class_sessions WHERE id=target
    AND source='landerware_event' AND registration_backend='landerware'
    AND record_scope='operational' AND status='scheduled'
    AND start_at='2026-10-13T09:00:00-04:00'::timestamptz
    AND end_at='2026-10-13T11:00:00-04:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Target session changed; review required'; END IF;
  PERFORM 1 FROM public.registrations WHERE id=ANY(ids) FOR UPDATE;
  IF (SELECT count(*) FROM public.registrations WHERE id=ANY(ids)
      AND class_session_id=target AND registration_source='landerware_native_checkout'
      AND status IN ('active','registered')) <> 2 THEN
    RAISE EXCEPTION 'Exact registration identities, session, source or status changed';
  END IF;
  FOR item IN SELECT * FROM public.registrations WHERE id=ANY(ids) AND status='active' LOOP
    INSERT INTO public.participant_lifecycle_events
      (event_key,event_type,customer_id,registration_id,class_session_id,source,actor,details)
    VALUES ('issue297:normalize-active:'||item.id, 'corrected', item.customer_id,item.id,target,
      'issue297_status_reconciliation',jsonb_build_object('agent','Codex','issue',297),
      jsonb_build_object('previous_status','active','new_status','registered',
        'reason','Existing native seat excluded by canonical status contract',
        'session_relationship_changed',false,'billing_changed',false));
    UPDATE public.registrations SET status='registered',updated_at=now() WHERE id=item.id;
  END LOOP;
END
$repair$;
SELECT jsonb_build_object(
  'session_id','eb020e4a-b74a-443e-acd8-05727c2a8170',
  'expected_registration_count',count(*),
  'registered_count',count(*) FILTER (WHERE status='registered'),
  'target_relationship_count',count(*) FILTER (WHERE class_session_id='eb020e4a-b74a-443e-acd8-05727c2a8170'),
  'audit_event_count',(SELECT count(*) FROM public.participant_lifecycle_events
    WHERE event_key IN ('issue297:normalize-active:8b844672-5823-4c98-9772-9514b7c574be',
                       'issue297:normalize-active:a9963887-6dca-4d1d-96ab-e3edd5d1b0b8'))
) AS proof
FROM public.registrations WHERE id IN ('8b844672-5823-4c98-9772-9514b7c574be','a9963887-6dca-4d1d-96ab-e3edd5d1b0b8');
ROLLBACK;
