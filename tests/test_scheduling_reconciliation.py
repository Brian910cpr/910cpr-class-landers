"""Scheduling contradiction regressions; no private source or network required."""
from copy import deepcopy
from datetime import datetime, timedelta
import unittest

from scripts.apply_anchor_policy import finalize_selector_payload, barnacle_compatible
from scripts.canonical_scheduling_demand import reconciliation_issues
from scripts.block_start_time_selector import build_occupancy, veto_calendar_collisions
from scripts.generate_dynamic_offers import has_conflict
from scripts.publish_scheduling_landscape import operational_lane_cells, daily_truth, publication_contradictions

POLICY = {"mode": "daily_anchor_stack_v1", "compact_paid_days": True, "barnacle_course_pairs": []}

def occurrence(sid, cid, clock, day="2026-10-02", minutes=120):
    start = datetime.fromisoformat(f"{day}T{clock}:00-04:00")
    return {"session_id": sid, "course_id": cid, "course_name": cid,
            "start_at": start.isoformat(), "end_at": (start+timedelta(minutes=minutes)).isoformat(),
            "location_name": "Room B", "lead_instructor_name": "Brian Ennis",
            "public_direct_booking": True, "registration_url": f"https://example.test/{sid}"}

def demand(row, count):
    return {"canonical_session_id": "canonical-"+row["session_id"],
            "external_class_id": row["session_id"], "external_course_id": row["course_id"],
            "start_at": row["start_at"], "end_at": row["end_at"],
            "active_registration_count": count, "count_available": count is not None,
            "demand_status": "current" if count is not None else "external_reconciliation_required",
            "workspace_projection_status": "current", "session_status": "scheduled"}

def offer(row, real=False):
    return {"date": row["start_at"][:10], "startTime": row["start_at"][11:16],
            "courseId": row["course_id"], "courseName": row["course_id"],
            "start_at": row["start_at"], "end_at": row["end_at"],
            "location": row["location_name"], "instructor": row["lead_instructor_name"],
            "offerType": "seated_class" if real else "dynamic_appointment",
            "registrationUrl": row["registration_url"] if real else "https://example.test/appointment"}

def payload(offers):
    return {"offers": deepcopy(offers), "dates": [{"date": item["date"],
            "startTimes": [{"startTime": item["startTime"], "courses": [item]}]} for item in offers]}

