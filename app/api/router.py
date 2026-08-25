from fastapi import APIRouter
from api.health import router as health_router
from api.v1.router import v1_router

main_router = APIRouter()

# Health check
main_router.include_router(health_router)

# Versioned API: /api/v1/supervisor/invoke, /api/v1/supervisor/stream
main_router.include_router(v1_router, prefix="/api")
