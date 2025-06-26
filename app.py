from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)