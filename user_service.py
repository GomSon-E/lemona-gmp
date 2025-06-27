from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from datetime import datetime
from mysql.connector import Error
from database import get_db_connection

# ! 사용자 생성
async def create_user(request: Request):
    try:
        user_data = await request.json()
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            # 중복 확인
            check_query = "SELECT USER_ID FROM USER WHERE USER_ID = %s"
            cursor.execute(check_query, (user_data['userId'],))
            if cursor.fetchone():
                return JSONResponse({
                    "success": False,
                    "message": "이미 존재하는 사용자 ID입니다."
                })
            
            # 사용자 생성
            current_time = datetime.now()
            insert_query = """
                INSERT INTO USER (USER_ID, PW, NAME, DIVISION, ROLE_ID, CREATE_DT, UPDATE_DT)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                user_data['userId'],
                hashlib.sha256('1234!'.encode()).hexdigest(),
                user_data['fullName'],
                user_data['division'],
                user_data['role'],
                current_time,
                current_time
            ))

            connection.commit()
            
            return JSONResponse({
                "success": True,
                "message": "사용자가 성공적으로 생성되었습니다.",
                "data": {
                    "userId": user_data['userId'],
                    "defaultPassword": '1234!',
                }
            })
            
    except Error as e:
        print(f"사용자 생성 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "사용자 생성 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })