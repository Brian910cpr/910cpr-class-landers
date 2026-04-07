@echo off
setlocal
set "ROOT=%~dp0.."
pushd "%ROOT%"

echo.
echo === 910CPR BUILD ALL V3 ===
echo Repo root: %CD%
echo.

if not exist "data\course-export.xlsx" (
  echo ERROR: Missing data\course-export.xlsx
  goto :fail
)

if not exist "data\Class Report.xlsx" (
  echo ERROR: Missing data\Class Report.xlsx
  goto :fail
)

python "scripts\build_schedule_json.py" --course-export "data\course-export.xlsx" --class-report "data\Class Report.xlsx" --output "data\schedule.json"
if errorlevel 1 goto :fail

python "scripts\build_sessions_current.py" --schedule-json "data\schedule.json" --output "data\sessions_current.json"
if errorlevel 1 goto :fail

python "scripts\build_index.py" --schedule-json "data\schedule.json" --output-dir "docs"
if errorlevel 1 goto :fail

python "scripts\build_discovery.py" --schedule-json "data\schedule.json" --output-html "docs\schedule.html"
if errorlevel 1 goto :fail

echo.
echo DONE.
echo.
popd
exit /b 0

:fail
echo.
echo BUILD FAILED.
echo.
popd
exit /b 1
