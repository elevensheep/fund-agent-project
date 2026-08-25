from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from core.lifespan import lifespan
from api.router import main_router


def create_app() -> FastAPI:
    """
    FastAPI Application Factory for A2A Client Server.
    """
    app = FastAPI(
        title="A2A Client Server API",
        description="A2A Architecture Client Server powered by a single Supervisor Agent",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.include_router(main_router)
    Instrumentator().instrument(app).expose(app)
    
    return app
