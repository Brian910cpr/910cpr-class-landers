# PII Worktree Audit Report

Generated: 2026-06-20T11:03:30

Report-only audit. No files were deleted, moved, redacted, staged, committed, deployed, or published.

## 1. Summary

- Tracked files scanned: 53968
- Current modified/untracked paths from `git status --short`: 150
- Ignored paths currently present: 11
- Tracked likely PII/operational candidates: 52468
- Worktree likely PII/operational candidates: 65
- Public docs/output PII-risk candidates: 428
- Sensitive-looking staged files: 0
- `data/raw/students_raw_live.csv` tracked: True

Highest-risk finding: `data/raw/students_raw_live.csv` is tracked and appears to contain student/contact/registration export data. This predates the Zapier bridge commit.

## 2. Tracked Files With Likely PII

| Path | Score | Signals | Redacted examples |
| --- | ---: | --- | --- |
| `data/raw/students_raw_live.csv` | 30 | operational/export-like filename; raw/runtime data path; emails:8204; phones:6877; addresses:5691; payment_terms:48; comment_employer_terms:154 | Reg. Date,Last Name,First Name,Email,License #,Mailing Address1,Mailing Address2,Mailing City,Mailing State,Mailing Zip,Phone,Alt Phone,Billing Address1,Billing Address2,Billing City,Billing State,Billing Zip,Course,Class ID,Course Date,Cou<br>12/13/19 11:32,McCorkle,John,j***@earthlink.net,,1204 Columbus Circle #B,,Wilmington,NC,28403,,,,,,,,"AHA - BLS Provider - In-person Initial<img src=""https://www.enrollware.com/sitefiles/coastalcprtraining/a-l.png"" style=""width:75px;vert<br>12/13/19 11:33,Reeves,Jennifer,j***@gmail.com,,1*** Chestnut St,,Wilmington,NC,28405,,,,,,,,"AHA - BLS Provider - In-person Initial<img src=""https://www.enrollware.com/sitefiles/coastalcprtraining/a-l.png"" style=""width:75px;vertical-alig |
| `tests/test_import_enrollware_registration_events.py` | 24 | operational/export-like filename; emails:13; addresses:2; registration_terms:15; payment_terms:10; comment_employer_terms:11 | "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"regId,courseId,courseSchedId,courseName,locationName,startTime,instructor,student,email,status,balanceDue\n"<br>'90000001,209806,99000001,AHA BLS Provider (Initial),"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR\'s Office",2026-06-21 17:00:00,Brian Ennis,Test Student,s***@example.test,Pending,75\n' |
| `data/runtime/enrollware_sync/reconciliation_20260427-074902.json` | 17 | raw/runtime data path; addresses:2427; payment_terms:6460; comment_employer_terms:38 | "session_key": "aha bls provider online class with in person skill session initial or renewal blended learning heartcode bls|2020-07-01T09:00:00-04:00|2020-07-01T10:00:00-04:00|wm 1*** jacksonville marine blvd",<br>"session_key": "aha bls provider online class with in person skill session initial or renewal blended learning heartcode bls|2020-07-01T09:00:00-04:00|2020-07-01T10:00:00-04:00|wm 1*** jacksonville marine blvd",<br>"session_key": "aha bls provider in person initial|2020-07-01T09:30:00-04:00|2020-07-01T12:30:00-04:00|wm 1*** jacksonville marine blvd", |
| `raw/course_archive_v3.json` | 17 | operational/export-like filename; phones:4; payment_terms:25; comment_employer_terms:7 | "original_html": "<!-- Header -->\n<div style=\"text-align: center; background-color: #3a5289; color: white; padding: 10px; font-weight: bold !important;\">AHA BLS Provider &ndash; In-Person &ndash; Renewal</div>\n<p style=\"text-indent: 0p<br>"raw_enrollware_html": "<!-- Header -->\n<div style=\"text-align: center; background-color: #3a5289; color: white; padding: 10px; font-weight: bold !important;\">AHA BLS Provider &ndash; In-Person &ndash; Renewal</div>\n<p style=\"text-inde<br>"raw_html_sha256": "3e30d177513af6bffefe9c89b393ec1acd7589c***-***-8782fcfcea59581f1ae" |
| `scripts/import_enrollware_registration_events.py` | 17 | operational/export-like filename; registration_terms:46; payment_terms:16; comment_employer_terms:28 | "regId": ["regId", "reg_id", "Registration ID", "RegistrationId", "Registration Id", "Reg ID", "RegId"],<br>"courseSchedId": [<br>"courseSchedId", |
| `data/raw/classes_raw_live.csv` | 16 | operational/export-like filename; raw/runtime data path; emails:1; phones:173; addresses:160 | 10809812,UPDATE,AHA - Heartsaver® - Become an American Heart Association Instructor  ,265876,https://coastalcprtraining.enrollware.com/enroll?id=10809812,Brighter Start Health,101560,NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office,$35<br>9947974,UPDATE,AHA - Heartsaver® CPR AED (No First Aid)- <b>In-person</b> ,344085,https://coastalcprtraining.enrollware.com/enroll?id=9947974,,101560,NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office,$70.00,1,5,,,"New  24057895173    ""<br>9947974,UPDATE,AHA - Heartsaver® CPR AED (No First Aid)- <b>In-person</b> ,344085,https://coastalcprtraining.enrollware.com/enroll?id=9947974,,101560,NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office,$70.00,1,5,,,"New  24057895173    "" |
| `debug/approved_name_apply_html/374378.after.htmlfrag` | 15 | phones:8; payment_terms:20; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-3024<br>StartFragment:***-***-0233 |
| `debug/edit_pages/371954.htmlfrag` | 15 | phones:8; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-0661<br>StartFragment:***-***-0233 |
| `debug/edit_pages/393791.htmlfrag` | 15 | phones:5; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-1626<br>StartFragment:***-***-0233 |
| `thread.txt` | 15 | emails:28; payment_terms:412; comment_employer_terms:174 | • Indicate that you already have access to a manual (via employer, previous course, or personal copy)<br><br>MANUAL: OTHER SOURCE - <br><br><br><div style="font-size: 14px; line-height: 1.5;"> <strong>Manual: Other Source</strong> <img src="https://www.enrollware.com/sitefiles/coastalcprtraining/Class_Images/THUP.png" width="75" style="float:right<br>Card Type: |
| `debug/apply_html/209808.after.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2805<br>StartFragment:***-***-0233 |
| `debug/apply_html/209808.before.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2805<br>StartFragment:***-***-0233 |
| `debug/apply_html/209811.before.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:22 | StartHTML:***-***-0197<br>EndHTML:***-***-9687<br>StartFragment:***-***-0233 |
| `debug/apply_html/351632.after.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-4779<br>StartFragment:***-***-0233 |
| `debug/apply_html/351632.before.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-4779<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209805.after.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-9913<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209805.before.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-9913<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209806.after.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-4425<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209806.before.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-4425<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209808.after.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2743<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209808.before.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2743<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209809.after.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-7749<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209809.before.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-7749<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209811.after.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:22 | StartHTML:***-***-0197<br>EndHTML:***-***-9450<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209811.before.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:22 | StartHTML:***-***-0197<br>EndHTML:***-***-9450<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209812.after.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-9296<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209812.before.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-9296<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209818.after.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-8561<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/209818.before.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-8561<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/210549.after.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-1105<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/210549.before.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-1105<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/241108.after.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-8524<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/241108.before.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-8524<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/248287.after.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2724<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/248287.before.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2724<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/248288.after.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-4019<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/248288.before.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-4019<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/251496.after.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-8479<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/251496.before.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-8479<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/251545.after.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-6133<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/251545.before.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-6133<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/252734.after.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-2713<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/252734.before.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-2713<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/329495.after.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-5080<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/329495.before.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-5080<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/344085.after.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-2678<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/344085.before.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-2678<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/351632.after.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-4923<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/351632.before.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-4923<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/359474.after.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-1418<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/359474.before.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-1418<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/369209.after.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-0435<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/369209.before.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-0435<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/371954.after.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-0795<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/371954.before.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-0795<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/374378.before.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-3024<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/380688.after.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-3843<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/380688.before.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-3843<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/410694.after.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-8839<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/410694.before.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-8839<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/422270.after.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-4827<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/422270.before.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-4827<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/440431.after.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-5970<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/440431.before.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-5970<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/444919.after.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2496<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/444919.before.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2496<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/445670.after.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-3758<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/445670.before.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-3758<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/448630.after.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2822<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/448630.before.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2822<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/449422.after.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-9797<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/449422.before.htmlfrag` | 14 | phones:4; payment_terms:18; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-9797<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/463743.after.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2957<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/463743.before.htmlfrag` | 14 | phones:4; payment_terms:17; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-2957<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/485317.after.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-6092<br>StartFragment:***-***-0233 |
| `debug/approved_name_apply_html/485317.before.htmlfrag` | 14 | phones:4; payment_terms:19; comment_employer_terms:20 | StartHTML:***-***-0197<br>EndHTML:***-***-6092<br>StartFragment:***-***-0233 |
| `debug/backups/guideline-update-20260512-230619/course_archive_v4.json` | 14 | phones:4; payment_terms:25; comment_employer_terms:7 | "original_html": "<!-- Header -->\n<div style=\"text-align: center; background-color: #3a5289; color: white; padding: 10px; font-weight: bold !important;\">AHA BLS Provider &ndash; In-Person &ndash; Renewal</div>\n<p style=\"text-indent: 0p<br>"raw_enrollware_html": "<!-- Header -->\n<div style=\"text-align: center; background-color: #3a5289; color: white; padding: 10px; font-weight: bold !important;\">AHA BLS Provider &ndash; In-Person &ndash; Renewal</div>\n<p style=\"text-inde<br>"raw_html_sha256": "3e30d177513af6bffefe9c89b393ec1acd7589c***-***-8782fcfcea59581f1ae", |
| `debug/course_name_cleanup_html/209805.after.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-9769<br>StartFragment:***-***-0233 |
| `debug/course_name_cleanup_html/209805.before.htmlfrag` | 14 | phones:4; payment_terms:21; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-9769<br>StartFragment:***-***-0233 |
| `debug/course_name_cleanup_html/209806.after.htmlfrag` | 14 | phones:4; payment_terms:20; comment_employer_terms:21 | StartHTML:***-***-0197<br>EndHTML:***-***-4262<br>StartFragment:***-***-0233 |

_Additional rows omitted from report table: 52388._

## 3. Untracked/Ignored Files With Likely PII Or Operational Data

| Path | Tracked? | Score | Signals | Redacted examples |
| --- | --- | ---: | --- | --- |
| `data/audit/zapier_registration_rich_event_review_bundle.md` | False | 32 | operational/export-like filename; audit output path; emails:7; phones:8; addresses:4; registration_terms:47; payment_terms:41; comment_employer_terms:31 | 6. Lander stores `courseSchedId` as the real Enrollware class/session ID associated with that seed.<br>- `regId`: `27966030`<br>- `courseSchedId`: `13657403` |
| `data/audit/appointment_seed_registration_matches.json` | False | 30 | operational/export-like filename; audit output path; emails:15; phones:12; addresses:2; registration_terms:42; payment_terms:39; comment_employer_terms:26 | "regId": "27966030",<br>"courseSchedId": "13657403",<br>"regId": "27966030", |
| `data/audit/enrollware_registration_events_normalized.json` | False | 30 | operational/export-like filename; audit output path; emails:18; phones:14; addresses:2; registration_terms:44; payment_terms:46; comment_employer_terms:30 | "regId": "27966030",<br>"courseSchedId": "13657403",<br>"locationName": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office", |
| `data/fixtures/enrollware_registration_real_shape_test_rows.csv` | False | 27 | operational/export-like filename; emails:6; phones:7; addresses:1; registration_terms:5; payment_terms:7; comment_employer_terms:4 | Zap ID,Zap Meta Timestamp,Registration Id,Course Id,Course Sched ID,Course Name,Discipline,Location Name,Class Start Time,Instructor Name,First Name,Last Name,Email Address,Phone Number,Alternate Phone Number,Address 1,Address 2,City,State,<br>zap-001,2026-06-20T10:30:00-04:00,27966030,209806,13657403,AHA BLS Provider (Initial),AHA BLS,"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",2026-06-21 17:00:00,Brian Ennis,Brian,AAADelete,t***@gmail.com,***-***-0100,***-**<br>zap-002,2026-06-20T10:31:00-04:00,,209806,13657404,AHA BLS Provider (Initial),AHA BLS,"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",2026-06-21 17:00:00,Brian Ennis,Missing,RegId,m***@example.com,***-***-0101,,,,,,,,,,Pendi |
| `data/schedule.json` | False | 25 | emails:6655; phones:23; addresses:498; payment_terms:21429; comment_employer_terms:11752 | "description": "<!-- META:\n{\n  \"course_id\": 209806,\n  \"meta_key\": \"AHA_BLS_INPERSON_INITIAL\",\n  \"course_type\": \"BLS_INPERSON_INITIAL\",\n  \"certifying_body\": \"AHA\",\n  \"delivery\": \"in_person\",\n  \"family\": \"BLS\",\n <br>"description": "AHA BLS Provider \u2013 In-Person \u2013 Renewal\n\n\n\nThis American Heart Association (AHA) Basic Life Support (BLS) Renewal course is designed for healthcare professionals with a current, valid AHA BLS Provider card who a<br>"description": "AHA - BLS Provider \u2013 En persona (SVB para Profesionales de la Salud)\n\nEl curso de Soporte Vital B\u00e1sico (SVB/BLS) de la American Heart Association (AHA) est\u00e1 dise\u00f1ado para profesionales de la salud que n |
| `data/audit/enrollware_zapier_registration_event_bridge.md` | False | 19 | operational/export-like filename; audit output path; emails:1; registration_terms:11; payment_terms:7; comment_employer_terms:5 | 6. Lander stores `courseSchedId` as the real Enrollware class/session ID associated with that seed.<br>- `regId`: `27966030`<br>- `courseSchedId`: `13657403` |
| `data/audit/enrollware_registration_event_import_summary.json` | False | 18 | operational/export-like filename; audit output path; registration_terms:8; payment_terms:12; comment_employer_terms:6 | "Registration Id",<br>"Course Sched ID",<br>"Class Price Code", |
| `data/audit/live_availability_snapshot_preview.json` | False | 18 | operational/export-like filename; audit output path; emails:19; phones:7; addresses:10 | "person_id": "instructor_***-***-1442",<br>"person_id": "instructor_***-***-1442",<br>"location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", |
| `data/audit/dynamic_offers_preview.json` | False | 16 | audit output path; emails:881; phones:738; addresses:256 | "offer_id": "offer-209811-instructor_***-***-1442-20260623-1800",<br>"instructor_person_id": "instructor_***-***-1442",<br>"location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", |
| `data/audit/public_sellable_offers_preview.json` | False | 16 | audit output path; emails:640; phones:600; addresses:256 | "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"offer_location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"source_location": "4*** Windchime Dr\\, Wilmington\\, NC 28412\\, USA", |
| `data/audit/schedule_seeds_preview.json` | False | 15 | audit output path; emails:131; phones:48; addresses:4 | "source_offer_id": "offer-209811-instructor_***-***-1442-20260623-1800",<br>"location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"resource": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", |
| `data/audit/people_assignment_policy_review.csv` | False | 13 | operational/export-like filename; audit output path; emails:79; phones:17 | instructor_24057895173,Brian Ennis,b***@910cpr.com,AHA_HEARTSAVER_INSTRUCTOR; AHA_BLS_INSTRUCTOR,PRIMARY,inverse_google_calendar,primary,True,NEEDS_REVIEW,Prefill: Brian is the owner/primary availability bridge candidate. Review before appl<br>instructor_***-***-1442,Amy Arnold,e***@outlook.com,AHA_HEARTSAVER_INSTRUCTOR; AHA_BLS_INSTRUCTOR; AHA_ACLS_INSTRUCTOR; AHA_PALS_INSTRUCTOR; AHA_PEARS_INSTRUCTOR,PRIMARY,google_calendar,primary,True,NEEDS_REVIEW,Prefill: Amy is an operation<br>instructor_***-***-6833,Nicholas Tripp,n***@910cpr.com,AHA_HEARTSAVER_INSTRUCTOR; AHA_BLS_INSTRUCTOR; AHA_PALS_INSTRUCTOR,ON_REQUEST,on_request,manual,False,NEEDS_REVIEW,"Prefill: known likely operational person, but no local availability-w |
| `data/audit/people_scheduler_enablement_review.csv` | False | 13 | operational/export-like filename; audit output path; emails:79; phones:17 | instructor_24057895173,Brian Ennis,b***@910cpr.com,AHA_HEARTSAVER_INSTRUCTOR; AHA_BLS_INSTRUCTOR,False,False,unavailable,inverse_google_calendar,inactive,NEEDS_REVIEW,Matched solver availability instructor: Brian Likely operational candidat<br>instructor_***-***-1442,Amy Arnold,e***@outlook.com,AHA_HEARTSAVER_INSTRUCTOR; AHA_BLS_INSTRUCTOR; AHA_ACLS_INSTRUCTOR; AHA_PALS_INSTRUCTOR; AHA_PEARS_INSTRUCTOR,False,False,unavailable,manual_window,inactive,NEEDS_REVIEW,Matched solver ava<br>instructor_***-***-6833,Nicholas Tripp,n***@910cpr.com,AHA_HEARTSAVER_INSTRUCTOR; AHA_BLS_INSTRUCTOR; AHA_PALS_INSTRUCTOR,False,False,unavailable,unknown,inactive,NEEDS_REVIEW,Likely operational candidate; Brian review required before enabl |
| `data/config/people_catalog.json` | False | 12 | operational/export-like filename; emails:87; phones:36 | "person_id": "instructor_***-***-8342",<br>"email": "m***@gmail.com",<br>"instructor_id": "***-***-8342", |
| `data/audit/amy_stack_fill_candidates.json` | False | 11 | audit output path; emails:48; phones:48 | "source_offer_id": "offer-209811-instructor_***-***-1442-20260623-1800",<br>"location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"resource": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", |
| `data/audit/brian_shipyard_raw_calendar_event_trace.json` | False | 10 | operational/export-like filename; audit output path; emails:14; addresses:2 | "selected_event_id": "4***@google.com",<br>"UID": "4***@google.com",<br>"calendar_id": "c***@group.calendar.google.com", |
| `data/audit/internal_dynamic_seed_preview.html` | False | 10 | audit output path; addresses:4; payment_terms:12 | .seed-card { background: white; border: 1px solid #d8dee9; border-radius: 16px; padding: 18px; margin-bottom: 16px; box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05); }<br>.card-head { display: flex; justify-content: space-between; gap: 16px; align-items: start; }<br><article class="seed-card"> |
| `data/audit/seed_appointment_blocker_diagnosis.json` | False | 10 | audit output path; phones:4; addresses:8 | "4*** College Rd\\, Wilmington\\, NC 28412\\, USA": 2,<br>"Wilmington International Airport\\, 1*** Airport Blvd\\, Wilmington\\, NC 28405\\, USA": 1,<br>"NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office": 4, |
| `data/audit/seed_appointment_blocker_diagnosis.md` | False | 10 | audit output path; phones:4; addresses:8 | - 4*** College Rd\, Wilmington\, NC 28412\, USA: 2<br>- Wilmington International Airport\, 1*** Airport Blvd\, Wilmington\, NC 28405\, USA: 1<br>- NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office: 4 |
| `data/audit/brian_shipyard_raw_calendar_event_trace.md` | False | 8 | operational/export-like filename; audit output path; emails:7 | - Selected raw event ID: `4***@google.com`<br>"UID": "4***@google.com",<br>"calendar_id": "c***@group.calendar.google.com", |
| `data/audit/enrollware_registration_event_import_report.md` | False | 8 | operational/export-like filename; audit output path; registration_terms:10 | - Missing required identifiers: {"regId": 1, "courseId": 0, "courseSchedId": 1, "startTime": 0}<br>## Course Schedule ID Registration Counts<br>| regId | courseSchedId | Seed | Course | Appointment Start | Status | |
| `data/audit/people_assignment_policy_apply_report.md` | False | 8 | operational/export-like filename; audit output path; phones:17 | | instructor_***-***-1442 | Amy Arnold | assignment_mode, availability_source, scheduling_role, dynamic_offer_eligible, scheduler_notes |<br>| instructor_***-***-6833 | Nicholas Tripp | assignment_mode, availability_source, scheduling_role, dynamic_offer_eligible, scheduler_notes |<br>| instructor_***-***-2085 | Audrie Babineau | assignment_mode, availability_source, scheduling_role, dynamic_offer_eligible, scheduler_notes | |
| `data/audit/people_assignment_policy_apply_summary.json` | False | 8 | operational/export-like filename; audit output path; phones:17 | "person_id": "instructor_***-***-1442",<br>"person_id": "instructor_***-***-6833",<br>"person_id": "instructor_***-***-2085", |
| `data/audit/people_assignment_policy_patch_template.json` | False | 8 | operational/export-like filename; audit output path; phones:17 | "person_id": "instructor_***-***-1442",<br>"person_id": "instructor_***-***-6833",<br>"person_id": "instructor_***-***-2085", |
| `data/audit/people_assignment_policy_review.md` | False | 8 | operational/export-like filename; audit output path; emails:3; phones:2 | | instructor_24057895173 | Brian Ennis | b***@910cpr.com | PRIMARY | inverse_google_calendar | primary | True | Prefill: Brian is the owner/primary availability bridge candidate. Review before applying. |<br>| instructor_***-***-1442 | Amy Arnold | e***@outlook.com | PRIMARY | google_calendar | primary | True | Prefill: Amy is an operational availability bridge candidate. Review before applying. |<br>| instructor_***-***-6833 | Nicholas Tripp | n***@910cpr.com | ON_REQUEST | on_request | manual | False | Prefill: known likely operational person, but no local availability-window proof found; keep manual/on-request until Brian confirms. | |
| `data/audit/people_scheduler_enablement_patch_template.json` | False | 8 | operational/export-like filename; audit output path; phones:17 | "person_id": "instructor_***-***-1442",<br>"person_id": "instructor_***-***-6833",<br>"person_id": "instructor_***-***-2085", |
| `data/audit/people_scheduler_enablement_review.md` | False | 8 | operational/export-like filename; audit output path; emails:3; phones:2 | | instructor_24057895173 | Brian Ennis | b***@910cpr.com | False | inverse_google_calendar | Matched solver availability instructor: Brian Likely operational candidate; Brian review required before enabling. |<br>| instructor_***-***-1442 | Amy Arnold | e***@outlook.com | False | manual_window | Matched solver availability instructor: Amy Likely operational candidate; Brian review required before enabling. |<br>| instructor_***-***-6833 | Nicholas Tripp | n***@910cpr.com | False | unknown | Likely operational candidate; Brian review required before enabling. | |
| `data/audit/amy_protected_pilot_strategy_report.md` | False | 6 | audit output path; phones:48 | | 2026-06-23 | 18:00-19:30 | AHA ACLS HeartCode | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office | `offer-209811-instructor_***-***-1442-20260623-1800` |<br>| 2026-06-23 | 18:15-19:45 | AHA ACLS HeartCode | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office | `offer-209811-instructor_***-***-1442-20260623-1815` |<br>| 2026-06-23 | 18:30-20:00 | AHA ACLS HeartCode | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office | `offer-209811-instructor_***-***-1442-20260623-1830` | |
| `data/audit/appointment_container_coverage_review.csv` | False | 6 | audit output path; addresses:25 | Brian Ennis,"4*** College Rd\, Wilmington\, NC 28412\, USA",BLS,AHA BLS Provider,2026-06-22,2026-06-22,2,location_mismatch,map_to_existing_container<br>Brian Ennis,"4*** College Rd\, Wilmington\, NC 28412\, USA",BLS,AHA BLS Provider Renewal,2026-06-22,2026-06-22,2,location_mismatch,map_to_existing_container<br>Brian Ennis,"4*** College Rd\, Wilmington\, NC 28412\, USA",BLS,AHA HeartCode BLS,2026-06-22,2026-06-22,4,location_mismatch,map_to_existing_container |
| `data/audit/appointment_container_coverage_review.md` | False | 6 | audit output path; addresses:28 | | `shipyard_brian_continuous_20260621_20270430` | Brian | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office | 2026-06-21 to 2027-04-30 | 260670 to 260983 | 0 |<br>| Brian Ennis | 4*** College Rd\, Wilmington\, NC 28412\, USA | BLS | AHA BLS Provider | 2026-06-22 | 2026-06-22 | 2 | `location_mismatch` | `map_to_existing_container` |<br>| Brian Ennis | 4*** College Rd\, Wilmington\, NC 28412\, USA | BLS | AHA BLS Provider Renewal | 2026-06-22 | 2026-06-22 | 2 | `location_mismatch` | `map_to_existing_container` | |
| `data/audit/enrollware_exit_roadmap_summary.json` | False | 6 | audit output path; payment_terms:15 | "Lander does not yet own registration/payment/roster/attendance/card workflows.",<br>"name": "Native Lander registration/payment",<br>"goal": "Move registration intent, customer intake, and payment into Lander-controlled flow.", |
| `data/audit/public_sellable_offers_review.csv` | False | 6 | audit output path; phones:10 | 2026-06-22,08:30,10:30,AHA BLS Provider,BLS,Brian Ennis,NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office,6,high,offer-209806-instructor_24057895173-20260622-0830,NEEDS_REVIEW,"Review action: approve, hide, adjust time, or adjust policy<br>2026-06-22,08:30,10:30,AHA BLS Provider Renewal,BLS,Brian Ennis,NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office,6,high,offer-359474-instructor_24057895173-20260622-0830,NEEDS_REVIEW,"Review action: approve, hide, adjust time, or adjus<br>2026-06-22,08:30,09:30,AHA HeartCode BLS,BLS,Brian Ennis,NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office,1,high,offer-210549-instructor_24057895173-20260622-0830,NEEDS_REVIEW,"Review action: approve, hide, adjust time, or adjust polic |
| `data/audit/public_sellable_offers_review.md` | False | 6 | audit output path; phones:10 | | 08:30-10:00 | AHA ACLS HeartCode | Amy Arnold | 1 | high | `offer-209811-instructor_***-***-1442-20260623-0830` |<br>| 08:30-12:30 | AHA ACLS Provider (Initial) | Amy Arnold | 6 | high | `offer-241108-instructor_***-***-1442-20260623-0830` |<br>| 08:30-12:30 | AHA ACLS Provider (Renewal) | Amy Arnold | 6 | high | `offer-209818-instructor_***-***-1442-20260623-0830` | |
| `data/audit/scheduler_consumption_window_summary.json` | False | 6 | audit output path; phones:250 | "offer_id": "offer-209811-instructor_***-***-1442-20260623-1800",<br>"offer_id": "offer-209811-instructor_***-***-1442-20260623-1815",<br>"offer_id": "offer-209811-instructor_***-***-1442-20260623-1830", |
| `data/audit/solver_audit_candidates.json` | False | 6 | audit output path; phones:6 | "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"resource": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", |
| `data/fixtures/enrollware_registration_bls_test_row.csv` | False | 6 | operational/export-like filename; emails:1; registration_terms:2; payment_terms:1 | regId,courseId,courseSchedId,courseName,locationName,startTime,instructor,student,email,status,balanceDue<br>27966030,209806,13657403,AHA BLS Provider (Initial),"NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",2026-06-21 17:00:00,Brian Ennis,Brian AAADelete,t***@gmail.com,Pending,75 |
| `docs/910cpr_lander_scheduler_scope_lock.md` | False | 6 | public docs/output path; payment_terms:7; comment_employer_terms:1 | This means the first useful solver does not need to understand products, payments, inventory, reminders, add-ons, or payroll. It needs to understand who can teach, what can be taught, when space/instructors are available, and what is alread<br>- Stripe payments<br>- invoice/payroll logic |
| `data/audit/internal_dynamic_seed_preview.json` | False | 5 | audit output path; addresses:4 | "public_offer_location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"source_availability_location": "4*** Windchime Dr\\, Wilmington\\, NC 28412\\, USA",<br>"public_offer_location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", |
| `docs/enrollware_exit_roadmap_2027.md` | False | 5 | public docs/output path; payment_terms:21 | - `shipyard_brian_continuous_20260621_20270430`: Brian / NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office / appointmentDayId 260670 through 260983 / dates 2026-06-21 through 2027-04-30<br>- Payment or payment delegation.<br>- Card/certificate workflow support or export. |
| `data/audit/brian_shipyard_container_match_diagnosis.json` | False | 4 | audit output path; emails:3 | "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"source_event_id": "4***@google.com",<br>"4***@google.com" |
| `data/audit/calendar_snapshot_export_summary.json` | False | 4 | audit output path; emails:3 | "calendar_id": "c***@group.calendar.google.com",<br>"calendar_id": "c***@group.calendar.google.com",<br>"calendar_id": "c***@group.calendar.google.com", |
| `data/audit/live_availability_snapshot_report.md` | False | 4 | operational/export-like filename; audit output path; phones:1 | | amy_availability | Amy Arnold | `instructor_***-***-1442` | |
| `scripts/build_internal_dynamic_seed_preview.py` | False | 4 | payment_terms:4 | <article class="seed-card"><br><div class="card-head"><br>.seed-card {{ background: white; border: 1px solid #d8dee9; border-radius: 16px; padding: 18px; margin-bottom: 16px; box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05); }} |
| `tests/test_build_live_availability_snapshot.py` | False | 4 | operational/export-like filename; emails:2 | "email": "a***@example.com",<br>"email": "a***@example.com",<br>"location": "4018 Shipyard Blvd, Wilmington, NC 28403, USA", |
| `data/audit/brian_shipyard_offer_generation_trace.json` | False | 3 | audit output path; emails:2 | "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"source_event_id": "4***@google.com",<br>"normalized_location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", |
| `data/audit/brian_shipyard_public_filter_diagnosis.json` | False | 3 | audit output path; emails:2 | "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",<br>"source_event_id": "4***@google.com",<br>"location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", |
| `data/audit/brian_test_shipyard_container_filter_trace.json` | False | 3 | audit output path; emails:2 | "location_name": "4018 Shipyard Blvd\\, Wilmington\\, NC 28403\\, USA",<br>"source_event_id": "3***@google.com",<br>"location": "4018 Shipyard Blvd\\, Wilmington\\, NC 28403\\, USA", |
| `data/audit/live_availability_recheck_requirements.json` | False | 3 | operational/export-like filename; audit output path |  |
| `data/audit/people_catalog_import_report.md` | False | 3 | operational/export-like filename; audit output path |  |
| `data/audit/people_catalog_import_summary.json` | False | 3 | operational/export-like filename; audit output path |  |
| `debug/appointment_offer_calendar.html` | False | 3 | payment_terms:3 | document.querySelectorAll('.offer').forEach(card => {<br>const visible = filters.every(name => !selected[name] || card.dataset[name] === selected[name]);<br>card.classList.toggle('hidden', !visible); |
| `data/Class Report.xlsx"` | False | 2 | operational/export-like filename |  |
| `data/audit/brian_shipyard_container_match_diagnosis.md` | False | 2 | audit output path; emails:1 | - source `4***@google.com`: Brian Ennis / NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office / 2026-07-04 00:00-00:00<br>- `shipyard_brian_continuous_20260621_20270430`: instructor `Brian`, location `NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office`, dates `2026-06-21` to `2027-04-30`, appointmentDayId `260670` to `260983` |
| `data/audit/brian_shipyard_offer_generation_trace.md` | False | 2 | audit output path; emails:1 | - Source: `4***@google.com`<br>- Location: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office<br>- Normalized location/resource: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office / NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office |
| `data/audit/brian_shipyard_public_filter_diagnosis.md` | False | 2 | audit output path; emails:1 | - `4***@google.com`: 2026-07-04 16:01-03:59 / Brian Ennis / NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office / timed |
| `data/audit/brian_test_shipyard_container_filter_trace.md` | False | 2 | audit output path; emails:1 | - Source event: `3***@google.com`<br>- Location: 4018 Shipyard Blvd\, Wilmington\, NC 28403\, USA<br>- Location: 4018 Shipyard Blvd\, Wilmington\, NC 28403\, USA |
| `data/audit/instructor_catalog_validation.md` | False | 2 | audit output path; payment_terms:1 | - `can_teach_course_families` is copied from local availability blocks and is not the same as a verified instructor certification card. |
| `data/audit/instructor_credentials_patch_template.json` | False | 2 | audit output path; payment_terms:1 | "Do not add product, inventory, payment, or Enrollware URL behavior here." |
| `data/audit/solver_audit_report.md` | False | 2 | audit output path; phones:1 | | Amy | Amy Arnold (`instructor_***-***-1442`) | True | `AHA_ACLS_INSTRUCTOR`, `AHA_BLS_INSTRUCTOR`, `AHA_HEARTSAVER_INSTRUCTOR`, `AHA_PALS_INSTRUCTOR`, `AHA_PEARS_INSTRUCTOR` | |
| `data/audit/solver_audit_summary.json` | False | 2 | audit output path; phones:1 | "person_id": "instructor_***-***-1442", |
| `data/runtime/calendar_snapshots/` | False | 2 | raw/runtime data path |  |
| `docs/live_availability_recheck_plan.md` | False | 2 | operational/export-like filename; public docs/output path |  |
| `scripts/build_live_availability_snapshot.py` | False | 2 | operational/export-like filename | "shipyard": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office", |
| `scripts/import_people_catalog.py` | False | 2 | operational/export-like filename |  |
| `tests/test_export_calendar_snapshots.py` | False | 2 | emails:2 | "calendar_id": "c***@group.calendar.google.com",<br>"calendar_id": "p***@example.com", |

## 4. Public Docs/Output Risk

| Path | Score | Signals | Redacted examples |
| --- | ---: | --- | --- |
| `docs/arc.html` | 14 | public docs/output path; phones:6; payment_terms:32; comment_employer_terms:4 | <meta name="description" content="American Red Cross BLS, CPR/AED, and First Aid/CPR/AED options from 910CPR for students whose employer, school, or program requires ARC certification."><br><div class="card slug-hub-shell ecosystem-hub ecosystem-arc"><br><p class="subhead">Use this hub when your employer, school, or program specifically asks for American Red Cross certification, including practical CPR/AED and first aid recognition topics aligned to current first aid guidance.</p> |
| `docs/group.html` | 11 | public docs/output path; emails:1; payment_terms:8; comment_employer_terms:5 | <div class="card slug-hub-shell"><br><div class="slug-panel-card"><br><div class="slug-panel-card"> |
| `docs/hsi.html` | 11 | public docs/output path; phones:6; payment_terms:38; comment_employer_terms:1 | <div class="card slug-hub-shell ecosystem-hub ecosystem-hsi"><br><p class="subhead">Use this hub when your employer, school, or program accepts or requests HSI certification for practical workplace CPR, AED, BLS, and first aid response.</p><br><section class="finder-card ecosystem-card" id="hsi-bls"> |
| `docs/pay/index.html` | 10 | public docs/output path; emails:1; phones:3; payment_terms:50; comment_employer_terms:1 | <title>910CPR Payment</title><br><meta name="description" content="Use this 910CPR payment page for class balances, registration payment issues, group training payments, or special arrangements."><br>.pay-card { |
| `docs/request_group_session.html` | 10 | public docs/output path; payment_terms:8; comment_employer_terms:5 | <div class='card request-shell'><br><section class='tab-panel active' id='bls'><div class='request-program-card'><h2>BLS On-Site</h2><p>American Heart Association BLS Provider training delivered at your location. Ideal for healthcare offices, dental teams, clinics, and medica<br><section class='section-box request-form-card' id='request-form'> |
| `docs/classes/12774548.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774585.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774595.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774598.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775294.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775317.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775542.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775558.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12776266.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12776339.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12776434.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12776435.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12776437.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12776441.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12776565.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12776666.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/13601250.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/13623263.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/13652928.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/13652929.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/13652943.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/13652944.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/13652945.html` | 9 | public docs/output path; payment_terms:7; comment_employer_terms:4 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/courses/index.html` | 9 | public docs/output path; phones:4; payment_terms:14 | .plain-card {<br><a href="tel:***-***-5193">Call ***-***-5193</a><br><section class="section plain-card"> |
| `docs/assets/live-sessions.js` | 8 | operational/export-like filename; public docs/output path; payment_terms:6 | group.querySelectorAll(".slug-day-card").forEach(function (card) {<br>if (!card.querySelector(".slug-time-row") && !card.querySelector(".js-session-item")) {<br>card.remove(); |
| `docs/classes/12774031.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774032.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774040.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774085.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774086.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774087.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774088.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774089.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774090.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774091.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774092.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774093.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774094.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774095.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774096.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774097.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774325.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774326.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774334.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774335.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774336.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774337.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774338.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774339.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774340.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774341.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774342.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774343.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774344.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774345.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774346.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774347.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774348.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774571.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774575.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774582.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774584.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774586.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774587.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774588.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774589.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774590.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774591.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774592.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774593.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774594.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774596.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774597.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774599.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12774600.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775295.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775298.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775306.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775308.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775309.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775310.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775311.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775312.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775313.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775314.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775315.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775316.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775318.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775319.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775320.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775321.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775322.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775323.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775324.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |
| `docs/classes/12775325.html` | 8 | public docs/output path; payment_terms:7; comment_employer_terms:3 | "@type": "Organization",<br>"@type": "Organization",<br><span>Same-day card processing when course requirements and roster details are complete.</span> |

_Additional rows omitted from report table: 328._

## 5. Files That Should Likely Be Gitignored

- `data/Class Report.xlsx"`
- `data/audit/amy_protected_pilot_strategy_report.md`
- `data/audit/amy_stack_fill_candidates.json`
- `data/audit/appointment_container_coverage_review.csv`
- `data/audit/appointment_container_coverage_review.md`
- `data/audit/appointment_seed_registration_matches.json`
- `data/audit/brian_shipyard_container_match_diagnosis.json`
- `data/audit/brian_shipyard_container_match_diagnosis.md`
- `data/audit/brian_shipyard_offer_generation_trace.json`
- `data/audit/brian_shipyard_offer_generation_trace.md`
- `data/audit/brian_shipyard_public_filter_diagnosis.json`
- `data/audit/brian_shipyard_public_filter_diagnosis.md`
- `data/audit/brian_shipyard_raw_calendar_event_trace.json`
- `data/audit/brian_shipyard_raw_calendar_event_trace.md`
- `data/audit/brian_test_shipyard_container_filter_trace.json`
- `data/audit/brian_test_shipyard_container_filter_trace.md`
- `data/audit/calendar_snapshot_export_summary.json`
- `data/audit/dynamic_offers_preview.json`
- `data/audit/enrollware_exit_roadmap_summary.json`
- `data/audit/enrollware_registration_event_import_report.md`
- `data/audit/enrollware_registration_event_import_summary.json`
- `data/audit/enrollware_registration_events_normalized.json`
- `data/audit/enrollware_zapier_registration_event_bridge.md`
- `data/audit/instructor_catalog_validation.md`
- `data/audit/instructor_credentials_patch_template.json`
- `data/audit/internal_dynamic_seed_preview.html`
- `data/audit/internal_dynamic_seed_preview.json`
- `data/audit/live_availability_recheck_requirements.json`
- `data/audit/live_availability_snapshot_preview.json`
- `data/audit/live_availability_snapshot_report.md`
- `data/audit/people_assignment_policy_apply_report.md`
- `data/audit/people_assignment_policy_apply_summary.json`
- `data/audit/people_assignment_policy_patch_template.json`
- `data/audit/people_assignment_policy_review.csv`
- `data/audit/people_assignment_policy_review.md`
- `data/audit/people_catalog_import_report.md`
- `data/audit/people_catalog_import_summary.json`
- `data/audit/people_scheduler_enablement_patch_template.json`
- `data/audit/people_scheduler_enablement_review.csv`
- `data/audit/people_scheduler_enablement_review.md`
- `data/audit/public_sellable_offers_preview.json`
- `data/audit/public_sellable_offers_review.csv`
- `data/audit/public_sellable_offers_review.md`
- `data/audit/schedule_seeds_preview.json`
- `data/audit/scheduler_consumption_window_summary.json`
- `data/audit/seed_appointment_blocker_diagnosis.json`
- `data/audit/seed_appointment_blocker_diagnosis.md`
- `data/audit/solver_audit_candidates.json`
- `data/audit/solver_audit_report.md`
- `data/audit/solver_audit_summary.json`
- `data/audit/zapier_registration_rich_event_review_bundle.md`
- `data/runtime/calendar_snapshots/`
- `debug/appointment_offer_calendar.html`

## 6. Files That May Need Redaction Or Synthetic Replacement

- `build_discovery.py`
- `build_index.py`
- `data/Class Report.xlsx`
- `data/backups/stale_offer_suppression/20260608-105844/public_schedule.json`
- `data/backups/stale_offer_suppression/20260608-121645/public_schedule.json`
- `data/backups/stale_offer_suppression/20260608-133130/public_schedule.json`
- `data/backups/stale_offer_suppression/20260608-161405/public_schedule.json`
- `data/backups/stale_offer_suppression/20260608-192518/public_schedule.json`
- `data/config/calendar_sources.json`
- `data/config/slug_hubs.json`
- `data/enrollware_export.xlsx`
- `data/facebook_post_queue.json`
- `data/facebook_sources.json`
- `data/inventory/910cpr_inventory_events.csv`
- `data/raw/classes_raw_live.csv`
- `data/raw/course-export.xlsx`
- `data/raw/reviews/reviews.json`
- `data/raw/students_raw_live.csv`
- `data/runtime/enrollware_sync/20260427-074805/sync_report.json`
- `data/runtime/enrollware_sync/reconciliation_20260427-074902.json`
- `data/runtime/enrollware_sync/reconciliation_20260427-074950.json`
- `data/schedule_all.json`
- `data/state/session_manifest.json`
- `data/state/stale_offer_suppression_approvals.json`
- `debug/apply_html/209808.after.htmlfrag`
- `debug/apply_html/209808.before.htmlfrag`
- `debug/apply_html/209811.before.htmlfrag`
- `debug/apply_html/351632.after.htmlfrag`
- `debug/apply_html/351632.before.htmlfrag`
- `debug/approved_name_apply_html/209805.after.htmlfrag`
- `debug/approved_name_apply_html/209805.before.htmlfrag`
- `debug/approved_name_apply_html/209806.after.htmlfrag`
- `debug/approved_name_apply_html/209806.before.htmlfrag`
- `debug/approved_name_apply_html/209808.after.htmlfrag`
- `debug/approved_name_apply_html/209808.before.htmlfrag`
- `debug/approved_name_apply_html/209809.after.htmlfrag`
- `debug/approved_name_apply_html/209809.before.htmlfrag`
- `debug/approved_name_apply_html/209811.after.htmlfrag`
- `debug/approved_name_apply_html/209811.before.htmlfrag`
- `debug/approved_name_apply_html/209812.after.htmlfrag`
- `debug/approved_name_apply_html/209812.before.htmlfrag`
- `debug/approved_name_apply_html/209818.after.htmlfrag`
- `debug/approved_name_apply_html/209818.before.htmlfrag`
- `debug/approved_name_apply_html/210549.after.htmlfrag`
- `debug/approved_name_apply_html/210549.before.htmlfrag`
- `debug/approved_name_apply_html/241108.after.htmlfrag`
- `debug/approved_name_apply_html/241108.before.htmlfrag`
- `debug/approved_name_apply_html/248287.after.htmlfrag`
- `debug/approved_name_apply_html/248287.before.htmlfrag`
- `debug/approved_name_apply_html/248288.after.htmlfrag`
- `debug/approved_name_apply_html/248288.before.htmlfrag`
- `debug/approved_name_apply_html/251496.after.htmlfrag`
- `debug/approved_name_apply_html/251496.before.htmlfrag`
- `debug/approved_name_apply_html/251545.after.htmlfrag`
- `debug/approved_name_apply_html/251545.before.htmlfrag`
- `debug/approved_name_apply_html/252734.after.htmlfrag`
- `debug/approved_name_apply_html/252734.before.htmlfrag`
- `debug/approved_name_apply_html/329495.after.htmlfrag`
- `debug/approved_name_apply_html/329495.before.htmlfrag`
- `debug/approved_name_apply_html/344085.after.htmlfrag`
- `debug/approved_name_apply_html/344085.before.htmlfrag`
- `debug/approved_name_apply_html/351632.after.htmlfrag`
- `debug/approved_name_apply_html/351632.before.htmlfrag`
- `debug/approved_name_apply_html/359474.after.htmlfrag`
- `debug/approved_name_apply_html/359474.before.htmlfrag`
- `debug/approved_name_apply_html/369209.after.htmlfrag`
- `debug/approved_name_apply_html/369209.before.htmlfrag`
- `debug/approved_name_apply_html/371954.after.htmlfrag`
- `debug/approved_name_apply_html/371954.before.htmlfrag`
- `debug/approved_name_apply_html/374378.after.htmlfrag`
- `debug/approved_name_apply_html/374378.before.htmlfrag`
- `debug/approved_name_apply_html/380688.after.htmlfrag`
- `debug/approved_name_apply_html/380688.before.htmlfrag`
- `debug/approved_name_apply_html/410694.after.htmlfrag`
- `debug/approved_name_apply_html/410694.before.htmlfrag`
- `debug/approved_name_apply_html/422270.after.htmlfrag`
- `debug/approved_name_apply_html/422270.before.htmlfrag`
- `debug/approved_name_apply_html/440431.after.htmlfrag`
- `debug/approved_name_apply_html/440431.before.htmlfrag`
- `debug/approved_name_apply_html/444919.after.htmlfrag`
- `debug/approved_name_apply_html/444919.before.htmlfrag`
- `debug/approved_name_apply_html/445670.after.htmlfrag`
- `debug/approved_name_apply_html/445670.before.htmlfrag`
- `debug/approved_name_apply_html/448630.after.htmlfrag`
- `debug/approved_name_apply_html/448630.before.htmlfrag`
- `debug/approved_name_apply_html/449422.after.htmlfrag`
- `debug/approved_name_apply_html/449422.before.htmlfrag`
- `debug/approved_name_apply_html/463743.after.htmlfrag`
- `debug/approved_name_apply_html/463743.before.htmlfrag`
- `debug/approved_name_apply_html/485317.after.htmlfrag`
- `debug/approved_name_apply_html/485317.before.htmlfrag`
- `debug/backups/guideline-update-20260512-230619/build_index_and_sitemap.py`
- `debug/backups/guideline-update-20260512-230619/build_landers.py`
- `debug/backups/guideline-update-20260512-230619/build_slug_hubs.py`
- `debug/backups/guideline-update-20260512-230619/course_archive_v4.json`
- `debug/backups/guideline-update-20260512-230619/slug_hubs.json`
- `debug/course_name_cleanup_html/209805.after.htmlfrag`
- `debug/course_name_cleanup_html/209805.before.htmlfrag`
- `debug/course_name_cleanup_html/209806.after.htmlfrag`
- `debug/course_name_cleanup_html/209806.before.htmlfrag`
- `debug/course_name_cleanup_html/209808.after.htmlfrag`
- `debug/course_name_cleanup_html/209808.before.htmlfrag`
- `debug/course_name_cleanup_html/209808.retry.after.htmlfrag`
- `debug/course_name_cleanup_html/209809.after.htmlfrag`
- `debug/course_name_cleanup_html/209809.before.htmlfrag`
- `debug/course_name_cleanup_html/209811.after.htmlfrag`
- `debug/course_name_cleanup_html/209811.before.htmlfrag`
- `debug/course_name_cleanup_html/209811.retry.after.htmlfrag`
- `debug/course_name_cleanup_html/209812.after.htmlfrag`
- `debug/course_name_cleanup_html/209812.before.htmlfrag`
- `debug/course_name_cleanup_html/209812.retry.after.htmlfrag`
- `debug/course_name_cleanup_html/209818.after.htmlfrag`
- `debug/course_name_cleanup_html/209818.before.htmlfrag`
- `debug/course_name_cleanup_html/210549.after.htmlfrag`
- `debug/course_name_cleanup_html/210549.before.htmlfrag`
- `debug/course_name_cleanup_html/210549.retry.after.htmlfrag`
- `debug/course_name_cleanup_html/241108.after.htmlfrag`
- `debug/course_name_cleanup_html/241108.before.htmlfrag`
- `debug/course_name_cleanup_html/248287.after.htmlfrag`
- `debug/course_name_cleanup_html/248287.before.htmlfrag`
- `debug/course_name_cleanup_html/248287.retry.after.htmlfrag`
- `debug/course_name_cleanup_html/248288.after.htmlfrag`
- `debug/course_name_cleanup_html/248288.before.htmlfrag`
- `debug/course_name_cleanup_html/248288.retry.after.htmlfrag`
- `debug/course_name_cleanup_html/251496.after.htmlfrag`
- `debug/course_name_cleanup_html/251496.before.htmlfrag`
- `debug/course_name_cleanup_html/251545.after.htmlfrag`
- `debug/course_name_cleanup_html/251545.before.htmlfrag`
- `debug/course_name_cleanup_html/252734.after.htmlfrag`
- `debug/course_name_cleanup_html/252734.before.htmlfrag`
- `debug/course_name_cleanup_html/329495.after.htmlfrag`
- `debug/course_name_cleanup_html/329495.before.htmlfrag`
- `debug/course_name_cleanup_html/344085.after.htmlfrag`
- `debug/course_name_cleanup_html/344085.before.htmlfrag`
- `debug/course_name_cleanup_html/344085.final.after.htmlfrag`
- `debug/course_name_cleanup_html/344085.retry.after.htmlfrag`
- `debug/course_name_cleanup_html/351632.after.htmlfrag`
- `debug/course_name_cleanup_html/351632.before.htmlfrag`
- `debug/course_name_cleanup_html/351632.final.after.htmlfrag`
- `debug/course_name_cleanup_html/351632.retry.after.htmlfrag`
- `debug/course_name_cleanup_html/359474.after.htmlfrag`
- `debug/course_name_cleanup_html/359474.before.htmlfrag`
- `debug/course_name_cleanup_html/369209.after.htmlfrag`
- `debug/course_name_cleanup_html/369209.before.htmlfrag`
- `debug/course_name_cleanup_html/369209.retry.after.htmlfrag`
- `debug/course_name_cleanup_html/371954.after.htmlfrag`
- `debug/course_name_cleanup_html/371954.before.htmlfrag`
- `debug/course_name_cleanup_html/374378.after.htmlfrag`
- `debug/course_name_cleanup_html/374378.before.htmlfrag`
- `debug/course_name_cleanup_html/380688.after.htmlfrag`

## 7. Sensitive Files Currently Staged

- None. `git diff --cached --name-only` returned no staged files.

## 8. Recommended Next Actions

1. Do not commit broad worktree changes until raw/runtime/audit artifacts are reviewed path-by-path.
2. Treat `data/raw/students_raw_live.csv` as the first tracked cleanup candidate. Decide whether to remove from future commits, replace with a synthetic fixture, and/or rotate/redact history in a separate approved task.
3. Review other tracked operational exports such as `data/Class Report.xlsx`, `data/enrollware_export.xlsx`, `data/raw/classes_raw_live.csv`, and `data/runtime/enrollware_sync/**` for whether they belong in git.
4. Consider expanding `.gitignore` for raw live exports, local Class Reports, runtime sync output, and generated audit/debug reports after confirming which files are source-of-truth versus disposable.
5. Public `docs/` scan did not find the Zapier bridge PII strings, but some public files naturally contain business contact/location terms and Enrollware public class metadata. Keep registration/student/person data out of `docs/`.
6. Keep the Zapier bridge cleanup separate from any historical PII cleanup. The bridge commit `bf0cbcffdb31999e47c738a1ed7ba041a3bdffc0` was selective and did not add registration audit files or fixtures.

