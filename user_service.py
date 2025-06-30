from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from datetime import date, timedelta
from mysql.connector import Error
from database import get_db_connection

# ! 사용자 로그인
async def login_user(request: Request):
    try:
        login_data = await request.json()
        user_id = login_data['userId']
        password = login_data['password']
        
        with get_db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            # 사용자 정보 조회 및 검증
            query = """
                SELECT u.USER_ID, u.PW, u.NAME, u.DIVISION, u.STATUS, u.ROLE_ID, r.ROLE_NAME, u.PW_UPDATE_DT
                FROM USER u
                LEFT JOIN ROLE r ON u.ROLE_ID = r.ROLE_ID
                WHERE u.USER_ID = %s AND u.STATUS = TRUE
            """
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return JSONResponse({
                    "success": False,
                    "message": "존재하지 않거나 비활성화된 사용자입니다."
                })
            
            # 비밀번호 확인
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if user['PW'] != hashed_password:
                return JSONResponse({
                    "success": False,
                    "message": "비밀번호가 일치하지 않습니다."
                })
            
            # 비밀번호 변경 필요 여부 체크
            password_change_required = False
            password_change_reason = ""
            
            # 1. 초기 비밀번호 사용 체크
            if password == '1234!':
                password_change_required = True
                password_change_reason = "초기 비밀번호를 사용 중입니다. 보안을 위해 비밀번호를 변경해주세요."
            
            # 2. 90일 경과 체크
            if user['PW_UPDATE_DT']:
                ninety_days_ago = date.today() - timedelta(days=90)
                if user['PW_UPDATE_DT'] < ninety_days_ago:
                    password_change_required = True
                    password_change_reason = "비밀번호 변경 후 90일이 경과했습니다. 보안을 위해 비밀번호를 변경해주세요."
            
            # 로그인 성공
            response_data = {
                "success": True,
                "message": "로그인 성공",
                "data": {
                    "userId": user['USER_ID'],
                    "name": user['NAME'],
                    "division": user['DIVISION'],
                    "roleId": user['ROLE_ID'],
                    "roleName": user['ROLE_NAME'],
                    "passwordChangeRequired": password_change_required,
                    "passwordChangeReason": password_change_reason
                }
            }

            return JSONResponse(response_data)
            
    except Error as e:
        print(f"로그인 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "로그인 처리 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })

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
            current_time = date.today()
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
    
# ! 비밀번호 변경
async def change_password(request: Request):
    try:
        password_data = await request.json()
        user_id = password_data['userId']
        current_password = password_data['currentPassword']
        new_password = password_data['newPassword']
        
        with get_db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            # 현재 비밀번호 확인
            query = "SELECT PW FROM USER WHERE USER_ID = %s AND STATUS = TRUE"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return JSONResponse({
                    "success": False,
                    "message": "사용자를 찾을 수 없습니다."
                })
            
            # 현재 비밀번호 검증
            current_hashed = hashlib.sha256(current_password.encode()).hexdigest()
            if user['PW'] != current_hashed:
                return JSONResponse({
                    "success": False,
                    "message": "현재 비밀번호가 일치하지 않습니다."
                })
            
            # 새 비밀번호 해시화
            new_hashed = hashlib.sha256(new_password.encode()).hexdigest()
            
            # 비밀번호 업데이트
            current_time = date.today()
            update_query = """
                UPDATE USER 
                SET PW = %s, PW_UPDATE_DT = %s, UPDATE_DT = %s 
                WHERE USER_ID = %s
            """
            
            cursor.execute(update_query, (new_hashed, current_time, current_time, user_id))
            connection.commit()
            
            return JSONResponse({
                "success": True,
                "message": "비밀번호가 성공적으로 변경되었습니다."
            })
            
    except Error as e:
        print(f"비밀번호 변경 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "비밀번호 변경 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })