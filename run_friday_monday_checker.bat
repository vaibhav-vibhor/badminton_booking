@echo off
echo ======================================================================
echo 🏸 NEXT FRIDAY & MONDAY BADMINTON SLOT CHECKER
echo ======================================================================
echo Checking the next upcoming Friday and Monday only (2 dates total)...
echo.

cd /d "%~dp0"
python friday_monday_checker.py

echo.
echo ======================================================================
echo Checker completed. Press any key to exit...
pause > nul
