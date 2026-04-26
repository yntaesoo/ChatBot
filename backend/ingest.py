import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import bs4
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

DATA_DIR = "./data"
CHROMA_DB_DIR = "./chroma_db"

import shutil

def main():
    print("문서 로딩 중...")
    
    # 기존 DB가 있다면 중복 방지를 위해 삭제 후 재생성 (전체 동기화 방식)
    if os.path.exists(CHROMA_DB_DIR):
        print("기존 DB 초기화 중 (중복 방지)...")
        shutil.rmtree(CHROMA_DB_DIR)
    
    # 폴더가 없으면 생성
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"[{DATA_DIR}] 폴더가 없어서 생성했습니다. 문서를 넣어주세요.")
        return
        
    # 텍스트 문서 로드
    text_loader = DirectoryLoader(DATA_DIR, glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
    try:
        text_docs = text_loader.load()
    except Exception as e:
        print(f"TXT 로딩 오류 (인코딩 문제일 수 있음): {e}")
        text_docs = []
    
    # PDF 문서 로드
    pdf_loader = DirectoryLoader(DATA_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    try:
        pdf_docs = pdf_loader.load()
    except Exception as e:
        print(f"PDF 로딩 오류: {e}")
        pdf_docs = []
        
    # 웹페이지 문서 로드 (urls.txt 파일이 있을 경우)
    web_docs = []
    urls_file_path = os.path.join(DATA_DIR, "urls.txt")
    if os.path.exists(urls_file_path):
        try:
            with open(urls_file_path, "r", encoding="utf-8") as f:
                urls = []
                for line in f:
                    # '#' 기호가 있으면 그 이후는 주석으로 간주하고 잘라냄
                    if "#" in line:
                        line = line.split("#")[0]
                    
                    cleaned_line = line.strip()
                    if cleaned_line:
                        urls.append(cleaned_line)
            
            if urls:
                print(f"{len(urls)}개의 웹페이지 URL을 수집합니다...")
                web_loader = WebBaseLoader(
                    web_paths=urls,
                    bs_kwargs=dict(parse_only=bs4.SoupStrainer(
                        # 본문과 무관한 헤더/푸터/네비게이션 태그 등을 제외하고 텍스트 추출
                        # 특정 태그만 추출하고 싶다면 여기서 필터링 가능합니다. (현재는 전체에서 불필요 요소 제거)
                    ))
                )
                web_docs = web_loader.load()
                print(f"웹페이지 수집 완료: {len(web_docs)} 페이지")
        except Exception as e:
            print(f"웹페이지 로딩 오류: {e}")
    
    docs = text_docs + pdf_docs + web_docs

    if not docs:
        print(f"[{DATA_DIR}] 폴더에 학습할 문서가 없습니다.")
        return

    print(f"총 {len(docs)}개의 문서를 찾았습니다.")

    # 텍스트 청킹 (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    chunks = text_splitter.split_documents(docs)
    print(f"문서를 {len(chunks)}개의 조각으로 나누었습니다.")

    # 벡터화 및 DB 저장
    print("벡터 DB(Chroma) 생성 및 저장 중...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    print(f"DB 저장 완료! 위치: {CHROMA_DB_DIR}")

if __name__ == "__main__":
    main()
