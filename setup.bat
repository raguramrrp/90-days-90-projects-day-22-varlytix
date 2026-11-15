@echo off
REM SIGMORA - Environment Setup Script
echo ========================================================
echo   SIGMORA -- Automated Environment Setup (Windows)
echo ========================================================

cd /d "%~dp0"

IF NOT EXIST ".venv" (
    echo [*] Creating Python 3.12 virtual environment...
    python -m venv .venv
)

echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [*] Upgrading pip...
python -m pip install --upgrade pip

echo [*] Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo [*] Initializing database and seeding synthetic demo data...
set PYTHONPATH=%~dp0
python scripts\seed_demo_data.py

echo [*] Running automated tests...
pytest tests -q

echo ========================================================
echo [SUCCESS] SIGMORA setup completed successfully.
echo Run 'run.bat' or 'streamlit run app.py' to launch.
echo ========================================================
pause
