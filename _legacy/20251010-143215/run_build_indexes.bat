@echo off
pushd "%~dp0"
py scripts\build_indexes.py
set EC=%ERRORLEVEL%
popd
pause
exit /b %EC%
