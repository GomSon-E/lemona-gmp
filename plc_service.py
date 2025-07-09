from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time
import pymcprotocol

app = FastAPI()

PLC_IP = "192.168.1.1"
PLC_PORT = 5000
def connect_plc():
    """PLC 연결 (MC 프로토콜)"""
    client = None
    try:
        client = pymcprotocol.Type3E()
        print(f"PLC {PLC_IP}:{PLC_PORT}에 연결을 시도합니다...")
        client.connect(PLC_IP, PLC_PORT)
        print("PLC 연결에 성공했습니다!")
        return client
    except Exception as e:
        print(f"PLC 연결 오류: {e}")
        if client:
            client.close()
        return None

def disconnect_plc(client):
    """PLC 연결 해제 (MC 프로토콜)"""
    try:
        if client:
            client.close()
            print("PLC 연결 종료 완료.")
    except Exception as e:
        print(f"PLC 연결 해제 오류: {e}")

# ! PLC 데이터 읽기 엔드포인트
async def read_plc_data():
    """6000번 메모리 읽기 및 6008번에 읽기 완료 신호 전송 (MC 프로토콜)"""
    client = None
    try:
        # PLC 연결
        client = connect_plc()
        if not client:
            return JSONResponse({
                "success": False,
                "message": "PLC 연결에 실패했습니다."
            }, status_code=500)

        # 1. D6000에서 word 값 읽기
        print("D6000 디바이스의 값을 읽는 중...")
        d6000_values = client.batchread_wordunits(headdevice="D6000", readsize=1)
        
        data_value = d6000_values[0]
        print(f"D6000에서 읽은 값: {data_value}")

        # 1. D6008에 word 값 쓰기
        print("D6008 디바이스에 값 1을 쓰는 중...")
        client.batchwrite_wordunits(headdevice="D6008", values=[1])
        print("D6008에 값 1 쓰기 완료!")

        return JSONResponse({
            "success": True,
            "message": "PLC 데이터 읽기 및 신호 전송 완료",
            "data": {
                "address": "D6000",
                "value": data_value,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "signal_sent": True
            }
        })

    except Exception as e:
        print(f"PLC 통신 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": f"PLC 통신 중 오류가 발생했습니다: {str(e)}"
        }, status_code=500)
    finally:
        disconnect_plc(client)

# ! PLC 상태 확인 엔드포인트
async def check_plc_status():
    """PLC 연결 상태 확인 (MC 프로토콜)"""
    client = None
    try:
        client = connect_plc()
        if client:
            disconnect_plc(client)
            return JSONResponse({
                "success": True,
                "message": "PLC 연결 상태 양호",
                "data": {
                    "ip": PLC_IP,
                    "port": PLC_PORT,
                    "status": "connected",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "PLC 연결 실패",
                "data": {
                    "ip": PLC_IP,
                    "port": PLC_PORT,
                    "status": "disconnected",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }, status_code=500)

    except Exception as e:
        print(f"PLC 상태 확인 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": f"PLC 상태 확인 중 오류가 발생했습니다: {str(e)}"
        }, status_code=500)
    finally:
        disconnect_plc(client)
