@echo off
chcp 65001 > nul
echo ===================================================
echo     IC ChatBot 지식 베이스(Vector DB) 업데이트
echo ===================================================
echo.
echo [안내] backend\data 폴더에 추가/수정된 문서를 스캔하여
echo 챗봇의 뇌(ChromaDB)에 주입합니다. 잠시만 기다려주세요...
echo.

cd backend
call .venv\Scripts\activate.bat
python ingest.py

echo.
echo ===================================================
echo 학습이 모두 완료되었습니다! 
echo 이제 창을 닫으셔도 되며, 챗봇은 새로 배운 내용을 바로 사용합니다.
echo ===================================================
pause
