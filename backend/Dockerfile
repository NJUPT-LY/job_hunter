# ============================================================
# 职路AI - 后端Dockerfile
# Python FastAPI 服务容器
# ============================================================

# 使用轻量级Python基础镜像
FROM python:3.11-slim AS builder

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ============================================================
# 生产运行阶段
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    DATA_DIR=/app/data \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# 从builder阶段复制已安装的Python包
COPY --from=builder /install /usr/local

# 浏览器与系统依赖随镜像安装，运行用户无需再次下载。
RUN python -m playwright install --with-deps chromium

# 安装运行时系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    # 创建非root用户
    groupadd -r zhilu && useradd -r -g zhilu zhilu && \
    mkdir -p /app/data /app/logs && \
    chown -R zhilu:zhilu /app

# 复制应用代码
COPY --chown=zhilu:zhilu . .

# 切换到非root用户
USER zhilu

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
