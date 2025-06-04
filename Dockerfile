# SWEng-Project-main/Dockerfile

# 1. 选择基础镜像
# 使用一个官方的 Python 3.9 slim 镜像，它比较小且包含常用工具
FROM python:3.9-buster

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1  # 防止 Python 写入 .pyc 文件
ENV PYTHONUNBUFFERED 1      # 防止 Python 缓冲 stdout 和 stderr，使日志立即显示

# 2. 设置工作目录
WORKDIR /app/backend

# 3. ==> 新增：安装系统依赖和编译工具 <==
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

ENV BLIS_ARCH=generic

# 4. 复制依赖文件并安装依赖
# COPY ./requirements.txt /app/requirements.txt
COPY ./backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. 下载NLTK数据模型
# COPY ./download_nltk.py /app/download_nltk.py # 不再需要这个脚本
# ENV NLTK_DATA /app/nltk_data_in_app # 如果用下面的方法，NLTK_DATA 可以不设置或指向标准路径

# ==> 直接使用 NLTK downloader 下载数据包 <==
RUN python -m nltk.downloader -d /usr/local/share/nltk_data stopwords punkt averaged_perceptron_tagger wordnet omw-1.4
# -d /usr/local/share/nltk_data 是一个常见的 NLTK 数据存放路径，通常在 PATH 中
# 您也可以选择 /usr/share/nltk_data 或 /root/nltk_data，或您之前设置的 /app/nltk_data_in_app
# 如果不指定 -d，它会尝试下载到默认路径列表中的某个位置

# 对于 spaCy (如果您决定使用它并且解决了安装问题):
RUN python -m spacy download en_core_web_sm

# 6. 复制应用代码到工作目录
# 这里我们将整个项目上下文复制到 /app，然后在 .dockerignore 中排除不需要的文件
# 或者，您可以只复制 backend 目录：COPY ./backend /app/backend
COPY SWEng-Project/backend/ .
# 如果 gunicorn.conf.py 在根目录，而应用在 backend/
# 确保 gunicorn 命令能找到它，或者也复制到 /app

# 7. (可选) 创建一个非 root 用户来运行应用，增强安全性
# RUN useradd --create-home appuser
# USER appuser

# 8. 暴露应用监听的端口 (与 Gunicorn 配置中的 bind 端口一致)
EXPOSE 8000

# 9. 定义容器启动时运行的命令
# Gunicorn 将从项目根目录 (即 /app) 启动
# 它会查找 backend/app.py 中的 app 实例
# -c /app/gunicorn.conf.py 指定了Gunicorn配置文件 (假设它在根目录并被复制到/app)
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "/app/gunicorn.conf.py", "backend.app:app"]
# 如果 gunicorn.conf.py 中已经设置了 worker_class，可以简化为：
# CMD ["gunicorn", "-c", "/app/gunicorn.conf.py", "backend.app:app"]