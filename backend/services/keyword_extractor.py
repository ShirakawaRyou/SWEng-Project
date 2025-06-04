# backend/services/keyword_extractor.py
import spacy
from spacy.matcher import PhraseMatcher
from spacy.lang.en.stop_words import STOP_WORDS as spacy_stop_words
from typing import List, Set, Optional, Dict
import re

# --- spaCy 模型加载 ---
# 确保此模型已在 Dockerfile 中下载: python -m spacy download en_core_web_md
try:
    nlp = spacy.load("en_core_web_md") # 使用中型模型以获得更好的NER和词向量
except OSError:
    print("spaCy model 'en_core_web_md' not found. Please run: `python -m spacy download en_core_web_md` or ensure it's in your Dockerfile.")
    # 在生产环境中，如果模型加载失败，可能需要更健壮的错误处理或回退机制
    # 为了演示，如果加载失败，后续的 nlp(text) 调用会直接失败
    raise ImportError("spaCy 'md' model not found. Critical for keyword extraction.")

# --- 已知技术技能列表 (您提供的列表已经很全面了) ---
# --- 预定义的技术/技能词典 ---
# 这个列表需要您根据目标JD的领域和常见技术不断扩充和优化
KNOWN_TECH_SKILLS = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "golang", "ruby", "php", "swift", 
    "kotlin", "scala", "rust", "perl", "lua", "dart", "r", "objective-c", "groovy", "haskell", "elixir",
    "clojure", "erlang", "f#", "powershell", "bash", "shell scripting", "sql", "pl/sql",

    # Frontend Frameworks/Libraries
    "react", "react.js", "angular", "angular.js", "vue", "vue.js", "svelte", "next.js", "nuxtjs", 
    "gatsby", "ember.js", "jquery", "redux", "mobx", "rxjs", "ngrx", "vuex", "zustand", "pinia",
    "html", "html5", "css", "css3", "sass", "scss", "less", "bootstrap", "tailwind css", "material ui", 
    "ant design", "chakra ui", "styled components", "webpack", "babel", "vite", "gulp", "grunt", "jest", 
    "cypress", "playwright", "storybook", "figma", "sketch", "adobe xd", "webgl", "three.js",

    # Backend Frameworks/Libraries
    "node.js", "express", "express.js", "django", "flask", "fastapi", "spring", "spring boot", 
    "ruby on rails", "rails", "laravel", ".net", ".net core", "asp.net", "asp.net core", "entity framework", 
    "phoenix (elixir)", "akka", "play framework (scala/java)", "ktor (kotlin)", "gin (go)", "echo (go)", 
    "fiber (go)", "symfony", "cakephp", "codeigniter", "nestjs", "koa", "hapi",

    # Databases & Storage
    "mysql", "postgresql", "postgres", "sqlite", "microsoft sql server", "ms sql", "sql server", "oracle database", 
    "nosql", "mongodb", "mongo", "redis", "memcached", "cassandra", "elasticsearch", "solr", "opensearch", 
    "dynamodb", "firebase realtimedb", "firebase firestore", "google firestore",
    "couchbase", "couchdb", "neo4j", "influxdb", "timescaledb", "prometheus", "graphql", "realm", "supabase",
    "sqlalchemy", "typeorm", "mongoose", "beanie ODM", "prisma ORM", "drizzle orm",

    # Cloud Platforms & Services
    "aws", "amazon web services", "azure", "microsoft azure", "gcp", "google cloud platform", 
    "heroku", "digitalocean", "netlify", "vercel", "firebase hosting", "oracle cloud (oci)", "ibm cloud",
    "alibaba cloud", "tencent cloud", "openshift", "cloudfoundry", "kubernetes engine (gke, aks, eks)",
    "ec2", "s3", "lambda (aws)", "rds", "ecs", "eks", "fargate", "beanstalk", "cloudfront", "route 53",
    "azure functions", "azure app service", "azure blob storage", "azure virtual machines", "azure kubernetes service (aks)",
    "google app engine", "google compute engine", "google kubernetes engine (gke)", "google cloud functions", 
    "google cloud storage", "serverless framework",

    # DevOps, CI/CD, & Tools
    "docker", "kubernetes", "k8s", "jenkins", "gitlab ci", "gitlab", "github actions", "circleci", "travis ci", 
    "ansible", "terraform", "chef", "puppet", "vagrant", "git", "github", "bitbucket", 
    "svn", "maven", "gradle", "npm", "yarn", "pip", "conda", "jira", "confluence", "slack", "trello",
    "sonarqube", "artifactory", "nexus repository", "prometheus", "grafana", "datadog", "new relic", "splunk",
    "elk stack", "logstash", "kibana", "argocd", "spinnaker", "datadog", "sentry",

    # Data Science, ML, AI
    "machine learning", "ml", "deep learning", "dl", "natural language processing", "nlp", 
    "computer vision", "cv", "data analysis", "data mining", "data visualization", "statistics", "econometrics",
    "tensorflow", "keras", "pytorch", "torch", "scikit-learn", "sklearn", "pandas", "numpy", "scipy", 
    "matplotlib", "seaborn", "plotly", "dash", "nltk", "spacy", "gensim", "hugging face transformers", "transformers",
    "opencv", "hadoop", "apache spark", "spark", "pyspark", "kafka", "apache kafka", "airflow", "apache airflow", 
    "rstudio", "jupyter", "jupyter notebook", "jupyterlab", "tableau", "power bi", "google data studio", 
    "bigquery", "redshift", "snowflake", "databricks", "dbt", "mlflow", "kubeflow", "dvc", "apache flink",

    # Mobile Development
    "ios development", "android development", "swift (ios)", "objective-c (ios)", "kotlin (android)", "java (android)", 
    "react native", "flutter", "xamarin", "ionic", "nativescript", "xcode", "android studio",

    # Operating Systems
    "linux", "unix", "windows server", "macos server", "ubuntu", "centos", "debian", "red hat enterprise linux (rhel)", "fedora",

    # Methodologies & Concepts
    "agile", "scrum", "kanban", "lean", "waterfall", "devops principles", "ci/cd pipelines", "microservice architecture", 
    "restful services", "rest apis", "api design principles", "object-oriented programming (oop)", "functional programming (fp)", 
    "test-driven development (tdd)", "behavior-driven development (bdd)", "domain-driven design (ddd)", 
    "software design patterns", "data structures and algorithms", "system architecture", "scalability principles", 
    "high availability", "disaster recovery", "software security principles", "encryption techniques",
    "authentication protocols", "authorization mechanisms", "oauth2", "saml", "openid connect", "jwt (json web tokens)", 
    "web scraping", "web crawling", "performance optimization", "code optimization", "unit testing", "integration testing", 
    "end-to-end testing", "e2e testing",

    # Testing Frameworks/Tools (expanded)
    "junit (java)", "testng (java)", "selenium webdriver", "playwright", "puppeteer", "pytest (python)", 
    "unittest (python)", "robot framework", "mocha (js)", "chai (js)", "jasmine (js)", "enzyme (react)", 
    "react testing library", "vue test utils", "appium (mobile)", "postman (api)", "soapui (api)", "k6 (load testing)",
    "jmeter (load testing)", "mockito (java)", "nunit (.net)", "xctest (ios)", "espresso (android)",

    # Big Data (expanded)
    "hdfs", "mapreduce", "apache hive", "apache pig", "apache presto", "apache flink", "kafka streams", 
    "apache nifi", "apache beam", "druid", "clickhouse",

    # Game Development
    "unity3d", "unreal engine (ue4, ue5)", "c# (for unity)", "c++ (for unreal)", "blender (3d modeling)", 
    "maya (3d modeling)", "directx", "opengl", "vulkan api", "game physics", "game ai", "networking for games",

    # Cybersecurity
    "penetration testing (pentest)", "ethical hacking", "siem solutions", "ids/ips systems", "cryptography", 
    "network security protocols", "application security (appsec)", "owasp top 10", "firewall configuration", 
    "vulnerability assessment & management", "incident response", "digital forensics", "soc (security operations center)",

    # Other specific software or industry terms
    "salesforce development", "sap (abap, hana)", "sharepoint development", "microsoft excel (advanced, vba)", 
    "erp systems", "crm systems", "blockchain technology", "web3 development", "smart contracts", 
    "iot (internet of things)", "embedded systems programming", "firmware development", "rtos (real-time operating systems)"
]
KNOWN_TECH_SKILLS_SET = set(KNOWN_TECH_SKILLS)

