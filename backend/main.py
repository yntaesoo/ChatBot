from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from config import get_settings
from llm import stream_chat_completion
from tts import synthesize_speech_mp3


app = FastAPI()

class _NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp = await call_next(request)
        # 개발 중 캐시로 인해 JS가 갱신되지 않는 문제 방지
        if request.url.path == "/" or request.url.path.startswith("/static/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

app.add_middleware(_NoCacheMiddleware)

app.mount("/static", StaticFiles(directory="../web", html=False), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return FileResponse("../web/index.html")


@app.get("/sandbox", response_class=HTMLResponse)
def sandbox() -> HTMLResponse:
    # Live2D 렌더링 최소 재현(현재 앱 코드와 분리)
    return FileResponse("../web/sandbox.html")


def sse_event(data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
async def chat_stream(request: Request) -> StreamingResponse:
    """
    SSE로 LLM 텍스트를 스트리밍한다.
    프론트는 누적 텍스트를 표시하고, 필요 시 문장 단위로 TTS를 호출해 오디오 큐를 만든다.
    """
    try:
        settings = get_settings()
    except Exception as e:
        # 프론트가 "res.ok"를 통과하고 SSE로 에러 메시지를 받도록 200으로 반환한다.
        return StreamingResponse(
            iter([sse_event({"type": "error", "message": str(e)})]),
            media_type="text/event-stream",
        )

    body = await request.json()

    messages: List[Dict[str, Any]] = body.get("messages") or []
    model: str = (body.get("model") or "gpt-4o-mini").strip()
    language: str = (body.get("language") or "한국어").strip()

    client = OpenAI(api_key=settings.openai_api_key)

    def gen():
        try:
            yield sse_event({"type": "meta", "model": model})
            for chunk in stream_chat_completion(
                client=client,
                settings=settings,
                messages=messages,
                model=model,
                language=language,
            ):
                yield sse_event({"type": "delta", "text": chunk})
            yield sse_event({"type": "done"})
        except Exception as e:
            yield sse_event({"type": "error", "message": str(e)})

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/api/tts")
async def tts(request: Request) -> Response:
    try:
        settings = get_settings()
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    body = await request.json()
    text: str = body.get("text") or ""
    voice: str = body.get("voice") or settings.tts_voice

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        mp3 = synthesize_speech_mp3(client=client, settings=settings, text=text, voice=voice)
        return Response(content=mp3, media_type="audio/mpeg")
    except Exception as e:
        # 프론트가 원인을 볼 수 있도록 메시지를 내려준다.
        return JSONResponse(status_code=500, content={"error": str(e)})

