@echo off

cd /d E:\GitHub\910cpr-class-landers

echo.
echo =================================
echo 910CPR STACK RUN STARTING
echo =================================
echo.

git pull

echo.
echo Building sessions_current.json...
python scripts\build_sessions_current.py

echo.
echo Building schedule_future.json...
python scripts\build_schedule_future.py

echo.
echo Building slug hubs...
python scripts\build_slug_hubs.py

echo.
echo Building Control Booth...
python scripts\build_control_booth.py

echo.
echo Building index + sitemap...
python scripts\build_index_and_sitemap.py

if exist scripts\build_metadata.py (
    echo.
    echo Building metadata...
    python scripts\build_metadata.py
)

if exist scripts\stamp_generated_html.py (
    echo.
    echo Stamping generated HTML...
    python scripts\stamp_generated_html.py
)

echo.
echo =================================
echo GIT STATUS
echo =================================

git status

echo.
set /p START_PREVIEW=Start local preview server and open test pages? (Y/N): 
if /I "%START_PREVIEW%"=="Y" (
    cd /d "%~dp0"
    start "" "http://localhost:8000/debug/control-booth.html"
    start "" "http://localhost:8000/docs/bls.html"
    start "" "http://localhost:8000/docs/acls.html"
    start "" "http://localhost:8000/docs/pals.html"
    start "" "http://localhost:8000/docs/heartsaver.html"
    start "" "http://localhost:8000/docs/uscg-elementary-first-aid-cpr.html"
    echo.
    echo Press CTRL+C or close this window to stop the server.
    python -m http.server 8000
)

REM OPTIONAL:
REM git add .
REM git commit -m "Nightly stack rebuild"
REM git push

echo.
echo =================================
echo STACK COMPLETE
echo =================================
echo.

pause
