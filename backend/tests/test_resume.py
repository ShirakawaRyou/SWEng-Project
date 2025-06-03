"""
简历相关测试
""" 
# tests/api/test_resume.py
import pytest
from httpx import AsyncClient
from fastapi import status
import io

from backend.config import settings
from backend.models.resume import Resume # Beanie Resume model

pytestmark = pytest.mark.asyncio

# 您需要一个已登录的用户fixture (来自 conftest.py 或在这里重新获取)
# test_user fixture 已经提供了 token

async def test_upload_pdf_resume(async_client: AsyncClient, test_user: dict):
    """测试上传PDF简历"""
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    
    # 模拟文件上传
    # 创建一个简单的PDF文件内容 (实际测试中您可能需要一个真实的测试PDF文件)
    # 或者 mock掉 parse_resume_file 和 generate_pdf_thumbnail 服务
    fake_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n..." # 简化
    files = {'resume_file': ('test.pdf', io.BytesIO(fake_pdf_content), 'application/pdf')}
    data = {'title': 'My Test PDF Resume'}

    response = await async_client.post(
        f"{settings.API_V1_STR}/resumes/upload",
        headers=headers,
        data=data, # Form data
        files=files  # File data
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    resume_data = response.json()
    assert resume_data["title"] == "My Test PDF Resume" # 或 test.pdf 如果title为空
    assert resume_data["original_file_name"] == "test.pdf"
    assert "id" in resume_data
    assert "raw_text_content" in resume_data

    # 验证数据库
    db_resume = await Resume.get(resume_data["id"])
    assert db_resume is not None
    assert db_resume.title == data["title"]


async def test_list_user_resumes(async_client: AsyncClient, test_user: dict):
    """测试获取用户简历列表"""
    # 先确保上传一份简历 (可以调用上面的 test_upload_pdf_resume, 或者在fixture中准备)
    # 为了独立性，我们可以在这里再上传一份
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    files = {'resume_file': ('list_test.pdf', io.BytesIO(b"dummy pdf content"), 'application/pdf')}
    data = {'title': 'List Test Resume'}
    
    await async_client.post(
        f"{settings.API_V1_STR}/resumes/upload", 
        headers=headers, 
        files=files,
        data=data
    )

    response = await async_client.get(f"{settings.API_V1_STR}/resumes/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    resumes_list = response.json()
    assert isinstance(resumes_list, list)
    assert len(resumes_list) > 0 # 假设之前至少上传了一个

# ... 更多简历相关的测试：获取单个、删除、数量限制等 ...