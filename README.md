# Live2D 웹 챗봇 MVP (LLM+TTS 클라우드, SSE 스트리밍)

이 프로젝트는 **웹 기반**으로 동작하는 캐릭터 챗봇 MVP 뼈대입니다.

- 프론트: `web/` (순수 HTML/JS)
- 백엔드: `backend/` (FastAPI)
- LLM/TTS: 클라우드 API (기본: OpenAI Python SDK)
- 립싱크: 1차는 **오디오 볼륨 기반** (향후 viseme/정렬로 확장 가능)

## 빠른 시작

### 1) 환경변수 준비

`backend/.env.example`을 참고해서 `backend/.env`를 만드세요.

### 2) 백엔드 실행

PowerShell에서 아래를 실행합니다.

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### 3) 브라우저에서 접속

- `http://localhost:8000/`

## Live2D 연결(드롭인 방식)

현재 `web/app.js`는 **Live2D가 없어도 동작**하도록 되어 있고,
Live2D Cubism SDK/Framework를 넣으면 `Live2DAvatarDriver`로 교체할 수 있게 구조를 잡아둔 상태입니다.

다음 두 가지가 준비되면 Live2D로 실캐릭터 구동이 가능합니다.

- Live2D Cubism Web SDK/Framework (라이선스 준수 필요)
- 모델 파일(.model3.json + 텍스처/모션 등)

### Live2D 켜기

기본 화면은 더미 아바타로 동작합니다. Live2D 드라이버를 시도하려면 아래처럼 접속하세요.

- `http://localhost:8000/?live2d=1`

### 모델 위치 규칙(권장)

기본은 `web/assets/live2d/` 아래에 모델 폴더를 두는 방식입니다.

예: 히요리(사용자 제공 `hiyori_free_ko.zip`)를 풀면 아래 경로에 `model3.json`이 있습니다.

- `web/assets/live2d/hiyori/hiyori_free_ko/runtime/hiyori_free_t08.model3.json`

모델 경로를 바꾸고 싶으면 `web/live2d/Live2DAvatarDriver.js`의 `modelUrl` 기본값을 수정하면 됩니다.

## 다음 확장 포인트

- RAG(조직 문서 기반 답변)
- viseme 기반 립싱크(타임스탬프/forced-alignment)
- 3D(VRM) 드라이버 추가 (`AvatarDriver` 인터페이스 유지)

"# ChatBot" 
