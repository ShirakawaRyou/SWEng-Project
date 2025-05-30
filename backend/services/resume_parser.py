"""
简历解析
""" 
# backend/services/resume_parser.py
import io
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from fastapi import UploadFile
from typing import Optional, Tuple, Dict, List, Any # 确保导入 Dict, List, Any
import fitz # PyMuPDF
import re # 导入正则表达式库

SUPPORTED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}

async def parse_resume_file(file: UploadFile) -> str:
    """
    解析上传的简历文件 (PDF 或 DOCX) 并提取纯文本内容。
    """
    if file.content_type not in SUPPORTED_MIME_TYPES:
        raise ValueError(f"Unsupported file type: {file.content_type}. Supported types are PDF and DOCX.")

    file_extension = SUPPORTED_MIME_TYPES[file.content_type]
    content = await file.read() # 读取文件内容为 bytes
    await file.seek(0) # 重置文件指针，以防后续需要再次读取

    text_content = ""

    try:
        if file_extension == "pdf":
            # ==> 使用 PyMuPDF (fitz) 解析 PDF <==
            pdf_doc = fitz.open(stream=content, filetype="pdf")
            for page_num in range(len(pdf_doc)):
                page = pdf_doc.load_page(page_num)
                # 使用 text_content += page.get_text("text") or "" 获取纯文本，通常效果更好
                # "blocks" 参数可以提供更结构化的文本块，但对于纯文本提取，"text" 即可
                text_content += page.get_text("text", sort=True) or "" # sort=True尝试按阅读顺序排序
            pdf_doc.close()
        
        elif file_extension == "docx":
            docx_file = io.BytesIO(content)
            doc = DocxDocument(docx_file)
            for para in doc.paragraphs:
                text_content += para.text + "\n"
        
        return ' '.join(text_content.split()) # 清理多余的空格和换行符

    except Exception as e:
        # 可以记录更详细的日志
        print(f"Error parsing file {file.filename}: {e}")
        # 根据需要，可以选择抛出更具体的错误或返回空字符串/None
        raise ValueError(f"Could not parse the uploaded file: {file.filename}. Error: {str(e)}")
    

THUMBNAIL_WIDTH = 150 # 缩略图目标宽度 (像素)
THUMBNAIL_HEIGHT = 200 # 缩略图目标高度 (像素) - 可根据简历常见比例调整


async def generate_pdf_thumbnail(pdf_content: bytes) -> Optional[Tuple[bytes, str]]:
    print("[Thumbnail Service] Attempting to generate PDF thumbnail...") # 1. 函数进入点
    doc = None # 初始化 doc，确保 finally 块中可用
    try:
        if not pdf_content:
            print("[Thumbnail Service] PDF content is empty. Returning None.") # 2. 检查输入内容
            return None

        print(f"[Thumbnail Service] Opening PDF from bytes (length: {len(pdf_content)})...") # 3. 尝试打开
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        print(f"[Thumbnail Service] PDF opened. Number of pages: {len(doc)}") # 4. 页面数量

        if len(doc) == 0:
            print("[Thumbnail Service] PDF has no pages. Returning None.") # 5. 无页面处理
            if doc: doc.close() # 确保关闭文档
            return None

        page = doc[0] # 获取第一页
        print("[Thumbnail Service] Got first page.") # 6. 获取首页

        # 根据您的 THUMBNAIL_WIDTH 和 THUMBNAIL_HEIGHT 计算缩放
        zoom_x = THUMBNAIL_WIDTH / page.rect.width if page.rect.width > 0 else 1
        zoom_y = THUMBNAIL_HEIGHT / page.rect.height if page.rect.height > 0 else 1
        zoom = min(zoom_x, zoom_y) 
        if zoom <= 0: # 防止 zoom 值为0或负数
            print(f"[Thumbnail Service] Invalid zoom factor calculated ({zoom}). Using zoom=1.")
            zoom = 1 # 使用一个安全的默认值
        
        print(f"[Thumbnail Service] Page rect: {page.rect}, Calculated zoom: {zoom}") # 7. 页面尺寸和缩放

        matrix = fitz.Matrix(zoom, zoom)
        print("[Thumbnail Service] Getting pixmap with matrix...") # 8. 尝试获取像素图
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        print(f"[Thumbnail Service] Got pixmap (width: {pix.width}, height: {pix.height}). Converting to PNG bytes...") # 9. 获取成功

        img_bytes = pix.tobytes("png") # 输出为 PNG 格式
        if not img_bytes:
            print("[Thumbnail Service] PNG bytes are empty after conversion. Returning None.") # 10. 检查转换结果
            if doc: doc.close()
            return None

        print(f"[Thumbnail Service] PNG bytes generated (length: {len(img_bytes)}). Returning image data.") # 11. 成功返回
        if doc: doc.close()
        return img_bytes, "image/png"
    except Exception as e:
        print(f"[Thumbnail Service] Error generating PDF thumbnail: {e}") # 12. 捕获到异常
        # 考虑打印更详细的堆栈跟踪信息进行调试
        import traceback
        print(traceback.format_exc())
        if doc: doc.close() # 确保在异常情况下也关闭文档
        return None
    # finally: # finally 块不是必须的，因为我们在 try 和 except 中都调用了 close
    #     if doc:
    #         print("[Thumbnail Service] Closing PDF document in finally.")
    #         doc.close()

