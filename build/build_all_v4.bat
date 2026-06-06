@echo off
setlocal ENABLEDELAYEDEXPANSION

REM ============================================================
REM 910CPR BUILD ALL V4
REM Runs the existing lander generator first, then the V3
REM schedule/index/discovery pipeline.
REM
REM Optional environment variables:
REM   LANDER_CMD=custom command to build class/course landers
REM   SKIP_LANDERS=1 to skip the lander build phase
REM ============================================================

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"

echo.
echo === 910CPR BUILD ALL V4 ===
echo Repo root: %ROOT%
echo.

cd /d "%ROOT%"
if errorlevel 1 (
  echo ERROR: Could not change to repo root.
  exit /b 1
)

if not exist "data" (
  echo ERROR: Missing data folder.
  exit /b 1
)

set "COURSE_XLSX="
if exist "data\course-export.xlsx" set "COURSE_XLSX=data\course-export.xlsx"
if not defined COURSE_XLSX if exist "data\enrollware_export.xlsx" set "COURSE_XLSX=data\enrollware_export.xlsx"

set "CLASS_XLSX="
if exist "data\Class Report.xlsx" set "CLASS_XLSX=data\Class Report.xlsx"
if not defined CLASS_XLSX if exist "data\class-report.xlsx" set "CLASS_XLSX=data\class-report.xlsx"

if not defined COURSE_XLSX (
  echo ERROR: Missing course export in data\.
  echo Expected one of:
  echo   data\course-export.xlsx
  echo   data\enrollware_export.xlsx
  exit /b 1
)

if not defined CLASS_XLSX (
  echo ERROR: Missing class report in data\.
  echo Expected one of:
  echo   data\Class Report.xlsx
  echo   data\class-report.xlsx
  exit /b 1
)

echo Course export: %COURSE_XLSX%
echo Class report : %CLASS_XLSX%
echo.

echo === CONFIG VALIDATION PHASE ===
python "scripts\validate_calendar_sources.py"
if errorlevel 1 (
  echo.
  echo CONFIG VALIDATION FAILED.
  exit /b 1
)
echo.

if "%SKIP_LANDERS%"=="1" goto RUN_INDEX_PIPELINE

echo === LANDER BUILD PHASE ===
if defined LANDER_CMD (
  echo Using LANDER_CMD:
  echo   %LANDER_CMD%
  call %LANDER_CMD%
  if errorlevel 1 (
    echo.
    echo LANDER BUILD FAILED.
    exit /b 1
  )
  goto RUN_INDEX_PIPELINE
)

REM Try known existing repo entry points in safest order.
if exist "run_910cpr_landers.bat" (
  echo Running existing lander builder: run_910cpr_landers.bat
  call ".\run_910cpr_landers.bat"
  if errorlevel 1 (
    echo.
    echo LANDER BUILD FAILED: run_910cpr_landers.bat
    exit /b 1
  )
  goto RUN_INDEX_PIPELINE
)

if exist "run_rebuild.bat" (
  echo Running existing rebuild entry point: run_rebuild.bat
  call ".\run_rebuild.bat"
  if errorlevel 1 (
    echo.
    echo LANDER BUILD FAILED: run_rebuild.bat
    exit /b 1
  )
  goto RUN_INDEX_PIPELINE
)

if exist "run_landers_worker.bat" (
  echo Running existing lander worker: run_landers_worker.bat
  call ".\run_landers_worker.bat"
  if errorlevel 1 (
    echo.
    echo LANDER BUILD FAILED: run_landers_worker.bat
    exit /b 1
  )
  goto RUN_INDEX_PIPELINE
)

echo No existing lander batch file detected.
echo Skipping lander generation and continuing to index pipeline.
echo You can force a command with:
echo   set LANDER_CMD=^".\your_file.bat^"
echo.

:RUN_INDEX_PIPELINE
echo === INDEX / DATA PHASE ===

if exist "build\build_all_v3.bat" (
  call ".\build\build_all_v3.bat"
  if errorlevel 1 (
    echo.
    echo INDEX PIPELINE FAILED.
    exit /b 1
  )
) else (
  echo ERROR: Missing build\build_all_v3.bat
  exit /b 1
)

echo.
echo === CONTROL BOOTH RECEIPT PHASE ===
python "scripts\build_control_booth.py"
if errorlevel 1 (
  echo.
  echo CONTROL BOOTH RECEIPT FAILED.
  echo Public build completed, but debug\control_booth_data.json was not regenerated.
  exit /b 1
)

echo.
echo DONE.
exit /b 0
