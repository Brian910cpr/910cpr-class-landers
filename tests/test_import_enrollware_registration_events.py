import tempfile
import unittest
from pathlib import Path

from scripts import check_first_dynamic_booking_status as status_runner
from scripts import import_enrollware_registration_events as importer


class EnrollwareRegistrationEventImportTests(unittest.TestCase):
    def seed_payload(self):
        return {
            "seeds": [
                {
                    "seed_id": "seed-offer-209806-instructor_24057895173-20260621-1700",
                    "source_offer_id": "offer-209806-instructor_24057895173-20260621-1700",
                    "course_id": "209806",
                    "course_title": "AHA BLS Provider",
                    "appointment_display_start": "2026-06-21T17:00:00",
                    "scheduler_consumption_start": "2026-06-21T17:00:00",
                    "scheduler_consumption_end": "2026-06-21T19:45:00",
                    "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                    "instructor_display_name": "Brian Ennis",
                }
            ]
        }

    def write_temp_csv(self, content: str) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        csv_path = Path(tmpdir.name) / "registration_events.csv"
        csv_path.write_text(content, encoding="utf-8")
        return csv_path

    def test_synthetic_bls_registration_row_matches_approved_seed(self):
        fixture = self.write_temp_csv(
            "regId,courseId,courseSchedId,courseName,locationName,startTime,instructor,student,email,status,balanceDue\n"
            '90000001,209806,99000001,AHA BLS Provider (Initial),"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Test Student,student@example.test,Pending,75\n'
        )
        result = importer.import_events(fixture, self.seed_payload())

        self.assertEqual(result["summary"]["rows_read"], 1)
        self.assertEqual(result["summary"]["matched_appointment_seeds"], 1)
        self.assertEqual(result["summary"]["unmatched_registrations"], 0)
        match = result["matched_seed_records"][0]
        self.assertEqual(match["regId"], "90000001")
        self.assertEqual(match["courseSchedId"], "99000001")
        self.assertEqual(match["registration_status"], "booked_pending_class_report")
        self.assertIn("registration_signal_seen", match["status_history"])

    def test_synthetic_real_sheet_shape_matches_and_reports_bad_rows(self):
        fixture = self.write_temp_csv(
            "Zap ID,Zap Meta Timestamp,Registration Id,Course Id,Course Sched ID,Course Name,Discipline,Location Name,Class Start Time,Instructor Name,First Name,Last Name,Email Address,Phone Number,Alternate Phone Number,Address 1,Address 2,City,State,Zip,Country,License,Promo Code,Class Price Code,Status,Balance Due,Class Price,Order Total,Option Total,Ship Price,Options,Questions,Payments,Comments,Query String,Source Metadata,Unmapped Zapier Field\n"
            'zap-test-001,2026-06-20T10:30:00-04:00,90000001,209806,99000001,AHA BLS Provider (Initial),AHA BLS,"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Test,Student,student@example.test,555-0100,555-0109,123 Test St,Suite 4,Testville,TS,00000,US,TEST-LICENSE,PILOT,STANDARD,Pending,75,75,75,0,0,"Book: none; Keycode: none","Employer: Example Company; Department: Training; How did you hear about us? Test import","Pending payment; balance due 75","Billing contact: Test Manager","utm_source=synthetic-test","Zap ID zap-test-001; Sheet row 2",synthetic-extra-value\n'
            ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\n"
            'zap-test-002,2026-06-20T10:31:00-04:00,,209806,99000002,AHA BLS Provider (Initial),AHA BLS,"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Missing,RegId,missing-regid@example.test,555-0101,,,,,,,,,,Pending,75,75,75,0,0,,,,,missing-regid-extra\n'
            'zap-test-003,2026-06-20T10:32:00-04:00,90000002,209806,,AHA BLS Provider (Initial),AHA BLS,"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Missing,Sched,missing-sched@example.test,555-0102,,,,,,,,,,Pending,75,75,75,0,0,,,,,\n'
            'zap-test-004,2026-06-20T10:33:00-04:00,90000003,209806,99000001,AHA BLS Provider (Initial),AHA BLS,"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Second,Student,second@example.test,555-0103,,,,,,,,,,Pending,75,75,75,0,0,,,,,\n'
            'zap-test-005,2026-06-20T10:34:00-04:00,90000003,209806,99000001,AHA BLS Provider (Initial),AHA BLS,"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Second,Student,second@example.test,555-0103,,,,,,,,,,Pending,75,75,75,0,0,,,,,\n'
            'zap-test-006,2026-06-20T10:35:00-04:00,90000004,209806,99000003,AHA BLS Provider (Initial),AHA BLS,"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",not a date,Brian Ennis,Bad,Date,bad-date@example.test,555-0104,,,,,,,,,,Pending,75,75,75,0,0,,,,,\n'
        )

        result = importer.import_events(fixture, self.seed_payload())
        summary = result["summary"]

        self.assertEqual(summary["rows_read"], 7)
        self.assertEqual(summary["blank_rows_skipped"], 1)
        self.assertEqual(summary["normalized_events"], 6)
        self.assertEqual(summary["matched_appointment_seeds"], 2)
        self.assertEqual(summary["unmatched_registrations"], 3)
        self.assertEqual(summary["duplicate_regIds"], ["90000003"])
        self.assertEqual(summary["missing_required_identifiers"]["regId"], 1)
        self.assertEqual(summary["missing_required_identifiers"]["courseSchedId"], 1)
        self.assertEqual(summary["unparseable_startTimes"], ["90000004"])
        self.assertEqual(summary["courseSchedId_registration_counts"]["99000001"], 2)
        self.assertEqual(
            summary["duplicate_courseSchedIds_with_different_regIds"],
            {"99000001": ["90000001", "90000003"]},
        )
        first_event = result["normalized_events"][0]
        self.assertEqual(first_event["discipline"], "AHA BLS")
        self.assertEqual(first_event["firstName"], "Test")
        self.assertEqual(first_event["lastName"], "Student")
        self.assertEqual(first_event["student"], "Test Student")
        self.assertEqual(first_event["emailAddress"], "student@example.test")
        self.assertEqual(first_event["phoneNumber"], "555-0100")
        self.assertEqual(first_event["altPhoneNumber"], "555-0109")
        self.assertEqual(first_event["address1"], "123 Test St")
        self.assertEqual(first_event["address2"], "Suite 4")
        self.assertEqual(first_event["city"], "Testville")
        self.assertEqual(first_event["state"], "TS")
        self.assertEqual(first_event["zip"], "00000")
        self.assertEqual(first_event["country"], "US")
        self.assertEqual(first_event["license"], "TEST-LICENSE")
        self.assertEqual(first_event["promoCode"], "PILOT")
        self.assertEqual(first_event["classPriceCode"], "STANDARD")
        self.assertEqual(first_event["classPrice"], "75")
        self.assertEqual(first_event["orderTotal"], "75")
        self.assertEqual(first_event["optionTotal"], "0")
        self.assertEqual(first_event["shipPrice"], "0")
        self.assertIn("Employer: Example Company", first_event["questions"])
        self.assertEqual(first_event["comments"], "Billing contact: Test Manager")
        self.assertEqual(first_event["queryString"], "utm_source=synthetic-test")
        self.assertEqual(first_event["receivedAt"], "2026-06-20T10:30:00-04:00")
        self.assertEqual(first_event["sourceMetadata"], "Zap ID zap-test-001; Sheet row 2")
        self.assertEqual(first_event["corporate_account_preview"]["email_domain"], "example.test")
        self.assertEqual(first_event["corporate_account_preview"]["employer_clue"], "Example Company")
        self.assertEqual(first_event["corporate_account_preview"]["possible_person_key"], "email:student@example.test")
        self.assertEqual(first_event["corporate_account_preview"]["possible_account_key"], "email_domain:example.test")
        self.assertEqual(first_event["raw"]["Unmapped Zapier Field"], "synthetic-extra-value")
        self.assertEqual(first_event["raw_unmapped_fields"]["Unmapped Zapier Field"], "synthetic-extra-value")
        self.assertIn("Example Company", summary["corporate_account_preview"]["employer_clues"])

    def test_duplicate_reg_id_is_not_double_counted(self):
        fixture = self.write_temp_csv(
            "regId,courseId,courseSchedId,courseName,locationName,startTime,instructor,student,email,status,balanceDue\n"
            '90000001,209806,99000001,AHA BLS Provider (Initial),"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Test Student,student@example.test,Pending,75\n'
            '90000001,209806,99000001,AHA BLS Provider (Initial),"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Test Student,student@example.test,Pending,75\n'
        )
        result = importer.import_events(fixture, self.seed_payload())

        self.assertEqual(result["summary"]["rows_read"], 2)
        self.assertEqual(result["summary"]["unique_registration_events"], 1)
        self.assertEqual(result["summary"]["duplicate_regIds"], ["90000001"])
        self.assertEqual(result["summary"]["matched_appointment_seeds"], 1)
        self.assertEqual(result["summary"]["courseSchedId_registration_counts"], {"99000001": 1})

    def test_same_course_sched_id_groups_multiple_unique_registrations(self):
        fixture = self.write_temp_csv(
            "regId,courseId,courseSchedId,courseName,locationName,startTime,instructor,student,email,status,balanceDue\n"
            '90000001,209806,99000001,AHA BLS Provider (Initial),"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Test Student,student@example.test,Pending,75\n'
            '90000002,209806,99000001,AHA BLS Provider (Initial),"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Second Student,student2@example.test,Pending,75\n'
        )
        result = importer.import_events(fixture, self.seed_payload())

        self.assertEqual(result["summary"]["unique_registration_events"], 2)
        self.assertEqual(result["summary"]["matched_appointment_seeds"], 2)
        self.assertEqual(result["summary"]["courseSchedId_registration_counts"], {"99000001": 2})

    def test_booking_status_runner_degrades_gracefully_when_registration_signal_missing(self):
        status = status_runner.build_status()
        stage_7 = next(stage for stage in status["stages"] if stage["number"] == 7)

        self.assertIn(stage_7["passed"], [True, False])
        if not stage_7["passed"]:
            self.assertEqual(
                stage_7["blocker"],
                "No matched Zapier/Sheet registration signal has been imported for a seed.",
            )
            self.assertIn("appointment_seed_registration_matches", status.get("load_errors", {}))


if __name__ == "__main__":
    unittest.main()
