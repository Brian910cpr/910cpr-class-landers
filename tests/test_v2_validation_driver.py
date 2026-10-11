"""Safety checks for the validation-only driver, without real credentials."""
import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import validate_v2_real_sources as driver
from tests import test_layered_publication_adapter as fixtures


class ValidationDriverTests(unittest.TestCase):
    def test_attribution_preserves_booking_identity_but_changed_time_or_host_does_not(self):
        expected='https://booking.test/enroll?courseId=209806&appointmentDayId=1&startTime=12%3A00%20AM'
        decorated='https://booking.test/enroll?startTime=12%3A00+AM&appointmentDayId=1&courseId=209806&utm_source=direct'
        self.assertTrue(driver.same_public_booking_url(expected,decorated))
        self.assertFalse(driver.same_public_booking_url(expected,decorated.replace('12%3A00','13%3A00')))
        self.assertFalse(driver.same_public_booking_url(expected,decorated.replace('booking.test','wrong.test')))

    def test_private_source_id_is_removed_from_shareable_reason_counts(self):
        self.assertEqual(driver.public_reasons({'conflict_or_transition:private-source-id':2,
                                               'outside_explicit_availability':3}),
                         {'conflict_or_transition':2,'outside_explicit_availability':3})

    def test_real_occupancy_guard_detects_lost_positive_interval(self):
        f=fixtures.LayeredPublicationTests();f.setUp();f.add(11,'12:00','13:00',count=1)
        payload=f.payload()
        self.assertEqual(driver.physical_occupancy_preserved(payload,payload),0)
        broken=copy.deepcopy(payload)
        for report in broken['layeredDiagnostics']['reports']:report['normalized_occupancy']=[]
        self.assertGreater(driver.physical_occupancy_preserved(payload,broken),0)

    def test_exception_body_cannot_leak_to_artifact_or_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            stream=io.StringIO()
            with patch('sys.argv',['validate','--baseline','fixture','--output',directory]), \
                 patch.object(driver,'run',side_effect=RuntimeError('privateValueThatMustNotLeak')), \
                 contextlib.redirect_stdout(stream):
                self.assertEqual(driver.main(),1)
            result=(Path(directory)/'sanitized/summary.json').read_text()
            self.assertNotIn('privateValueThatMustNotLeak',result+stream.getvalue())
            self.assertEqual(json.loads(result)['failure_code'],'source_or_validation_check_failed')
