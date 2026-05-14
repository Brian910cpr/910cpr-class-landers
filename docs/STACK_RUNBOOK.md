# 910CPR Stack Runbook

This runbook documents the current repository behavior in `E:\GitHub\910cpr-class-landers`.

The site is a static GitHub Pages site served from `docs/`. Build scripts generate JSON, HTML, sitemap, debug status files, and the internal Control Booth. There is no backend in the public site.

## Python Command

Most commands below use `python`. In the Codex desktop environment used for recent work, `python` was not on `PATH`; the bundled interpreter worked:

```powershell
C:\Users\ten77\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m scripts.build_slug_hubs
```

If `python` is available on your machine, use:

```powershell
python -m scripts.build_slug_hubs
```

Run commands from repo root:

```powershell
Set-Location E:\GitHub\910cpr-class-landers
```

## Quick Start

The local stack runner is:

```powershell
.\run_stack.bat
```

Current behavior:

1. Changes to `E:\GitHub\910cpr-class-landers`.
2. Runs `git pull`.
3. Rebuilds `sessions_current`, `schedule_future`, slug hubs, Control Booth, index/sitemap, optional metadata, and optional generated HTML stamps.
4. Prints `git status`.
5. Asks whether to start a local preview server.

If you answer `Y` to:

```text
Start local preview server and open test pages? (Y/N):
```

the BAT opens the Control Booth and main hub pages at `http://localhost:8000/`, then runs:

```powershell
python -m http.server 8000
```

The server runs until you press `CTRL+C` or close the command window.

## Full Stack Build Order

There is not currently one modern orchestrator that runs every current page builder in the exact desired full-stack order. The safe current full-stack order is:

1. Validate/refresh current sessions from source exports.
2. Build public future schedule JSON.
3. Build class landers.
4. Build course pages.
5. Build location pages.
6. Build course-at-city pages.
7. Build slug hubs.
8. Build request group session page.
9. Build index and sitemap.
10. Build Control Booth data.
11. Run verification/audits.

Commands:

```powershell
python -m scripts.build_sessions_current
python -m scripts.build_schedule_future
python -m scripts.build_landers
python -m scripts.build_course_landers
python -m scripts.build_courses
python -m scripts.build_locations
python -m scripts.build_course_at_city
python -m scripts.build_slug_hubs
python -m scripts.build_request_group_session
python -m scripts.build_index_and_sitemap
python -m scripts.build_control_booth
python -m scripts.verify_generated_stack
```

`scripts/prebuild_cleanup_validate.py` also exists and runs `build_sessions_current` and `build_schedule_future` after deleting JSON files from `docs/data`. Because `docs/data/site-emergency-settings.json` now lives in that directory, do not use this script until it is audited for the emergency settings file.

## Main Orchestrator Entry Points

### `build/build_all_v4.bat`

Batch entry point. Current behavior:

1. Checks for `data/course-export.xlsx` or `data/enrollware_export.xlsx`.
2. Checks for `data/Class Report.xlsx` or `data/class-report.xlsx`.
3. Optionally runs an external lander batch file if present:
   - `run_910cpr_landers.bat`
   - `run_rebuild.bat`
   - `run_landers_worker.bat`
4. Calls `build/build_all_v3.bat`.
5. Runs `python scripts\build_control_booth.py`.

Command:

```powershell
build\build_all_v4.bat
```

Optional:

```powershell
$env:SKIP_LANDERS='1'
build\build_all_v4.bat
```

### `scripts/build_all_v4.py`

Python wrapper around the same broad phases as `build_all_v4.bat`. Current behavior:

1. Checks input exports.
2. Optionally runs a detected lander command unless `--skip-landers` is passed.
3. Runs `.\build\build_all_v3.bat` by default.
4. Runs `scripts/build_control_booth.py`.
5. Writes build status through `scripts/build_status.py`.

Commands:

```powershell
python -m scripts.build_all_v4
python -m scripts.build_all_v4 --skip-landers
python -m scripts.build_all_v4 --lander-cmd ".\run_rebuild.bat"
```

### `build/build_all_v3.bat`

Legacy schedule/index pipeline. Current behavior:

1. Requires `data/course-export.xlsx`.
2. Requires `data/Class Report.xlsx`.
3. Runs `scripts/build_schedule_json.py`.
4. Runs `scripts/build_sessions_current.py`.
5. Runs `scripts/build_index.py`.
6. Runs `scripts/build_discovery.py`.

