import chromadb

def inspect_chromadb():
    print("========================================")
    print("   ChromaDB 데이터베이스 구조 확인")
    print("========================================\n")
    
    try:
        # ChromaDB 클라이언트 로드
        client = chromadb.PersistentClient(path='./chroma_db')
        
        # 컬렉션 가져오기 (기본값: langchain)
        collections = client.list_collections()
        if not collections:
            print("데이터베이스가 비어있습니다. (컬렉션 없음)")
            return
            
        print(f"발견된 컬렉션 개수: {len(collections)}개")
        for c in collections:
            print(f"- {c.name}")
            
        # 첫 번째 컬렉션(주로 langchain) 확인
        collection = client.get_collection(collections[0].name)
        total_count = collection.count()
        print(f"\n총 청크(조각난 문서) 개수: {total_count}개")
        
        if total_count == 0:
            print("컬렉션은 있지만 저장된 데이터가 없습니다.")
            return
            
        # 상위 3개 데이터 샘플 가져오기
        print("\n--- 데이터 샘플 확인 (최대 3개) ---")
        data = collection.peek(3)
        
        for i in range(len(data['documents'])):
            doc = data['documents'][i]
            meta = data['metadatas'][i] if data['metadatas'] else {}
            
            # 출처(파일 이름이나 URL) 가져오기
            source = meta.get("source", "출처 알 수 없음")
            
            print(f"\n[데이터 #{i+1}]")
            print(f"출처: {source}")
            # 텍스트가 너무 길면 잘라서 보여주기
            preview_text = doc[:150].replace('\n', ' ') + "..." if len(doc) > 150 else doc.replace('\n', ' ')
            print(f"내용 미리보기: {preview_text}")
            
        print("\n========================================")
        
    except Exception as e:
        print(f"데이터베이스를 읽는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    inspect_chromadb()
