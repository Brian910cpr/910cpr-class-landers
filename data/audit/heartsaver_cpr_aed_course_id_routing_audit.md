# Heartsaver CPR AED Course ID Routing Audit

## Course ID Rule

- Routine public AHA Heartsaver CPR AED in-person: `344085`.
- Routine public AHA Heartsaver CPR AED blended/online + skills: `209808`.
- Reserved Fire Department/public-safety partner course: `460465` only. This is the $0 partner-program path with optional $30 card fee for public participants; it must not be used for routine public classes.

## Summary

- Total `460465` references found in scan scope: 22
- Routine public routing/output `460465` references found: 0
- References replaced: 0
- References intentionally preserved: 22
- Heartsaver public offer IDs after rebuild: `209808, 209809, 251545, 329495, 344085, 351632`
- Heartsaver public output contains `460465`: `False`
- Invalid register URLs after rebuild: `0`
- Public selectable Heartsaver offers/dates/start times: `3014` / `39` / `512`

## Sample Generated URLs

- AHA Heartsaver CPR AED In-person (`344085`): https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=9%3A30%20AM&courseId=344085
- AHA Heartsaver CPR AED Blended (`209808`): https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260682&startTime=9%3A30%20AM&courseId=209808

## 460465 References Found

| File | Line | Classification | Action | Reason | Snippet |
|---|---:|---|---|---|---|
| `data/audit/heartsaver_block_schedule.json` | 106 | `preserved_policy_guard` | preserved | Intentional config/audit metadata note preventing routine public reuse of reserved partner course ID. | `"460465": "Reserved for Fire Department/public-safety partner programs only ($0 class with optional public participant card fee). Do not use for routine public Heartsaver CPR AED routing."` |
| `data/config/block_schedule_pages.json` | 291 | `preserved_policy_guard` | preserved | Intentional config/audit metadata note preventing routine public reuse of reserved partner course ID. | `"460465": "Reserved for Fire Department/public-safety partner programs only ($0 class with optional public participant card fee). Do not use for routine public Heartsaver CPR AED routing."` |
| `debug/apply_pilot_skips.json` | 135 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"course_type_id": "460465",` |
| `debug/apply_pilot_skips.json` | 140 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"edit_url": "https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465",` |
| `debug/apply_pilot_skips.json` | 148 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"course_type_id": "460465",` |
| `debug/apply_pilot_skips.json` | 153 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"edit_url": "https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465",` |
| `debug/apply_pilot_skips.json` | 434 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"course_type_id": "460465",` |
| `debug/apply_pilot_skips.json` | 439 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"edit_url": "https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465",` |
| `debug/enrollware_appointment_course_match_report.csv` | 12 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `AHA - Heartsaver® CPR AED - In-person,AHA - Heartsaver® CPR AED - In-person 🚒,460465,Heartsaver,$0.00,low,low-confidence normalized candidate score 1.00; skipped,https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465,no,not inspected` |
| `debug/enrollware_appointment_course_match_report.csv` | 13 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `AHA - Heartsaver® CPR AED - In-person 🚒,AHA - Heartsaver® CPR AED - In-person 🚒,460465,Heartsaver,$0.00,low,low-confidence normalized candidate score 1.00; skipped,https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465,no,not inspe...` |
| `debug/enrollware_appointment_course_match_report.csv` | 54 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `Heartsaver® TOTAL In-Person,AHA - Heartsaver® CPR AED - In-person 🚒,460465,Heartsaver,$0.00,low,low-confidence normalized candidate score 0.76; skipped,https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465,no,not inspected` |
| `debug/enrollware_course_list_clipboard.htmlfrag` | 16 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `" style="box-sizing: content-box; padding: 10px; text-align: center; line-height: 1.3em; font-weight: bold; border-bottom: 1px solid rgb(221, 221, 221); font-size: 15px; white-space: nowrap;">Action<span style="box-sizing: border-box;"></span></th></tr></th...` |
| `debug/enrollware_course_name_cleanup_apply_report.json` | 780 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"﻿course_type_id": "460465",` |
| `debug/enrollware_course_name_cleanup_apply_report.json` | 788 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"edit_url": "https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465",` |
| `debug/enrollware_course_name_cleanup_review_all.csv` | 51 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `460465,AHA - Heartsaver® CPR AED - In-person 🚒,AHA - Heartsaver® CPR AED - In-person 🚒,,,$0 placeholder/legacy/internal risk,low,skipped,https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465,$0 placeholder/legacy/internal risk` |
| `debug/enrollware_course_name_cleanup_skipped_review.csv` | 24 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `AHA - Heartsaver® CPR AED - In-person 🚒,low,,AHA - Heartsaver® CPR AED - In-person 🚒,,https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465,,$0 placeholder/legacy/internal risk,$0 placeholder/legacy/internal risk,skipped,460465` |
| `debug/enrollware_course_type_rows.json` | 548 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"edit_url": "https://www.enrollware.com/admin/course-edit.aspx?ret=course-list.aspx&id=460465",` |
| `debug/enrollware_course_type_rows.json` | 549 | `preserved_debug_reference` | preserved | Debug/admin snapshot or prior matching report; not public routing or generated site output. | `"course_type_id": "460465",` |
| `tests/test_block_start_time_selector.py` | 139 | `preserved_regression_guard` | preserved | Regression test asserts reserved partner course ID is excluded from public Heartsaver routing/output. | `self.assertNotIn("460465", configured_ids)` |
| `tests/test_block_start_time_selector.py` | 140 | `preserved_regression_guard` | preserved | Regression test asserts reserved partner course ID is excluded from public Heartsaver routing/output. | `self.assertIn("Fire Department/public-safety partner", heartsaver["course_id_notes"]["460465"])` |
| `tests/test_block_start_time_selector.py` | 146 | `preserved_regression_guard` | preserved | Regression test asserts reserved partner course ID is excluded from public Heartsaver routing/output. | `self.assertNotIn("460465", public_ids)` |
| `tests/test_block_start_time_selector.py` | 150 | `preserved_regression_guard` | preserved | Regression test asserts reserved partner course ID is excluded from public Heartsaver routing/output. | `self.assertNotIn("courseId=460465", html)` |

## Changed Files Intended For This Fix

- `data/config/block_schedule_pages.json`
- `data/audit/heartsaver_block_schedule.json`
- `data/audit/heartsaver_block_schedule_report.md`
- `docs/heartsaver-schedule.html`
- `tests/test_block_start_time_selector.py`
- `data/audit/heartsaver_cpr_aed_course_id_routing_audit.json`
- `data/audit/heartsaver_cpr_aed_course_id_routing_audit.md`
