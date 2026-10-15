import copy
import unittest
from scripts.public_registration_closures import apply_closures, load_closures, overlaps_closure


class ClosureTests(unittest.TestCase):
    def feed(self, day='2026-10-21', start='12:00', end='2026-10-21T14:30:00-04:00'):
        return dict(dates=[dict(date=day, startTimes=[dict(startTime=start, courses=[
            dict(courseId=str(i), offerType=kind, durationMinutes=120, occupiedUntil=end)
            for i,kind in enumerate(['dynamic_appointment','seated_class'])])])],
            layeredLandscape={'sources':[{'id':'preserve-class'}]})

    def test_all_choices_removed_and_sources_unmutated(self):
        feed=self.feed();before=copy.deepcopy(feed)
        result,removed=apply_closures(feed)
        self.assertEqual(result['dates'],[]);self.assertEqual(len(removed),2)
        self.assertEqual(feed,before)
        self.assertEqual(result['layeredLandscape'],before['layeredLandscape'])

    def test_boundaries_are_eastern_whole_day_and_half_open(self):
        c=load_closures()
        self.assertFalse(overlaps_closure('2026-10-21T03:00Z','2026-10-21T04:00Z',c))
        self.assertTrue(overlaps_closure('2026-10-21T03:59Z','2026-10-21T04:01Z',c))
        self.assertTrue(overlaps_closure('2026-10-22T03:59Z','2026-10-22T04:01Z',c))
        self.assertFalse(overlaps_closure('2026-10-22T04:00Z','2026-10-22T05:00Z',c))

    def test_tuesday_overnight_overlap_removed_thursday_preserved(self):
        self.assertEqual(apply_closures(self.feed('2026-10-20','23:30','2026-10-21T01:00-04:00'))[0]['dates'],[])
        self.assertEqual(len(apply_closures(self.feed('2026-10-22','00:00','2026-10-22T02:00-04:00'))[0]['dates']),1)

    def test_explicit_empty_policy_reopens_projection_without_changing_source(self):
        result,removed=apply_closures(self.feed(),[])
        self.assertEqual(len(result['dates']),1);self.assertEqual(removed,[])

    def test_duration_fallback_and_all_families(self):
        for family in ['BLS','Heartsaver','ARC','HSI','ACLS','PALS','USCG','Family CPR']:
            feed=self.feed()
            for course in feed['dates'][0]['startTimes'][0]['courses']:
                course.pop('occupiedUntil');course['courseFamily']=family
            self.assertEqual(apply_closures(feed)[0]['dates'],[])

    def test_generator_public_projection_uses_global_guard(self):
        from scripts.layered_publication_adapter import finalize
        from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
        feed=self.feed()
        feed['offers']=[dict(c,date='2026-10-21',startTime='12:00')
                        for c in feed['dates'][0]['startTimes'][0]['courses']]
        result=public_selector_availability_payload(finalize(feed))
        self.assertEqual(result['dates'],[])
