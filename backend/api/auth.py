"""
认证相关API
""" 
# backend/api/auth.py
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm # 用于登录表单
from beanie.exceptions import RevisionIdWasChanged # 用于处理可能的并发写入
from pydantic import BaseModel
from pydantic import EmailStr # 确保 EmailStr 已导入

from backend.models.user import User, UserCreate, UserRead # User是Beanie模型, UserCreate/Read是Pydantic模型
from backend.core.security import get_password_hash, verify_password, create_access_token, get_current_active_user
from backend.config import settings

router = APIRouter()

class Token(BaseModel): # Pydantic模型，用于定义登录成功返回的token结构
    access_token: str
    token_type: str

class UserReactivationRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate):
    """
    用户注册.
    - **email**: 用户的邮箱地址 (将作为登录用户名).
    - **password**: 用户密码.
    - **full_name**: (可选) 用户全名.
    """
    existing_user = await User.find_one(User.email == user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )
    
    hashed_password = get_password_hash(user_in.password)
    
    new_user_data = user_in.model_dump(exclude={"password"}) # Pydantic V2
    # new_user_data = user_in.dict(exclude={"password"}) # Pydantic V1
    
    user_doc = User(**new_user_data, hashed_password=hashed_password)
    
    try:
        await user_doc.insert()
    except RevisionIdWasChanged: # 处理 Beanie 并发插入的罕见情况
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create user due to a conflict. Please try again.",
        )

    # 为了匹配 UserRead 模型，我们需要确保返回的 user_doc 有 id (Beanie会自动添加_id)
    # Beanie的 find_one/get 返回的文档实例可以直接用于 Pydantic 模型（如果字段匹配且orm_mode/from_attributes=True）
    # 这里我们直接使用插入后的 user_doc。 UserRead 的 orm_mode 会处理 id 的转换。
    # 或者更安全地，再次查询一次以确保所有默认值和转换都已应用，但通常 insert() 后的实例即可
    return UserRead.model_validate(user_doc) # Pydantic V2
    # return UserRead.from_orm(user_doc) # Pydantic V1


@router.post("/login/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录获取访问令牌.
    需要以表单形式提交 `username` (即邮箱) 和 `password`.
    """
    user = await User.find_one(User.email == form_data.username) # form_data.username 对应登录时的邮箱
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires # user.id 是 PydanticObjectId，转为str
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    获取当前已登录用户信息.
    需要有效的 JWT Bearer Token 在 Authorization header 中.
    """
    # current_user 是 Beanie User Document 实例
    # UserRead.from_orm (Pydantic V1) 或 UserRead.model_validate (Pydantic V2)
    # 可以将 Beanie 文档实例转换为 Pydantic 模型实例
    return UserRead.model_validate(current_user) # Pydantic V2
    # return UserRead.from_orm(current_user) # Pydantic V1


@router.post("/users/me/deactivate", response_model=UserRead, status_code=status.HTTP_200_OK)
async def deactivate_current_user(current_user: User = Depends(get_current_active_user)):
    """
    停用当前已登录用户的账户 (软删除).
    用户将被标记为 is_active = False.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already inactive."
        )

    current_user.is_active = False
    current_user.updated_at = datetime.now(timezone.utc) # 手动更新 updated_at
    
    try:
        await current_user.save() # 保存更改到数据库
    except RevisionIdWasChanged:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not deactivate account due to a conflict. Please try again.",
        )
    
    # 返回更新后的用户信息 (现在 is_active 会是 false)
    return UserRead.model_validate(current_user)


# 如果您确实需要硬删除功能 (永久删除用户及其数据 - 请谨慎使用)
# 可以考虑添加一个不同的端点，例如 DELETE /users/me
@router.delete("/users/me/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_permanently(current_user: User = Depends(get_current_active_user)):
    """
    永久删除当前已登录用户的账户及其关联数据 (硬删除).
    警告：此操作不可逆！
    您还需要在这里处理与该用户关联的其他数据，例如删除他们的简历等。
    """
    user_id_to_delete = current_user.id
    await current_user.delete() # Beanie 的 delete 方法

    # 此处添加删除用户关联数据（如简历）的逻辑
    # from backend.models.resume import Resume
    # await Resume.find(Resume.user_id == user_id_to_delete).delete()

    # 对于 DELETE 操作，通常返回 204 No Content，不需要响应体
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.post("/reactivate", response_model=Token) # 成功激活后返回新的token
async def reactivate_user_account(reactivation_data: UserReactivationRequest):
    """
    重新激活一个之前被停用的用户账户.
    需要提供用户的邮箱和密码.
    成功后会返回一个新的访问令牌 (access token).
    """
    user = await User.find_one(User.email == reactivation_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # 或 400 Bad Request，避免泄露用户是否存在
            detail="User with this email not found or incorrect password.", # 通用错误信息
        )

    if not verify_password(reactivation_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # 使用 400 而不是 401，因为这不是标准的 token 认证失败
            detail="User with this email not found or incorrect password.", # 通用错误信息
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already active.",
        )

    # 激活用户
    user.is_active = True
    user.updated_at = datetime.now(timezone.utc) # 手动更新 updated_at

    try:
        await user.save()
    except RevisionIdWasChanged:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not reactivate account due to a conflict. Please try again.",
        )

    # 重新激活成功，生成新的访问令牌让用户直接登录
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
