# PII Containment Plan: Raw Live Enrollware Exports

Generated: 2026-06-20T11:07:16

Plan only. No files were deleted, moved, redacted, untracked, staged, committed, deployed, or published.

## 1. Current Tracking Status

| Path | Tracked now? | Size bytes | Risk note |
| --- | --- | ---: | --- |
| `data/raw/students_raw_live.csv` | True | 4870226 | Live student export; confirmed student/contact data risk. |
| `data/raw/classes_raw_live.csv` | True | 160177 | Live class export; likely operational schedule/class IDs, lower person-data risk than students export. |
| `data/Class Report.xlsx` | True | 23120 | Operational Class Report spreadsheet; authoritative local roster/session source used by build scripts. |
| `data/enrollware_export.xlsx` | True | 1511114 | Enrollware export spreadsheet used by sync/reconcile tooling. |
| `data/runtime/enrollware_sync/20260427-074805/desired_sessions.json` | true | 1918381 | Generated Enrollware sync runtime output; operational/reconciliation data. |
| `data/runtime/enrollware_sync/20260427-074805/sync_report.json` | true | 8417191 | Generated Enrollware sync runtime output; operational/reconciliation data. |
| `data/runtime/enrollware_sync/20260427-074805/sync_report.md` | true | 5522 | Generated Enrollware sync runtime output; operational/reconciliation data. |
| `data/runtime/enrollware_sync/playwright_scaffold_20260427-074844.json` | true | 364 | Generated Enrollware sync runtime output; operational/reconciliation data. |
| `data/runtime/enrollware_sync/reconciliation_20260427-074902.json` | true | 53820664 | Generated Enrollware sync runtime output; operational/reconciliation data. |
| `data/runtime/enrollware_sync/reconciliation_20260427-074950.json` | true | 9699900 | Generated Enrollware sync runtime output; operational/reconciliation data. |

## 2. PII / Operational Live Data Assessment

| Path group | Appears to contain PII or operational live data? | Rationale |
| --- | --- | --- |
| `data/raw/students_raw_live.csv` | Yes, highest risk | Student names, contact fields, registration/course data, and likely roster/payment-adjacent export fields. Do not print or commit new copies. |
| `data/raw/classes_raw_live.csv` | Operational live data, possible lower PII | Class/session export with class IDs, schedule data, locations, instructor/class metadata. May include live operational state. |
| `data/Class Report.xlsx` | Operational live data, possible roster/session PII depending columns | Current build source for sessions. Treat as local operational input, not source code. |
| `data/enrollware_export.xlsx` | Operational live data | Enrollware export for sync/reconcile. Treat as local operational input. |
| `data/runtime/enrollware_sync/**` | Operational generated data | Desired sessions, reconciliation, and sync reports can contain live IDs, class/session data, and possibly copied export fields. Generated runtime outputs should not be source-controlled. |

## 3. Script/Test/Build Dependencies

The following references were found. These are path references only; no full PII rows are included.

