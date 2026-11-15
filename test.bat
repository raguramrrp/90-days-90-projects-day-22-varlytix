@echo off
REM VARLYTIX - Test Suite Runner
echo ========================================================
echo   VARLYTIX -- Automated Quantitative Test Suite
echo ========================================================

cd /d "%~dp0"
set PYTHONPATH=%~dp0
call .venv\Scripts\activate.bat

pytest tests -v --durations=10

pause
