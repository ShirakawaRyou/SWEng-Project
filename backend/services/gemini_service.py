# backend/services/gemini_service.py
import google.generativeai as genai
from backend.config import settings
from typing import List, Dict, Any

# 配置 Gemini API 密钥
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}. Ensure GEMINI_API_KEY is set correctly.")
    # 根据需要，可以选择在这里抛出异常或设置一个标志指示服务不可用

# 选择一个 Gemini 模型
# gemini-1.5-flash-latest 通常性价比高且速度快
# gemini-1.0-pro 也是一个不错的选择
# 查阅 Gemini 文档获取最新和最适合您需求的模型名称
GENERATION_CONFIG = {
  "temperature": 0.7, # 控制创意程度，0.0-1.0
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048, # 根据需要调整输出长度
}

SAFETY_SETTINGS = [ # 根据需要调整安全设置
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# 初始化模型，建议在应用启动时或首次使用时进行，而不是每次调用都初始化
# 为简单起见，我们在这里全局初始化，但对于大型应用，可以考虑更复杂的管理方式
gemini_model = None
if settings.GEMINI_API_KEY: # 仅当API密钥存在时才尝试初始化
    try:
        gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest", # 或者 gemini-pro
            generation_config=GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS
        )
        print("Gemini model initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Gemini model: {e}")
        gemini_model = None # 确保模型为 None 如果初始化失败
else:
    print("GEMINI_API_KEY not found. Gemini service will not be available.")


async def generate_suggestions_from_gemini(prompt: str) -> str:
    """
    使用提供的完整 prompt 调用 Gemini API 并获取建议。
    """
    if not gemini_model:
        # raise HTTPException(status_code=503, detail="Gemini service is not available. API key may be missing or model failed to initialize.")
        print("Gemini model not initialized. Returning empty suggestions.")
        return "Gemini service is currently unavailable or not configured."

    try:
        print("\n--- Sending Prompt to Gemini ---")
        print(prompt)
        print("--- End of Prompt ---\n")
        
        # Gemini API v1.0.0 推荐使用 generate_content_async
        response = await gemini_model.generate_content_async(prompt)
        
        # 检查是否有候选内容并且内容不为空
        if response.candidates and response.candidates[0].content.parts:
            suggestions = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
            print("\n--- Received Suggestions from Gemini ---")
            print(suggestions)
            print("--- End of Suggestions ---\n")
            return suggestions.strip()
        else:
            # 处理没有有效回复的情况 (例如，被安全设置阻止)
            # response.prompt_feedback 会包含被阻止的原因
            block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "Unknown"
            error_message = f"Gemini API did not return suggestions. Block reason: {block_reason}. Check safety settings or prompt."
            print(error_message)
            if response.prompt_feedback:
                for rating in response.prompt_feedback.safety_ratings:
                    print(rating)
            return error_message

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # import traceback
        # print(traceback.format_exc())
        # 对于生产环境，这里应该记录更详细的错误并可能返回一个用户友好的错误信息
        return f"An error occurred while generating suggestions: {str(e)}"