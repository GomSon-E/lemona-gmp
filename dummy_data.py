import mysql.connector
import random
from datetime import datetime, timedelta
from faker import Faker

# 한글 locale 설정
fake = Faker('ko_KR')

# 데이터베이스 연결 설정
MYSQL_CONFIG = {
    'host': 'localhost!',
    'database': 'LEMONA_GMP',
    'user': 'root',
    'password': '1234!',
    'port': 3306,
    'charset': 'utf8mb4'
}

# 더미 데이터 생성 개수
TOTAL_RECORDS = 2000
RECORDS_PER_TABLE = TOTAL_RECORDS // 6  # 6개 테이블에 균등 분배

def get_existing_users(connection):
    """데이터베이스에서 실제 존재하는 사용자 ID 목록 조회"""
    cursor = connection.cursor()
    cursor.execute("SELECT USER_ID FROM USER WHERE STATUS = TRUE")
    users = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return users

def generate_dummy_data(user_ids):
    """더미 데이터 생성"""
    
    # 설비 가동 이력 내용
    equipment_contents = [
        '설비 시작',
        '설비 정지',
        '자동 운전 시작',
        '자동 운전 정지',
        '수동 모드 전환',
        '생산 시작',
        '생산 완료',
        '정기 점검 시작',
        '정기 점검 완료',
        '비상 정지',
        '설비 재시작',
        '모터 가동',
        '컨베이어 시작',
        '온도 조절 시작',
        '압력 조절',
        '속도 조절',
        '설비 초기화',
        '센서 점검',
        '보정 작업 완료',
        '일일 점검 완료'
    ]
    
    # 알람 이력 내용 (ALARM_LIST 테이블의 내용 참조)
    alarm_contents = [
        '1축 투입 분리 서보 알람',
        '2축 간격조절 이송 서보 알람',
        'OP 비상정지 알람',
        '박스 투입 컨베어 비상정지 알람',
        '메인 에어 센서 알람',
        '도어1 열림 알람',
        '도어2 열림 알람',
        '로봇 핸드1 흡착 패드 교체주기 알람',
        '수량선별 병 공급 지연 알람',
        '간격조절 유닛 전진 병 간섭',
        '비전 Ready 신호 미확인 알람',
        '로봇 READY OFF 신호 이상',
        'PC 통신 이상 알람',
        '설비 온도 이상',
        '압력 센서 오류',
        '모터 과부하 알람'
    ]
    
    # 보고서 생성 이력 내용
    report_contents = [
        '보고서 생성 - 설비 가동 이력',
        '보고서 생성 - 설비 알람 이력',
        '보고서 생성 - 접속 이력',
        '보고서 생성 - 사용자 관리 이력',
        '보고서 생성 - 데이터 관리 이력',
        '보고서 생성 - Audit Trail',
        '일일 생산 보고서 생성',
        '주간 설비 점검 보고서 생성',
        '월간 운영 보고서 생성',
        '품질 관리 보고서 생성'
    ]
    
    # 접속 이력 내용
    login_contents = [
        '로그인 성공',
        '로그아웃 - 수동 로그아웃',
        '로그아웃 - 자동 로그아웃',
        '로그인 실패 - 비밀번호 불일치',
        '비밀번호 변경 후 로그인'
    ]
    
    # 사용자 관리 이력 내용
    user_management_contents = [
        '사용자 생성 - 새 직원 등록',
        '사용자 수정 - 부서 이동',
        '사용자 수정 - 권한 변경',
        '사용자 상태 변경 - 활성화',
        '사용자 상태 변경 - 비활성화',
        '비밀번호 초기화',
        '권한별 접근 페이지 설정',
        '사용자 권한 승급',
        '사용자 정보 업데이트',
        '계정 잠금 해제'
    ]
    
    # 데이터 관리 이력 내용
    data_management_contents = [
        '데이터 백업 - 자동 데이터 백업',
        '데이터 백업 - 수동 데이터 백업',
        '데이터 복원 완료',
        '데이터베이스 최적화',
        '테이블 정리 작업',
        '인덱스 재구성',
        '로그 파일 정리',
        '시스템 데이터 검증',
        '데이터 무결성 점검',
        '백업 파일 검증'
    ]
    
    # 코멘트 내용
    comments = [
        '정상 작업 완료',
        '이상 없음',
        '점검 필요',
        '추가 확인 요망',
        '조치 완료',
        '모니터링 지속',
        '예방 조치 필요',
        '정기 점검',
        '긴급 대응',
        '시스템 정상',
        '작업 완료 확인',
        '안전 점검 완료',
        '품질 관리 차원',
        '효율성 개선',
        '보안 강화 목적',
        None  # 코멘트 없는 경우도 포함
    ]
    
    # 2025년 7월 1일부터 7월 10일까지의 랜덤 시간 생성
    start_time = datetime(2025, 7, 1, 0, 0, 0)  # 2025-07-01 00:00:00
    end_time = datetime(2025, 7, 10, 23, 59, 59)  # 2025-07-10 23:59:59
    
    def random_datetime():
        time_between = end_time - start_time
        total_seconds = int(time_between.total_seconds())
        random_seconds = random.randrange(total_seconds)
        return start_time + timedelta(seconds=random_seconds)
    
    dummy_data = {
        'EQUIPMENT_HISTORY': [],
        'ALARM_HISTORY': [],
        'REPORT_HISTORY': [],
        'LOGIN_HISTORY': [],
        'USER_HISTORY': [],
        'DATA_HISTORY': []
    }
    
    # 코멘트 데이터 생성 (실제 필요한 만큼만 생성)
    # 전체 히스토리 레코드의 30% 정도만 코멘트 생성
    total_history_records = RECORDS_PER_TABLE * 6  # 6개 테이블
    estimated_comment_count = int(total_history_records * 0.3)  # 30%만 코멘트 필요
    
    comment_data = []
    for i in range(estimated_comment_count):
        comment_data.append({
            'content': random.choice([c for c in comments if c is not None]),
            'user_id': random.choice(user_ids)
        })
    
    # 각 테이블별 더미 데이터 생성
    for i in range(RECORDS_PER_TABLE):
        create_dt = random_datetime()
        user_id = random.choice(user_ids)
        
        # EQUIPMENT_HISTORY
        dummy_data['EQUIPMENT_HISTORY'].append({
            'content': random.choice(equipment_contents),
            'user_id': user_id,
            'create_dt': create_dt
        })
        
        # ALARM_HISTORY
        dummy_data['ALARM_HISTORY'].append({
            'content': random.choice(alarm_contents),
            'user_id': user_id,
            'create_dt': create_dt
        })
        
        # REPORT_HISTORY
        dummy_data['REPORT_HISTORY'].append({
            'content': random.choice(report_contents),
            'user_id': user_id,
            'create_dt': create_dt
        })
        
        # LOGIN_HISTORY
        dummy_data['LOGIN_HISTORY'].append({
            'content': random.choice(login_contents),
            'user_id': user_id,
            'create_dt': create_dt
        })
        
        # USER_HISTORY
        dummy_data['USER_HISTORY'].append({
            'content': random.choice(user_management_contents),
            'user_id': user_id,
            'create_dt': create_dt
        })
        
        # DATA_HISTORY
        dummy_data['DATA_HISTORY'].append({
            'content': random.choice(data_management_contents),
            'user_id': user_id,
            'create_dt': create_dt
        })
    
    return dummy_data, comment_data