# --- 新增：简历区段化逻辑 ---
SECTION_TITLE_KEYWORDS = {
    "contact_info": [r"contact information", r"contact details", r"personal information", r"personal details", r"phone", r"email", r"linkedin", r"github", r"portfolio"],
    "summary": [r"summary", r"objective", r"professional profile", r"profile", r"about me", r"personal summary"],
    "experience": [r"experience", r"work experience", r"professional experience", r"employment history", r"career history", r"relevant experience"],
    "education": [r"education", r"academic background", r"academic qualifications", r"qualifications"],
    "skills": [r"skills", r"technical skills", r"technical proficiency", r"proficiencies", r"expertise", r"core competencies"],
    "projects": [r"projects", r"personal projects", r"academic projects", r"portfolio"],
    "awards": [r"awards", r"honors", r"recognitions", r"achievements"], # 'achievements' 比较通用，也可能在经验部分
    "publications": [r"publications", r"research"],
    "certifications": [r"certifications", r"licenses & certifications", r"certificates"],
    "languages": [r"languages", r"language proficiency"],
    "references": [r"references"]
    # 您可以根据需要添加更多区段和关键词
}

# 将检测到的标题标准化为统一的键名
CANONICAL_SECTION_KEYS = {
    "contact information": "contact_info", "contact details": "contact_info", "personal information": "contact_info", "personal details": "contact_info",
    "phone": "contact_info", "email": "contact_info", "linkedin": "contact_info", "github": "contact_info",
    "objective": "summary", "professional profile": "summary", "profile": "summary", "about me": "summary", "personal summary":"summary",
    "work experience": "experience", "professional experience": "experience", "employment history": "experience", "career history": "experience", "relevant experience":"experience",
    "academic background": "education", "academic qualifications": "education", "qualifications": "education", # qualifications 也可能指技能
    "technical skills": "skills", "technical proficiency": "skills", "proficiencies": "skills", "expertise": "skills", "core competencies": "skills",
    "personal projects": "projects", "academic projects": "projects",
    "honors": "awards", "recognitions": "awards", # achievements 比较通用
    "research": "publications",
    "licenses & certifications": "certifications", "certificates": "certifications",
    "language proficiency": "languages"
}

def segment_text_into_sections(raw_text: str) -> Dict[str, str]:
    """
    尝试将原始简历文本分割成不同的区段。
    这是一个基于规则的简单实现。
    """
    if not raw_text or not raw_text.strip():
        return {}

    sections: Dict[str, str] = {}
    lines = raw_text.splitlines()
    
    current_section_key: Optional[str] = None
    current_section_content: List[str] = []
    
    # 构建一个扁平的 (原始标题小写, 标准化键名) 列表，用于匹配
    header_patterns = []
    for canonical_key, keywords_list in SECTION_TITLE_KEYWORDS.items():
        for keyword in keywords_list:
            # 为每个关键词创建一个不区分大小写的、匹配整行（可带冒号等）的正则表达式模式
            # ^\s*keyword\s*[:\-\–—]?\s*$
            # \s* 匹配任意空白符（包括没有）
            # [:\-\–—]? 匹配可选的冒号或各种破折号
            # $ 匹配行尾
            pattern = re.compile(r"^\s*" + re.escape(keyword) + r"\s*[:\-\–—]?\s*$", re.IGNORECASE)
            header_patterns.append((pattern, CANONICAL_SECTION_KEYS.get(keyword, canonical_key)))

    # 内容开始前的部分，可以放入 "header_details" 或 "unknown_initial"
    initial_content_key = "unknown_initial"

    for line in lines:
        cleaned_line = line.strip()
        
        matched_section_key: Optional[str] = None
        for pattern, key in header_patterns:
            if pattern.fullmatch(cleaned_line): # 使用 fullmatch 确保整行都是标题
                matched_section_key = key
                break
        
        if matched_section_key:
            # 找到了新的区段标题
            if current_section_key and current_section_content: # 保存上一个区段的内容
                sections[current_section_key] = "\n".join(current_section_content).strip()
            elif not current_section_key and current_section_content: # 处理第一个区段之前的内容
                 sections[initial_content_key] = "\n".join(current_section_content).strip()

            current_section_key = matched_section_key
            current_section_content = [] # 为新区段重置内容
            # 通常不把标题行本身作为内容，除非标题行也包含信息
            # 如果标题行也可能包含内容，可以在这里添加： current_section_content.append(cleaned_line)
        elif cleaned_line: # 非空行且不是标题行
            current_section_content.append(cleaned_line)
        elif current_section_key: # 空行，但在一个区段内，保留它以维持段落感
            current_section_content.append("")


    # 保存最后一个区段的内容
    if current_section_key and current_section_content:
        sections[current_section_key] = "\n".join(current_section_content).strip()
    elif not current_section_key and current_section_content: # 如果整个简历都没有匹配到任何标题
        sections[initial_content_key] = "\n".join(current_section_content).strip()

    # 清理空的 initial_content_key
    if initial_content_key in sections and not sections[initial_content_key]:
        del sections[initial_content_key]
        
    return sections