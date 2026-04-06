
@echo off
setlocal

set COURSE_XLS=course-export.xlsx
set CLASS_XLS=Class Report.xlsx

if not exist "%COURSE_XLS%" (
  echo Missing %COURSE_XLS%
  exit /b 1
)

if not exist "%CLASS_XLS%" (
  echo Missing %CLASS_XLS%
  exit /b 1
)

python build_schedule_json.py --course-export "%COURSE_XLS%" --class-report "%CLASS_XLS%" --output "docs\data\schedule.json" || exit /b 1
python build_sessions_current.py --schedule-json "docs\data\schedule.json" --output "docs\data\sessions_current.json" || exit /b 1
python build_index_v2.py --schedule-json "docs\data\schedule.json" --output-dir "docs" || exit /b 1
python build_discovery_v2.py --schedule-json "docs\data\schedule.json" --output-html "docs\discovery.html" || exit /b 1

echo Done.
endlocal
