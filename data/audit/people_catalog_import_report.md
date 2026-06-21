# People Catalog Import Report

This is a read-only People/Instructor qualification import. It did not modify public pages, Enrollware behavior, appointment URLs, Worker behavior, generated HTML, or solver behavior.

## Workbook Inspection

- Source workbook: `D:\Users\ten77\Downloads\910CPR Instructor Roster - Allied 100 Transfer.xlsx`
- Worksheets: `Sheet1`
- Imported worksheet: `Sheet1`
- Header row: 1

## Column Mapping

| Field | Column Number |
| --- | ---: |
| `acls` | 10 |
| `alt_email` | 23 |
| `bls` | 9 |
| `email` | 2 |
| `hs` | 8 |
| `instructor_id` | 5 |
| `job_association` | 6 |
| `last_verified` | 22 |
| `name` | 1 |
| `pals` | 11 |
| `pears` | 12 |
| `phone` | 3 |
| `prior_tc` | 7 |
| `transfer_status` | 21 |

## Import Summary

- Rows processed: 79
- People created: 79
- Duplicate emails: 0
- Duplicate names: 0
- Missing emails: 0
- Unclear credential values: 0
- Active for dynamic scheduling: 0

## Certifications Found By Type

| Certification Code | Count |
| --- | ---: |
| `AHA_ACLS_INSTRUCTOR` | 12 |
| `AHA_BLS_INSTRUCTOR` | 74 |
| `AHA_HEARTSAVER_INSTRUCTOR` | 75 |
| `AHA_PALS_INSTRUCTOR` | 14 |
| `AHA_PEARS_INSTRUCTOR` | 9 |

## Duplicate Emails

- None

## Duplicate Names

- None

## Missing Emails

- None

## Unclear Credential Values

- None

## Recommended Next Step

- Brian should review people_catalog.json and confirm which people should be active for dynamic scheduling before any solver integration.
- Do not activate anyone for dynamic scheduling until Brian confirms scheduler eligibility separately from credential presence.
