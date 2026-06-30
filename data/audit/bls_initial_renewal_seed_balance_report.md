# BLS Initial/Renewal seed balance report

## Plain answer
Initial won before because daily BLS family mix sorted by preferred start, then course_title_priority_terms; 'BLS Provider' ranked Initial before Renewal. Renewal rows were present as seed candidates and rejected mostly as family_mix_target_already_met.

## Rule
Implemented recommendation C: keep one BLS seed per date, but alternate Initial and Renewal across eligible BLS seed dates.

- Before: 6 selected, {'Initial': 6}
- After: 6 selected, {'Renewal': 3, 'Initial': 3}
- Rendered rows in docs/bls.html: 6
- Duplicate selected seed rows: 0

## After selected rows
| Date | Time | CourseId | Variant | Course | Rendered |
| --- | --- | --- | --- | --- | --- |
| 2026-08-03 | 09:15 | 359474 | Renewal | AHA BLS Provider Renewal | True |
| 2026-08-04 | 09:15 | 209806 | Initial | AHA BLS Provider | True |
| 2026-08-05 | 09:15 | 359474 | Renewal | AHA BLS Provider Renewal | True |
| 2026-08-10 | 09:15 | 209806 | Initial | AHA BLS Provider | True |
| 2026-08-11 | 09:15 | 359474 | Renewal | AHA BLS Provider Renewal | True |
| 2026-08-12 | 09:15 | 209806 | Initial | AHA BLS Provider | True |

## Existing real August BLS Enrollware rows
| Session | Start | CourseId | Variant |
| --- | --- | --- | --- |
| 12946259 | 2026-08-10T09:00:00-04:00 | 359474 | Renewal |
| 13601250 | 2026-08-14T12:45:00-04:00 | 209806 | Initial |
