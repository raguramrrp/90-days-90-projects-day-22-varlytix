@echo off
REM SIGMORA - Application Launch Script
echo ========================================================
echo   SIGMORA -- Portfolio Risk Intelligence Platform
echo   Launching Streamlit Quantitative Analytics Terminal...
echo ========================================================

cd /d "%~dp0"

IF NOT EXIST ".venv\Scripts\streamlit.exe" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

set PYTHONPATH=%~dp0
call .venv\Scripts\activate.bat
streamlit run app.py --server.port 8501 --server.headless false

pause
