from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check(request: Request):
    """
    서비스 Health Check 및 런타임 상태 정보 반환
    """
    supervisor = getattr(request.app.state, "supervisor", None)
    return {
        "status": "ok",
        "role": "a2a_client_server",
        "supervisor_active": supervisor is not None,
        "remote_agents": list(getattr(request.app.state, "a2a_registry", {}).keys()),
    }
