@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ==================================================
REM 910CPR LANDER MASTER RUNNER
REM Save in repo root
REM ==================================================

set REPO_DIR=D:\Users\ten77\Documents\GitHub\910cpr-class-landers
set VENV_ACTIVATE=%REPO_DIR%\.venv\Scripts\activate.bat
set LOG_DIR=%REPO_DIR%\logs

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set TS=%%i
set LOG_FILE=%LOG_DIR%\run_%TS%.log

call :log ==========================================
call :log 910CPR lander run started
call :log Repo: %REPO_DIR%
call :log Log:  %LOG_FILE%
call :log ==========================================

cd /d "%REPO_DIR%"
if errorlevel 1 (
    call :log ERROR: Could not change to repo directory.
    goto :fail
)

if exist "%VENV_ACTIVATE%" (
    call :log Activating virtual environment...
    call "%VENV_ACTIVATE%" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        call :log ERROR: Failed to activate virtual environment.
        goto :fail
    )
) else (
    call :log WARNING: No virtual environment activate script found. Continuing without venv.
)

REM --------------------------------------------------
REM STEP 1 - Watch Enrollware schedule feed
REM --------------------------------------------------
call :runstep "STEP 1 - Enrollware schedule watcher" python scripts\ew_schedule_watcher.py
if errorlevel 1 goto :fail

REM --------------------------------------------------
REM STEP 2 - Build or update class landers
REM --------------------------------------------------
call :runstep "STEP 2 - Build or update landers" python scripts\build_or_update_landers.py
if errorlevel 1 goto :fail

REM --------------------------------------------------
REM STEP 3 - Rebuild indexes / sitemap
REM --------------------------------------------------
call :runstep "STEP 3 - Build index and sitemap" python scripts\build_index_and_sitemap.py
if errorlevel 1 goto :fail

REM --------------------------------------------------
REM STEP 4 - Optional PowerShell step
REM Uncomment and edit if needed
REM --------------------------------------------------
REM call :runstep "STEP 4 - Optional PowerShell task" powershell -NoProfile -ExecutionPolicy Bypass -File scripts\your_step.ps1
REM if errorlevel 1 goto :fail

call :log SUCCESS: Run completed successfully.
call :log Finished at %date% %time%
exit /b 0

:fail
call :log FAILED: Run stopped due to an error.
call :log Finished at %date% %time%
exit /b 1

:runstep
set STEP_NAME=%~1
shift
call :log.
call :log ==================================================
call :log RUNNING: %STEP_NAME%
call :log COMMAND: %*
call :log ==================================================
%* >> "%LOG_FILE%" 2>&1
set STEP_ERR=%ERRORLEVEL%
if not "%STEP_ERR%"=="0" (
    call :log ERROR: %STEP_NAME% failed with exit code %STEP_ERR%.
    exit /b %STEP_ERR%
)
call :log DONE: %STEP_NAME%
exit /b 0

:log
echo %~1
>> "%LOG_FILE%" echo %~1
exit /b 0