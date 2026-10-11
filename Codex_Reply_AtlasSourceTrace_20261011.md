# Atlas class source trace — 2026-10-11 (America/New_York)

State: VERIFIED source trace; BLOCKED final Atlas submission format and required selections.
Branch: codex/atlas-source-trace-20261011
Source commit inspected: 8c276183cd32d0b46af1a022f1551cfaed693678
Delivery commit: the commit containing this reply (resolve with git log -1 --format=%H -- this file).

## Findings
- Actual matching generator: scripts/build_index_and_sitemap.py, constants at lines 27–32, load_schedule_future_sessions at line 432, class index write at line 2119.
- Default input: docs/data/schedule_future.json.
- Conditional override: docs/data/canonical_schedule_from_class_report.json when build.source_mode equals class_report_authoritative. That file is absent locally.
- Intermediate source: data/sessions_current.json; scripts/build_schedule_future.py produces the public schedule.
- Repository rules identify Class Report.xlsx as a primary source, but this snapshot reports source_mode=enrollware_ical_authoritative. Do not assume the workbook fed this build.
- Source snapshot generated_at: 2026-10-01T20:53:36.191649-04:00. It is stale relative to the review date and must be refreshed/verified before publication.
- The similarly named scripts/build-classes-index.py is a separate aggregate builder, not the generator matching the inspected public class-finder layout.

## Work performed and exact changed files
- data/audit/atlas_class_entry_working_20261011.json: all 27 source sessions preserved, source IDs and fields retained, Atlas fields explicitly null, candidate booking URL separately labeled, inferred end times flagged. Eight rows start before 2026-10-11. No rows marked ready_for_atlas.
- Codex_Reply_AtlasSourceTrace_20261011.md: this receipt.
- A user-facing copy was persisted to C:/Users/ten77/Documents/Codex/2026-10-11/wh/outputs/atlas_class_entry_working_20261011.json.

## Validation
Read-only generator inspection and live HTML/script inspection identified embedded cards and filtering behavior.
PowerShell ConvertFrom-Json successfully parsed source and output.
Exact result: Validated JSON: 27 rows; 27 unique session IDs; past-date rows: 8
Output count equals source count; no duplicate session IDs.
No application code changed; no application tests needed. No site generator was run.

## Limits and next action
This is working data, not a verified Atlas CSV/import schema. AHA's September 2023 Create a Class guide documents form sections, not a proven bulk class upload path.
Inspect the user's current authenticated Atlas Create a Class page (or actual import template if offered), verify exact course/format/location/instructor options and enrollment settings, then map the source records. Do not guess pricing, capacity, language, card type, end-time duration, or dropdown IDs.
Official guide: https://cpr.heart.org/-/media/CPR2-Files/Private/Atlas-Info_Resources/9_21_2023/Job-Aid--Class-Management_Create-a-Class_updated-September-2023.pdf
No Atlas submission, production change, merge, or deployment occurred. Local data validation only. This is a one-time preparation artifact, not a monitored publishing system.

## Unrelated work preserved
Pre-existing modified files: docs/Earl/index.html; docs/Jackson/index.html; scripts/__pycache__/build_sessions_current.cpython-312.pyc; scripts/__pycache__/build_status.cpython-312.pyc; scripts/__pycache__/course_identity_resolver.cpython-312.pyc; scripts/__pycache__/local_data_paths.cpython-312.pyc.
Only the two explicit assignment files are staged. No cleanup or broad rebuild performed.
