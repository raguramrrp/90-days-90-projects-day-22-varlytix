@echo off
REM SIGMORA - Test Suite Runner
echo ========================================================
echo   SIGMORA -- Automated Quantitative Test Suite
echo ========================================================

cd /d "%~dp0"
set PYTHONPATH=%~dp0
call .venv\Scripts\activate.bat

pytest tests -v --durations=10

pause
