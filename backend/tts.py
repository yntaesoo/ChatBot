from __future__ import annotations

from openai import OpenAI

from config import Settings


def synthesize_speech_mp3(*, client: OpenAI, settings: Settings, text: str, voice: str = None) -> bytes:
    """
    TTS는 클라우드 API로 생성하고, 프론트는 오디오 재생 + (1차) 볼륨 기반 립싱크를 수행한다.
    향후 viseme/타임스탬프가 가능한 공급자나 forced-alignment를 붙여 확장할 수 있다.
    """
    text = (text or "").strip()
    if not text:
        return b""

    # OpenAI Python SDK는 버전에 따라 반환 형태가 약간 다를 수 있어 방어적으로 처리한다.
    resp = client.audio.speech.create(
        model=settings.tts_model,
        voice=voice or settings.tts_voice,
        input=text,
        response_format="mp3",
    )

    if hasattr(resp, "read"):
        return resp.read()
    if hasattr(resp, "content") and isinstance(resp.content, (bytes, bytearray)):
        return bytes(resp.content)
    if isinstance(resp, (bytes, bytearray)):
        return bytes(resp)

    # 마지막 fallback
    data = getattr(resp, "data", None)
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)

    raise RuntimeError("TTS 응답을 mp3 bytes로 변환할 수 없습니다(라이브러리 버전 확인 필요).")