Command:

```powershell
build\build_all_v3.bat
```

Note: this is not the same as the modern `docs/data/schedule_future.json` plus slug hub pipeline.

## What Each Script Does

### Data Builders

`scripts/build_sessions_current.py`

- Reads `data/Class Report.xlsx`, `data/raw/classes_raw_live.csv`, `data/raw/students_raw_live.csv`, and `data/config/course_map.json`.
- Writes `data/sessions_current.json`.
- Writes audit files under `data/audit/`.
- Writes status files under `data/runtime/` and `debug/status/`.

Command:

```powershell
python -m scripts.build_sessions_current
```

`scripts/build_schedule_future.py`

- Reads `data/sessions_current.json`.
- Reconciles against `data/Class Report.xlsx`.
- Filters out past, orphan, and unmapped sessions unless flags say otherwise.
- Writes `docs/data/schedule_future.json`.

Command:

```powershell
python -m scripts.build_schedule_future
```

Useful options:

```powershell
python -m scripts.build_schedule_future --include-past
python -m scripts.build_schedule_future --fail-on-unmapped
```

`scripts/build_schedule_json.py`

- Legacy builder used by `build/build_all_v3.bat`.
- Reads course export and class report arguments.
- Writes configured output, usually `data/schedule.json`.

Command:

```powershell
python scripts\build_schedule_json.py --course-export data\course-export.xlsx --class-report "data\Class Report.xlsx" --output data\schedule.json
```

### Page Builders

`scripts/build_landers.py`

- Builds session/class landers under `docs/classes/`.
- Defaults to `docs/data/schedule_future.json`.
- Can use full dataset from `data/sessions_current.json`.

Commands:

```powershell
python -m scripts.build_landers
python -m scripts.build_landers --dataset full
python -m scripts.build_landers --resume-stamped
python -m scripts.build_landers --shard-index 0 --shard-count 4
```

`scripts/build_course_landers.py`

- Reads `docs/data/schedule_future.json`.
- Builds exact course pages under `docs/courses/`.
- Writes `docs/courses/index.json`.

Command:

```powershell
python -m scripts.build_course_landers
```

`scripts/build_courses.py`

- Reads `data/sessions_current.json`.
- Builds filtered course hub pages under `docs/courses/`.
- Purges stale output in `docs/courses/`.

Command:

```powershell
python -m scripts.build_courses
```

`scripts/build_locations.py`

- Reads `data/sessions_current.json`.
- Builds filtered location pages under `docs/locations/`.
- Purges stale output in `docs/locations/`.

Command:

```powershell
python -m scripts.build_locations
```

`scripts/build_course_at_city.py`

- Reads `data/sessions_current.json`.
- Builds course-at-city pages under `docs/course-at-city/`.
- Purges stale output in `docs/course-at-city/`.

Command:

```powershell
python -m scripts.build_course_at_city
```

`scripts/build_slug_hubs.py`

- Reads `data/config/slug_hubs.json` and `docs/data/schedule_future.json`.
- Also reads `data/sessions_current.json` for debug/reconciliation helpers.
- Builds:
  - `docs/bls.html`
  - `docs/acls.html`
  - `docs/pals.html`
  - `docs/heartsaver.html`
  - `docs/uscg-elementary-first-aid-cpr.html`
  - `docs/group.html`
- Writes ACLS and Heartsaver debug files under `data/runtime/`.

Command:

```powershell
python -m scripts.build_slug_hubs
```

`scripts/build_request_group_session.py`

- Builds `docs/group.html`.

Command:

```powershell
python -m scripts.build_request_group_session
```

`scripts/build_index_and_sitemap.py`

- Reads generated class pages from `docs/classes/`.
- Reads `docs/data/schedule_future.json`.
- Reads reviews from `data/raw/reviews/reviews.json`.
- Builds:
  - `docs/index.html`
  - `docs/classes/index.html`
  - `docs/courses/index.html`
  - generated course archive/support pages
  - generated location archive/support pages
  - `docs/sitemap.xml`

Command:

```powershell
python -m scripts.build_index_and_sitemap
```

`scripts/build_index.py` and `scripts/build_discovery.py`

- Legacy V3 builders.
- `build_index.py` reads a schedule JSON and writes index/topic/year pages.
- `build_discovery.py` reads `data/schedule.json` and writes `docs/schedule.html`.

