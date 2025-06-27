from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

app = FastAPI(title="얼굴 특징 벡터 추출 및 비교 API")
app.mount("/static", StaticFiles(directory="static"), name="static")

MYSQL_CONFIG = {
    'host': 'localhost',
    'database': 'LEMONA_GMP',
    'user': 'root',
    'password': '1234',
    'port': 3306,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        yield connection
    except Error as e:
        print(f"MySQL 연결 오류: {e}")
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail="데이터베이스 연결 오류")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.get("/")
async def root_page():
    return FileResponse('static/html/login.html')

@app.get("/login")
async def login_page():
    return FileResponse('static/html/login.html')

@app.get("/landing")
async def login_page():
    return FileResponse('static/html/landing.html')

@app.get("/api/test")
async def test_database():
    try:
        with get_db_connection() as connection:
            cursor = connection.cursor(buffered=True, dictionary=True)
            cursor.execute("SELECT * FROM PAGE LIMIT 1;")
            result = cursor.fetchone()
            cursor.close()
            
            print("DB 연결 성공:", result)
            
            return {
                "message": "데이터베이스 연결 성공",
                "count": result,
                "status": "ok"
            }
            
    except Exception as e:
        print(f"오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)