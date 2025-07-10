from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
import subprocess
import os
from datetime import datetime
import tempfile

from database import get_db_connection

# 백업 설정
BACKUP_DIR = "./backup"
MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'LEMONA_GMP',
    'user': 'root',
    'password': '1234',
    'port': 3306
}

# MySQL 설치 경로
MYSQL_PATHS = [
    r"C:\Program Files\MySQL\MySQL Server 8.0\bin",
    r"C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin",
    r"C:\mysql\bin",
    r"C:\xampp\mysql\bin",
    r"C:\wamp64\bin\mysql\mysql8.0.31\bin",
    r"C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin"
]

# 백업 디렉토리 생성
os.makedirs(BACKUP_DIR, exist_ok=True)

def find_mysql_executable(exe_name):
    """MySQL 실행 파일 경로 찾기"""
    import shutil
    
    # 먼저 PATH에서 찾기
    mysql_path = shutil.which(exe_name)
    if mysql_path:
        return mysql_path
    
    # Windows 기본 설치 경로에서 찾기
    for path in MYSQL_PATHS:
        exe_path = os.path.join(path, f"{exe_name}.exe")
        if os.path.exists(exe_path):
            return exe_path
    
    return None

def get_comprehensive_mysqldump_command(output_file):
    """완전한 백업을 위한 mysqldump 명령어 생성 (구조 + 데이터 + 권한)"""
    mysqldump_path = find_mysql_executable('mysqldump')
    if not mysqldump_path:
        raise FileNotFoundError("mysqldump 실행 파일을 찾을 수 없습니다.")
    
    return [
        mysqldump_path,
        f'--host={MYSQL_CONFIG["host"]}',
        f'--port={MYSQL_CONFIG["port"]}',
        f'--user={MYSQL_CONFIG["user"]}',
        f'--password={MYSQL_CONFIG["password"]}',
        '--routines',                    # 저장 프로시저, 함수 포함
        '--triggers',                    # 트리거 포함
        '--events',                      # 이벤트 포함
        '--single-transaction',          # 일관성 보장
        '--quick',                       # 메모리 효율성
        '--lock-tables=false',           # 테이블 잠금 방지
        '--add-drop-database',           # DROP DATABASE 문 추가
        '--create-options',              # 테이블 생성 옵션 포함
        '--disable-keys',                # 키 비활성화로 속도 향상
        '--extended-insert',             # 확장 삽입 사용
        '--hex-blob',                    # BLOB 데이터를 16진수로
        '--complete-insert',             # 완전한 INSERT 문
        '--add-drop-table',              # DROP TABLE 문 추가
        '--databases', MYSQL_CONFIG['database'],  # 데이터베이스 생성 문 포함
        '--result-file=' + output_file
    ]

def get_mysqldump_command(output_file):
    """기본 mysqldump 명령어 생성"""
    mysqldump_path = find_mysql_executable('mysqldump')
    if not mysqldump_path:
        raise FileNotFoundError("mysqldump 실행 파일을 찾을 수 없습니다.")
    
    return [
        mysqldump_path,
        f'--host={MYSQL_CONFIG["host"]}',
        f'--port={MYSQL_CONFIG["port"]}',
        f'--user={MYSQL_CONFIG["user"]}',
        f'--password={MYSQL_CONFIG["password"]}',
        '--routines',
        '--triggers',
        '--single-transaction',
        '--quick',
        '--lock-tables=false',
        MYSQL_CONFIG['database'],
        '--result-file=' + output_file
    ]

def get_mysql_command():
    """mysql 명령어 생성"""
    mysql_path = find_mysql_executable('mysql')
    if not mysql_path:
        raise FileNotFoundError("mysql 실행 파일을 찾을 수 없습니다.")
    
    return [
        mysql_path,
        f'--host={MYSQL_CONFIG["host"]}',
        f'--port={MYSQL_CONFIG["port"]}',
        f'--user={MYSQL_CONFIG["user"]}',
        f'--password={MYSQL_CONFIG["password"]}',
        '--default-character-set=utf8mb4'
    ]

def get_mysql_command_without_db():
    """데이터베이스 지정 없는 mysql 명령어 생성"""
    mysql_path = find_mysql_executable('mysql')
    if not mysql_path:
        raise FileNotFoundError("mysql 실행 파일을 찾을 수 없습니다.")
    
    return [
        mysql_path,
        f'--host={MYSQL_CONFIG["host"]}',
        f'--port={MYSQL_CONFIG["port"]}',
        f'--user={MYSQL_CONFIG["user"]}',
        f'--password={MYSQL_CONFIG["password"]}',
        '--default-character-set=utf8mb4'
    ]

