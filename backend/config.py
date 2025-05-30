# backend/config.py
import os
from datetime import timedelta # 确保导入 timedelta
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# --- .env 文件加载逻辑 ---
# 确定 backend 目录的绝对路径
# __file__ 是当前文件 (config.py) 的路径
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# .env 文件在 backend 目录中的路径
backend_env_path = os.path.join(BACKEND_DIR, ".env")

# .env 文件在项目根目录 (backend 目录的上一级) 中的路径
project_root_env_path = os.path.join(os.path.dirname(BACKEND_DIR), ".env")

# 优先加载 backend 目录下的 .env 文件
if os.path.exists(backend_env_path):
    load_dotenv(dotenv_path=backend_env_path)
    print(f"Loaded .env configuration from: {backend_env_path}")
elif os.path.exists(project_root_env_path):
    load_dotenv(dotenv_path=project_root_env_path)
    print(f"Loaded .env configuration from: {project_root_env_path}")
else:
    print(
        f"Warning: .env file not found at {backend_env_path} or {project_root_env_path}. "
        "Application will rely on environment variables or default Pydantic settings."
    )
# --- 结束 .env 文件加载逻辑 ---


class Settings(BaseSettings):
    PROJECT_NAME: str = "ResumeAlign"
    API_V1_STR: str = "/api/v1"

    # MongoDB Settings - 这些将从 .env 文件加载
    MONGO_CONNECTION_STRING: str
    MONGO_DATABASE_NAME: str # 之前这里可能有默认值，现在我们让它从.env加载

    # JWT Token settings
    JWT_SECRET_KEY: str # 将从 .env 文件加载
    JWT_ALGORITHM: str = "HS256" # 可以保留默认值，除非 .env 中有定义
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 可以保留默认值，除非 .env 中有定义

    # Gemini API Key
    GEMINI_API_KEY: str # <--- 新增


    # Pydantic V2 使用 model_config 来配置 .env 文件加载等行为，
    # 但我们在这里使用了 python-dotenv 的显式 load_dotenv()，
    # BaseSettings 仍会自动查找匹配的环境变量（包括由 load_dotenv 加载的）。
    class Config:
        case_sensitive = True # 环境变量名称是否区分大小写

# 创建配置实例
settings = Settings()

# (可选) 启动时打印一些配置项以供调试 (生产环境中应移除或控制日志级别)
print(f"--- ResumeAlign Configuration Loaded ---")
print(f"Project Name: {settings.PROJECT_NAME}")
print(f"MongoDB Database: {settings.MONGO_DATABASE_NAME}")
print(f"JWT Algorithm: {settings.JWT_ALGORITHM}")
print(f"Access Token Expire Minutes: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
print(f"Mongo Connection String Loaded: {'Yes' if settings.MONGO_CONNECTION_STRING else 'No'}")
print(f"JWT Secret Key Loaded: {'Yes' if settings.JWT_SECRET_KEY else 'No'}")
print(f"------------------------------------")