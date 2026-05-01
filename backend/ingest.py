import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import bs4
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_classic.indexes import SQLRecordManager, index

load_dotenv()

DATA_DIR = "./data"
CHROMA_DB_DIR = "./chroma_db"
RECORD_MANAGER_DB_URL = f"sqlite:///{DATA_DIR}/record_manager.db"

def main():
    print("문서 로딩 중...")
    
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
                urls_with_depth = []
                for line in f:
                    # '#' 기호가 있으면 그 이후는 주석으로 간주하고 잘라냄
                    if "#" in line:
                        line = line.split("#")[0]
                    
                    cleaned_line = line.strip()
                    if cleaned_line:
                        # " : " 분리해서 depth 추출 (기본값 1)
                        depth = 1
                        if ":" in cleaned_line:
                            parts = cleaned_line.rsplit(":", 1)
                            if len(parts) == 2 and parts[1].strip().isdigit():
                                url = parts[0].strip()
                                depth = int(parts[1].strip())
                            else:
                                url = cleaned_line
                        else:
                            url = cleaned_line
                            
                        urls_with_depth.append((url, depth))
            
            if urls_with_depth:
                from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
                import re

                def bs4_extractor(html: str) -> str:
                    soup = bs4.BeautifulSoup(html, "html.parser")
                    return re.sub(r"\n\n+", "\n\n", soup.text).strip()
                    
                print(f"{len(urls_with_depth)}개의 웹페이지 설정 발견. 하위 링크 수집을 진행합니다...")
                for url, depth in urls_with_depth:
                    print(f"- 수집 중: {url} (탐색 깊이: {depth})")
                    loader = RecursiveUrlLoader(
                        url=url,
                        max_depth=depth,
                        extractor=bs4_extractor,
                        prevent_outside=True
                    )
                    web_docs.extend(loader.load())
                print(f"웹페이지 수집 완료: 총 {len(web_docs)} 개의 문서 조각 생성됨")
        except Exception as e:
            print(f"웹페이지 로딩 오류: {e}")
    
    docs = text_docs + pdf_docs + web_docs

    if not docs:
        print(f"[{DATA_DIR}] 폴더에 학습할 문서가 없습니다.")
        return

    print(f"총 {len(docs)}개의 원본 문서를 찾았습니다.")

    # 텍스트 청킹 (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    chunks = text_splitter.split_documents(docs)
    print(f"문서를 {len(chunks)}개의 조각으로 나누었습니다.")

    # 디버그용 RAG 데이터 저장
    debug_file_path = os.path.join(DATA_DIR, "rag_debug_chunks.txt")
    try:
        with open(debug_file_path, "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks):
                f.write(f"--- Chunk {i+1} ---\n")
                f.write(f"Source: {chunk.metadata.get('source', 'Unknown')}\n")
                f.write(f"Content:\n{chunk.page_content}\n\n")
        print(f"디버깅용 텍스트 파일 저장 완료: {debug_file_path}")
    except Exception as e:
        print(f"디버그 파일 저장 실패: {e}")

    # 벡터 DB 클라이언트 및 임베딩 설정
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name="langchain",
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

    # RecordManager 설정 (증분 업데이트 추적용)
    namespace = f"chromadb/langchain"
    record_manager = SQLRecordManager(
        namespace, db_url=RECORD_MANAGER_DB_URL
    )
    record_manager.create_schema()

    # 인덱싱 (변경사항만 업데이트)
    print("\n벡터 DB(Chroma) 증분 업데이트 시작...")
    indexing_result = index(
        chunks,
        record_manager,
        vectorstore,
        cleanup="full",
        source_id_key="source"
    )
    
    print("\n[업데이트 결과]")
    print(f"- 새롭게 추가된 조각: {indexing_result['num_added']} 개")
    print(f"- 내용이 수정된 조각: {indexing_result['num_updated']} 개")
    print(f"- 변동 없어 건너뜀: {indexing_result['num_skipped']} 개")
    print(f"- 삭제된 조각: {indexing_result['num_deleted']} 개")
    print(f"\nDB 저장 완료! 위치: {CHROMA_DB_DIR}")

if __name__ == "__main__":
    main()
