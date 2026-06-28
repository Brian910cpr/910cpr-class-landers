# Dynamic Offer Presentation Policy Report

Read-only audit for public presentation compaction. Internal dynamic candidates are preserved upstream; this report classifies which candidates should render publicly.

## Summary

- Public sellable dynamic candidates: 23
- Render-target eligible candidates: 20
- Rendered anchor-stack offers: 7
- Rendered flexible-start windows: 0
- Suppressed adjacent duplicates: 13
- Suppressed unmapped course keys: 3
- Suppressed invalid: 0

## Presentation Modes

- `suppressed_adjacent_candidate`: 13
- `anchor_stack_after`: 7
- `suppressed_unmapped_course_key`: 3

## Rendered Public Offer Examples

| Mode | Date | Time | Course | Instructor | Choices | Source Offer |
| --- | --- | --- | --- | --- | ---: | --- |
| `anchor_stack_after` | 2026-07-04 | 14:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 0 | `offer-209808-instructor_24057895173-20260704-1445` |
| `anchor_stack_after` | 2026-07-04 | 14:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 0 | `offer-251545-instructor_24057895173-20260704-1445` |
| `anchor_stack_after` | 2026-07-04 | 14:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 0 | `offer-329495-instructor_24057895173-20260704-1445` |
| `anchor_stack_after` | 2026-07-04 | 14:45 | AHA Heartsaver CPR AED | Brian Ennis | 0 | `offer-344085-instructor_24057895173-20260704-1445` |
| `anchor_stack_after` | 2026-07-04 | 14:45 | HSI Adult First Aid | CPR AED - Blended Learning | Brian Ennis | 0 | `offer-371954-instructor_24057895173-20260704-1445` |
| `anchor_stack_after` | 2026-07-04 | 14:45 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | 0 | `offer-445670-instructor_24057895173-20260704-1445` |
| `anchor_stack_after` | 2026-07-04 | 14:45 | HSI BLS Challenge | Brian Ennis | 0 | `offer-463743-instructor_24057895173-20260704-1445` |

## Suppressed Adjacent Examples

| Offer | Course | Candidate | Reason |
| --- | --- | --- | --- |
| `offer-209808-instructor_24057895173-20260704-1430` | 209808 | 2026-07-04T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260704-1500` | 209808 | 2026-07-04T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260704-1430` | 251545 | 2026-07-04T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260704-1500` | 251545 | 2026-07-04T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260704-1430` | 329495 | 2026-07-04T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260704-1500` | 329495 | 2026-07-04T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260704-1430` | 344085 | 2026-07-04T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-371954-instructor_24057895173-20260704-1430` | 371954 | 2026-07-04T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-371954-instructor_24057895173-20260704-1500` | 371954 | 2026-07-04T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260704-1430` | 445670 | 2026-07-04T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260704-1500` | 445670 | 2026-07-04T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-463743-instructor_24057895173-20260704-1430` | 463743 | 2026-07-04T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-463743-instructor_24057895173-20260704-1500` | 463743 | 2026-07-04T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
