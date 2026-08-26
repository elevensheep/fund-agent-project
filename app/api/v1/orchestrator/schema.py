from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    message: str = Field(..., description="사용자 요청 메시지")
    thread_id: Optional[str] = Field(None, description="대화 세션 식별자")
    force_refresh: bool = Field(False, description="캐시 무시 및 강제 재실행 여부")


class InvokeResponse(BaseModel):
    output: str = Field(..., description="Supervisor 최종 응답")
    used_agents: List[str] = Field(default_factory=list, description="호출 및 위임된 Remote Agent 목록")
    plan: Optional[Dict[str, Any]] = Field(None, description="Plan-and-Execute 실행 계획 (DAG)")
    remote_response: Optional[str] = Field(None, description="Remote Agent raw 응답")
    is_cached: bool = Field(False, description="Redis 캐시 데이터 여부")
    cached_at: Optional[str] = Field(None, description="캐시 적재 타임스탬프 (ISO 8601)")
    ttl_remaining: Optional[int] = Field(None, description="캐시 만료 잔여 시간 (초)")