# 初始化 PhraseMatcher
skill_patterns = [nlp.make_doc(text) for text in KNOWN_TECH_SKILLS]
phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
phrase_matcher.add("TECH_SKILLS", skill_patterns)

# 停用词 (使用 spaCy 的，如果需要NLTK的可以合并)
combined_stopwords = spacy_stop_words

# --- 噪音词和短语列表 ---
NOISE_WORDS_TO_REMOVE = {
    # 您列出的通用词
    "10", "17", "401(k", "able", "access", "accommodation", "accordance", "act", 
    "additional", "advance", "adverse", "affiliate", "area", "arrest", "assistance", 
    "authority", "bachelor", "belief", "benefit", "communication", "company", "date", "day", "degree", 
    "department", "description", "detail", "development", "discretionary", "document", 
    "documentation", "e.g.", "ease", "employee", "employer", "employment", "end", 
    "energy", "environment", "equivalent", "etc", "excellent", "expect", "expected", 
    "explain", "fair", "familiar", "feedback", "field", "file", "full", "full-time", 
    "holiday", "hour", "idea", "impact", "including", "individual", "industry", 
    "information", "intern", "internal", "knowledge", "language", "law", "learning", 
    "lifecycle", "master", "maintainable", "management", "meeting", "member", "mentor", 
    "mission", "month", "need", "new", "note", "opportunity", "option", "order", 
    "others", "overview", "participate", "participation", "pay", "people", "percent", 
    "performance", "person", "platform", "positive", "preferred", "problem", "process", 
    "proficiency", "program", "project", "provide", "pursuing", "qualification", 
    "quality", "reasoned", "regard", "related", "reliable", "report", "requirement", 
    "resource", "response", "responsibility", "result", "review", "role", "saving", 
    "scalable", "schedule", "science", "scope", "setting", "share", "ship", "skill", 
    "software", "solution", "solving", "stand", "statement", "status", "strong", 
    "support", "system", "technical", "technology", "term", "testable", "testing", 
    "tool", "understanding", "uplifting", "use", "verbal", "version", "view", "web", 
    "week", "well", "willingness", "work", "world", "written", "year",
    # 一些常见的非技能名词和形容词
    "ability", "application", "approach", "aspect", "background", "base", "basis",
    "candidate", "capability", "career", "challenge", "collaboration", "concept",
    "condition", "consideration", "context", "contribution", "creation", "culture",
    "customer", "delivery", "design", # "design"本身可能太泛，但"api design"是好的
    "detail", "effort", "element", "emphasis", "engineering", # "engineering"本身太泛
    "example", "execution", "explanation", "exposure", "focus", "function", "goal",
    "graduation", "growth", "guidance", "idea", "implementation", "improvement",
    "initiative", "insight", "interest", "issue", "item", "level", "lifecycle",
    "maintenance", "manner", "material", "matter", "method", "model", "nature",
    "objective", "operation", "outcome", "output", "owner", "ownership", "part",
    "partner", "path", "pattern", "perspective", "phase", "philosophy", "piece",
    "plan", "position", "practice", "principle", "priority", "procedure",
    "product", # "product"本身可能太泛，除非是NER识别的具体产品名
    "progress", "purpose", "range", "rate", "record", "reference", "relation",
    "release", "research", "result", "review", "satisfaction", "scenario",
    "sense", "service", "set", "side", "site", "situation", "source", "specification",
    "standard", "step", "strategy", "structure", "style", "subject", "success",
    "support", "task", "technique", "term", "test", "time", "title", "topic",
    "track", "trade-off", "tradition", "training", "trend", "type", "unit",
    "usage", "user", "value", "variety", "version", "viewpoint", "way",
    # 确保这里都是小写，并且是词元形式（如果您的提取结果是词元）
}

