@echo off
echo Starting Remote Auto-Update Service...
cd /d "%~dp0backend"
call .venv\Scripts\activate.bat
cd ..
python updater_service.py
pause