Commands:

```powershell
python scripts\build_index.py --schedule-json data\schedule.json --output-dir docs
python scripts\build_discovery.py --schedule-json data\schedule.json --output-html docs\schedule.html
```

### Control And Verification

`scripts/build_control_booth.py`

- Reads build status files, filesystem counts, audit files, optional GA4 export, and `docs/data/site-emergency-settings.json`.
- Writes `debug/control_booth_data.json`.
- `debug/control-booth.html` is the static viewer.

Command:

```powershell
python -m scripts.build_control_booth
```

`scripts/verify_generated_stack.py`

- Verifies generated HTML stack against schedule data.
- Writes `debug/generated_stack_verification.json`.

Command:

```powershell
python -m scripts.verify_generated_stack
```

`scripts/check_schedule_integrity.py`

- Checks `docs/data/schedule_future.json` against `data/Class Report.xlsx`.

Command:

```powershell
python -m scripts.check_schedule_integrity
```

`scripts/audit_stale_sessions.py`

- Audits stale sessions not present in `data/Class Report.xlsx`.
- Can warn only or cleanup with quarantine behavior.

Commands:

```powershell
python -m scripts.audit_stale_sessions --warn-only
python -m scripts.audit_stale_sessions --cleanup
```

`scripts/audit_session_landers.py`

- Audits generated session landers.
- Writes `debug/session_lander_product_audit.json`.

Command:

```powershell
python -m scripts.audit_session_landers
```

## Required Inputs

Primary inputs:

- `data/Class Report.xlsx`
- `data/raw/classes_raw_live.csv`
- `data/raw/students_raw_live.csv`
- `data/config/course_map.json`
- `data/config/slug_hubs.json`
- `data/raw/reviews/reviews.json`

Legacy/alternate inputs:

- `data/course-export.xlsx`
- `data/enrollware_export.xlsx`
- `data/schedule.json`
- `docs/data/schedule.json`
- `docs/public_schedule.json`
- `docs/data/public_schedule.json`

Runtime settings input:

- `docs/data/site-emergency-settings.json`

## Generated Outputs

Public outputs:

- `docs/index.html`
- `docs/sitemap.xml`
- `docs/schedule.html`
- `docs/group.html`
- `docs/bls.html`
- `docs/acls.html`
- `docs/pals.html`
- `docs/heartsaver.html`
- `docs/uscg-elementary-first-aid-cpr.html`
- `docs/group.html`
- `docs/classes/*.html`
- `docs/courses/*.html`
- `docs/locations/*.html`
- `docs/course-at-city/*.html`
- `docs/data/schedule_future.json`

Internal/debug outputs:

- `data/sessions_current.json`
- `data/runtime/*.json`
- `debug/status/*.json`
- `debug/control_booth_data.json`
- `debug/generated_stack_verification.json`
- `debug/session_integrity_report.json`
- `debug/stale_sessions_audit.json`
- `data/audit/*.json`
- `data/audit/*.md`

## Runtime-Only Systems Vs Rebuild-Required Systems

Runtime-only after JSON/asset publish:

- Emergency settings: `docs/data/site-emergency-settings.json` read by `docs/assets/hub-ui.js`.
- Home schedule loading: `docs/assets/booking-home.js` fetches public schedule JSON, including `/data/schedule_future.json`.
- Hub UI pruning/grouping/tab behavior: `docs/assets/hub-ui.js`, `live-sessions.js`, `session-expiry.js`.
- Flexible inventory widget: `docs/assets/hybrid-inventory.js` reads markup payload and calls Enrollware appointment endpoint in browser.

Requires rebuild:

- Any generated HTML content in `docs/classes/`, `docs/courses/`, `docs/locations/`, `docs/course-at-city/`, and hub pages.
- `docs/data/schedule_future.json`.
- `docs/sitemap.xml`.
- `debug/control_booth_data.json`.
- Audit/status snapshots.

## Safe Rebuild Procedures

Before any rebuild:

```powershell
git status --short
```

Do not overwrite unrelated user changes. If generated files are dirty from another task, understand them before rebuilding.

Schedule refresh:

```powershell
python -m scripts.build_sessions_current
python -m scripts.build_schedule_future
```

Main generated pages:

