# backend/app.py
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from backend.config import settings
from backend.utils.db import connect_to_mongo, close_mongo_connection, initialize_database, get_database
from backend.api import auth as auth_router # <--- 导入认证路由

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

# 根路由
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}

@app.get("/ping-db", tags=["Database"])
async def ping_database():
    try:
        db = get_database() # get_database() 应该在 utils/db.py 中定义
        await db.command('ping')
        return {"status": "success", "message": "MongoDB connection is healthy.", "db_name": db.name}
    except Exception as e:
        print(f"Database ping error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# 注册认证路由
app.include_router(auth_router.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)