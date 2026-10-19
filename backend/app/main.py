from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.endpoints.health import get_health, get_readiness
from backend.app.api.v1.router import api_router
from backend.app.core.config import Settings, get_settings
from backend.app.models.health import HealthResponse, ReadinessResponse
from backend.app.rag.llm import LLMConfigurationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for application startup and shutdown."""
    settings = get_settings()
    # Ensure standard storage directories exist on startup
    for path in [settings.DATA_DIR, settings.RAW_DOCUMENTS_DIR, settings.VECTOR_STORE_DIR, settings.EVAL_DATASETS_DIR]:
        os.makedirs(path, exist_ok=True)

    # Ensure database directory exists
    db_dir = os.path.dirname(os.path.abspath(settings.METADATA_DB_PATH))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # Operational notice for fake LLM provider in production
    if settings.APP_ENV.lower() == "production" and settings.LLM_PROVIDER.lower() == "fake":
        import logging
        logging.getLogger("uvicorn.error").warning(
            "OPERATIONAL NOTICE: LLM_PROVIDER is set to 'fake' in production. "
            "Answers will be deterministic synthetic responses and do not reflect genuine LLM reasoning."
        )

    yield


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-ready FastAPI backend for Document Question Answering using Retrieval-Augmented Generation (RAG).",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(LLMConfigurationError)
async def llm_configuration_error_handler(request: Request, exc: LLMConfigurationError):
    """Handle missing or misconfigured LLM provider cleanly with HTTP 503."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": {
                "error": "LLM_NOT_CONFIGURED",
                "message": str(exc),
                "hint": "Set LLM_PROVIDER ('openai' or 'anthropic') and supply the corresponding API key in your .env file, or set LLM_PROVIDER=fake for testing.",
            }
        },
    )

# Root-level health and readiness endpoints
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Root"],
    summary="Root Health Check",
    description="Root-level health check endpoint returning system operational status.",
)
async def root_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return await get_health(settings=settings)


@app.get(
    "/ready",
    response_model=ReadinessResponse,
    tags=["Root"],
    summary="Root Readiness Check",
    description="Root-level readiness probe verifying service dependencies and storage access.",
)
async def root_ready(settings: Settings = Depends(get_settings)) -> ReadinessResponse:
    return await get_readiness(settings=settings)


@app.get("/", tags=["Root"], summary="API Root")
async def root(settings: Settings = Depends(get_settings)):
    """API root landing endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_PREFIX,
    }


# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