NOISE_WORDS_TO_REMOVE_SET = set(NOISE_WORDS_TO_REMOVE)

NOISE_PHRASES_TO_REMOVE = { # 小写短语
    "10 pay holiday", "401(k saving plan", "additional discretionary bonus", "affiliate job",
    "bachelor's or master’s", "bachelor's or master's", "bachelor's degree", "master’s degree", #学历本身可能需要保留，但这些短语可能太泛
    "bytedance inspiring creativity", "bytedance mission", # 公司相关的通常是噪音
    "california fair chance act", 
    # "computer science", "computer engineering", "electrical engineering", # 这些作为技能是好的，但作为JD中的普通描述可能是噪音
    "cross-functional teams", "daily or weekly stand ups", "equivalent experience required",
    "expected graduation date", "fast-paced development team",
    "full time", "nice to have", "required skills", "problem-solving skills", # "problem-solving"本身可能是好的
    "software development lifecycle", "technical background", "verbal and written communication",
    "web and mobile apps", "work both independently and collaboratively", "additional responsibilities as needed",
    "based on specific role or team", "all aspects of software development", "etc."
    # ... 持续扩充 ...
}

# --- JD 区段识别逻辑 (来自之前的回复) ---
QUALIFICATION_SECTION_HEADERS = [
    re.compile(r"^\s*(basic qualifications|minimum qualifications|requirements|what you'll need|key qualifications|candidate profile|essential skills|technical skills|skills & qualifications|qualifications|preferred qualifications|desired skills|nice to have|plus(?:es)?)\s*[:\-\–—]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*(skills|experience|education)\s*[:\-\–—]?\s*$", re.IGNORECASE) 
]
IRRELEVANT_SECTION_HEADERS_AFTER_QUALIFICATIONS = [
    re.compile(r"^\s*(about the company|company overview|what we offer|benefits|perks|our mission|eeo statement|equal opportunity employer|application instructions|how to apply)\s*[:\-\–—]?\s*$", re.IGNORECASE)
]

