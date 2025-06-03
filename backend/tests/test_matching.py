"""
匹配相关测试
""" 
# tests/api/test_matching.py
import pytest
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, AsyncMock, MagicMock # 使用 AsyncMock 来 mock 异步函数
from bson import ObjectId

from backend.app import app
from backend.config import settings
from backend.models.user import User
from backend.models.resume import Resume
from backend.models.processed_jd import ProcessedJD
from backend.core.security import get_current_active_user

pytestmark = pytest.mark.asyncio

@pytest.mark.parametrize("mock_db", [True])  # 使用参数化标记表示这是一个需要 mock 数据库的测试
async def test_get_suggestions(mock_db, async_client: AsyncClient):
    """测试获取建议，并mock全部数据库和API操作"""
    # 创建模拟的用户和简历数据
    mock_user_id = str(ObjectId())  # 生成有效的MongoDB ObjectId
    mock_user = AsyncMock(spec=User)
    mock_user.id = mock_user_id
    
    mock_resume_id = str(ObjectId())  # 生成有效的MongoDB ObjectId
    mock_resume = AsyncMock(spec=Resume)
    mock_resume.id = mock_resume_id
    mock_resume.user_id = mock_user_id
    mock_resume.raw_text_content = "Mock resume content"
    
    # 通过修改依赖项直接在FastAPI应用中进行测试时的依赖项替换
    app.dependency_overrides = {
        get_current_active_user: lambda: mock_user
    }
    
    # Mock Resume.get 调用
    with patch("backend.models.resume.Resume.get", return_value=mock_resume):
        # Mock Gemini API 调用
        with patch("backend.api.matching.generate_suggestions_from_gemini", 
                   return_value="This is a mocked suggestion."):
            # 创建有效的文本以满足最小长度要求
            jd_text = """Software engineer needed with Python and FastAPI skills. Must have 3+ years experience
            in web development and be familiar with cloud services. Experience with MongoDB and
            React is a plus. The candidate should be able to work in a team environment and have 
            excellent communication skills."""
            
            resume_text = """
            Experienced software developer with 2 years of Python development experience.
            Familiar with FastAPI, Django and Flask frameworks.
            Worked on several web applications using modern frontend technologies.
            """
            
            request_data = {
                "resume_id": mock_resume_id,
                "jd_text": jd_text,
                "resume_text_to_analyze": resume_text
            }
            
            # 不需要认证头，因为我们已经覆盖了依赖项
            response = await async_client.post(
                f"{settings.API_V1_STR}/matching/suggestions", 
                json=request_data
            )
            
            # 打印响应内容以便调试
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            # 检查响应
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["suggestions"] == "This is a mocked suggestion."
            assert "prompt_used" in data
    
    # 清理依赖项覆盖
    app.dependency_overrides = {}