```powershell
python -m scripts.build_landers
python -m scripts.build_course_landers
python -m scripts.build_courses
python -m scripts.build_locations
python -m scripts.build_course_at_city
python -m scripts.build_slug_hubs
python -m scripts.build_request_group_session
python -m scripts.build_index_and_sitemap
```

Control Booth and verification:

```powershell
python -m scripts.build_control_booth
python -m scripts.verify_generated_stack
```

## Partial Rebuild Procedures

Hub-only rebuild:

```powershell
python -m scripts.build_slug_hubs
```

Control Booth rebuild:

```powershell
python -m scripts.build_control_booth
```

Metadata/session JSON rebuild:

```powershell
python -m scripts.build_sessions_current
python -m scripts.build_schedule_future
```

Schedule JSON legacy rebuild:

```powershell
python scripts\build_schedule_json.py --course-export data\course-export.xlsx --class-report "data\Class Report.xlsx" --output data\schedule.json
```

Class lander rebuild:

```powershell
python -m scripts.build_landers
```

Course pages only:

```powershell
python -m scripts.build_course_landers
python -m scripts.build_courses
```

Locations only:

```powershell
python -m scripts.build_locations
python -m scripts.build_course_at_city
```

Index/sitemap only:

```powershell
python -m scripts.build_index_and_sitemap
```

Request group page only:

```powershell
python -m scripts.build_request_group_session
```

## Emergency Troubleshooting

### Live page still shows emergency banner or `Email Us To Register`

1. Confirm JSON is OFF:

```powershell
Get-Content docs\data\site-emergency-settings.json
```

2. Search generated hub HTML:

```powershell
rg -n "Email Us To Register|Our Schedule Platform Vendor|slug-emergency-alert|mailto:info@910cpr.com" docs\bls.html docs\acls.html docs\pals.html docs\heartsaver.html docs\uscg-elementary-first-aid-cpr.html docs\group.html
```

3. If generated HTML contains emergency markup, rebuild hubs:

```powershell
python -m scripts.build_slug_hubs
```

4. Verify runtime restoration exists in `docs/assets/hub-ui.js`.

5. Commit and push changed generated HTML/JS/JSON.

6. Check browser cache/CDN cache after GitHub Pages deploy.

### Missing sessions

Run:

```powershell
python -m scripts.build_sessions_current
python -m scripts.build_schedule_future
python -m scripts.check_schedule_integrity
```

Inspect:

- `data/audit/unmapped_courses.json`
- `debug/session_integrity_report.json`
- `debug/stale_sessions_audit.json`

### Control Booth stale

Run:

```powershell
python -m scripts.build_control_booth
```

Open:

- `debug/control-booth.html`
- `debug/control_booth_data.json`

## GitHub Pages Deployment Flow

The public site is static and served from `docs/`.

Typical flow:

```powershell
git status --short
git add docs data scripts build debug
git commit -m "Describe build/update"
git push
```

GitHub Pages then serves the committed `docs/` output. There is no server-side code to recompute JSON or HTML after deploy.

The repo includes `docs/CNAME`, so custom-domain behavior depends on GitHub Pages settings plus that file.

## Verification Checklist

After a schedule or hub rebuild:

```powershell
python -m scripts.verify_generated_stack
python -m scripts.check_schedule_integrity
python -m scripts.build_control_booth
```

Hub emergency checks:

```powershell
rg -n "Email Us To Register|Our Schedule Platform Vendor|slug-emergency-alert|mailto:info@910cpr.com" docs\bls.html docs\acls.html docs\pals.html docs\heartsaver.html docs\uscg-elementary-first-aid-cpr.html docs\group.html
```

Expected when emergency settings are OFF:

- No emergency banner in generated hub HTML.
- No `Email Us To Register` in generated hub HTML.
- No `mailto:info@910cpr.com` in generated hub HTML.
- Session buttons point to `https://coastalcprtraining.enrollware.com/enroll?id=...`.
- `data-original-href` remains present on hub session buttons.

Syntax checks:

```powershell
node --check docs\assets\hub-ui.js
python -m py_compile scripts\build_slug_hubs.py scripts\build_control_booth.py scripts\build_sessions_current.py scripts\build_schedule_future.py
```

## Common Failure Points

