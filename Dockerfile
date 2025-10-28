# 多阶段构建，使用 alpine 基础镜像以最小化体积
FROM python:3.12-alpine AS builder

WORKDIR /app

# 安装构建依赖
RUN apk add --no-cache gcc musl-dev libffi-dev

# 安装 uv（仅用于构建阶段）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制项目文件
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# 安装依赖到 /app/.venv
RUN uv sync --frozen --no-dev --no-cache

# 最终镜像 - 使用 alpine 减小体积
FROM python:3.12-alpine

WORKDIR /app

# 安装运行时依赖
RUN apk add --no-cache libffi && \
    adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app

# 从 builder 复制虚拟环境（不包含 uv）
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# 复制应用代码
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser pyproject.toml ./

# 切换到非 root 用户
USER appuser

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5001

# 启动应用
CMD ["python", "-m", "fb_oauth"]