# def get_relevant_jd_sections_text(jd_text: str) -> Optional[str]:
#     lines = jd_text.splitlines()
#     relevant_text_parts: List[str] = []
#     in_relevant_section = False
#     potential_section_buffer: List[str] = [] # 缓冲可能是区段开头的部分

#     for line in lines:
#         stripped_line = line.strip()
        
#         # 尝试匹配资格区段的头部
#         is_qualification_header = any(pattern.fullmatch(stripped_line) for pattern in QUALIFICATION_SECTION_HEADERS)
        
#         if is_qualification_header:
#             in_relevant_section = True
#             # 将缓冲区的内容（如果被认为是相关区段的一部分）加入
#             if potential_section_buffer:
#                 relevant_text_parts.extend(potential_section_buffer)
#                 relevant_text_parts.append("") # 添加空行分隔
#                 potential_section_buffer = []
#             # 通常不直接添加标题行本身，除非标题行也包含信息
#             # relevant_text_parts.append(stripped_line) 
#             if relevant_text_parts and relevant_text_parts[-1] != "" and stripped_line: # 区段间空行
#                  relevant_text_parts.append("")
#             continue

#         if in_relevant_section:
#             is_irrelevant_header = any(pattern.fullmatch(stripped_line) for pattern in IRRELEVANT_SECTION_HEADERS_AFTER_QUALIFICATIONS)
#             if is_irrelevant_header:
#                 in_relevant_section = False # 资格区段结束
#                 # 不再收集此无关区段及之后的内容，或者可以收集到这里然后break
#                 # break # 如果一旦遇到无关头部就停止收集
#             else:
#                 if stripped_line: # 只添加非空行到内容中
#                     relevant_text_parts.append(stripped_line)
#                 elif relevant_text_parts and relevant_text_parts[-1] != "": # 保留段内空行
#                     relevant_text_parts.append("")
#         elif stripped_line: # 如果还未进入相关区段，但有内容，先缓冲
#             potential_section_buffer.append(stripped_line)
            
