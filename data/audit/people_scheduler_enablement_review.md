# People Scheduler Enablement Review

This is a Brian-reviewable scheduler enablement worksheet. It does not modify `data/config/people_catalog.json`, public pages, Enrollware behavior, appointment URLs, Worker behavior, generated HTML, or solver behavior.

## Safety Defaults

- `proposed_active_for_dynamic_scheduling` defaults to `false` for every person.
- `proposed_scheduler_status` defaults to `unavailable`.
- `scheduling_role` defaults to `inactive`.
- Brian must explicitly approve any person before dynamic scheduling uses them as an offerable instructor.

## Valid Values

- `proposed_scheduler_status`: `owner`, `employee`, `contractor`, `manual_only`, `unavailable`, `archived`
- `availability_source`: `google_calendar`, `inverse_google_calendar`, `manual_window`, `none`, `unknown`
- `scheduling_role`: `primary`, `backup`, `subcontractor`, `admin_only`, `instructor_customer`, `inactive`

## Summary

- People included: 79
- People currently active for dynamic scheduling: 0
- Likely operational candidates listed first: 3
- Solver availability bridge matches: Amy Arnold, Brian Ennis

## Likely Operational Candidates Listed First

| Person ID | Display Name | Email | Current Active | Availability Source | Notes |
| --- | --- | --- | --- | --- | --- |
| instructor_24057895173 | Brian Ennis | brian@910cpr.com | False | inverse_google_calendar | Matched solver availability instructor: Brian Likely operational candidate; Brian review required before enabling. |
| instructor_4180671442 | Amy Arnold | emschick@outlook.com | False | manual_window | Matched solver availability instructor: Amy Likely operational candidate; Brian review required before enabling. |
| instructor_10160506833 | Nicholas Tripp | nicholas@910cpr.com | False | unknown | Likely operational candidate; Brian review required before enabling. |

## Review Columns

Edit the CSV or JSON patch template after review. Keep people inactive unless Brian confirms they should be scheduler-eligible.

| Column | Meaning |
| --- | --- |
| `proposed_active_for_dynamic_scheduling` | Set to `true` only for people Brian approves for dynamic scheduling. |
| `proposed_scheduler_status` | Operational status such as `owner`, `employee`, `contractor`, or `manual_only`. |
| `availability_source` | Where the scheduler should eventually read availability for that person. Use `unknown` if not confirmed. |
| `scheduling_role` | How the person should be used by the scheduler. |
| `brian_review` | Keep `NEEDS_REVIEW` until Brian approves or rejects the row. |

## Reminder

This is review-only. It does not enable any instructor or change scheduling behavior.
