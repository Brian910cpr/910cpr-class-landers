import unittest,copy
from datetime import datetime,timedelta
from public_edge_planner_offline import blocks,candidates

def t(clock,day='2026-10-05'):return datetime.fromisoformat(day+'T'+clock+':00-04:00')
def row(id,start,end,location='Shipyard'):return {'id':id,'start':t(start),'end':t(end),'instructor':'Brian','location':location}
W={'start':t('00:00'),'end':t('00:00','2026-10-06'),'instructor':'Brian','location':'Shipyard'}
C={'bls-skills':60,'hs-skills':60,'bls-full':150}
class Proof(unittest.TestCase):
 def starts(self,rows):return [c['start'].strftime('%H:%M') for c in candidates(rows,W,C) if c['course']=='bls-skills']
 def test_growth(self):
  self.assertEqual(self.starts([row('noon','12:00','13:00')]),['11:00','13:00'])
  self.assertEqual(self.starts([row('noon','12:00','13:00'),row('right','13:00','14:00')]),['11:00','14:00'])
  self.assertEqual(self.starts([row('left','11:00','12:00'),row('noon','12:00','13:00'),row('right','13:00','14:00')]),['10:00','14:00'])
 def test_full_class_edges(self):
  cs=candidates([row('noon','12:00','13:00')],W,C)
  self.assertEqual([c['start'].strftime('%H:%M') for c in cs if c['course']=='bls-full'],['09:30','13:00'])
  self.assertEqual(self.starts([row('noon','12:00','13:00'),row('full','13:00','15:30')]),['11:00','15:30'])
 def test_no_scatter_and_multiple_blocks(self):self.assertEqual(self.starts([row('a','12:00','13:00'),row('b','18:00','19:00')]),['11:00','13:00','17:00','19:00'])
 def test_offsite_not_impossible_merge(self):self.assertEqual(len(blocks([row('a','12:00','13:00'),row('b','13:00','14:00','Offsite')])),2)
 def test_overnight(self):
  night=row('night','23:00','23:00');night['end']=t('01:00','2026-10-06');window={**W,'start':t('00:00','2026-10-06'),'end':t('04:00','2026-10-06')}
  self.assertEqual([c['start'].strftime('%H:%M') for c in candidates([night],window,{'skills':60})],['01:00'])
 def test_wide_and_tight(self):
  self.assertEqual(len(candidates([],W,{'skills':60})),24)
  self.assertEqual(len(candidates([],{**W,'start':t('04:00'),'end':t('06:00')},{'skills':60})),3)
 def test_bookings_immutable(self):
  rows=[row('a','12:00','13:00')];before=copy.deepcopy(rows);candidates(rows,W,C);self.assertEqual(rows,before)
 def test_unknown_duration_fails(self):
  with self.assertRaises(ValueError):blocks([row('unknown','12:00','12:00')])
if __name__=='__main__':unittest.main()
