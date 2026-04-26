from __future__ import annotations

from typing import Iterable, List, Dict, Any

from openai import OpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from config import Settings

_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        try:
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            _vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
        except Exception as e:
            print("ChromaDB 로드 오류:", e)
    return _vectorstore


def build_system_prompt(settings: Settings, language: str = "한국어", context: str = "") -> str:
    prompt = (
        f"너는 {settings.org_name}의 공식 챗봇이다.\n"
        f"페르소나: {settings.org_persona_summary}\n"
        "규칙:\n"
        f"- {language}로 답한다.\n"
        "- 존댓말을 사용한다.\n"
        "- 불확실한 내용은 추측하지 말고, 필요한 정보를 질문하거나 '확인 필요'라고 말한다.\n"
        f"- 다음 주제는 거절한다: {settings.org_forbidden_topics}\n"
        "- 개인정보(비밀번호, 주민등록번호, 계좌, 인증코드 등)를 요구하지 않는다.\n"
    )
    
    if context:
        prompt += (
            "\n[중요 지침]\n"
            "아래 제공된 [검색된 문서 내용]을 반드시 바탕으로 대답해. 내용에 없는 사실은 지어내지 마.\n"
            "\n[검색된 문서 내용]\n"
            f"{context}\n"
        )
        
    return prompt


def stream_chat_completion(
    *,
    client: OpenAI,
    settings: Settings,
    messages: List[Dict[str, Any]],
    model: str = "gpt-4o-mini",
    language: str = "한국어",
) -> Iterable[str]:
    user_query = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_query = msg.get("content", "")
            break

    context = ""
    if user_query:
        vs = get_vectorstore()
        if vs:
            try:
                docs = vs.similarity_search(user_query, k=3)
                context = "\n\n".join([f"- {doc.page_content}" for doc in docs])
            except Exception as e:
                print("RAG 검색 오류:", e)

    sys = {"role": "system", "content": build_system_prompt(settings, language, context)}
    req_messages = [sys, *messages]

    stream = client.chat.completions.create(
        model=model,
        messages=req_messages,
        temperature=0.6,
        stream=True,
    )

    for event in stream:
        delta = event.choices[0].delta
        if delta and getattr(delta, "content", None):
            yield delta.content

