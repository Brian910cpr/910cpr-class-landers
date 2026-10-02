from datetime import datetime as D,timedelta
import unittest
from scripts.public_block_edges import merged_blocks,plan_starts,serialize_blocks,retain_validated_roles,VERSION
class GeometryTests(unittest.TestCase):
 def block(self,start='12:00',end='13:00',loc='Shipyard',cid='210549'):
  return {'start':D.fromisoformat('2026-10-10T'+start),'end':D.fromisoformat('2026-10-10T'+end),'location':loc,'instructor':'Brian Ennis','is_training':True,'course_id':cid,'source_file':'fixture','source_event_id':start}
 def starts(self,items,minutes=60,begin='07:00',end='23:00'):
  return plan_starts(D.fromisoformat('2026-10-10T'+begin),D.fromisoformat('2026-10-10T'+end),'Brian Ennis','Shipyard',minutes,merged_blocks(items),items)
 def test_noon_edges(self):self.assertEqual([x['start'].strftime('%H:%M') for x in self.starts([self.block()])],['11:00','13:00'])
 def test_right_fill_moves_right_edge(self):self.assertEqual([x['start'].strftime('%H:%M') for x in self.starts([self.block(),self.block('13:00','14:00')])],['11:00','14:00'])
 def test_left_fill_moves_left_edge(self):self.assertEqual([x['start'].strftime('%H:%M') for x in self.starts([self.block('11:00','12:00'),self.block(),self.block('13:00','14:00')])],['10:00','14:00'])
 def test_full_class_enters_chain(self):self.assertEqual([x['start'].strftime('%H:%M') for x in self.starts([self.block(),self.block('13:00','15:30',cid='209806')])],['11:00','15:30'])
 def test_multiple_blocks_keep_all_edges(self):self.assertEqual(len(self.starts([self.block(),self.block('18:00','19:00')])),4)
 def test_offsite_not_merged_and_not_sold_at_zero_travel(self):
  values=self.starts([self.block(loc='Offsite')]);self.assertTrue(all('OFFSITE_EDGE_LOCATION' in x['geometryReasons'] for x in values))
 def test_free_wide_hourly_and_tight_half_hour(self):
  self.assertEqual([x['start'].strftime('%H:%M') for x in self.starts([],begin='07:00',end='11:00')],['07:00','08:00','09:00','10:00'])
  self.assertEqual([x['start'].strftime('%H:%M') for x in self.starts([],begin='07:00',end='09:00')],['07:00','07:30','08:00'])
 def test_free_day_subtracts_hold(self):
  hold=self.block('08:00','09:00');hold['is_training']=False;values=self.starts([hold],begin='07:00',end='11:00');self.assertTrue(all(x['start']+timedelta(minutes=60)<=hold['start'] or x['start']>=hold['end'] for x in values))
 def test_midnight_edges_remain_datetime_based(self):
  item=self.block('23:00','23:30');item['end']=D.fromisoformat('2026-10-11T00:00');values=self.starts([item],begin='22:00',end='23:59');self.assertEqual(values[-1]['start'],D.fromisoformat('2026-10-11T00:00'))
 def test_oct10_cross_course_candidates_exist(self):
  hs=self.block('14:00','17:00',cid='209809');self.assertEqual([x['start'].strftime('%H:%M') for x in self.starts([hs],150)],['11:30','17:00']);self.assertEqual([x['start'].strftime('%H:%M') for x in self.starts([hs],60)],['13:00','17:00'])
if __name__=='__main__':unittest.main()
