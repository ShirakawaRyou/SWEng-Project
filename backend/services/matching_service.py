# backend/services/matching_service.py
from typing import List, Set, Dict, Any, Tuple
# import spacy # 如果还需要 spaCy 进行简历文本预处理
from sentence_transformers import SentenceTransformer, util # 导入 sentence-transformers
import torch # sentence-transformers 可能需要 torch

# nltk 组件 (如果还需要用于简历文本预处理，例如分句)
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize 
# 确保 nltk.download('punkt') 已在 Dockerfile 中执行

# 初始化 Sentence Transformer 模型 (应该在应用启动时加载一次，而不是每次调用都加载)
# 为简单起见，我们在这里定义，实际应用中应考虑全局加载或作为类成员
try:
    model_name = 'all-MiniLM-L6-v2' # 速度快，效果不错
    # model_name = 'all-mpnet-base-v2' # 效果更好，稍大
    sbert_model = SentenceTransformer(model_name)
    print(f"SentenceTransformer model '{model_name}' loaded successfully.")
except Exception as e:
    print(f"Error loading SentenceTransformer model '{model_name}': {e}. Semantic matching will be degraded.")
    sbert_model = None


# （可选）如果还需要 spaCy/NLTK 进行简历文本的预处理（如分句、清理）
# try:
#     nlp_spacy = spacy.load("en_core_web_sm") # 或者您选择的 spaCy 模型
# except Exception as e:
#     print(f"Error loading spaCy model in matching_service: {e}")
#     nlp_spacy = None


# def calculate_semantic_match_score(resume_text: str, jd_key_phrases: List[str], similarity_threshold=0.5) -> float:
#     """
#     使用句子嵌入计算简历文本与JD关键短语列表的语义匹配度。
#     jd_key_phrases: 从JD提取的关键要求或技能短语列表。
#     similarity_threshold: 认为语义匹配的余弦相似度阈值。
#     """
#     if not sbert_model: # 如果模型加载失败
#         print("Warning: SentenceTransformer model not available. Falling back to basic keyword count (or returning 0).")
#         # 这里可以回退到之前的简单关键词计数方法，或者直接返回0或错误
#         # 为了演示，我们假设这里直接返回0，您需要实现回退逻辑
#         return 0.0 

#     if not resume_text or not jd_key_phrases:
#         return 0.0

#     # 1. 将简历文本分割成句子 (使用 NLTK)
#     #    也可以使用 spaCy: [sent.text for sent in nlp_spacy(resume_text).sents]
#     #    或者直接将整个 resume_text 或其主要区段作为单个文档进行编码
#     resume_sentences = sent_tokenize(resume_text)
#     if not resume_sentences:
#         return 0.0

#     # 2. 为简历句子和JD关键短语生成嵌入向量
#     try:
#         resume_embeddings = sbert_model.encode(resume_sentences, convert_to_tensor=True)
#         jd_phrase_embeddings = sbert_model.encode(jd_key_phrases, convert_to_tensor=True)
#     except Exception as e:
#         print(f"Error encoding texts with SentenceTransformer: {e}")
#         return 0.0 # 或者回退

#     matched_jd_phrases_count = 0
    
#     # 3. 对于每个JD关键短语，在简历句子中找到最相似的，并检查是否超过阈值
#     if jd_phrase_embeddings.nelement() == 0 or resume_embeddings.nelement() == 0 : # 处理空嵌入的情况
#         return 0.0

#     for jd_emb in jd_phrase_embeddings:
#         # 计算当前JD短语与所有简历句子的余弦相似度
#         cosine_scores = util.cos_sim(jd_emb, resume_embeddings)[0] # util.cos_sim 返回一个张量列表
        
#         # 找到最高的相似度得分
#         max_similarity = torch.max(cosine_scores).item()
        
#         if max_similarity >= similarity_threshold:
#             matched_jd_phrases_count += 1
#             # print(f"JD phrase matched with similarity: {max_similarity:.2f}") # 调试用

#     if not jd_key_phrases: # 避免除以零
#         return 0.0
        
#     score = (matched_jd_phrases_count / len(jd_key_phrases)) * 100.0
#     return round(score, 2)

def _get_max_semantic_similarity(jd_phrase: str, resume_sentences: List[str], resume_sentence_embeddings) -> float:
    if not sbert_model or not resume_sentences or resume_sentence_embeddings is None or resume_sentence_embeddings.nelement() == 0:
        return 0.0
    try:
        jd_phrase_embedding = sbert_model.encode(jd_phrase, convert_to_tensor=True)
        if jd_phrase_embedding.nelement() == 0:
            return 0.0
            
        # Ensure jd_phrase_embedding is 2D for cos_sim if it's a single phrase
        if len(jd_phrase_embedding.shape) == 1:
            jd_phrase_embedding = jd_phrase_embedding.unsqueeze(0)

        cosine_scores = util.cos_sim(jd_phrase_embedding, resume_sentence_embeddings)[0]
        return torch.max(cosine_scores).item()
    except Exception as e:
        print(f"Error calculating semantic similarity for phrase '{jd_phrase}': {e}")
        return 0.0

