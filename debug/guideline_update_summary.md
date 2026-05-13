# Guideline Content Update Summary

Generated: 2026-05-12

## Audit Summary

- Local audit report: `debug/guideline_content_audit.json`
- Audit findings before patch: 50 local source/config content issues
- Primary issue areas: opioid/naloxone, CPR with breaths for respiratory arrest, stroke recognition, choking sequence, seizure response, asthma inhaler assistance, heat/cold illness, and practical first aid topic scope
- Source references used: the user-provided 2024 AHA/Red Cross First Aid and 2025 AHA CPR/ECC update requirements in this task

## Major Medical Guidance Updates Applied

- Added opioid emergency language covering EMS activation, naloxone accessibility, and why hands-only CPR is not always enough when breathing has stopped or is inadequate.
- Updated choking language to use 5 back blows plus 5 abdominal thrusts for adults and children, and 5 back blows plus 5 chest thrusts for infants.
- Strengthened stroke copy around FAST recognition, rapid EMS activation, and pediatric stroke awareness where appropriate.
- Updated seizure guidance to protect from injury, avoid restraint, put nothing in the mouth, and recognize when EMS should be activated.
- Added asthma assistance language for prescribed bronchodilators, spacer preference, and improvised spacer framing.
- Added heat and cold illness copy covering rapid cooling, ice water immersion preference for severe heat illness when available, and safer rewarming language.
- Expanded Heartsaver, ARC, HSI, and First Aid positioning around practical emergency recognition, ticks, stings, burns, eye injuries, poison ivy/oak, and pulse oximetry limitations.
- Added training philosophy language around hands-on practice, scenario-based refreshers, confidence building, and team communication.

## Templates And Source Data Changed

- `scripts/build_landers.py`
- `scripts/build_slug_hubs.py`
- `scripts/build_courses.py`
- `scripts/build_index_and_sitemap.py`
- `scripts/hub_utils.py`
- `data/config/slug_hubs.json`
- `data/config/course_map.json`
- `raw/course_archive_v4.json`

Backups of the modified source/config files were preserved under `debug/backups/guideline-update-20260512-230619/`.

## Rebuild Output

- Rebuilt future schedule and current schedule data.
- Rebuilt 1,351 class landers.
- Rebuilt public slug hubs for BLS, ACLS, PALS, Heartsaver, ARC, HSI, USCG, and group training.
- Rebuilt course pages, location pages, course-at-city pages, index pages, public schedule JSON, and sitemap.
- Preserved direct `enroll?id=` booking links and JSON-LD event schema generation.

## Validation Results

- Python compile: PASS for modified scripts and related classification/build modules.
- Node syntax: PASS for `docs/assets/hub-ui.js`, `docs/assets/live-sessions.js`, `docs/assets/session-expiry.js`, and `docs/assets/hybrid-inventory.js`.
- Static generated-page validation: PASS.
  - Report: `debug/guideline_validation_report.json`
  - Files checked: 22
  - Schema blocks parsed: 10
  - CTA pages with enroll links: 17
  - Issues: 0
- Localhost validation: PASS.
  - Report: `debug/guideline_localhost_report.json`
  - Pages checked: 8
  - Local asset/link URLs checked: 63
  - Failures: 0

## Unresolved / Manual Review

- `debug/stale_sessions_audit.json` still reports 9 stale HTML ids and 9 stale hub reference ids in warn-only mode. This appears separate from the guideline content update and was not changed in this pass.
- Pre-existing root `live-*` scratch files were not part of this update.