#     if not relevant_text_parts and potential_section_buffer: # 如果没有找到明确的资格区段头部，但之前有缓冲内容
#         # 这种情况可能意味着整个JD都是“相关”的，或者没有清晰的头部
#         # 为了避免返回整个JD（如果它很大），可以决定不返回，让调用者处理整个JD
#         # 或者，如果缓冲内容本身像是JD的开头核心描述，也可以返回它
#         # full_relevant_text = "\n".join(potential_section_buffer).strip()
#         # if len(full_relevant_text.split()) > 20: # 避免太短
#         #     print(f"[Keyword Extractor] No specific headers, using buffered initial text (length: {len(full_relevant_text)} chars).")
#         #     return full_relevant_text
#         pass


#     if relevant_text_parts:
#         full_relevant_text = "\n".join(relevant_text_parts).strip()
#         # 移除可能因连续空行产生的多个换行
#         full_relevant_text = re.sub(r'\n{2,}', '\n', full_relevant_text) 
#         if len(full_relevant_text.split()) > 10: 
#             print(f"[Keyword Extractor] Extracted relevant sections from JD (length: {len(full_relevant_text)} chars).")
#             return full_relevant_text
#         else:
#             print("[Keyword Extractor] Relevant sections text too short, falling back to full JD.")
#             return None
            
#     print("[Keyword Extractor] No specific qualification sections found or text too short, using full JD text.")
#     return None

