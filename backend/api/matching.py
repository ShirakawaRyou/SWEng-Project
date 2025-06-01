# backend/api/matching.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from beanie import PydanticObjectId

from backend.models.user import User
from backend.models.resume import Resume, ResumeRead # ResumeRead 用于返回简历基本信息
from backend.core.security import get_current_active_user
from backend.services.keyword_extractor import extract_keywords_from_jd
from backend.services.matching_service import calculate_match_score
from backend.services.gemini_service import generate_suggestions_from_gemini # 导入 Gemini 服务
from datetime import timedelta, timezone # 导入 timedelta 和 timezone
from backend.models.processed_jd import ProcessedJD
from pydantic import BaseModel, Field, model_validator
from backend.models.processed_jd import ProcessedJD # 确保导入
from datetime import datetime # 用于获取当前UTC时间  





router = APIRouter()

class JDKeywordResponse(BaseModel): # 新的响应模型
    jd_id: str # PydanticObjectId 会序列化为 str
    keywords: List[str]

class JDInput(BaseModel):
    jd_text: str = Field(..., min_length=50, description="The full text of the Job Description.")

class MatchRequest(BaseModel):
    jd_text: Optional[str] = Field(None, min_length=50, description="The full text of the Job Description (if jd_id is not provided).")
    jd_id: Optional[PydanticObjectId] = Field(None, description="The ID of a previously processed Job Description.")
    resume_ids: List[PydanticObjectId] = Field(..., description="A list of resume IDs to match against the JD.")
    # 添加一个校验器确保 jd_text 或 jd_id 至少有一个被提供
    # from pydantic import root_validator
    # @root_validator(pre=False) # Pydantic V1
    # def check_jd_input(cls, values):
    #     if not values.get("jd_text") and not values.get("jd_id"):
    #         raise ValueError("Either jd_text or jd_id must be provided")
    #     if values.get("jd_text") and values.get("jd_id"):
    #         raise ValueError("Provide either jd_text or jd_id, not both")
    #     return values
    # Pydantic V2 使用 model_validator:
    @model_validator(mode='after')
    def check_jd_input(self) -> 'MatchRequest':
        if not self.jd_text and not self.jd_id:
            raise ValueError("Either jd_text or jd_id must be provided")
        if self.jd_text and self.jd_id:
            raise ValueError("Provide either jd_text or jd_id, not both")
        return self

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
    jd_text: Optional[str] = Field(default=None, min_length=50, description="The full text of the JD (if jd_id not provided).")
    jd_id: Optional[PydanticObjectId] = Field(default=None, description="The ID of a previously processed JD.")
    resume_id: PydanticObjectId
    resume_text_to_analyze: Optional[str] = Field(None, min_length=20)
    # target_keywords: Optional[List[str]] = Field(None)
    # 添加类似的 model_validator
    @model_validator(mode='after')
    def check_jd_input(self) -> 'SuggestionRequest':
        if not self.jd_text and not self.jd_id:
            raise ValueError("Either jd_text or jd_id must be provided")
        if self.jd_text and self.jd_id:
            raise ValueError("Provide either jd_text or jd_id, not both")
        return self

class SuggestionResponse(BaseModel):
    resume_id: str
    suggestions: str # Gemini 返回的文本建议
    prompt_used: str # 将实际发送给 Gemini 的 prompt 返回，方便调试



@router.post("/extract-jd-keywords", response_model=JDKeywordResponse) # 修改响应模型
async def api_extract_jd_keywords(jd_input: JDInput):
    if not jd_input.jd_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description text cannot be empty.")

    keywords = extract_keywords_from_jd(jd_input.jd_text)

    # 设置过期时间为从现在起24小时后
    expiration_time = datetime.now(timezone.utc) + timedelta(hours=24) # 使用带时区的UTC时间

    processed_jd_doc = ProcessedJD(
        jd_text=jd_input.jd_text, 
        keywords=keywords,
        expire_at=expiration_time # <--- 设置过期时间
    )
    await processed_jd_doc.insert()
    
    return JDKeywordResponse(jd_id=str(processed_jd_doc.id), keywords=keywords)


