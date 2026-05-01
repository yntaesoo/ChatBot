@echo off
echo ===================================================
echo ChatBot Installation and Environment Setup
echo ===================================================

echo.
echo [1] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.10+ and run this script again.
    pause
    exit /b 1
)

cd backend

echo.
echo [2] Creating virtual environment (.venv)...
if not exist .venv (
    python -m venv .venv
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

echo.
echo [3] Installing required libraries...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo [4] Checking environment configuration (.env)...
if not exist .env (
    echo OPENAI_API_KEY=your_api_key_here > .env
    echo ADMIN_PASSWORD=admin1234 >> .env
    echo .env file has been created. Please replace your_api_key_here with your actual key.
) else (
    echo .env file already exists.
)

echo.
echo ===================================================
echo Installation Complete!
echo You can now go back to the parent folder and run run.bat
echo ===================================================
pause
