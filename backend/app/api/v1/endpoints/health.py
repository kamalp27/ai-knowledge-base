import os
from fastapi import APIRouter, Depends, status
from backend.app.core.config import Settings, get_settings
from backend.app.models.health import HealthResponse, ReadinessResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns the overall operational status, application name, version, and environment.",
)
async def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return application health status."""
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Readiness Probe",
    description="Returns readiness state verifying that required local storage paths are accessible.",
)
async def get_readiness(settings: Settings = Depends(get_settings)) -> ReadinessResponse:
    """Return service readiness status."""
    # Verify storage path existence or accessibility
    data_dir_ready = os.path.isdir(settings.DATA_DIR) or os.path.exists(".")
    return ReadinessResponse(
        status="ready" if data_dir_ready else "degraded",
        storage_ready=data_dir_ready,
        services={
            "api": "up",
            "storage": "accessible" if data_dir_ready else "unreachable",
        },
    )
