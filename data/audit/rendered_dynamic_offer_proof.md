# Rendered Dynamic Offer Proof

Read-only rendered public-page proof. No deployment, redesign, filtering logic change, Enrollware write, or appointment creation was performed.

## RENDERED PUBLIC DYNAMIC OFFER STATUS

- PASS: All public sellable dynamic appointment-seed offers are visible in rendered customer-facing HTML with correct links.

## Render Command

- `python -m scripts.build_slug_hubs`

## Counts

- Public sellable dynamic appointment-seed offers: `1`
- Rendered dynamic offers: `1`
- Missing from rendered HTML: `0`
- Rendered with Book/Enroll/Register link text: `1`
- Rendered with exact audited href match: `1`
- Reachable from course hub or catalog: `1`
- Distinguishable dynamic in HTML: `1`
- Duplicate existing Enrollware class same tuple: `0`
- Overlap failures: `0`
- Enrollware URLs sample checked: `1`
- Enrollware URLs sample valid: `1`

## Offer Results

### offer-445670-instructor_24057895173-20260704-1445

- Course key: `HSI`
- Display course name: `HSI BLS and Adult First Aid | Blended Learning`
- Instructor: `Brian Ennis`
- Location: `NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office`
- Date: `2026-07-04`
- Public display start/end: `2026-07-04T14:45:00` / `2026-07-04T15:30:00`
- Scheduler consumption start/end: `2026-07-04T14:45:00` / `2026-07-04T16:15:00`
- Source availability block: `37d9u0mq0lh09sngouh6alou82@google.com`
- appointmentDayId/courseId/startTime: `260683` / `445670` / `2:45 PM`
- Final Enrollware href: `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=445670`
- Rendered page path(s): `docs/hsi.html`
- Link/button text: `Check this date/time`
- HTML href exactly matches audited href: `True`
- Reachable from course hub/catalog: `True`
- Dynamic distinguishable internally: `True`
- Duplicate existing Enrollware class rendered same tuple: `False`
- Overlap status: `unknown`
- Enrollware URL sample checked/valid: `True` / `True`
