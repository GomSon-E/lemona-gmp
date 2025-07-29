import uvicorn
import sys
import os
from pathlib import Path

# 실행 파일일 때 경로 설정
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
    os.chdir(application_path)
else:
    # 개발 환경
    application_path = os.path.dirname(os.path.abspath(__file__))

from app import app

if __name__ == "__main__":
    print("=== 보틀포장 1호기 데이터 & 권한 관리 S/W ===")
    print("서버를 시작합니다...")
    print("브라우저에서 http://localhost:8000 으로 접속하세요")
    print("종료하려면 Ctrl+C를 누르세요")
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
    except Exception as e:
        print(f"서버 실행 중 오류 발생: {e}")
        input("엔터를 눌러 종료하세요...")