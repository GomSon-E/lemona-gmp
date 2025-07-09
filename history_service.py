from fastapi import Request
from fastapi.responses import JSONResponse
from mysql.connector import Error
from database import get_db_connection
from datetime import datetime

class HistoryService:
    def __init__(self, table_name, comment_join=True):
        self.table_name = table_name
        self.comment_join = comment_join
    
    async def get_history_data(self, request: Request):
        try:
            # 쿼리 파라미터 추출
            params = dict(request.query_params)
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            user_id = params.get('userId', '').strip()
            content = params.get('content', '').strip()
            comment = params.get('comment', '').strip()
            last_update_time = params.get('lastUpdateTime')  # 마지막 업데이트 시간
            incremental = params.get('incremental', 'false').lower() == 'true'  # 증분 업데이트 여부
            
            with get_db_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # 기본 쿼리 구성
                if self.comment_join:
                    base_query = f"""
                        SELECT h.*, c.CONTENT as COMMENT_CONTENT
                        FROM {self.table_name} h
                        LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID
                    """
                else:
                    base_query = f"SELECT * FROM {self.table_name} h"
                
                # WHERE 조건 구성
                where_conditions = []
                query_params = []
                
                # 증분 업데이트인 경우 마지막 업데이트 시간 이후 데이터만 조회
                if incremental and last_update_time:
                    where_conditions.append("h.CREATE_DT > %s")
                    query_params.append(last_update_time)
                else:
                    # 전체 조회인 경우 기존 필터 조건들 적용
                    # 날짜 범위 조건
                    if start_date:
                        where_conditions.append("DATE(h.CREATE_DT) >= %s")
                        query_params.append(start_date)
                    
                    if end_date:
                        where_conditions.append("DATE(h.CREATE_DT) <= %s")
                        query_params.append(end_date)
                
                # 사용자 ID 조건
                if user_id:
                    where_conditions.append("h.USER_ID LIKE %s")
                    query_params.append(f"%{user_id}%")
                
                # 작업내용 조건
                if content:
                    where_conditions.append("h.CONTENT LIKE %s")
                    query_params.append(f"%{content}%")
                
                # 코멘트 조건
                if comment and self.comment_join:
                    where_conditions.append("c.CONTENT LIKE %s")
                    query_params.append(f"%{comment}%")
                
                # WHERE 절 추가
                if where_conditions:
                    base_query += " WHERE " + " AND ".join(where_conditions)
                
                # 정렬 추가
                data_query = base_query + " ORDER BY h.CREATE_DT DESC"

                print(f"실행할 쿼리: {data_query}")
                print(f"쿼리 파라미터: {query_params}")
                
                cursor.execute(data_query, query_params)
                data = cursor.fetchall()
                
                # 날짜 포맷팅
                for row in data:
                    if 'CREATE_DT' in row and row['CREATE_DT']:
                        row['CREATE_DT'] = row['CREATE_DT'].isoformat()
                
                return JSONResponse({
                    "success": True,
                    "data": data,
                    "incremental": incremental,
                    "count": len(data),
                    "serverTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 서버 시간 추가
                })
                
        except Error as e:
            print(f"{self.table_name} 조회 오류: {e}")
            return JSONResponse({
                "success": False,
                "message": f"{self.table_name} 조회 중 오류가 발생했습니다."
            })
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return JSONResponse({
                "success": False,
                "message": "서버 내부 오류가 발생했습니다."
            })