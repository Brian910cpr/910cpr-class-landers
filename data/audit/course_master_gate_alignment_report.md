# Course Master Gate Alignment Report

## Verdict

Course Master should gate generated rows, not real scheduled Enrollware classes. The current visible rows include real Class Report rows that are safe to keep, plus appointment seeds that are blocked by the stricter Course Master rule until reviewed or explicitly excepted.

## Gate Matrix

| Row category | Public rule |
|---|---|
| existing_enrollware_class | May render when it matches the latest Class Report and uses `/enroll?id=`. Dynamic flags do not block real scheduled classes. |
| appointment_seed | Requires `appointment_seed_allowed=true` or an explicit reviewed exception, known course key, reviewed page/card, `appointmentDayId`, and `startTime`; blocked by `review_needed_for_scheduling=true`. |
| dynamic_offer | Requires `dynamic_offer_allowed=true`, public sellable filtering, reviewed page/card, and no scheduling review flag. |
| request_only | Must stay request-only and pass reviewed generated-offer gates; it must not create checkout/class rows. |

## Current Public Row Audit

- Total visible rows audited: `216`
- Allowed by rule: `216`
- Blocked by rule: `0`
- By source: `{'existing_enrollware_class': 215, 'appointment_seed': 1}`
- Blocked reasons: `{}`

## Visible Generated-Row Violations

| course_key | courseId | course_display_name | date | time | visible_page | reason |
| --- | --- | --- | --- | --- | --- | --- |
| none |  |  |  |  |  |  |

## Investigation Answers

- Visible despite `dynamic_offer_allowed=false`: `0` generated/non-Class-Report rows.
- Visible despite `appointment_seed_allowed=false`: `0` appointment seed rows.
- Visible despite `review_needed_for_scheduling=true`: `0` generated/non-Class-Report rows.
- These are not real Class Report rows misclassified as dynamic; the blocked rows are appointment seed rows with appointmentDayId URLs.
- Under the new gate, they should be suppressed unless Brian explicitly reviews and allowlists the course/seed behavior.

## Output Files

- `data/audit/course_master_gate_alignment_report.json`
- `data/audit/public_row_gate_audit.csv`
- `data/audit/august_manual_schedule_floor_recommendation.md`
- `data/audit/july_4_seed_decision_report.md`
- `data/audit/minimum_safe_gate_fix_plan.md`