def calculate_combined_match_score(
    resume_text: str, 
    jd_keywords: List[str], # 假设这些是已预处理（小写、词形还原）的JD关键词/短语
    similarity_threshold=0.5 # 您选择的语义相似度阈值
) -> float:
    """
    结合直接字符串匹配和语义相似度匹配来计算分数。
    """
    if not resume_text or not jd_keywords:
        return 0.0

    # 1. 准备数据
    resume_text_lower = resume_text.lower() # 用于直接字符串匹配
    jd_keywords_set = set(kw.strip() for kw in jd_keywords if kw.strip()) # 清理并去重JD关键词

    if not jd_keywords_set:
        return 0.0

    # 为语义匹配准备简历句子和嵌入 (只做一次)
    resume_sentences = []
    resume_sentence_embeddings = None
    if sbert_model: # 仅当语义模型可用时
        try:
            resume_sentences = sent_tokenize(resume_text) # 使用NLTK分句
            if resume_sentences:
                resume_sentence_embeddings = sbert_model.encode(resume_sentences, convert_to_tensor=True)
        except Exception as e:
            print(f"Error preparing resume sentences/embeddings: {e}")
            # 如果出错，语义匹配部分将无法进行
            resume_sentences = []
            resume_sentence_embeddings = None


    matched_keywords_count = 0
    print(f"\n--- Matching JD Keywords ({len(jd_keywords_set)}) ---")

    for keyword_phrase in jd_keywords_set:
        # print(f"Checking JD keyword: '{keyword_phrase}'")
        found_match = False

        # 2. 尝试直接字符串匹配 (不区分大小写)
        if keyword_phrase in resume_text_lower:
            found_match = True
            # print(f"  Direct match found for: '{keyword_phrase}'")
        
        # 3. 如果直接匹配未成功，并且语义模型可用，则尝试语义匹配
        if not found_match and sbert_model and resume_sentences:
            max_similarity = _get_max_semantic_similarity(keyword_phrase, resume_sentences, resume_sentence_embeddings)
            # print(f"  Semantic similarity for '{keyword_phrase}': {max_similarity:.4f}")
            if max_similarity >= similarity_threshold:
                found_match = True
                # print(f"  Semantic match found for: '{keyword_phrase}' (score: {max_similarity:.4f})")

        if found_match:
            matched_keywords_count += 1

    print(f"Total JD keywords matched: {matched_keywords_count}")
    score = (matched_keywords_count / len(jd_keywords_set)) * 100.0
    return round(score, 2)

# 在您的 services/matching_service.py 中，将主要的 calculate_match_score 指向这个新函数
# calculate_match_score = calculate_combined_match_score # 如果您想替换掉旧的

# 别忘了在文件顶部加载 sbert_model (如之前的示例)
# 全局加载 sbert_model
_sbert_model_instance = None
def get_sbert_model():
    global _sbert_model_instance
    if _sbert_model_instance is None:
        try:
            model_name = 'all-MiniLM-L6-v2' # 或者 'all-mpnet-base-v2'
            _sbert_model_instance = SentenceTransformer(model_name)
            print(f"SentenceTransformer model '{model_name}' loaded successfully for matching service.")
        except Exception as e:
            print(f"Error loading SentenceTransformer model in matching_service: {e}")
    return _sbert_model_instance

sbert_model = get_sbert_model() # 在模块加载时尝试加载一次


# 确保您的 calculate_match_score 现在指向 calculate_combined_match_score
# 如果您在 api/matching.py 中导入的是 calculate_match_score，
# 那么在这里修改:
calculate_match_score = calculate_combined_match_score

if __name__ == '__main__':
    # 测试代码
    sample_resume = "I have extensive experience in developing web applications with Python and a strong background in data science projects using machine learning techniques. Proficient with tools like Git and Docker. Worked with AWS cloud services."
    jd_phrases = [
        "python web development experience", # 与 "developing web applications with Python" 语义相关
        "machine learning",                  # 精确匹配 (如果模型好)
        "aws cloud services",                # 精确匹配
        "knowledge of agile methodology"     # 简历中未提及
    ]
    
    score = calculate_match_score(sample_resume, jd_phrases, similarity_threshold=0.6) # 阈值需要调整
    print(f"Semantic match score: {score}%") # 期望是 75% (3 out of 4)

    # 如果 sbert_model 为 None 的测试
    # original_sbert_model = sbert_model
    # sbert_model = None
    # score_no_model = calculate_match_score(sample_resume, jd_phrases)
    # print(f"Score with no SBERT model: {score_no_model}%")
    # sbert_model = original_sbert_model