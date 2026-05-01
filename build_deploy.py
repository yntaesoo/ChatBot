import os
import zipfile

def create_deploy_zip():
    output_filename = "ChatBot_Deploy.zip"
    
    # 제외할 폴더 및 파일 패턴
    exclude_dirs = {'.venv', '__pycache__', 'chroma_db', '.git', '.vscode', '.gemini', 'build', 'dist'}
    exclude_files = {
        output_filename, 
        'build_deploy.py', 
        '.env', 
        'record_manager.db',
        'rag_debug_chunks.txt'
    }
    
    # 포함할 주요 디렉토리/파일
    # 루트에 있는 스크립트와 backend, web 폴더만 포함
    include_paths = ['backend', 'web', 'run.bat', 'install.bat', 'update_knowledge.bat']
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for path in include_paths:
            if not os.path.exists(path):
                print(f"[경고] {path} 를 찾을 수 없습니다.")
                continue
                
            if os.path.isfile(path):
                if os.path.basename(path) not in exclude_files:
                    zipf.write(path, path)
                    print(f"Added: {path.encode('utf-8', 'replace').decode('cp949', 'ignore')}")
            else:
                for root, dirs, files in os.walk(path):
                    # 제외 폴더 제거
                    dirs[:] = [d for d in dirs if d not in exclude_dirs]
                    
                    for file in files:
                        if file in exclude_files:
                            continue
                            
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, file_path)
                        print(f"Added: {file_path.encode('utf-8', 'replace').decode('cp949', 'ignore')}")
                        
    print(f"\n성공적으로 {output_filename} 이 생성되었습니다!")
    print("이 파일을 타겟 PC에 복사하여 압축을 풀고 install.bat 을 실행하세요.")

if __name__ == "__main__":
    create_deploy_zip()
