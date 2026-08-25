from fastapi import Request, HTTPException
from agents.supervisor import SupervisorAgent


def get_supervisor(request: Request) -> SupervisorAgent:
    """
    app.state.supervisor에서 단일 SupervisorAgent를 추출하는 FastAPI Dependency Injection 함수.
    """
    supervisor = getattr(request.app.state, "supervisor", None)
    if supervisor is None:
        raise HTTPException(
            status_code=503,
            detail="Supervisor Agent is not initialized.",
        )
    return supervisor
