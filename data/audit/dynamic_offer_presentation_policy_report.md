# Dynamic Offer Presentation Policy Report

Read-only audit for public presentation compaction. Internal dynamic candidates are preserved upstream; this report classifies which candidates should render publicly.

## Summary

- Public sellable dynamic candidates: 210
- Rendered anchor-stack offers: 62
- Rendered flexible-start windows: 44
- Suppressed adjacent duplicates: 104
- Suppressed invalid: 0

## Presentation Modes

- `suppressed_adjacent_candidate`: 104
- `flexible_start_window`: 44
- `anchor_stack_after`: 43
- `anchor_stack_before`: 19

## Rendered Public Offer Examples

| Mode | Date | Time | Course | Instructor | Choices | Source Offer |
| --- | --- | --- | --- | --- | ---: | --- |
| `anchor_stack_after` | 2026-07-06 | 14:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 0 | `offer-209808-instructor_24057895173-20260706-1445` |
| `anchor_stack_after` | 2026-07-06 | 14:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 0 | `offer-251545-instructor_24057895173-20260706-1445` |
| `anchor_stack_after` | 2026-07-06 | 14:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 0 | `offer-329495-instructor_24057895173-20260706-1445` |
| `anchor_stack_before` | 2026-07-06 | 15:00 | AHA Heartsaver CPR AED | Brian Ennis | 0 | `offer-344085-instructor_24057895173-20260706-1500` |
| `anchor_stack_after` | 2026-07-06 | 14:45 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | 0 | `offer-445670-instructor_24057895173-20260706-1445` |
| `anchor_stack_after` | 2026-07-07 | 12:30 | AHA BLS Provider | Brian Ennis | 0 | `offer-209806-instructor_24057895173-20260707-1230` |
| `anchor_stack_after` | 2026-07-07 | 12:45 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 0 | `offer-209809-instructor_24057895173-20260707-1245` |
| `anchor_stack_after` | 2026-07-07 | 12:30 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260707-1230` |
| `anchor_stack_after` | 2026-07-07 | 12:45 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 0 | `offer-351632-instructor_24057895173-20260707-1245` |
| `anchor_stack_after` | 2026-07-07 | 12:30 | AHA BLS Provider Renewal | Brian Ennis | 0 | `offer-359474-instructor_24057895173-20260707-1230` |
| `anchor_stack_after` | 2026-07-09 | 12:30 | AHA BLS Provider | Brian Ennis | 0 | `offer-209806-instructor_24057895173-20260709-1230` |
| `anchor_stack_after` | 2026-07-09 | 12:30 | AHA BLS Provider Renewal | Brian Ennis | 0 | `offer-359474-instructor_24057895173-20260709-1230` |
| `anchor_stack_before` | 2026-07-10 | 09:15 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260710-0915` |
| `flexible_start_window` | 2026-07-12 | 09:15 | AHA BLS Provider | Brian Ennis | 1 | `offer-209806-instructor_24057895173-20260712-0915` |
| `flexible_start_window` | 2026-07-12 | 09:15 | AHA HeartCode BLS | Brian Ennis | 1 | `offer-210549-instructor_24057895173-20260712-0915` |
| `flexible_start_window` | 2026-07-12 | 09:15 | AHA BLS Provider Renewal | Brian Ennis | 1 | `offer-359474-instructor_24057895173-20260712-0915` |
| `anchor_stack_after` | 2026-07-13 | 14:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 0 | `offer-209808-instructor_24057895173-20260713-1445` |
| `anchor_stack_after` | 2026-07-13 | 14:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 0 | `offer-251545-instructor_24057895173-20260713-1445` |
| `anchor_stack_after` | 2026-07-13 | 14:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 0 | `offer-329495-instructor_24057895173-20260713-1445` |
| `anchor_stack_before` | 2026-07-13 | 15:00 | AHA Heartsaver CPR AED | Brian Ennis | 0 | `offer-344085-instructor_24057895173-20260713-1500` |
| `anchor_stack_after` | 2026-07-13 | 14:45 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | 0 | `offer-445670-instructor_24057895173-20260713-1445` |
| `anchor_stack_after` | 2026-07-14 | 12:30 | AHA BLS Provider | Brian Ennis | 0 | `offer-209806-instructor_24057895173-20260714-1230` |
| `anchor_stack_after` | 2026-07-14 | 12:45 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 0 | `offer-209809-instructor_24057895173-20260714-1245` |
| `anchor_stack_after` | 2026-07-14 | 12:45 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 0 | `offer-351632-instructor_24057895173-20260714-1245` |
| `anchor_stack_after` | 2026-07-14 | 12:30 | AHA BLS Provider Renewal | Brian Ennis | 0 | `offer-359474-instructor_24057895173-20260714-1230` |
| `anchor_stack_before` | 2026-07-15 | 09:15 | AHA BLS Provider | Brian Ennis | 0 | `offer-209806-instructor_24057895173-20260715-0915` |
| `anchor_stack_before` | 2026-07-15 | 09:15 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260715-0915` |
| `anchor_stack_before` | 2026-07-15 | 09:15 | AHA BLS Provider Renewal | Brian Ennis | 0 | `offer-359474-instructor_24057895173-20260715-0915` |
| `anchor_stack_before` | 2026-07-17 | 09:15 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260717-0915` |
| `flexible_start_window` | 2026-07-19 | 09:15 | AHA BLS Provider | Brian Ennis | 1 | `offer-209806-instructor_24057895173-20260719-0915` |
| `flexible_start_window` | 2026-07-19 | 09:15 | AHA HeartCode BLS | Brian Ennis | 1 | `offer-210549-instructor_24057895173-20260719-0915` |
| `flexible_start_window` | 2026-07-19 | 09:15 | AHA BLS Provider Renewal | Brian Ennis | 1 | `offer-359474-instructor_24057895173-20260719-0915` |
| `anchor_stack_after` | 2026-07-20 | 14:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 0 | `offer-209808-instructor_24057895173-20260720-1445` |
| `anchor_stack_after` | 2026-07-20 | 14:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 0 | `offer-251545-instructor_24057895173-20260720-1445` |
| `anchor_stack_after` | 2026-07-20 | 14:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 0 | `offer-329495-instructor_24057895173-20260720-1445` |
| `anchor_stack_after` | 2026-07-20 | 14:45 | AHA Heartsaver CPR AED | Brian Ennis | 0 | `offer-344085-instructor_24057895173-20260720-1445` |
| `anchor_stack_after` | 2026-07-20 | 14:45 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | 0 | `offer-445670-instructor_24057895173-20260720-1445` |
| `anchor_stack_before` | 2026-07-22 | 12:30 | AHA BLS Provider | Brian Ennis | 0 | `offer-209806-instructor_24057895173-20260722-1230` |
| `anchor_stack_before` | 2026-07-22 | 09:00 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 0 | `offer-209809-instructor_24057895173-20260722-0900` |
| `anchor_stack_before` | 2026-07-22 | 09:15 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260722-0915` |
| `anchor_stack_before` | 2026-07-22 | 09:00 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 0 | `offer-351632-instructor_24057895173-20260722-0900` |
| `anchor_stack_before` | 2026-07-22 | 12:30 | AHA BLS Provider Renewal | Brian Ennis | 0 | `offer-359474-instructor_24057895173-20260722-1230` |
| `anchor_stack_before` | 2026-07-24 | 09:15 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260724-0915` |
| `flexible_start_window` | 2026-07-26 | 09:15 | AHA BLS Provider | Brian Ennis | 1 | `offer-209806-instructor_24057895173-20260726-0915` |
| `flexible_start_window` | 2026-07-26 | 09:15 | AHA HeartCode BLS | Brian Ennis | 1 | `offer-210549-instructor_24057895173-20260726-0915` |
| `flexible_start_window` | 2026-07-26 | 09:15 | AHA BLS Provider Renewal | Brian Ennis | 1 | `offer-359474-instructor_24057895173-20260726-0915` |
| `anchor_stack_after` | 2026-07-27 | 14:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 0 | `offer-209808-instructor_24057895173-20260727-1445` |
| `anchor_stack_after` | 2026-07-27 | 14:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 0 | `offer-251545-instructor_24057895173-20260727-1445` |
| `anchor_stack_after` | 2026-07-27 | 14:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 0 | `offer-329495-instructor_24057895173-20260727-1445` |
| `anchor_stack_before` | 2026-07-27 | 15:00 | AHA Heartsaver CPR AED | Brian Ennis | 0 | `offer-344085-instructor_24057895173-20260727-1500` |
| `anchor_stack_after` | 2026-07-27 | 14:45 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | 0 | `offer-445670-instructor_24057895173-20260727-1445` |
| `anchor_stack_after` | 2026-07-28 | 12:30 | AHA BLS Provider | Brian Ennis | 0 | `offer-209806-instructor_24057895173-20260728-1230` |
| `anchor_stack_after` | 2026-07-28 | 12:45 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 0 | `offer-209809-instructor_24057895173-20260728-1245` |
| `anchor_stack_after` | 2026-07-28 | 12:30 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260728-1230` |
| `anchor_stack_after` | 2026-07-28 | 12:45 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 0 | `offer-351632-instructor_24057895173-20260728-1245` |
| `anchor_stack_after` | 2026-07-28 | 12:30 | AHA BLS Provider Renewal | Brian Ennis | 0 | `offer-359474-instructor_24057895173-20260728-1230` |
| `anchor_stack_after` | 2026-07-02 | 12:30 | AHA BLS Provider | Brian Ennis | 0 | `offer-209806-instructor_24057895173-20260702-1230` |
| `anchor_stack_after` | 2026-07-02 | 12:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 0 | `offer-209808-instructor_24057895173-20260702-1245` |
| `anchor_stack_after` | 2026-07-02 | 12:45 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 0 | `offer-209809-instructor_24057895173-20260702-1245` |
| `anchor_stack_after` | 2026-07-02 | 12:30 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260702-1230` |
| `anchor_stack_after` | 2026-07-02 | 12:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 0 | `offer-251545-instructor_24057895173-20260702-1245` |
| `anchor_stack_after` | 2026-07-02 | 12:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 0 | `offer-329495-instructor_24057895173-20260702-1245` |
| `anchor_stack_after` | 2026-07-02 | 12:45 | AHA Heartsaver CPR AED | Brian Ennis | 0 | `offer-344085-instructor_24057895173-20260702-1245` |
| `anchor_stack_after` | 2026-07-02 | 12:45 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 0 | `offer-351632-instructor_24057895173-20260702-1245` |
| `anchor_stack_after` | 2026-07-02 | 12:30 | AHA BLS Provider Renewal | Brian Ennis | 0 | `offer-359474-instructor_24057895173-20260702-1230` |
| `anchor_stack_after` | 2026-07-02 | 12:45 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | 0 | `offer-445670-instructor_24057895173-20260702-1245` |
| `anchor_stack_before` | 2026-07-29 | 12:30 | AHA BLS Provider | Brian Ennis | 0 | `offer-209806-instructor_24057895173-20260729-1230` |
| `anchor_stack_before` | 2026-07-29 | 09:15 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260729-0915` |
| `anchor_stack_before` | 2026-07-29 | 12:30 | AHA BLS Provider Renewal | Brian Ennis | 0 | `offer-359474-instructor_24057895173-20260729-1230` |
| `anchor_stack_before` | 2026-07-31 | 09:15 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260731-0915` |
| `flexible_start_window` | 2026-08-03 | 09:15 | AHA BLS Provider | Brian Ennis | 1 | `offer-209806-instructor_24057895173-20260803-0915` |
| `flexible_start_window` | 2026-08-03 | 08:00 | AHA Heartsaver CPR AED Online | Brian Ennis | 3 | `offer-209808-instructor_24057895173-20260803-0800` |
| `flexible_start_window` | 2026-08-03 | 08:00 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 3 | `offer-209809-instructor_24057895173-20260803-0800` |
| `flexible_start_window` | 2026-08-03 | 09:15 | AHA HeartCode BLS | Brian Ennis | 1 | `offer-210549-instructor_24057895173-20260803-0915` |
| `flexible_start_window` | 2026-08-03 | 08:00 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 3 | `offer-251545-instructor_24057895173-20260803-0800` |
| `flexible_start_window` | 2026-08-03 | 08:00 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 3 | `offer-329495-instructor_24057895173-20260803-0800` |
| `flexible_start_window` | 2026-08-03 | 08:00 | AHA Heartsaver CPR AED | Brian Ennis | 3 | `offer-344085-instructor_24057895173-20260803-0800` |
| `flexible_start_window` | 2026-08-03 | 08:00 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 3 | `offer-351632-instructor_24057895173-20260803-0800` |
| `flexible_start_window` | 2026-08-03 | 09:15 | AHA BLS Provider Renewal | Brian Ennis | 1 | `offer-359474-instructor_24057895173-20260803-0915` |
| `flexible_start_window` | 2026-08-03 | 08:00 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | 3 | `offer-445670-instructor_24057895173-20260803-0800` |
| `flexible_start_window` | 2026-08-04 | 09:15 | AHA BLS Provider | Brian Ennis | 1 | `offer-209806-instructor_24057895173-20260804-0915` |
| `flexible_start_window` | 2026-08-04 | 09:15 | AHA HeartCode BLS | Brian Ennis | 1 | `offer-210549-instructor_24057895173-20260804-0915` |
| `flexible_start_window` | 2026-08-04 | 09:15 | AHA BLS Provider Renewal | Brian Ennis | 1 | `offer-359474-instructor_24057895173-20260804-0915` |
| `anchor_stack_before` | 2026-07-03 | 09:15 | AHA HeartCode BLS | Brian Ennis | 0 | `offer-210549-instructor_24057895173-20260703-0915` |
| `flexible_start_window` | 2026-08-05 | 09:15 | AHA BLS Provider | Brian Ennis | 1 | `offer-209806-instructor_24057895173-20260805-0915` |
| `flexible_start_window` | 2026-08-05 | 09:15 | AHA HeartCode BLS | Brian Ennis | 1 | `offer-210549-instructor_24057895173-20260805-0915` |
| `flexible_start_window` | 2026-08-05 | 09:15 | AHA BLS Provider Renewal | Brian Ennis | 1 | `offer-359474-instructor_24057895173-20260805-0915` |
| `flexible_start_window` | 2026-08-10 | 09:15 | AHA BLS Provider | Brian Ennis | 1 | `offer-209806-instructor_24057895173-20260810-0915` |
| `flexible_start_window` | 2026-08-10 | 08:00 | AHA Heartsaver CPR AED Online | Brian Ennis | 3 | `offer-209808-instructor_24057895173-20260810-0800` |
| `flexible_start_window` | 2026-08-10 | 08:00 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 3 | `offer-209809-instructor_24057895173-20260810-0800` |
| `flexible_start_window` | 2026-08-10 | 09:15 | AHA HeartCode BLS | Brian Ennis | 1 | `offer-210549-instructor_24057895173-20260810-0915` |
| `flexible_start_window` | 2026-08-10 | 08:00 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 3 | `offer-251545-instructor_24057895173-20260810-0800` |
| `flexible_start_window` | 2026-08-10 | 08:00 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 3 | `offer-329495-instructor_24057895173-20260810-0800` |
| `flexible_start_window` | 2026-08-10 | 08:00 | AHA Heartsaver CPR AED | Brian Ennis | 3 | `offer-344085-instructor_24057895173-20260810-0800` |
| `flexible_start_window` | 2026-08-10 | 08:00 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 3 | `offer-351632-instructor_24057895173-20260810-0800` |
| `flexible_start_window` | 2026-08-10 | 09:15 | AHA BLS Provider Renewal | Brian Ennis | 1 | `offer-359474-instructor_24057895173-20260810-0915` |
| `flexible_start_window` | 2026-08-10 | 08:00 | HSI BLS and Adult First Aid | Blended Learning | Brian Ennis | 3 | `offer-445670-instructor_24057895173-20260810-0800` |
| `flexible_start_window` | 2026-08-11 | 09:15 | AHA BLS Provider | Brian Ennis | 1 | `offer-209806-instructor_24057895173-20260811-0915` |
| `flexible_start_window` | 2026-08-11 | 09:15 | AHA HeartCode BLS | Brian Ennis | 1 | `offer-210549-instructor_24057895173-20260811-0915` |
| `flexible_start_window` | 2026-08-11 | 09:15 | AHA BLS Provider Renewal | Brian Ennis | 1 | `offer-359474-instructor_24057895173-20260811-0915` |

