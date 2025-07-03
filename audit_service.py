from fastapi import Request
from fastapi.responses import JSONResponse
from mysql.connector import Error
from database import get_db_connection
from datetime import datetime

# ! 코멘트 생성
async def create_comment(request: Request):
    try:
        comment_data = await request.json()
        content = comment_data['content']
        user_id = comment_data['userId']
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            # 코멘트 생성
            insert_query = """
                INSERT INTO COMMENT (CONTENT, USER_ID)
                VALUES (%s, %s)
            """
            
            cursor.execute(insert_query, (content, user_id))
            connection.commit()
            
            # 생성된 코멘트 ID 가져오기
            comment_id = cursor.lastrowid
            
            return JSONResponse({
                "success": True,
                "message": "코멘트가 성공적으로 저장되었습니다.",
                "data": {
                    "commentId": comment_id,
                    "content": content,
                    "userId": user_id
                }
            })
            
    except Error as e:
        print(f"코멘트 생성 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "코멘트 저장 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })
