"""
AttentionSync API - Linus style: Do one thing well.
No "smart" features, no "intelligent" adapters, just solid code.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import get_settings
from app.core.database import init_db

# Simple, direct logging - no JSON nonsense in development
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown - nothing fancy"""
    logger.info("Starting AttentionSync API")
    await init_db()
    yield
    logger.info("Shutting down")


def create_app() -> FastAPI:
    """Create the app - one way, the right way"""
    settings = get_settings()
    
    app = FastAPI(
        title="AttentionSync API",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS - simple and direct
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check - the only endpoint that should always work
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    # Include routers - but only if they exist
    try:
        from app.routers import auth, sources, items
        app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
        app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
        app.include_router(items.router, prefix="/api/v1/items", tags=["items"])
    except ImportError as e:
        logger.warning(f"Some routers not available: {e}")
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)