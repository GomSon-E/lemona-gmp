import asyncio
import pymcprotocol
from datetime import datetime
from database import get_db_connection
from mysql.connector import Error

class PLCDataCollector:
    def __init__(self):
        self.client = None
        self.running = False
        self.plc_ip = "192.168.1.1"
        self.plc_port = 5000
        self.heartbeat_counter = 0

    # ! PLC 데이터 수집 시작
    async def start_collection(self):
        print("PLC 데이터 수집 시작...")
        
        try:
            # PLC 연결
            self.client = pymcprotocol.Type3E()
            self.client.connect(self.plc_ip, self.plc_port)
            print(f"PLC {self.plc_ip}:{self.plc_port}에 연결 완료")
            
            self.running = True
            
            # 동시 실행할 태스크들
            tasks = [
                asyncio.create_task(self.heartbeat_task()),
                asyncio.create_task(self.monitor_equipment_status()),
                asyncio.create_task(self.monitor_alarm_status()),
                asyncio.create_task(self.monitor_daily_production()),
                asyncio.create_task(self.monitor_model_change()),
                asyncio.create_task(self.update_pc_time())
            ]
            
            # 모든 태스크 실행
            await asyncio.gather(*tasks)
            
        except Exception as e:
            print(f"PLC 데이터 수집 시작 오류: {e}")
        finally:
            await self.stop_collection()
    
    # ! PLC 데이터 수집 중지
    async def stop_collection(self):
        print("PLC 데이터 수집 중지...")
        self.running = False
        
        if self.client:
            try:
                self.client.close()
                print("PLC 연결 종료 완료")
            except Exception as e:
                print(f"PLC 연결 종료 오류: {e}")
    
    async def heartbeat_task(self):
        """6000번 주소에 1초마다 0과 1을 번갈아가며 쓰기"""
        while self.running:
            try:
                value = self.heartbeat_counter % 2
                self.client.batchwrite_wordunits(headdevice="D6000", values=[value])
                self.heartbeat_counter += 1
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Heartbeat 오류: {e}")
                await asyncio.sleep(5)  # 오류 시 5초 대기
    
    # ! 6001번 주소 모니터링 - 설비 운전 상태
    async def monitor_equipment_status(self):
        while self.running:
            try:
                values = self.client.batchread_wordunits(headdevice="D6001", readsize=1)
                status_value = values[0]
                
                if status_value != 0:
                    # 상태 메시지 매핑
                    status_messages = {
                        1: "자동 OFF", 2: "자동 ON", 3: "수동",
                        4: "자동운전 대기", 5: "자동운전 중"
                    }
                    
                    message = status_messages.get(status_value, f"알 수 없는 상태: {status_value}")
                    content = f"설비 상태 변경: {message}"
                    
                    # 최근 로그인 사용자 정보 조회
                    user_id, comment_id = await self.get_latest_login_info()
                    
                    # EQUIPMENT_HISTORY에 저장
                    await self.save_equipment_history(content, user_id, comment_id)
                    
                    # 다시 0으로 쓰기
                    self.client.batchwrite_wordunits(headdevice="D6001", values=[0])
                    print(f"설비 상태 변경 감지: {content} (User: {user_id})")
                
                await asyncio.sleep(0.5)  # 0.5초마다 체크
                
            except Exception as e:
                print(f"설비 상태 모니터링 오류: {e}")
                await asyncio.sleep(5)
    
    # ! 6004번 주소 모니터링 - 알람 상태
    async def monitor_alarm_status(self):
        while self.running:
            try:
                values = self.client.batchread_wordunits(headdevice="D6004", readsize=1)
                alarm_id = values[0]
                
                if alarm_id != 0:
                    # ALARM_LIST에서 알람 내용 조회
                    alarm_content = await self.get_alarm_content(alarm_id)
                    
                    # 최근 로그인 사용자 정보 조회
                    user_id, comment_id = await self.get_latest_login_info()
                    
                    if alarm_content:
                        # ALARM_HISTORY에 저장
                        await self.save_alarm_history(alarm_content, user_id, comment_id)
                        print(f"알람 발생: ID {alarm_id} - {alarm_content} (User: {user_id})")
                    else:
                        await self.save_alarm_history(f"알 수 없는 알람 ID: {alarm_id}", user_id, comment_id)
                        print(f"알 수 없는 알람 ID: {alarm_id} (User: {user_id})")
                    
                    # 다시 0으로 쓰기
                    self.client.batchwrite_wordunits(headdevice="D6004", values=[0])
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"알람 상태 모니터링 오류: {e}")
                await asyncio.sleep(5)
    
    # ! 6005번 주소 모니터링 - 일 생산수량
    async def monitor_daily_production(self):
        while self.running:
            try:
                # 2워드 읽기 (D6006, D6007)
                values = self.client.batchread_wordunits(headdevice="D6006", readsize=2)
                production_count_low = values[0]   # 하위 워드
                production_count_high = values[1]  # 상위 워드
                
                # 2워드를 32비트 정수로 결합
                production_count = (production_count_high << 16) + production_count_low
                
                if production_count != 0:
                    content = f"일 생산수량: {production_count}개"
                    
                    # 최근 로그인 사용자 정보 조회
                    user_id, comment_id = await self.get_latest_login_info()
                    
                    # EQUIPMENT_HISTORY에 저장
                    await self.save_equipment_history(content, user_id, comment_id)
                    print(f"일 생산수량 업데이트: {content} (User: {user_id})")
                    
                    # 두 워드 모두 0으로 쓰기
                    self.client.batchwrite_wordunits(headdevice="D6006", values=[0, 0])
                
                await asyncio.sleep(0.5)
            
            except Exception as e:
                print(f"일 생산수량 모니터링 오류: {e}")
                await asyncio.sleep(5)
    
    # ! 6010번 주소 모니터링 - 모델 변경
    async def monitor_model_change(self):
        while self.running:
            try:
                values = self.client.batchread_wordunits(headdevice="D6010", readsize=1)
                model_number = values[0]
                
                if model_number != 0:
                    # 6011번에서 모델 타입 읽기
                    model_type_values = self.client.batchread_wordunits(headdevice="D6011", readsize=1)
                    model_type = model_type_values[0]
                    
                    # 6020~6029번에서 모델 품번 읽기 (10개)
                    part_numbers = self.client.batchread_wordunits(headdevice="D6020", readsize=10)
                    
                    # 아스키 코드를 문자열로 변환
                    part_number_str = self.convert_words_to_string(part_numbers)
                    
                    content = f"모델 변경 - 모델번호: {model_number}, 모델타입: {model_type}, 품번: {part_number_str}"
                    
                    # 최근 로그인 사용자 정보 조회
                    user_id, comment_id = await self.get_latest_login_info()
                    
                    # EQUIPMENT_HISTORY에 저장
                    await self.save_equipment_history(content, user_id, comment_id)
                    print(f"모델 변경 감지: {content} (User: {user_id})")
                    
                    # 6010번에 0 쓰기
                    self.client.batchwrite_wordunits(headdevice="D6010", values=[0])
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"모델 변경 모니터링 오류: {e}")
                await asyncio.sleep(5)

    # ! 아스키 코드 리스트를 문자열로 변환
    def convert_words_to_string(self, word_values):
        try:
            result = ""
            
            for word_value in word_values:
                if word_value == 0:  # 0이면 문자열 종료
                    break
                    
                # 16비트를 상위 8비트와 하위 8비트로 분할
                high_byte = (word_value >> 8) & 0xFF  # 상위 8비트
                low_byte = word_value & 0xFF          # 하위 8비트
                
                # 하위 바이트 처리
                if low_byte != 0:  # 0이 아닌 경우만 처리
                    if 32 <= low_byte <= 126:  # 출력 가능한 아스키 문자
                        result += chr(low_byte)
                    elif low_byte == 32:  # 공백 문자도 포함하되 연속 공백은 하나로
                        if not result.endswith(' '):
                            result += ' '

                # 상위 바이트 처리
                if high_byte != 0:  # 0이 아닌 경우만 처리
                    if 32 <= high_byte <= 126:  # 출력 가능한 아스키 문자
                        result += chr(high_byte)
                    elif high_byte == 32:  # 공백 문자도 포함하되 연속 공백은 하나로
                        if not result.endswith(' '):
                            result += ' '
            
            return result.strip()  # 앞뒤 공백 제거
        
        except Exception as e:
            print(f"16비트 워드 변환 오류: {e}")
            return "변환 실패"
    
    # ! 6040, 6041, 6042번에 PC 시간 쓰기
    async def update_pc_time(self):
        while self.running:
            try:
                now = datetime.now()
                hour = now.hour
                minute = now.minute
                second = now.second
                
                # 시, 분, 초를 각각 쓰기
                self.client.batchwrite_wordunits(headdevice="D6040", values=[hour])
                self.client.batchwrite_wordunits(headdevice="D6041", values=[minute])
                self.client.batchwrite_wordunits(headdevice="D6042", values=[second])
                
                await asyncio.sleep(1)  # 1초마다 업데이트
                
            except Exception as e:
                print(f"PC 시간 업데이트 오류: {e}")
                await asyncio.sleep(5)
    
    # ! 6002번에 사용자 권한 레벨 쓰기
    async def write_user_level(self, role_id):
        try:
            # ROLE_ID를 PLC 값으로 매핑
            role_mapping = {4: 1, 3: 2, 2: 3}  # USER:1, MANAGER:2, ADMIN:3
            plc_value = role_mapping.get(role_id, 0)
            
            if self.client:
                self.client.batchwrite_wordunits(headdevice="D6002", values=[plc_value])
                print(f"사용자 권한 레벨 업데이트: ROLE_ID {role_id} -> PLC값 {plc_value}")
        except Exception as e:
            print(f"사용자 권한 레벨 쓰기 오류: {e}")
    
    # ! ALARM_LIST에서 알람 내용 조회
    async def get_alarm_content(self, alarm_id):
        try:
            with get_db_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                query = "SELECT CONTENT FROM ALARM_LIST WHERE ID = %s"
                cursor.execute(query, (alarm_id,))
                result = cursor.fetchone()
                return result['CONTENT'] if result else None
        except Exception as e:
            print(f"알람 내용 조회 오류: {e}")
            return None
    
    # ! EQUIPMENT_HISTORY에 로그 저장
    async def save_equipment_history(self, content, user_id=None, comment_id=None):
        try:
            with get_db_connection() as connection:
                cursor = connection.cursor()
                query = """
                    INSERT INTO EQUIPMENT_HISTORY (CONTENT, USER_ID, COMMENT_ID, CREATE_DT)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (content, user_id, comment_id, datetime.now()))
                connection.commit()
        except Exception as e:
            print(f"설비 이력 저장 오류: {e}")
    
    # ! ALARM_HISTORY에 알람 이력 저장
    async def save_alarm_history(self, content, user_id=None, comment_id=None):
        try:
            with get_db_connection() as connection:
                cursor = connection.cursor()
                query = """
                    INSERT INTO ALARM_HISTORY (CONTENT, USER_ID, COMMENT_ID, CREATE_DT)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (content, user_id, comment_id, datetime.now()))
                connection.commit()
        except Exception as e:
            print(f"알람 이력 저장 오류: {e}")

    # ! 가장 최근 로그인한 사용자 정보 조회
    async def get_latest_login_info(self):
        try:
            with get_db_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # 가장 최근 로그인 성공 기록 조회
                query = """
                    SELECT USER_ID, COMMENT_ID 
                    FROM LOGIN_HISTORY 
                    WHERE CONTENT = '로그인 성공' 
                    ORDER BY CREATE_DT DESC 
                    LIMIT 1
                """
                cursor.execute(query)
                result = cursor.fetchone()
                
                if result:
                    return result['USER_ID'], result['COMMENT_ID']
                else:
                    return None, None
                    
        except Exception as e:
            print(f"최근 로그인 정보 조회 오류: {e}")
            return None, None

# 전역 PLC 수집기 인스턴스
plc_collector = PLCDataCollector()