@router.post("/match-resumes", response_model=MatchResponse)
async def api_match_resumes_with_jd(
    request_data: MatchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    接收职位描述和简历ID列表，计算匹配度.
    用户必须已登录.
    """
    final_jd_text = ""
    jd_keywords: List[str] = []

    if request_data.jd_id:
        processed_jd_doc = await ProcessedJD.get(request_data.jd_id)
        if not processed_jd_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processed JD not found for the given jd_id.")
        final_jd_text = processed_jd_doc.jd_text
        jd_keywords = processed_jd_doc.keywords
    elif request_data.jd_text:
        final_jd_text = request_data.jd_text
        if not final_jd_text.strip(): # 确保不为空
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description text cannot be empty.")
        jd_keywords = extract_keywords_from_jd(final_jd_text)
    else:
        # 这个情况应该被 Pydantic model_validator 捕获
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No JD input provided.")

    if not request_data.resume_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume IDs list cannot be empty.")

    if not jd_keywords: # 如果JD没有提取出任何关键词
        # 返回空的关键词列表和空的匹配结果，或者一个特定的提示
        return MatchResponse(job_description_keywords=[], match_results=[])

    match_results: List[ResumeMatchResult] = []

    for resume_id in request_data.resume_ids:
        resume_doc = await Resume.get(resume_id)
        if not resume_doc:
            # 如果某个简历ID无效，可以选择跳过，或抛出错误，或在结果中标记
            # 这里我们选择跳过，并在结果中不包含它
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

# backend/api/matching.py
# ...
@router.post("/suggestions", response_model=SuggestionResponse)
async def get_resume_improvement_suggestions(
    request_data: SuggestionRequest,
    current_user: User = Depends(get_current_active_user)
):
    resume_doc = await Resume.get(request_data.resume_id)
    if not resume_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    if resume_doc.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this resume.")

    text_to_analyze = ""
    if request_data.resume_text_to_analyze:
        text_to_analyze = request_data.resume_text_to_analyze
    elif resume_doc.raw_text_content:
        text_to_analyze = resume_doc.raw_text_content
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume has no text content to analyze, and no specific text was provided.")

    # ==> 获取 JD 文本和关键词 <==
    final_jd_text = ""
    retrieved_jd_keywords: List[str] = []

    if request_data.jd_id:
        processed_jd_doc = await ProcessedJD.get(request_data.jd_id)
        if not processed_jd_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processed JD not found for the given jd_id.")
        final_jd_text = processed_jd_doc.jd_text
        retrieved_jd_keywords = processed_jd_doc.keywords
    elif request_data.jd_text: # jd_id 没提供，但 jd_text 提供了
        final_jd_text = request_data.jd_text
        if not final_jd_text.strip():
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description text cannot be empty.")
        retrieved_jd_keywords = extract_keywords_from_jd(final_jd_text) # 动态提取
    else:
        # 此情况应被 Pydantic model_validator 捕获
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No JD input (jd_id or jd_text) provided.")


    # 构建发送给 Gemini 的 Prompt
    keywords_focus_str = "relevant keywords from the job description"
    if retrieved_jd_keywords: # <--- 使用从数据库获取或动态提取的关键词
        keywords_focus_str = "the following specific keywords: " + ", ".join(retrieved_jd_keywords)

    prompt_template = f"""
    You are an expert AI career advisor and resume optimization specialist.
    Your goal is to provide actionable, specific, and constructive suggestions to improve the provided resume text so it aligns better with the given job description, particularly focusing on incorporating {keywords_focus_str}.

    Job Description (JD):
    ---
    {final_jd_text} 
    ---

    Resume Text to Improve:
    ---
    {text_to_analyze}
    ---

    Please provide detailed suggestions for improvement. Consider the following:
    1.  Identify key skills, experiences, and qualifications from the JD that are missing or underrepresented in the resume text, focusing on the keywords: {", ".join(retrieved_jd_keywords) if retrieved_jd_keywords else "general JD requirements"}.
    2.  Suggest how to rephrase sentences or bullet points in the resume text to naturally integrate these keywords or related concepts from the JD.
    3.  Recommend adding specific, quantifiable achievements or examples where possible, if relevant to the JD and the user's likely experience.
    4.  Ensure suggestions help maintain a professional tone and are grammatically correct.
    5.  Do NOT invent new experiences or skills for the user. Suggestions should be about better presenting existing qualifications or highlighting transferable skills.
    6.  Structure your output clearly. For example, you can list a keyword or a resume section, followed by your specific suggestions for it. Offer 2-3 alternative phrasings if appropriate.

    Provide your improvement suggestions below:
    """
    final_prompt = prompt_template.strip()

    generated_suggestions = await generate_suggestions_from_gemini(prompt=final_prompt)

    return SuggestionResponse(
        resume_id=str(request_data.resume_id),
        suggestions=generated_suggestions,
        prompt_used=final_prompt
    )