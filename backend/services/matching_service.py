# backend/services/matching_service.py
from typing import List
import spacy # 我们也用 spaCy 来处理简历文本以保持一致性
from typing import Set

# 确保 nlp 模型已加载 (可以从 keyword_extractor 导入或再次加载)
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e: # 更通用的异常捕获
    print(f"Error loading spaCy model in matching_service: {e}. Ensure 'en_core_web_sm' is downloaded.")
    raise ImportError("spaCy model 'en_core_web_sm' not found or failed to load.")


def preprocess_text_for_matching(text: str) -> Set[str]:
    """
    对文本进行预处理（小写、词形还原、移除停用词和标点），返回词元集合。
    """
    if not text:
        return set()
    
    doc = nlp(text)
    lemmas = set()
    for token in doc:
        if not token.is_stop and not token.is_punct and not token.is_space:
            lemmas.add(token.lemma_.lower().strip())
    lemmas.discard("")
    return lemmas

def calculate_match_score(resume_text: str, jd_keywords: List[str]) -> float:
    """
    计算简历文本与JD关键词列表的匹配度。
    返回一个 0-100 之间的百分比分数。
    简单匹配：计算简历中出现JD关键词的比例。
    """
    if not resume_text or not jd_keywords:
        return 0.0

    processed_resume_lemmas = preprocess_text_for_matching(resume_text)
    
    # JD 关键词也应该是小写词元形式 (keyword_extractor 已处理)
    jd_keywords_set = set(keyword.lower().strip() for keyword in jd_keywords if keyword.strip()) # 确保jd_keywords也被清理

    if not jd_keywords_set: # 如果JD关键词为空，则无法匹配
        return 0.0

    matched_keywords_count = 0
    for keyword in jd_keywords_set:
        # 对于多词关键词，我们需要检查它们是否作为一个整体出现在简历中
        # 但我们的 preprocess_text_for_matching 返回的是单个词元集合
        # 所以，对于多词JD关键词，简单匹配可能会失效
        # 改进：如果JD关键词是多词，检查这些词是否都存在于简历词元中
        # 或者，更简单的方式是，直接在预处理后的简历文本字符串中查找关键词字符串
        
        # 方案1: 基于词元集合的匹配 (对单字关键词友好)
        # if keyword in processed_resume_lemmas:
        #    matched_keywords_count += 1
            
        # 方案2: 在原始文本（小写处理后）中查找关键词（对多字关键词更直接）
        # 我们需要对简历文本做小写处理
        resume_text_lower = resume_text.lower()
        if keyword in resume_text_lower: # 直接查找小写的关键词字符串
            matched_keywords_count += 1
            
    score = (matched_keywords_count / len(jd_keywords_set)) * 100.0
    return round(score, 2)


if __name__ == '__main__':
    # 测试代码
    sample_resume_text = """
    Highly skilled Python Software Engineer with 3 years of experience in web development
    using FastAPI and Django. Proficient in PostgreSQL and Git. 
    Developed and deployed applications on AWS. Familiar with Docker.
    Excellent problem-solver.
    """
    sample_jd_keywords = [
        "python", "fastapi", "django", "postgresql", "git", "aws", "docker", 
        "problem-solving", "web development", "software engineer", "experience"
    ] # 假设这些是已提取并小写处理的关键词

    score = calculate_match_score(sample_resume_text, sample_jd_keywords)
    print(f"Resume match score: {score}%")

    empty_resume_score = calculate_match_score("", sample_jd_keywords)
    print(f"Empty resume score: {empty_resume_score}%")
    
    empty_keywords_score = calculate_match_score(sample_resume_text, [])
    print(f"Empty keywords score: {empty_keywords_score}%")

    # 测试多词关键词 (假设 keyword_extractor 返回的关键词是小写词元化的)
    multi_word_keywords = ["software engineer", "web development", "problem-solving skill"] # 注意 skill vs skills
    # 预处理简历，得到词元
    processed_resume = preprocess_text_for_matching(sample_resume_text)
    print(f"Processed resume lemmas: {processed_resume}")
    
    # 对于多词关键词，方案2（直接在小写文本中查找）更直接
    score_multi_word_direct = calculate_match_score(sample_resume_text, multi_word_keywords)
    print(f"Multi-word keywords direct search score: {score_multi_word_direct}%")