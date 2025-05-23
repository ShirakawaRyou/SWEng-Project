# backend/api/matching.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from beanie import PydanticObjectId

from backend.models.user import User
from backend.models.resume import Resume, ResumeRead # ResumeRead 用于返回简历基本信息
from backend.core.security import get_current_active_user
from backend.services.keyword_extractor import extract_keywords_from_jd
from backend.services.matching_service import calculate_match_score
from backend.services.gemini_service import generate_suggestions_from_gemini # 导入 Gemini 服务


router = APIRouter()

class JDInput(BaseModel):
    jd_text: str = Field(..., min_length=50, description="The full text of the Job Description.")

class MatchRequest(BaseModel):
    jd_text: str = Field(..., min_length=50, description="The full text of the Job Description.")
    resume_ids: List[PydanticObjectId] = Field(..., description="A list of resume IDs to match against the JD.")

class ResumeMatchResult(BaseModel):
    resume_id: str # PydanticObjectId 会被 FastAPI 序列化为 str
    resume_title: str
    original_file_name: Optional[str] = None
    match_score: float
    # 可以在这里添加更多从 ResumeRead 获取的字段

class MatchResponse(BaseModel):
    job_description_keywords: List[str]
    match_results: List[ResumeMatchResult]

class SuggestionRequest(BaseModel):
    resume_id: PydanticObjectId = Field(..., description="The ID of the resume to get suggestions for.")
    job_description_text: str = Field(..., min_length=50, description="The full text of the Job Description.")
    # 用户可以提供简历中特定的文本片段进行分析，否则使用整个简历的原始文本
    resume_text_to_analyze: Optional[str] = Field(None, min_length=20, description="Specific section or text from the resume to focus on for improvement. If null, the whole resume's raw text is used.")
    target_keywords: Optional[List[str]] = Field(None, description="Specific keywords to focus on for improvement.")
    # custom_prompt_template: Optional[str] = None # 高级功能：允许用户提供自定义提示模板 (暂时移除以简化)

class SuggestionResponse(BaseModel):
    resume_id: str
    suggestions: str # Gemini 返回的文本建议
    prompt_used: str # 将实际发送给 Gemini 的 prompt 返回，方便调试



@router.post("/extract-jd-keywords", response_model=List[str])
async def api_extract_jd_keywords(jd_input: JDInput):
    """
    接收职位描述文本并提取关键词.
    """
    if not jd_input.jd_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description text cannot be empty.")
    
    keywords = extract_keywords_from_jd(jd_input.jd_text)
    return keywords


@router.post("/match-resumes", response_model=MatchResponse)
async def api_match_resumes_with_jd(
    request_data: MatchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    接收职位描述和简历ID列表，计算匹配度.
    用户必须已登录.
    """
    if not request_data.jd_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description text cannot be empty.")
    if not request_data.resume_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume IDs list cannot be empty.")

    # 1. 提取JD关键词
    jd_keywords = extract_keywords_from_jd(request_data.jd_text)
    if not jd_keywords: # 如果JD没有提取出任何关键词
        # 返回空的关键词列表和空的匹配结果，或者一个特定的提示
        return MatchResponse(job_description_keywords=[], match_results=[])


    match_results: List[ResumeMatchResult] = []

    for resume_id in request_data.resume_ids:
        resume_doc = await Resume.get(resume_id)
        if not resume_doc:
            # 如果某个简历ID无效，可以选择跳过，或抛出错误，或在结果中标记
            # 这里我们选择跳过，并在结果中不包含它
            # 也可以收集错误信息：
            # match_results.append(ResumeMatchResult(resume_id=str(resume_id), resume_title="Not Found", match_score=-1.0))
            print(f"Warning: Resume with ID {resume_id} not found.")
            continue 
        
        if resume_doc.user_id != current_user.id:
            # 如果简历不属于当前用户，也跳过
            print(f"Warning: Resume {resume_id} does not belong to user {current_user.id}.")
            continue

        if not resume_doc.raw_text_content:
            # 如果简历没有解析后的文本内容，无法匹配
            match_results.append(ResumeMatchResult(
                resume_id=str(resume_doc.id),
                resume_title=resume_doc.title,
                original_file_name=resume_doc.original_file_name,
                match_score=0.0 # 或者一个特殊值表示无法计算
            ))
            print(f"Warning: Resume {resume_id} has no raw text content for matching.")
            continue

        # 2. 计算匹配度
        score = calculate_match_score(resume_doc.raw_text_content, jd_keywords)
        
        match_results.append(ResumeMatchResult(
            resume_id=str(resume_doc.id),
            resume_title=resume_doc.title,
            original_file_name=resume_doc.original_file_name,
            match_score=score
        ))
        
    return MatchResponse(job_description_keywords=jd_keywords, match_results=match_results)

# backend/api/matching.py
# ... (router 和之前的端点) ...

@router.post("/suggestions", response_model=SuggestionResponse)
async def get_resume_improvement_suggestions(
    request_data: SuggestionRequest,
    current_user: User = Depends(get_current_active_user) # 确保用户已登录
):
    """
    为指定的简历和职位描述生成改进建议.
    """
    resume_doc = await Resume.get(request_data.resume_id)
    if not resume_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    if resume_doc.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this resume.")

    # 确定用于分析的简历文本
    text_to_analyze = ""
    if request_data.resume_text_to_analyze:
        text_to_analyze = request_data.resume_text_to_analyze
    elif resume_doc.raw_text_content:
        text_to_analyze = resume_doc.raw_text_content
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume has no text content to analyze, and no specific text was provided.")

    # 构建发送给 Gemini 的 Prompt
    keywords_focus_str = "relevant keywords from the job description"
    if request_data.target_keywords:
        keywords_focus_str = "the following specific keywords: " + ", ".join(request_data.target_keywords)

    # 您可以在这里迭代和优化您的 Prompt
    prompt_template = f"""
    You are an expert AI career advisor and resume optimization specialist.
    Your goal is to provide actionable, specific, and constructive suggestions to improve the provided resume text so it aligns better with the given job description, particularly focusing on incorporating {keywords_focus_str}.

    Job Description (JD):
    ---
    {request_data.job_description_text}
    ---

    Resume Text to Improve:
    ---
    {text_to_analyze}
    ---

    Please provide detailed suggestions for improvement. Consider the following:
    1.  Identify key skills, experiences, and qualifications from the JD that are missing or underrepresented in the resume text.
    2.  Suggest how to rephrase sentences or bullet points in the resume text to naturally integrate {keywords_focus_str} or related concepts from the JD.
    3.  Recommend adding specific, quantifiable achievements or examples where possible, if relevant to the JD and the user's likely experience.
    4.  Ensure suggestions help maintain a professional tone and are grammatically correct.
    5.  Do NOT invent new experiences or skills for the user. Suggestions should be about better presenting existing qualifications or highlighting transferable skills.
    6.  Structure your output clearly. For example, you can list a keyword or a resume section, followed by your specific suggestions for it. Offer 2-3 alternative phrasings if appropriate.

    Provide your improvement suggestions below:
    """

    final_prompt = prompt_template.strip() # 移除可能的前后空白

    # 调用 Gemini 服务
    generated_suggestions = await generate_suggestions_from_gemini(prompt=final_prompt)

    return SuggestionResponse(
        resume_id=str(request_data.resume_id),
        suggestions=generated_suggestions,
        prompt_used=final_prompt # 返回实际使用的prompt，方便调试
    )