# backend/app.py
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from backend.config import settings
from backend.utils.db import connect_to_mongo, close_mongo_connection, initialize_database, get_database # 确保 get_database 导入
from backend.api import auth as auth_router
from backend.api import resume as resume_router
from backend.api import matching as matching_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await initialize_database()
    yield
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# 根路由和 ping-db 路由 (保持不变)
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}

@app.get("/ping-db", tags=["Database"])
async def ping_database():
    try:
        db = get_database()
        await db.command('ping')
        return {"status": "success", "message": "MongoDB connection is healthy.", "db_name": db.name}
    except Exception as e:
        print(f"Database ping error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# 注册认证路由
app.include_router(auth_router.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
# 注册简历路由
app.include_router(resume_router.router, prefix=f"{settings.API_V1_STR}/resumes", tags=["Resumes"]) 

app.include_router(matching_router.router, prefix=f"{settings.API_V1_STR}/matching", tags=["Matching Analysis"]) # <--- 添加这行




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)