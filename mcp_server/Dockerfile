FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /workspace

# 의존성 복사 (루트 기준)
COPY mcp_server/pyproject.toml mcp_server/uv.lock ./mcp_server/
COPY shared_core/ ./shared_core/

WORKDIR /workspace/mcp_server
RUN uv sync --frozen --no-dev --no-install-project
ENV PYTHONPATH=/workspace/shared_core/src:/workspace/mcp_server

# 애플리케이션 복사
COPY mcp_server/ ./
EXPOSE 28002
# SSE 전송을 위한 실행 명령어 (필요시 PORT 설정)
CMD ["uv", "run", "python", "server.py"]
