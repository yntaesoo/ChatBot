@echo off
f:
cd "f:\Create with Claude\ChatBot\backend"
call .venv\Scripts\activate.bat
uvicorn main:app --reload --port 8080
