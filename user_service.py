from fastapi import Request
from fastapi.responses import JSONResponse
import hashlib
from datetime import datetime,date, timedelta
from mysql.connector import Error
from database import get_db_connection
from plc_data_service import plc_collector

# ! 사용자 로그인
async def login_user(request: Request):
    try:
        login_data = await request.json()
        user_id = login_data['userId']
        password = login_data['password']
        
        with get_db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            from datetime import datetime
            current_time = datetime.now()
            
            # 사용자 정보 조회 및 검증
            query = """
                SELECT u.USER_ID, u.PW, u.NAME, u.DIVISION, u.STATUS, u.ROLE_ID, r.ROLE_NAME, u.PW_UPDATE_DT
                FROM USER u
                LEFT JOIN ROLE r ON u.ROLE_ID = r.ROLE_ID
                WHERE u.USER_ID = %s
            """
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            
            # 로그인 기록 쿼리 준비
            login_history_query = """
                INSERT INTO LOGIN_HISTORY (CONTENT, USER_ID, CREATE_DT)
                VALUES (%s, %s, %s)
            """
            
            if not user:
                # 존재하지 않는 사용자 - 로그인 실패 기록
                cursor.execute(login_history_query, (f'로그인 실패 - 존재하지 않는 사용자 : {user_id}', None, current_time))
                connection.commit()
                
                return JSONResponse({
                    "success": False,
                    "message": "존재하지 않는 사용자입니다."
                })
            
            if not user['STATUS']:
                # 비활성화된 사용자 - 로그인 실패 기록
                cursor.execute(login_history_query, ('로그인 실패 - 비활성화된 사용자', user_id, current_time))
                connection.commit()
                
                return JSONResponse({
                    "success": False,
                    "message": "비활성화된 사용자입니다. 관리자에게 문의하세요."
                })
            
            # 비밀번호 확인
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if user['PW'] != hashed_password:
                # 비밀번호 불일치 - 로그인 실패 기록
                cursor.execute(login_history_query, ('로그인 실패 - 비밀번호 불일치', user_id, current_time))
                connection.commit()
                
                # 로그인 실패 후 계정 잠금 처리
                await handle_login_failure(cursor, user_id, current_time, connection)
                
                return JSONResponse({
                    "success": False,
                    "message": "비밀번호가 일치하지 않습니다."
                })
            
            # 로그인 성공 처리
            cursor.execute(login_history_query, ('로그인 성공', user_id, current_time))
            login_history_id = cursor.lastrowid

            # PLC에 사용자 권한 레벨 쓰기
            await plc_collector.write_user_level(user['ROLE_ID'])
            
            # 비밀번호 변경 필요 여부 체크
            password_change_required = False
            password_change_reason = ""
            
            if user['ROLE_ID'] != 1:  # ROOT가 아닌 경우만 체크
                if password == '1234!':
                    password_change_required = True
                    password_change_reason = "초기 비밀번호를 사용 중입니다. 보안을 위해 비밀번호를 변경해주세요."
                
                if user['PW_UPDATE_DT']:
                    ninety_days_ago = date.today() - timedelta(days=90)
                    if user['PW_UPDATE_DT'] < ninety_days_ago:
                        password_change_required = True
                        password_change_reason = "비밀번호 변경 후 90일이 경과했습니다. 보안을 위해 비밀번호를 변경해주세요."
            
            connection.commit()
            
            # 로그인 성공 응답
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
                    "passwordChangeReason": password_change_reason,
                    "loginHistoryId": login_history_id,
                    "loginTime": current_time.isoformat(),
                    "expiresAt": (current_time + timedelta(minutes=5)).isoformat()
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

# ! 로그인 실패 후 계정 잠금 처리
async def handle_login_failure(cursor, user_id, current_time, connection):
    try:
        # 30분 이내 로그인 실패 기록 조회
        thirty_minutes_ago = current_time - timedelta(minutes=30)
        
        # 최근 30분 내의 로그인 기록 조회
        recent_history_query = """
            SELECT CONTENT, CREATE_DT 
            FROM LOGIN_HISTORY 
            WHERE USER_ID = %s 
            AND CREATE_DT >= %s 
            ORDER BY CREATE_DT DESC
        """
        
        cursor.execute(recent_history_query, (user_id, thirty_minutes_ago))
        recent_attempts = cursor.fetchall()
        
        if not recent_attempts:
            return
        
        # 연속 실패 횟수 계산
        consecutive_failures = 0
        for attempt in recent_attempts:
            if '로그인 실패' in attempt['CONTENT']:
                consecutive_failures += 1
            elif '로그인 성공' in attempt['CONTENT']:
                # 성공 기록이 있으면 연속 실패 카운트 중단
                break
        
        # 연속 실패가 5회 이상인지 확인
        if consecutive_failures >= 5:
            # 계정 비활성화
            deactivate_query = """
                UPDATE USER 
                SET STATUS = FALSE, UPDATE_DT = %s 
                WHERE USER_ID = %s
            """
            cursor.execute(deactivate_query, (current_time.date(), user_id))
            connection.commit()
            
    except Exception as e:
        print(f"로그인 실패 처리 오류: {e}")

