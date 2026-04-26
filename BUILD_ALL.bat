@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "COMPLETE_REBUILD=0"
if /I "%~1"=="--complete" set "COMPLETE_REBUILD=1"
if /I "%~1"=="--full" set "COMPLETE_REBUILD=1"

cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Could not change to repo root.
    pause
    exit /b 1
)

echo.
echo ============================================
echo STARTING SUPERVISOR SERVER
echo ============================================

REM Start local HTTP server in background so the dashboard can read JSON
start "910CPR Supervisor Server" cmd /c "cd /d "%cd%" && python -m http.server 8080"

REM Give the server a moment to start
timeout /t 2 >nul

echo ============================================
echo OPENING DASHBOARD
echo ============================================

start "" http://localhost:8080/supervisor/index.html

echo.
echo ============================================
echo FULL STACK BUILD START
echo ============================================
echo RUNNING FROM:
cd
echo.
if "%COMPLETE_REBUILD%"=="1" (
    echo MODE: COMPLETE REBUILD
    echo EXTRA STEP: python -m scripts.build_index_and_sitemap
) else (
    echo MODE: STANDARD REBUILD
)
echo NOTE: This run does not call python -m scripts.build_sessions_current
echo.

set "BAR_WIDTH=40"
set /a TOTAL_WEIGHT=100
if "%COMPLETE_REBUILD%"=="1" set /a TOTAL_WEIGHT=106
set /a COMPLETED_WEIGHT=0

call :show_progress "Starting build"
echo.

echo ------------------------------------------------
echo RUNNING: Build schedule
echo COMMAND: python -m scripts.build_schedule
echo ------------------------------------------------
call :show_progress "Running Build schedule"
python -m scripts.build_schedule
if errorlevel 1 goto :fail
set /a COMPLETED_WEIGHT+=12
call :show_progress "Completed Build schedule"
echo.

echo ------------------------------------------------
echo RUNNING: Build future schedule
echo COMMAND: python -m scripts.build_schedule_future
echo ------------------------------------------------
call :show_progress "Running Build future schedule"
python -m scripts.build_schedule_future
if errorlevel 1 goto :fail
set /a COMPLETED_WEIGHT+=8
call :show_progress "Completed Build future schedule"
echo.

echo ------------------------------------------------
echo RUNNING: Build class landers (parallel)
echo COMMAND: python -m scripts.build_landers --workers 6
echo ------------------------------------------------
call :show_progress "Running Build class landers"
python -m scripts.build_landers --workers 6
if errorlevel 1 goto :fail
set /a COMPLETED_WEIGHT+=55
call :show_progress "Completed Build class landers"
echo.

echo ------------------------------------------------
echo RUNNING: Build request group session page
echo COMMAND: python -m scripts.build_request_group_session
echo ------------------------------------------------
call :show_progress "Running Build request group session page"
python -m scripts.build_request_group_session
if errorlevel 1 goto :fail
set /a COMPLETED_WEIGHT+=5
call :show_progress "Completed Build request group session page"
echo.

echo ------------------------------------------------
echo RUNNING: Build top-level slug hubs
echo COMMAND: python -m scripts.build_slug_hubs
echo ------------------------------------------------
call :show_progress "Running Build top-level slug hubs"
python -m scripts.build_slug_hubs
if errorlevel 1 goto :fail
set /a COMPLETED_WEIGHT+=5
call :show_progress "Completed Build top-level slug hubs"
echo.

echo ------------------------------------------------
echo RUNNING: Build courses pages
echo COMMAND: python -m scripts.build_courses
echo ------------------------------------------------
call :show_progress "Running Build courses pages"
python -m scripts.build_courses
if errorlevel 1 goto :fail
set /a COMPLETED_WEIGHT+=3
call :show_progress "Completed Build courses pages"
echo.

echo ------------------------------------------------
echo RUNNING: Build location pages
echo COMMAND: python -m scripts.build_locations
echo ------------------------------------------------
call :show_progress "Running Build location pages"
python -m scripts.build_locations
if errorlevel 1 goto :fail
set /a COMPLETED_WEIGHT+=6
call :show_progress "Completed Build location pages"
echo.

echo ------------------------------------------------
echo RUNNING: Build course-at-city pages
echo COMMAND: python -m scripts.build_course_at_city
echo ------------------------------------------------
call :show_progress "Running Build course-at-city pages"
python -m scripts.build_course_at_city
if errorlevel 1 goto :fail
set /a COMPLETED_WEIGHT+=6
call :show_progress "Completed Build course-at-city pages"
echo.

if "%COMPLETE_REBUILD%"=="1" (
echo ------------------------------------------------
echo RUNNING: Build index and sitemap
echo COMMAND: python -m scripts.build_index_and_sitemap
echo ------------------------------------------------
call :show_progress "Running Build index and sitemap"
python -m scripts.build_index_and_sitemap
if errorlevel 1 goto :fail
set /a COMPLETED_WEIGHT+=6
call :show_progress "Completed Build index and sitemap"
echo.
)

call :show_progress "Build complete"
echo ============================================
echo FULL STACK BUILD COMPLETE
echo ============================================
pause
exit /b 0

:fail
echo.
call :show_progress "Build failed"
echo ============================================
echo BUILD FAILED
echo ============================================
pause
exit /b 1

:show_progress
set "STATUS=%~1"
set /a PERCENT=(COMPLETED_WEIGHT*100)/TOTAL_WEIGHT
set /a FILLED=(COMPLETED_WEIGHT*BAR_WIDTH)/TOTAL_WEIGHT
set "BAR="

for /L %%I in (1,1,%BAR_WIDTH%) do (
    if %%I LEQ !FILLED! (
        set "BAR=!BAR!#"
    ) else (
        set "BAR=!BAR!."
    )
)

echo [!BAR!] !PERCENT!%% - !STATUS!
exit /b 0
