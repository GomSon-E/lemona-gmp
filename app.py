from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from user_service import login_user, get_access, create_user, change_password

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

@app.get("/api/access/{role_id}")
async def get_access_api(role_id: str):
    return await get_access(role_id)
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)