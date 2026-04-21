@echo off
cd /d "E:\Users\ten77\Documents\GitHub\910cpr-class-landers"

echo ========================================
echo 910CPR FULL STACK BUILD START
echo ========================================

python -m scripts.build_schedule_future
if errorlevel 1 goto :fail

python -m scripts.build_landers --workers 6
if errorlevel 1 goto :fail

python -m scripts.build_request_group_session
if errorlevel 1 goto :fail

python -m scripts.build_slug_hubs
if errorlevel 1 goto :fail

python -m scripts.build_courses
if errorlevel 1 goto :fail

python -m scripts.build_locations
if errorlevel 1 goto :fail

python -m scripts.build_course_at_city
if errorlevel 1 goto :fail

python scripts/build_index_and_sitemap.py
if errorlevel 1 goto :fail

python scripts/build_course_landers.py
if errorlevel 1 goto :fail

python scripts/retrofit_live_sessions.py
if errorlevel 1 goto :fail

echo ========================================
echo BUILD COMPLETE
echo ========================================
pause
exit /b 0

:fail
echo.
echo ========================================
echo BUILD FAILED
echo ========================================
pause
exit /b 1