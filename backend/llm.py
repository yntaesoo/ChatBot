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


def extract_search_query(client: OpenAI, user_query: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "사용자의 질문에서 문서 검색을 위한 핵심 명사(키워드)만 추출하세요. 일상어(알려줘, 뭐야 등)는 제거하고 띄어쓰기를 명확히 하세요. 필요한 경우 영단어(Visa 등)를 병기하세요. (예: '비자연장 절차 좀 알려줘' -> '비자 연장 절차 Visa'). 결과만 출력하세요."
                },
                {"role": "user", "content": user_query}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("키워드 추출 오류:", e)
        return user_query  # 실패 시 원본 쿼리 반환


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
        # 1. 쿼리 재작성 (검색 정확도 향상)
        search_query = extract_search_query(client, user_query)
        print(f"[RAG] 원본 질문: '{user_query}' -> 검색 키워드: '{search_query}'")
        
        vs = get_vectorstore()
        if vs:
            try:
                # 2. k 개수를 늘려 문맥 다양성 확보
                docs = vs.similarity_search(search_query, k=5)
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

