# People Assignment Policy Review

This review file replaces the simple scheduler enablement idea with an assignment-policy model. It is review-only and does not modify `data/config/people_catalog.json`, public pages, Enrollware behavior, appointment URLs, Worker behavior, generated HTML, or solver behavior.

## Assignment Modes

- `PRIMARY`: Automatic scheduling candidate.
- `SECONDARY`: Automatic candidate only if primary cannot cover.
- `SUBCONTRACTOR`: Qualified person who may be offered work, but not auto-assigned without policy.
- `ON_REQUEST`: Can be selected manually for special cases.
- `INSTRUCTOR_CUSTOMER`: Instructor associated with 910CPR, but primarily tracked as customer/affiliate, not scheduling labor.
- `INACTIVE`: Historical or currently unavailable instructor.
- `ARCHIVED`: Never consider for scheduling.

## Valid Availability Sources

`inverse_google_calendar`, `google_calendar`, `manual_window`, `on_request`, `none`, `unknown`

## Summary

- Total people included: 79
- Proposed `PRIMARY`: 2
- Proposed `SECONDARY`: 0
- Proposed `SUBCONTRACTOR`: 0
- Proposed `ON_REQUEST`: 1
- Proposed `INACTIVE`: 76
- Proposed `ARCHIVED`: 0

## Likely Operational People Listed First

| Person ID | Display Name | Email | Assignment Mode | Availability Source | Role | Dynamic Offer Eligible | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| instructor_24057895173 | Brian Ennis | brian@910cpr.com | PRIMARY | inverse_google_calendar | primary | True | Prefill: Brian is the owner/primary availability bridge candidate. Review before applying. |
| instructor_4180671442 | Amy Arnold | emschick@outlook.com | PRIMARY | google_calendar | primary | True | Prefill: Amy is an operational availability bridge candidate. Review before applying. |
| instructor_10160506833 | Nicholas Tripp | nicholas@910cpr.com | ON_REQUEST | on_request | manual | False | Prefill: known likely operational person, but no local availability-window proof found; keep manual/on-request until Brian confirms. |

## Review Guidance

- Brian should review the likely operational people first instead of editing all 79 rows.
- Everyone else defaults to `INACTIVE`, `none`, `inactive`, and `false`.
- Do not infer assignment policy from Enrollware Training Site/Admin fields.
- A later audited import step can apply only reviewed rows to `people_catalog.json`.

## Reminder

This is review-only. It does not enable dynamic scheduling or change solver behavior.
