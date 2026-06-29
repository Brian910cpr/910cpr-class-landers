# Dynamic Offer Presentation Policy Report

Read-only audit for public presentation compaction. Internal dynamic candidates are preserved upstream; this report classifies which candidates should render publicly.

## Summary

- Public sellable dynamic candidates: 14
- Course Master gate eligible candidates: 3
- Suppressed by Course Master gate: 11
- Rendered anchor-stack offers: 1
- Rendered flexible-start windows: 0
- Suppressed adjacent duplicates: 2
- Suppressed invalid: 0

## Presentation Modes

- `suppressed_course_master_gate`: 11
- `suppressed_adjacent_candidate`: 2
- `anchor_stack_after`: 1

## Rendered Public Offer Examples

| Mode | Date | Time | Course | Instructor | Choices | Source Offer |
| --- | --- | --- | --- | --- | ---: | --- |
| `anchor_stack_after` | 2026-07-04 | 14:45 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | 0 | `offer-445670-instructor_24057895173-20260704-1445` |

## Suppressed Adjacent Examples

| Offer | Course | Candidate | Reason |
| --- | --- | --- | --- |
| `offer-445670-instructor_24057895173-20260704-1430` | 445670 | 2026-07-04T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260704-1500` | 445670 | 2026-07-04T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
