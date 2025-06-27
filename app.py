from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import hashlib
from datetime import datetime

import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

from user_service import create_user

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

@app.post("/api/users")
async def create_user_api(request: Request):
    return await create_user(request)
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)