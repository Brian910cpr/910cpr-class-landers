DEPLOY THIS ZIP INTO THE ROOT OF YOUR 910CPR-CLASS-LANDERS REPO.

It contains:
- build/build_all_v3.bat
- scripts/ew_ingest.py
- scripts/build_schedule_json.py
- scripts/build_sessions_current.py
- scripts/build_index.py
- scripts/build_discovery.py

Expected inputs:
- data/course-export.xlsx
- data/Class Report.xlsx

Outputs:
- data/schedule.json
- data/sessions_current.json
- docs/index.html
- docs/schedule.html
- docs/topics/
- docs/topics-year/
- docs/years/
- docs/locations/
- docs/courses/all-courses.html
- docs/data/schedule.json

This bundle fixes the ZIP/html-folder confusion and targets your real repo shape:
inputs in data/, outputs in docs/, BAT in build/.
