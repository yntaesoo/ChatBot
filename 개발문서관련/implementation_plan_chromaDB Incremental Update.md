# ChromaDB 증분 업데이트(Incremental Update) 구현 계획

매번 DB를 초기화하고 모든 문서를 다시 임베딩하는 방식은 문서가 많아질수록 시간과 API 비용이 기하급수적으로 증가합니다. 이를 해결하기 위해 LangChain의 **Indexing API**와 **SQLRecordManager**를 도입하여 변경된 부분만 똑똑하게 업데이트하도록 개선합니다.

## User Review Required
> [!IMPORTANT]
> 이 변경사항을 적용하면 기존의 전체 삭제 로직(`shutil.rmtree`)이 제거되고, `record_manager.db`라는 작은 SQLite 파일이 생성되어 각 문서의 해시(Hash)값과 변경 내역을 추적하게 됩니다.
> 파일이 삭제되거나 내용이 변경된 경우만 감지해서 DB를 수정하므로 속도가 매우 빨라집니다.
> **진행해도 될지 확인 부탁드립니다.**

## Proposed Changes

### 백엔드 (Backend)

#### [MODIFY] [ingest.py](file:///f:/Create%20with%20Claude/ChatBot/backend/ingest.py)
1. **의존성 추가:** `from langchain.indexes import SQLRecordManager, index` 추가
2. **기존 삭제 로직 제거:** `if os.path.exists(CHROMA_DB_DIR): shutil.rmtree(...)` 부분 삭제
3. **RecordManager 도입:** 문서의 상태(추가, 수정, 삭제)를 추적할 `SQLRecordManager` 인스턴스 생성
4. **인덱싱(Indexing) 적용:** `Chroma.from_documents()` 대신 `index()` 함수를 사용하여 `cleanup="full"` 모드로 동기화. 
   - `cleanup="full"`: 현재 폴더에 없는 문서(삭제된 파일)는 DB에서도 지우고, 내용이 바뀐 문서만 재학습하는 모드입니다.

## Verification Plan

### 수동 검증 (Manual Verification)
1. 코드를 수정한 뒤 `update_knowledge.bat`을 실행합니다. (최초 실행 시 전체 인덱싱 됨)
2. `update_knowledge.bat`을 **아무 수정 없이 한 번 더 실행**합니다. 
   - 콘솔 출력에 `{'num_added': 0, 'num_updated': 0, 'num_skipped': N, 'num_deleted': 0}` 형태로 모든 문서가 스킵(Skipped)되는지 확인합니다. (비용 0원)
3. `data/urls.txt` 에 주소를 하나 추가하고 다시 실행하여 `num_added` 만 증가하는지 확인합니다.
