# Same-course starred day-anchor correction

Owner identified systemic unwanted duplicates beside every starred course, with Oct19 starred09:00 plus11:00 and Oct20 starred11:45 plus09:15/20:00/21:00. Existing engine consolidation relied on paid/count-known occupancy and individual availability windows; the customer projection retained real classes with unknown counts independently. Consequently the final feed could contain a star and additional offers of that same course.

Narrow production publication correction: every retained seated_class establishes an exact(date,courseId) day anchor, regardless full/skills or unknown count. Retain all actual classes; reject only calculated offers with identical courseId on that date, including separate Google availability gaps. Different courseIDs/formats and other dates remain eligible. Confirmed-zero retirement and unknown occupancy preservation unchanged. No bookings or roster counts modified.

59 targeted public adapter, browser pipeline, cache and validation tests passed. Regression covers full and skills anchors with unknown counts, same-day suppression, other-format survival and next-day survival. Syntax checked. Production not yet changed; deployment/actual public day checks pending.
