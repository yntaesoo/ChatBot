# 학습 데이터 업로드 및 학습 기능 추가

신규 학습 데이터를 업로드하고 챗봇(ChromaDB)을 재학습시킬 수 있는 기능을 구현합니다. 관리자만 학습을 실행할 수 있도록 비밀번호 암호화 처리를 포함합니다.

## User Review Required

> [!IMPORTANT]
> - 기본 관리자 비밀번호를 환경변수(`backend/.env`의 `ADMIN_PASSWORD`)로 관리하고자 합니다. `.env` 파일에 비밀번호가 없으면 기본값인 `admin1234`가 사용됩니다.
> - 업로드 된 파일은 `backend/data` 폴더에 바로 저장되고, URL은 `backend/data/urls.txt` 파일에 추가됩니다.

## Proposed Changes

### Backend

#### [MODIFY] [config.py](file:///f:/Create%20with%20Claude/ChatBot/backend/config.py)
- `Settings` 클래스에 `admin_password` 추가 (기본값: "admin1234")

#### [MODIFY] [main.py](file:///f:/Create%20with%20Claude/ChatBot/backend/main.py)
- **POST `/api/upload`**: PDF 및 TXT 파일을 `backend/data/` 디렉터리에 저장.
- **POST `/api/train`**: URL 목록과 `password`를 받아 인증을 수행.
  - 비밀번호가 올바르면 URL을 `data/urls.txt`에 기록
  - `python ingest.py` 서브프로세스를 실행하여 학습(Vector DB 업데이트) 진행.

---

### Frontend

#### [MODIFY] [index.html](file:///f:/Create%20with%20Claude/ChatBot/web/index.html)
- 상단 네비게이션 헤더(topbar)에 **"학습 데이터 관리"** 버튼 추가.
- 모달(Modal) 창 추가:
  - 파일 업로드 영역 (PDF, TXT 선택 가능)
  - URL 입력 텍스트 영역
  - 관리자 비밀번호 입력 필드
  - "업로드 및 학습" 버튼

#### [MODIFY] [style.css](file:///f:/Create%20with%20Claude/ChatBot/web/style.css)
- 모달 창과 오버레이 백그라운드 등 UI 디자인 스타일 추가 (어두운 테마 및 깔끔한 입력 폼)

#### [MODIFY] [app.js](file:///f:/Create%20with%20Claude/ChatBot/web/app.js)
- 모달 열기/닫기 로직 구현
- 선택된 파일 및 URL 수집
- `/api/upload`로 파일을 먼저 전송하고, 성공하면 `/api/train`으로 URL과 비밀번호 전송
- 학습 진행 상태 표시(로딩 표시) 및 결과 Alert 제공

## Verification Plan

### Manual Verification
1. 프론트엔드에서 "학습 데이터 관리" 메뉴 클릭 시 모달이 제대로 뜨는지 확인.
2. PDF, TXT 파일을 선택하고 URL을 입력한 뒤 잘못된 비밀번호를 입력 시 "비밀번호가 틀렸습니다" 에러가 뜨는지 확인.
3. 올바른 비밀번호를 입력하면 `backend/data/` 폴더에 파일이 저장되고, `urls.txt`가 업데이트 되며, 백그라운드에서 `ingest.py`가 실행되어 챗봇이 새로운 지식을 사용할 수 있는지 확인.
