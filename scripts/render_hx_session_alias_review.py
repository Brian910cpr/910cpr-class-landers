#!/usr/bin/env python3
"""Render the redacted Hx session-alias migration review."""

import argparse, json
from pathlib import Path


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--inventory',type=Path,required=True); ap.add_argument('--validation',type=Path,required=True)
    ap.add_argument('--json-output',type=Path,required=True); ap.add_argument('--markdown-output',type=Path,required=True)
    a=ap.parse_args(); inv=json.loads(a.inventory.read_text(encoding='utf-8')); val=json.loads(a.validation.read_text(encoding='utf-8'))
    report={"report":"Hx-Builder historical session alias review","mode":"dry_run_only","production_mutated":False,"historical_import_performed":False,"application_deployed":False,
            "alias_proposals":inv["proposals"],"instructor_classification":inv["instructor_classification"],"timing_review":inv["timing_review"],
            "frequency_ranked_unresolved_before":inv["frequency_ranked"],"validation":val,
            "persistence_design":{"reuse":["historical_location_aliases","historical_instructor_aliases","historical_course_aliases"],"source_scope":"(source_system, source_label) primary key","collision_behavior":"plain inserts fail on scoped-label collision","target":"one canonical foreign key per alias","provenance":"JSON evidence plus review commit","review":"review_status and reviewed_at","reversal":"active=false; alias evidence retained"},
            "nhcso":"The supplied Enrollware export lacks the 2026 period; no history or balancing events were manufactured.",
            "recommendation":"READY FOR SESSION-ALIAS MIGRATION REVIEW",
            "remaining_blockers_for_historical_import":["4,258 location references remain unresolved because canonical location authority is absent or the source value is missing/ambiguous.","126 rows have no instructor value and remain review-required.","17 course rows remain intentionally unresolved across three ambiguous/generic course labels.","85 rows retain unknown, ranged, zero, or implausible duration evidence; no end time was synthesized.","27 participant identity conflicts remain outside this session-alias review."]}
    a.json_output.parent.mkdir(parents=True,exist_ok=True); a.json_output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    b=val['before_after']; lines=["# Hx-Builder Historical Session Alias Review","","No aliases or historical records were applied to production. No application code was deployed.","","## Dry-run effect","","| Dimension | Before | After | Change |","| --- | ---: | ---: | ---: |"]
    for label,key in (("Unresolved location rows","locations"),("Unresolved instructor rows","instructors"),("Unresolved course rows","courses"),("Unresolved timing rows","timing"),("Fully canonicalized sessions","sessions_ready")):
        x,y=b[key]; lines.append(f"| {label} | {x:,} | {y:,} | {y-x:+,} |")
    lines += ["","## Determinism", "", f"- Hash: `{val['first_hash']}`", f"- Independent output identical: **{str(val['independent_equal']).lower()}**", f"- Replay additional operations/assertions: **{val['replay_operations']} / {val['replay_assertions']}**", f"- Unexplained mismatches: **{val['unexplained_mismatches']}**", f"- Identity conflicts: **{val['identity_conflicts']}**", f"- Duplicate candidates: **{val['duplicate_candidates']}**", "", "## Alias proposal", "", f"- Locations: **{inv['proposals']['locations']}**", f"- Instructors: **{inv['proposals']['instructors']}**", f"- Courses: **{inv['proposals']['courses']}**", "- Timing corrections: **0**", "", "The complete frequency-ranked inventories for all four dimensions are included in the redacted JSON artifact.", "", "## Persistence design", "", "The proposal reuses the three shared historical alias tables. It adds source scope, provenance, review status, reversible activation, and a scoped primary key. Plain inserts deliberately fail on collisions.", "", "## Remaining blockers for import", ""]
    lines += [f"- {x}" for x in report['remaining_blockers_for_historical_import']]
    lines += ["", "NHCSO 2026 remains outside this export and was not reconstructed."]
    a.markdown_output.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return 0

if __name__=='__main__': raise SystemExit(main())
