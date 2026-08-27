FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /workspace

# 의존성 복사 (루트 기준)
COPY app/pyproject.toml app/uv.lock ./app/
COPY shared_core/ ./shared_core/

WORKDIR /workspace/app
RUN uv sync --frozen --no-dev --no-install-project
ENV PYTHONPATH=/workspace/shared_core/src:/workspace/app

# 애플리케이션 복사
COPY app/ ./
EXPOSE 28000
CMD ["uv", "run", "fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "28000"]
