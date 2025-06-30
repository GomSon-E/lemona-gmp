from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from user_service import login_user, create_user, change_password
from access_service import get_access, get_all_pages, update_access

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

@app.post("/api/users")
async def create_user_api(request: Request):
    return await create_user(request)

@app.put("/api/users/password")
async def change_password_api(request: Request):
    return await change_password(request)

@app.get("/api/pages")
async def get_all_pages_api():
    return await get_all_pages()

@app.get("/api/access/{role_id}")
async def get_access_api(role_id: str):
    return await get_access(role_id)

@app.put("/api/access")
async def update_access_api(request: Request):
    return await update_access(request)
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)