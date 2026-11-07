from __future__ import annotations

import unittest
import copy
from unittest.mock import patch
from urllib.parse import urlencode
from scripts import validate_public_refresh_output as validator

from scripts.validate_public_refresh_output import validate_admin_reconciliation, validate_public_demand, validate_selector_lease
from scripts.fetch_canonical_scheduling_demand import validate_payload, SCHEMA_VERSION
from datetime import datetime, timedelta, timezone


class ValidatePublicRefreshOutputTests(unittest.TestCase):
    def native_payload(self):
        lease=(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()
        course=dict(courseId='509474',courseName='Skills Session Only',offerType='dynamic_appointment',
            publicSelectable=True,date='2031-04-05',startTime='10:00',instructor='Brian Ennis',
            location=':: Wilmington; Shipyard Blvd',resource=':: Wilmington; Shipyard Blvd - B',
            durationMinutes=45,schedulerConsumptionMinutes=60,cleanupBufferMinutes=15,setupBufferMinutes=0,
            availabilityBlockId='fixture-source',sourceSessionIds=[],validUntil=lease,occupiedUntil='2031-04-05T15:00:00Z')
        course['appointmentUrl']='/register/skills-session/?'+urlencode(dict(course='509474',date=course['date'],
            startTime=course['startTime'],instructor=course['instructor'],location=course['location']))
        return dict(schemaVersion='selector-resolved-availability.v1',anchor_policy={'finalized':True},
            validUntil=lease,dates=[dict(date=course['date'],startTimes=[dict(startTime='10:00',courses=[course])])],
            counts=dict(publicSelectableDateCount=1,publicSelectableStartTimeCount=1,publicSelectableOfferCount=1))

    def test_native_skills_publish_without_enrollware_container(self):
        for key in ['heartsaver','arc','hsi']:
            with self.subTest(key=key), patch.object(validator,'load_json',return_value=self.native_payload()):
                self.assertEqual(validator.validate_selector(key,set()),dict(dates=1,starts=1,offers=1))

    def test_native_skills_reject_tampering_and_preserve_legacy_requirements(self):
        for field,value in [('publicSelectable',False),('durationMinutes',90),('cleanupBufferMinutes',0),
                            ('instructor','Other'),('resource','Room C'),('sourceSessionIds',None),
                            ('appointmentUrl','https://example.invalid/register/skills-session/'),
                            ('occupiedUntil','2031-04-05T14:45:00Z'),
                            ('validUntil',(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat())]:
            payload=copy.deepcopy(self.native_payload());payload['dates'][0]['startTimes'][0]['courses'][0][field]=value
            with self.subTest(field=field), patch.object(validator,'load_json',return_value=payload):
                with self.assertRaises(ValueError):validator.validate_selector('heartsaver',set())
        with patch.object(validator,'load_json',return_value=self.native_payload()):
            with self.assertRaisesRegex(ValueError,'invalid page context'):validator.validate_selector('pals',set())
        payload=self.native_payload();payload['dates'][0]['startTimes'][0]['courses'][0]['courseId']='209806'
        with patch.object(validator,'load_json',return_value=payload):
            with self.assertRaisesRegex(ValueError,'appointmentDayId'):validator.validate_selector('bls',set())

    def test_expired_lease_preserves_existing_classes_but_rejects_calculated_offers(self):
        payload=dict(validUntil=(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat(),
                     dates=[dict(startTimes=[dict(courses=[dict(offerType='seated_class')])])])
        validate_selector_lease(payload,'acls')
        for kind in ['dynamic_appointment',None]:
            payload['dates'][0]['startTimes'][0]['courses'].append(dict(offerType=kind))
            with self.assertRaisesRegex(ValueError,'expired publication'):
                validate_selector_lease(payload,'acls')
            payload['dates'][0]['startTimes'][0]['courses'].pop()

    def demand(self, count=1):
        now = datetime(2026, 9, 27, 14, 0, tzinfo=timezone.utc)
        return now, {
            "schema_version": SCHEMA_VERSION, "generated_at": now.isoformat(),
            "non_session_sources": [], "sessions": [{
                "canonical_session_id": "canonical-incident", "external_class_id": "14361098",
                "active_registration_count": count, "count_available": True,
                "demand_basis": "canonical_active_registrations", "freshness_minutes": 60,
                "source_observed_at": (now - timedelta(minutes=59)).isoformat(),
            }],
        }

    def test_current_zero_and_positive_counts_allow_publication(self):
        for count in (0, 1):
            now, demand = self.demand(count)
            validate_public_demand([{"session_id": "14361098"}], validate_payload(demand, now=now))

    def test_source_expiring_during_build_refuses_publication_without_faking_zero(self):
        now, demand = self.demand()
        generated = [{"session_id": "14361098", "active_registration_count": 1, "count_available": True}]
        validate_public_demand(generated, validate_payload(demand, now=now))
        expired = validate_payload(demand, now=now + timedelta(minutes=2))
        with self.assertRaisesRegex(ValueError, "14361098: stale_reconciliation"):
            validate_public_demand(generated, expired)
        self.assertIsNone(expired["sessions"][0]["active_registration_count"])
        self.assertEqual(generated[0]["active_registration_count"], 1)

    def test_unknown_relationships_preserve_occupancy_but_refuse_fabricated_counts(self):
        now, demand = self.demand()
        validate_public_demand([{"session_id": "14421081"}], validate_payload(demand, now=now))
        with self.assertRaisesRegex(ValueError, "14421081: missing_canonical_session"):
            validate_public_demand([{"session_id": "14421081", "active_registration_count":0}], validate_payload(demand, now=now))
        duplicate = dict(demand["sessions"][0], canonical_session_id="another-canonical")
        demand["sessions"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "14361098: ambiguous"):
            validate_public_demand([{"session_id": "14361098", "count_available":True}], validate_payload(demand, now=now))

    def test_private_or_quarantined_sources_do_not_block_unrelated_public_rows(self):
        now, demand = self.demand()
        demand["sessions"].append({
            "canonical_session_id": "private-unreconciled", "external_class_id": "13895152",
            "active_registration_count": None, "count_available": False, "demand_basis": "unknown",
        })
        validate_public_demand([{"session_id": "14361098"}], validate_payload(demand, now=now))

    def test_allows_durable_manual_but_rejects_stale_enrollware(self) -> None:
        current = {"sessions": [{"session_id": "ew-current"}]}
        admin = {"sources": {"hot_sync": {"available": True}}, "sessions": [
            {"session_id": "ew-current", "source": "enrollware_ical"},
            {"session_id": "hs-durable", "source": "hot_sync_manual", "hot_sync": True},
            {"session_id": "13963996", "source": "enrollware_ical"},
        ]}
        with self.assertRaisesRegex(ValueError, "13963996"):
            validate_admin_reconciliation(current, admin)

        admin["sessions"].pop()
        self.assertEqual({"ew-current", "hs-durable"}, validate_admin_reconciliation(current, admin))

    def test_rejects_manual_copy_of_same_durable_lineage(self) -> None:
        admin = {"sources": {"hot_sync": {"available": True}}, "sessions": [
            {"session_id": "hs-durable", "source": "hot_sync_manual", "hot_sync": True},
            {"session_id": "manual-copy-hs-durable", "source": "hot_sync_manual", "hot_sync": True},
        ]}
        with self.assertRaisesRegex(ValueError, "duplicate durable sessions"):
            validate_admin_reconciliation({"sessions": []}, admin)

    def test_rejects_admin_output_built_without_authoritative_hot_sync(self) -> None:
        admin = {"sources": {"hot_sync": {"available": False}}, "sessions": []}
        with self.assertRaisesRegex(ValueError, "authoritative HOT_SYNC"):
            validate_admin_reconciliation({"sessions": []}, admin)


if __name__ == "__main__":
    unittest.main()
