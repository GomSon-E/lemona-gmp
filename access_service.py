from fastapi import Request
from fastapi.responses import JSONResponse
from mysql.connector import Error
from database import get_db_connection

# ! 전체 페이지 목록 조회
async def get_all_pages():
    try:
        with get_db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT PAGE_ID, PAGE_LINK, MENU_NAME, PAGE_NAME
                FROM PAGE
                ORDER BY PAGE_ID
            """
            cursor.execute(query)
            pages = cursor.fetchall()
            
            return JSONResponse({
                "success": True,
                "data": pages
            })
            
    except Error as e:
        print(f"페이지 목록 조회 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "페이지 목록 조회 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })

# ! 접근 권한 업데이트
async def update_access(request: Request):
    try:
        access_data = await request.json()
        role_id = access_data['roleId']
        page_ids = access_data['pageIds']
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            # 기존 접근 권한 삭제
            delete_query = "DELETE FROM ACCESS WHERE ROLE_ID = %s"
            cursor.execute(delete_query, (role_id,))
            
            # 새로운 접근 권한 추가
            if page_ids:
                insert_query = "INSERT INTO ACCESS (ROLE_ID, PAGE_ID) VALUES (%s, %s)"
                access_values = [(role_id, page_id) for page_id in page_ids]
                cursor.executemany(insert_query, access_values)
            
            connection.commit()
            
            return JSONResponse({
                "success": True,
                "message": "접근 권한이 성공적으로 업데이트되었습니다."
            })
            
    except Error as e:
        print(f"접근 권한 업데이트 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "접근 권한 업데이트 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })