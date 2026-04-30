@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo Running from %CD%

if not exist "scripts\build_schedule_future.py" (
    echo ERROR: This does not look like the lander repo.
    pause
    exit /b 1
)

for %%P in ("E:\Users\ten77\Documents\GitHub\910cpr-class-landers" "D:\Users\ten77\Documents\GitHub\910cpr-class-landers" "E:\GitHub\910cpr-class-landers") do (
    if exist "%%~P" if /I not "%%~fP"=="%CD%" echo WARNING: Another repo copy exists at %%~fP
)

echo.
echo ========================================
echo FULL STACK BUILD START
echo ========================================

python -m scripts.build_sessions_current
if errorlevel 1 goto :fail

python -m scripts.build_schedule
if errorlevel 1 goto :fail

python -m scripts.build_schedule_future
if errorlevel 1 goto :fail

python -m scripts.audit_stale_sessions --warn-only
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

python -m scripts.build_index_and_sitemap
if errorlevel 1 goto :fail

python scripts/retrofit_live_sessions.py
if errorlevel 1 goto :fail

python -m scripts.audit_stale_sessions --warn-only
if errorlevel 1 goto :fail

echo ========================================
echo FULL STACK BUILD COMPLETE
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
