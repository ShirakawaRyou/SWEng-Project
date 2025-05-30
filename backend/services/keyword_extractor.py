# backend/services/keyword_extractor.py
import spacy
from spacy.lang.en.stop_words import STOP_WORDS as spacy_stop_words
import nltk
from nltk.corpus import stopwords as nltk_stop_words # NLTK 的停用词列表更全一些
from typing import List, Set
import re # 导入正则表达式库


# 加载 spaCy 的小型英文模型
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
    # 或者在这里尝试下载，但通常建议用户手动下载
    # spacy.cli.download("en_core_web_sm")
    # nlp = spacy.load("en_core_web_sm")
    # For now, if not found, we can let it fail or use a dummy nlp, but proper installation is key.
    raise ImportError("spaCy model 'en_core_web_sm' not found. Please ensure it's downloaded.")


# 合并停用词列表
try:
    nltk_stopwords_set = set(nltk_stop_words.words('english'))
except LookupError:
    nltk.download('stopwords')
    nltk_stopwords_set = set(nltk_stop_words.words('english'))
combined_stopwords = spacy_stop_words.union(nltk_stopwords_set)

def extract_keywords_from_jd(jd_text: str) -> List[str]:
    """
    从职位描述文本中提取关键词。
    - 使用 spaCy 进行词形还原、词性标注。
    - 提取名词、专有名词、形容词作为候选关键词。
    - 提取名词短语。
    - 移除停用词和标点符号。
    - 返回去重后的关键词列表。
    """
    if not jd_text:
        return []
    
    # ==> 规范化换行符和空白 <==
    # 1. 将所有类型的换行符 (\r\n, \r, \n) 替换为单个空格
    processed_jd_text = jd_text.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
    # 2. 使用正则表达式将多个连续的空白符合并为一个空格
    processed_jd_text = re.sub(r'\s+', ' ', processed_jd_text).strip()


    doc = nlp(processed_jd_text)
    keywords: Set[str] = set()

    for token in doc:
        if (
            not token.is_stop and          # 非停用词
            not token.is_punct and         # 非标点
            not token.is_space and         # 非空白符
            token.pos_ in ["NOUN", "PROPN", "ADJ"] # 词性为名词、专有名词、形容词
        ):
            keywords.add(token.lemma_.lower().strip()) # 使用词元的小写形式

    # 提取名词短语 (Noun Chunks)
    for chunk in doc.noun_chunks:
        # 清理名词短语，移除内部的停用词和多余空格，然后小写
        # 例如 "data analysis skills" -> "data analysis skill"
        # 我们需要对 chunk 中的每个 token 进行处理
        cleaned_chunk_parts = [
            token.lemma_.lower() for token in chunk 
            if not token.is_stop and not token.is_punct and not token.is_space
        ]
        if cleaned_chunk_parts:
            keywords.add(" ".join(cleaned_chunk_parts).strip())
            
    for ent in doc.ents: # 如果您使用命名实体
        if ent.label_ in ["ORG", "PRODUCT", "GPE", "LOC", "LANGUAGE", "WORK_OF_ART"]: # 根据需要调整实体类型
             keywords.add(ent.text.lower().strip())

    # 移除可能混入的空字符串
    keywords.discard("")
    
    return sorted(list(keywords))

if __name__ == '__main__':
    # 测试代码
    sample_jd = """
    Job Title: Software Engineer (Python, FastAPI)
    Location: San Francisco, CA
    We are looking for a skilled Software Engineer to join our dynamic team.
    Responsibilities:
    - Design, develop, and maintain web applications using Python and FastAPI.
    - Collaborate with cross-functional teams to define and ship new features.
    - Write clean, scalable, and well-tested code.
    Required Skills:
    - 2+ years of experience in Python development.
    - Strong understanding of FastAPI or similar frameworks (e.g., Django, Flask).
    - Experience with relational databases (e.g., PostgreSQL, MySQL).
    - Proficient in Git and version control.
    - Excellent problem-solving skills.
    Nice to have:
    - Experience with Docker and Kubernetes.
    - Knowledge of cloud platforms (AWS, GCP, Azure).
    - Familiarity with frontend technologies (React, Vue).
    """
    extracted = extract_keywords_from_jd(sample_jd)
    print("Extracted Keywords:")
    for keyword in extracted:
        print(f"- {keyword}")