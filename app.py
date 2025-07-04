from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from user_service import login_user, logout_user, create_user, change_password, reset_password, get_all_users, get_user, update_user
from access_service import get_access, get_all_pages, update_access
from audit_service import create_comment

app = FastAPI(title="얼굴 특징 벡터 추출 및 비교 API")
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

@app.put("/api/users/password")
async def change_password_api(request: Request):
    return await change_password(request)

@app.put("/api/users/password/reset")
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)