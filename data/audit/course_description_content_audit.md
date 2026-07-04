# Course Description Content Audit

## Summary

910CPR now has a reusable structured course-description content layer at `data/content/course_descriptions.json`.

The content is intentionally structured, not a single HTML blob. Each record can carry:

- title
- short description
- who this is for
- topics covered
- required materials
- certification issued
- compliance/acceptance notes
- certifying body
- family
- full course page link

No scheduling logic, course IDs, Enrollware appointment URL behavior, pricing, or public visibility rules were changed.

## Sources Reviewed

- `data/config/course_master.json`
- `data/config/course_catalog.json`
- `data/config/slug_hubs.json`
- `data/config/block_schedule_pages.json`
- generated public course pages under `docs/courses/`
- generated selector pages `docs/bls-schedule.html` and `docs/heartsaver-schedule.html`
- existing hub pages `docs/bls.html`, `docs/acls.html`, `docs/pals.html`, `docs/heartsaver.html`, `docs/arc.html`, and `docs/hsi.html`

## Findings

`data/config/slug_hubs.json` is currently the strongest public-page copy source. It already contains richer Heartsaver, ARC, HSI, BLS, ACLS, and PALS page/panel copy.

`data/config/course_master.json` contains useful short descriptions, but rich `description_long` content is incomplete. Several records are `unknown`, and some long descriptions are partner-specific or class-context-specific, so they should not be blindly promoted to public course pages.

Generated class detail pages may contain Enrollware-derived class/session descriptions, but they are not a clean reusable source for course-level descriptions.

Schedule selector pages previously had only short option clarification strings. They now read compact expandable course details from `data/content/course_descriptions.json`.

Date/time/register cards were intentionally left focused on date, time, location, course title, and registration.

## Courses Added To Structured Content

| Course ID | Course |
| ---: | --- |
| 209806 | AHA BLS Provider |
| 359474 | AHA BLS Provider Renewal |
| 210549 | AHA HeartCode BLS |
| 241108 | AHA ACLS Provider |
| 209818 | AHA ACLS Renewal |
| 209811 | AHA ACLS HeartCode |
| 209805 | AHA PALS Provider |
| 251496 | AHA PALS Renewal |
| 209812 | AHA PALS HeartCode |
| 344085 | AHA Heartsaver CPR AED |
| 209808 | AHA Heartsaver CPR AED Online + Skills |
| 209809 | AHA Heartsaver First Aid CPR AED |
| 329495 | AHA Heartsaver First Aid CPR AED Online + Skills |
| 351632 | AHA Heartsaver Pediatric First Aid / CPR / AED |
| 251545 | AHA Heartsaver Pediatric First Aid CPR AED Online + Skills |
| 248288 | American Red Cross Basic Life Support |
| 248287 | American Red Cross Basic Life Support - Blended Learning |
| 445670 | HSI BLS + Adult First Aid |
| 463743 | HSI BLS |

## Where The Content Appears

The structured descriptions are wired into `scripts/build_bls_block_schedule_pilot.py`.

The generated schedule selector course cards now include a collapsed `Course details` panel when description content exists. The panel can show the short description, audience, up to five topics, certification note, and a link to the full course page.

Rebuilt selector outputs:

- `docs/bls-schedule.html`
- `docs/heartsaver-schedule.html`

Course pages remain the best home for full descriptions. This pass does not overwrite existing page-specific copy because the current slug hub copy is already richer than many generated Course Master fields.

## Copyright / Copy Handling

No long Enrollware/manual text was blindly pasted into public pages. The new records are concise 910CPR-controlled summaries and structured fields based on existing public page/course knowledge.

## Validation Notes

- Schedule logic changed: no
- Course IDs changed: no
- Appointment URL behavior changed: no
- Date/time/register cards changed: no
- Heartsaver ASAP broadening public label remains absent from the generated Heartsaver selector output
- Routine public Heartsaver output still does not contain `courseId=460465`

## Recommended Next Steps

1. Review `data/content/course_descriptions.json` as the proposed reusable content source.
2. After approval, promote it into slug hub/course-page generation with page-specific copy precedence so good existing public copy is not overwritten.
3. Backfill richer ARC and HSI course-specific details only after accepted public descriptions are approved.
4. Continue keeping long descriptions out of individual schedule/register cards.