# ! 사용자 로그아웃
async def logout_user(request: Request):
    try:
        logout_data = await request.json()
        user_id = logout_data['userId']
        logout_type = logout_data.get('logoutType', 'manual')  # manual 또는 auto
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            # 로그아웃 기록 저장
            from datetime import datetime
            current_time = datetime.now()
            
            # 로그아웃 타입에 따른 메시지 설정
            if logout_type == 'auto':
                content = '로그아웃 - 자동 로그아웃'
            elif logout_type == 'session_expired':
                content = '로그아웃 - 자동 로그아웃'
            else:
                content = '로그아웃 - 수동 로그아웃'
            
            logout_history_query = """
                INSERT INTO LOGIN_HISTORY (CONTENT, USER_ID, CREATE_DT)
                VALUES (%s, %s, %s)
            """
            
            cursor.execute(logout_history_query, (content, user_id, current_time))
            connection.commit()

            # 로그아웃 시 PLC 권한 레벨을 0으로 설정
            await plc_collector.write_user_level(0)
            
            return JSONResponse({
                "success": True,
                "message": "로그아웃이 성공적으로 처리되었습니다."
            })
            
    except Error as e:
        print(f"로그아웃 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "로그아웃 처리 중 오류가 발생했습니다."
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
        
        # 현재 사용자 정보 추출
        current_user_id = user_data.get('currentUserId', 'system')
        login_history_id = user_data.get('loginHistoryId')
        
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
            
            # User History 로그 저장
            role_name = get_role_name_by_id(user_data['role'])
            log_content = f"사용자 생성 - ID: {user_data['userId']}, 이름: {user_data['fullName']}, 부서: {user_data['division']}, 권한: {role_name}"
            await save_user_history_log(log_content, current_user_id, login_history_id)
            
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
        login_history_id = password_data.get('loginHistoryId')
        
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
            current_time = datetime.now()
            update_query = """
                UPDATE USER 
                SET PW = %s, PW_UPDATE_DT = %s, UPDATE_DT = %s 
                WHERE USER_ID = %s
            """
            
            cursor.execute(update_query, (new_hashed, current_time, current_time, user_id))
            connection.commit()

            # User History 로그 저장
            log_content = f"비밀번호 변경"
            await save_user_history_log(log_content, user_id, login_history_id)
            
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

# ! 비밀번호 초기화
async def reset_password(request: Request):
    try:
        reset_data = await request.json()
        target_user_id = reset_data['userId']
        current_user_id = reset_data.get('currentUserId', None)
        login_history_id = reset_data.get('loginHistoryId')
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            # 사용자 존재 확인
            check_query = "SELECT USER_ID FROM USER WHERE USER_ID = %s AND STATUS = TRUE"
            cursor.execute(check_query, (target_user_id,))
            if not cursor.fetchone():
                return JSONResponse({
                    "success": False,
                    "message": "사용자를 찾을 수 없습니다."
                })
            
            # 비밀번호를 1234!로 초기화
            default_password = '1234!'
            hashed_password = hashlib.sha256(default_password.encode()).hexdigest()
            
            # 비밀번호 업데이트 (PW_UPDATE_DT는 NULL로 설정하여 강제 변경 유도)
            current_date = date.today()
            update_query = """
                UPDATE USER 
                SET PW = %s, PW_UPDATE_DT = NULL, UPDATE_DT = %s 
                WHERE USER_ID = %s
            """
            
            cursor.execute(update_query, (hashed_password, current_date, target_user_id))
            connection.commit()
            
            # User History 로그 저장
            log_content = f"비밀번호 초기화 - 대상자: {target_user_id}"
            await save_user_history_log(log_content, current_user_id, login_history_id)

            return JSONResponse({
                "success": True,
                "message": "비밀번호가 성공적으로 초기화되었습니다."
            })
            
    except Error as e:
        print(f"비밀번호 초기화 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "비밀번호 초기화 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })

