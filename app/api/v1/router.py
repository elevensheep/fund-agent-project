from fastapi import APIRouter
from api.v1.orchestrator import router as orchestrator_router
from api.v1.stock.router import router as stock_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(orchestrator_router)
v1_router.include_router(stock_router)

