from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from mysql.connector import Error
from database import get_db_connection
from datetime import datetime
import io
import os
from urllib.parse import quote
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

class HistoryService:
    def __init__(self, table_name, comment_join=True, report_title="", log_title=""):
        self.table_name = table_name
        self.comment_join = comment_join
        self.report_title = report_title
        self.log_title = log_title
    
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

    async def export_history_data(self, request: Request):
        try:
            # 쿼리 파라미터 추출
            params = dict(request.query_params)
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            user_id = params.get('userId', '').strip()
            content = params.get('content', '').strip()
            comment = params.get('comment', '').strip()
            current_user_id = params.get('currentUserId', 'system')  # 현재 사용자 ID
            login_history_id = params.get('loginHistoryId')  # 로그인 히스토리 ID
            
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
                
                # 전체 데이터 조회
                if self.comment_join:
                    base_query = f"""
                        SELECT h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                        FROM {self.table_name} h
                        LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID
                    """
                else:
                    base_query = f"SELECT CREATE_DT, USER_ID, CONTENT FROM {self.table_name} h"
                
                where_conditions = []
                query_params = []
                
                if start_date:
                    where_conditions.append("DATE(h.CREATE_DT) >= %s")
                    query_params.append(start_date)
                
                if end_date:
                    where_conditions.append("DATE(h.CREATE_DT) <= %s")
                    query_params.append(end_date)
                
                if user_id:
                    where_conditions.append("h.USER_ID LIKE %s")
                    query_params.append(f"%{user_id}%")
                
                if content:
                    where_conditions.append("h.CONTENT LIKE %s")
                    query_params.append(f"%{content}%")
                
                if comment and self.comment_join:
                    where_conditions.append("c.CONTENT LIKE %s")
                    query_params.append(f"%{comment}%")
                
                if where_conditions:
                    base_query += " WHERE " + " AND ".join(where_conditions)
                
                base_query += " ORDER BY h.CREATE_DT DESC"
                
                cursor.execute(base_query, query_params)
                data = cursor.fetchall()
                
                # PDF 생성
                pdf_buffer = self.generate_pdf_report(data, params)
                
                current_time = datetime.now()
                report_content = f"Report Generated - {self.log_title}"
                
                # REPORT_HISTORY에 기록 저장
                report_history_query = """
                    INSERT INTO REPORT_HISTORY (CONTENT, USER_ID, COMMENT_ID, CREATE_DT)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(report_history_query, (report_content, current_user_id, comment_id, current_time))
                connection.commit()
                
                print(f"보고서 생성 기록 저장 완료: {report_content} by {current_user_id}, comment_id: {comment_id}")
                
                # 파일명 생성
                current_time_str = current_time.strftime('%Y%m%d_%H%M%S')
                filename_korean = f"{self.report_title} 보고서_{current_time_str}.pdf"
                
                # URL 인코딩된 파일명 생성
                filename_encoded = quote(filename_korean.encode('utf-8'))
                
                # PDF 응답 반환
                return StreamingResponse(
                    io.BytesIO(pdf_buffer),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
                    }
                )
                
        except Error as e:
            print(f"{self.table_name} 보고서 생성 오류: {e}")
            return JSONResponse({
                "success": False,
                "message": f"{self.table_name} 보고서 생성 중 오류가 발생했습니다."
            })
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return JSONResponse({
                "success": False,
                "message": "서버 내부 오류가 발생했습니다."
            })

    def generate_pdf_report(self, data, filters):
        buffer = io.BytesIO()
        
        # 한글 폰트 등록
        try:
            font_path = "C:/Windows/Fonts/malgun.ttf"  # 맑은 고딕
            if not os.path.exists(font_path):
                font_path = "C:/Windows/Fonts/gulim.ttc"  # 굴림
            
            # 폰트 등록
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Korean', font_path))
                korean_font = 'Korean'
            else:
                # 폰트를 찾을 수 없는 경우 기본 폰트 사용
                korean_font = 'Helvetica'
                print("한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
        except Exception as e:
            korean_font = 'Helvetica'
            print(f"폰트 등록 오류: {e}")
        
        # A4 가로 방향 설정
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        # 스타일 설정 (한글 폰트 적용)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=korean_font,
            fontSize=16,
            spaceAfter=20,
            alignment=1  # 중앙 정렬
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=korean_font,
            fontSize=12
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=korean_font,
            fontSize=14
        )
        
        # 컨텐츠 리스트
        story = []
        
        # 제목
        story.append(Paragraph(f"{self.report_title} 보고서", title_style))
        story.append(Spacer(1, 12))
        
        # 필터 조건 표시
        filter_info = self.create_filter_info(filters)
        if filter_info:
            story.append(Paragraph("검색 조건:", heading_style))
            story.append(Paragraph(filter_info, normal_style))
            story.append(Spacer(1, 12))
        
        # 출력 정보
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        story.append(Paragraph(f"출력일시: {current_time}", normal_style))
        story.append(Paragraph(f"총 건수: {len(data):,}건", normal_style))
        story.append(Spacer(1, 20))
        
        # 테이블 데이터 생성
        if data:
            table_data = self.create_table_data(data)
            
            # 테이블 생성
            table = Table(table_data, repeatRows=1)
            
            # 테이블 스타일 적용 (한글 폰트 포함)
            table.setStyle(TableStyle([
                # 헤더 스타일
                ('BACKGROUND', (0, 0), (-1, 0), colors.yellow),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), korean_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # 데이터 행 스타일
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), korean_font),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # 줄무늬 효과
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(table)
        else:
            story.append(Paragraph("조회된 데이터가 없습니다.", normal_style))
        
        # PDF 빌드
        doc.build(story)
        
        # 버퍼 내용 반환
        buffer.seek(0)
        return buffer.read()
    
    def create_filter_info(self, filters):
        """필터 조건 문자열 생성"""
        filter_parts = []
        
        if filters.get('startDate') or filters.get('endDate'):
            start = filters.get('startDate', '시작일 없음')
            end = filters.get('endDate', '종료일 없음')
            filter_parts.append(f"기간: {start} ~ {end}")
        
        if filters.get('userId'):
            filter_parts.append(f"사용자 ID: {filters['userId']}")
        
        if filters.get('content'):
            filter_parts.append(f"작업내용: {filters['content']}")
        
        if filters.get('comment'):
            filter_parts.append(f"코멘트: {filters['comment']}")
        
        return " | ".join(filter_parts) if filter_parts else "전체 데이터"
    
    def create_table_data(self, data):
        """테이블 데이터 생성"""
        # 헤더 행
        if self.comment_join:
            headers = ['일시', '사용자 ID', '작업내용', '코멘트']
        else:
            headers = ['일시', '사용자 ID', '작업내용']
        
        table_data = [headers]
        
        # 데이터 행 추가
        for row in data:
            # 날짜 포맷팅
            create_dt = row.get('CREATE_DT', '')
            if create_dt:
                if isinstance(create_dt, str):
                    try:
                        dt = datetime.fromisoformat(create_dt.replace('Z', '+00:00'))
                        create_dt = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        create_dt = str(create_dt)
                else:
                    create_dt = create_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 사용자 ID
            user_id = row.get('USER_ID', '') or ''
            
            # 작업내용
            content = row.get('CONTENT', '') or ''
            
            if self.comment_join:
                # 코멘트 (20자 제한)
                comment = row.get('COMMENT_CONTENT', '') or ''
                if len(comment) > 20:
                    comment = comment[:20] + '...'
                
                table_data.append([create_dt, user_id, content, comment])
            else:
                table_data.append([create_dt, user_id, content])
        
        return table_data

# 각 히스토리 테이블별 서비스 인스턴스 생성
equipment_history_service = HistoryService('EQUIPMENT_HISTORY', True, '설비 가동 이력', 'Equipment Operation History')
alarm_history_service = HistoryService('ALARM_HISTORY', True, '설비 알람 이력', 'Equipment Alarm History')
report_history_service = HistoryService('REPORT_HISTORY', True, '보고서 생성 이력', 'Report Generation History')
login_history_service = HistoryService('LOGIN_HISTORY', True, '접속 이력', 'Login/Logout History')
user_history_service = HistoryService('USER_HISTORY', True, '사용자 관리 이력', 'User Management History')
data_history_service = HistoryService('DATA_HISTORY', True, '데이터 관리 이력', 'Data Management History')

# API 엔드포인트 함수들
async def get_equipment_history(request: Request):
    return await equipment_history_service.get_history_data(request)

async def export_equipment_history(request: Request):
    return await equipment_history_service.export_history_data(request)

async def get_alarm_history(request: Request):
    return await alarm_history_service.get_history_data(request)

async def export_alarm_history(request: Request):
    return await alarm_history_service.export_history_data(request)

async def get_report_history(request: Request):
    return await report_history_service.get_history_data(request)

async def export_report_history(request: Request):
    return await report_history_service.export_history_data(request)

async def get_login_history(request: Request):
    return await login_history_service.get_history_data(request)

async def export_login_history(request: Request):
    return await login_history_service.export_history_data(request)

async def get_user_history(request: Request):
    return await user_history_service.get_history_data(request)

async def export_user_history(request: Request):
    return await user_history_service.export_history_data(request)

async def get_data_history(request: Request):
    return await data_history_service.get_history_data(request)

async def export_data_history(request: Request):
    return await data_history_service.export_history_data(request)