- `python` missing from `PATH`; use the bundled interpreter path or install/configure Python.
- Missing `data/Class Report.xlsx`.
- Missing `data/raw/classes_raw_live.csv`.
- Missing `data/raw/students_raw_live.csv`.
- Missing or stale `data/config/course_map.json`.
- Unmapped courses cause sessions to be skipped from `schedule_future.json`.
- `docs/data/schedule_future.json` can be stale if `build_schedule_future` is not run after source data changes.
- `build/build_all_v3.bat` expects `data/course-export.xlsx`, not just `data/enrollware_export.xlsx`.
- `scripts/build_all.py` references scripts that do not currently exist (`scripts/build_public_schedule.py`, `scripts/build_course_pages.py`, `scripts/build_class_landers.py`); do not use it as the current build entry point.
- `scripts/prebuild_cleanup_validate.py` deletes all `docs/data/*.json`; this can remove `docs/data/site-emergency-settings.json`.
- GitHub Pages and browsers can cache JSON/JS/HTML after deploy.

## What Should Never Be Manually Edited

Do not manually edit generated outputs unless the explicit goal is a temporary emergency patch:

- `docs/classes/*.html`
- `docs/courses/*.html`
- `docs/locations/*.html`
- `docs/course-at-city/*.html`
- generated hub pages under `docs/*.html` such as `bls.html`, `acls.html`, `pals.html`, `heartsaver.html`, `uscg-elementary-first-aid-cpr.html`, `group.html`
- `docs/index.html`
- `docs/sitemap.xml`
- `docs/data/schedule_future.json`
- `data/sessions_current.json`
- `data/runtime/*.json`
- `debug/status/*.json`
- `debug/control_booth_data.json`

Edit source/config instead:

- `data/Class Report.xlsx`
- `data/raw/classes_raw_live.csv`
- `data/raw/students_raw_live.csv`
- `data/config/course_map.json`
- `data/config/slug_hubs.json`
- builder scripts under `scripts/`
- runtime JS under `docs/assets/`
- emergency settings JSON under `docs/data/site-emergency-settings.json`

## Emergency Mode Operational Procedure

Emergency behavior is controlled by:

```text
docs/data/site-emergency-settings.json
```

Safe default:

```json
{
  "emergency": {
    "enabled": false,
    "outage_banner": { "enabled": false },
    "hub_email_fallback": { "enabled": false }
  }
}
```

Turn hub emergency fallback ON:

1. Edit `docs/data/site-emergency-settings.json`.
2. Set `emergency.enabled` to `true`.
3. Set `emergency.hub_email_fallback.enabled` to `true`.
4. Optionally set `emergency.outage_banner.enabled` to `true`.
5. Fill `updated_at`, `updated_by`, and `note`.
6. Commit and push the JSON.
7. Verify the live hub page after GitHub Pages deploy.

Turn emergency mode OFF:

1. Set `emergency.enabled` to `false`.
2. Set `emergency.outage_banner.enabled` to `false`.
3. Set `emergency.hub_email_fallback.enabled` to `false`.
4. Commit and push the JSON.
5. Verify hub buttons restore to Enrollware links.

Runtime rules:

- Missing/invalid/unavailable JSON fails closed.
- Emergency behavior requires both `emergency.enabled=true` and the specific feature flag.
- Hub email fallback is hub-session-only.
- `data-original-href` is preserved and used for restoration.
- Group training request buttons should not become emergency mailto buttons.

## Runtime Settings JSON Behavior

`docs/assets/hub-ui.js` fetches:

```text
/data/site-emergency-settings.json
```

It uses `cache: "no-store"` in the browser fetch. GitHub Pages/CDN/browser behavior can still delay visibility immediately after deploy.

When settings are OFF, runtime removes stale emergency hub banners and restores stale baked mailto buttons from `data-original-href`.

## Control Booth Generation/Update Behavior

Control Booth consists of:

- `debug/control-booth.html`
- `debug/control_booth_data.json`
- `scripts/build_control_booth.py`

`debug/control-booth.html` is a static browser viewer. It fetches `control_booth_data.json` with `cache: "no-store"`.

`scripts/build_control_booth.py` reads:

- `debug/status/*.json`
- `data/runtime/*.json`
- `data/sessions_current.json`
- `docs/data/schedule_future.json`
- `data/audit/*.json`
- `data/analytics/ga4_latest.csv` if present
- `docs/data/site-emergency-settings.json`

It writes:

- `debug/control_booth_data.json`

Command:

```powershell
python -m scripts.build_control_booth
```