```text
docs\910cpr_lander_scheduler_punchlist.md:119:- `data/runtime/enrollware_sync/<timestamp>/`
docs\910cpr_lander_scheduler_punchlist.md:132:- `data/Class Report.xlsx`, `data/raw/classes_raw_live.csv`, `data/raw/students_raw_live.csv`, `data/sessions_current.json`, `docs/data/schedule_future.json`, Enrollware public schedule feeds, a
docs\control-center\control-center.js:208:  const classReport = await fileMeta("../../data/Class Report.xlsx");
docs\control-center\control-center.js:214:  addAction("classReport", classStatus, "Upload new Class Report", classAge === null ? "data/Class Report.xlsx is not readable from this page." : `Class Report age is ${classAge} days.`, "Upload the
docs\control-center\index.html:88:            <div class="fact"><span class="label">Current condition</span><span id="class-report-modified" class="value">Checking data/Class Report.xlsx</span></div>
docs\control-center\index.html:93:            <div class="fact"><span class="label">Where to fix</span><span class="value">data/Class Report.xlsx</span></div>
docs\first_successful_dynamic_booking_checklist.md:134:- Updated `Class Report.xlsx` includes the created class and roster details.
docs\enrollware_sync.md:16:  --master data\Class Report.xlsx `
docs\enrollware_sync.md:17:  --enrollware-export data\enrollware_export.xlsx `
docs\enrollware_sync.md:21:Outputs go to `data/runtime/enrollware_sync/<timestamp>/`:
docs\enrollware_sync.md:59:  --master data\Class Report.xlsx `
docs\enrollware_sync.md:88:  --enrollware-export E:\GitHub\910cpr-class-landers\data\enrollware_export.xlsx
docs\courses\acls.html:15:    <h1>ACLS</h1><p class='muted'>Live course hub built from Class Report.xlsx. Use this page to jump into actual upcoming sessions instead of a generic article.</p><table class='table-lite'><thead><tr><th>Date / T
docs\DATA_FLOW_MAP.md:4:- `data/Class Report.xlsx` (authoritative session list)
docs\DATA_FLOW_MAP.md:13:- Primary: `Registration Link` query param `id=...` in `Class Report.xlsx`
docs\DATA_FLOW_MAP.md:14:- Fallback: `ID` column in `Class Report.xlsx`
docs\DATA_FLOW_MAP.md:64:- `scripts/build_sessions_current.py` previously preferred `data/raw/Class Report.xlsx` over `data/Class Report.xlsx` (fixed).
docs\courses\aha-family-friends-cpr.html:15:    <h1>AHA - Family & FriendsÂ® CPR</h1><p class='muted'>Live course hub built from Class Report.xlsx. Use this page to jump into actual upcoming sessions instead of a generic article.</p><p clas
docs\control-center\modules\diagnostics.html:26:          <div class="list-item"><span>data/Class Report.xlsx</span><span>Enrollware source export</span></div>
scripts\build_courses.py:42:                "<p class='muted'>Live course hub built from Class Report.xlsx. Use this page to jump into actual upcoming sessions instead of a generic article.</p>",
docs\control-center\modules\lander-builder.html:33:          <div class="fact"><span class="label">Source file</span><span class="value">data/Class Report.xlsx</span></div>
docs\data\schedule_future.json:18:    "class_report": "E:\\GitHub\\910cpr-class-landers\\data\\Class Report.xlsx"
scripts\build_appointment_offer_inventory.py:37:CLASS_REPORT_PATH = ROOT / "data" / "Class Report.xlsx"
scripts\build_appointment_offer_inventory.py:385:    if source_file.endswith("Class Report.xlsx"):
scripts\build_all_v4.py:52:    course_candidates = ["course-export.xlsx", "enrollware_export.xlsx"]
scripts\build_all_v4.py:53:    class_candidates = ["Class Report.xlsx", "class-report.xlsx"]
scripts\audit_stale_sessions.py:52:        repo_root / "data" / "Class Report.xlsx",
scripts\audit_stale_sessions.py:53:        repo_root / "data" / "raw" / "Class Report.xlsx",
scripts\audit_stale_sessions.py:339:    parser = argparse.ArgumentParser(description="Audit and quarantine stale sessions not present in Class Report.xlsx")
scripts\audit_stale_sessions.py:341:    parser.add_argument("--class-report", default="data/Class Report.xlsx")
scripts\audit_stale_sessions.py:396:            "stale_hub_ref_ids": "Hard failure: public hubs or sitemap reference session IDs absent from Class Report.xlsx.",
scripts\audit_stale_sessions.py:397:            "stale_html_ids": "Hard failure only when obsolete HTML files remain for session IDs absent from Class Report.xlsx; --cleanup quarantines them.",
scripts\audit_stale_sessions.py:398:            "retained_past_page_ids": "Class pages present in Class Report.xlsx but absent from schedule_future.json are retained past/non-public pages and are not failures unless publicly referenced.",
docs\courses\bls.html:15:    <h1>BLS</h1><p class='muted'>Live course hub built from Class Report.xlsx. Use this page to jump into actual upcoming sessions instead of a generic article.</p><table class='table-lite'><thead><tr><th>Date / Tim
docs\courses\heartsaver-first-aid-cpr-aed.html:15:    <h1>Heartsaver / First Aid / CPR / AED</h1><p class='muted'>Live course hub built from Class Report.xlsx. Use this page to jump into actual upcoming sessions instead of a generic article
docs\courses\pals.html:15:    <h1>PALS</h1><p class='muted'>Live course hub built from Class Report.xlsx. Use this page to jump into actual upcoming sessions instead of a generic article.</p><table class='table-lite'><thead><tr><th>Date / T
docs\STACK_RUNBOOK.md:98:1. Checks for `data/course-export.xlsx` or `data/enrollware_export.xlsx`.
docs\STACK_RUNBOOK.md:99:2. Checks for `data/Class Report.xlsx` or `data/class-report.xlsx`.
docs\STACK_RUNBOOK.md:143:2. Requires `data/Class Report.xlsx`.
docs\STACK_RUNBOOK.md:163:- Reads `data/Class Report.xlsx`, `data/raw/classes_raw_live.csv`, `data/raw/students_raw_live.csv`, and `data/config/course_map.json`.
docs\STACK_RUNBOOK.md:177:- Reconciles against `data/Class Report.xlsx`.
docs\STACK_RUNBOOK.md:203:python scripts\build_schedule_json.py --course-export data\course-export.xlsx --class-report "data\Class Report.xlsx" --output data\schedule.json
docs\STACK_RUNBOOK.md:359:- Checks `docs/data/schedule_future.json` against `data/Class Report.xlsx`.
docs\STACK_RUNBOOK.md:369:- Audits stale sessions not present in `data/Class Report.xlsx`.
docs\STACK_RUNBOOK.md:394:- `data/Class Report.xlsx`
docs\STACK_RUNBOOK.md:395:- `data/raw/classes_raw_live.csv`
docs\STACK_RUNBOOK.md:396:- `data/raw/students_raw_live.csv`
docs\STACK_RUNBOOK.md:404:- `data/enrollware_export.xlsx`
docs\STACK_RUNBOOK.md:524:python scripts\build_schedule_json.py --course-export data\course-export.xlsx --class-report "data\Class Report.xlsx" --output data\schedule.json
docs\STACK_RUNBOOK.md:667:- Missing `data/Class Report.xlsx`.
docs\STACK_RUNBOOK.md:668:- Missing `data/raw/classes_raw_live.csv`.
docs\STACK_RUNBOOK.md:669:- Missing `data/raw/students_raw_live.csv`.
docs\STACK_RUNBOOK.md:673:- `build/build_all_v3.bat` expects `data/course-export.xlsx`, not just `data/enrollware_export.xlsx`.
docs\STACK_RUNBOOK.md:697:- `data/Class Report.xlsx`
docs\STACK_RUNBOOK.md:698:- `data/raw/classes_raw_live.csv`
docs\STACK_RUNBOOK.md:699:- `data/raw/students_raw_live.csv`
docs\STACK_ARCHITECTURE.md:11:  A["data/Class Report.xlsx"] --> B["scripts/build_sessions_current.py"]
docs\STACK_ARCHITECTURE.md:12:  C["data/raw/classes_raw_live.csv"] --> B
docs\STACK_ARCHITECTURE.md:13:  D["data/raw/students_raw_live.csv"] --> B
docs\STACK_ARCHITECTURE.md:39:- `data/Class Report.xlsx`: authoritative session list.
docs\STACK_ARCHITECTURE.md:40:- `data/raw/classes_raw_live.csv`: live class export used to patch/enrich sessions.
docs\STACK_ARCHITECTURE.md:41:- `data/raw/students_raw_live.csv`: live student/export data used for enrollment counts.
docs\STACK_ARCHITECTURE.md:49:- `data/enrollware_export.xlsx`
docs\STACK_ARCHITECTURE.md:123:  A["Class Report.xlsx"] --> B["sessions_current"]
docs\STACK_ARCHITECTURE.md:124:  C["classes_raw_live.csv"] --> B
docs\STACK_ARCHITECTURE.md:125:  D["students_raw_live.csv"] --> B
scripts\build_schedule_future.py:155:        repo_root / "data" / "Class Report.xlsx",
scripts\build_schedule_future.py:156:        repo_root / "data" / "raw" / "Class Report.xlsx",
scripts\build_schedule_future.py:292:        default="data/Class Report.xlsx",
scripts\build_schedule_future.py:293:        help="Relative path from repo root to Class Report.xlsx used for hard reconciliation",
scripts\check_schedule_integrity.py:18:        repo_root / "data" / "Class Report.xlsx",
scripts\check_schedule_integrity.py:19:        repo_root / "data" / "raw" / "Class Report.xlsx",
scripts\build_sessions_current.py:49:        repo_root / "data" / "Class Report.xlsx",
scripts\build_sessions_current.py:50:        repo_root / "data" / "raw" / "Class Report.xlsx",
scripts\build_sessions_current.py:643:    parser.add_argument("--class-report", default="data/Class Report.xlsx")
scripts\build_sessions_current.py:644:    parser.add_argument("--classes-csv", default="data/raw/classes_raw_live.csv")
scripts\build_sessions_current.py:645:    parser.add_argument("--students-csv", default="data/raw/students_raw_live.csv")
scripts\enrollware_sync.py:39:DEFAULT_OUTPUT_DIR = Path("data/runtime/enrollware_sync")
scripts\enrollware_sync.py:40:DEFAULT_MASTER_PATH = Path("data/Class Report.xlsx")
scripts\enrollware_sync.py:41:DEFAULT_EXPORT_PATH = Path("data/enrollware_export.xlsx")
scripts\enrollware_sync.py:884:    dry.add_argument("--master", default=str(DEFAULT_MASTER_PATH), help="Master schedule CSV/XLSX path relative to repo root.")
scripts\enrollware_sync.py:885:    dry.add_argument("--enrollware-export", default=str(DEFAULT_EXPORT_PATH), help="Enrollware export CSV/XLSX path relative to repo root.")
scripts\enrollware_sync.py:887:    dry.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for desired sessions and reports.")
scripts\enrollware_sync.py:893:    scaffold.add_argument("--master", default=str(DEFAULT_MASTER_PATH), help="Master schedule path used for the dry run.")
scripts\enrollware_sync.py:900:    scaffold.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for scaffold logs.")
scripts\enrollware_sync.py:906:    reconcile_parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for reconciliation reports.")
scripts\hub_utils.py:12:RAW_REPORT = ROOT / "data" / "Class Report.xlsx"
scripts\prebuild_cleanup_validate.py:23:        repo_root / "data" / "Class Report.xlsx",
scripts\prebuild_cleanup_validate.py:24:        repo_root / "data" / "raw" / "Class Report.xlsx",
scripts\prebuild_cleanup_validate.py:109:    parser.add_argument("--class-report", default="data/Class Report.xlsx")
```

Likely breakage if files are removed from tracking without replacement/local setup:
- `scripts/build_sessions_current.py` defaults to `data/Class Report.xlsx`, `data/raw/classes_raw_live.csv`, and `data/raw/students_raw_live.csv`.
- `scripts/build_schedule_future.py`, `scripts/check_schedule_integrity.py`, `scripts/prebuild_cleanup_validate.py`, and related hub builders expect `data/Class Report.xlsx` or `data/raw/Class Report.xlsx`.
- `scripts/enrollware_sync.py` defaults to `data/Class Report.xlsx`, `data/enrollware_export.xlsx`, and writes `data/runtime/enrollware_sync`.
- Existing docs/runbooks mention the current live file names. Those docs may need to be updated after the approved cleanup. Public pages should not be changed in this planning step.

## 4. Recommended Disposition By File

| Path | Recommendation | Reason |
| --- | --- | --- |
| `data/raw/students_raw_live.csv` | Remove from tracking and add to `.gitignore`; keep local-only private copy; optionally replace with sanitized fixture | Highest-risk student/contact export. Scripts need the data locally, but git does not. |
| `data/raw/classes_raw_live.csv` | Remove from tracking and add to `.gitignore`; keep local-only private copy; optionally replace with sanitized fixture | Live class export is operational data. Use synthetic fixture for tests/docs if needed. |
| `data/Class Report.xlsx` | Move to local-only private path or keep local with `.gitignore`; add README/placeholder documenting required local file | Operational spreadsheet required by build pipeline. Should be supplied locally, not tracked. |
| `data/enrollware_export.xlsx` | Remove from tracking and add to `.gitignore`; keep local-only private copy | Sync/reconcile input export. Should be local operational data. |
| `data/runtime/enrollware_sync/**` | Remove from tracking and add to `.gitignore` | Generated runtime output. Rebuildable and potentially sensitive. |

## 5. Exact Proposed Git Actions (Do Not Run Yet)

These are proposed for a later approved cleanup task only:

```powershell
# Stop tracking live/raw operational exports while preserving local files
git rm --cached -- data/raw/students_raw_live.csv
git rm --cached -- data/raw/classes_raw_live.csv
git rm --cached -- "data/Class Report.xlsx"
git rm --cached -- data/enrollware_export.xlsx
git rm --cached -r -- data/runtime/enrollware_sync

# Add/update ignore rules in .gitignore
# Then add sanitized fixtures/placeholders as separately reviewed files
git add .gitignore data/raw/README.md data/fixtures/README.md

# Run tests/build checks that do not require private files, plus a local-private-file smoke test if needed
python -m unittest discover tests
```

History cleanup is a separate decision. Removing files from tracking prevents future commits but does not remove past blobs from git history.

## 6. Suggested `.gitignore` Additions

```gitignore
# Live/raw Enrollware and student exports - local operational data only
data/raw/students_raw_live.csv
data/raw/classes_raw_live.csv
data/raw/*_raw_live.csv
data/Class Report.xlsx
data/class-report.xlsx
data/enrollware_export.xlsx
data/*enrollware*export*.xlsx
data/runtime/enrollware_sync/

# Local operational spreadsheets
data/*.local.xlsx
data/private/
```

## 7. Suggested Sanitized Fixture Names

- `data/fixtures/classes_raw_live.synthetic.csv`
- `data/fixtures/students_raw_live.synthetic.csv`
- `data/fixtures/class_report.synthetic.xlsx` or preferably `.csv`/`.json` if tests can avoid XLSX
- `data/fixtures/enrollware_export.synthetic.xlsx` or preferably `.csv`/`.json` if tests can avoid XLSX
- `data/fixtures/enrollware_sync/desired_sessions.synthetic.json`
- `data/fixtures/enrollware_sync/reconciliation.synthetic.json`

Synthetic fixtures should use fake names, `example.test` emails, `555-0100` phone numbers, fake addresses, fake registration IDs, and fake course schedule IDs unless the ID is a public course/session ID already intentionally published.

## 8. README / Placeholder Strategy

Recommended local-only placeholder approach:
- Add `data/raw/README.md` explaining that live exports are required locally and intentionally ignored.
- Add `data/private/README.md` for private operational inputs, if using `data/private/` as the long-term home.
- Update runbooks to say: copy current Enrollware exports into local ignored paths before running local builds.
- Avoid publishing private file names or real row examples in public `docs/`; internal docs can describe paths without PII rows.

## 9. Public `docs/classes/*.html` Flags

The PII audit flagged many `docs/classes/*.html` files because they contain public Enrollware session IDs, registration links, public business/location schema, and generic registration wording. Based on the patterns reviewed, these look mostly like public class-page false positives rather than student PII.

Caveat: public output should still be periodically scanned for actual student names, personal emails, phone numbers, home addresses, payment/balance fields, comments/questions, or raw rows. The known Zapier bridge PII strings were not found in public docs after containment.

## 10. Recommended Next Step

Approve a narrow cleanup task to stop tracking `data/raw/students_raw_live.csv` first, add ignore coverage, and add a sanitized fixture or README placeholder so scripts/tests remain understandable. Then repeat for `classes_raw_live.csv`, `Class Report.xlsx`, `enrollware_export.xlsx`, and `data/runtime/enrollware_sync/**`.
