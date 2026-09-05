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

    def test_ecard_lookup_copies_only_the_first_twenty_numbers_one_per_line(self) -> None:
        html = PAGE.read_text(encoding="utf-8")
        self.assertIn("new Set([...rosterNumbers,...noteNumbers])", html)
        self.assertIn("numbers.join('\\n')", html)
        self.assertIn("https://www.910cpr.com/go/myecards", html)
        self.assertIn("navigator.clipboard.writeText", html)
        script = r"""
const fs=require('fs');
const html=fs.readFileSync(process.argv[1],'utf8');
const start=html.indexOf('function ecardNumbersForLookup');
const end=html.indexOf('function renderRoster',start);
if(start<0||end<0)throw new Error('eCard lookup function not found');
const workingRoster=[];
const $=()=>({value:''});
eval(html.slice(start,end));
const roster=Array.from({length:23},(_,i)=>({ecard_number:i===1?'':`  CARD-${i+1}  `}));
process.stdout.write(ecardNumbersForLookup(roster).join('\n'));
"""
        completed = subprocess.run(
            ["node", "-e", script, str(PAGE)],
            check=True,
            capture_output=True,
            text=True,
        )
        lines = completed.stdout.splitlines()
        self.assertEqual(len(lines), 20)
        self.assertEqual(lines[0], "CARD-1")
        self.assertEqual(lines[1], "CARD-3")
        self.assertEqual(lines[-1], "CARD-21")
        self.assertFalse(completed.stdout.endswith("\n"))

    def test_ecard_lookup_recognizes_existing_tab_separated_note_exports(self) -> None:
        script = r"""
const fs=require('fs');
const html=fs.readFileSync(process.argv[1],'utf8');
const start=html.indexOf('function ecardNumbersForLookup');
const end=html.indexOf('function renderRoster',start);
const $=()=>({value:''});
eval(html.slice(start,end));
const notes='271267055184\tKristopher Withem\tkwithem@nhcgov.com\nNot an eCard line\n  271267055185\tAndrew McKay';
process.stdout.write(ecardNumbersForLookup([],notes).join('\n'));
"""
        completed = subprocess.run(
            ["node", "-e", script, str(PAGE)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout, "271267055184\n271267055185")

    def test_uploaded_documents_have_download_and_confirmed_delete_controls(self) -> None:
        html = PAGE.read_text(encoding="utf-8")
        source = EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn("data-document-download", html)
        self.assertIn("data-document-delete", html)
        self.assertIn("Permanently delete", html)
        self.assertIn("action:'get_document_link'", html)
        self.assertIn("action:'delete_document'", html)
        self.assertIn('if (action === "delete_document")', source)
        self.assertIn('.storage.from("nhcso-class-docs").remove', source)

    def test_finalization_is_confirmed_and_enforced_by_the_backend(self) -> None:
        html = PAGE.read_text(encoding="utf-8")
        source = EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn('id="finalize"', html)
        self.assertIn("Type the complete class number to continue", html)
        self.assertIn("action:'finalize_class'", html)
        self.assertIn("Print Final AHA Roster", html)
        self.assertIn('if (action === "finalize_class")', source)
        self.assertIn('existingClass?.status === "finalized"', source)
        self.assertIn('classRow?.status === "finalized"', source)
        self.assertIn("Finalized classes cannot be deleted", source)

    def test_server_canonicalizes_existing_identity_and_deduplicates_each_batch(self) -> None:
        source = EDGE_FUNCTION.read_text(encoding="utf-8")
        self.assertIn('existingByIdentity.get(identity)', source)
        self.assertIn('stagedRows.set(identity', source)
        self.assertIn('const rows = [...stagedRows.values()]', source)


if __name__ == "__main__":
    unittest.main()