# ! 전체 사용자 조회
async def get_all_users():
    try:
        with get_db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT u.USER_ID, u.NAME, u.DIVISION, u.STATUS, u.ROLE_ID, r.ROLE_NAME, 
                       u.CREATE_DT, u.UPDATE_DT, u.PW_UPDATE_DT
                FROM USER u
                LEFT JOIN ROLE r ON u.ROLE_ID = r.ROLE_ID
                WHERE u.ROLE_ID != 1
                ORDER BY u.CREATE_DT DESC
            """
            cursor.execute(query)
            users = cursor.fetchall()
            
            for user in users:
                if user['CREATE_DT']:
                    user['CREATE_DT'] = user['CREATE_DT'].strftime('%Y-%m-%d')
                if user['UPDATE_DT']:
                    user['UPDATE_DT'] = user['UPDATE_DT'].strftime('%Y-%m-%d')
                if user['PW_UPDATE_DT']:
                    user['PW_UPDATE_DT'] = user['PW_UPDATE_DT'].strftime('%Y-%m-%d')
            
            return JSONResponse({
                "success": True,
                "data": users
            })
            
    except Error as e:
        print(f"사용자 목록 조회 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "사용자 목록 조회 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })
    
# ! 단일 사용자 조회
async def get_user(user_id: str):
    try:
        with get_db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT u.USER_ID, u.NAME, u.DIVISION, u.STATUS, u.ROLE_ID, r.ROLE_NAME, 
                       u.CREATE_DT, u.UPDATE_DT, u.PW_UPDATE_DT
                FROM USER u
                LEFT JOIN ROLE r ON u.ROLE_ID = r.ROLE_ID
                WHERE u.USER_ID = %s
            """
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()

            # date 객체를 문자열로 변환
            if user['CREATE_DT']:
                user['CREATE_DT'] = user['CREATE_DT'].strftime('%Y-%m-%d %H:%M:%S')
            if user['UPDATE_DT']:
                user['UPDATE_DT'] = user['UPDATE_DT'].strftime('%Y-%m-%d %H:%M:%S')
            if user['PW_UPDATE_DT']:
                user['PW_UPDATE_DT'] = user['PW_UPDATE_DT'].strftime('%Y-%m-%d %H:%M:%S')
            
            if not user:
                return JSONResponse({
                    "success": False,
                    "message": "사용자를 찾을 수 없습니다."
                })
            
            return JSONResponse({
                "success": True,
                "data": user
            })
            
    except Error as e:
        print(f"사용자 조회 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "사용자 조회 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })

# ! 사용자 수정
async def update_user(user_id: str, request: Request):
    try:
        user_data = await request.json()
        
        # 현재 사용자 정보 추출
        current_user_id = user_data.get('currentUserId', 'system')
        login_history_id = user_data.get('loginHistoryId')
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            # 사용자 존재 확인
            check_query = "SELECT USER_ID FROM USER WHERE USER_ID = %s"
            cursor.execute(check_query, (user_id,))
            if not cursor.fetchone():
                return JSONResponse({
                    "success": False,
                    "message": "사용자를 찾을 수 없습니다."
                })
            
            # 사용자 정보 업데이트
            current_time = date.today()
            update_query = """
                UPDATE USER 
                SET NAME = %s, DIVISION = %s, STATUS = %s, ROLE_ID = %s, UPDATE_DT = %s
                WHERE USER_ID = %s
            """
            
            cursor.execute(update_query, (
                user_data['name'],
                user_data['division'],
                user_data['status'] == '1',
                user_data['roleId'],
                current_time,
                user_id
            ))

            connection.commit()
            
            # User History 로그 저장
            status_text = "활성" if user_data['status'] == '1' else "비활성"
            role_name = get_role_name_by_id(user_data['roleId'])
            log_content = f"사용자 수정 - ID: {user_id}, 이름: {user_data['name']}, 부서: {user_data['division']}, 권한: {role_name}, 상태: {status_text}"
            await save_user_history_log(log_content, current_user_id, login_history_id)
            
            return JSONResponse({
                "success": True,
                "message": "사용자 정보가 성공적으로 수정되었습니다."
            })
            
    except Error as e:
        print(f"사용자 수정 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "사용자 수정 중 오류가 발생했습니다."
        })
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": "서버 내부 오류가 발생했습니다."
        })
    
#! 사용자 관리 이력 저장
async def save_user_history_log(content: str, user_id: str, login_history_id: str = None):
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
                INSERT INTO USER_HISTORY (CONTENT, USER_ID, COMMENT_ID, CREATE_DT)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (content, user_id, comment_id, current_time))
            connection.commit()
            
            print(f"User History 로그 저장 완료: {content} by {user_id}, comment_id: {comment_id}")
            
    except Exception as e:
        print(f"User History 로그 저장 실패: {e}")

# ! 권한ID로 권한명 조회
def get_role_name_by_id(role_id):
    role_mapping = {
        1: 'ROOT',
        2: 'ADMIN', 
        3: 'MANAGER',
        4: 'USER'
    }
    return role_mapping.get(int(role_id), None)