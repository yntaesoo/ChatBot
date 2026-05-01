@echo off
echo Starting Remote Patch Process...
cd /d "%~dp0backend"
call .venv\Scripts\activate.bat
cd ..
python send_patch.py
pause
