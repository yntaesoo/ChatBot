from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


_ENV_PATH = Path(__file__).with_name(".env")
# 항상 backend/.env를 우선 로딩(실행 cwd가 달라도 안정적으로 동작)
load_dotenv(dotenv_path=_ENV_PATH, override=False)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str

    org_name: str
    org_persona_summary: str
    org_forbidden_topics: str

    tts_model: str
    tts_voice: str


def get_settings() -> Settings:
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다. backend/.env를 확인하세요.")

    return Settings(
        openai_api_key=openai_api_key,
        org_name=os.getenv("ORG_NAME", "Your Organization").strip(),
        org_persona_summary=os.getenv(
            "ORG_PERSONA_SUMMARY",
            "친절하고 정확한 조직 공식 안내자. 반말 금지. 과장 금지. 불확실하면 확인 요청.",
        ).strip(),
        org_forbidden_topics=os.getenv(
            "ORG_FORBIDDEN_TOPICS",
            "불법행위 조장, 개인정보 수집(주민번호/계좌/비밀번호), 혐오/폭력 선동, 성적 콘텐츠",
        ).strip(),
        tts_model=os.getenv("TTS_MODEL", "gpt-4o-mini-tts").strip(),
        tts_voice=os.getenv("TTS_VOICE", "alloy").strip(),
    )

