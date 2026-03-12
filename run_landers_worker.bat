@echo off
echo ==========================================
echo 910CPR AUTOMATED LANDER BUILDER
echo ==========================================

cd /d D:\Users\ten77\Documents\GitHub\910cpr-class-landers

echo Running master builder...

python scripts\build_all.py

echo.
echo Pushing updates to GitHub...

git add .
git commit -m "auto rebuild"
git push

echo.
echo ==========================================
echo BUILD COMPLETE
echo ==========================================

pause