from fastapi import Request
from fastapi.responses import JSONResponse
from pymodbus.client import ModbusTcpClient
import time

# PLC 설정
PLC_IP = "192.168.1.1"
PLC_PORT = 8500

def connect_plc():
    """PLC 연결"""
    try:
        client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
        connection = client.connect()
        if connection:
            return client
        else:
            return None
    except Exception as e:
        print(f"PLC 연결 오류: {e}")
        return None

def disconnect_plc(client):
    """PLC 연결 해제"""
    try:
        if client:
            client.close()
    except Exception as e:
        print(f"PLC 연결 해제 오류: {e}")

# ! PLC 데이터 읽기
async def read_plc_data():
    """6000번 메모리 읽기 및 6008번에 읽기 완료 신호 전송"""
    client = None
    try:
        # PLC 연결
        client = connect_plc()
        if not client:
            return JSONResponse({
                "success": False,
                "message": "PLC 연결에 실패했습니다."
            })

        # 6000번 메모리 읽기 (Holding Register)
        result = client.read_holding_registers(address=6000, count=1, unit=1)
        
        if result.isError():
            return JSONResponse({
                "success": False,
                "message": "PLC 데이터 읽기에 실패했습니다."
            })

        # 읽은 데이터
        data_value = result.registers[0]
        
        # 6008번에 읽기 완료 신호 전송 (값 1)
        write_result = client.write_register(address=6008, value=1, unit=1)
        
        if write_result.isError():
            return JSONResponse({
                "success": False,
                "message": "PLC 신호 전송에 실패했습니다."
            })

        return JSONResponse({
            "success": True,
            "message": "PLC 데이터 읽기 완료",
            "data": {
                "address": 6000,
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
        })
    finally:
        # 연결 해제
        disconnect_plc(client)

# ! PLC 상태 확인
async def check_plc_status():
    """PLC 연결 상태 확인"""
    client = None
    try:
        client = connect_plc()
        if client:
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
            })

    except Exception as e:
        print(f"PLC 상태 확인 오류: {e}")
        return JSONResponse({
            "success": False,
            "message": f"PLC 상태 확인 중 오류가 발생했습니다: {str(e)}"
        })
    finally:
        disconnect_plc(client)