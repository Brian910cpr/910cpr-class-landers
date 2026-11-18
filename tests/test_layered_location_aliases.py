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

    def test_room_worded_shipyard_office_label_does_not_invent_a_room(self):
        resources=json.loads((Path(__file__).resolve().parents[1]/'data/config/location_resource_map.json').read_text(encoding='utf-8'))
        label='910CPR Office - Shipyard Blvd, Room B'
        public,physical,resolved=normalize_location_resource(label,label,resources)
        self.assertTrue(resolved)
        self.assertEqual(public,':: Wilmington; Shipyard Blvd')
        # Venue is confirmed, but this wording is not a resource_id assignment.
        # Continue using the existing conservative primary-room hold.
        self.assertEqual(physical,label)
        for offsite in ('MedNorth @ 917 N 4th St',
                        'Carolina Beach Physical Therapy, 1300 Bridge Barrier Road, Building 3, Carolina Beach NC 28428',
                        'NC Sound, 2925 Boundary Street, Suite 29, Wilmington NC 28405'):
            _,_,known=normalize_location_resource(offsite,offsite,resources)
            self.assertFalse(known)
