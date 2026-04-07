910CPR COMBINED BUILD BUNDLE

What this adds
- build/build_all_v4.bat
- scripts/build_all_v4.py

What build_all_v4.bat does
1. Runs your existing lander generator first, if found.
   It tries:
   - run_910cpr_landers.bat
   - run_rebuild.bat
   - run_landers_worker.bat
2. Then runs build/build_all_v3.bat
   which builds:
   - data/schedule.json
   - data/sessions_current.json
   - docs/index.html
   - docs/schedule.html
   - docs/topics/
   - docs/topics-year/
   - docs/years/
   - docs/locations/

Run from repo root
    .\build\build_all_v4.bat

Optional
- Force a specific lander command:
    set LANDER_CMD=".\run_910cpr_landers.bat"
    .\build\build_all_v4.bat

- Skip the lander phase:
    set SKIP_LANDERS=1
    .\build\build_all_v4.bat

Python runner alternative
    python .\scripts\build_all_v4.py
