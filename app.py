from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File
import uvicorn
from contextlib import asynccontextmanager

from user_service import login_user, logout_user, create_user, change_password, reset_password, get_all_users, get_user, update_user
from access_service import get_access, get_all_pages, update_access
from audit_service import create_comment, get_audit_trail, export_audit_trail
from plc_service import read_plc_data, check_plc_status
from backup_service import create_backup, restore_backup
from history_service import (
    get_equipment_history, export_equipment_history,
    get_alarm_history, export_alarm_history,
    get_report_history, export_report_history,
    get_login_history, export_login_history,
    get_user_history, export_user_history,
    get_data_history, export_data_history
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print("애플리케이션 시작 - 초기 백업 생성 중...")
        backup_response = await create_backup(None, is_manual=False)
        print("초기 백업 생성 완료")
    except Exception as e:
        print(f"초기 백업 생성 실패: {e}")
    
    yield

app = FastAPI(
    title="보틀포장 1호기 데이터 & 권한 관리 S/W API",
    lifespan=lifespan
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root_page():
    return FileResponse('static/html/login.html')

@app.get("/login")
async def login_page():
    return FileResponse('static/html/login.html')

@app.get("/landing")
async def login_page():
    return FileResponse('static/html/landing.html')

@app.post("/api/login")
async def login_api(request: Request):
    return await login_user(request)

@app.post("/api/logout")
async def logout_api(request: Request):
    return await logout_user(request)

@app.get("/api/users")
async def get_all_users_api():
    return await get_all_users()

@app.get("/api/users/{user_id}")
async def get_user_api(user_id: str):
    return await get_user(user_id)

@app.put("/api/users/{user_id}")
async def update_user_api(user_id: str, request: Request):
    return await update_user(user_id, request)

@app.post("/api/users")
async def create_user_api(request: Request):
    return await create_user(request)

@app.put("/api/password/change")
async def change_password_api(request: Request):
    return await change_password(request)

@app.put("/api/password/reset")
async def reset_user_password_api(request: Request):
    return await reset_password(request)

@app.get("/api/pages")
async def get_all_pages_api():
    return await get_all_pages()

@app.get("/api/access/{role_id}")
async def get_access_api(role_id: str):
    return await get_access(role_id)

@app.put("/api/access")
async def update_access_api(request: Request):
    return await update_access(request)

@app.post("/api/comments")
async def create_comment_api(request: Request):
    return await create_comment(request)

@app.get("/api/plc/read")
async def read_plc_data_api():
    return await read_plc_data()

@app.get("/api/plc/status")
async def check_plc_status_api():
    return await check_plc_status()

@app.post("/api/backup/create")
async def create_backup_api(request: Request):
    return await create_backup(request, is_manual=True)

@app.post("/api/backup/restore")
async def restore_backup_api(request: Request, backup_file: UploadFile = File(...)):
    return await restore_backup(request, backup_file)

@app.get("/api/equipment-history")
async def get_equipment_history_api(request: Request):
    return await get_equipment_history(request)

@app.get("/api/equipment-history/export")
async def export_equipment_history_api(request: Request):
    return await export_equipment_history(request)

@app.get("/api/alarm-history")
async def get_alarm_history_api(request: Request):
    return await get_alarm_history(request)

@app.get("/api/alarm-history/export")
async def export_alarm_history_api(request: Request):
    return await export_alarm_history(request)

@app.get("/api/report-history")
async def get_report_history_api(request: Request):
    return await get_report_history(request)

@app.get("/api/report-history/export")
async def export_report_history_api(request: Request):
    return await export_report_history(request)

@app.get("/api/login-history")
async def get_login_history_api(request: Request):
    return await get_login_history(request)

@app.get("/api/login-history/export")
async def export_login_history_api(request: Request):
    return await export_login_history(request)

@app.get("/api/user-history")
async def get_user_history_api(request: Request):
    return await get_user_history(request)

@app.get("/api/user-history/export")
async def export_user_history_api(request: Request):
    return await export_user_history(request)

@app.get("/api/data-history")
async def get_data_history_api(request: Request):
    return await get_data_history(request)

@app.get("/api/data-history/export")
async def export_data_history_api(request: Request):
    return await export_data_history(request)

@app.get("/api/audit-trail")
async def get_audit_trail_api(request: Request):
    return await get_audit_trail(request)

@app.get("/api/audit-trail/export")
async def export_audit_trail_api(request: Request):
    return await export_audit_trail(request)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)