class SchedulingReconciliationTests(unittest.TestCase):
    def test_native_event_slug_is_an_occupied_day_even_without_external_seats(self):
        event={**demand(occurrence("local-event-slug","252737","12:30"),0),
               "source":"landerware_event","registration_backend":"landerware"}
        result=finalize_selector_payload(payload([offer(occurrence("x","210549","07:45"))]),
            [],{"sessions":[event]},POLICY)
        self.assertEqual([],result["offers"])
        self.assertEqual(["2026-10-02"],result["occupiedDates"])

    def test_real_class_booking_is_vetoed_by_hard_busy_block_without_erasing_class(self):
        source=occurrence("existing","209806","10:00","2026-10-03")
        candidate=offer(source,True)
        candidate["durationMinutes"]=120
        live={"availability_blocks":[{"availability_status":"blocked",
              "start_at":"2026-10-03T09:00:00-04:00","end_at":"2026-10-03T11:30:00-04:00",
              "instructor_name":"Brian Ennis","location_name":"Offsite"}]}
        kept,rejected,issues=veto_calendar_collisions([candidate],live)
        self.assertEqual([],kept)
        self.assertEqual(["HARD_BLOCK_COLLISION"],rejected[0]["reasons"])
        result=finalize_selector_payload({**payload([]),"reconciliationIssues":issues},
            [source],{"sessions":[demand(source,2)]},POLICY)
        self.assertEqual(["2026-10-03"],result["synthesisBlockedDates"])
        self.assertEqual("10:00",source["start_at"][11:16])
        self.assertEqual("HARD_BLOCK_COLLISION",result["reconciliationIssues"][0]["code"])

    def test_oct2_two_seated_bls_and_family_remove_all_orphan_overnight_starts(self):
        classes = [occurrence("family","252737","08:45"), occurrence("renewal","359474","10:45"),
                   occurrence("initial","209806","12:45")]
        candidates = [offer(occurrence("dynamic","209806",f"{hour:02}:{minute:02}"))
                      for hour in range(6) for minute in (0,30)]
        candidates += [offer(occurrence("dynamic","209806","07:45"))]
        candidates += [offer(row,True) for row in classes]
        result = finalize_selector_payload(payload(candidates), classes,
            {"sessions": [demand(row,n) for row,n in zip(classes,[2,1,2])]}, POLICY)
        self.assertEqual(["08:45","10:45","12:45"], [row["startTime"] for row in result["offers"]])
        self.assertEqual(13,result["rejectionReasonCounts"]["ORPHAN_SYNTHETIC_OFFER"])
        flattened=[r for d in result["dates"] for s in d["startTimes"] for r in s["courses"]]
        self.assertEqual(result["offers"],flattened,"landscape and booking consume identical final decisions")

    def test_missing_roster_is_unknown_and_stops_new_synthesis_but_keeps_real_occurrence(self):
        row=occurrence("initial","209806","12:45")
        result=finalize_selector_payload(payload([offer(row,True),offer(occurrence("x","210549","07:45"))]),
            [row],{"sessions":[demand(row,None)]},POLICY)
        self.assertEqual(["2026-10-02"],result["synthesisBlockedDates"])
        self.assertEqual("MISSING_ROSTER",result["reconciliationIssues"][0]["code"])
        self.assertEqual(["12:45"],[r["startTime"] for r in result["offers"]])

    def test_oct12_renewal_anchor_removes_orphans_from_initial_selector(self):
        renewal=occurrence("oct12-renewal","359474","09:00","2026-10-12")
        initial=occurrence("oct12-initial","209806","17:00","2026-10-12")
        orphan_times=[f"{hour:02}:{minute:02}" for hour in range(5) for minute in (0,30)]+["12:45"]
        candidates=[offer(occurrence("dynamic","209806",clock,"2026-10-12")) for clock in orphan_times]
        # The Initial selector must honor a Renewal anchor even when Renewal
        # is not among its displayed course offers. Initial seats are not known
        # from the owner's report, so cover both verified zero and unknown.
        for initial_count in (0,None):
            with self.subTest(initial_count=initial_count):
                result=finalize_selector_payload(payload(candidates+[offer(initial,True)]),
                    [renewal,initial],{"sessions":[demand(renewal,1),demand(initial,initial_count)]},POLICY)
                self.assertEqual(["17:00"],[item["startTime"] for item in result["offers"]])
                self.assertEqual(["2026-10-12"],result["occupiedDates"])
                flattened=[item for day in result["dates"] for slot in day["startTimes"] for item in slot["courses"]]
                self.assertEqual(result["offers"],flattened)
                rejected={item["startTime"] for item in result["rejectedCourseStartTimes"]}
                self.assertEqual(set(orphan_times),rejected)

    def test_reschedule_closes_old_and_new_dates_and_never_promotes_stale_time(self):
        source=occurrence("heartcode","210549","12:30","2026-10-03",60)
        old={**demand(source,1),"start_at":"2026-10-02T10:00:00-04:00"}
        issues=reconciliation_issues([source],[old])
        self.assertEqual({"2026-10-02","2026-10-03"},{r["date"] for r in issues})
        self.assertTrue(all(r["code"]=="STALE_ANCHOR" for r in issues))
        result=finalize_selector_payload(payload([offer(source,True),offer(occurrence("x","210549","10:00","2026-10-03",60))]),
            [source],{"sessions":[old]},POLICY)
        self.assertEqual(0,result["anchor_policy"]["anchors_promoted"])
        self.assertEqual(["12:30"],[r["startTime"] for r in result["offers"]])

    def test_missing_projection_blocks_synthesis_even_with_current_roster(self):
        source=occurrence("initial","209806","12:45")
        issues=reconciliation_issues([source],[{**demand(source,2),"workspace_projection_status":"missing"}])
        self.assertEqual("MISSING_SESSION_PROJECTION",issues[0]["code"])

    def test_private_unknown_roster_outside_public_schedule_still_blocks_synthesis(self):
        private={**demand(occurrence("private","210549","12:30"),None),"visibility":"private"}
        result=finalize_selector_payload(payload([offer(occurrence("x","210549","07:45"))]),
            [],{"sessions":[private]},POLICY)
        self.assertEqual([],result["offers"])
        self.assertEqual("MISSING_ROSTER",result["reconciliationIssues"][0]["code"])

    def test_private_offsite_canonical_commitment_blocks_without_calendar_or_workspace(self):
        row={"canonical_session_id":"church","session_status":"scheduled",
             "start_at":"2026-10-03T13:00:00Z","end_at":"2026-10-03T15:30:00Z",
             "consumption_start_at":"2026-10-03T13:00:00Z","consumption_end_at":"2026-10-03T15:30:00Z",
             "location_name":"Christ Community","lead_instructor_name":"Brian Ennis",
             "active_registration_count":0,"workspace_projection_status":"missing","visibility":"private"}
        blocks=build_occupancy({"canonical_demand":{"sessions":[row]}},{})
        self.assertTrue(has_conflict(datetime(2026,10,3,10),datetime(2026,10,3,11),blocks,"Room B",{"display_name":"Brian Ennis"})[0])
        self.assertFalse(has_conflict(datetime(2026,10,3,12,30),datetime(2026,10,3,13,30),blocks,"Room B",{"display_name":"Brian Ennis"})[0])
        result=finalize_selector_payload(payload([offer(occurrence("x","210549","12:30","2026-10-03"))]),[],{"sessions":[row]},POLICY)
        self.assertEqual([],result["offers"])

    def test_short_ics_reserves_full_course_duration(self):
        source=occurrence("heartcode","210549","12:30","2026-10-03",30)
        rules={"210549":{"duration_minutes":60,"scheduler_consumption_minutes":60,
               "setup_buffer_minutes":0,"cleanup_buffer_minutes":0}}
        blocks=build_occupancy({"schedule_future":{"sessions":[source]}},rules)
        self.assertEqual(datetime(2026,10,3,13,30),blocks[0]["end"])
        self.assertTrue(has_conflict(datetime(2026,10,3,13,15),datetime(2026,10,3,13,30),blocks,"Room B",{"display_name":"Brian Ennis"})[0])

    def test_adr_cross_midnight_lane_uses_eastern_not_utc(self):
        events={"events":[{"instructor_key":"brian","source_key":"brian_do_not_schedule",
            "start":"2026-10-02T21:00:00Z","end":"2026-10-03T11:00:00Z"}]}
        cells=operational_lane_cells({},events)
        self.assertEqual(("2026-10-02","17:00"),(cells[0]["date"],cells[0]["startTime"]))
        self.assertEqual(("2026-10-03","06:45"),(cells[-1]["date"],cells[-1]["startTime"]))
        truth=daily_truth({},events,{"sessions":[]})
        self.assertEqual(1,len(truth["2026-10-02"]["hardBlocks"]))
        self.assertEqual(1,len(truth["2026-10-03"]["hardBlocks"]))

    def test_barnacle_requires_explicit_pair_same_resources_and_exact_boundary(self):
        anchor={"course_id":"anchor","start_at":"2026-10-03T12:30:00-04:00",
                "end_at":"2026-10-03T13:30:00-04:00","location":"Room B","instructor":"Brian Ennis"}
        item=offer(occurrence("candidate","candidate","13:30","2026-10-03",60))
        allowed={**POLICY,"barnacle_course_pairs":[["anchor","candidate"]]}
        self.assertTrue(barnacle_compatible(item,anchor,allowed))
        for changed in ({**item,"instructor":"Someone Else"},{**item,"location":"Elsewhere"},
                        offer(occurrence("candidate","candidate","00:00","2026-10-03",60))):
            self.assertFalse(barnacle_compatible(changed,anchor,allowed))
        self.assertFalse(barnacle_compatible(item,anchor,POLICY))

    def test_diagnostic_reports_orphan_and_hard_block_collision_without_cell_inspection(self):
        truth={"2026-10-03":{"classes":[{"externalClassId":"heartcode"}],"hardBlocks":[{
            "start":"2026-10-03T09:00:00-04:00","end":"2026-10-03T11:30:00-04:00",
            "source":"brian_do_not_schedule","label":"Busy"}]}}
        cell={"date":"2026-10-03","startTime":"10:00","durationMinutes":60,
              "result":"offered","courseName":"BLS","instructor":"Brian Ennis"}
        self.assertEqual({"ORPHAN_SYNTHETIC_OFFER","HARD_BLOCK_COLLISION"},
                         {r["code"] for r in publication_contradictions([cell],truth)})

if __name__=="__main__":
    unittest.main()
