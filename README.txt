FIRST STACK DROP

What this contains
- request_group_session.html builder
- course hub builder
- location hub builder
- course-at-city hub builder
- shared hub utility/parser using Class Report.xlsx
- nearby cities config
- simple supervisor control-site stub

Assumptions already encoded
- canonical session filename is last 7 digits of Registration Link
- public/open = Location starts with ":: " AND Seats < 100 AND Registration Link exists
- Seats >= 100 can still create regional/private presence
- nearby cities are support/enrichment, not duplicate pages
- group fallback page = /request_group_session.html

What you need to do
1. Put your report at: data/raw/Class Report.xlsx
2. Keep docs/css/lander.css in your repo
3. Run:
   python scripts/build_request_group_session.py
   python scripts/build_courses.py
   python scripts/build_locations.py
   python scripts/build_course_at_city.py

Notes
- These builders are intentionally conservative starter files.
- They do not yet wire into your supervisor main.py automatically.
- They are meant to get tonight’s stack moving without changing your stable class/session builder.
- After `python -m scripts.build_schedule_future`, run `python scripts/summarize_unmatched_courses.py` to create `debug/unmatched_courses_grouped.json` and `debug/unmatched_courses_grouped.csv` for course alias review. This review step does not change public course names.
