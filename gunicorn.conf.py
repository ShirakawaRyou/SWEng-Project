# SWEng-Project-main/gunicorn.conf.py

import multiprocessing
import os

# Gunicorn 将监听的IP和端口。在 Docker 容器内，通常是 0.0.0.0。
# 端口可以与 Dockerfile 或 docker-compose.yml 中暴露的端口一致。
# 如果 Gunicorn 在反向代理（如 Nginx）后面运行，这里可以监听一个 Unix 套接字或本地端口。
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# 工作进程数量
# 推荐值：(2 * CPU核心数) + 1
# 您也可以根据服务器资源和应用负载进行调整
workers = int(os.environ.get("GUNICORN_WORKERS", (multiprocessing.cpu_count() * 2) + 1))

# 工作进程类型
# 使用 uvicorn.workers.UvicornWorker 来运行 FastAPI (ASGI) 应用
worker_class = "uvicorn.workers.UvicornWorker"

# UvicornWorker 的线程数 (通常对于 asyncio 应用，每个worker一个主事件循环，不需要很多线程)
# threads = int(os.environ.get("GUNICORN_THREADS", "1")) # UvicornWorker 默认会处理并发

# 工作进程超时时间 (秒)
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))

# HTTP Keep-Alive 超时时间 (秒)
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

# 日志配置
# '-' 表示输出到标准输出 (stdout)，这在 Docker 中很常见
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info") # "debug", "info", "warning", "error", "critical"

# 预加载应用代码 (在工作进程fork之前加载应用)
# 可以节省一些内存，但如果应用在加载时执行了某些初始化（如数据库连接池），可能需要小心
# 对于 FastAPI/Starlette，通常设置为 False 或不设置，让每个 worker 独立加载
preload_app = os.environ.get("GUNICORN_PRELOAD_APP", "False").lower() == "true"

# (可选) 如果 gunicorn.conf.py 不在 FastAPI 应用的直接父目录，可能需要设置 chdir
# 例如，如果 FastAPI 应用在 backend/ 目录中，而 Gunicorn 从项目根目录启动
# chdir = "/app/backend" # 在 Dockerfile 中 WORKDIR 通常会处理好路径问题

# (可选) Uvicorn 特定的设置，可以通过 Gunicorn 的 --raw-env 传递或在 worker_class 中处理
# 例如，设置 Uvicorn 的日志格式等
# raw_env = [
#     f"UVICORN_LOG_LEVEL={loglevel}",
# ]

# 打印配置信息 (可选，用于调试)
print(f"Gunicorn bind: {bind}")
print(f"Gunicorn workers: {workers}")
print(f"Gunicorn worker_class: {worker_class}")
print(f"Gunicorn loglevel: {loglevel}")