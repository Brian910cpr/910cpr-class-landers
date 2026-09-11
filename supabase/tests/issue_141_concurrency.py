import concurrent.futures
import os
import uuid

import psycopg


DSN = os.environ["DATABASE_URL"]


def call(sql, params):
    with psycopg.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()[0]


def concurrent_pair(sql, params):
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: call(sql, params), range(2)))
    replay_flags = sorted(result["idempotentReplay"] for result in results)
    assert replay_flags == [False, True], results


with psycopg.connect(DSN) as conn:
    with conn.cursor() as cur:
        cur.execute("insert into public.landerware_organizations(display_name) values ('Issue 141 concurrency') returning id")
        organization_id = cur.fetchone()[0]
        cur.execute("insert into public.landerware_people(current_first_name,current_last_name) values ('Concurrent','Participant') returning id")
        person_id = cur.fetchone()[0]
        cur.execute("insert into public.landerware_certification_requirements(person_id,organization_id,course_id,course_name) values (%s,%s,'issue-141-concurrency','Issue 141 concurrency') returning id", (person_id, organization_id))
        requirement_id = cur.fetchone()[0]
        cur.execute("insert into public.landerware_sessions(course_id,course_name,starts_at,ends_at,organization_id,lifecycle_state,provenance,requirements_manifest) values ('issue-141-concurrency','Issue 141 concurrency',now()-interval '3 hours',now()-interval '1 hour',%s,'completed','concurrency_test','{}') returning id", (organization_id,))
        session_id = cur.fetchone()[0]
        cur.execute("insert into public.landerware_rosters(session_id) values (%s) returning id", (session_id,))
        roster_id = cur.fetchone()[0]
        cur.execute("insert into public.landerware_registrations(person_id,requirement_id,session_id,roster_id,organization_id,status,source) values (%s,%s,%s,%s,%s,'active','system') returning id", (person_id, requirement_id, session_id, roster_id, organization_id))
        registration_id = cur.fetchone()[0]
        cur.execute("insert into public.landerware_roster_memberships(roster_id,session_id,person_id,registration_id,display_name,source) values (%s,%s,%s,%s,'Concurrent Participant','system') returning id", (roster_id, session_id, person_id, registration_id))
        membership_id = cur.fetchone()[0]

request_key = f"issue141-concurrent-request-{uuid.uuid4()}"
concurrent_pair(
    "select public.landerware_request_scheduling(%s,current_date+30,'explicit_sender_deadline',%s)",
    (requirement_id, request_key),
)

assertion_key = f"issue141-concurrent-attendance-{uuid.uuid4()}"
asserted_at = "2026-09-11T12:00:00-04:00"
concurrent_pair(
    "select public.landerware_assert_attendance(%s,'absent','authorized-concurrency-test',%s,'authorized_human',null,null,%s)",
    (membership_id, asserted_at, assertion_key),
)

with psycopg.connect(DSN) as conn:
    with conn.cursor() as cur:
        cur.execute("select count(*) from public.landerware_scheduling_request_receipts where idempotency_key=%s", (request_key,))
        assert cur.fetchone()[0] == 1
        cur.execute("select count(*) from public.landerware_activity_events where requirement_id=%s and event_type='scheduling_requested'", (requirement_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("select count(*) from public.landerware_attendance_assertions where idempotency_key=%s", (assertion_key,))
        assert cur.fetchone()[0] == 1
        cur.execute("select count(*) from public.landerware_activity_events where registration_id=%s and event_type='attendance_asserted'", (registration_id,))
        assert cur.fetchone()[0] == 1

print("concurrency proof passed: scheduling and attendance each produced one durable effect")
