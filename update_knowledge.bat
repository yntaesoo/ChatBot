@echo off
echo ===================================================
echo     IC ChatBot Knowledge Base (Vector DB) Update
echo ===================================================
echo.
echo [INFO] Scanning backend\data folder for new or modified documents...
echo Injecting data into ChromaDB. Please wait...
echo.

cd /d "%~dp0backend"
call .venv\Scripts\activate.bat
python ingest.py

echo.
echo ===================================================
echo Training successfully completed!
echo You can now close this window. The chatbot will use the new knowledge immediately.
echo ===================================================
pause
