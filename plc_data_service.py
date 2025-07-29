import asyncio
import pymcprotocol
from datetime import datetime
from database import get_db_connection
from mysql.connector import Error
import logging

# 로깅 설정
logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PLCDataCollector:
   def __init__(self):
       self.client = None
       self.running = False
       self.plc_ip = "192.168.1.1"
       self.plc_port = 5000
       self.heartbeat_counter = 0
       self.connection_retry_count = 0
       self.max_retry_attempts = 3
       self.reconnect_delay = 10  # 재연결 대기 시간 (초)
       self.connection_timeout = 30  # 연결 타임아웃 (초)

   async def connect_with_retry(self):
       """재연결 로직이 포함된 PLC 연결"""
       for attempt in range(self.max_retry_attempts):
           try:
               # 기존 연결 정리
               if self.client:
                   try:
                       self.client.close()
                   except:
                       pass
                   self.client = None
               
               # 새로운 연결 시도
               self.client = pymcprotocol.Type3E()
               logger.info(f"PLC {self.plc_ip}:{self.plc_port}에 연결 시도 중... (시도 {attempt + 1}/{self.max_retry_attempts})")
               
               # 연결 시도
               self.client.connect(self.plc_ip, self.plc_port)
               
               # 연결 테스트
               test_values = self.client.batchread_wordunits(headdevice="D6000", readsize=1)
               
               logger.info(f"PLC 연결 성공 (시도 {attempt + 1}/{self.max_retry_attempts})")
               self.connection_retry_count = 0
               return True
               
           except Exception as e:
               logger.error(f"PLC 연결 실패 (시도 {attempt + 1}/{self.max_retry_attempts}): {e}")
               if self.client:
                   try:
                       self.client.close()
                   except:
                       pass
                   self.client = None
                   
               if attempt < self.max_retry_attempts - 1:
                   logger.info(f"{self.reconnect_delay}초 후 재시도...")
                   await asyncio.sleep(self.reconnect_delay)
               
       logger.error("PLC 연결 최종 실패")
       return False

   async def start_collection(self):
       """PLC 데이터 수집 시작"""
       logger.info("PLC 데이터 수집 시작...")
       
       # 초기 연결 시도
       if not await self.connect_with_retry():
           logger.error("PLC 연결 실패로 데이터 수집을 시작할 수 없습니다.")
           return
       
       self.running = True
       
       try:
           # 동시 실행할 태스크들
           tasks = [
               asyncio.create_task(self.heartbeat_task()),
               asyncio.create_task(self.monitor_equipment_status()),
               asyncio.create_task(self.monitor_alarm_status()),
               asyncio.create_task(self.monitor_daily_production()),
               asyncio.create_task(self.monitor_model_change()),
               asyncio.create_task(self.update_pc_time()),
               asyncio.create_task(self.connection_monitor())  # 연결 모니터링 태스크 추가
           ]
           
           # 모든 태스크 실행 (예외 발생 시에도 계속 실행)
           results = await asyncio.gather(*tasks, return_exceptions=True)
           
           # 태스크 실행 결과 로깅
           for i, result in enumerate(results):
               if isinstance(result, Exception):
                   logger.error(f"태스크 {i} 실행 중 오류: {result}")
           
       except Exception as e:
           logger.error(f"PLC 데이터 수집 오류: {e}")
       finally:
           await self.stop_collection()

   async def stop_collection(self):
       """PLC 데이터 수집 중지"""
       logger.info("PLC 데이터 수집 중지...")
       self.running = False
       
       if self.client:
           try:
               self.client.close()
               logger.info("PLC 연결 종료 완료")
           except Exception as e:
               logger.error(f"PLC 연결 종료 오류: {e}")
           finally:
               self.client = None

   async def connection_monitor(self):
       """연결 상태 모니터링 및 재연결"""
       while self.running:
           try:
               await asyncio.sleep(30)  # 30초마다 연결 상태 확인
               
               if not self.client:
                   logger.warning("PLC 연결이 없습니다. 재연결 시도...")
                   await self.connect_with_retry()
                   continue
               
               # 간단한 연결 테스트
               try:
                   self.client.batchread_wordunits(headdevice="D6000", readsize=1)
                   logger.debug("PLC 연결 상태 정상")
               except Exception as e:
                   logger.error(f"PLC 연결 테스트 실패: {e}")
                   logger.info("PLC 재연결 시도...")
                   await self.connect_with_retry()
                   
           except Exception as e:
               logger.error(f"연결 모니터링 오류: {e}")
               await asyncio.sleep(5)

   async def safe_plc_operation(self, operation_func, *args, **kwargs):
       """안전한 PLC 작업 수행 (재연결 포함)"""
       max_attempts = 3
       
       for attempt in range(max_attempts):
           try:
               if not self.client:
                   if not await self.connect_with_retry():
                       return None
               
               return await operation_func(*args, **kwargs)
               
           except Exception as e:
               logger.error(f"PLC 작업 실패 (시도 {attempt + 1}/{max_attempts}): {e}")
               
               if attempt < max_attempts - 1:
                   logger.info("PLC 재연결 시도...")
                   await self.connect_with_retry()
                   await asyncio.sleep(1)
               else:
                   logger.error("PLC 작업 최종 실패")
                   return None

   async def heartbeat_task(self):
       """개선된 하트비트 태스크"""
       while self.running:
           try:
               await self.safe_plc_operation(self._heartbeat_operation)
               await asyncio.sleep(1)
           except Exception as e:
               logger.error(f"Heartbeat 오류: {e}")
               await asyncio.sleep(5)

   async def _heartbeat_operation(self):
       """실제 하트비트 작업"""
       value = self.heartbeat_counter % 2
       self.client.batchwrite_wordunits(headdevice="D6000", values=[value])
       self.heartbeat_counter += 1

   async def monitor_equipment_status(self):
       """6001번 주소 모니터링 - 설비 운전 상태"""
       while self.running:
           try:
               result = await self.safe_plc_operation(self._monitor_equipment_operation)
               if result:
                   status_value = result[0]
                   
                   if status_value != 0:
                       # 상태 메시지 매핑
                       status_messages = {
                           1: "전원 OFF", 2: "전원 ON", 3: "수동",
                           4: "자동운전 대기", 5: "자동운전 중"
                       }
                       
                       message = status_messages.get(status_value, f"알 수 없는 상태: {status_value}")
                       content = f"설비 상태 변경: {message}"
                       
                       # 최근 로그인 사용자 정보 조회
                       user_id, comment_id = await self.get_latest_login_info()
                       
                       # EQUIPMENT_HISTORY에 저장
                       await self.save_equipment_history(content, user_id, comment_id)
                       
                       # 다시 0으로 쓰기
                       await self.safe_plc_operation(self._reset_equipment_status)
                       logger.info(f"설비 상태 변경 감지: {content} (User: {user_id})")
               
               await asyncio.sleep(0.5)  # 0.5초마다 체크
               
           except Exception as e:
               logger.error(f"설비 상태 모니터링 오류: {e}")
               await asyncio.sleep(5)

   async def _monitor_equipment_operation(self):
       """실제 설비 상태 모니터링 작업"""
       return self.client.batchread_wordunits(headdevice="D6001", readsize=1)

   async def _reset_equipment_status(self):
       """설비 상태를 0으로 리셋"""
       self.client.batchwrite_wordunits(headdevice="D6001", values=[0])

   async def monitor_alarm_status(self):
       """6004번 주소 모니터링 - 알람 상태"""
       while self.running:
           try:
               result = await self.safe_plc_operation(self._monitor_alarm_operation)
               if result:
                   alarm_id = result[0]
                   
                   if alarm_id != 0:
                       # ALARM_LIST에서 알람 내용 조회
                       alarm_content = await self.get_alarm_content(alarm_id)
                       
                       # 최근 로그인 사용자 정보 조회
                       user_id, comment_id = await self.get_latest_login_info()
                       
                       if alarm_content:
                           # ALARM_HISTORY에 저장
                           await self.save_alarm_history(alarm_content, user_id, comment_id)
                           logger.info(f"알람 발생: ID {alarm_id} - {alarm_content} (User: {user_id})")
                       else:
                           await self.save_alarm_history(f"알 수 없는 알람 ID: {alarm_id}", user_id, comment_id)
                           logger.warning(f"알 수 없는 알람 ID: {alarm_id} (User: {user_id})")
                       
                       # 다시 0으로 쓰기
                       await self.safe_plc_operation(self._reset_alarm_status)
               
               await asyncio.sleep(0.5)
               
           except Exception as e:
               logger.error(f"알람 상태 모니터링 오류: {e}")
               await asyncio.sleep(5)

   async def _monitor_alarm_operation(self):
       """실제 알람 상태 모니터링 작업"""
       return self.client.batchread_wordunits(headdevice="D6004", readsize=1)

   async def _reset_alarm_status(self):
       """알람 상태를 0으로 리셋"""
       self.client.batchwrite_wordunits(headdevice="D6004", values=[0])

   async def monitor_daily_production(self):
       """6005번 주소 모니터링 - 일 생산수량"""
       while self.running:
           try:
               result = await self.safe_plc_operation(self._monitor_production_operation)
               if result:
                   production_count_low = result[0]   # 하위 워드
                   production_count_high = result[1]  # 상위 워드
                   
                   # 2워드를 32비트 정수로 결합
                   production_count = (production_count_high << 16) + production_count_low
                   
                   if production_count != 0:
                       content = f"일 생산수량: {production_count}개"
                       
                       # 최근 로그인 사용자 정보 조회
                       user_id, comment_id = await self.get_latest_login_info()
                       
                       # EQUIPMENT_HISTORY에 저장
                       await self.save_equipment_history(content, user_id, comment_id)
                       logger.info(f"일 생산수량 업데이트: {content} (User: {user_id})")
                       
                       # 두 워드 모두 0으로 쓰기
                       await self.safe_plc_operation(self._reset_production_count)
               
               await asyncio.sleep(0.5)
           
           except Exception as e:
               logger.error(f"일 생산수량 모니터링 오류: {e}")
               await asyncio.sleep(5)

   async def _monitor_production_operation(self):
       """실제 생산수량 모니터링 작업"""
       return self.client.batchread_wordunits(headdevice="D6006", readsize=2)

   async def _reset_production_count(self):
       """생산수량을 0으로 리셋"""
       self.client.batchwrite_wordunits(headdevice="D6006", values=[0, 0])

   async def monitor_model_change(self):
       """6010번 주소 모니터링 - 모델 변경"""
       while self.running:
           try:
               result = await self.safe_plc_operation(self._monitor_model_operation)
               if result:
                   model_number = result[0]
                   
                   if model_number != 0:
                       # 6011번에서 모델 타입 읽기
                       model_type_result = await self.safe_plc_operation(self._read_model_type)
                       model_type = model_type_result[0] if model_type_result else 0
                       
                       # 6020~6029번에서 모델 품번 읽기 (10개)
                       part_numbers_result = await self.safe_plc_operation(self._read_part_numbers)
                       part_numbers = part_numbers_result if part_numbers_result else []
                       
                       # 아스키 코드를 문자열로 변환
                       part_number_str = self.convert_words_to_string(part_numbers)
                       
                       content = f"모델 변경 - 모델번호: {model_number}, 모델타입: {model_type}, 품번: {part_number_str}"
                       
                       # 최근 로그인 사용자 정보 조회
                       user_id, comment_id = await self.get_latest_login_info()
                       
                       # EQUIPMENT_HISTORY에 저장
                       await self.save_equipment_history(content, user_id, comment_id)
                       logger.info(f"모델 변경 감지: {content} (User: {user_id})")
                       
                       # 6010번에 0 쓰기
                       await self.safe_plc_operation(self._reset_model_change)
               
               await asyncio.sleep(0.5)
               
           except Exception as e:
               logger.error(f"모델 변경 모니터링 오류: {e}")
               await asyncio.sleep(5)

   async def _monitor_model_operation(self):
       """실제 모델 변경 모니터링 작업"""
       return self.client.batchread_wordunits(headdevice="D6010", readsize=1)

   async def _read_model_type(self):
       """모델 타입 읽기"""
       return self.client.batchread_wordunits(headdevice="D6011", readsize=1)

   async def _read_part_numbers(self):
       """품번 읽기"""
       return self.client.batchread_wordunits(headdevice="D6020", readsize=10)

   async def _reset_model_change(self):
       """모델 변경 플래그를 0으로 리셋"""
       self.client.batchwrite_wordunits(headdevice="D6010", values=[0])

   def convert_words_to_string(self, word_values):
       """아스키 코드 리스트를 문자열로 변환"""
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
           logger.error(f"16비트 워드 변환 오류: {e}")
           return "변환 실패"

   async def update_pc_time(self):
       """6040, 6041, 6042번에 PC 시간 쓰기"""
       while self.running:
           try:
               await self.safe_plc_operation(self._update_time_operation)
               await asyncio.sleep(1)  # 1초마다 업데이트
               
           except Exception as e:
               logger.error(f"PC 시간 업데이트 오류: {e}")
               await asyncio.sleep(5)

   async def _update_time_operation(self):
       """실제 시간 업데이트 작업"""
       now = datetime.now()
       hour = now.hour
       minute = now.minute
       second = now.second
       
       # 시, 분, 초를 각각 쓰기
       self.client.batchwrite_wordunits(headdevice="D6040", values=[hour])
       self.client.batchwrite_wordunits(headdevice="D6041", values=[minute])
       self.client.batchwrite_wordunits(headdevice="D6042", values=[second])

   async def write_user_level(self, role_id):
       """6002번에 사용자 권한 레벨 쓰기"""
       try:
           await self.safe_plc_operation(self._write_user_level_operation, role_id)
       except Exception as e:
           logger.error(f"사용자 권한 레벨 쓰기 오류: {e}")

   async def _write_user_level_operation(self, role_id):
       """실제 사용자 권한 레벨 쓰기 작업"""
       # ROLE_ID를 PLC 값으로 매핑
       role_mapping = {4: 1, 3: 2, 2: 3}  # USER:1, MANAGER:2, ADMIN:3
       plc_value = role_mapping.get(role_id, 0)
       
       if self.client:
           self.client.batchwrite_wordunits(headdevice="D6002", values=[plc_value])
           logger.info(f"사용자 권한 레벨 업데이트: ROLE_ID {role_id} -> PLC값 {plc_value}")

   async def get_alarm_content(self, alarm_id):
       """ALARM_LIST에서 알람 내용 조회"""
       try:
           with get_db_connection() as connection:
               cursor = connection.cursor(dictionary=True)
               query = "SELECT CONTENT FROM ALARM_LIST WHERE ID = %s"
               cursor.execute(query, (alarm_id,))
               result = cursor.fetchone()
               return result['CONTENT'] if result else None
       except Exception as e:
           logger.error(f"알람 내용 조회 오류: {e}")
           return None

   async def save_equipment_history(self, content, user_id=None, comment_id=None):
       """EQUIPMENT_HISTORY에 로그 저장"""
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
           logger.error(f"설비 이력 저장 오류: {e}")

   async def save_alarm_history(self, content, user_id=None, comment_id=None):
       """ALARM_HISTORY에 알람 이력 저장"""
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
           logger.error(f"알람 이력 저장 오류: {e}")

   async def get_latest_login_info(self):
       """가장 최근 로그인한 사용자 정보 조회"""
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
           logger.error(f"최근 로그인 정보 조회 오류: {e}")
           return None, None

# 전역 PLC 수집기 인스턴스
plc_collector = PLCDataCollector()