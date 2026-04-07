@echo off
echo.
echo ================================
echo   910CPR SESSION BUILDER
echo ================================
echo.

cd /d %~dp0\..

echo Running Python builder...
python build\build_sessions.py

echo.
echo DONE.
pause