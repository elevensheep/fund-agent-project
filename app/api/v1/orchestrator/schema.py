from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    message: str = Field(..., description="사용자 요청 메시지")
    thread_id: Optional[str] = Field(None, description="대화 세션 식별자")


class InvokeResponse(BaseModel):
    output: str = Field(..., description="Supervisor 최종 응답")
    used_agents: List[str] = Field(default_factory=list, description="호출 및 위임된 Remote Agent 목록")
    plan: Optional[Dict[str, Any]] = Field(None, description="Plan-and-Execute 실행 계획 (DAG)")
    remote_response: Optional[str] = Field(None, description="Remote Agent raw 응답")
