from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from agents.supervisor import SupervisorAgent
from dependencies.supervisor import get_supervisor
from api.v1.orchestrator.schema import InvokeRequest, InvokeResponse
from api.v1.orchestrator.service import OrchestratorService

router = APIRouter(prefix="/supervisor", tags=["supervisor"])


@router.post("/invoke", response_model=InvokeResponse)
async def invoke_supervisor(
    body: InvokeRequest,
    supervisor: SupervisorAgent = Depends(get_supervisor),
):
    """
    Supervisor Agent 단건 호출 (Non-streaming)
    """
    return await OrchestratorService.invoke(body, supervisor)


@router.post("/stream")
async def stream_supervisor(
    body: InvokeRequest,
    supervisor: SupervisorAgent = Depends(get_supervisor),
):
    """
    Supervisor Agent SSE 스트리밍 호출
    """
    event_generator = OrchestratorService.stream(body, supervisor)
    return StreamingResponse(event_generator, media_type="text/event-stream")


@router.get("/info")
async def get_supervisor_info(
    supervisor: SupervisorAgent = Depends(get_supervisor),
):
    """
    Supervisor Agent 상태 및 연결된 Remote A2A Agent 정보 반환
    """
    return await OrchestratorService.get_info(supervisor)


@router.get("/recommend")
async def get_stock_recommendation(
    query: str = "지금 진입하기 좋은 AI 반도체 및 저평가 우량주 추천해줘",
):
    """
    AI 종목 추천 파이프라인 (Top Picks 및 모델 포트폴리오 생성)
    """
    from agents.recommendation_agent import StockRecommendationAgent
    return await StockRecommendationAgent.generate_recommendation(query)

