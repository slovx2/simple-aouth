# Stage 1: 构建阶段 - 使用 uv 安装依赖和构建项目
FROM ghcr.io/astral-sh/uv:latest AS uv-installer

FROM python:3.12-alpine AS builder

WORKDIR /app

# 使用阿里云镜像源加速（解决网络和SSL问题）
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 安装构建依赖
RUN apk add --no-cache gcc musl-dev libffi-dev

# 从 uv-installer 复制 uv 工具
COPY --from=uv-installer /uv /usr/local/bin/uv

# 复制依赖配置文件（源码变化不会使此层缓存失效）
COPY pyproject.toml uv.lock ./

# 只安装依赖，不安装项目本身
RUN uv sync --frozen --no-dev --no-install-project

# 复制 README 和源码
COPY README.md ./
COPY src/ ./src/

# 安装项目本身
RUN uv sync --frozen --no-dev

# Stage 2: 运行时镜像
FROM python:3.12-alpine

WORKDIR /app

# 安装运行时依赖并创建用户
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
