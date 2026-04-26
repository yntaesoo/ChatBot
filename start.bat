@echo off
chcp 65001 > nul
echo Live2D ChatBot 서버를 시작합니다...

:: 1. backend 폴더로 이동
cd backend

:: 2. Uvicorn 서버 백그라운드 실행
start cmd /k "uvicorn main:app"

:: 3. 서버가 켜질 시간을 2초 정도 기다린 후 브라우저 열기
timeout /t 2 /nobreak > nul
start http://localhost:8080
