import json,unittest
from pathlib import Path
from scripts.generate_dynamic_offers import normalize_location_resource

class RoomAliasTests(unittest.TestCase):
    def test_declared_room_alias_preserves_actual_room_assignment(self):
        resources=json.loads((Path(__file__).resolve().parents[1]/'data/config/location_resource_map.json').read_text(encoding='utf-8'))
        for room in resources['locations'][0]['internal_resources']:
            for alias in room.get('aliases',[]):
                public,physical,resolved=normalize_location_resource(alias,alias,resources)
                self.assertTrue(resolved)
                self.assertEqual(public,resources['locations'][0]['canonical_public_location'])
                self.assertEqual(physical,room['resource_name'])
        _,_,resolved=normalize_location_resource('Unknown offsite','Unknown offsite',resources)
        self.assertFalse(resolved)