# ! 데이터 백업
async def create_backup(request, is_manual: bool = True):
    try:
        # 백업 파일명 생성
        backup_filename = "backup.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        backup_type = "자동 데이터 백업"
        current_user_id = None
        login_history_id = None
        
        if is_manual:
            backup_type = "수동 데이터 백업"
            params = dict(request.query_params)
            current_user_id = params.get('currentUserId')
            login_history_id = params.get('loginHistoryId')
        
        # 백업 파일 생성 전에 로그 저장
        await save_data_history_log(f"데이터 백업 - {backup_type} ", current_user_id, login_history_id)
        
        # 구조 + 데이터 백업을 위한 mysqldump 명령
        try:
            dump_command = get_comprehensive_mysqldump_command(backup_path)
        except FileNotFoundError as e:
            return JSONResponse({
                "success": False,
                "message": f"MySQL 도구를 찾을 수 없습니다. MySQL이 설치되어 있는지 확인해주세요. 오류: {str(e)}"
            })
        
        result = subprocess.run(
            dump_command,
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        if result.returncode != 0:
            return JSONResponse({
                "success": False,
                "message": f"백업 생성 실패: {result.stderr}"
            })
        
        # 백업 파일 정보 확인
        if os.path.exists(backup_path):
            file_size = os.path.getsize(backup_path)
            
            return JSONResponse({
                "success": True,
                "message": "데이터베이스 백업이 성공적으로 생성되었습니다.",
                "data": {
                    "filename": backup_filename,
                    "path": backup_path,
                    "size": file_size,
                    "created_at": datetime.now().isoformat(),
                    "backup_type": "complete_with_structure"
                }
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "백업 파일이 생성되지 않았습니다."
            })
    
    except subprocess.TimeoutExpired:
        return JSONResponse({
            "success": False,
            "message": "백업 생성 시간이 초과되었습니다."
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"백업 생성 중 오류가 발생했습니다: {str(e)}"
        })

# ! 데이터 복원
async def restore_backup(request, backup_file: UploadFile):
    try:
        params = dict(request.query_params)
        current_user_id = params.get('currentUserId', 'system')
        login_history_id = params.get('loginHistoryId')

        # 파일 확장자 확인
        if not backup_file.filename.endswith('.bak'):
            return JSONResponse({
                "success": False,
                "message": "BAK 파일만 업로드할 수 있습니다."
            })
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bak') as tmp_file:
            content = await backup_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            mysql_command = get_mysql_command_without_db()
        except FileNotFoundError as e:
            return JSONResponse({
                "success": False,
                "message": f"MySQL 도구를 찾을 수 없습니다. MySQL이 설치되어 있는지 확인해주세요. 오류: {str(e)}"
            })
            
        try:
            # 기존 데이터베이스 삭제
            drop_db_command = mysql_command + ['-e', f'DROP DATABASE IF EXISTS {MYSQL_CONFIG["database"]};']
            result = subprocess.run(drop_db_command, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"데이터베이스 삭제 경고: {result.stderr}")
            
            # 백업 파일 복원
            restore_command = mysql_command
            
            with open(tmp_file_path, 'r', encoding='utf-8') as backup_content:
                result = subprocess.run(
                    restore_command,
                    stdin=backup_content,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            
            if result.returncode != 0:
                return JSONResponse({
                    "success": False,
                    "message": f"데이터 복원 실패: {result.stderr}"
                })
            
            await save_data_history_log(f"데이터 복원 - 파일: {backup_file.filename}", current_user_id, login_history_id)
            
            return JSONResponse({
                "success": True,
                "message": "데이터베이스가 성공적으로 복원되었습니다.",
                "data": {
                    "restored_from": backup_file.filename,
                    "database": MYSQL_CONFIG["database"],
                    "restored_at": datetime.now().isoformat()
                }
            })
        
        finally:
            # 임시 파일 삭제
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
    
    except subprocess.TimeoutExpired:
        return JSONResponse({
            "success": False,
            "message": "데이터 복원 시간이 초과되었습니다."
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"데이터 복원 중 오류가 발생했습니다: {str(e)}"
        })

# Data History 로그 저장 함수
async def save_data_history_log(content: str, user_id: str, login_history_id: str = None):
    try: 
        with get_db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            # 로그인 히스토리에서 코멘트 ID 조회
            comment_id = None
            if login_history_id:
                comment_query = """
                    SELECT COMMENT_ID 
                    FROM LOGIN_HISTORY 
                    WHERE ID = %s
                """
                cursor.execute(comment_query, (login_history_id,))
                comment_result = cursor.fetchone()
                if comment_result and comment_result['COMMENT_ID']:
                    comment_id = comment_result['COMMENT_ID']
            
            current_time = datetime.now()
            
            insert_query = """
                INSERT INTO DATA_HISTORY (CONTENT, USER_ID, COMMENT_ID, CREATE_DT)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (content, user_id, comment_id, current_time))
            connection.commit()
            
            print(f"Data History 로그 저장 완료: {content} by {user_id}, comment_id: {comment_id}")
            
    except Exception as e:
        print(f"Data History 로그 저장 실패: {e}")