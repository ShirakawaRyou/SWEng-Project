"""
简历管理API
""" 
# backend/api/resume.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response
from beanie import PydanticObjectId

from backend.models.user import User
from backend.models.resume import Resume, ResumeCreate, ResumeRead # 确保 ResumeCreate 和 ResumeRead 已定义
from backend.core.security import get_current_active_user
from backend.services.resume_parser import parse_resume_file, generate_pdf_thumbnail
from backend.config import settings # 导入 settings 用于构建 URL
import io # 确保导入了 io
from backend.services.resume_parser import parse_resume_file, generate_pdf_thumbnail, segment_text_into_sections # <--- 导入 segment_text_into_sections



router = APIRouter()

MAX_RESUMES_PER_USER = 5 # 定义最大简历数量常量

@router.post("/upload", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    resume_file: UploadFile = File(..., description="The resume file (PDF or DOCX)"),
    title: Optional[str] = Form(None, description="Optional title for the resume. If not provided, filename will be used."),
    current_user: User = Depends(get_current_active_user)
):
    # ==> 新增：检查用户现有简历数量 <==
    existing_resumes_count = await Resume.find(Resume.user_id == current_user.id).count()
    if existing_resumes_count >= MAX_RESUMES_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 或者 400 Bad Request
            detail=f"Upload limit reached. You can only upload a maximum of {MAX_RESUMES_PER_USER} resumes."
        )
    # ==> 检查结束 <==

    if not resume_file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")

    file_content_bytes = await resume_file.read()
    await resume_file.seek(0)

    try:
        raw_text = await parse_resume_file(resume_file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    # ==> 新增：对原始文本进行区段化解析 <==
    parsed_sections_data: Dict[str, str] = {} # 默认为空字典
    if raw_text and raw_text.strip(): # 仅当有原始文本时才尝试区段化
        try:
            parsed_sections_data = segment_text_into_sections(raw_text)
            # 您可以在这里打印日志，看看区段化的效果
            print(f"[Upload Service] Resume segmented. Found sections: {list(parsed_sections_data.keys())}")
        except Exception as e_segment:
            # 即使区段化失败，我们仍然保存原始文本，不中断上传流程
            print(f"Warning: Error segmenting resume text for {resume_file.filename}: {e_segment}")
            # parsed_sections_data 将保持为空字典

    resume_title = title if title else resume_file.filename
    
    thumbnail_data = None
    thumbnail_media_type = None
    if resume_file.content_type == "application/pdf":
        thumbnail_result = await generate_pdf_thumbnail(file_content_bytes)
        if thumbnail_result:
            thumbnail_data, thumbnail_media_type = thumbnail_result

    resume_doc_data = {
        "title": resume_title,
        "original_file_name": resume_file.filename,
        "user_id": current_user.id,
        "raw_text_content": raw_text,
        "parsed_sections": parsed_sections_data,  # <--- 存储区段化后的内容
        "file_content": file_content_bytes,
        "file_media_type": resume_file.content_type,
        "thumbnail_content": thumbnail_data,
        "thumbnail_media_type": thumbnail_media_type,
    }
    
    new_resume = Resume(**resume_doc_data)
    await new_resume.insert()
    
    resume_id_str = str(new_resume.id)
    file_download_url = f"{settings.API_V1_STR}/resumes/{resume_id_str}/file" if new_resume.file_content else None
    thumbnail_url = f"{settings.API_V1_STR}/resumes/{resume_id_str}/thumbnail" if new_resume.thumbnail_content else None

    resume_data_for_read_model = {
        "id": resume_id_str,
        "user_id": str(new_resume.user_id), # 确保user_id也是字符串
        "title": new_resume.title,
        "original_file_name": new_resume.original_file_name,
        "raw_text_content": new_resume.raw_text_content,
        "parsed_sections": new_resume.parsed_sections,
        "uploaded_at": new_resume.uploaded_at,
        "updated_at": new_resume.updated_at,
        "file_download_url": file_download_url,
        "thumbnail_url": thumbnail_url
    }
    return ResumeRead.model_validate(resume_data_for_read_model)


# ... (list_user_resumes, get_resume, delete_resume 端点) ...
# 您可能也需要在 get_resume 和 list_user_resumes 中进行类似的显式转换
# 例如，在 list_user_resumes 中:
# return [ResumeRead.model_validate({**resume.model_dump(exclude={'id', 'user_id'}), 'id': str(resume.id), 'user_id': str(resume.user_id)}) for resume in resumes]
# 或者更清晰：
# validated_resumes = []
# for resume_doc in resumes:
#     data = resume_doc.model_dump() # 获取所有字段
#     data['id'] = str(resume_doc.id)
#     data['user_id'] = str(resume_doc.user_id)
#     validated_resumes.append(ResumeRead.model_validate(data))
# return validated_resumes


@router.get("/", response_model=List[ResumeRead])
async def list_user_resumes(current_user: User = Depends(get_current_active_user)):
    resumes_from_db = await Resume.find(Resume.user_id == current_user.id).to_list()

    response_resumes = []
    for resume_doc in resumes_from_db:
        resume_id_str = str(resume_doc.id)
        file_download_url = f"{settings.API_V1_STR}/resumes/{resume_id_str}/file" if resume_doc.file_content else None
        thumbnail_url = f"{settings.API_V1_STR}/resumes/{resume_id_str}/thumbnail" if resume_doc.thumbnail_content else None # <--- 构建缩略图URL


        data_for_read = {
            "id": resume_id_str,
            "user_id": str(resume_doc.user_id),
            "title": resume_doc.title,
            "original_file_name": resume_doc.original_file_name,
            "raw_text_content": resume_doc.raw_text_content,
            "parsed_sections": resume_doc.parsed_sections,
            "uploaded_at": resume_doc.uploaded_at,
            "updated_at": resume_doc.updated_at,
            "file_download_url": file_download_url, # 添加下载链接
            "thumbnail_url": thumbnail_url # <--- 添加缩略图 URL

        }
        response_resumes.append(ResumeRead.model_validate(data_for_read))
    return response_resumes


from fastapi.responses import StreamingResponse # 用于返回文件流
import io # 用于将 bytes 转换为类文件对象

# ... (upload_resume, list_user_resumes 等) ...

@router.get("/{resume_id}/file") # 定义在 get_resume (带ID) 之前，或使用不同路径模式避免冲突
async def download_resume_file(
    resume_id: PydanticObjectId,
    current_user: User = Depends(get_current_active_user) # 确保用户已登录
):
    """
    下载指定ID的原始简历文件.
    只有简历所有者才能下载.
    """
    resume = await Resume.get(resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this file.")

    if not resume.file_content or not resume.file_media_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File content not available for this resume.")

    # 使用 StreamingResponse 返回文件内容
    file_like_object = io.BytesIO(resume.file_content) # 将 bytes 转换为类文件对象
    
    # 设置 Content-Disposition header 建议浏览器下载并使用原始文件名
    headers = {
        'Content-Disposition': f'attachment; filename="{resume.original_file_name}"'
    }
    # 如果希望浏览器内联显示（如PDF），可以使用 'inline' 而不是 'attachment'
    # headers = {
    #     'Content-Disposition': f'inline; filename="{resume.original_file_name}"'
    # }
    
    return StreamingResponse(file_like_object, media_type=resume.file_media_type, headers=headers)

# 确保这个新的端点注册在 GET /{resume_id} 之前，如果路径可能冲突的话。
# 或者，更清晰的路径是像这样 GET /resumes/{resume_id}/download
# 我上面的 upload_resume 返回的链接是 /file，所以这里也用 /file

@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(
    resume_id: PydanticObjectId,
    current_user: User = Depends(get_current_active_user)
):
    resume_doc = await Resume.get(resume_id)
    if not resume_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    if resume_doc.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this resume.")

    resume_id_str = str(resume_doc.id)
    file_download_url = f"{settings.API_V1_STR}/resumes/{resume_id_str}/file" if resume_doc.file_content else None
    thumbnail_url = f"{settings.API_V1_STR}/resumes/{resume_id_str}/thumbnail" if resume_doc.thumbnail_content else None # <--- 构建缩略图URL
    
    data_for_read = {
        "id": resume_id_str,
        "user_id": str(resume_doc.user_id),
        "title": resume_doc.title,
        "original_file_name": resume_doc.original_file_name,
        "raw_text_content": resume_doc.raw_text_content,
        "parsed_sections": resume_doc.parsed_sections,
        "uploaded_at": resume_doc.uploaded_at,
        "updated_at": resume_doc.updated_at,
        "file_download_url": file_download_url, # 添加下载链接
        "thumbnail_url": thumbnail_url # <--- 添加缩略图 URL
    }
    return ResumeRead.model_validate(data_for_read)




@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: PydanticObjectId,
    current_user: User = Depends(get_current_active_user)
):
    """
    删除指定ID的简历.
    只有简历所有者才能删除.
    成功删除后返回 204 No Content.
    """
    resume = await Resume.get(resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    if resume.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this resume.")

    await resume.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT) # 返回一个没有内容的204响应


@router.get("/{resume_id}/thumbnail")
async def get_resume_thumbnail(
    resume_id: PydanticObjectId,
    # current_user: User = Depends(get_current_active_user) # 可选：如果缩略图也需要认证
):
    """
    获取指定ID简历的缩略图.
    这里我们暂时不加用户认证，因为缩略图URL可能是公开的。
    如果需要保护，取消 current_user 的注释并添加用户ID校验。
    """
    resume = await Resume.get(resume_id)
    if not resume or not resume.thumbnail_content or not resume.thumbnail_media_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found for this resume.")

    # (可选) 用户权限校验，如果缩略图需要保护
    # if resume.user_id != current_user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this thumbnail.")

    return StreamingResponse(io.BytesIO(resume.thumbnail_content), media_type=resume.thumbnail_media_type)