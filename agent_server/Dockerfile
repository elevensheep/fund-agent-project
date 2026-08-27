FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /workspace

# 의존성 복사 (루트 기준)
COPY agent_server/pyproject.toml agent_server/uv.lock ./agent_server/
COPY shared_core/ ./shared_core/

WORKDIR /workspace/agent_server
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV UV_LINK_MODE=copy
RUN uv sync --frozen --no-dev --no-install-project
ENV PYTHONPATH=/workspace/shared_core/src:/workspace/agent_server
ENV PATH="/opt/venv/bin:$PATH"

# 애플리케이션 복사
COPY agent_server/ ./
# 실행할 에이전트 모듈 (기본값: agents.echo_agent)
ENV AGENT_MODULE="agents.echo_agent"
# 에이전트별 포트 (서비스마다 오버라이드 가능)
ENV AGENT_PORT="28001"
EXPOSE ${AGENT_PORT}
CMD ["sh", "-c", "uv run uvicorn ${AGENT_MODULE}:app --host 0.0.0.0 --port ${AGENT_PORT}"]
