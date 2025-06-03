# SWEng-Project-main/download_nltk.py
import nltk
import os # 用于创建 nltk_data 目录

# 定义 NLTK 数据路径 (在 Docker 镜像中通常是 /usr/local/share/nltk_data 或 /usr/share/nltk_data)
# 我们可以尝试创建一个用户可写的目录，或者依赖NLTK的默认搜索路径之一
# 为了确保权限，可以尝试在 /app/nltk_data 下载
nltk_data_dir = os.path.join(os.getcwd(), "nltk_data_in_app") # 在 /app/nltk_data_in_app
if not os.path.exists(nltk_data_dir):
    os.makedirs(nltk_data_dir)
if nltk_data_dir not in nltk.data.path: # 将此路径添加到 NLTK 的搜索路径
    nltk.data.path.append(nltk_data_dir)

nltk_packages = [
    ('stopwords', 'corpora/stopwords'),
    ('punkt', 'tokenizers/punkt'),
    ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger'),
    ('wordnet', 'corpora/wordnet'),
    ('omw-1.4', 'corpora/omw-1.4') # Open Multilingual Wordnet
]

for package_name, package_path_check in nltk_packages:
    try:
        nltk.data.find(package_path_check) # 检查资源是否存在
        print(f"NLTK package '{package_name}' already available.")
    except LookupError: # 如果资源未找到，会抛出 LookupError
        print(f"NLTK package '{package_name}' not found. Downloading...")
        try:
            # 下载到 NLTK 能找到的路径，或者我们指定的 download_dir
            nltk.download(package_name, download_dir=nltk_data_dir, quiet=True)
            print(f"NLTK package '{package_name}' downloaded successfully to {nltk_data_dir}.")
        except Exception as e_download: # 捕获下载过程中可能发生的其他错误
            print(f"Error downloading NLTK package '{package_name}': {e_download}")
            # 根据需要，您可以决定下载失败是否应该使整个 Docker 构建失败
            # exit(1) # 如果需要构建失败

print("NLTK data download process finished.")