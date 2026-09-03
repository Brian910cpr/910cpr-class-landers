from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "corp" / "nhcso" / "index.html"
EDGE_FUNCTION = ROOT / "supabase" / "functions" / "nhcso-workspace" / "index.ts"


class NhcsoRosterWorkflowTests(unittest.TestCase):
    def test_pasted_people_are_deduplicated_and_trailing_separators_are_cleaned(self) -> None:
        script = r"""
const fs=require('fs');
const html=fs.readFileSync(process.argv[1],'utf8');
const start=html.indexOf('function parseLine');
const end=html.indexOf('function activeCount',start);
if(start<0||end<0)throw new Error('roster parsing functions not found');
let workingRoster=JSON.parse(process.argv[2]);
const fields={paste:{value:process.argv[3]},saveStatus:{}};
const $=id=>fields[id];
function renderRoster(){}
const document={querySelectorAll:()=>[]};
eval(html.slice(start,end));
addPastedPeople();
process.stdout.write(JSON.stringify({roster:workingRoster,status:fields.saveStatus.textContent}));
"""
        starting = [{"name": "Paul McMahon", "email": "pmcmahon@nhcgov.com", "status": "Active"}]
        pasted = "Paul McMahon - pmcmahon@nhcgov.com\nLatrice McKoy - lmckoy@nhcgov.com"
        completed = subprocess.run(
            ["node", "-e", script, str(PAGE), json.dumps(starting), pasted],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual([person["name"] for person in result["roster"]], ["Paul McMahon", "Latrice McKoy"])
        self.assertEqual(len(result["roster"]), 2)
        self.assertIn("1 already on this roster was not duplicated", result["status"])

    def test_roster_changes_are_explicitly_unsaved_until_submit(self) -> None:
        html = PAGE.read_text(encoding="utf-8")
        self.assertIn("Click Submit / Save Class to make the change permanent.", html)
        self.assertIn('title="Mark as Removed"', html)

    def test_server_canonicalizes_existing_identity_and_deduplicates_each_batch(self) -> None:
        source = EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn('existingByIdentity.get(identity)', source)
        self.assertIn('stagedRows.set(identity', source)
        self.assertIn('const rows = [...stagedRows.values()]', source)


if __name__ == "__main__":
    unittest.main()
