"""
简历解析
""" 
# backend/services/resume_parser.py
import io
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from fastapi import UploadFile
from typing import Optional, Tuple # 导入 Optional 和 Tuple
import fitz # PyMuPDF

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
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text_content += page.extract_text() or "" # 添加 "or """ 以处理 None 的情况
        
        elif file_extension == "docx":
            docx_file = io.BytesIO(content)
            doc = DocxDocument(docx_file)
            for para in doc.paragraphs:
                text_content += para.text + "\n"
        
        return text_content.strip()

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