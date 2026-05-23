# Internal Missing Links Follow-Up Audit

- Total missing internal link occurrences: 36323
- Unique missing target paths: 1554
- User-facing or review-needed occurrences: 9863
- False-positive or low-priority occurrences: 26460

## Counts By Family

- class_numeric: 9863
- external: 26460

## Counts By Priority

- false_positive: 26460
- fix_generated_source: 6771
- review: 3092

## Counts By Likely Type

- false_positive: 26460
- old_generated_reference: 6771
- real_broken_link: 3092

## Top 25 Source Files Creating Missing Links

- docs/classes/cities/wilmington.html: 1544 links, 1544 targets
- docs/classes/certifying-bodies/aha.html: 1244 links, 1244 targets
- docs/classes/certifying-bodies/other.html: 309 links, 309 targets
- docs/classes/courses/209806-bls.html: 307 links, 307 targets
- docs/classes/courses/aha-bls-provider-renewal-for-currently-certified-providers-bls.html: 306 links, 306 targets
- docs/classes/course-at-city/aha-bls-provider-renewal-for-currently-certified-providers-b--wilmington.html: 305 links, 305 targets
- docs/classes/course-at-city/aha-bls-provider-renewal-for-currently-certified-providers-bls--wilmington.html: 305 links, 305 targets
- docs/classes/course-at-city/209806-bls--wilmington.html: 304 links, 304 targets
- docs/classes/course-at-city/aha-heartsaver-first-aid-cpr-aed-blended-online-course-in-pe--wilmington.html: 298 links, 298 targets
- docs/classes/course-at-city/aha-heartsaver-first-aid-cpr-aed-blended-online-course-in-person-skills-session---wilmington.html: 298 links, 298 targets
- docs/classes/courses/aha-heartsaver-first-aid-cpr-aed-blended-online-course-in-person-skills-session-.html: 298 links, 298 targets
- docs/classes/courses/aha-heartsaver-first-aid-cpr-aed-blended-online-course-in-person-skills-session.html: 298 links, 298 targets
- docs/classes/course-at-city/aha-bls-provider-heartcode-skills-blended-learning-with-onli--wilmington.html: 259 links, 259 targets
- docs/classes/course-at-city/aha-bls-provider-heartcode-skills-blended-learning-with-online-course-in-person---wilmington.html: 259 links, 259 targets
- docs/classes/courses/aha-bls-provider-heartcode-skills-blended-learning-with-online-course-in-person-.html: 259 links, 259 targets
- docs/classes/courses/aha-bls-provider-heartcode-skills-blended-learning-with-online-course-in-person.html: 259 links, 259 targets
- docs/classes/months/2026-07.html: 185 links, 185 targets
- docs/classes/months/2026-10.html: 185 links, 185 targets
- docs/classes/months/2026-12.html: 183 links, 183 targets
- docs/classes/months/2026-08.html: 181 links, 181 targets
- docs/classes/months/2026-06.html: 179 links, 179 targets
- docs/classes/months/2026-09.html: 177 links, 177 targets
- docs/classes/months/2026-11.html: 171 links, 171 targets
- docs/classes/months/2026-05.html: 170 links, 170 targets
- docs/classes/course-at-city/aha-heartsaver-first-aid-cpr-aed-in-person-traditional-class--wilmington.html: 148 links, 148 targets

## Top 25 Missing Targets

- /ns.html: 26460 sources, 26460 occurrences, family=external
- /classes/49616.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/49629.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/49968.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/49971.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/49977.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/49978.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50152.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50153.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50246.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50251.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50252.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50374.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50375.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50854.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50905.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/50938.html: 10 sources, 10 occurrences, family=class_numeric
- /classes/48225.html: 9 sources, 9 occurrences, family=class_numeric
- /classes/48229.html: 9 sources, 9 occurrences, family=class_numeric
- /classes/48234.html: 9 sources, 9 occurrences, family=class_numeric
- /classes/48235.html: 9 sources, 9 occurrences, family=class_numeric
- /classes/49206.html: 9 sources, 9 occurrences, family=class_numeric
- /classes/49211.html: 9 sources, 9 occurrences, family=class_numeric
- /classes/49218.html: 9 sources, 9 occurrences, family=class_numeric
- /classes/49412.html: 9 sources, 9 occurrences, family=class_numeric

## User-Facing Fix Guidance

- `fix`: restore the missing page, redirect it, or update the link target before relying on the page.
- `fix_generated_source`: likely generated hub/index references; update generation inputs/templates, then rebuild.
- `review`: inspect manually, often query routes or miscellaneous HTML paths.
- `false_positive`: ignored protocols, external links, anchors, or assets that should not be treated as missing docs pages.

## Recommendation Types

- ignore as false positive: 26460
- restore page or update generated index/hub target: 9863
