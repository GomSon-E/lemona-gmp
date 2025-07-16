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
    def __init__(self, table_name, comment_join=True, report_title=""):
        self.table_name = table_name
        self.comment_join = comment_join
        self.report_title = report_title
    
    async def get_history_data(self, request: Request):
        try:
            # 쿼리 파라미터 추출
            params = dict(request.query_params)
            start_datetime = params.get('startDateTime')
            end_datetime = params.get('endDateTime')
            user_id = params.get('userId', '').strip()
            content = params.get('content', '').strip()
            comment = params.get('comment', '').strip()
            last_update_time = params.get('lastUpdateTime')
            incremental = params.get('incremental', 'false').lower() == 'true'
            
            with get_db_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # 기본 쿼리 구성 (기존과 동일)
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
                
                # 증분 업데이트인 경우
                if incremental and last_update_time:
                    where_conditions.append("h.CREATE_DT > %s")
                    query_params.append(last_update_time)
                else:
                    # 전체 조회인 경우 - 날짜+시간 조건 적용
                    if start_datetime:
                        where_conditions.append("h.CREATE_DT >= %s")
                        query_params.append(start_datetime)
                    
                    if end_datetime:
                        where_conditions.append("h.CREATE_DT <= %s")
                        query_params.append(end_datetime)
                
                # 나머지 조건들 (기존과 동일)
                if user_id:
                    where_conditions.append("h.USER_ID LIKE %s")
                    query_params.append(f"%{user_id}%")
                
                if content:
                    where_conditions.append("h.CONTENT LIKE %s")
                    query_params.append(f"%{content}%")
                
                if comment and self.comment_join:
                    where_conditions.append("c.CONTENT LIKE %s")
                    query_params.append(f"%{comment}%")
                
                # WHERE 절 추가 (기존과 동일)
                if where_conditions:
                    base_query += " WHERE " + " AND ".join(where_conditions)
                
                # 정렬 추가
                data_query = base_query + " ORDER BY h.CREATE_DT DESC"

                print(f"실행할 쿼리: {data_query}")
                print(f"쿼리 파라미터: {query_params}")
                
                cursor.execute(data_query, query_params)
                data = cursor.fetchall()
                
                # 날짜 포맷팅 (기존과 동일)
                for row in data:
                    if 'CREATE_DT' in row and row['CREATE_DT']:
                        row['CREATE_DT'] = row['CREATE_DT'].isoformat()
                
                return JSONResponse({
                    "success": True,
                    "data": data,
                    "incremental": incremental,
                    "count": len(data),
                    "serverTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
            start_datetime = params.get('startDateTime')
            end_datetime = params.get('endDateTime')
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
                
                if start_datetime:
                    where_conditions.append("h.CREATE_DT >= %s")
                    query_params.append(start_datetime)
                
                if end_datetime:
                    where_conditions.append("h.CREATE_DT <= %s")
                    query_params.append(end_datetime)
                
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
                report_content = f"보고서 생성 - {self.report_title}"
                
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
        
        # 검색 조건을 표 형태로 표시 (항상 표시)
        story.append(Paragraph("검색 조건:", heading_style))
        
        filter_table_data = self.create_filter_table_data(filters)
        
        # 4개 컬럼 균등 분배 (총 8인치)
        filter_col_widths = [2*inch, 2*inch, 2*inch, 2*inch]
        
        # 검색 조건 테이블 생성
        filter_table = Table(filter_table_data, colWidths=filter_col_widths)
        filter_table.setStyle(TableStyle([
            # 헤더 스타일
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),  # 헤더 폰트 크기
            ('FONTSIZE', (0, 1), (-1, 1), 9),   # 데이터 폰트 크기
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(filter_table)
        story.append(Spacer(1, 12))
        
        # 출력 정보
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_info_data = [
            ['출력일시', current_time],
            ['총 건수', f'{len(data):,}건']
        ]
        
        story.append(Paragraph("보고서 정보:", heading_style))
        
        # 보고서 정보 테이블 생성
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
        # 보고서 정보 헤더와 데이터
        report_info_header = ['출력일시', '총 건수']
        report_info_data = [current_time, f'{len(data):,}건']
        report_info_table_data = [report_info_header, report_info_data]
        
        # 보고서 정보 테이블 생성
        report_info_col_widths = [4*inch, 4*inch]
        report_info_table = Table(report_info_table_data, colWidths=report_info_col_widths)
        report_info_table.setStyle(TableStyle([
            # 헤더 스타일
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), korean_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),  # 헤더 폰트 크기
            ('FONTSIZE', (0, 1), (-1, 1), 9),   # 데이터 폰트 크기
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(report_info_table)
        story.append(Spacer(1, 20))
        
        # 테이블 데이터 생성
        if data:
            table_data = self.create_table_data(data)

            col_widths = [
                1.5*inch,   # 일시
                1.2*inch,   # 사용자 ID
                4.8*inch,   # 작업내용
                3*inch   # 코멘트
            ]
            
            # 테이블 생성
            table = Table(table_data, repeatRows=1, colWidths=col_widths)
            
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
    
    def create_filter_table_data(self, filters):
        """검색 조건 테이블 데이터 생성"""
        
        # 헤더 행
        header_row = ['기간', '사용자 ID', '작업내용', '코멘트']
        
        # 데이터 행
        data_row = []
        
        # 기간
        if filters.get('startDate') or filters.get('endDate'):
            start = filters.get('startDate', '')
            end = filters.get('endDate', '')
            if start and end:
                period_value = f'{start} ~ {end}'
            elif start:
                period_value = f'{start} ~'
            elif end:
                period_value = f'~ {end}'
            else:
                period_value = ''
        else:
            period_value = ''
        data_row.append(period_value)
        
        # 사용자 ID
        data_row.append(filters.get('userId', ''))
        
        # 작업내용
        data_row.append(filters.get('content', ''))
        
        # 코멘트
        data_row.append(filters.get('comment', ''))
        
        return [header_row, data_row]
    
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
equipment_history_service = HistoryService('EQUIPMENT_HISTORY', True, '설비 가동 이력')
alarm_history_service = HistoryService('ALARM_HISTORY', True, '설비 알람 이력')
report_history_service = HistoryService('REPORT_HISTORY', True, '보고서 생성 이력')
login_history_service = HistoryService('LOGIN_HISTORY', True, '접속 이력')
user_history_service = HistoryService('USER_HISTORY', True, '사용자 관리 이력')
data_history_service = HistoryService('DATA_HISTORY', True, '데이터 관리 이력')

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