# --- 主关键词提取函数 ---
def extract_keywords_from_jd(jd_text: str) -> List[str]:
    if not jd_text:
        return []

    # # 1. 尝试提取相关区段文本
    # text_to_process = get_relevant_jd_sections_text(jd_text)
    # if text_to_process is None:
    #     text_to_process = jd_text # 回退到完整JD
    text_to_process = jd_text
    # 2. 规范化换行符和空白
    processed_text = text_to_process.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
    processed_text = re.sub(r'\s+', ' ', processed_text).strip()
    
    doc = nlp(processed_text)
    
    # 使用集合存储，自动去重
    extracted_keywords: Set[str] = set()

    # 优先级 1: PhraseMatcher 匹配已知技术/技能 (高质量)
    phrase_matches = phrase_matcher(doc)
    for match_id, start, end in phrase_matches:
        span = doc[start:end]
        extracted_keywords.add(span.text.lower().strip())
    print(f"[DEBUG] Keywords after PhraseMatcher: {extracted_keywords}") # <--- 添加调试打印


    # 优先级 2: NER 提取相关实体
    for ent in doc.ents:
        print(f"[DEBUG] NER Entity: '{ent.text.lower().strip()}' Label: '{ent.label_}'") # <--- 添加调试打印

        ent_text_lower = ent.text.lower().strip()
        # 只选择我们认为相关的实体类型
        if ent.label_ in ["PRODUCT", "LANGUAGE", "WORK_OF_ART"]: # WORK_OF_ART 有时是项目/技术名称
            if ent_text_lower not in combined_stopwords and len(ent_text_lower) > 2 and not ent_text_lower.isdigit():
                extracted_keywords.add(ent_text_lower)
        elif ent.label_ == "ORG": # 对于组织名，仅当它也在我们的技术词典中时才添加
            if ent_text_lower in KNOWN_TECH_SKILLS_SET:
                extracted_keywords.add(ent_text_lower)
        # GPE (地点) 和 LOC (位置) 通常是噪音，除非特定职位需要 (例如，区域销售经理)
        # PERSON, DATE, TIME, MONEY, QUANTITY, ORDINAL, CARDINAL 通常也是噪音

    # 优先级 3: 名词短语 (Noun Chunks)
    for chunk in doc.noun_chunks:
        # 清理名词短语，移除内部的停用词等，保留多个词构成的有意义短语
        cleaned_chunk_parts = [
            token.lemma_.lower() for token in chunk
            if not token.is_stop and not token.is_punct and not token.is_space and len(token.lemma_) > 1 and not token.like_num
        ]
        if len(cleaned_chunk_parts) >= 1: # 至少包含一个有效词元
            phrase = " ".join(cleaned_chunk_parts).strip()
            # 避免太短或太长的短语，且不是纯数字，且包含字母
            if 3 < len(phrase) < 50 and not phrase.isdigit() and any(p.isalpha() for p in cleaned_chunk_parts):
                # 避免与 PhraseMatcher 的结果过于重复，如果 PhraseMatcher 已匹配更长的，这里可能不需要
                # 也可以先添加，后续通过去重和噪音短语列表过滤
                extracted_keywords.add(phrase)

    # 优先级 4: 基于词性的关键词 (名词、专有名词 - 作为补充，更易产生噪音)
    for token in doc:
        if (
            not token.is_stop and
            not token.is_punct and
            not token.is_space and
            len(token.lemma_) > 2 and # 至少3个字符
            not token.like_num # 非数字
        ):
            lemma = token.lemma_.lower().strip()
            if lemma in ["html", "css", "javascript"]:
                print(f"[DEBUG] Token: '{lemma}', POS: '{token.pos_}', In KNOWN_TECH: {lemma in KNOWN_TECH_SKILLS_SET}, Passes Length/Noise Check: {len(lemma) > 3 and lemma not in NOISE_WORDS_TO_REMOVE_SET}")

            if token.pos_ in ["PROPN", "NOUN"]:
                # 如果这个词元已经是某个PhraseMatcher结果或名词短语的一部分，可能不需要单独添加
                # 这是一个复杂的判断，目前简单添加，后续通过噪音列表过滤
                # 确保它不是一个非常通用的词（除非它在KNOWN_TECH_SKILLS中）
                if lemma in KNOWN_TECH_SKILLS_SET or (len(lemma) > 3 and lemma not in NOISE_WORDS_TO_REMOVE_SET):
                     extracted_keywords.add(lemma)

    # --- 后期过滤 ---
    # 1. 移除空字符串 (虽然前面步骤尽量避免了，但再次确认)
    extracted_keywords.discard("")

    # 2. 移除明确定义的噪音短语
    keywords_after_phrase_noise_filter = {
        kw for kw in extracted_keywords if kw not in NOISE_PHRASES_TO_REMOVE
    }
    
    # 3. 移除单个噪音词 (但要小心，不要移除是已知技术词的词)
    #    例如，"java" 是技术词，但如果 "java" 也被错误地加入噪音词列表就会有问题
    #    所以，KNOWN_TECH_SKILLS_SET 中的词应该被豁免于 NOISE_WORDS_TO_REMOVE_SET 的过滤
    final_keywords_set = {
        kw for kw in keywords_after_phrase_noise_filter
        if kw in KNOWN_TECH_SKILLS_SET or kw not in NOISE_WORDS_TO_REMOVE_SET
    }

    # 4. (可选) 处理子字符串/包含关系
    #    例如，如果同时提取了 "java" 和 "java developer"，通常保留 "java developer"
    #    这是一个更复杂的步骤，可以后续优化。一个简单方法是优先保留更长的关键词。
    #    例如：
    final_keywords_list = sorted(list(final_keywords_set), key=len, reverse=True)
    deduplicated_keywords = []
    for kw_long in final_keywords_list:
        is_sub_part_of_already_added = False
        for kw_added in deduplicated_keywords:
            if kw_long in kw_added: # 如果长的包含短的，通常已处理。这里是短的包含在长的里面。
                # 如果 kw_long 是 kw_added 的子串，并且它们不完全一样
                if kw_long != kw_added and kw_long in kw_added.split(): # 避免 "py" in "python"
                    is_sub_part_of_already_added = True
                    break
        if not is_sub_part_of_already_added:
            is_super_string_of_already_added = False
            temp_dedup_list = []
            for kw_added in deduplicated_keywords:
                if kw_added != kw_long and kw_added in kw_long.split(): # kw_added 是 kw_long 的子串
                    pass # kw_long 更具体，保留它，之后 kw_added 会被过滤
                else:
                    temp_dedup_list.append(kw_added)
            deduplicated_keywords = temp_dedup_list
            deduplicated_keywords.append(kw_long)
    return sorted(list(set(deduplicated_keywords)))
    # 上述子串逻辑比较复杂且容易出错，初期可以先不加，依赖前面的优先级和噪音过滤。

    # return sorted(list(final_keywords_set))


