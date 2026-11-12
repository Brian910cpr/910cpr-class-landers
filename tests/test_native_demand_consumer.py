import unittest
from datetime import datetime,timezone,timedelta
from scripts.fetch_canonical_scheduling_demand import validate_payload

NOW=datetime(2030,9,1,12,tzinfo=timezone.utc)
def payload(**override):
    row=dict(canonical_session_id='fixture',external_class_id='12345',count_available=True,
        active_registration_count=6,demand_status='current',freshness_minutes=None,
        source_observed_at=None,demand_basis='native_authoritative_occupied_seats',
        canonical_registered_count=2,held_seat_count=1,unreconciled_reserved_count=3)
    row.update(override)
    return dict(schema_version='910cpr-canonical-scheduling-demand.v1',generated_at=NOW.isoformat(),sessions=[row])
class NativeDemandConsumerTests(unittest.TestCase):
    def test_native_occupied_reserve_and_holds_survive_consumer(self):
        result=validate_payload(payload(),now=NOW)['sessions'][0]
        self.assertEqual(result['active_registration_count'],6)
        self.assertEqual(result['unreconciled_reserved_count'],3)
        self.assertTrue(result['count_available'])
    def test_legacy_freshness_still_expires(self):
        result=validate_payload(payload(freshness_minutes=60,source_observed_at='2020-01-01T00:00:00Z'),now=NOW)['sessions'][0]
        self.assertIsNone(result['active_registration_count'])
        self.assertFalse(result['count_available'])
    def test_native_snapshot_still_expires(self):
        with self.assertRaises(ValueError): validate_payload(payload(),now=NOW+timedelta(minutes=16))
    def test_pii_is_rejected(self):
        with self.assertRaises(ValueError): validate_payload(payload(email='fixture@example.test'),now=NOW)
    def test_unknown_is_never_zero(self):
        result=validate_payload(payload(active_registration_count=None,count_available=False,demand_basis='unknown'),now=NOW)['sessions'][0]
        self.assertIsNone(result['active_registration_count'])
if __name__=='__main__': unittest.main()
