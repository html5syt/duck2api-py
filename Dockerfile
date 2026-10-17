FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    BROWSER_HEADLESS=true

# 安装基础网络、证书工具与常用字体库（保证无头浏览器在 Linux 环境下的 DOM 字体渲染度量与真实桌面一致）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    fonts-liberation \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖描述文件
COPY pyproject.toml README.md ./

# 安装 Python 依赖并安装 Playwright 所需的 Chromium 与系统依赖包
RUN pip install --upgrade pip && \
    pip install . && \
    playwright install --with-deps chromium

# 复制源代码
COPY duck2api/ ./duck2api/
COPY main.py .

EXPOSE 8080

# 容器健康检查探针
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

CMD ["python", "main.py"]