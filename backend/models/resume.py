"""
简历模型
""" 
# backend/models/resume.py
from datetime import datetime
from typing import Optional, Dict, Any

from beanie import Document, Indexed, PydanticObjectId # PydanticObjectId 用于外键链接
from pydantic import BaseModel, Field
# from .user import User # 如果使用 Beanie Link 类型，可以导入User

class ResumeBase(BaseModel):
    """Pydantic模型：简历基础信息"""
    title: str
    original_file_name: Optional[str] = None

class ResumeCreate(ResumeBase):
    """Pydantic模型：创建简历时使用"""
    pass # 继承自ResumeBase，暂时没有额外字段

class ResumeUpdate(BaseModel):
    """Pydantic模型：更新简历时使用 (可选字段)"""
    title: Optional[str] = None
    original_file_name: Optional[str] = None
    raw_text_content: Optional[str] = None
    parsed_sections: Optional[Dict[str, Any]] = None # 解析后的结构化内容，可以是灵活的字典

class ResumeRead(ResumeBase):
    """Pydantic模型：从API读取简历数据时使用，包含ID和其他元数据"""
    id: str # Beanie 会将 MongoDB 的 _id (ObjectId) 转为 str
    user_id: str # 存储用户ID的字符串形式
    uploaded_at: datetime
    updated_at: datetime
    raw_text_content: Optional[str] = None
    parsed_sections: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True # Pydantic V1
        # from_attributes = True # Pydantic V2

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

class Resume(Document, ResumeInDBBase): # Beanie Document 模型
    """Beanie MongoDB Document 模型：简历"""
    # title, original_file_name, user_id, uploaded_at, updated_at, raw_text_content, parsed_sections 继承
    # id (ObjectId) 会由 Beanie 自动处理

    # 为 user_id 创建索引，以便快速查询某个用户的所有简历
    user_id: Indexed(PydanticObjectId) # type: ignore

    class Settings:
        name = "resumes" # MongoDB collection的名称