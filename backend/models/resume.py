"""
简历模型
""" 
# backend/models/resume.py
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from beanie import Document, Indexed, PydanticObjectId # PydanticObjectId 用于外键链接
from pydantic import BaseModel, Field, HttpUrl
# from .user import User # 如果使用 Beanie Link 类型，可以导入User

class ResumeBase(BaseModel):
    """Pydantic模型：简历基础信息"""
    title: str
    original_file_name: Optional[str] = None

class ResumeCreate(ResumeBase):
    """Pydantic模型：创建简历时使用"""
    pass # 继承自ResumeBase，暂时没有额外字段

class ResumeCreatePayload(BaseModel):
    title: Optional[str] = None


class ResumeUpdate(BaseModel):
    """Pydantic模型：更新简历时使用 (可选字段)"""
    title: Optional[str] = None
    original_file_name: Optional[str] = None
    raw_text_content: Optional[str] = None
    parsed_sections: Optional[Dict[str, Any]] = None # 解析后的结构化内容，可以是灵活的字典

class ResumeRead(BaseModel): # 用于API响应的模型
    id: str  # <--- API 响应为字符串ID
    user_id: str # <--- API 响应为字符串用户ID
    title: str
    original_file_name: Optional[str] = None
    raw_text_content: Optional[str] = None
    parsed_sections: Optional[Dict[str, Any]] = None
    uploaded_at: datetime
    updated_at: datetime
    file_download_url: Optional[str] = None # <--- 修改：从 HttpUrl 改为 str
    thumbnail_url: Optional[str] = None    # <--- 新增：缩略图 URL

    class Config:
        from_attributes = True # 即使我们手动转换，保留它通常无害
        arbitrary_types_allowed = True

class ResumeInDBBase(ResumeBase):
    """Pydantic模型：数据库中存储的简历基础信息"""
    id: str
    user_id: PydanticObjectId # 在数据库中存储为 ObjectId
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    raw_text_content: Optional[str] = None
    parsed_sections: Optional[Dict[str, Any]] = None # 例如: {"experience": [...], "education": [...], "skills": []}

    class Config:
        orm_mode = True # Pydantic V1
        # from_attributes = True # Pydantic V2

class Resume(Document):
    title: str
    user_id: Indexed(PydanticObjectId) # type: ignore
    original_file_name: Optional[str] = None
    raw_text_content: Optional[str] = None
    parsed_sections: Optional[Dict[str, Any]] = None

    # 新增字段用于存储原始文件
    file_content: Optional[bytes] = None # 存储文件原始内容
    file_media_type: Optional[str] = None # 存储文件的媒体类型 (e.g., "application/pdf")

    # 新增字段用于存储缩略图
    thumbnail_content: Optional[bytes] = None      # <--- 新增：缩略图二进制内容
    thumbnail_media_type: Optional[str] = None   # <--- 新增：缩略图媒体类型 (e.g., "image/png")

    
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "resumes"