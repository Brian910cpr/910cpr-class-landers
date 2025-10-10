@echo on
setlocal enabledelayedexpansion

rem Root folder where output HTML goes (docs\past)
set "ROOT=D:\Users\ten77\Documents\GitHub\910cpr-class-landers\docs"

rem Inputs (CSV only; no pandas)
set "ENROLLCSV=D:\Users\ten77\Documents\GitHub\910cpr-class-landers\data\Enrollware_Courses_with_HOVN_Matches.csv"
set "HOVNCSV=D:\Users\ten77\Documents\GitHub\910cpr-class-landers\data\course-offerings (6).csv"
set "COURSEEXPORT="

pushd D:\Users\ten77\Documents\GitHub\910cpr-class-landers || goto :fail

rem Show that the script actually exists
dir ".\tools\build_past_class_landers_nopandas.py"

where py >nul 2>&1
if errorlevel 1 (
  where python || (echo Python not found in PATH & goto :fail)
  set "PYEXE=python"
) else (
  set "PYEXE=py -3"
)

%PYEXE% ".\tools\build_past_class_landers_nopandas.py" ^
  --root "%ROOT%" ^
  --enrollware_csv "%ENROLLCSV%" ^
  --hovn_csv "%HOVNCSV%" ^
  --course_export "%COURSEEXPORT%"

if errorlevel 1 goto :fail

echo.
echo ===== SUCCESS =====
echo Output is in: %ROOT%\past
echo.
pause
popd
exit /b 0

:fail
echo.
echo ===== FAILED =====
echo Check that tools\build_past_class_landers_nopandas.py exists and input CSV paths are correct.
echo.
pause
popd
exit /b 1
