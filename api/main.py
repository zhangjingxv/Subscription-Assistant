from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator


def create_app() -> FastAPI:
    application = FastAPI(title="AttentionSync API", version="0.1.0")

    # Enable permissive CORS for initial development
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health endpoint
    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    # Root endpoint
    @application.get("/")
    async def root() -> dict[str, str]:
        return {"message": "AttentionSync API is running"}

    # Prometheus metrics
    Instrumentator().instrument(application).expose(application, endpoint="/metrics")

    return application


app = create_app()

