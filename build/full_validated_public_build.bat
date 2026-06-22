@echo off
setlocal EnableExtensions

cd /d "%~dp0.."
if errorlevel 1 exit /b 1

echo.
echo ========================================
echo 910CPR VALIDATED PUBLIC BUILD START
echo ========================================
echo Repo: %CD%
echo.

if not exist "scripts\generate_dynamic_offers.py" (
    echo ERROR: This does not look like the 910CPR lander repo.
    exit /b 1
)

echo.
echo === Build current sessions from Enrollware iCal ===
python -m scripts.build_sessions_current || goto :fail

echo.
echo === Build public future schedule ===
python -m scripts.build_schedule_future || goto :fail

echo.
echo === Build class lander pages ===
python -m scripts.build_landers || goto :fail

echo.
echo === Generate dynamic offers ===
python -m scripts.generate_dynamic_offers || goto :fail

echo.
echo === Filter public sellable offers ===
python -m scripts.filter_public_sellable_offers || goto :fail

echo.
echo === Select schedule seeds ===
python -m scripts.select_schedule_seeds || goto :fail

echo.
echo === Build seed appointment URL preview ===
python -m scripts.build_seed_appointment_url_preview || goto :fail

echo.
echo === Build slug hubs ===
python -m scripts.build_slug_hubs || goto :fail

echo.
echo === Build index and sitemap ===
python -m scripts.build_index_and_sitemap || goto :fail

echo.
echo === Ensure analytics tags ===
python -m scripts.ensure_analytics_tags || goto :fail

echo.
echo === Run unit tests ===
python -m unittest discover tests || goto :fail

echo.
echo ========================================
echo 910CPR VALIDATED PUBLIC BUILD COMPLETE
echo ========================================
echo.
git status --short
exit /b 0

:fail
echo.
echo ========================================
echo 910CPR VALIDATED PUBLIC BUILD FAILED
echo ========================================
exit /b 1
