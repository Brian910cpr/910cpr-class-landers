@echo off
cd /d D:\Users\ten77\Documents\GitHub\910cpr-class-landers

echo =========================
echo 910CPR FULL REBUILD START
echo =========================
echo.

echo STEP 1 - Build schedule
python scripts\build_schedule.py
if errorlevel 1 goto error

echo.
echo STEP 2 - Build public schedule JSON
python scripts\build_public_schedule_json.py
if errorlevel 1 goto error

echo.
echo STEP 3 - Build class landers
python scripts\build_landers.py
if errorlevel 1 goto error

echo.
echo STEP 4 - Build course landers
python scripts\build_course_landers.py
if errorlevel 1 goto error

echo.
echo STEP 5 - Build index and sitemap
python scripts\build_index_and_sitemap.py
if errorlevel 1 goto error

echo.
echo =========================
echo BUILD COMPLETE
echo =========================
pause
exit /b 0

:error
echo.
echo =========================
echo BUILD FAILED
echo =========================
pause
exit /b 1