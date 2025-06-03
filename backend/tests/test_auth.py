"""
认证相关测试
""" 
import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, AsyncMock, MagicMock
from bson import ObjectId
import json

from backend.app import app
from backend.config import settings # 用于构建URL
from backend.models.user import User # Beanie User model for DB checks
from backend.api.auth import register_user, login_for_access_token, read_users_me, deactivate_current_user, reactivate_user_account

# 标记所有这个文件中的测试为异步 (pytest-asyncio)
pytestmark = pytest.mark.asyncio

# 创建一个模拟的register_user函数
async def mock_register_user_success(user_in):
    # 模拟成功注册
    mock_user = AsyncMock(spec=User)
    mock_user.id = str(ObjectId())
    mock_user.email = user_in.email
    mock_user.full_name = user_in.full_name
    mock_user.is_active = True
    mock_user.created_at = "2023-01-01T00:00:00"
    mock_user.updated_at = "2023-01-01T00:00:00"
    
    return mock_user

# 创建一个模拟的login_for_access_token函数
async def mock_login_success(form_data):
    # 模拟成功登录
    return {"access_token": "mock_token", "token_type": "bearer"}

# 创建一个模拟的login_for_access_token函数处理密码错误的情况
async def mock_login_failure(form_data):
    # 模拟密码错误
    from fastapi import HTTPException
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def test_register_new_user(async_client: AsyncClient):
    """测试成功注册一个新用户"""
    # 使用依赖项覆盖
    app.dependency_overrides = {
        register_user: mock_register_user_success
    }
    
    try:
        user_data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        response = await async_client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        created_user = response.json()
        assert created_user["email"] == user_data["email"]
        assert created_user["full_name"] == user_data["full_name"]
        assert "id" in created_user
        assert "hashed_password" not in created_user # 确保密码哈希不被返回
    finally:
        # 清理依赖项覆盖
        app.dependency_overrides = {}

async def test_register_duplicate_user(async_client: AsyncClient, test_user: dict):
    """测试注册已存在的用户邮箱"""
    # 定义模拟函数
    async def mock_register_duplicate_user(user_in):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )
    
    # 使用依赖项覆盖
    app.dependency_overrides = {
        register_user: mock_register_duplicate_user
    }
    
    try:
        user_data = { # 使用 test_user fixture 创建的用户的邮箱
            "email": test_user["user"]["email"],
            "password": "anotherpassword",
            "full_name": "Duplicate User"
        }
        response = await async_client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "User with this email already exists" in response.json()["detail"]
    finally:
        # 清理依赖项覆盖
        app.dependency_overrides = {}

async def test_login_for_access_token(async_client: AsyncClient, test_user: dict):
    """测试成功登录并获取token"""
    # 使用依赖项覆盖
    app.dependency_overrides = {
        login_for_access_token: mock_login_success
    }
    
    try:
        login_data = {
            "username": test_user["user"]["email"], # email作为username
            "password": test_user["raw_password"]   # 使用原始密码
        }
        response = await async_client.post(f"{settings.API_V1_STR}/auth/login/token", data=login_data)
        assert response.status_code == status.HTTP_200_OK
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
    finally:
        # 清理依赖项覆盖
        app.dependency_overrides = {}

async def test_login_incorrect_password(async_client: AsyncClient, test_user: dict):
    """测试密码错误时登录失败"""
    # 使用依赖项覆盖
    app.dependency_overrides = {
        login_for_access_token: mock_login_failure
    }
    
    try:
        login_data = {
            "username": test_user["user"]["email"],
            "password": "wrongpassword"
        }
        response = await async_client.post(f"{settings.API_V1_STR}/auth/login/token", data=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED # 或您在API中定义的400
        assert "Incorrect email or password" in response.json()["detail"]
    finally:
        # 清理依赖项覆盖
        app.dependency_overrides = {}

async def test_read_users_me(async_client: AsyncClient, test_user: dict):
    """测试获取当前用户信息"""
    # 定义模拟函数
    async def mock_read_users_me(current_user = None):
        # 模拟用户信息
        return {
            "id": test_user["user"]["id"],
            "email": test_user["user"]["email"],
            "full_name": test_user["user"]["full_name"],
            "is_active": True,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
    
    # 使用依赖项覆盖
    app.dependency_overrides = {
        read_users_me: mock_read_users_me
    }
    
    try:
        response = await async_client.get(f"{settings.API_V1_STR}/auth/users/me")
        assert response.status_code == status.HTTP_200_OK
        user_me = response.json()
        assert user_me["email"] == test_user["user"]["email"]
        assert user_me["id"] == test_user["user"]["id"]
    finally:
        # 清理依赖项覆盖
        app.dependency_overrides = {}

async def test_read_users_me_no_token(async_client: AsyncClient):
    """测试无token时获取用户信息失败"""
    response = await async_client.get(f"{settings.API_V1_STR}/auth/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED # FastAPI的OAuth2PasswordBearer(auto_error=True)会处理

# --- 您可以继续添加测试用例 ---
# 例如：测试停用账户、重新激活账户等
# async def test_deactivate_user(async_client: AsyncClient, test_user: dict): ...
# async def test_reactivate_user(async_client: AsyncClient, test_user_registered_and_deactivated: dict): ...