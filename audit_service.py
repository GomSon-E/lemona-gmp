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

class AuditTrailService:
    def __init__(self):
        self.report_title = "Audit Trail"
    
    async def get_history_data(self, request: Request):
        try:
            # 쿼리 파라미터 추출
            params = dict(request.query_params)
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            user_id = params.get('userId', '').strip()
            content = params.get('content', '').strip()
            comment = params.get('comment', '').strip()
            last_update_time = params.get('lastUpdateTime')
            incremental = params.get('incremental', 'false').lower() == 'true'
            
            with get_db_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # 모든 히스토리 테이블을 UNION으로 통합
                base_query = """
                    (SELECT '설비 가동 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM EQUIPMENT_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '설비 알람 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM ALARM_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '보고서 생성 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM REPORT_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '접속 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM LOGIN_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '사용자 관리 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM USER_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '데이터 관리 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM DATA_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                """
                
                # WHERE 조건 구성
                where_conditions = []
                query_params = []
                
                # 서브쿼리로 감싸서 WHERE 조건 적용
                final_query = f"SELECT * FROM ({base_query}) as unified_history"
                
                if incremental and last_update_time:
                    where_conditions.append("CREATE_DT > %s")
                    query_params.append(last_update_time)
                else:
                    if start_date:
                        where_conditions.append("DATE(CREATE_DT) >= %s")
                        query_params.append(start_date)
                    
                    if end_date:
                        where_conditions.append("DATE(CREATE_DT) <= %s")
                        query_params.append(end_date)
                
                if user_id:
                    where_conditions.append("USER_ID LIKE %s")
                    query_params.append(f"%{user_id}%")
                
                if content:
                    where_conditions.append("CONTENT LIKE %s")
                    query_params.append(f"%{content}%")
                
                if comment:
                    where_conditions.append("COMMENT_CONTENT LIKE %s")
                    query_params.append(f"%{comment}%")
                
                # WHERE 절 추가
                if where_conditions:
                    final_query += " WHERE " + " AND ".join(where_conditions)
                
                # 정렬 추가
                final_query += " ORDER BY CREATE_DT DESC"
                
                print(f"실행할 쿼리: {final_query}")
                print(f"쿼리 파라미터: {query_params}")
                
                cursor.execute(final_query, query_params)
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
                    "serverTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
        except Error as e:
            print(f"Audit Trail 조회 오류: {e}")
            return JSONResponse({
                "success": False,
                "message": "Audit Trail 조회 중 오류가 발생했습니다."
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
            current_user_id = params.get('currentUserId', 'system')
            login_history_id = params.get('loginHistoryId')
            
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
                
                # 통합 데이터 조회
                base_query = """
                    (SELECT '설비 가동 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM EQUIPMENT_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '설비 알람 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM ALARM_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '보고서 생성 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM REPORT_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '접속 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM LOGIN_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '사용자 관리 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM USER_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                    UNION ALL
                    (SELECT '데이터 관리 이력' as CATEGORY, h.CREATE_DT, h.USER_ID, h.CONTENT, c.CONTENT as COMMENT_CONTENT
                     FROM DATA_HISTORY h
                     LEFT JOIN COMMENT c ON h.COMMENT_ID = c.COMMENT_ID)
                """
                
                final_query = f"SELECT * FROM ({base_query}) as unified_history"
                where_conditions = []
                query_params = []
                
                if start_datetime:
                    where_conditions.append("CREATE_DT >= %s")
                    query_params.append(start_datetime)

                if end_datetime:
                    where_conditions.append("CREATE_DT <= %s")
                    query_params.append(end_datetime)
                
                if user_id:
                    where_conditions.append("USER_ID LIKE %s")
                    query_params.append(f"%{user_id}%")
                
                if content:
                    where_conditions.append("CONTENT LIKE %s")
                    query_params.append(f"%{content}%")
                
                if comment:
                    where_conditions.append("COMMENT_CONTENT LIKE %s")
                    query_params.append(f"%{comment}%")
                
                if where_conditions:
                    final_query += " WHERE " + " AND ".join(where_conditions)
                
                final_query += " ORDER BY CREATE_DT DESC"
                
                cursor.execute(final_query, query_params)
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
            print(f"Audit Trail 보고서 생성 오류: {e}")
            return JSONResponse({
                "success": False,
                "message": "Audit Trail 보고서 생성 중 오류가 발생했습니다."
            })
        except Exception as e:
            print(f"예상치 못한 오류: {e}")
            return JSONResponse({
                "success": False,
                "message": "서버 내부 오류가 발생했습니다."
            })

    def generate_pdf_report(self, data, filters):
        buffer = io.BytesIO()
        
        # 한글 폰트 등록 (기존과 동일)
        try:
            font_path = "C:/Windows/Fonts/malgun.ttf"
            if not os.path.exists(font_path):
                font_path = "C:/Windows/Fonts/gulim.ttc"
            
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Korean', font_path))
                korean_font = 'Korean'
            else:
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
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=korean_font,
            fontSize=16,
            spaceAfter=20,
            alignment=1
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
        
        # 보고서 정보 섹션        
        story.append(Paragraph("보고서 정보:", heading_style))
        
        # 보고서 정보 테이블 생성
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
        # 보고서 정보 헤더와 데이터
        report_info_header = ['출력일시', '총 건수', '출력자ID']
        report_info_data = [current_time, f'{len(data):,}건', filters.get('currentUserId', 'system')]
        report_info_table_data = [report_info_header, report_info_data]
        
        # 보고서 정보 테이블 생성
        report_info_col_widths = [2.65*inch, 2.65*inch, 2.65*inch]
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
            
            # 테이블 생성
            table = Table(table_data, repeatRows=1)
            
            # 테이블 스타일 적용
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
        """테이블 데이터 생성 - CATEGORY 컬럼 추가"""
        # 헤더 행 (카테고리 추가)
        headers = ['카테고리', '일시', '사용자 ID', '작업내용', '코멘트']
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
            
            # 카테고리
            category = row.get('CATEGORY', '') or ''
            
            # 사용자 ID
            user_id = row.get('USER_ID', '') or ''
            
            # 작업내용 (40자 제한)
            content = row.get('CONTENT', '') or ''
            if len(content) > 40:
                content = content[:40] + '...'
            
            # 코멘트 (20자 제한)
            comment = row.get('COMMENT_CONTENT', '') or ''
            if len(comment) > 20:
                comment = comment[:20] + '...'
            
            table_data.append([category, create_dt, user_id, content, comment])
        
        return table_data

audit_trail_service = AuditTrailService()

async def get_audit_trail(request: Request):
    return await audit_trail_service.get_history_data(request)

async def export_audit_trail(request: Request):
    return await audit_trail_service.export_history_data(request)

# ! 코멘트 생성
async def create_comment(request: Request):
    try:
        comment_data = await request.json()
        content = comment_data['content']
        user_id = comment_data['userId']
        login_history_id = comment_data['loginHistoryId']
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            # 코멘트 생성
            insert_query = """
                INSERT INTO COMMENT (CONTENT, USER_ID)
                VALUES (%s, %s)
            """
            
            cursor.execute(insert_query, (content, user_id))
            comment_id = cursor.lastrowid
            
            # 로그인 기록에 코멘트 ID 업데이트
            update_login_history_query = """
                UPDATE LOGIN_HISTORY 
                SET COMMENT_ID = %s 
                WHERE ID = %s
            """
            cursor.execute(update_login_history_query, (comment_id, login_history_id))
            
            connection.commit()
            
            return JSONResponse({
                "success": True,
                "message": "코멘트가 성공적으로 저장되었습니다."
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