def insert_dummy_data():
    """더미 데이터를 데이터베이스에 삽입"""
    
    try:
        # 데이터베이스 연결
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        # 실제 존재하는 사용자 ID 목록 조회
        print("기존 사용자 확인 중...")
        user_ids = get_existing_users(connection)
        
        if not user_ids:
            print("오류: 활성 사용자가 존재하지 않습니다.")
            print("먼저 사용자를 생성해주세요.")
            return
        
        print(f"발견된 활성 사용자: {user_ids}")
        
        print("더미 데이터 생성 중...")
        dummy_data, comment_data = generate_dummy_data(user_ids)
        
        # 1. 코멘트 데이터 먼저 삽입
        print("코멘트 데이터 삽입 중...")
        comment_ids = []
        comment_query = "INSERT INTO COMMENT (CONTENT, USER_ID) VALUES (%s, %s)"
        
        for comment in comment_data:
            cursor.execute(comment_query, (comment['content'], comment['user_id']))
            comment_ids.append(cursor.lastrowid)  # 방금 삽입된 코멘트 ID 저장
        
        connection.commit()
        print(f"코멘트 데이터 {len(comment_data)}개 삽입 완료")
        print(f"생성된 코멘트 ID 범위: {min(comment_ids) if comment_ids else 'None'} ~ {max(comment_ids) if comment_ids else 'None'}")
        
        # 2. 각 히스토리 테이블에 데이터 삽입
        for table_name, records in dummy_data.items():
            print(f"\n{table_name} 테이블에 데이터 삽입 중...")
            
            # 랜덤하게 일부 레코드에만 코멘트 ID 할당
            for i, record in enumerate(records):
                if random.random() < 0.3 and comment_ids:  # 30% 확률로 코멘트 추가
                    record['comment_id'] = random.choice(comment_ids)
                else:
                    record['comment_id'] = None
            
            # INSERT 쿼리 실행
            insert_query = f"""
                INSERT INTO {table_name} (CONTENT, USER_ID, COMMENT_ID, CREATE_DT)
                VALUES (%s, %s, %s, %s)
            """
            
            batch_size = 100  # 배치 단위로 처리
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                for record in batch:
                    cursor.execute(insert_query, (
                        record['content'],
                        record['user_id'],
                        record['comment_id'],
                        record['create_dt']
                    ))
                connection.commit()
                print(f"  진행률: {min(i + batch_size, len(records))}/{len(records)}")
            
            print(f"{table_name}: {len(records)}개 레코드 삽입 완료")
        
        print("\n=== 더미 데이터 삽입 완료 ===")
        print(f"총 {sum(len(records) for records in dummy_data.values())}개의 히스토리 레코드가 생성되었습니다.")
        print(f"총 {len(comment_data)}개의 코멘트가 생성되었습니다.")
        
        # 각 테이블별 레코드 수 확인
        print("\n=== 테이블별 레코드 수 확인 ===")
        for table_name in dummy_data.keys():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_name}: {count}개")
        
        cursor.execute("SELECT COUNT(*) FROM COMMENT")
        comment_count = cursor.fetchone()[0]
        print(f"COMMENT: {comment_count}개")
        
        # 코멘트와 연결된 히스토리 레코드 수 확인
        print("\n=== 코멘트 연결 상태 확인 ===")
        for table_name in dummy_data.keys():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE COMMENT_ID IS NOT NULL")
            count_with_comment = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_count = cursor.fetchone()[0]
            percentage = (count_with_comment / total_count * 100) if total_count > 0 else 0
            print(f"{table_name}: {count_with_comment}/{total_count} ({percentage:.1f}%) 코멘트 연결")
        
    except mysql.connector.Error as e:
        print(f"데이터베이스 오류: {e}")
        connection.rollback()
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n데이터베이스 연결이 종료되었습니다.")

if __name__ == "__main__":
    print("=== LEMONA GMP 히스토리 더미 데이터 생성기 ===")
    print(f"총 {TOTAL_RECORDS}개의 더미 데이터를 생성합니다.")
    print(f"각 테이블당 약 {RECORDS_PER_TABLE}개씩 분배됩니다.")
    
    confirm = input("\n계속하시겠습니까? (y/N): ")
    if confirm.lower() in ['y', 'yes']:
        insert_dummy_data()
    else:
        print("작업이 취소되었습니다.")