if __name__ == '__main__':
    sample_jd_qualifications = """
    About the job
About Us

The future of transportation is electric, and our software solves the most critical emerging grid integration challenges to ensure that the impending energy transition is clean, equitable, and resilient. Our enterprise solutions help the grid absorb the coming electrification wave with ease. Utilizing modern, cloud-native platform architecture and robust systems optimization, WeaveGrid’s software is built from the ground up to tackle the most critical network challenges while meeting the stringent regulatory, security, and reliability requirements of the utility industry.

About The Job

As a Software Engineering Intern at WeaveGrid, you will work on impactful, high-priority projects that power the transition to a clean energy future. Whether your interests lie in backend systems, full-stack development, data platforms, or machine learning, this internship offers the opportunity to contribute to real-world solutions in electric vehicle grid integration and clean energy innovation.

You’ll collaborate with a cross-functional team of engineers, product managers, data scientists, and designers to build and improve the software systems that help utilities manage EV charging and modernize the electric grid.

Core Responsibilities

Design and build scalable backend services, APIs, and data pipelines to support internal tools and utility-facing applications.
Contribute to full-stack development, including intuitive, performant UIs using modern frameworks like React.
Support development of machine learning infrastructure and data platforms that drive intelligent decision-making for utility partners.
Participate in sprint planning, code reviews, and team standups to ensure high-quality, collaborative software development.
Conduct research and experimentation on new tools, frameworks, or models to improve product performance and reliability.
Contribute to special projects and other duties as designated by your mentor or assigned designee.

About you

Currently pursuing a Bachelor’s or Master’s degree in Computer Science, Engineering, Data Science, or a related field.
Expected graduation of December 2025 or later.
Demonstrated software engineering experience from internships, school projects, or personal work. Comfortable coding in languages such as Python, Go, JavaScript/TypeScript, or Java.
Exposure to front-end development (HTML, CSS, JavaScript) and frameworks like React or Vue.js is a plus. Familiarity with cloud infrastructure (e.g., AWS, GCP), databases (e.g., PostgreSQL), or data tools (e.g., Apache Beam, Airflow) is beneficial. Strong interest in clean energy, climate tech, and building software with real-world impact.
Eager to learn, grow, and contribute in a fast-paced, mission-driven environment.
Location for this role is SF Bay Area preferred. 

Salary

The expected compensation for this opportunity is between $25-40 an hour.
    """
    extracted = extract_keywords_from_jd(sample_jd_qualifications)
    print(f"\n--- Extracted Keywords from Sample JD ({len(extracted)}) ---")
    for keyword in extracted:
        print(f"- {keyword}")

    print("\n--- Testing with full JD (if section extraction falls back) ---")
    full_jd_text = "We need a Python and React developer. This is a full-time role. Benefits include 10 pay holiday. Join our team in California."
    extracted_full = extract_keywords_from_jd(full_jd_text)
    print(f"\n--- Extracted Keywords from Full JD ({len(extracted_full)}) ---")
    for keyword in extracted_full:
        print(f"- {keyword}")