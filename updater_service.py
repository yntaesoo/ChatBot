import os
import zipfile
import shutil
import subprocess
import time
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

def kill_main_server():
    print("기존 챗봇 서버(uvicorn)를 종료합니다...")
    # uvicorn main:app 프로세스를 찾아 강제 종료합니다.
    try:
        subprocess.run(
            'wmic process where "name=\'python.exe\' and commandline like \'%uvicorn%main:app%\'" delete', 
            shell=True, capture_output=True
        )
        time.sleep(2)  # 프로세스가 완전히 죽을 때까지 대기
    except Exception as e:
        print(f"서버 종료 중 에러: {e}")

def start_main_server():
    print("챗봇 서버를 다시 시작합니다...")
    try:
        # start 명령어를 사용하여 새로운 cmd 창에서 run.bat을 실행시킵니다.
        subprocess.Popen("start cmd /c run.bat", shell=True)
    except Exception as e:
        print(f"서버 시작 중 에러: {e}")

@app.post("/update")
async def receive_update(file: UploadFile = File(...)):
    print(f"업데이트 파일 수신: {file.filename}")
    
    # 1. 파일 저장
    temp_zip_path = "temp_update.zip"
    with open(temp_zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. 메인 서버 종료
    kill_main_server()
    
    # 3. 압축 해제 및 덮어쓰기
    print("업데이트 압축 해제 중...")
    try:
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            # 타겟 PC의 루트 폴더에 그대로 덮어씁니다.
            zip_ref.extractall(".")
            
        print("파일 덮어쓰기 완료!")
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"압축 해제 실패: {e}"})
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
            
    # 4. (선택) requirements.txt 변경 시 재설치 로직
    # 백그라운드 환경이므로 install.bat을 전체 실행하기보다는 
    # run.bat이 실행될 때 필요한 패키지가 알아서 설치되도록 가이드하는 것이 좋습니다.
    # 하지만 일단 여기서는 단순히 메인 서버만 재시작합니다.
    
    # 5. 메인 서버 재시작
    start_main_server()
    
    return {"message": "업데이트가 성공적으로 적용되고 서버가 재시작되었습니다!"}

if __name__ == "__main__":
    print("=========================================")
    print(" 원격 자동 업데이트 서비스 가동 중...")
    print(" 포트: 8088")
    print("=========================================")
    uvicorn.run(app, host="0.0.0.0", port=8088)
