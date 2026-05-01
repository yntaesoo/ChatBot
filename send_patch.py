import requests
import os
import sys

TARGET_IP = "192.168.0.103"
TARGET_PORT = "8088"
UPDATE_URL = f"http://{TARGET_IP}:{TARGET_PORT}/update"
ZIP_FILE = "ChatBot_Deploy.zip"

def main():
    print("===================================================")
    print(f" 원격 패치 시스템 (Target: {TARGET_IP})")
    print("===================================================\n")
    
    # 1. build_deploy.py 실행하여 최신 ZIP 생성
    print("[1] 최신 배포본(ZIP) 생성 중...")
    try:
        import build_deploy
        build_deploy.create_deploy_zip()
    except Exception as e:
        print(f"[에러] ZIP 파일 생성 실패: {e}")
        return

    if not os.path.exists(ZIP_FILE):
        print(f"[에러] {ZIP_FILE} 파일을 찾을 수 없습니다.")
        return

    # 2. 서버로 전송
    print(f"\n[2] 타겟 PC({TARGET_IP})로 패치 파일 전송 중...")
    try:
        with open(ZIP_FILE, "rb") as f:
            files = {"file": (ZIP_FILE, f, "application/zip")}
            response = requests.post(UPDATE_URL, files=files, timeout=30)
            
        if response.status_code == 200:
            print(f"\n[성공] 타겟 PC 응답: {response.json().get('message')}")
        else:
            print(f"\n[실패] 서버 오류: {response.status_code} - {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"\n[에러] 타겟 PC({TARGET_IP}:{TARGET_PORT})에 연결할 수 없습니다.")
        print("타겟 PC에서 run_updater.bat 가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"\n[에러] 전송 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
