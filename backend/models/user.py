# backend/models/user.py
from datetime import datetime
from typing import Optional

from beanie import Document, Indexed, PydanticObjectId # <--- 确保 PydanticObjectId 已导入
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserRead(UserBase): # 用于API响应的模型
    id: PydanticObjectId # <--- 修改这里：从 str 改为 PydanticObjectId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True # 明确允许任意类型，有助于处理像 PydanticObjectId 这样的自定义类型

# Beanie Document 模型 (数据库模型) - 保持不变
class User(Document):
    email: Indexed(EmailStr, unique=True) # type: ignore
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"