## Suppressed Adjacent Examples

| Offer | Course | Candidate | Reason |
| --- | --- | --- | --- |
| `offer-209808-instructor_24057895173-20260706-1430` | 209808 | 2026-07-06T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260706-1500` | 209808 | 2026-07-06T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260706-1430` | 251545 | 2026-07-06T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260706-1500` | 251545 | 2026-07-06T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260706-1430` | 329495 | 2026-07-06T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260706-1500` | 329495 | 2026-07-06T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260706-1430` | 344085 | 2026-07-06T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260706-1445` | 344085 | 2026-07-06T14:45:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260706-1430` | 445670 | 2026-07-06T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260706-1500` | 445670 | 2026-07-06T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260707-1230` | 209809 | 2026-07-07T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260707-1300` | 209809 | 2026-07-07T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260707-1230` | 351632 | 2026-07-07T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260707-1300` | 351632 | 2026-07-07T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260713-1430` | 209808 | 2026-07-13T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260713-1500` | 209808 | 2026-07-13T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260713-1430` | 251545 | 2026-07-13T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260713-1500` | 251545 | 2026-07-13T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260713-1430` | 329495 | 2026-07-13T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260713-1500` | 329495 | 2026-07-13T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260713-1430` | 344085 | 2026-07-13T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260713-1445` | 344085 | 2026-07-13T14:45:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260713-1430` | 445670 | 2026-07-13T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260713-1500` | 445670 | 2026-07-13T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260714-1230` | 209809 | 2026-07-14T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260714-1300` | 209809 | 2026-07-14T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260714-1230` | 351632 | 2026-07-14T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260714-1300` | 351632 | 2026-07-14T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260720-1430` | 209808 | 2026-07-20T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260720-1500` | 209808 | 2026-07-20T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260720-1430` | 251545 | 2026-07-20T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260720-1500` | 251545 | 2026-07-20T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260720-1430` | 329495 | 2026-07-20T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260720-1500` | 329495 | 2026-07-20T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260720-1430` | 344085 | 2026-07-20T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260720-1500` | 344085 | 2026-07-20T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260720-1430` | 445670 | 2026-07-20T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260720-1500` | 445670 | 2026-07-20T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209806-instructor_24057895173-20260722-0915` | 209806 | 2026-07-22T09:15:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260722-0830` | 209809 | 2026-07-22T08:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260722-0845` | 209809 | 2026-07-22T08:45:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260722-0830` | 351632 | 2026-07-22T08:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260722-0845` | 351632 | 2026-07-22T08:45:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-359474-instructor_24057895173-20260722-0915` | 359474 | 2026-07-22T09:15:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260727-1430` | 209808 | 2026-07-27T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260727-1500` | 209808 | 2026-07-27T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260727-1430` | 251545 | 2026-07-27T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260727-1500` | 251545 | 2026-07-27T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260727-1430` | 329495 | 2026-07-27T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260727-1500` | 329495 | 2026-07-27T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260727-1430` | 344085 | 2026-07-27T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260727-1445` | 344085 | 2026-07-27T14:45:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260727-1430` | 445670 | 2026-07-27T14:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260727-1500` | 445670 | 2026-07-27T15:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260728-1230` | 209809 | 2026-07-28T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260728-1300` | 209809 | 2026-07-28T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260728-1230` | 351632 | 2026-07-28T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260728-1300` | 351632 | 2026-07-28T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260702-1230` | 209808 | 2026-07-02T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260702-1300` | 209808 | 2026-07-02T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260702-1230` | 209809 | 2026-07-02T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209809-instructor_24057895173-20260702-1300` | 209809 | 2026-07-02T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260702-1230` | 251545 | 2026-07-02T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-251545-instructor_24057895173-20260702-1300` | 251545 | 2026-07-02T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260702-1230` | 329495 | 2026-07-02T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-329495-instructor_24057895173-20260702-1300` | 329495 | 2026-07-02T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260702-1230` | 344085 | 2026-07-02T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-344085-instructor_24057895173-20260702-1300` | 344085 | 2026-07-02T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260702-1230` | 351632 | 2026-07-02T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-351632-instructor_24057895173-20260702-1300` | 351632 | 2026-07-02T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260702-1230` | 445670 | 2026-07-02T12:30:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-445670-instructor_24057895173-20260702-1300` | 445670 | 2026-07-02T13:00:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209806-instructor_24057895173-20260729-0915` | 209806 | 2026-07-29T09:15:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-359474-instructor_24057895173-20260729-0915` | 359474 | 2026-07-29T09:15:00 | Suppressed because another candidate in this course/window fits the anchor more tightly. |
| `offer-209808-instructor_24057895173-20260803-0815` | 209808 | 2026-08-03T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-209808-instructor_24057895173-20260803-0830` | 209808 | 2026-08-03T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-209809-instructor_24057895173-20260803-0815` | 209809 | 2026-08-03T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-209809-instructor_24057895173-20260803-0830` | 209809 | 2026-08-03T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-251545-instructor_24057895173-20260803-0815` | 251545 | 2026-08-03T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-251545-instructor_24057895173-20260803-0830` | 251545 | 2026-08-03T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-329495-instructor_24057895173-20260803-0815` | 329495 | 2026-08-03T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-329495-instructor_24057895173-20260803-0830` | 329495 | 2026-08-03T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-344085-instructor_24057895173-20260803-0815` | 344085 | 2026-08-03T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-344085-instructor_24057895173-20260803-0830` | 344085 | 2026-08-03T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-351632-instructor_24057895173-20260803-0815` | 351632 | 2026-08-03T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-351632-instructor_24057895173-20260803-0830` | 351632 | 2026-08-03T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-445670-instructor_24057895173-20260803-0815` | 445670 | 2026-08-03T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-445670-instructor_24057895173-20260803-0830` | 445670 | 2026-08-03T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-209808-instructor_24057895173-20260810-0815` | 209808 | 2026-08-10T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-209808-instructor_24057895173-20260810-0830` | 209808 | 2026-08-10T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-209809-instructor_24057895173-20260810-0815` | 209809 | 2026-08-10T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-209809-instructor_24057895173-20260810-0830` | 209809 | 2026-08-10T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-251545-instructor_24057895173-20260810-0815` | 251545 | 2026-08-10T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-251545-instructor_24057895173-20260810-0830` | 251545 | 2026-08-10T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-329495-instructor_24057895173-20260810-0815` | 329495 | 2026-08-10T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-329495-instructor_24057895173-20260810-0830` | 329495 | 2026-08-10T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-344085-instructor_24057895173-20260810-0815` | 344085 | 2026-08-10T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-344085-instructor_24057895173-20260810-0830` | 344085 | 2026-08-10T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-351632-instructor_24057895173-20260810-0815` | 351632 | 2026-08-10T08:15:00 | Suppressed because this course/window is represented by a flexible-start offer. |
| `offer-351632-instructor_24057895173-20260810-0830` | 351632 | 2026-08-10T08:30:00 | Suppressed because this course/window is represented by a flexible-start offer. |
